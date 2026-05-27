"""Phase 11 — audit_log table for destructive actions.

Revision ID: 008_audit_log
Revises: 007_brain_merge_log
Create Date: 2026-05-27

Note: Re-chained from 001 to 007_brain_merge_log when reconciling main into
merge/wave-3 — the linear chain now is 001 -> 002 -> 003 -> 004 -> 005 ->
006_dead_letter_queue -> 140054f726ca -> 007_brain_merge_log -> 008_audit_log.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_audit_log"
down_revision: Union[str, None] = "007_brain_merge_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

AUDIT_LOG_DDL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'user',
    payload_hash TEXT,
    occurred_at TEXT NOT NULL DEFAULT (datetime('now')),
    ip TEXT
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)",
    "CREATE INDEX IF NOT EXISTS idx_audit_log_occurred ON audit_log(occurred_at)",
    "CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log(actor)",
]


def upgrade() -> None:
    op.execute(AUDIT_LOG_DDL)
    for idx in INDEXES:
        op.execute(idx)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_log")
