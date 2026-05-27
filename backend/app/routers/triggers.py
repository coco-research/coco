"""Triggers & Webhooks -- CRUD + webhook receiver."""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import insert, select, delete
import structlog

from app.db.session import get_db
from app.db.tables import triggers, trigger_log

log = structlog.get_logger()

router = APIRouter(prefix="/api/triggers", tags=["Triggers"])
webhook_router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


# -- Pydantic models --

_TRIGGER_TYPE_RE = r"^(cron|webhook|file_watch)$"
_ACTION_TYPE_RE = r"^(spawn_agent|run_command|create_todo|notify|self_improve_auto|podcast_generate)$"


class TriggerCreate(BaseModel):
    name: str
    trigger_type: str = Field(..., pattern=_TRIGGER_TYPE_RE)
    config: dict = {}
    action_type: str = Field(..., pattern=_ACTION_TYPE_RE)
    action_config: dict = {}
    node_id: Optional[str] = None
    enabled: bool = True


class TriggerUpdate(BaseModel):
    name: Optional[str] = None
    trigger_type: Optional[str] = Field(None, pattern=_TRIGGER_TYPE_RE)
    config: Optional[dict] = None
    action_type: Optional[str] = Field(None, pattern=_ACTION_TYPE_RE)
    action_config: Optional[dict] = None
    node_id: Optional[str] = None
    enabled: Optional[bool] = None


# -- Helpers --

def _row_to_dict(row) -> dict:
    d = dict(row._mapping)
    for key in ("config", "action_config"):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    d["enabled"] = bool(d.get("enabled", 0))
    return d


async def _execute_trigger_action(trigger: dict, context: dict | None = None) -> dict:
    """Execute the action for a trigger.

    Thin wrapper around the registry in app.services.trigger_actions; kept
    here for backwards compatibility with imports from trigger_engine.
    """
    from app.services.trigger_actions import dispatch_action

    return await dispatch_action(trigger, context=context)


