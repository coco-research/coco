"""Wave 0.2 schema reconcile: insights, verification_results, tasks.

Revision ID: 010_wave02_schema_reconcile
Revises: 009_widen_cost_ledger_source
Create Date: 2026-06-01

Reconciles three tables on existing platform.db installs to match db/tables.py
(the create_all source of truth), fixing silent write failures:

  #4 insights            -- add metadata_json + updated_at columns the engine
                            writes (CompileError / NOT NULL on every cycle).
  #5 verification_results -- live table used the legacy models.py schema
                            (gate_name/passed/score); rebuild to the new schema
                            (gate/verdict/checks_json/...) the service inserts.
                            Live table has 0 rows, so no data is lost.
  #10 tasks              -- drop the stale status CHECK that rejected the board
                            states the router emits (backlog/todo/in_review/
                            archived); the app's TASK_STATES governs instead.

All steps are idempotent and committed explicitly (SQLite non-transactional DDL).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "010_wave02_schema_reconcile"
down_revision: Union[str, None] = "009_widen_cost_ledger_source"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(bind, table: str, column: str) -> bool:
    rows = bind.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


_VR_NEW = """
    CREATE TABLE verification_results (
        id TEXT PRIMARY KEY,
        gate TEXT NOT NULL,
        verdict TEXT NOT NULL,
        checks_json TEXT,
        summary TEXT,
        node_id TEXT,
        entity_type TEXT,
        entity_id TEXT,
        retry_count INTEGER DEFAULT 0,
        budget_spent_usd REAL DEFAULT 0.0,
        run_at TEXT NOT NULL,
        duration_ms INTEGER DEFAULT 0
    );
"""

_TASKS_COLS = (
    "id, title, description, agent_id, project_id, status, priority, "
    "checked_out_by, checked_out_at, created_at, updated_at, node_id, "
    "delegated_by, delegated_to, parent_task_id, context_json"
)

_TASKS_NEW = """
    CREATE TABLE tasks_new (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        agent_id TEXT REFERENCES "agents"(id),
        project_id TEXT,
        status TEXT NOT NULL DEFAULT 'open',
        priority TEXT DEFAULT 'medium' CHECK(priority IN ('high','medium','low')),
        checked_out_by TEXT,
        checked_out_at TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        node_id TEXT,
        delegated_by TEXT,
        delegated_to TEXT,
        parent_task_id TEXT,
        context_json TEXT DEFAULT '{}'
    );
"""

_TASKS_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_node ON tasks(node_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_delegated_to ON tasks(delegated_to)",
)


def upgrade() -> None:
    bind = op.get_bind()

    # #4 insights: add the columns the engine writes.
    if not _has_column(bind, "insights", "metadata_json"):
        bind.exec_driver_sql("ALTER TABLE insights ADD COLUMN metadata_json TEXT DEFAULT '{}'")
    if not _has_column(bind, "insights", "updated_at"):
        bind.exec_driver_sql("ALTER TABLE insights ADD COLUMN updated_at TEXT")

    # #5 verification_results: rebuild legacy schema -> new schema (0 rows live).
    bind.exec_driver_sql("DROP TABLE IF EXISTS verification_results")
    bind.exec_driver_sql(_VR_NEW)
    bind.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_vr_gate ON verification_results(gate)")
    bind.exec_driver_sql(
        "CREATE INDEX IF NOT EXISTS idx_vr_entity ON verification_results(entity_type, entity_id)"
    )

    # #10 tasks: drop the stale status CHECK (recreate-table), preserve rows.
    bind.exec_driver_sql("DROP TABLE IF EXISTS tasks_new")
    bind.exec_driver_sql(_TASKS_NEW)
    bind.exec_driver_sql(
        f"INSERT INTO tasks_new ({_TASKS_COLS}) SELECT {_TASKS_COLS} FROM tasks"
    )
    bind.exec_driver_sql("DROP TABLE tasks")
    bind.exec_driver_sql("ALTER TABLE tasks_new RENAME TO tasks")
    for stmt in _TASKS_INDEXES:
        bind.exec_driver_sql(stmt)

    bind.commit()


def downgrade() -> None:
    # Non-reversible in practice (would reinstate broken CHECK / drop columns).
    # Left as a no-op to avoid re-breaking the write plane.
    pass
