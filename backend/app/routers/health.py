"""Health endpoints — liveness, readiness, and detailed dependency probe.

See .planning/v3/INTEGRATION.md §2.1 (rows for /api/health, /api/health/ready,
/api/health/detail) and .planning/v3/backend/DESIGN.md §9.
"""
from __future__ import annotations

import os
import sqlite3
import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import (
    HUB_DB_PATH,
    PLATFORM_DB_PATH,
    BRAIN_JSON_PATH,
    QUEUE_JSON_PATH,
    COCO_AUTH_TOKEN,
)
from app.services import auth as auth_service

router = APIRouter(tags=["System"])
_start_time = time.time()

# Tables that must exist for the platform to be considered "ready".
_REQUIRED_TABLES: tuple[str, ...] = (
    "nodes",
    "agents",
    "events",
    "idempotency_keys",
)

PLATFORM_VERSION = os.getenv("PLATFORM_VERSION", "0.1.0")


def _platform_db_status() -> tuple[bool, list[str], str | None]:
    """Return (reachable, missing_required_tables, error_msg)."""
    if not PLATFORM_DB_PATH.exists():
        return False, list(_REQUIRED_TABLES), "platform_db_missing"
    try:
        conn = sqlite3.connect(str(PLATFORM_DB_PATH), timeout=2.0)
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            existing = {r[0] for r in rows}
            missing = [t for t in _REQUIRED_TABLES if t not in existing]
            return True, missing, None
        finally:
            conn.close()
    except sqlite3.Error as e:
        return False, list(_REQUIRED_TABLES), f"sqlite_error:{e.__class__.__name__}"


@router.get("/api/health")
def health():
    """Liveness probe — always 200 as long as the process is up."""
    return {
        "status": "ok",
        "version": PLATFORM_VERSION,
        "uptime_seconds": int(time.time() - _start_time),
        "databases": {
            "hub_db": {"exists": HUB_DB_PATH.exists()},
            "platform_db": {"exists": PLATFORM_DB_PATH.exists()},
        },
        "files": {
            "brain_json": {"exists": BRAIN_JSON_PATH.exists()},
            "queue_json": {"exists": QUEUE_JSON_PATH.exists()},
        },
    }


@router.get("/api/health/ready")
def ready():
    """Readiness probe — 200 if DB reachable AND schema present, else 503."""
    reachable, missing, err = _platform_db_status()
    if reachable and not missing:
        return {
            "status": "ready",
            "platform_db": "ok",
            "schema": "ok",
        }
    return JSONResponse(
        status_code=503,
        content={
            "status": "not_ready",
            "platform_db": "ok" if reachable else "down",
            "schema": "ok" if not missing else "missing",
            "missing_tables": missing,
            "error": err,
        },
    )


def _queue_depth() -> int:
    """Best-effort queue depth from ~/.coco/queue.json."""
    try:
        import json
        if not QUEUE_JSON_PATH.exists():
            return 0
        data = json.loads(QUEUE_JSON_PATH.read_text() or "{}")
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            items = data.get("items") or data.get("queue") or []
            if isinstance(items, list):
                return len(items)
        return 0
    except Exception:
        return -1  # signal unknown


def _db_lag_seconds() -> float | None:
    """Best-effort DB lag (seconds since most recent event), if events table exists."""
    if not PLATFORM_DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(str(PLATFORM_DB_PATH), timeout=2.0)
        try:
            row = conn.execute(
                "SELECT strftime('%s', 'now') - strftime('%s', MAX(created_at)) "
                "FROM events"
            ).fetchone()
            if row is None or row[0] is None:
                return None
            try:
                return float(row[0])
            except (TypeError, ValueError):
                return None
        finally:
            conn.close()
    except sqlite3.Error:
        return None


@router.get("/api/health/detail")
def health_detail():
    """Detailed health for the UI status panel."""
    reachable, missing, err = _platform_db_status()
    return {
        "status": "ready" if (reachable and not missing) else "degraded",
        "version": PLATFORM_VERSION,
        "uptime_seconds": int(time.time() - _start_time),
        # SEC-FIX L4-W2#2: report the true PIN state, not the env-flag.
        # ``COCO_AUTH_TOKEN`` is the legacy bearer-token toggle; the new PIN
        # mode lives in the auth service. Either configured source counts.
        "pin_required": bool(COCO_AUTH_TOKEN) or auth_service.is_pin_set(),
        "platform_db": {
            "reachable": reachable,
            "missing_tables": missing,
            "lag_seconds": _db_lag_seconds(),
            "error": err,
        },
        "hub_db": {"exists": HUB_DB_PATH.exists()},
        "queue": {
            "depth": _queue_depth(),
        },
    }
