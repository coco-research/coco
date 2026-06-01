"""In-process async event bus for broadcasting real-time events to SSE subscribers.

Events are persisted to the ``events`` table in platform.db so that SSE clients
can replay missed events after a reconnection.  They are also appended to
``~/.coco/events.jsonl`` so that the CLI can tail the same stream.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import AsyncGenerator, Callable

import structlog
from sqlalchemy import delete, insert, select

from app.config import EVENTS_JSONL_PATH
from app.db.compat import now
from app.db.engine import engine
from app.db.tables import events

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------

class EventBus:
    """Async broadcast bus with SQLite persistence for replay."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue] = []
        # Synchronous in-process listeners: (event_type | None, callback).
        # event_type None means "all events". Invoked inside emit().
        self._listeners: list[tuple[str | None, Callable[[dict], None]]] = []

    # -- synchronous listener API -----------------------------------------

    def on(self, event_type: str | None, callback: Callable[[dict], None]) -> None:
        """Register a synchronous listener invoked on every matching emit().

        Args:
            event_type: Exact event type to match, or ``None`` for all events.
            callback: Called as ``callback(data)`` where ``data`` is the emit
                payload dict.

        Idempotent: registering the same ``(event_type, callback)`` pair more
        than once is a no-op, so callers may safely re-run their registration
        (e.g. repeated app startup in tests or a reload) without stacking
        duplicate listeners.
        """
        for et, cb in self._listeners:
            if et == event_type and cb == callback:
                return
        self._listeners.append((event_type, callback))

    def off(self, event_type: str | None, callback: Callable[[dict], None]) -> None:
        """Remove a previously registered listener. No-op if not present."""
        self._listeners = [
            (et, cb)
            for et, cb in self._listeners
            if not (et == event_type and cb == callback)
        ]

    # -- persistence helpers (fire-and-forget, never block emit) ----------

    def _persist(self, event_type: str, data_json: str) -> None:
        """Write event to DB. Called synchronously; errors are swallowed."""
        try:
            with engine.connect() as conn:
                conn.execute(
                    insert(events).values(
                        event_type=event_type,
                        data_json=data_json,
                        created_at=now(),
                    )
                )
                conn.commit()
        except Exception as exc:
            # Never let persistence failure break the live event path
            log.warning("event_persist_failed", event_type=event_type, error=str(exc))

    # -- public API -------------------------------------------------------

    def emit(self, event_type: str, data: dict) -> None:
        """Send an event to every active subscriber and persist to DB.

        Safe to call from sync code -- it does not await.
        """
        data_json = json.dumps({**data, "type": event_type, "ts": time.time()})
        envelope = {"event": event_type, "data": data_json}

        # Broadcast to in-memory subscribers
        dead: list[asyncio.Queue] = []
        for q in self._subscribers:
            try:
                q.put_nowait(envelope)
            except asyncio.QueueFull:
                try:
                    q.get_nowait()
                    q.put_nowait(envelope)
                except Exception:
                    dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

        # Persist (fire-and-forget)
        self._persist(event_type, data_json)

        # Bridge to events.jsonl for CLI visibility
        self._append_jsonl(event_type, data)

        # Notify synchronous in-process listeners. Iterate a snapshot so a
        # listener that emits re-entrantly (e.g. emits another event) cannot
        # mutate the list mid-iteration. Listener errors never break emit.
        for et, cb in list(self._listeners):
            if et is None or et == event_type:
                try:
                    cb(data)
                except Exception as exc:
                    log.warning(
                        "event_listener_error",
                        event_type=event_type,
                        error=str(exc),
                    )

    # -- events.jsonl bridge ------------------------------------------------

    _JSONL_MAX_LINES = 10_000
    _JSONL_TRIM_TO = 5_000

    def _append_jsonl(self, event_type: str, data: dict) -> None:
        """Append one line to ~/.coco/events.jsonl. Never blocks emit()."""
        try:
            line = json.dumps({
                "type": event_type,
                "data": data,
                "ts": datetime.now(timezone.utc).isoformat(),
            })
            EVENTS_JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(EVENTS_JSONL_PATH, "a") as f:
                f.write(line + "\n")
            self._trim_events_file()
        except Exception:
            pass  # Never block on file append

    def _trim_events_file(self) -> None:
        """If events.jsonl exceeds _JSONL_MAX_LINES, truncate to the last _JSONL_TRIM_TO lines."""
        try:
            if not EVENTS_JSONL_PATH.exists():
                return
            lines = EVENTS_JSONL_PATH.read_text().splitlines()
            if len(lines) > self._JSONL_MAX_LINES:
                trimmed = lines[-self._JSONL_TRIM_TO :]
                tmp = EVENTS_JSONL_PATH.with_suffix(".jsonl.tmp")
                tmp.write_text("\n".join(trimmed) + "\n")
                tmp.rename(EVENTS_JSONL_PATH)
                log.info("events_jsonl_trimmed", kept=len(trimmed))
        except Exception:
            pass  # Best effort

    def replay(self, since: str) -> list[dict]:
        """Return persisted events created after *since* (ISO-8601 timestamp).

        Returns a list of SSE-ready dicts: ``{"event": ..., "data": ...}``.
        """
        try:
            with engine.connect() as conn:
                rows = conn.execute(
                    select(events.c.event_type, events.c.data_json)
                    .where(events.c.created_at > since)
                    .order_by(events.c.id.asc())
                ).fetchall()
                return [{"event": r.event_type, "data": r.data_json} for r in rows]
        except Exception as exc:
            log.warning("event_replay_failed", since=since, error=str(exc))
            return []

    def cleanup(self, max_age_hours: int = 24) -> int:
        """Delete events older than *max_age_hours*. Returns deleted count."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    delete(events).where(events.c.created_at < cutoff)
                )
                conn.commit()
                deleted = result.rowcount
                if deleted:
                    log.info("events_cleaned_up", deleted=deleted, cutoff=cutoff)
                return deleted
        except Exception as exc:
            log.warning("event_cleanup_failed", error=str(exc))
            return 0

    async def subscribe(self, event_prefix: str | None = None) -> AsyncGenerator[dict, None]:
        """Yield SSE-ready dicts as they arrive.

        Args:
            event_prefix: If set, only yield events whose ``event`` field
                starts with this prefix (e.g. ``"agent."``).
        """
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._subscribers.append(q)
        try:
            while True:
                event = await q.get()
                if event_prefix and not event.get("event", "").startswith(event_prefix):
                    continue
                yield event
        finally:
            self.unsubscribe(q)

    def unsubscribe(self, q: asyncio.Queue) -> None:
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass


# Module-level singleton
event_bus = EventBus()
