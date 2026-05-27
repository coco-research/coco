"""GAP M9 — todo_dependencies join table with UNIQUE(blocker_id, blocked_id).

Revision ID: 003
Revises: 002
Create Date: 2026-05-26

The table already exists in init_db.py SCHEMA with semantically equivalent
columns (todo_id = blocked, depends_on = blocker). This migration:
  1. Ensures the table exists (IF NOT EXISTS) for environments bootstrapped
     before todo_dependencies was added to the baseline.
  2. Ensures the UNIQUE(todo_id, depends_on) constraint exists by recreating
     the table with the constraint if missing (no-op on conforming DBs).

A hard FOREIGN KEY is not added because a todo may live in either
hub_todos (read-only mirror) or todo_overrides (platform-native) — there is
no single parent table. Referential integrity is enforced in the application
layer via _get_todo_by_id() before INSERT.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CREATE_SQL = """
CREATE TABLE IF NOT EXISTS todo_dependencies (
    id TEXT PRIMARY KEY,
    todo_id TEXT NOT NULL,
    depends_on TEXT NOT NULL,
    dep_type TEXT NOT NULL DEFAULT 'blocked_by' CHECK(dep_type IN ('blocked_by', 'related_to')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(todo_id, depends_on)
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_todo_deps_todo ON todo_dependencies(todo_id)",
    "CREATE INDEX IF NOT EXISTS idx_todo_deps_dep ON todo_dependencies(depends_on)",
]


def _has_unique_constraint(conn) -> bool:
    """Check whether todo_dependencies has UNIQUE(todo_id, depends_on)."""
    rows = conn.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='todo_dependencies'"
    ).fetchall()
    if not rows:
        return False
    sql = (rows[0][0] or "").lower()
    # The exact tokens we expect somewhere in the CREATE TABLE statement.
    return "unique" in sql and "todo_id" in sql and "depends_on" in sql


def upgrade() -> None:
    op.execute(CREATE_SQL)
    for idx in CREATE_INDEXES:
        op.execute(idx)

    bind = op.get_bind()
    if not _has_unique_constraint(bind):
        # Recreate with constraint, preserving data.
        op.execute("ALTER TABLE todo_dependencies RENAME TO todo_dependencies_old")
        op.execute(CREATE_SQL)
        op.execute(
            "INSERT OR IGNORE INTO todo_dependencies (id, todo_id, depends_on, dep_type, created_at) "
            "SELECT id, todo_id, depends_on, dep_type, created_at FROM todo_dependencies_old"
        )
        op.execute("DROP TABLE todo_dependencies_old")
        for idx in CREATE_INDEXES:
            op.execute(idx)


def downgrade() -> None:
    # We do not drop the table on downgrade — data loss risk.
    pass
