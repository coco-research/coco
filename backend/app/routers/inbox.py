"""Inbox read-state persistence endpoints and server-persisted notifications."""

import json
import logging
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, text

from app.db.session import get_db
from app.db.tables import inbox_read_state, inbox_notifications

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
        with get_db() as conn:
            rows = conn.execute(
                select(inbox_read_state.c.item_key, inbox_read_state.c.read_state)
            ).fetchall()
            return {r._mapping["item_key"]: r._mapping["read_state"] for r in rows}
    except Exception:
        return {}


@router.patch("/api/inbox/read-state")
def patch_read_state(body: ReadStatePatch):
    """Set the read state for a single inbox item."""
    if body.read_state not in ("unread", "seen", "dismissed"):
        raise HTTPException(400, "read_state must be 'unread', 'seen', or 'dismissed'")

    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.exec_driver_sql(
            "INSERT INTO inbox_read_state (item_key, read_state, updated_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(item_key) DO UPDATE SET read_state = excluded.read_state, updated_at = excluded.updated_at",
            (body.item_key, body.read_state, now),
        )
    return {"item_key": body.item_key, "read_state": body.read_state}


@router.patch("/api/inbox/read-states/batch")
def batch_patch_read_states(body: BatchReadStatePatch):
    """Set the read state for multiple inbox items at once."""
    if body.read_state not in ("unread", "seen", "dismissed"):
        raise HTTPException(400, "read_state must be 'unread', 'seen', or 'dismissed'")

    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        for key in body.item_keys:
            conn.exec_driver_sql(
                "INSERT INTO inbox_read_state (item_key, read_state, updated_at) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(item_key) DO UPDATE SET read_state = excluded.read_state, updated_at = excluded.updated_at",
                (key, body.read_state, now),
            )
    return {"updated": len(body.item_keys), "read_state": body.read_state}


@router.post("/api/inbox/mark-all-seen")
def mark_all_seen():
    """Mark all current unread items as seen."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        result = conn.exec_driver_sql(
            "UPDATE inbox_read_state SET read_state = 'seen', updated_at = ? WHERE read_state = 'unread'",
            (now,),
        )
        return {"updated": result.rowcount}


# ---------------------------------------------------------------------------
# Server-persisted inbox notifications
# ---------------------------------------------------------------------------

@router.get("/api/inbox/notifications")
def get_notifications(
    item_type: str | None = Query(default=None, description="Filter by item_type"),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return server-persisted inbox notification items with their read states.

    These include self-improvement summaries and other system-generated items.
    """
    try:
        with get_db() as conn:
            if item_type:
                rows = conn.exec_driver_sql(
                    "SELECT n.id, n.item_type, n.item_key, n.title, n.body, n.metadata_json, n.created_at, "
                    "COALESCE(rs.read_state, 'unread') as read_state "
                    "FROM inbox_notifications n "
                    "LEFT JOIN inbox_read_state rs ON n.item_key = rs.item_key "
                    "WHERE n.item_type = ? "
                    "ORDER BY n.created_at DESC LIMIT ?",
                    (item_type, limit),
                ).fetchall()
            else:
                rows = conn.exec_driver_sql(
                    "SELECT n.id, n.item_type, n.item_key, n.title, n.body, n.metadata_json, n.created_at, "
                    "COALESCE(rs.read_state, 'unread') as read_state "
                    "FROM inbox_notifications n "
                    "LEFT JOIN inbox_read_state rs ON n.item_key = rs.item_key "
                    "ORDER BY n.created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()

            items = []
            for r in rows:
                item = dict(r._mapping)
                if item.get("metadata_json"):
                    try:
                        item["metadata"] = json.loads(item["metadata_json"])
                    except (json.JSONDecodeError, TypeError):
                        item["metadata"] = {}
                else:
                    item["metadata"] = {}
                del item["metadata_json"]
                items.append(item)
            return items
    except Exception as e:
        log.warning("inbox_notifications_query_failed: %s", str(e))
        return []


@router.get("/api/inbox/self-improve-summaries")
def get_self_improve_summaries(limit: int = Query(default=20, ge=1, le=100)):
    """Return self-improvement summary inbox items."""
    return get_notifications(item_type="self_improve_summary", limit=limit)
