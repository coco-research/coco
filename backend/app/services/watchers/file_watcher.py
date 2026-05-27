"""Cross-platform file watcher for HxStore, attachments, and project syncs.

Phase 10 — `.planning/v3/backend/DESIGN.md` Bird's-eye view §1:
  com.coco.platform-watcher — HxStore + project folders.

This service is event-driven (uses the `watchdog` library) and emits
`IngestRequest` objects to a registered handler — typically the Phase 5
ingest router's enqueue function.  On handler failure, the request is
forwarded to the DLQ so it can be retried out-of-band.

Why event-driven rather than polling: HxStore mutates frequently but
quietly; relying on launchd intervals misses bursts. watchdog's
FSEvents (macOS) / inotify (Linux) backend gives sub-second latency
with O(1) CPU at rest.

The service is *idempotent*: it never persists state.  Replays and
debouncing are the responsibility of the ingest handler.

Cross-platform notes:
- macOS: FSEvents observer (default).
- Linux: inotify observer.
- Tests: PollingObserver with very low interval, plus direct
  `_dispatch_event` calls so we don't depend on FS timing.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Iterable, Optional

from watchdog.events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WatchSpec:
    """One directory to watch + its ingest semantics."""

    path: str
    source: str  # logical label: 'hxstore' | 'attachments' | 'project_sync'
    recursive: bool = True
    # Optional filename suffix allowlist (e.g. ('.eml', '.msg')); empty = all.
    suffixes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class IngestRequest:
    """Payload passed to the ingest handler / DLQ on failure.

    Mirrors the public schema of the Phase 5 ingest router so a watcher
    fire can be handed off directly without translation.
    """

    source: str
    path: str
    event_type: str  # 'created' | 'modified' | 'moved'
    detected_at: str
    extra: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "path": self.path,
            "event_type": self.event_type,
            "detected_at": self.detected_at,
            **self.extra,
        }


# Handler protocol: callable(IngestRequest) -> None.
# On exception the file watcher routes to the DLQ.
IngestHandler = Callable[[IngestRequest], None]
DLQFallback = Callable[[str, dict[str, Any], str], None]
"""Signature: fallback(source_task, payload_dict, error_str)."""


# ---------------------------------------------------------------------------
# Internal: per-spec event handler
# ---------------------------------------------------------------------------


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class _SpecHandler(FileSystemEventHandler):
    """watchdog handler bound to one WatchSpec + the parent service."""

    def __init__(self, service: "FileWatcherService", spec: WatchSpec) -> None:
        super().__init__()
        self.service = service
        self.spec = spec

    # We only care about create/modify/move (not delete) for ingest.

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self.service._dispatch_event(self.spec, event.src_path, "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        self.service._dispatch_event(self.spec, event.src_path, "modified")

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        # dest_path is the new location.
        dest = getattr(event, "dest_path", event.src_path)
        self.service._dispatch_event(self.spec, dest, "moved")


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class FileWatcherService:
    """Drive watchdog observers and route events to ingest + DLQ.

    Lifecycle:
        svc = FileWatcherService(specs, handler, dlq_fallback=...)
        svc.start()       # spins up the Observer thread
        ...
        svc.stop()        # joins the Observer thread

    Tests typically *do not* call start(); they construct the service and
    call `_dispatch_event` directly to exercise routing without depending
    on FS event timing.
    """

    def __init__(
        self,
        specs: Iterable[WatchSpec],
        handler: IngestHandler,
        *,
        dlq_fallback: Optional[DLQFallback] = None,
        debounce_seconds: float = 0.5,
        observer_factory: Callable[[], Any] = Observer,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.specs: list[WatchSpec] = list(specs)
        self.handler = handler
        self.dlq_fallback = dlq_fallback
        self.debounce_seconds = debounce_seconds
        self._observer_factory = observer_factory
        self._clock = clock

        self._observer: Optional[Any] = None
        self._last_event_at: dict[tuple[str, str], float] = {}
        self._lock = Lock()
        self._stats = {
            "dispatched": 0,
            "handled_ok": 0,
            "handled_fail": 0,
            "dlq_routed": 0,
            "debounced": 0,
            "filtered_suffix": 0,
        }

    # -- stats --------------------------------------------------------------

    @property
    def stats(self) -> dict[str, int]:
        with self._lock:
            return dict(self._stats)

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        if self._observer is not None:
            return
        observer = self._observer_factory()
        for spec in self.specs:
            p = Path(spec.path).expanduser()
            if not p.exists():
                # Don't fail boot; log + skip. The directory may appear later
                # (e.g., project_sync folders created by user).
                log.warning("file_watcher: path missing, skipping: %s", p)
                continue
            observer.schedule(
                _SpecHandler(self, spec),
                str(p),
                recursive=spec.recursive,
            )
        observer.start()
        self._observer = observer
        log.info("file_watcher: started with %d spec(s)", len(self.specs))

    def stop(self, timeout: float = 5.0) -> None:
        if self._observer is None:
            return
        try:
            self._observer.stop()
            self._observer.join(timeout=timeout)
        finally:
            self._observer = None
        log.info("file_watcher: stopped")

    # -- filtering / debounce ----------------------------------------------

    def _matches_suffix(self, spec: WatchSpec, path: str) -> bool:
        if not spec.suffixes:
            return True
        low = path.lower()
        return any(low.endswith(s.lower()) for s in spec.suffixes)

    def _is_debounced(self, key: tuple[str, str]) -> bool:
        if self.debounce_seconds <= 0:
            return False
        now = self._clock()
        with self._lock:
            last = self._last_event_at.get(key)
            if last is not None and (now - last) < self.debounce_seconds:
                return True
            self._last_event_at[key] = now
            return False

    # -- core dispatch ------------------------------------------------------

    def _dispatch_event(self, spec: WatchSpec, path: str, event_type: str) -> None:
        """Route one filesystem event to the handler (or DLQ on failure)."""
        if not self._matches_suffix(spec, path):
            with self._lock:
                self._stats["filtered_suffix"] += 1
            return

        key = (spec.source, os.path.abspath(path))
        if self._is_debounced(key):
            with self._lock:
                self._stats["debounced"] += 1
            return

        req = IngestRequest(
            source=spec.source,
            path=path,
            event_type=event_type,
            detected_at=_utc_iso(),
        )
        with self._lock:
            self._stats["dispatched"] += 1

        try:
            self.handler(req)
        except Exception as exc:  # noqa: BLE001 — handler errors → DLQ
            with self._lock:
                self._stats["handled_fail"] += 1
            log.exception(
                "file_watcher: ingest handler failed source=%s path=%s",
                spec.source,
                path,
            )
            if self.dlq_fallback is not None:
                try:
                    self.dlq_fallback(
                        f"file_watcher.{spec.source}",
                        req.to_payload(),
                        str(exc),
                    )
                    with self._lock:
                        self._stats["dlq_routed"] += 1
                except Exception:  # noqa: BLE001
                    log.exception("file_watcher: DLQ fallback raised")
        else:
            with self._lock:
                self._stats["handled_ok"] += 1


# ---------------------------------------------------------------------------
# Convenience: default WatchSpecs for production launchd job
# ---------------------------------------------------------------------------

HXSTORE_DEFAULT = (
    "~/Library/Group Containers/UBF8T346G9.Office/Outlook/"
    "Outlook 15 Profiles/Main Profile"
)
ATTACHMENTS_DEFAULT = (
    "~/Library/Group Containers/UBF8T346G9.Office/Outlook/"
    "Outlook 15 Profiles/Main Profile/Files/S0/4/Attachments/0"
)


def default_specs(project_sync_root: Optional[str] = None) -> list[WatchSpec]:
    """Production defaults — used by the launchd watcher entrypoint.

    Caller wires this up in `main.py`'s lifespan; tests pass their own.
    """
    specs: list[WatchSpec] = [
        WatchSpec(
            path=HXSTORE_DEFAULT,
            source="hxstore",
            recursive=False,
            suffixes=(".hxd",),
        ),
        WatchSpec(
            path=ATTACHMENTS_DEFAULT,
            source="attachments",
            recursive=True,
        ),
    ]
    if project_sync_root:
        specs.append(
            WatchSpec(
                path=project_sync_root,
                source="project_sync",
                recursive=True,
            )
        )
    return specs
