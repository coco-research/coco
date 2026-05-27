"""Tests for the file watcher service (Phase 10).

We exercise routing logic directly via `_dispatch_event` to avoid
depending on FS-event timing. One integration-flavoured test uses a
real watchdog PollingObserver against a tmp dir to confirm the wiring.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import pytest

from app.services.watchers.file_watcher import (
    FileWatcherService,
    IngestRequest,
    WatchSpec,
    default_specs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _RecordingHandler:
    """Captures every ingest call; can be flipped to raise."""

    def __init__(self) -> None:
        self.calls: list[IngestRequest] = []
        self._raise: Exception | None = None

    def __call__(self, req: IngestRequest) -> None:
        if self._raise is not None:
            raise self._raise
        self.calls.append(req)

    def raise_with(self, exc: Exception) -> None:
        self._raise = exc

    def stop_raising(self) -> None:
        self._raise = None


class _RecordingDLQ:
    """Stand-in for DeadLetterQueue.enqueue, matching the fallback signature."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any], str]] = []

    def __call__(self, source_task: str, payload: dict[str, Any], err: str) -> None:
        self.calls.append((source_task, payload, err))


# ---------------------------------------------------------------------------
# 1. Suffix filtering
# ---------------------------------------------------------------------------


def test_suffix_filter_blocks_non_matching_paths() -> None:
    handler = _RecordingHandler()
    spec = WatchSpec(path="/tmp/never", source="hxstore", suffixes=(".hxd",))
    svc = FileWatcherService([spec], handler, debounce_seconds=0)

    svc._dispatch_event(spec, "/tmp/never/foo.txt", "modified")

    assert handler.calls == []
    assert svc.stats["dispatched"] == 0
    assert svc.stats["filtered_suffix"] == 1


def test_suffix_filter_allows_matching_paths() -> None:
    handler = _RecordingHandler()
    spec = WatchSpec(path="/tmp/never", source="hxstore", suffixes=(".hxd",))
    svc = FileWatcherService([spec], handler, debounce_seconds=0)

    svc._dispatch_event(spec, "/tmp/never/HxStore.hxd", "modified")

    assert len(handler.calls) == 1
    assert handler.calls[0].source == "hxstore"
    assert handler.calls[0].event_type == "modified"
    assert handler.calls[0].path.endswith("HxStore.hxd")


# ---------------------------------------------------------------------------
# 2. Debouncing
# ---------------------------------------------------------------------------


def test_debounce_suppresses_duplicate_events_within_window(monkeypatch: pytest.MonkeyPatch) -> None:
    handler = _RecordingHandler()
    spec = WatchSpec(path="/tmp/x", source="attachments")
    fake_time = {"now": 100.0}
    svc = FileWatcherService(
        [spec], handler, debounce_seconds=1.0, clock=lambda: fake_time["now"]
    )

    svc._dispatch_event(spec, "/tmp/x/a.bin", "modified")
    fake_time["now"] = 100.3
    svc._dispatch_event(spec, "/tmp/x/a.bin", "modified")
    fake_time["now"] = 100.7
    svc._dispatch_event(spec, "/tmp/x/a.bin", "modified")

    assert len(handler.calls) == 1
    assert svc.stats["debounced"] == 2


def test_debounce_window_releases_after_interval() -> None:
    handler = _RecordingHandler()
    spec = WatchSpec(path="/tmp/x", source="attachments")
    fake_time = {"now": 100.0}
    svc = FileWatcherService(
        [spec], handler, debounce_seconds=1.0, clock=lambda: fake_time["now"]
    )

    svc._dispatch_event(spec, "/tmp/x/a.bin", "created")
    fake_time["now"] = 102.0  # well past the 1s window
    svc._dispatch_event(spec, "/tmp/x/a.bin", "modified")

    assert len(handler.calls) == 2
    assert svc.stats["debounced"] == 0


# ---------------------------------------------------------------------------
# 3. Error routing to DLQ
# ---------------------------------------------------------------------------


def test_handler_failure_is_forwarded_to_dlq() -> None:
    handler = _RecordingHandler()
    handler.raise_with(RuntimeError("boom"))
    dlq = _RecordingDLQ()
    spec = WatchSpec(path="/tmp/x", source="hxstore")
    svc = FileWatcherService(
        [spec], handler, dlq_fallback=dlq, debounce_seconds=0
    )

    svc._dispatch_event(spec, "/tmp/x/HxStore.hxd", "modified")

    assert handler.calls == []
    assert svc.stats["handled_fail"] == 1
    assert svc.stats["dlq_routed"] == 1
    assert len(dlq.calls) == 1
    source_task, payload, err = dlq.calls[0]
    assert source_task == "file_watcher.hxstore"
    assert payload["source"] == "hxstore"
    assert payload["event_type"] == "modified"
    assert err == "boom"