def _log_trigger_fire(conn, trigger_id: str, status: str, result: str = None, error: str = None):
    """Insert a trigger_log row and bump fire_count / last_fired_at."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        insert(trigger_log).values(
            trigger_id=trigger_id,
            fired_at=now,
            status=status,
            result=result,
            error=error,
        )
    )
    conn.exec_driver_sql(
        "UPDATE triggers SET fire_count = fire_count + 1, last_fired_at = ?, updated_at = ? WHERE id = ?",
        (now, now, trigger_id),
    )


# -- CRUD endpoints --

@router.get("")
async def list_triggers(
    node_id: Optional[str] = Query(None),
    enabled: Optional[int] = Query(None),
):
    """List all triggers (with last_log attached), optionally filtered."""
    clauses = []
    params = []
    if node_id is not None:
        clauses.append("node_id = ?")
        params.append(node_id)
    if enabled is not None:
        clauses.append("enabled = ?")
        params.append(enabled)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_db() as conn:
        rows = conn.exec_driver_sql(
            f"SELECT * FROM triggers{where} ORDER BY created_at DESC",
            tuple(params),
        ).fetchall()
        items = [_row_to_dict(r) for r in rows]

        # Attach the most recent log entry per trigger so the UI can render
        # last-fire status without an N+1 round trip.
        if items:
            ids = [t["id"] for t in items]
            placeholders = ",".join("?" * len(ids))
            log_rows = conn.exec_driver_sql(
                f"""
                SELECT l.* FROM trigger_log l
                INNER JOIN (
                    SELECT trigger_id, MAX(fired_at) AS max_at
                    FROM trigger_log
                    WHERE trigger_id IN ({placeholders})
                    GROUP BY trigger_id
                ) latest
                ON l.trigger_id = latest.trigger_id AND l.fired_at = latest.max_at
                """,
                tuple(ids),
            ).fetchall()
            by_id = {row._mapping["trigger_id"]: dict(row._mapping) for row in log_rows}
            for t in items:
                t["last_log"] = by_id.get(t["id"])
    return items


@router.get("/{trigger_id}")
async def get_trigger(trigger_id: str):
    """Get a single trigger with its recent log entries."""
    with get_db() as conn:
        row = conn.execute(
            select(triggers).where(triggers.c.id == trigger_id)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trigger not found")
        recent_logs = conn.exec_driver_sql(
            "SELECT * FROM trigger_log WHERE trigger_id = ? ORDER BY fired_at DESC LIMIT 10",
            (trigger_id,),
        ).fetchall()
    trigger = _row_to_dict(row)
    trigger["recent_logs"] = [dict(r._mapping) for r in recent_logs]
    return trigger


@router.post("", status_code=201)
async def create_trigger(body: TriggerCreate):
    """Create a new trigger."""
    trigger_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with get_db() as conn:
        conn.execute(
            insert(triggers).values(
                id=trigger_id,
                name=body.name,
                trigger_type=body.trigger_type,
                enabled=int(body.enabled),
                config=json.dumps(body.config),
                action_type=body.action_type,
                action_config=json.dumps(body.action_config),
                node_id=body.node_id,
                created_at=now,
                updated_at=now,
            )
        )
        row = conn.execute(
            select(triggers).where(triggers.c.id == trigger_id)
        ).fetchone()
    return _row_to_dict(row)


@router.patch("/{trigger_id}")
async def update_trigger(trigger_id: str, body: TriggerUpdate):
    """Update fields on an existing trigger."""
    with get_db() as conn:
        existing = conn.execute(
            select(triggers).where(triggers.c.id == trigger_id)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Trigger not found")

        updates = []
        params = []
        for field in ("name", "trigger_type", "action_type", "node_id"):
            val = getattr(body, field, None)
            if val is not None:
                updates.append(f"{field} = ?")
                params.append(val)
        for field in ("config", "action_config"):
            val = getattr(body, field, None)
            if val is not None:
                updates.append(f"{field} = ?")
                params.append(json.dumps(val))
        if body.enabled is not None:
            updates.append("enabled = ?")
            params.append(int(body.enabled))

        if not updates:
            return _row_to_dict(existing)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        updates.append("updated_at = ?")
        params.append(now)
        params.append(trigger_id)

        conn.exec_driver_sql(
            f"UPDATE triggers SET {', '.join(updates)} WHERE id = ?",
            tuple(params),
        )
        row = conn.execute(
            select(triggers).where(triggers.c.id == trigger_id)
        ).fetchone()
    return _row_to_dict(row)


@router.delete("/{trigger_id}", status_code=204)
async def delete_trigger(trigger_id: str):
    """Delete a trigger and all its log entries."""
    with get_db() as conn:
        existing = conn.exec_driver_sql(
            "SELECT id FROM triggers WHERE id = ?", (trigger_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Trigger not found")
        conn.execute(delete(trigger_log).where(trigger_log.c.trigger_id == trigger_id))
        conn.execute(delete(triggers).where(triggers.c.id == trigger_id))
    return None


@router.post("/{trigger_id}/test")
async def test_trigger(trigger_id: str):
    """Manually fire a trigger once and log the result."""
    with get_db() as conn:
        row = conn.execute(
            select(triggers).where(triggers.c.id == trigger_id)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trigger not found")
        trigger = _row_to_dict(row)

    result = await _execute_trigger_action(trigger)

    with get_db() as conn:
        _log_trigger_fire(
            conn,
            trigger_id,
            status=result.get("status", "success"),
            result=result.get("result"),
            error=result.get("error"),
        )
    return result


@router.get("/{trigger_id}/logs")
async def get_trigger_logs(
    trigger_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Paginated log history for a trigger."""
    with get_db() as conn:
        existing = conn.exec_driver_sql(
            "SELECT id FROM triggers WHERE id = ?", (trigger_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Trigger not found")
        total = conn.exec_driver_sql(
            "SELECT COUNT(*) FROM trigger_log WHERE trigger_id = ?", (trigger_id,)
        ).fetchone()[0]
        rows = conn.exec_driver_sql(
            "SELECT * FROM trigger_log WHERE trigger_id = ? ORDER BY fired_at DESC LIMIT ? OFFSET ?",
            (trigger_id, limit, offset),
        ).fetchall()
    return {"items": [dict(r._mapping) for r in rows], "total": total, "limit": limit, "offset": offset}


# -- Webhook receiver --

@webhook_router.post("/{trigger_id}")
async def receive_webhook(
    trigger_id: str,
    request: Request,
    token: Optional[str] = Query(None),
):
    """Webhook receiver -- validates trigger, fires action, logs result.

    If the trigger's config has a 'token' set, the caller must pass it as
    either a `?token=` query param or `X-Webhook-Token` header. Triggers
    without a token configured are open (anyone with the URL can fire).
    """
    with get_db() as conn:
        row = conn.execute(
            select(triggers).where(triggers.c.id == trigger_id)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trigger not found")
        trigger = _row_to_dict(row)

    if trigger["trigger_type"] != "webhook":
        raise HTTPException(status_code=400, detail="Trigger is not of type 'webhook'")

    if not trigger["enabled"]:
        raise HTTPException(status_code=409, detail="Trigger is disabled")

    expected_token = (trigger.get("config") or {}).get("token")
    if expected_token:
        provided = token or request.headers.get("x-webhook-token") or request.headers.get("X-Webhook-Token")
        if provided != expected_token:
            raise HTTPException(status_code=401, detail="Invalid or missing webhook token")

    context = None
    try:
        body = await request.body()
        if body:
            context = await request.json()
    except Exception:
        context = None

    result = await _execute_trigger_action(trigger, context=context)

    with get_db() as conn:
        _log_trigger_fire(
            conn,
            trigger_id,
            status=result.get("status", "success"),
            result=result.get("result"),
            error=result.get("error"),
        )
    return result
