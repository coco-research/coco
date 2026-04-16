"""Hub Sync Service — mirrors hub.db tables into platform.db.

hub.db is owned by Knowledge Hub and MUST remain read-only.
This service copies 7 hub tables into hub_* mirror tables in platform.db
so platform queries never touch hub.db directly.

- Initial full sync on startup
- Delta sync every 60 seconds (new rows by rowid watermark)
- FTS5 virtual table on hub_content for full-text search
"""

import asyncio
import json
import sqlite3
import structlog
from datetime import datetime, timezone
from pathlib import Path

from app.config import HUB_DB_PATH, KNOWLEDGE_DB_PATH, PLATFORM_DB_PATH

log = structlog.get_logger()

# Hub table -> mirror table name in platform.db
HUB_TABLE_MAP = {
    "todos": "hub_todos",
    "content": "hub_content",
    "projects": "hub_projects",
    "sync_state": "hub_sync_state",
    "project_content": "hub_project_content",
    "api_costs": "hub_api_costs",
    "drafts": "hub_drafts",
}

# DDL for hub mirror tables — columns match hub.db schema
_MIRROR_DDL = """
CREATE TABLE IF NOT EXISTS hub_todos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    project_id TEXT,
    owner TEXT,
    due_date TEXT,
    priority TEXT,
    status TEXT,
    source_type TEXT,
    source_content_id TEXT,
    jira_key TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    tags TEXT
);

CREATE TABLE IF NOT EXISTS hub_content (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT,
    source_path TEXT,
    content_type TEXT,
    title TEXT,
    raw_text TEXT,
    processed_text TEXT,
    metadata TEXT DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'ingested',
    relevance_score REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    processed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_hub_content_source ON hub_content(source);
CREATE INDEX IF NOT EXISTS idx_hub_content_status ON hub_content(status);

CREATE TABLE IF NOT EXISTS hub_projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    jira_key TEXT,
    confluence_space TEXT,
    folder_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    metadata_json TEXT DEFAULT '{}',
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS hub_sync_state (
    source_name TEXT PRIMARY KEY,
    last_success TEXT,
    last_failure TEXT,
    items_synced INTEGER DEFAULT 0,
    error_message TEXT,
    status TEXT DEFAULT 'unknown'
);

CREATE TABLE IF NOT EXISTS hub_project_content (
    project_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    method TEXT DEFAULT '',
    classified_at TEXT,
    PRIMARY KEY (project_id, content_id)
);

CREATE TABLE IF NOT EXISTS hub_api_costs (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    model TEXT NOT NULL,
    feature TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    cost_usd REAL NOT NULL,
    content_id TEXT
);

CREATE TABLE IF NOT EXISTS hub_drafts (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    source_content_id TEXT NOT NULL,
    target_template TEXT NOT NULL,
    target_section TEXT NOT NULL,
    content TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'bullet',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS hub_sync_watermark (
    table_name TEXT PRIMARY KEY,
    last_synced_at TEXT NOT NULL,
    last_rowid INTEGER NOT NULL DEFAULT 0,
    row_count INTEGER NOT NULL DEFAULT 0
);
"""


