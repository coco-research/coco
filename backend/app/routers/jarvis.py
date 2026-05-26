"""Jarvis command endpoint -- lightweight, non-streaming command interpreter."""

import asyncio
import json
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

import structlog
from fastapi import APIRouter, Query
from sqlalchemy import select, insert, delete, func

from app.config import USE_AGENT_SDK
from app.db.compat import today, now, upsert
from app.db.session import get_db
from app.db.tables import (
    hub_todos, hub_projects, hub_drafts, hub_sync_state,
    jarvis_sessions, draft_decisions, todo_overrides,
    self_improve_cycles, self_improve_improvements,
)
from app.models.jarvis import (
    CardActionModel,
    CardDataModel,
    CommandRequest,
    CommandResponse,
)
from app.routers.home import get_home, _build_briefing

log = structlog.get_logger()

router = APIRouter(tags=["Jarvis"])


# -- Session Memory --

def _record_exchange(user_text: str, reply: str, cards: list | None = None) -> None:
    try:
        cards_json = json.dumps([c.model_dump() if hasattr(c, 'model_dump') else c for c in (cards or [])]) if cards else None
        with get_db() as conn:
            conn.execute(
                insert(jarvis_sessions).values(
                    command=user_text[:500], response_summary=reply[:500], cards_json=cards_json,
                )
            )
    except Exception as e:
        log.warning("jarvis_record_exchange_failed", error=str(e))


def _get_history_context() -> str:
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(jarvis_sessions.c.command, jarvis_sessions.c.response_summary)
                .order_by(jarvis_sessions.c.created_at.desc())
                .limit(5)
            ).fetchall()
        if not rows:
            return ""
        lines = []
        for entry in reversed(rows):
            lines.append(f"User: {entry.command}")
            lines.append(f"Assistant: {entry.response_summary}")
        return "\n".join(lines)
    except Exception:
        return ""


def _get_recent_history(limit: int = 20) -> list[dict]:
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    jarvis_sessions.c.id, jarvis_sessions.c.command,
                    jarvis_sessions.c.response_summary, jarvis_sessions.c.cards_json,
                    jarvis_sessions.c.created_at,
                )
                .order_by(jarvis_sessions.c.created_at.desc())
                .limit(limit)
            ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        log.warning("jarvis_get_history_failed", error=str(e))
        return []


# -- Inline Action Extraction --

