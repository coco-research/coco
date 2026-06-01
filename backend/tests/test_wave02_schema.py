"""Wave 0.2 schema-reconcile regression tests (Track 0).

  #4  insights  -- table accepts metadata_json/updated_at/sources the engine writes
  #5  verification_results -- new schema (gate/verdict/checks_json) + get_history JOIN runs
  #10 tasks     -- accepts the board states the router emits (no stale status CHECK)

#5 and #10 are live-migration fixes (fresh create_all DBs already match tables.py);
these tests guard the canonical schema + the JOIN, and migration 010 reconciles
the live DB (verified separately).
"""

from __future__ import annotations

import pytest

from app.db.session import get_db


def _count(table: str, where: str = "", params: tuple = ()) -> int:
    with get_db() as db:
        return db.exec_driver_sql(
            f"SELECT COUNT(*) AS c FROM {table} {where}", params
        ).fetchone()._mapping["c"]


# #4 — insights accepts the engine's columns (RED before tables.py gained
# metadata_json/updated_at: CompileError on unknown columns).
def test_insights_table_accepts_engine_columns(fresh_db):
    from app.db.tables import insights
    with get_db() as db:
        db.execute(
            insights.insert().values(
                id="i1", insight_type="cross_ref", title="t", description="d",
                confidence=0.7, entity_ids="[]", content_ids="[]", sources="[]",
                status="new", metadata_json='{"k":1}',
                created_at="2026-06-01", updated_at="2026-06-01",
            )
        )
    assert _count("insights", "WHERE id = ?", ("i1",)) == 1


# #5 — verification_results new schema + get_history JOIN on vr.gate runs clean.
def test_verification_results_new_schema_and_history(fresh_db):
    from app.db.tables import verification_results
    from app.services.verification import verification_service
    with get_db() as db:
        db.execute(
            verification_results.insert().values(
                id="v1", gate="ideation", verdict="pass", checks_json="[]",
                summary="ok", run_at="2026-06-01",
            )
        )
    assert _count("verification_results", "WHERE gate = ?", ("ideation",)) == 1
    hist = verification_service.get_history()  # JOINs on vr.gate — must not raise
    assert isinstance(hist, list)


# #10 — tasks accepts every router board state (no blocking status CHECK).
@pytest.mark.parametrize("state", ["backlog", "todo", "in_progress", "in_review", "done", "archived"])
def test_tasks_accepts_board_states(fresh_db, state):
    from app.db.tables import tasks
    with get_db() as db:
        db.execute(
            tasks.insert().values(
                id=f"t-{state}", title="x", status=state,
                created_at="2026-06-01", updated_at="2026-06-01",
            )
        )
    assert _count("tasks", "WHERE status = ?", (state,)) == 1
