"""Phase 11 — brain B4: brain_merge_log table

Adds the operational merge log used by the graph-ops repair tooling
(detect / repair / undo). Distinct from `brain_merge_audit` (B0):

  - `brain_merge_audit`   forever record of WHAT was merged (resolver-side)
  - `brain_merge_log`     operator-side metadata: WHO merged, until WHEN
                          the merge stays reversible, and WHEN (if ever)
                          it was undone. The admin endpoints in
                          `routers/brain_ops.py` read/write this table.

Revision ID: 003_brain_merge_log
Revises: 140054f726ca
Create Date: 2026-05-27
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_brain_merge_log"
down_revision: Union[str, None] = "140054f726ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SCHEMA = """
CREATE TABLE IF NOT EXISTS brain_merge_log (
    id TEXT PRIMARY KEY,
    merged_from TEXT NOT NULL,
    merged_into TEXT NOT NULL,
    performed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    performed_by TEXT,
    reversible_until TEXT,
    undone_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_brain_merge_log_merged_into
    ON brain_merge_log(merged_into);

CREATE INDEX IF NOT EXISTS idx_brain_merge_log_reversible
    ON brain_merge_log(reversible_until)
    WHERE undone_at IS NULL;
"""


def upgrade() -> None:
    for stmt in SCHEMA.strip().split(";\n"):
        stmt = stmt.strip()
        if stmt:
            op.execute(stmt)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_brain_merge_log_reversible")
    op.execute("DROP INDEX IF EXISTS idx_brain_merge_log_merged_into")
    op.execute("DROP TABLE IF EXISTS brain_merge_log")
