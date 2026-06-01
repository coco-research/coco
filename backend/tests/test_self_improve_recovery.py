"""Regression tests for the self-improve cycle robustness fixes.

Covers three bugs found when cycle 9faac75d wedged in 'planning' for 24 days
having spawned 0 agents, produced 0 improvements, and leaked the lock file:

  Patch 1 (start_cycle): the PM-prompt build + first agent spawn ran OUTSIDE
    the lock-guarded try/except, so any throw wedged the cycle in 'planning'
    forever, leaked the lock, and recorded no error. Now guarded -> the cycle
    is marked 'failed' with the error and the lock is released.

  Patch 2 (_spawn_squad_agent): an explicit db.commit() between the two INSERTs
    made the agents row and its self_improve_agents link non-atomic, allowing
    an orphan agents row with no cycle link. Now a single get_db() transaction
    writes both atomically.

  Patch 3 (recover_interrupted_cycles): nothing previously reconciled a cycle
    left mid-flight by a crash/restart. Now startup fails such cycles (but
    preserves 'awaiting_approval', which legitimately waits for a human).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.services import self_improve as si
from app.services.self_improve import SelfImproveService
from app.db.session import get_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _insert_cycle(cycle_id: str, status: str = "planning", error: str = "") -> None:
    with get_db() as db:
        db.exec_driver_sql(
            "INSERT INTO self_improve_cycles "
            "(id, status, budget_usd, spent_usd, max_improvements, error, started_at, created_at) "
            "VALUES (?, ?, 5.0, 0.0, 5, ?, ?, ?)",
            (cycle_id, status, error, _now(), _now()),
        )


@pytest.fixture()
def hermetic(monkeypatch):
    """Neutralize host-touching side effects (lock file, git, events)."""
    released = {"count": 0}
    monkeypatch.setattr(si, "_acquire_lock", lambda: True)
    monkeypatch.setattr(si, "_check_disk_space", lambda *a, **k: True)
    monkeypatch.setattr(si, "cleanup_stale_worktrees", lambda *a, **k: None)

    def _fake_release():
        released["count"] += 1

    monkeypatch.setattr(si, "_release_lock", _fake_release)
    monkeypatch.setattr(si.event_bus, "emit", lambda *a, **k: None)
    return released


# ---------------------------------------------------------------------------
# Patch 1 — start_cycle no longer wedges on spawn failure
# ---------------------------------------------------------------------------

def test_start_cycle_spawn_failure_fails_cycle_and_releases_lock(fresh_db, hermetic, monkeypatch):
    monkeypatch.setattr(
        si.process_manager, "spawn",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("claude not found")),
    )
    svc = SelfImproveService()

    with pytest.raises(RuntimeError):
        svc.start_cycle(budget_usd=5.0, max_improvements=3, focus_areas=None)

    # Cycle must be 'failed' with the error recorded -- NOT stuck in 'planning'.
    with get_db() as db:
        rows = db.exec_driver_sql(
            "SELECT status, error, completed_at FROM self_improve_cycles"
        ).fetchall()
    assert len(rows) == 1
    row = rows[0]._mapping
    assert row["status"] == "failed"
    assert "Failed to spawn PM agent" in (row["error"] or "")
    assert row["completed_at"]

    # Lock released and in-memory active state cleared (recoverable).
    assert hermetic["count"] >= 1
    assert svc._active_cycle_id is None


# ---------------------------------------------------------------------------
# Patch 2 — agents + self_improve_agents written atomically
# ---------------------------------------------------------------------------

def test_spawn_squad_agent_writes_both_rows_atomically(fresh_db, hermetic, monkeypatch):
    monkeypatch.setattr(si.process_manager, "spawn", lambda *a, **k: 4321)
    svc = SelfImproveService()
    _insert_cycle("cyc-1", status="planning")

    agent_id = svc._spawn_squad_agent("cyc-1", "pm", "do the thing")

    with get_db() as db:
        a = db.exec_driver_sql(
            "SELECT pid, role FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        link = db.exec_driver_sql(
            "SELECT COUNT(*) AS n FROM self_improve_agents WHERE cycle_id = ? AND agent_id = ?",
            ("cyc-1", agent_id),
        ).fetchone()

    assert a is not None and a._mapping["role"] == "self-improve-pm"
    assert a._mapping["pid"] == 4321
    # The link row exists -> both inserts committed together (no orphan).
    assert link._mapping["n"] == 1


# ---------------------------------------------------------------------------
# Patch 3 — crash recovery fails interrupted cycles, spares awaiting_approval
# ---------------------------------------------------------------------------

def test_recover_interrupted_cycles(fresh_db, hermetic):
    _insert_cycle("c-planning", status="planning")
    _insert_cycle("c-developing", status="developing")
    _insert_cycle("c-await", status="awaiting_approval")
    _insert_cycle("c-done", status="completed")

    svc = SelfImproveService()
    recovered = svc.recover_interrupted_cycles()

    assert recovered == 2  # only the two processing states
    with get_db() as db:
        statuses = {
            r._mapping["id"]: (r._mapping["status"], r._mapping["error"])
            for r in db.exec_driver_sql(
                "SELECT id, status, error FROM self_improve_cycles"
            ).fetchall()
        }

    assert statuses["c-planning"][0] == "failed"
    assert "Interrupted by restart" in (statuses["c-planning"][1] or "")
    assert statuses["c-developing"][0] == "failed"
    # Human gate + terminal states are preserved.
    assert statuses["c-await"][0] == "awaiting_approval"
    assert statuses["c-done"][0] == "completed"
    # Lock released because cycles were recovered.
    assert hermetic["count"] >= 1


def test_recover_interrupted_cycles_noop_when_clean(fresh_db, hermetic):
    _insert_cycle("c-await", status="awaiting_approval")
    _insert_cycle("c-done", status="completed")
    svc = SelfImproveService()
    assert svc.recover_interrupted_cycles() == 0