def _extract_create_todo(text_str: str) -> str | None:
    for pat in [
        r"create\s+todo[:\s]+(.+)",
        r"add\s+todo[:\s]+(.+)",
        r"new\s+todo[:\s]+(.+)",
        r"remind\s+me\s+to\s+(.+)",
    ]:
        m = re.search(pat, text_str, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _extract_approve_draft(text_str: str) -> str | None:
    for pat in [r"approve\s+draft\s+(\S+)"]:
        m = re.search(pat, text_str, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


async def _handle_create_todo(title: str) -> CommandResponse:
    from app.routers.todos import create_todo
    from app.models.todos import CreateTodoBody

    body = CreateTodoBody(title=title)
    result = create_todo(body)
    todo_id = result.get("id", "")
    return CommandResponse(
        reply=f'Created todo: "{title}".',
        cards=[CardDataModel(
            id=_card_id(),
            type="todo_list",
            data={"title": "New Todo", "todos": [{"id": todo_id, "title": title, "status": "open", "priority": "medium", "due_date": None, "project_name": None}]},
        )],
        action="navigate",
        url="/todos",
    )


async def _handle_approve_draft(draft_id: str) -> CommandResponse:
    from app.routers.drafts import approve_draft

    try:
        result = approve_draft(draft_id)
        title = result.get("title") or result.get("template") or draft_id
        return CommandResponse(
            reply=f'Draft "{title}" approved.',
            cards=[CardDataModel(
                id=_card_id(),
                type="text_response",
                data={"text": f'Draft "{title}" has been approved.'},
            )],
        )
    except Exception as e:
        log.warning("jarvis_approve_draft_failed", error=str(e), draft_id=draft_id)
        return CommandResponse(
            reply=f"Couldn't approve draft {draft_id}. It may not exist.",
            cards=[],
        )


def _card_id() -> str:
    return uuid.uuid4().hex[:8]


# -- Command Patterns --

COMMAND_PATTERNS = [
    (["next decision", "next item", "what's next in queue", "whats next"], "cmd_next_decision"),
    (["approve it", "approve", "yes", "looks good", "lgtm"], "cmd_voice_approve"),
    (["reject it", "reject", "no", "pass on this"], "cmd_voice_reject"),
    (["defer", "later", "snooze", "come back to this"], "cmd_voice_defer"),
    (["process", "sync", "ingest", "refresh"], "cmd_process"),
    (["briefing", "catch me up", "what's new", "whats new", "update me"], "cmd_briefing"),
    (["overdue", "late", "behind"], "cmd_overdue"),
    (["decide", "decision", "attention", "needs my", "inbox", "drafts"], "cmd_decide"),
    (["todo", "todos", "task", "tasks", "my list"], "cmd_todos"),
    (["health", "system status", "systems", "adapters"], "cmd_health"),
    (["cost", "costs", "spending", "how much", "budget"], "cmd_costs"),
    (["search", "find", "look for", "look up"], "cmd_search"),
    (["chat", "talk to claude", "ask claude", "open chat"], "cmd_chat"),
    (["projects", "my projects", "project list"], "cmd_projects"),
    (["dismiss", "clear", "go back", "never mind", "cancel"], "cmd_dismiss"),
    (["self improve", "self-improve", "improvements", "improved overnight", "what did you improve"], "cmd_self_improve"),
]


def _match_command(text_str: str) -> tuple[str | None, str]:
    lower = text_str.lower().strip()
    for keywords, handler in COMMAND_PATTERNS:
        for kw in keywords:
            if kw in lower:
                idx = lower.find(kw)
                remaining = text_str[idx + len(kw):].strip().lstrip("for").strip()
                return handler, remaining
    return None, text_str


# -- Handlers --

async def cmd_process(**_) -> CommandResponse:
    status = "ok"
    output = ""
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            ["uv", "run", "python", "-m", "knowledge_hub.cli", "process"],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.expanduser("~"),
        )
        output = (proc.stdout or "")[-300:]
        if proc.returncode != 0:
            status = "error"
    except subprocess.TimeoutExpired:
        status = "timeout"
    except Exception:
        status = "error"

    reply = {
        "ok": "Processing pipeline complete. New content ingested.",
        "timeout": "Process is still running in background (timed out after 30s).",
        "error": "Process encountered an error. Check KH logs.",
    }.get(status, "Process triggered.")

    return CommandResponse(
        reply=reply,
        cards=[CardDataModel(
            id=_card_id(), type="health_detail",
            data={"sources": [], "overall_pct": 0, "process_status": status, "process_output": output},
            actions=[CardActionModel(label="Run Again", action="process", endpoint="/home/process", method="POST")],
        )],
    )


async def cmd_briefing(**_) -> CommandResponse:
    data = get_home()
    if not data:
        return CommandResponse(
            reply="Couldn't load briefing data right now.",
            cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": "Briefing data unavailable."})],
        )
    result = _build_briefing(data)
    script = result.get("script", "") if result else ""
    if not script:
        return CommandResponse(
            reply="No briefing to report right now.",
            cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": "No briefing available."})],
        )
    return CommandResponse(reply=script, cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": script})])


async def cmd_overdue(**_) -> CommandResponse:
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    hub_todos.c.id, hub_todos.c.title, hub_todos.c.status,
                    hub_todos.c.priority, hub_todos.c.due_date, hub_todos.c.project_id,
                    hub_projects.c.name.label("project_name"),
                )
                .select_from(hub_todos.outerjoin(hub_projects, hub_todos.c.project_id == hub_projects.c.id))
                .where(hub_todos.c.status == "open")
                .where(hub_todos.c.due_date < today())
                .order_by(hub_todos.c.due_date.asc())
                .limit(10)
            ).fetchall()
            if not rows:
                return CommandResponse(
                    reply="Nothing overdue. You're in good shape.",
                    cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": "Nothing overdue. You're in good shape."})],
                )
            items = [dict(r._mapping) for r in rows]
            count = len(items)
            reply = f"{count} overdue item{'s' if count != 1 else ''}. "
            reply += ". ".join(r["title"] for r in items[:3])
            if count > 3:
                reply += f". And {count - 3} more."
            return CommandResponse(
                reply=reply,
                cards=[CardDataModel(id=_card_id(), type="todo_list", data={"title": f"Overdue Items ({count})", "todos": items})],
            )
    except Exception as e:
        log.warning("cmd_overdue_error", error=str(e))
        return CommandResponse(reply="Couldn't check overdue items.", cards=[])


