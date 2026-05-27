"""Trigger action dispatcher.

Each action is a coroutine `async def(trigger: dict, ctx: dict | None) -> dict`
registered in ACTION_HANDLERS. The returned dict shape is:

    {"status": "success" | "failed" | "skipped",
     "result": optional human-readable string,
     "error":  optional error string,
     ...optional metadata fields...}

Adding a new action: write the coroutine, register it in ACTION_HANDLERS,
add it to the CHECK constraint in init_db.py + the Pydantic regex in
routers/triggers.py.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional

import structlog

from app.db.session import get_db
from app.db.tables import agents, todo_overrides
from app.services.event_bus import event_bus
from sqlalchemy import insert

log = structlog.get_logger()

ActionHandler = Callable[[dict, Optional[dict]], Awaitable[dict]]

RUN_COMMAND_TIMEOUT_SECONDS = 30


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _action_config(trigger: dict) -> dict:
    cfg = trigger.get("action_config") or {}
    if isinstance(cfg, str):
        try:
            cfg = json.loads(cfg)
        except (json.JSONDecodeError, TypeError):
            cfg = {}
    return cfg


async def spawn_agent(trigger: dict, ctx: Optional[dict]) -> dict:
    from app.services.process_manager import process_manager

    cfg = _action_config(trigger)
    trigger_name = trigger.get("name", "unknown")
    node_id = trigger.get("node_id")

    agent_name = cfg.get("agent_name", f"trigger-{trigger_name}")
    task = cfg.get("task", f"Triggered by automation: {trigger_name}")
    model = cfg.get("model", "sonnet")
    cwd = cfg.get("cwd")
    role = cfg.get("role", "custom")

    if ctx:
        task += f"\n\nTrigger context:\n```json\n{json.dumps(ctx, indent=2)}\n```"

    agent_id = str(uuid.uuid4())
    now = _now_iso()
    with get_db() as conn:
        conn.execute(
            insert(agents).values(
                id=agent_id,
                name=agent_name,
                node_id=node_id,
                model=model,
                role=role,
                task_description=task,
                status="running",
                started_at=now,
            )
        )

    try:
        pid = process_manager.spawn(agent_id, task, cwd=cwd, model=model, node_id=node_id, role=role)
        with get_db() as conn:
            conn.exec_driver_sql("UPDATE agents SET pid = ? WHERE id = ?", (pid, agent_id))
        return {"status": "success", "result": f"Spawned agent '{agent_name}' (pid={pid})", "agent_id": agent_id}
    except RuntimeError as e:
        with get_db() as conn:
            conn.exec_driver_sql(
                "UPDATE agents SET status = 'failed', stopped_at = datetime('now') WHERE id = ?",
                (agent_id,),
            )
        return {"status": "failed", "error": str(e)}


async def create_todo(trigger: dict, ctx: Optional[dict]) -> dict:
    cfg = _action_config(trigger)
    trigger_name = trigger.get("name", "unknown")
    node_id = trigger.get("node_id")

    title = cfg.get("title", f"Auto-todo from {trigger_name}")
    priority = cfg.get("priority", "medium")
    todo_id = f"trigger-{uuid.uuid4().hex[:12]}"
    now = _now_iso()
    with get_db() as conn:
        conn.execute(
            insert(todo_overrides).values(
                hub_todo_id=todo_id,
                title=title,
                status="open",
                priority=priority,
                node_id=node_id,
                is_platform_native=1,
                created_at=now,
                updated_at=now,
            )
        )
    event_bus.emit("todo.created", {"todo_id": todo_id, "title": title, "source": "trigger"})
    return {"status": "success", "result": f"Created todo: {title}", "todo_id": todo_id}


async def notify(trigger: dict, ctx: Optional[dict]) -> dict:
    cfg = _action_config(trigger)
    trigger_name = trigger.get("name", "unknown")
    message = cfg.get("message", f"Trigger fired: {trigger_name}")
    event_bus.emit("trigger.notification", {
        "trigger_id": trigger["id"],
        "trigger_name": trigger_name,
        "message": message,
        "context": ctx,
    })
    log.info("trigger_notification", trigger_id=trigger["id"], message=message)
    return {"status": "success", "result": f"Notification sent: {message}"}


async def run_command(trigger: dict, ctx: Optional[dict]) -> dict:
    cfg = _action_config(trigger)
    command = cfg.get("command", "")
    if not command:
        return {"status": "failed", "error": "No command specified"}
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=RUN_COMMAND_TIMEOUT_SECONDS)
        output = stdout.decode("utf-8", errors="replace").strip()
        err_output = stderr.decode("utf-8", errors="replace").strip()
        if proc.returncode == 0:
            return {"status": "success", "result": output[:2000] or "Command succeeded"}
        return {"status": "failed", "error": f"Exit code {proc.returncode}: {err_output[:1000]}"}
    except asyncio.TimeoutError:
        return {"status": "failed", "error": f"Command timed out after {RUN_COMMAND_TIMEOUT_SECONDS} seconds"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


async def self_improve_auto(trigger: dict, ctx: Optional[dict]) -> dict:
    from app.services.self_improve_scheduler import auto_start_cycle
    result = auto_start_cycle()
    if result.get("action") == "started":
        return {
            "status": "success",
            "result": f"Started self-improve cycle {result['cycle_id']}",
            "cycle_id": result["cycle_id"],
        }
    return {"status": "skipped", "result": result.get("reason", "Skipped")}


async def podcast_generate(trigger: dict, ctx: Optional[dict]) -> dict:
    from app.services.podcast import generate_podcast as _gen_podcast
    cfg = _action_config(trigger)
    voice = cfg.get("voice", "andrew")
    try:
        result = await _gen_podcast(voice=voice)
        return {
            "status": "success",
            "result": f"Podcast generated: {result.get('id')}",
            "podcast_id": result.get("id"),
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


ACTION_HANDLERS: dict[str, ActionHandler] = {
    "spawn_agent": spawn_agent,
    "create_todo": create_todo,
    "notify": notify,
    "run_command": run_command,
    "self_improve_auto": self_improve_auto,
    "podcast_generate": podcast_generate,
}


async def dispatch_action(trigger: dict, context: Optional[dict] = None) -> dict:
    """Look up the trigger's action_type in the registry and run it."""
    action_type = trigger.get("action_type")
    handler = ACTION_HANDLERS.get(action_type)
    if handler is None:
        return {"status": "skipped", "result": f"Unknown action type: {action_type}"}
    try:
        return await handler(trigger, context)
    except Exception as e:
        log.warning("action_handler_unhandled_error", trigger_id=trigger.get("id"), action=action_type, error=str(e))
        return {"status": "failed", "error": str(e)}