class HubSyncService:
    """Background service that mirrors hub.db -> platform.db hub_* tables."""

    SYNC_INTERVAL = 60  # seconds

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self):
        """Start the background sync loop."""
        self._running = True
        self._ensure_mirror_tables()
        await self._initial_sync()

        # Delta sync loop
        while self._running:
            await asyncio.sleep(self.SYNC_INTERVAL)
            try:
                await self._delta_sync()
            except Exception as e:
                log.error("hub_delta_sync_failed", error=str(e))

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------

    def _ensure_mirror_tables(self):
        """Create hub_* mirror tables in platform.db if they don't exist."""
        conn = sqlite3.connect(str(PLATFORM_DB_PATH), timeout=10)
        try:
            conn.executescript(_MIRROR_DDL)

            # Migrate: add columns introduced for knowledge.db sync
            existing_cols = {
                r[1] for r in conn.execute("PRAGMA table_info(hub_projects)").fetchall()
            }
            if "updated_at" not in existing_cols:
                conn.execute("ALTER TABLE hub_projects ADD COLUMN updated_at TEXT")
            if "metadata_json" not in existing_cols:
                conn.execute(
                    "ALTER TABLE hub_projects ADD COLUMN metadata_json TEXT DEFAULT '{}'"
                )

            conn.commit()
            log.info("hub_mirror_tables_ensured")
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Hub.db read-only connection helper
    # ------------------------------------------------------------------

    def _open_hub(self) -> sqlite3.Connection | None:
        if not HUB_DB_PATH.exists():
            log.warning("hub_db_not_found", path=str(HUB_DB_PATH))
            return None
        try:
            conn = sqlite3.connect(
                f"file:{HUB_DB_PATH}?mode=ro", uri=True, timeout=10
            )
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            log.error("hub_db_connect_failed", error=str(e))
            return None

    # ------------------------------------------------------------------
    # Initial full sync
    # ------------------------------------------------------------------

    async def _initial_sync(self):
        """Full copy from hub.db -> hub_* mirror tables."""
        hub_conn = self._open_hub()
        if not hub_conn:
            return

        try:
            plat_conn = sqlite3.connect(str(PLATFORM_DB_PATH), timeout=10)
            plat_conn.execute("PRAGMA journal_mode=WAL")
            plat_conn.execute("PRAGMA busy_timeout=5000")

            for hub_table, mirror_table in HUB_TABLE_MAP.items():
                try:
                    self._sync_table_full(hub_conn, plat_conn, hub_table, mirror_table)
                except Exception as e:
                    log.warning(
                        "hub_initial_sync_table_failed",
                        table=hub_table,
                        error=str(e),
                    )

            # Create FTS5 virtual table for hub_content
            self._create_fts5(plat_conn)

            plat_conn.commit()
            log.info("hub_initial_sync_complete")
            plat_conn.close()
        finally:
            hub_conn.close()

        # Sync knowledge.db projects (after hub.db sync so hub projects take precedence)
        self._sync_knowledge_projects()

    def _sync_table_full(
        self,
        hub_conn: sqlite3.Connection,
        plat_conn: sqlite3.Connection,
        hub_table: str,
        mirror_table: str,
    ):
        """Full sync: delete + re-insert all rows for one table."""
        # Get columns that exist in both hub table and mirror table
        hub_cols = [
            r[1] for r in hub_conn.execute(f"PRAGMA table_info({hub_table})").fetchall()
        ]
        if not hub_cols:
            log.debug("hub_table_missing", table=hub_table)
            return

        mirror_cols = [
            r[1]
            for r in plat_conn.execute(
                f"PRAGMA table_info({mirror_table})"
            ).fetchall()
        ]
        common_cols = [c for c in mirror_cols if c in hub_cols]
        if not common_cols:
            return

        col_list = ", ".join(common_cols)
        rows = hub_conn.execute(f"SELECT {col_list} FROM {hub_table}").fetchall()

        # Clear mirror table
        plat_conn.execute(f"DELETE FROM {mirror_table}")

        if rows:
            placeholders = ", ".join(["?"] * len(common_cols))
            plat_conn.executemany(
                f"INSERT OR REPLACE INTO {mirror_table} ({col_list}) VALUES ({placeholders})",
                [tuple(row[col] for col in common_cols) for row in rows],
            )

        # Update watermark
        max_rowid = (
            hub_conn.execute(f"SELECT MAX(rowid) FROM {hub_table}").fetchone()[0] or 0
        )
        plat_conn.execute(
            "INSERT OR REPLACE INTO hub_sync_watermark (table_name, last_synced_at, last_rowid, row_count) "
            "VALUES (?, ?, ?, ?)",
            (
                hub_table,
                datetime.now(timezone.utc).isoformat(),
                max_rowid,
                len(rows),
            ),
        )

        log.info("hub_initial_sync_table", table=hub_table, rows=len(rows))

    # ------------------------------------------------------------------
    # FTS5 virtual table
    # ------------------------------------------------------------------

    def _create_fts5(self, plat_conn: sqlite3.Connection):
        """Create FTS5 virtual table on hub_content for full-text search."""
        try:
            plat_conn.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS hub_content_fts USING fts5(
                    title, raw_text, processed_text, source,
                    content='hub_content', content_rowid=rowid
                );

                -- Rebuild FTS index from current hub_content data
                INSERT INTO hub_content_fts(hub_content_fts) VALUES('rebuild');

                -- Auto-sync triggers
                CREATE TRIGGER IF NOT EXISTS hub_content_ai AFTER INSERT ON hub_content BEGIN
                    INSERT INTO hub_content_fts(rowid, title, raw_text, processed_text, source)
                    VALUES (new.rowid, new.title, new.raw_text, new.processed_text, new.source);
                END;

                CREATE TRIGGER IF NOT EXISTS hub_content_ad AFTER DELETE ON hub_content BEGIN
                    INSERT INTO hub_content_fts(hub_content_fts, rowid, title, raw_text, processed_text, source)
                    VALUES ('delete', old.rowid, old.title, old.raw_text, old.processed_text, old.source);
                END;

                CREATE TRIGGER IF NOT EXISTS hub_content_au AFTER UPDATE ON hub_content BEGIN
                    INSERT INTO hub_content_fts(hub_content_fts, rowid, title, raw_text, processed_text, source)
                    VALUES ('delete', old.rowid, old.title, old.raw_text, old.processed_text, old.source);
                    INSERT INTO hub_content_fts(rowid, title, raw_text, processed_text, source)
                    VALUES (new.rowid, new.title, new.raw_text, new.processed_text, new.source);
                END;
            """)
            log.info("hub_content_fts5_created")
        except Exception as e:
            log.warning("hub_content_fts5_failed", error=str(e))

    # ------------------------------------------------------------------
    # Knowledge.db project sync
    # ------------------------------------------------------------------

    def _sync_knowledge_projects(self):
        """Sync projects from knowledge.db project_registry into hub_projects.

        Uses INSERT OR IGNORE so hub.db-sourced projects are never overwritten
        (hub.db is authoritative for its own projects).
        """
        if not KNOWLEDGE_DB_PATH.exists():
            log.debug("knowledge_db_not_found", path=str(KNOWLEDGE_DB_PATH))
            return

        try:
            k_conn = sqlite3.connect(
                f"file:{KNOWLEDGE_DB_PATH}?mode=ro", uri=True, timeout=10
            )
            k_conn.row_factory = sqlite3.Row
        except Exception as e:
            log.error("knowledge_db_connect_failed", error=str(e))
            return

        try:
            rows = k_conn.execute(
                "SELECT slug, description, registered_at, last_harvest, temperature "
                "FROM project_registry"
            ).fetchall()
        except Exception as e:
            log.warning("knowledge_project_registry_query_failed", error=str(e))
            k_conn.close()
            return

        if not rows:
            k_conn.close()
            return

        try:
            plat_conn = sqlite3.connect(str(PLATFORM_DB_PATH), timeout=10)
            plat_conn.execute("PRAGMA journal_mode=WAL")
            plat_conn.execute("PRAGMA busy_timeout=5000")

            synced = 0
            for row in rows:
                slug = row["slug"]
                description = row["description"] or ""
                name = description if description.strip() else slug
                created_at = row["registered_at"] or datetime.now(timezone.utc).isoformat()
                updated_at = row["last_harvest"]
                temperature = row["temperature"] or "warm"
                metadata_json = json.dumps({"temperature": temperature, "source": "knowledge"})

                result = plat_conn.execute(
                    "INSERT OR IGNORE INTO hub_projects "
                    "(id, name, created_at, updated_at, metadata_json, active) "
                    "VALUES (?, ?, ?, ?, ?, 1)",
                    (slug, name, created_at, updated_at, metadata_json),
                )
                synced += result.rowcount

            plat_conn.commit()
            plat_conn.close()
            log.info("knowledge_projects_synced", total=len(rows), inserted=synced)
        except Exception as e:
            log.error("knowledge_projects_sync_failed", error=str(e))
        finally:
            k_conn.close()

    # ------------------------------------------------------------------
    # Delta sync
    # ------------------------------------------------------------------

    async def _delta_sync(self):
        """Incremental sync: only rows with rowid > last watermark."""
        hub_conn = self._open_hub()
        if not hub_conn:
            return

        try:
            plat_conn = sqlite3.connect(str(PLATFORM_DB_PATH), timeout=10)
            plat_conn.execute("PRAGMA journal_mode=WAL")
            plat_conn.execute("PRAGMA busy_timeout=5000")
            plat_conn.row_factory = sqlite3.Row

            for hub_table, mirror_table in HUB_TABLE_MAP.items():
                try:
                    self._sync_table_delta(
                        hub_conn, plat_conn, hub_table, mirror_table
                    )
                except Exception as e:
                    log.debug(
                        "hub_delta_sync_table_failed",
                        table=hub_table,
                        error=str(e),
                    )

            plat_conn.commit()
            plat_conn.close()
        finally:
            hub_conn.close()

    def _sync_table_delta(
        self,
        hub_conn: sqlite3.Connection,
        plat_conn: sqlite3.Connection,
        hub_table: str,
        mirror_table: str,
    ):
        """Delta sync one table: rows with rowid > watermark."""
        # Get watermark
        wm = plat_conn.execute(
            "SELECT last_rowid FROM hub_sync_watermark WHERE table_name = ?",
            (hub_table,),
        ).fetchone()
        last_rowid = wm["last_rowid"] if wm else 0

        # Get common columns
        hub_cols = [
            r[1] for r in hub_conn.execute(f"PRAGMA table_info({hub_table})").fetchall()
        ]
        mirror_cols = [
            r[1]
            for r in plat_conn.execute(
                f"PRAGMA table_info({mirror_table})"
            ).fetchall()
        ]
        common_cols = [c for c in mirror_cols if c in hub_cols]
        if not common_cols:
            return

        col_list = ", ".join(common_cols)

        # Fetch new rows
        new_rows = hub_conn.execute(
            f"SELECT {col_list} FROM {hub_table} WHERE rowid > ?", (last_rowid,)
        ).fetchall()

        if not new_rows:
            return

        # Upsert
        placeholders = ", ".join(["?"] * len(common_cols))
        plat_conn.executemany(
            f"INSERT OR REPLACE INTO {mirror_table} ({col_list}) VALUES ({placeholders})",
            [tuple(row[col] for col in common_cols) for row in new_rows],
        )

        # Update watermark
        max_rowid = (
            hub_conn.execute(f"SELECT MAX(rowid) FROM {hub_table}").fetchone()[0] or 0
        )
        current_count = (
            hub_conn.execute(f"SELECT COUNT(*) FROM {hub_table}").fetchone()[0] or 0
        )
        plat_conn.execute(
            "INSERT OR REPLACE INTO hub_sync_watermark (table_name, last_synced_at, last_rowid, row_count) "
            "VALUES (?, ?, ?, ?)",
            (
                hub_table,
                datetime.now(timezone.utc).isoformat(),
                max_rowid,
                current_count,
            ),
        )

        log.info("hub_delta_sync", table=hub_table, new_rows=len(new_rows))


# Singleton
hub_sync = HubSyncService()