async def cmd_decide(**_) -> CommandResponse:
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    hub_drafts.c.id, hub_drafts.c.project_id, hub_drafts.c.template,
                    hub_drafts.c.section, hub_drafts.c.status, hub_drafts.c.created_at,
                    hub_projects.c.name.label("project_name"),
                )
                .select_from(hub_drafts.outerjoin(hub_projects, hub_drafts.c.project_id == hub_projects.c.id))
                .where(hub_drafts.c.status == "pending")
                .order_by(hub_drafts.c.created_at.desc())
                .limit(10)
            ).fetchall()
            if not rows:
                return CommandResponse(
                    reply="No pending drafts. Your queue is clean.",
                    cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": "No pending drafts."})],
                )
            drafts = [
                {
                    "id": r.id,
                    "title": f"{r.template} -> {r.section}",
                    "project_name": r.project_name or r.project_id or "Unknown",
                    "draft_type": r.template,
                    "preview": f"Draft for {r.project_name or r.project_id or 'unknown'}: {r.template} / {r.section}",
                }
                for r in rows
            ]
            return CommandResponse(
                reply=f"{len(drafts)} drafts pending your review.",
                cards=[CardDataModel(id=_card_id(), type="approval_batch", data={"drafts": drafts})],
            )
    except Exception as e:
        log.warning("cmd_decide_error", error=str(e))
        return CommandResponse(reply="Opening your decision queue.", action="navigate", url="/inbox", cards=[])


async def cmd_todos(**_) -> CommandResponse:
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    hub_todos.c.id, hub_todos.c.title, hub_todos.c.status,
                    hub_todos.c.priority, hub_todos.c.due_date, hub_todos.c.project_id,
                    hub_projects.c.name.label("project_name"),
                )
                .select_from(hub_todos.outerjoin(hub_projects, hub_todos.c.project_id == hub_projects.c.id))
                .where(hub_todos.c.status == "open")
                .where(hub_todos.c.priority == "high")
                .order_by(hub_todos.c.due_date.asc().nullslast())
                .limit(10)
            ).fetchall()
            total_row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(hub_todos)
                .where(hub_todos.c.status == "open")
            ).fetchone()
            total_count = total_row.cnt if total_row else 0
            items = [dict(r._mapping) for r in rows]
            reply = f"You have {total_count} open todos, {len(items)} high priority."
            return CommandResponse(
                reply=reply,
                cards=[CardDataModel(id=_card_id(), type="todo_list", data={"title": f"High Priority ({len(items)})", "todos": items})],
            )
    except Exception as e:
        log.warning("cmd_todos_error", error=str(e))
        return CommandResponse(reply="Opening your todo list.", action="navigate", url="/todos", cards=[])


