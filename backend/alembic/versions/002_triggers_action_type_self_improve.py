"""Allow self_improve_auto in triggers.action_type CHECK constraint.

Revision ID: 002
Revises: 001
Create Date: 2026-05-26

SQLite cannot ALTER a CHECK constraint in place. We use the standard
recreate-table pattern: create new table with the updated CHECK, copy
data, drop the old, rename the new.

The new CHECK includes every action_type the application code references:
spawn_agent, run_command, create_todo, notify, podcast_generate,
self_improve_auto.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_TRIGGERS_DDL = """
CREATE TABLE triggers_new (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('cron', 'webhook', 'file_watch')),
    enabled INTEGER NOT NULL DEFAULT 1,
    config TEXT NOT NULL DEFAULT '{}',
    action_type TEXT NOT NULL CHECK(action_type IN ('spawn_agent', 'run_command', 'create_todo', 'notify', 'podcast_generate', 'self_improve_auto')),
    action_config TEXT NOT NULL DEFAULT '{}',
    node_id TEXT,
    last_fired_at TEXT,
    fire_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

OLD_TRIGGERS_DDL = """
CREATE TABLE triggers_old (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('cron', 'webhook', 'file_watch')),
    enabled INTEGER NOT NULL DEFAULT 1,
    config TEXT NOT NULL DEFAULT '{}',
    action_type TEXT NOT NULL CHECK(action_type IN ('spawn_agent', 'run_command', 'create_todo', 'notify')),
    action_config TEXT NOT NULL DEFAULT '{}',
    node_id TEXT,
    last_fired_at TEXT,
    fire_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _rebuild_triggers(bind, new_ddl: str, new_table_name: str) -> None:
    """Recreate triggers with a new CHECK constraint.

    Drives DDL + DML through Alembic's bound connection, then commits the
    SQLAlchemy transaction explicitly. SQLite's "non-transactional DDL" mode
    on the Alembic context otherwise emits a ROLLBACK at end-of-migration
    that discards INSERT/DROP/RENAME steps.

    Cleans up any stray <new_table_name> left over from a prior failed run.
    """
    # Drop any leftover scratch table from a partially-applied prior attempt.
    bind.exec_driver_sql(f"DROP TABLE IF EXISTS {new_table_name}")

    bind.exec_driver_sql(new_ddl)
    bind.exec_driver_sql(
        f"INSERT INTO {new_table_name} ("
        "id, name, trigger_type, enabled, config, action_type, action_config, "
        "node_id, last_fired_at, fire_count, created_at, updated_at"
        ") SELECT "
        "id, name, trigger_type, enabled, config, action_type, action_config, "
        "node_id, last_fired_at, fire_count, created_at, updated_at "
        "FROM triggers"
    )
    bind.exec_driver_sql("DROP TABLE triggers")
    bind.exec_driver_sql(f"ALTER TABLE {new_table_name} RENAME TO triggers")


def upgrade() -> None:
    bind = op.get_bind()

    # If triggers table doesn't exist yet (fresh DB bootstrapped by Alembic
    # alone), there's nothing to migrate — init_db.py SCHEMA will create it
    # with the correct CHECK on first app boot.
    exists = bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='triggers'"
    ).fetchone()
    if not exists:
        return

    _rebuild_triggers(bind, NEW_TRIGGERS_DDL, "triggers_new")


def downgrade() -> None:
    bind = op.get_bind()
    exists = bind.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='triggers'"
    ).fetchone()
    if not exists:
        return

    # Strip any rows the narrower CHECK would reject, then recreate.
    bind.exec_driver_sql(
        "DELETE FROM triggers WHERE action_type NOT IN "
        "('spawn_agent', 'run_command', 'create_todo', 'notify')"
    )
    _rebuild_triggers(bind, OLD_TRIGGERS_DDL, "triggers_old")
