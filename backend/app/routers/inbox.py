"""Inbox read-state persistence endpoints."""

import logging
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from app.db.connections import get_platform_db

log = logging.getLogger(__name__)

router = APIRouter(tags=["Inbox"])


class ReadStatePatch(BaseModel):
    item_key: str
    read_state: str  # 'unread' | 'seen' | 'dismissed'


class BatchReadStatePatch(BaseModel):
    item_keys: list[str]
    read_state: str


@router.get("/api/inbox/read-states")
def get_read_states():
    """Return all inbox read states as a dict of item_key -> read_state."""
    try:
        with get_platform_db() as db:
            rows = db.execute("SELECT item_key, read_state FROM inbox_read_state").fetchall()
            return {r["item_key"]: r["read_state"] for r in rows}
    except Exception:
        return {}


@router.patch("/api/inbox/read-state")
def patch_read_state(body: ReadStatePatch):
    """Set the read state for a single inbox item."""
    if body.read_state not in ("unread", "seen", "dismissed"):
        raise HTTPException(400, "read_state must be 'unread', 'seen', or 'dismissed'")

    now = datetime.now(timezone.utc).isoformat()
    with get_platform_db() as db:
        db.execute(
            "INSERT INTO inbox_read_state (item_key, read_state, updated_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(item_key) DO UPDATE SET read_state = excluded.read_state, updated_at = excluded.updated_at",
            (body.item_key, body.read_state, now),
        )
        db.commit()
    return {"item_key": body.item_key, "read_state": body.read_state}


@router.patch("/api/inbox/read-states/batch")
def batch_patch_read_states(body: BatchReadStatePatch):
    """Set the read state for multiple inbox items at once."""
    if body.read_state not in ("unread", "seen", "dismissed"):
        raise HTTPException(400, "read_state must be 'unread', 'seen', or 'dismissed'")

    now = datetime.now(timezone.utc).isoformat()
    with get_platform_db() as db:
        for key in body.item_keys:
            db.execute(
                "INSERT INTO inbox_read_state (item_key, read_state, updated_at) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(item_key) DO UPDATE SET read_state = excluded.read_state, updated_at = excluded.updated_at",
                (key, body.read_state, now),
            )
        db.commit()
    return {"updated": len(body.item_keys), "read_state": body.read_state}


@router.post("/api/inbox/mark-all-seen")
def mark_all_seen():
    """Mark all current unread items as seen."""
    now = datetime.now(timezone.utc).isoformat()
    with get_platform_db() as db:
        result = db.execute(
            "UPDATE inbox_read_state SET read_state = 'seen', updated_at = ? WHERE read_state = 'unread'",
            (now,),
        )
        db.commit()
        return {"updated": result.rowcount}
