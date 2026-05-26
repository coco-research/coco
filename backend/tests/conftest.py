"""Test fixtures for backend tests.

This module sets COCO_DIR and DATABASE_URL to per-session temp paths BEFORE
the app modules import, so that `app.config` picks up the test paths and
`app.db.engine` builds an engine pointing at the test database.

For tests that need a fresh database per test function, use the `fresh_db`
fixture — it rebuilds platform.db schema with init_db's SCHEMA + mirror DDL
and disposes the engine pool to avoid stale connections.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Session-wide environment setup — must run BEFORE app imports
# ---------------------------------------------------------------------------

_TEST_TMP = Path(tempfile.mkdtemp(prefix="coco-tests-"))
_COCO_DIR = _TEST_TMP / "coco"
_HUB_DIR = _TEST_TMP / "hub"
_COCO_DIR.mkdir(parents=True, exist_ok=True)
_HUB_DIR.mkdir(parents=True, exist_ok=True)

# Set BEFORE any `from app...` import below
os.environ["COCO_DIR"] = str(_COCO_DIR)
os.environ["HUB_DIR"] = str(_HUB_DIR)
_DB_PATH = _COCO_DIR / "platform.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
# Empty brain DB path to avoid touching the user's real brain DB
os.environ["BRAIN_DB_PATH"] = str(_TEST_TMP / "project_brain.db")


def _build_schema(db_path: Path) -> None:
    """Create empty platform.db with platform tables + hub mirror tables."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Late import so env vars are honored
    from app.db.init_db import SCHEMA
    from app.services.hub_sync import _MIRROR_DDL

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        conn.executescript(_MIRROR_DDL)
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def fresh_db():
    """Reset platform.db to a clean schema-only state for each test."""
    if _DB_PATH.exists():
        _DB_PATH.unlink()
    # Also wipe -wal / -shm so old data does not bleed in
    for suffix in ("-wal", "-shm"):
        sidecar = _DB_PATH.parent / (_DB_PATH.name + suffix)
        if sidecar.exists():
            sidecar.unlink()

    _build_schema(_DB_PATH)

    # Dispose the engine so the next get_db() opens a fresh connection
    # against the recreated file (avoids cached connections pointing at
    # the deleted DB).
    from app.db.engine import engine
    engine.dispose()

    yield _DB_PATH

    # Cleanup after test
    engine.dispose()


@pytest.fixture()
def app_client(fresh_db):
    """FastAPI TestClient with a fresh platform.db.

    Builds a lightweight FastAPI app and lets each test include the routers
    it needs via `register_router`. Keeping startup small avoids triggering
    the full app lifespan (process_manager, hub_sync, etc.).
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    class _Builder:
        def __init__(self, _app):
            self._app = _app

        def include(self, router):
            self._app.include_router(router)
            return self

        def client(self):
            return TestClient(self._app, raise_server_exceptions=False)

    yield _Builder(app)
