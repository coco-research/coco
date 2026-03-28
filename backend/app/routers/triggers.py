"""Triggers & Webhooks — CRUD + webhook receiver."""

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
import structlog

from app.db.connections import get_platform_db
from app.services.event_bus import event_bus

log = structlog.get_logger()

router = APIRouter(prefix="/api/triggers", tags=["Triggers"])
webhook_router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


# ── Pydantic models ──────────────────────────────────────────────

class TriggerCreate(BaseModel):
    name: str
    trigger_type: str = Field(..., pattern=r"^(cron|webhook|file_watch)$")
    config: dict = {}
    action_type: str = Field(..., pattern=r"^(spawn_agent|run_command|create_todo|notify)$")
    action_config: dict = {}
    node_id: Optional[str] = None
    enabled: bool = True


class TriggerUpdate(BaseModel):
    name: Optional[str] = None
    trigger_type: Optional[str] = Field(None, pattern=r"^(cron|webhook|file_watch)$")
    config: Optional[dict] = None
    action_type: Optional[str] = Field(None, pattern=r"^(spawn_agent|run_command|create_todo|notify)$")
    action_config: Optional[dict] = None
    node_id: Optional[str] = None
    enabled: Optional[bool] = None


# ── Helpers ───────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    d = dict(row)
    for key in ("config", "action_config"):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    d["enabled"] = bool(d.get("enabled", 0))
    return d


