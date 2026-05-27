"""Test fixtures for backend tests.

This module sets COCO_DIR and DATABASE_URL to per-session temp paths BEFORE
the app modules import, so that `app.config` picks up the test paths and
`app.db.engine` builds an engine pointing at the test database.

For tests that need a fresh database per test function, use the `fresh_db`
fixture — it rebuilds platform.db via SA Core metadata.create_all() and
disposes the engine pool to avoid stale connections.

For phase-11 auth/audit/telemetry tests that need to monkey-patch engines,
use the `isolated_db` fixture.
"""

from __future__ import annotations

import os
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
    """Create empty platform.db with all platform + hub mirror tables via SA Core."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Late import so env vars are honored
    from app.db.engine import engine
    from app.db.tables import metadata

    metadata.create_all(engine, checkfirst=True)


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

    # Dispose the engine first so create_all opens a fresh connection
    # against the recreated file (avoids cached connections pointing at
    # the deleted DB).
    from app.db.engine import engine
    engine.dispose()

    _build_schema(_DB_PATH)

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


# ---------------------------------------------------------------------------
# Phase-11 fixture — isolated engine for auth/audit/telemetry tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def isolated_db(monkeypatch, tmp_path):
    """Yield an isolated SQLite platform.db with phase-11 tables created.

    The fixture patches `app.db.engine.engine` to point at a tempfile, ensures
    schema is created via SA Core, and stubs out `~/.coco` to a temp dir so
    secrets and telemetry tests don't read/write real user data.
    """
    # Isolate filesystem first
    tmp_coco = tmp_path / "coco_home"
    tmp_coco.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("COCO_DIR", str(tmp_coco))
    monkeypatch.setenv("HUB_DIR", str(tmp_path / "hub_home"))
    (tmp_path / "hub_home").mkdir(exist_ok=True)

    # Build a fresh engine bound to a tempfile
    db_path = tmp_path / "platform.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    # Re-create the engine pointing at the tempfile.
    from sqlalchemy import create_engine, event
    from app.db import engine as engine_mod
    from app.db import session as session_mod
    from app.db import tables as tables_mod

    new_engine = create_engine(db_url, connect_args={"timeout": 5}, pool_pre_ping=True)

    @event.listens_for(new_engine, "connect")
    def _pragmas(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    # Patch the module-level engine in both spots that import it
    monkeypatch.setattr(engine_mod, "engine", new_engine, raising=True)
    monkeypatch.setattr(session_mod, "engine", new_engine, raising=True)

    # Create tables we need for these tests
    tables_mod.metadata.create_all(new_engine, tables=[
        tables_mod.preferences,
        tables_mod.audit_log,
    ])

    # Also re-import config to pick up COCO_DIR override (used by secrets/telemetry)
    import importlib
    from app import config as cfg_mod
    importlib.reload(cfg_mod)
    # services that captured COCO_DIR at import time need refresh
    from app.services import secrets as secrets_mod
    from app.services import telemetry as telemetry_mod
    importlib.reload(secrets_mod)
    importlib.reload(telemetry_mod)

    # Reset in-memory state
    from app.services import auth as auth_mod
    importlib.reload(auth_mod)
    auth_mod.reset_state_for_tests()

    yield {
        "db_url": db_url,
        "db_path": str(db_path),
        "coco_dir": str(tmp_coco),
        "engine": new_engine,
    }

    # Dispose the test engine
    new_engine.dispose()