async def cmd_health(**_) -> CommandResponse:
    try:
        with get_db() as conn:
            rows = conn.execute(select(hub_sync_state)).fetchall()
            now = datetime.now(timezone.utc)
            sources = []
            parts = []
            for r in rows:
                h = dict(r._mapping)
                name = h.get("source", "unknown")
                last_sync = h.get("last_sync")
                items_synced = h.get("item_count", 0)
                stale_hours = None
                status = "ok"
                if last_sync:
                    try:
                        ts = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        stale_hours = (now - ts).total_seconds() / 3600
                    except Exception:
                        pass
                    if stale_hours and stale_hours > 24:
                        status = "red"
                        parts.append(f"{name.title()}: {stale_hours/24:.0f} days ago, needs attention")
                    elif stale_hours:
                        parts.append(f"{name.title()}: {stale_hours:.0f} hours ago, healthy")
                    else:
                        parts.append(f"{name.title()}: synced")
                else:
                    status = "red"
                    parts.append(f"{name.title()}: never synced")
                sources.append({
                    "source": name, "status": status,
                    "stale_hours": stale_hours,
                    "last_sync": last_sync,
                    "items_synced": items_synced or 0,
                })
            scores = [100 if (s["stale_hours"] or 999) < 12 else 60 if (s["stale_hours"] or 999) < 24 else 20 for s in sources]
            overall = sum(scores) / len(scores) if scores else 100
            return CommandResponse(
                reply=". ".join(parts) + "." if parts else "No sync data available.",
                cards=[CardDataModel(
                    id=_card_id(), type="health_detail",
                    data={"sources": sources, "overall_pct": round(overall)},
                    actions=[CardActionModel(label="Run Process", action="process", endpoint="/home/process", method="POST")],
                )],
            )
    except Exception as e:
        log.warning("cmd_health_error", error=str(e))
        return CommandResponse(reply="Couldn't check system health.", cards=[])


async def cmd_costs(**_) -> CommandResponse:
    data = get_home()
    costs = data.get("costs", {}) if data else {}
    today = costs.get("today_usd", 0)
    month = costs.get("month_usd", 0)
    return CommandResponse(
        reply=f"Today: ${today:.2f}. This month: ${month:.2f}.",
        cards=[CardDataModel(
            id=_card_id(), type="metric_grid",
            data={"metrics": [
                {"label": "Today", "value": round(today, 2), "color": "sky"},
                {"label": "This Month", "value": round(month, 2), "color": "sky"},
            ]},
        )],
    )


async def cmd_search(remaining: str = "", **_) -> CommandResponse:
    if remaining:
        qs = urlencode({"q": remaining})
        url = f"/knowledge?{qs}"
        return CommandResponse(
            reply=f'Searching for "{remaining}".',
            action="navigate", url=url,
            cards=[CardDataModel(id=_card_id(), type="navigate_hint", data={"destination": f"Knowledge: {remaining}", "url": url})],
        )
    return CommandResponse(reply="What should I search for?", cards=[])


async def cmd_chat(**_) -> CommandResponse:
    return CommandResponse(reply="Opening chat with Claude.", action="navigate", url="/chat",
        cards=[CardDataModel(id=_card_id(), type="navigate_hint", data={"destination": "Chat", "url": "/chat"})])


async def cmd_projects(**_) -> CommandResponse:
    data = get_home()
    projects = [p for p in data.get("projects", []) if p.get("active")][:6]
    cards = []
    for p in projects:
        cards.append(CardDataModel(
            id=_card_id(), type="project_detail",
            data={
                "id": p["id"], "name": p["name"],
                "email_count": p.get("sources", {}).get("email", 0),
                "jira_count": p.get("sources", {}).get("jira", 0),
                "todo_open": p.get("todo_open", 0),
                "todo_done": p.get("todo_done", 0),
                "recent_activity": [],
            },
        ))
    return CommandResponse(reply=f"{len(projects)} active projects.", cards=cards)


async def cmd_dismiss(**_) -> CommandResponse:
    return CommandResponse(reply="Dismissed.", cards=[])


