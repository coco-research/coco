"""Add agent_tasks table for inter-agent delegation.

Revision ID: 004
Revises: 003
Create Date: 2026-05-26

Schema must stay in sync with backend/app/db/init_db.py SCHEMA.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


AGENT_TASKS_DDL = """
CREATE TABLE IF NOT EXISTS agent_tasks (
    id TEXT PRIMARY KEY,
    from_agent_id TEXT REFERENCES agents(id),
    to_agent_id TEXT NOT NULL REFERENCES agents(id),
    prompt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','claimed','done','failed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    claimed_at TEXT,
    completed_at TEXT,
    result TEXT
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_agent_tasks_to_status ON agent_tasks(to_agent_id, status);",
    "CREATE INDEX IF NOT EXISTS idx_agent_tasks_from ON agent_tasks(from_agent_id);",
]


def upgrade() -> None:
    op.execute(AGENT_TASKS_DDL)
    for idx in INDEXES:
        op.execute(idx)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agent_tasks")
