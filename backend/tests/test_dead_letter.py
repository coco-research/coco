"""Tests for the dead-letter queue (Phase 10).

The DLQ is engine-backed; tests use an in-memory SQLite engine with the
`dead_letter_queue` table created directly via metadata, so no Alembic
machinery is required in the test path.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from sqlalchemy import create_engine, MetaData
from sqlalchemy.engine import Engine

from app.db.tables import dead_letter_queue
from app.services.watchers.dead_letter import (
    DEFAULT_BACKOFFS_SEC,
    DLQEntry,
    DeadLetterQueue,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine() -> Engine:
    """Fresh in-memory SQLite engine with only the DLQ table created."""
    eng = create_engine("sqlite:///:memory:")
    # Create *only* the dead_letter_queue table to avoid pulling unrelated
    # CREATE TABLEs (and their indexes referenced elsewhere) into memory.
    md = MetaData()
    dlq_clone = dead_letter_queue.to_metadata(md)  # noqa: F841 — registers on md
    md.create_all(eng)
    return eng


class _FrozenClock:
    """Deterministic clock for backoff testing."""

    def __init__(self, start: datetime) -> None:
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now = self.now + timedelta(seconds=seconds)


@pytest.fixture()
def clock() -> _FrozenClock:
    return _FrozenClock(datetime(2026, 5, 27, 12, 0, 0, tzinfo=timezone.utc))


@pytest.fixture()
def dlq(engine: Engine, clock: _FrozenClock) -> DeadLetterQueue:
    return DeadLetterQueue(engine, now=clock)


# ---------------------------------------------------------------------------
# 1. Enqueue creates a pending row with scheduled retry
# ---------------------------------------------------------------------------


def test_enqueue_creates_pending_row_with_backoff(
    dlq: DeadLetterQueue, clock: _FrozenClock
) -> None:
    entry_id = dlq.enqueue(
        source_task="file_watcher.hxstore",
        payload={"path": "/tmp/HxStore.hxd"},
        error="upstream 500",
    )

    entry = dlq.get(entry_id)
    assert entry is not None
    assert entry.source_task == "file_watcher.hxstore"
    assert entry.payload == {"path": "/tmp/HxStore.hxd"}
    assert entry.error == "upstream 500"
    assert entry.retry_count == 0
    assert entry.status == "pending"

    # next_retry_at = created + first backoff (60s by default)
    assert entry.next_retry_at is not None
    expected = (clock.now + timedelta(seconds=DEFAULT_BACKOFFS_SEC[0])).replace(
        microsecond=0
    ).isoformat()
    assert entry.next_retry_at == expected


# ---------------------------------------------------------------------------
# 2. list_due only returns rows whose next_retry_at <= now
# ---------------------------------------------------------------------------


def test_list_due_respects_next_retry_at(
    dlq: DeadLetterQueue, clock: _FrozenClock
) -> None:
    id_a = dlq.enqueue("task.a", {"v": 1}, "err-a")  # next_retry = now+60s
    id_b = dlq.enqueue("task.b", {"v": 2}, "err-b")

    # Initially nothing is due (backoff is 60s).
    assert dlq.list_due() == []

    # Advance past first backoff window.
    clock.advance(120)
    due = dlq.list_due()
    due_ids = {e.id for e in due}
    assert id_a in due_ids and id_b in due_ids


# ---------------------------------------------------------------------------
# 3. process_due — success path
# ---------------------------------------------------------------------------


def test_process_due_marks_handled_rows_resolved(
    dlq: DeadLetterQueue, clock: _FrozenClock
) -> None:
    id1 = dlq.enqueue("task.ok", {"k": 1}, "transient")
    clock.advance(120)

    received: list[tuple[str, dict[str, Any]]] = []

    def handler(source_task: str, payload: dict[str, Any]) -> None:
        received.append((source_task, payload))

    counters = dlq.process_due(handler)

    assert counters == {"processed": 1, "resolved": 1, "failed": 0, "archived": 0}
    assert received == [("task.ok", {"k": 1})]

    entry = dlq.get(id1)
    assert entry is not None
    assert entry.status == "resolved"
    assert entry.next_retry_at is None
    assert entry.last_attempt_at is not None


# ---------------------------------------------------------------------------
# 4. process_due — failure path schedules retry with backoff
# ---------------------------------------------------------------------------


def test_process_due_failure_increments_retry_and_reschedules(
    dlq: DeadLetterQueue, clock: _FrozenClock
) -> None:
    entry_id = dlq.enqueue("task.flaky", {"k": 1}, "initial")
    clock.advance(120)

    def bad_handler(*_: Any) -> None:
        raise RuntimeError("still flaky")

    counters = dlq.process_due(bad_handler)
    assert counters == {"processed": 1, "resolved": 0, "failed": 1, "archived": 0}

    entry = dlq.get(entry_id)
    assert entry is not None
    assert entry.status == "pending"
    assert entry.retry_count == 1
    assert entry.error == "still flaky"
    # Second backoff = DEFAULT_BACKOFFS_SEC[1] (300s) from the failure time.
    expected = (clock.now + timedelta(seconds=DEFAULT_BACKOFFS_SEC[1])).replace(
        microsecond=0
    ).isoformat()
    assert entry.next_retry_at == expected


# ---------------------------------------------------------------------------
# 5. max retries → archived
# ---------------------------------------------------------------------------


def test_repeated_failure_archives_after_max_retries(
    dlq: DeadLetterQueue, clock: _FrozenClock
) -> None:
    entry_id = dlq.enqueue("task.doomed", {"k": 1}, "first")

    def bad_handler(*_: Any) -> None:
        raise RuntimeError("nope")

    archived_seen = False
    # Loop until either archived or we exceed retry budget. Each iteration
    # advances past the row's scheduled next_retry_at.
    for _ in range(dlq.max_retries + 2):
        # Jump far enough that the next_retry_at is in the past.
        clock.advance(3600)
        counters = dlq.process_due(bad_handler)
        if counters["archived"]:
            archived_seen = True
            break

    assert archived_seen, "expected the row to be archived within max_retries"
    entry = dlq.get(entry_id)
    assert entry is not None
    assert entry.status == "archived"
    assert entry.retry_count == dlq.max_retries
    assert entry.next_retry_at is None


# ---------------------------------------------------------------------------
# 6. retry_now and listing
# ---------------------------------------------------------------------------


def test_retry_now_brings_due_time_forward(
    dlq: DeadLetterQueue, clock: _FrozenClock
) -> None:
    entry_id = dlq.enqueue("task.x", {"k": 1}, "")
    # Not yet due
    assert dlq.list_due() == []

    assert dlq.retry_now(entry_id) is True
    due = dlq.list_due()
    assert len(due) == 1 and due[0].id == entry_id


def test_list_all_filters_by_status(dlq: DeadLetterQueue) -> None:
    a = dlq.enqueue("t.a", {}, "")
    b = dlq.enqueue("t.b", {}, "")
    dlq.mark_resolved(a)
    dlq.mark_archived(b, error="manual archive")

    all_rows = dlq.list_all()
    assert {r.id for r in all_rows} == {a, b}

    resolved = dlq.list_all(status="resolved")
    archived = dlq.list_all(status="archived")
    assert [r.id for r in resolved] == [a]
    assert [r.id for r in archived] == [b]
    assert next(r for r in archived if r.id == b).error == "manual archive"


# ---------------------------------------------------------------------------
# 7. retry_now is a no-op for non-pending rows
# ---------------------------------------------------------------------------


def test_retry_now_returns_false_for_archived_row(dlq: DeadLetterQueue) -> None:
    entry_id = dlq.enqueue("task.x", {"k": 1}, "")
    dlq.mark_archived(entry_id)

    assert dlq.retry_now(entry_id) is False
    entry = dlq.get(entry_id)
    assert entry is not None and entry.status == "archived"


# ---------------------------------------------------------------------------
# 8. Empty sweep returns zero counters cleanly
# ---------------------------------------------------------------------------


def test_process_due_with_no_rows_returns_zero_counters(dlq: DeadLetterQueue) -> None:
    def never_called(*_: Any) -> None:
        raise AssertionError("handler should not be called")

    counters = dlq.process_due(never_called)
    assert counters == {"processed": 0, "resolved": 0, "failed": 0, "archived": 0}


# ---------------------------------------------------------------------------
# 9. DLQEntry payload survives JSON round-trip
# ---------------------------------------------------------------------------


def test_payload_json_roundtrips_nested_dict(dlq: DeadLetterQueue) -> None:
    payload = {
        "source": "hxstore",
        "path": "/Users/me/x.hxd",
        "extra": {"size": 1234, "tags": ["a", "b"]},
    }
    entry_id = dlq.enqueue("file_watcher.hxstore", payload, "err")
    entry = dlq.get(entry_id)
    assert entry is not None
    assert entry.payload == payload
    assert isinstance(entry, DLQEntry)