async def cmd_self_improve(**_) -> CommandResponse:
    """Show the latest self-improvement cycle summary."""
    try:
        data = jarvis_self_improve_summary()
        summary = data.get("summary")
        if not summary:
            return CommandResponse(
                reply="No completed self-improvement cycles yet.",
                cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": "No self-improvement cycles have completed yet."})],
            )
        return CommandResponse(
            reply=summary,
            cards=[CardDataModel(
                id=_card_id(), type="metric_grid",
                data={"metrics": [
                    {"label": "Improvements", "value": data.get("improvements_count", 0), "color": "green"},
                    {"label": "Cost", "value": f"${data.get('spent_usd', 0):.2f}", "color": "sky"},
                ]},
            )],
            action="navigate",
            url="/self-improve",
        )
    except Exception as e:
        log.warning("cmd_self_improve_error", error=str(e))
        return CommandResponse(reply="Couldn't check self-improvement status.", cards=[])


# -- Voice Decision Queue --

_voice_queue_state: dict = {"current_item": None, "current_type": None, "current_id": None}


async def cmd_next_decision(**_) -> CommandResponse:
    try:
        with get_db() as conn:
            decided_rows = conn.execute(
                select(draft_decisions.c.hub_draft_id)
            ).fetchall()
            decided_ids = [r.hub_draft_id for r in decided_rows]

            if decided_ids:
                draft = conn.execute(
                    select(hub_drafts.c.id, hub_drafts.c.template, hub_drafts.c.section,
                           hub_drafts.c.project_id, hub_drafts.c.created_at)
                    .where(hub_drafts.c.status == "pending")
                    .where(hub_drafts.c.id.notin_(decided_ids))
                    .order_by(hub_drafts.c.created_at)
                    .limit(1)
                ).fetchone()
            else:
                draft = conn.execute(
                    select(hub_drafts.c.id, hub_drafts.c.template, hub_drafts.c.section,
                           hub_drafts.c.project_id, hub_drafts.c.created_at)
                    .where(hub_drafts.c.status == "pending")
                    .order_by(hub_drafts.c.created_at)
                    .limit(1)
                ).fetchone()

            if draft:
                _voice_queue_state["current_item"] = dict(draft._mapping)
                _voice_queue_state["current_type"] = "draft"
                _voice_queue_state["current_id"] = draft.id
                project = draft.project_id or "unknown project"
                reply = f"Pending draft: {draft.template} for {project}. Approve, reject, or defer?"
                return CommandResponse(
                    reply=reply,
                    cards=[CardDataModel(id=_card_id(), type="approval_batch", data={"drafts": [dict(draft._mapping)]})],
                )
    except Exception as e:
        log.warning("cmd_next_decision_drafts_error", error=str(e))

    # Try overdue todos
    try:
        with get_db() as conn:
            overridden_rows = conn.execute(
                select(todo_overrides.c.hub_todo_id)
                .where(todo_overrides.c.status.in_(["done", "archived", "deferred"]))
            ).fetchall()
            overridden_ids = [r.hub_todo_id for r in overridden_rows]

            if overridden_ids:
                todo = conn.execute(
                    select(hub_todos.c.id, hub_todos.c.title, hub_todos.c.priority, hub_todos.c.due_date)
                    .where(hub_todos.c.status == "open")
                    .where(hub_todos.c.due_date < today())
                    .where(hub_todos.c.id.notin_(overridden_ids))
                    .order_by(hub_todos.c.due_date)
                    .limit(1)
                ).fetchone()
            else:
                todo = conn.execute(
                    select(hub_todos.c.id, hub_todos.c.title, hub_todos.c.priority, hub_todos.c.due_date)
                    .where(hub_todos.c.status == "open")
                    .where(hub_todos.c.due_date < today())
                    .order_by(hub_todos.c.due_date)
                    .limit(1)
                ).fetchone()

            if todo:
                _voice_queue_state["current_item"] = dict(todo._mapping)
                _voice_queue_state["current_type"] = "todo"
                _voice_queue_state["current_id"] = todo.id
                reply = f"Overdue: {todo.title}. Due {todo.due_date}. Mark done, defer, or skip?"
                return CommandResponse(
                    reply=reply,
                    cards=[CardDataModel(id=_card_id(), type="todo_list", data={"title": "Overdue", "todos": [dict(todo._mapping)]})],
                )
    except Exception as e:
        log.warning("cmd_next_decision_todos_error", error=str(e))

    _voice_queue_state["current_item"] = None
    _voice_queue_state["current_type"] = None
    _voice_queue_state["current_id"] = None
    return CommandResponse(reply="Queue is clear. Nothing pending.", cards=[])