async def _execute_trigger_action(trigger: dict, context: dict | None = None) -> dict:
    """Execute the action for a trigger. Dispatches to real action handlers."""
    from app.services.process_manager import process_manager

    action_type = trigger["action_type"]
    action_config = trigger["action_config"]
    if isinstance(action_config, str):
        action_config = json.loads(action_config)

    trigger_name = trigger.get("name", "unknown")
    node_id = trigger.get("node_id")

    if action_type == "spawn_agent":
        # Spawn a real Claude agent via ProcessManager
        agent_name = action_config.get("agent_name", f"trigger-{trigger_name}")
        task = action_config.get("task", f"Triggered by automation: {trigger_name}")
        model = action_config.get("model", "sonnet")
        cwd = action_config.get("cwd")
        role = action_config.get("role", "custom")

        # If context was provided (e.g. webhook payload), append to task
        if context:
            task += f"\n\nTrigger context:\n```json\n{json.dumps(context, indent=2)}\n```"

        agent_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with get_platform_db() as db:
            db.execute(
                "INSERT INTO agents (id, name, node_id, model, role, task_description, status, started_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 'running', ?)",
                (agent_id, agent_name, node_id, model, role, task, now),
            )
            db.commit()

        try:
            pid = process_manager.spawn(agent_id, task, cwd=cwd, model=model, node_id=node_id, role=role)
            with get_platform_db() as db:
                db.execute("UPDATE agents SET pid = ? WHERE id = ?", (pid, agent_id))
                db.commit()
            return {"status": "success", "result": f"Spawned agent '{agent_name}' (pid={pid})", "agent_id": agent_id}
        except RuntimeError as e:
            with get_platform_db() as db:
                db.execute(
                    "UPDATE agents SET status = 'failed', stopped_at = datetime('now') WHERE id = ?",
                    (agent_id,),
                )
                db.commit()
            return {"status": "failed", "error": str(e)}

    elif action_type == "create_todo":
        # Insert a platform-native todo into todo_overrides
        title = action_config.get("title", f"Auto-todo from {trigger_name}")
        priority = action_config.get("priority", "medium")
        todo_id = f"trigger-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with get_platform_db() as db:
            db.execute(
                """INSERT INTO todo_overrides
                   (hub_todo_id, title, status, priority, node_id, is_platform_native, created_at, updated_at)
                   VALUES (?, ?, 'open', ?, ?, 1, ?, ?)""",
                (todo_id, title, priority, node_id, now, now),
            )
            db.commit()
        event_bus.emit("todo.created", {"todo_id": todo_id, "title": title, "source": "trigger"})
        return {"status": "success", "result": f"Created todo: {title}", "todo_id": todo_id}

    elif action_type == "notify":
        # Emit an event via EventBus (picked up by SSE subscribers)
        message = action_config.get("message", f"Trigger fired: {trigger_name}")
        event_bus.emit("trigger.notification", {
            "trigger_id": trigger["id"],
            "trigger_name": trigger_name,
            "message": message,
            "context": context,
        })
        log.info("trigger_notification", trigger_id=trigger["id"], message=message)
        return {"status": "success", "result": f"Notification sent: {message}"}

    elif action_type == "run_command":
        # Run a shell command (capped at 30s timeout)
        import asyncio
        command = action_config.get("command", "")
        if not command:
            return {"status": "failed", "error": "No command specified"}
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            output = stdout.decode("utf-8", errors="replace").strip()
            err_output = stderr.decode("utf-8", errors="replace").strip()
            if proc.returncode == 0:
                return {"status": "success", "result": output[:2000] or "Command succeeded"}
            else:
                return {"status": "failed", "error": f"Exit code {proc.returncode}: {err_output[:1000]}"}
        except asyncio.TimeoutError:
            return {"status": "failed", "error": "Command timed out after 30 seconds"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    return {"status": "skipped", "result": "Unknown action type"}


def _log_trigger_fire(conn, trigger_id: str, status: str, result: str = None, error: str = None):
    """Insert a trigger_log row and bump fire_count / last_fired_at."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    conn.execute(
        "INSERT INTO trigger_log (trigger_id, fired_at, status, result, error) VALUES (?, ?, ?, ?, ?)",
        (trigger_id, now, status, result, error),
    )
    conn.execute(
        "UPDATE triggers SET fire_count = fire_count + 1, last_fired_at = ?, updated_at = ? WHERE id = ?",
        (now, now, trigger_id),
    )
    conn.commit()


# ── CRUD endpoints ────────────────────────────────────────────────

@router.get("")
async def list_triggers(
    node_id: Optional[str] = Query(None),
    enabled: Optional[int] = Query(None),
):
    """List all triggers, optionally filtered by node_id and/or enabled."""
    clauses = []
    params = []
    if node_id is not None:
        clauses.append("node_id = ?")
        params.append(node_id)
    if enabled is not None:
        clauses.append("enabled = ?")
        params.append(enabled)

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with get_platform_db() as conn:
        rows = conn.execute(f"SELECT * FROM triggers{where} ORDER BY created_at DESC", params).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{trigger_id}")
async def get_trigger(trigger_id: str):
    """Get a single trigger with its recent log entries."""
    with get_platform_db() as conn:
        row = conn.execute("SELECT * FROM triggers WHERE id = ?", (trigger_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trigger not found")
        recent_logs = conn.execute(
            "SELECT * FROM trigger_log WHERE trigger_id = ? ORDER BY fired_at DESC LIMIT 10",
            (trigger_id,),
        ).fetchall()
    trigger = _row_to_dict(row)
    trigger["recent_logs"] = [dict(r) for r in recent_logs]
    return trigger


@router.post("", status_code=201)
async def create_trigger(body: TriggerCreate):
    """Create a new trigger."""
    trigger_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with get_platform_db() as conn:
        conn.execute(
            "INSERT INTO triggers (id, name, trigger_type, enabled, config, action_type, action_config, node_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                trigger_id,
                body.name,
                body.trigger_type,
                int(body.enabled),
                json.dumps(body.config),
                body.action_type,
                json.dumps(body.action_config),
                body.node_id,
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM triggers WHERE id = ?", (trigger_id,)).fetchone()
    return _row_to_dict(row)


@router.patch("/{trigger_id}")
async def update_trigger(trigger_id: str, body: TriggerUpdate):
    """Update fields on an existing trigger."""
    with get_platform_db() as conn:
        existing = conn.execute("SELECT * FROM triggers WHERE id = ?", (trigger_id,)).fetchone()
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

        conn.execute(f"UPDATE triggers SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        row = conn.execute("SELECT * FROM triggers WHERE id = ?", (trigger_id,)).fetchone()
    return _row_to_dict(row)


@router.delete("/{trigger_id}", status_code=204)
async def delete_trigger(trigger_id: str):
    """Delete a trigger and all its log entries."""
    with get_platform_db() as conn:
        existing = conn.execute("SELECT id FROM triggers WHERE id = ?", (trigger_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Trigger not found")
        conn.execute("DELETE FROM trigger_log WHERE trigger_id = ?", (trigger_id,))
        conn.execute("DELETE FROM triggers WHERE id = ?", (trigger_id,))
        conn.commit()
    return None


@router.post("/{trigger_id}/test")
async def test_trigger(trigger_id: str):
    """Manually fire a trigger once and log the result."""
    with get_platform_db() as conn:
        row = conn.execute("SELECT * FROM triggers WHERE id = ?", (trigger_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trigger not found")
        trigger = _row_to_dict(row)

    result = await _execute_trigger_action(trigger)

    with get_platform_db() as conn:
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
    with get_platform_db() as conn:
        existing = conn.execute("SELECT id FROM triggers WHERE id = ?", (trigger_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Trigger not found")
        total = conn.execute(
            "SELECT COUNT(*) FROM trigger_log WHERE trigger_id = ?", (trigger_id,)
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT * FROM trigger_log WHERE trigger_id = ? ORDER BY fired_at DESC LIMIT ? OFFSET ?",
            (trigger_id, limit, offset),
        ).fetchall()
    return {"items": [dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}


# ── Webhook receiver ──────────────────────────────────────────────

@webhook_router.post("/{trigger_id}")
async def receive_webhook(trigger_id: str, request: Request):
    """Webhook receiver — validates trigger exists with type='webhook', fires action, logs result.

    Accepts any JSON body and passes it as context to the action.
    """
    with get_platform_db() as conn:
        row = conn.execute("SELECT * FROM triggers WHERE id = ?", (trigger_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Trigger not found")
        trigger = _row_to_dict(row)

    if trigger["trigger_type"] != "webhook":
        raise HTTPException(status_code=400, detail="Trigger is not of type 'webhook'")

    if not trigger["enabled"]:
        raise HTTPException(status_code=409, detail="Trigger is disabled")

    # Parse incoming JSON body as context
    context = None
    try:
        body = await request.body()
        if body:
            context = await request.json()
    except Exception:
        context = None

    result = await _execute_trigger_action(trigger, context=context)

    with get_platform_db() as conn:
        _log_trigger_fire(
            conn,
            trigger_id,
            status=result.get("status", "success"),
            result=result.get("result"),
            error=result.get("error"),
        )
    return result