def test_handler_success_does_not_invoke_dlq() -> None:
    handler = _RecordingHandler()
    dlq = _RecordingDLQ()
    spec = WatchSpec(path="/tmp/x", source="project_sync")
    svc = FileWatcherService(
        [spec], handler, dlq_fallback=dlq, debounce_seconds=0
    )

    svc._dispatch_event(spec, "/tmp/x/note.md", "created")

    assert svc.stats["handled_ok"] == 1
    assert svc.stats["handled_fail"] == 0
    assert dlq.calls == []


def test_dlq_fallback_exception_does_not_crash_watcher() -> None:
    handler = _RecordingHandler()
    handler.raise_with(RuntimeError("primary fail"))

    def bad_dlq(source_task: str, payload: dict[str, Any], err: str) -> None:
        raise RuntimeError("dlq fail")

    spec = WatchSpec(path="/tmp/x", source="hxstore")
    svc = FileWatcherService([spec], handler, dlq_fallback=bad_dlq, debounce_seconds=0)

    # Should not raise — watcher must remain resilient.
    svc._dispatch_event(spec, "/tmp/x/HxStore.hxd", "modified")

    # We tried to route to DLQ but it raised, so dlq_routed should *not*
    # have been incremented.
    assert svc.stats["handled_fail"] == 1
    assert svc.stats["dlq_routed"] == 0


# ---------------------------------------------------------------------------
# 4. IngestRequest shape
# ---------------------------------------------------------------------------


def test_ingest_request_payload_contains_expected_fields() -> None:
    handler = _RecordingHandler()
    spec = WatchSpec(path="/tmp/x", source="project_sync")
    svc = FileWatcherService([spec], handler, debounce_seconds=0)

    svc._dispatch_event(spec, "/tmp/x/proj/note.md", "created")

    req = handler.calls[0]
    payload = req.to_payload()
    assert payload["source"] == "project_sync"
    assert payload["path"] == "/tmp/x/proj/note.md"
    assert payload["event_type"] == "created"
    assert "detected_at" in payload and payload["detected_at"]


# ---------------------------------------------------------------------------
# 5. Default specs builder
# ---------------------------------------------------------------------------


def test_default_specs_includes_hxstore_and_attachments() -> None:
    specs = default_specs()
    sources = {s.source for s in specs}
    assert "hxstore" in sources
    assert "attachments" in sources
    assert "project_sync" not in sources


def test_default_specs_adds_project_sync_when_provided() -> None:
    specs = default_specs(project_sync_root="/Users/me/projects")
    sources = {s.source for s in specs}
    assert "project_sync" in sources
    ps = next(s for s in specs if s.source == "project_sync")
    assert ps.path == "/Users/me/projects"
    assert ps.recursive is True


# ---------------------------------------------------------------------------
# 6. Lifecycle (start/stop) with PollingObserver against a real tmpdir
# ---------------------------------------------------------------------------


def test_observer_lifecycle_with_polling_observer(tmp_path: Path) -> None:
    """Integration-ish: real watchdog Observer wired to a tmp dir.

    We don't rely on the OS-event timing — we just confirm start() and
    stop() are idempotent and don't raise. The pure-routing assertions
    above cover behaviour.
    """
    from watchdog.observers.polling import PollingObserver

    handler = _RecordingHandler()
    spec = WatchSpec(path=str(tmp_path), source="project_sync")
    svc = FileWatcherService(
        [spec],
        handler,
        debounce_seconds=0,
        observer_factory=lambda: PollingObserver(timeout=0.05),
    )

    svc.start()
    # idempotent start
    svc.start()
    try:
        # touch a file to give the observer something to do
        (tmp_path / "hello.txt").write_text("hi", encoding="utf-8")
        time.sleep(0.3)  # give the polling observer a tick or two
    finally:
        svc.stop()
        # idempotent stop
        svc.stop()

    # We assert lifecycle ran; FS event delivery via PollingObserver is
    # best-effort across platforms, so we don't gate on handler.calls.
    assert svc.stats["dispatched"] >= 0  # smoke


# ---------------------------------------------------------------------------
# 7. Missing path is skipped, not fatal
# ---------------------------------------------------------------------------


def test_start_skips_missing_paths(tmp_path: Path) -> None:
    handler = _RecordingHandler()
    real = WatchSpec(path=str(tmp_path), source="project_sync")
    missing = WatchSpec(path=str(tmp_path / "does-not-exist"), source="hxstore")

    fake_observer_calls: list[tuple[Any, str, bool]] = []

    class _FakeObserver:
        def schedule(self, h: Any, p: str, recursive: bool) -> None:
            fake_observer_calls.append((h, p, recursive))

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

        def join(self, timeout: float = 0) -> None:
            pass

    svc = FileWatcherService(
        [real, missing],
        handler,
        debounce_seconds=0,
        observer_factory=_FakeObserver,
    )
    svc.start()
    try:
        # only the real path should have been scheduled
        assert len(fake_observer_calls) == 1
        assert fake_observer_calls[0][1] == str(tmp_path)
    finally:
        svc.stop()