async def cmd_voice_approve(**_) -> CommandResponse:
    if not _voice_queue_state["current_id"]:
        return CommandResponse(reply="Nothing to approve. Say 'next' first.", cards=[])

    item_id = _voice_queue_state["current_id"]
    item_type = _voice_queue_state["current_type"]

    if item_type == "draft":
        with get_db() as conn:
            conn.execute(
                upsert(
                    draft_decisions,
                    values={"id": uuid.uuid4().hex, "hub_draft_id": item_id, "status": "approved", "decided_by": "voice", "decided_at": datetime.now(timezone.utc).isoformat()},
                    conflict_columns=["id"],
                    update_columns=["status", "decided_by", "decided_at"],
                )
            )
        _voice_queue_state.update(current_item=None, current_type=None, current_id=None)
        return CommandResponse(reply="Approved. Say 'next' for the next item.", cards=[])

    elif item_type == "todo":
        with get_db() as conn:
            conn.execute(
                upsert(
                    todo_overrides,
                    values={"hub_todo_id": item_id, "status": "done", "updated_at": datetime.now(timezone.utc).isoformat()},
                    conflict_columns=["hub_todo_id"],
                    update_columns=["status", "updated_at"],
                )
            )
        _voice_queue_state.update(current_item=None, current_type=None, current_id=None)
        return CommandResponse(reply="Marked done. Say 'next' for the next item.", cards=[])

    return CommandResponse(reply="Done.", cards=[])


async def cmd_voice_reject(**_) -> CommandResponse:
    if not _voice_queue_state["current_id"]:
        return CommandResponse(reply="Nothing to reject. Say 'next' first.", cards=[])

    item_id = _voice_queue_state["current_id"]
    item_type = _voice_queue_state["current_type"]

    if item_type == "draft":
        with get_db() as conn:
            conn.execute(
                upsert(
                    draft_decisions,
                    values={"id": uuid.uuid4().hex, "hub_draft_id": item_id, "status": "rejected", "decided_by": "voice", "decided_at": datetime.now(timezone.utc).isoformat()},
                    conflict_columns=["id"],
                    update_columns=["status", "decided_by", "decided_at"],
                )
            )
        _voice_queue_state.update(current_item=None, current_type=None, current_id=None)
        return CommandResponse(reply="Rejected. Say 'next' for the next item.", cards=[])

    elif item_type == "todo":
        with get_db() as conn:
            conn.execute(
                upsert(
                    todo_overrides,
                    values={"hub_todo_id": item_id, "status": "archived", "updated_at": datetime.now(timezone.utc).isoformat()},
                    conflict_columns=["hub_todo_id"],
                    update_columns=["status", "updated_at"],
                )
            )
        _voice_queue_state.update(current_item=None, current_type=None, current_id=None)
        return CommandResponse(reply="Skipped. Say 'next' for the next item.", cards=[])

    return CommandResponse(reply="Done.", cards=[])


