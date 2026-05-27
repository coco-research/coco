"""Tests for QueueService (≥8 required) — ported from V3 REFERENCE-IMPL.

Covers:
 1. enqueue creates pending item
 2. dequeue returns highest-priority pending and marks approved
 3. persistence across restart (new JsonStore reads same file)
 4. idempotency: replay returns same result
 5. idempotency: mismatched body raises IdempotencyConflict
 6. race for same item — second writer with same idem key replays
 7. backpressure: MAX_QUEUE_SIZE enforced
 8. cancel marks status cancelled
 9. replay returns last result
10. malformed payload (torn file) raises TornFileDetected
11. concurrent writers — merge_from_external is additive
12. defer sets deferred_until
13. unknown id raises ItemNotFound
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.queue_service import (
    IdempotencyConflict,
    IdempotencyReplay,
    ItemNotFound,
    JsonStore,
    QueueFull,
    QueueService,
    TornFileDetected,
)


# ---------------------------------------------------------------------------
# Fixtures (kept local so tests run without a top-level conftest)
# ---------------------------------------------------------------------------

@pytest.fixture()
def queue_file(tmp_path: Path) -> Path:
    """A pristine queue.json path (file does not yet exist)."""
    d = tmp_path / "coco"
    d.mkdir(parents=True, exist_ok=True)
    return d / "queue.json"


@pytest.fixture()
def svc(queue_file: Path) -> QueueService:
    return QueueService(JsonStore(queue_file), max_size=100)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_enqueue_creates_pending_item(svc):
    item = svc.enqueue(project_id="P", kind="decision_request",
                       summary="Approve Slack reply?", priority=7)
    items, _ = svc.list()
    assert len(items) == 1
    assert items[0].id == item.id
    assert items[0].status == "pending"
    assert items[0].priority == 7


def test_dequeue_returns_highest_priority(svc):
    low = svc.enqueue(project_id="P", kind="k", summary="low", priority=1)
    high = svc.enqueue(project_id="P", kind="k", summary="high", priority=9)
    popped = svc.dequeue()
    assert popped is not None
    assert popped.id == high.id
    assert popped.status == "approved"
    # Subsequent dequeue picks the next pending
    nxt = svc.dequeue()
    assert nxt is not None
    assert nxt.id == low.id


def test_persistence_across_restart(svc, queue_file):
    item = svc.enqueue(project_id="P", kind="k", summary="s", priority=5)
    # New service instance pointing at same file
    svc2 = QueueService(JsonStore(queue_file))
    items, _ = svc2.list()
    assert len(items) == 1
    assert items[0].id == item.id


def test_idempotency_replay_returns_same_result(svc):
    item = svc.enqueue(project_id="P", kind="k", summary="s")
    r1 = svc.approve(item.id, idem_key="K-1")
    # Same idem key, no other body diff
    with pytest.raises(IdempotencyReplay) as ei:
        svc.approve(item.id, idem_key="K-1")
    assert ei.value.result == r1


def test_idempotency_mismatched_body_conflict(svc):
    item = svc.enqueue(project_id="P", kind="k", summary="s")
    svc.defer(item.id, until="2026-05-28T09:00:00Z", idem_key="K-2")
    # Reuse same key with a different "until" value → conflict
    with pytest.raises(IdempotencyConflict):
        svc.defer(item.id, until="2026-05-29T09:00:00Z", idem_key="K-2")


def test_race_for_same_item_first_wins(svc):
    """Two callers approve the same item; the second sees an already-approved state."""
    item = svc.enqueue(project_id="P", kind="k", summary="s")
    r1 = svc.approve(item.id, idem_key="K-A")
    # Without idem key, second approve is a no-op state transition but succeeds
    r2 = svc.approve(item.id)
    assert r1["status"] == "approved"
    assert r2["status"] == "approved"
    # With same idem key, second is a replay
    with pytest.raises(IdempotencyReplay):
        svc.approve(item.id, idem_key="K-A")


def test_backpressure_max_size(queue_file):
    svc_small = QueueService(JsonStore(queue_file), max_size=3)
    svc_small.enqueue(project_id="P", kind="k", summary="1")
    svc_small.enqueue(project_id="P", kind="k", summary="2")
    svc_small.enqueue(project_id="P", kind="k", summary="3")
    with pytest.raises(QueueFull):
        svc_small.enqueue(project_id="P", kind="k", summary="4")


def test_cancel_marks_cancelled(svc):
    item = svc.enqueue(project_id="P", kind="k", summary="s")
    r = svc.cancel(item.id)
    assert r["status"] == "cancelled"
    items, _ = svc.list(status="cancelled")
    assert any(it.id == item.id for it in items)


def test_replay_returns_last_result(svc):
    item = svc.enqueue(project_id="P", kind="k", summary="s")
    svc.reject(item.id, reason="not now", idem_key="K-R")
    last = svc.replay(item.id)
    assert last is not None
    assert last["status"] == "rejected"


def test_torn_file_detected(queue_file):
    """A corrupted queue.json triggers TornFileDetected on read."""
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    queue_file.write_text("{ not valid json")
    svc = QueueService(JsonStore(queue_file))
    with pytest.raises(TornFileDetected):
        svc.list()


def test_concurrent_writers_merge_additive(svc):
    """External producer (think.py) appends via merge_from_external; only NEW ids added."""
    item = svc.enqueue(project_id="P", kind="k", summary="exists")
    external = [
        {"id": item.id, "project_id": "P", "kind": "k", "summary": "DUP", "status": "pending"},
        {"id": "B" * 26, "project_id": "P", "kind": "k", "summary": "fresh1", "status": "pending"},
        {"id": "C" * 26, "project_id": "P", "kind": "k", "summary": "fresh2", "status": "pending"},
    ]
    added = svc.merge_from_external(external)
    assert added == 2
    items, _ = svc.list()
    summaries = {it.summary for it in items}
    # Existing item preserved (not overwritten)
    assert "exists" in summaries
    assert "DUP" not in summaries
    assert "fresh1" in summaries
    assert "fresh2" in summaries


def test_defer_sets_deferred_until(svc):
    item = svc.enqueue(project_id="P", kind="k", summary="s")
    r = svc.defer(item.id, until="2026-05-28T09:00:00Z")
    assert r["status"] == "deferred"
    assert r["deferred_until"] == "2026-05-28T09:00:00Z"


def test_item_not_found_on_unknown_id(svc):
    with pytest.raises(ItemNotFound):
        svc.approve("NOT-AN-ID")
