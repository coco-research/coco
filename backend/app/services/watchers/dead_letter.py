"""Dead-letter queue for failed background jobs and ingest tasks.

Phase 10 — `.planning/v3/backend/DESIGN.md` §8 row "Dead-letter retry":
  Retry stuck jobs up to 3x; emit alert on permanent failure.

Storage: `platform.db.dead_letter_queue`.

Lifecycle:
    enqueue(source_task, payload, error)
        → row with status='pending', retry_count=0,
          next_retry_at = now + initial_backoff
    process_due(now, handler)
        for each row with status='pending' and next_retry_at <= now:
            try handler(source_task, payload)
            on success → row status='resolved', last_attempt_at=now
            on failure → retry_count += 1; if retry_count >= max_retries
                         → status='archived' (and an event emitted);
                         else next_retry_at = now + backoff(retry_count)
    archive_permanent(id) — manual archive (operator).
    retry_now(id) — manual replay (admin DLQ endpoint hook).

The handler signature: `(source_task: str, payload: dict) -> None`. Any
raised exception is treated as a retryable failure; the exception's
str() is stored in `error`.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Optional

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Engine

from app.db.tables import dead_letter_queue


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DLQEntry:
    """Read-only view of one dead-letter-queue row."""

    id: str
    source_task: str
    payload: dict[str, Any]
    error: str
    retry_count: int
    status: str
    created_at: str
    next_retry_at: Optional[str]
    last_attempt_at: Optional[str]


# ---------------------------------------------------------------------------
# Backoff schedule
# ---------------------------------------------------------------------------

# Defaults: 1m, 5m, 30m. After 3 attempts → archive.
DEFAULT_BACKOFFS_SEC: tuple[int, ...] = (60, 300, 1800)
DEFAULT_MAX_RETRIES = 3


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


# ---------------------------------------------------------------------------
# DLQ implementation
# ---------------------------------------------------------------------------


class DeadLetterQueue:
    """Persistent retry queue. Engine-backed; no in-memory state."""

    def __init__(
        self,
        engine: Engine,
        *,
        backoffs_sec: Iterable[int] = DEFAULT_BACKOFFS_SEC,
        max_retries: int = DEFAULT_MAX_RETRIES,
        now: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.engine = engine
        self.backoffs_sec: tuple[int, ...] = tuple(backoffs_sec)
        self.max_retries = max_retries
        self._now = now

    # -- internals ---------------------------------------------------------

    def _backoff_delay(self, attempted: int) -> timedelta:
        """Backoff delay AFTER `attempted` total attempts (1-based count)."""
        idx = max(0, min(attempted - 1, len(self.backoffs_sec) - 1))
        return timedelta(seconds=self.backoffs_sec[idx])

    def _row_to_entry(self, row: Any) -> DLQEntry:
        try:
            payload = json.loads(row.payload_json) if row.payload_json else {}
        except (TypeError, ValueError):
            payload = {}
        return DLQEntry(
            id=row.id,
            source_task=row.source_task,
            payload=payload,
            error=row.error or "",
            retry_count=row.retry_count or 0,
            status=row.status or "pending",
            created_at=row.created_at,
            next_retry_at=row.next_retry_at,
            last_attempt_at=row.last_attempt_at,
        )

    # -- public API --------------------------------------------------------

    def enqueue(
        self,
        source_task: str,
        payload: dict[str, Any],
        error: str = "",
    ) -> str:
        """Add a new failed task. Returns the row id."""
        now = self._now()
        next_at = now + self._backoff_delay(1)
        entry_id = str(uuid.uuid4())
        with self.engine.begin() as conn:
            conn.execute(
                insert(dead_letter_queue).values(
                    id=entry_id,
                    source_task=source_task,
                    payload_json=json.dumps(payload, default=str),
                    error=error or "",
                    retry_count=0,
                    status="pending",
                    created_at=_iso(now),
                    next_retry_at=_iso(next_at),
                    last_attempt_at=None,
                )
            )
        return entry_id

    def list_due(self, now: Optional[datetime] = None, limit: int = 50) -> list[DLQEntry]:
        cur = now or self._now()
        stmt = (
            select(dead_letter_queue)
            .where(dead_letter_queue.c.status == "pending")
            .where(dead_letter_queue.c.next_retry_at <= _iso(cur))
            .order_by(dead_letter_queue.c.next_retry_at.asc())
            .limit(limit)
        )
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def list_all(self, status: Optional[str] = None, limit: int = 200) -> list[DLQEntry]:
        stmt = select(dead_letter_queue)
        if status:
            stmt = stmt.where(dead_letter_queue.c.status == status)
        stmt = stmt.order_by(dead_letter_queue.c.created_at.desc()).limit(limit)
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
        return [self._row_to_entry(r) for r in rows]

    def get(self, entry_id: str) -> Optional[DLQEntry]:
        stmt = select(dead_letter_queue).where(dead_letter_queue.c.id == entry_id)
        with self.engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
        return self._row_to_entry(row) if row else None

    def mark_resolved(self, entry_id: str) -> None:
        now = self._now()
        with self.engine.begin() as conn:
            conn.execute(
                update(dead_letter_queue)
                .where(dead_letter_queue.c.id == entry_id)
                .values(
                    status="resolved",
                    last_attempt_at=_iso(now),
                    next_retry_at=None,
                )
            )

    def mark_archived(self, entry_id: str, error: Optional[str] = None) -> None:
        now = self._now()
        values: dict[str, Any] = {
            "status": "archived",
            "last_attempt_at": _iso(now),
            "next_retry_at": None,
        }
        if error is not None:
            values["error"] = error
        with self.engine.begin() as conn:
            conn.execute(
                update(dead_letter_queue)
                .where(dead_letter_queue.c.id == entry_id)
                .values(**values)
            )

    def _record_failure(
        self,
        entry: DLQEntry,
        err: str,
    ) -> tuple[str, int]:
        """Update row after a failed attempt. Returns (new_status, new_retry_count)."""
        now = self._now()
        new_count = entry.retry_count + 1
        if new_count >= self.max_retries:
            new_status = "archived"
            next_at: Optional[str] = None
        else:
            new_status = "pending"
            next_at = _iso(now + self._backoff_delay(new_count + 1))
        with self.engine.begin() as conn:
            conn.execute(
                update(dead_letter_queue)
                .where(dead_letter_queue.c.id == entry.id)
                .values(
                    retry_count=new_count,
                    error=err,
                    status=new_status,
                    last_attempt_at=_iso(now),
                    next_retry_at=next_at,
                )
            )
        return new_status, new_count

    def retry_now(self, entry_id: str) -> bool:
        """Move next_retry_at to now so the entry is picked up next sweep."""
        entry = self.get(entry_id)
        if not entry or entry.status != "pending":
            return False
        with self.engine.begin() as conn:
            conn.execute(
                update(dead_letter_queue)
                .where(dead_letter_queue.c.id == entry_id)
                .values(next_retry_at=_iso(self._now()))
            )
        return True

    def process_due(
        self,
        handler: Callable[[str, dict[str, Any]], None],
        *,
        now: Optional[datetime] = None,
        limit: int = 50,
    ) -> dict[str, int]:
        """Drive one retry sweep. Returns counters for tests/metrics."""
        due = self.list_due(now=now, limit=limit)
        resolved = 0
        failed = 0
        archived = 0
        for entry in due:
            try:
                handler(entry.source_task, entry.payload)
            except Exception as exc:  # noqa: BLE001 — all handler errors are retryable
                new_status, _ = self._record_failure(entry, str(exc))
                failed += 1
                if new_status == "archived":
                    archived += 1
            else:
                self.mark_resolved(entry.id)
                resolved += 1
        return {
            "processed": len(due),
            "resolved": resolved,
            "failed": failed,
            "archived": archived,
        }