async def cmd_voice_defer(**_) -> CommandResponse:
    if not _voice_queue_state["current_id"]:
        return CommandResponse(reply="Nothing to defer. Say 'next' first.", cards=[])

    item_id = _voice_queue_state["current_id"]
    item_type = _voice_queue_state["current_type"]

    if item_type == "draft":
        _voice_queue_state.update(current_item=None, current_type=None, current_id=None)
        return CommandResponse(reply="Deferred. What's next?", cards=[])

    elif item_type == "todo":
        with get_db() as conn:
            conn.execute(
                upsert(
                    todo_overrides,
                    values={"hub_todo_id": item_id, "status": "deferred", "updated_at": datetime.now(timezone.utc).isoformat()},
                    conflict_columns=["hub_todo_id"],
                    update_columns=["status", "updated_at"],
                )
            )
        _voice_queue_state.update(current_item=None, current_type=None, current_id=None)
        return CommandResponse(reply="Deferred. What's next?", cards=[])

    _voice_queue_state.update(current_item=None, current_type=None, current_id=None)
    return CommandResponse(reply="Deferred. What's next?", cards=[])


HANDLERS = {
    "cmd_process": cmd_process,
    "cmd_briefing": cmd_briefing,
    "cmd_overdue": cmd_overdue,
    "cmd_decide": cmd_decide,
    "cmd_todos": cmd_todos,
    "cmd_health": cmd_health,
    "cmd_costs": cmd_costs,
    "cmd_search": cmd_search,
    "cmd_chat": cmd_chat,
    "cmd_projects": cmd_projects,
    "cmd_dismiss": cmd_dismiss,
    "cmd_next_decision": cmd_next_decision,
    "cmd_voice_approve": cmd_voice_approve,
    "cmd_voice_reject": cmd_voice_reject,
    "cmd_voice_defer": cmd_voice_defer,
    "cmd_self_improve": cmd_self_improve,
}


# -- Claude fallback --

async def _claude_fallback(text_str: str) -> CommandResponse:
    system_prompt = (
        "You are CoCo, a concise AI assistant for a PM named Rijul. "
        "Answer in 1-2 short sentences, as if spoken aloud. Be helpful and direct."
    )
    history_ctx = _get_history_context()

    if USE_AGENT_SDK:
        from app.services.agent_sdk_client import agent_sdk
        if agent_sdk.is_available():
            try:
                prompt = ""
                if history_ctx:
                    prompt += f"[Recent conversation]\n{history_ctx}\n\n"
                prompt += f"[User message]\n{text_str[:2000]}"

                result = agent_sdk.quick_command(
                    prompt=prompt, model="haiku", system=system_prompt, max_tokens=512,
                    task_type="classification",
                )
                reply = result["content"].strip()
                if len(reply) > 300:
                    reply = reply[:297] + "..."

                from app.services.agent_sdk_client import record_sdk_cost
                record_sdk_cost(
                    model=result["model"], input_tokens=result["input_tokens"],
                    output_tokens=result["output_tokens"], source="chat",
                )

                return CommandResponse(
                    reply=reply, action="suggest_chat", url="/chat",
                    cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": reply, "suggest_chat": True})],
                )
            except Exception as e:
                log.warning("jarvis_sdk_fallback_failed", error=str(e))

    try:
        claude_path = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
        context_block = f"[System context]\n{system_prompt}\n"
        if history_ctx:
            context_block += f"\n[Recent conversation]\n{history_ctx}\n"
        context_block += f"\n[User message]\n{text_str[:2000]}"
        proc = await asyncio.to_thread(
            subprocess.run,
            [claude_path, "-p", "--model", "haiku"],
            input=context_block,
            capture_output=True, text=True, timeout=15,
        )
        reply = proc.stdout.strip() if proc.stdout else "I didn't catch that. Try process, briefing, or todos."
        if len(reply) > 300:
            reply = reply[:297] + "..."
        return CommandResponse(
            reply=reply, action="suggest_chat", url="/chat",
            cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": reply, "suggest_chat": True})],
        )
    except Exception as e:
        log.warning("jarvis_claude_fallback_failed", error=str(e))
        return CommandResponse(
            reply="I didn't understand that. Try process, briefing, todos, or search.",
            cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": "Try: process, briefing, todos, health, search, or ask anything."})],
        )


