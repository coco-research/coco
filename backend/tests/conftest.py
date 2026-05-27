"""Pytest fixtures for Phase 11 tests.

Provides an isolated platform.db tempfile so auth/audit tests can write to
the DB without polluting `~/.coco/platform.db`. Engine is patched in place
via SA Core dispose+recreate.
"""
from __future__ import annotations

import os
import tempfile
import pytest


@pytest.fixture()
def isolated_db(monkeypatch, tmp_path):
    """Yield an isolated SQLite platform.db with all tables created.

    The fixture patches `app.db.engine.engine` to point at a tempfile, ensures
    schema is created via init_db, and stubs out `~/.coco` to a temp dir so
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
