"""Phase 10 — dead_letter_queue table

Adds the dead-letter queue table used by file-watcher and background-job
failure handling.  Failed tasks are enqueued here, retried up to
`max_retries` times with exponential backoff, then archived for operator
review.

Revision ID: 006_dead_letter_queue
Revises: 005
Create Date: 2026-05-27
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_dead_letter_queue"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id TEXT PRIMARY KEY,
    source_task TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    error TEXT NOT NULL DEFAULT '',
    retry_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    next_retry_at TEXT,
    last_attempt_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_dlq_status_next_retry
    ON dead_letter_queue(status, next_retry_at);

CREATE INDEX IF NOT EXISTS idx_dlq_source_task
    ON dead_letter_queue(source_task);
"""


def upgrade() -> None:
    for stmt in SCHEMA.strip().split(";\n"):
        stmt = stmt.strip()
        if stmt:
            op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_dlq_source_task")
    op.execute("DROP INDEX IF EXISTS idx_dlq_status_next_retry")
    op.execute("DROP TABLE IF EXISTS dead_letter_queue")
