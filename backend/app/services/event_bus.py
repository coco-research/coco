"""In-process async event bus for broadcasting real-time events to SSE subscribers.

Events are persisted to the ``events`` table in platform.db so that SSE clients
can replay missed events after a reconnection.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator

import structlog

from app.config import PLATFORM_DB_PATH

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(PLATFORM_DB_PATH), timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=3000")
    return conn


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------

class EventBus:
    """Async broadcast bus with SQLite persistence for replay."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue] = []

    # -- persistence helpers (fire-and-forget, never block emit) ----------

    def _persist(self, event_type: str, data_json: str) -> None:
        """Write event to DB. Called synchronously; errors are swallowed."""
        try:
            conn = _get_conn()
            try:
                conn.execute(
                    "INSERT INTO events (event_type, data_json, created_at) VALUES (?, ?, ?)",
                    (event_type, data_json, _iso_now()),
                )
                conn.commit()
            finally:
                conn.close()
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

    def replay(self, since: str) -> list[dict]:
        """Return persisted events created after *since* (ISO-8601 timestamp).

        Returns a list of SSE-ready dicts: ``{"event": ..., "data": ...}``.
        """
        try:
            conn = _get_conn()
            try:
                rows = conn.execute(
                    "SELECT event_type, data_json FROM events "
                    "WHERE created_at > ? ORDER BY id ASC",
                    (since,),
                ).fetchall()
                return [{"event": r["event_type"], "data": r["data_json"]} for r in rows]
            finally:
                conn.close()
        except Exception as exc:
            log.warning("event_replay_failed", since=since, error=str(exc))
            return []

    def cleanup(self, max_age_hours: int = 24) -> int:
        """Delete events older than *max_age_hours*. Returns deleted count."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        try:
            conn = _get_conn()
            try:
                cur = conn.execute("DELETE FROM events WHERE created_at < ?", (cutoff,))
                conn.commit()
                deleted = cur.rowcount
                if deleted:
                    log.info("events_cleaned_up", deleted=deleted, cutoff=cutoff)
                return deleted
            finally:
                conn.close()
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
