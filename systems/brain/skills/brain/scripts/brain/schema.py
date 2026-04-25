"""Database schema, initialization, and migrations."""

import contextlib
import fcntl
import sqlite3
from pathlib import Path
from typing import Callable, Union
from . import SCHEMA_VERSION
from .models import now_iso

Migration = Union[str, Callable[[sqlite3.Connection], None]]


@contextlib.contextmanager
def exclusive_brain_lock(db_path: Path):
    """File-based exclusive lock for OneDrive-safe concurrent access."""
    lock_path = db_path.with_suffix('.lock')
    lf = open(lock_path, 'w')
    try:
        fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except BlockingIOError:
        raise RuntimeError(
            f"Brain DB locked by another session. Wait a few seconds and retry."
        )
    finally:
        fcntl.flock(lf, fcntl.LOCK_UN)
        lf.close()

SCHEMA_V1 = """
-- Version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- CORE
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active',
    description TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    type TEXT NOT NULL CHECK(type IN ('person','team','role','system','module','org_unit','document')),
    name TEXT NOT NULL,
    external_id TEXT,
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entities_project ON entities(project_id);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_ext ON entities(external_id);

CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES entities(id),
    target_id INTEGER NOT NULL REFERENCES entities(id),
    rel_type TEXT NOT NULL CHECK(rel_type IN (
        'member_of','owns','administers','reports_to',
        'depends_on','blocks','scoped_to','created_by'
    )),
    context TEXT,
    valid_from TEXT,
    valid_to TEXT
);
CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id);

-- WORK
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN (
        'open','in_progress','blocked','waiting','done','cancelled'
    )),
    owner_entity_id INTEGER REFERENCES entities(id),
    priority INTEGER DEFAULT 3,
    due_date TEXT,
    blocked_by_task_id INTEGER REFERENCES tasks(id),
    notes TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    category TEXT CHECK(category IN (
        'feature','incident','request','decision','research'
    )),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS thread_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL REFERENCES threads(id),
    item_type TEXT NOT NULL,
    item_id INTEGER NOT NULL
);

-- KNOWLEDGE
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    thread_id INTEGER REFERENCES threads(id),
    date TEXT NOT NULL,
    decision TEXT NOT NULL,
    context TEXT,
    decided_by TEXT,
    impact TEXT
);
CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project_id);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    date TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('meeting','email','call','milestone','deploy')),
    title TEXT NOT NULL,
    summary TEXT,
    source TEXT,
    participants_json TEXT DEFAULT '[]'
);
CREATE INDEX IF NOT EXISTS idx_events_project ON events(project_id);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(date);

-- META
CREATE TABLE IF NOT EXISTS changelog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id INTEGER NOT NULL REFERENCES entities(id),
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    source TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS taggables (
    taggable_type TEXT NOT NULL,
    taggable_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL REFERENCES tags(id),
    PRIMARY KEY (taggable_type, taggable_id, tag_id)
);
"""

def _migrate_events_columns_v2(conn: sqlite3.Connection) -> None:
    """V2: rename legacy events.event_date→date and events.event_type→type.

    Idempotent: inspects PRAGMA table_info and only ALTERs when needed.
    Matches /tmp/migrate_brain_events_columns.py logic for legacy brains
    that predate SCHEMA_V1's `date`/`type` column names.
    """
    cols = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    if not cols:
        return
    if "event_date" in cols and "date" not in cols:
        conn.execute("ALTER TABLE events RENAME COLUMN event_date TO date")
    if "event_type" in cols and "type" not in cols:
        conn.execute("ALTER TABLE events RENAME COLUMN event_type TO type")
    if "event_date" not in cols and "date" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN date TEXT")
    if "event_type" not in cols and "type" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN type TEXT")


def _migrate_events_participants_v3(conn: sqlite3.Connection) -> None:
    """V3: rename legacy events.participants→participants_json.

    Applied to 12 legacy brains on 2026-04-17 (10× Downloads, 2× E&C OneDrive).
    Required because aggregate_parent_brain.py, cross_project_generator.py,
    digest_generator.py, engine.py, project_summary_generator.py, and
    relationship_inferrer.py all query for `participants_json` specifically.
    """
    cols = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    if not cols:
        return
    if "participants" in cols and "participants_json" not in cols:
        conn.execute("ALTER TABLE events RENAME COLUMN participants TO participants_json")
    if "participants" not in cols and "participants_json" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN participants_json TEXT DEFAULT '[]'")


def _migrate_tasks_description_to_notes_v4(conn: sqlite3.Connection) -> None:
    """V4: rename legacy tasks.description→notes.

    Applied to 12 legacy brains on 2026-04-17 (10× Downloads + 2× E&C —
    second pass caught the E&C brains which the first Downloads-only pass
    missed).
    """
    cols = {row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
    if not cols:
        return
    if "description" in cols and "notes" not in cols:
        conn.execute("ALTER TABLE tasks RENAME COLUMN description TO notes")
    if "description" not in cols and "notes" not in cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN notes TEXT")


def _migrate_events_description_to_summary_v5(conn: sqlite3.Connection) -> None:
    """V5: rename legacy events.description→summary.

    Applied to 2 E&C OneDrive brains on 2026-04-17 (Diligence, Personal
    Compliance). Downloads/brains already had `summary` per SCHEMA_V1.
    """
    cols = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
    if not cols:
        return
    if "description" in cols and "summary" not in cols:
        conn.execute("ALTER TABLE events RENAME COLUMN description TO summary")
    if "description" not in cols and "summary" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN summary TEXT")


def _migrate_tasks_add_due_date_v6(conn: sqlite3.Connection) -> None:
    """V6: add tasks.due_date TEXT column.

    Applied to 10× Downloads/brains on 2026-04-17. Code at multiple call
    sites queries `t.due_date`; missing column raised "no such column:
    due_date" errors during Phase 8 composite generation.
    """
    cols = {row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
    if not cols:
        return
    if "due_date" not in cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")


MIGRATIONS: dict[int, Migration] = {
    2: _migrate_events_columns_v2,
    3: _migrate_events_participants_v3,
    4: _migrate_tasks_description_to_notes_v4,
    5: _migrate_events_description_to_summary_v5,
    6: _migrate_tasks_add_due_date_v6,
}


def get_db(db_path: Path) -> sqlite3.Connection:
    """Open a connection with recommended pragmas."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def current_version(conn: sqlite3.Connection) -> int:
    """Get the current schema version. Returns 0 if not initialized."""
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0
    except sqlite3.OperationalError:
        return 0


def init_db(db_path: Path) -> sqlite3.Connection:
    """Create a new brain database with the full schema."""
    with exclusive_brain_lock(db_path):
        conn = get_db(db_path)
        ver = current_version(conn)
        if ver >= SCHEMA_VERSION:
            return conn
        conn.executescript(SCHEMA_V1)
        conn.execute(
            "INSERT OR IGNORE INTO schema_version (version, applied_at) VALUES (?, ?)",
            (SCHEMA_VERSION, now_iso()),
        )
        conn.commit()
        return conn


def migrate(conn: sqlite3.Connection) -> None:
    """Apply pending migrations."""
    ver = current_version(conn)
    for target_ver in sorted(MIGRATIONS.keys()):
        if target_ver > ver:
            m = MIGRATIONS[target_ver]
            if callable(m):
                m(conn)
            else:
                conn.executescript(m)
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (target_ver, now_iso()),
            )
            conn.commit()