# -- Endpoint --

@router.post("/api/jarvis/command", response_model=CommandResponse)
async def jarvis_command(req: CommandRequest):
    todo_title = _extract_create_todo(req.text)
    if todo_title:
        result = await _handle_create_todo(todo_title)
        _record_exchange(req.text, result.reply, result.cards)
        return result

    draft_id = _extract_approve_draft(req.text)
    if draft_id:
        result = await _handle_approve_draft(draft_id)
        _record_exchange(req.text, result.reply, result.cards)
        return result

    handler_name, remaining = _match_command(req.text)
    if handler_name and handler_name in HANDLERS:
        result = await HANDLERS[handler_name](remaining=remaining)
        _record_exchange(req.text, result.reply, result.cards)
        return result

    result = await _claude_fallback(req.text)
    _record_exchange(req.text, result.reply, result.cards)
    return result


@router.get("/api/jarvis/self-improve-summary")
def jarvis_self_improve_summary():
    """Return the latest self-improvement cycle summary for Jarvis voice queue."""
    try:
        with get_db() as conn:
            row = conn.execute(
                select(
                    self_improve_cycles.c.id,
                    self_improve_cycles.c.status,
                    self_improve_cycles.c.budget_usd,
                    self_improve_cycles.c.spent_usd,
                    self_improve_cycles.c.max_improvements,
                    self_improve_cycles.c.started_at,
                    self_improve_cycles.c.completed_at,
                )
                .where(self_improve_cycles.c.status.in_(["completed", "rejected"]))
                .order_by(self_improve_cycles.c.completed_at.desc())
                .limit(1)
            ).fetchone()
            if not row:
                return {"summary": None, "message": "No completed self-improvement cycles."}

            cycle = dict(row._mapping)
            cycle_id = cycle["id"]

            imp_rows = conn.execute(
                select(self_improve_improvements.c.title)
                .where(self_improve_improvements.c.cycle_id == cycle_id)
                .where(self_improve_improvements.c.status.in_(
                    ["approved_by_human", "merged", "awaiting_approval"]
                ))
                .order_by(self_improve_improvements.c.priority)
                .limit(5)
            ).fetchall()
            titles = [r._mapping["title"] for r in imp_rows]

            imp_count_row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(self_improve_improvements)
                .where(self_improve_improvements.c.cycle_id == cycle_id)
                .where(self_improve_improvements.c.status.in_(
                    ["approved_by_human", "merged"]
                ))
            ).fetchone()
            imp_count = imp_count_row._mapping["cnt"] if imp_count_row else 0

        spent = cycle.get("spent_usd", 0) or 0
        if imp_count == 0:
            summary = f"Self-improvement cycle finished. No improvements were applied. Cost: ${spent:.2f}."
        else:
            changes_desc = ", ".join(titles[:3])
            if len(titles) > 3:
                changes_desc += f", and {len(titles) - 3} more"
            summary = (
                f"I improved {imp_count} file{'s' if imp_count != 1 else ''} overnight. "
                f"{changes_desc}. Total cost: ${spent:.2f}."
            )

        return {
            "summary": summary,
            "cycle_id": cycle_id,
            "improvements_count": imp_count,
            "spent_usd": spent,
            "titles": titles,
        }
    except Exception as e:
        log.warning("jarvis_self_improve_summary_failed", error=str(e))
        return {"summary": None, "message": str(e)}


@router.get("/api/jarvis/history")
def jarvis_history(limit: int = Query(default=20, ge=1, le=100)):
    return _get_recent_history(limit)


@router.delete("/api/jarvis/history")
def jarvis_clear_history():
    try:
        with get_db() as conn:
            conn.execute(delete(jarvis_sessions))
        return {"ok": True, "message": "History cleared."}
    except Exception as e:
        log.warning("jarvis_clear_history_failed", error=str(e))
        return {"ok": False, "message": str(e)}
