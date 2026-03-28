"""Jarvis command endpoint — lightweight, non-streaming command interpreter.

Returns structured card data alongside spoken replies for visual rendering.
"""

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

from app.db.connections import get_hub_db, get_platform_db
from app.models.jarvis import (
    CardActionModel,
    CardDataModel,
    CommandRequest,
    CommandResponse,
)
from app.routers.home import get_home, _build_briefing

log = structlog.get_logger()

router = APIRouter(tags=["Jarvis"])


# ─── Session Memory (DB-backed via jarvis_sessions table) ────────────────────


def _record_exchange(user_text: str, reply: str, cards: list | None = None) -> None:
    """Store a command+response pair in the jarvis_sessions DB table."""
    try:
        cards_json = json.dumps([c.model_dump() if hasattr(c, 'model_dump') else c for c in (cards or [])]) if cards else None
        with get_platform_db() as db:
            db.execute(
                "INSERT INTO jarvis_sessions (command, response_summary, cards_json) VALUES (?, ?, ?)",
                (user_text[:500], reply[:500], cards_json),
            )
            db.commit()
    except Exception as e:
        log.warning("jarvis_record_exchange_failed", error=str(e))


def _get_history_context() -> str:
    """Build a context string from last 5 commands in DB for Claude fallback."""
    try:
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT command, response_summary FROM jarvis_sessions "
                "ORDER BY created_at DESC LIMIT 5"
            ).fetchall()
        if not rows:
            return ""
        lines = []
        for entry in reversed(rows):
            lines.append(f"User: {entry['command']}")
            lines.append(f"Assistant: {entry['response_summary']}")
        return "\n".join(lines)
    except Exception:
        return ""


def _get_recent_history(limit: int = 20) -> list[dict]:
    """Return recent Jarvis interactions from DB."""
    try:
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT id, command, response_summary, cards_json, created_at "
                "FROM jarvis_sessions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        log.warning("jarvis_get_history_failed", error=str(e))
        return []


# ─── Inline Action Extraction ────────────────────────────────────────────────

def _extract_create_todo(text: str) -> str | None:
    """Extract a todo title from commands like 'create todo: Review 3Pi contract'."""
    for pat in [
        r"create\s+todo[:\s]+(.+)",
        r"add\s+todo[:\s]+(.+)",
        r"new\s+todo[:\s]+(.+)",
        r"remind\s+me\s+to\s+(.+)",
    ]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def _extract_approve_draft(text: str) -> str | None:
    """Extract a draft ID from commands like 'approve draft abc123'."""
    for pat in [r"approve\s+draft\s+(\S+)"]:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


async def _handle_create_todo(title: str) -> CommandResponse:
    """Create a todo via the todos endpoint logic."""
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
    """Approve a draft via the drafts endpoint logic."""
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


# ─── Command Patterns ─────────────────────────────────────────────────────────

COMMAND_PATTERNS = [
    # Voice decision queue commands (checked first — short voice utterances)
    (["next decision", "next item", "what's next in queue", "whats next"], "cmd_next_decision"),
    (["approve it", "approve", "yes", "looks good", "lgtm"], "cmd_voice_approve"),
    (["reject it", "reject", "no", "pass on this"], "cmd_voice_reject"),
    (["defer", "later", "snooze", "come back to this"], "cmd_voice_defer"),
    # General commands
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
]


def _match_command(text: str) -> tuple[str | None, str]:
    lower = text.lower().strip()
    for keywords, handler in COMMAND_PATTERNS:
        for kw in keywords:
            if kw in lower:
                idx = lower.find(kw)
                remaining = text[idx + len(kw):].strip().lstrip("for").strip()
                return handler, remaining
    return None, text


# ─── Handlers ─────────────────────────────────────────────────────────────────

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
            log.warning("cmd_process_failed", stderr=proc.stderr, returncode=proc.returncode)
    except subprocess.TimeoutExpired:
        status = "timeout"
        log.warning("cmd_process_timeout")
    except Exception as e:
        status = "error"
        log.warning("cmd_process_error", error=str(e))

    reply = {
        "ok": "Processing pipeline complete. New content ingested.",
        "timeout": "Process is still running in background (timed out after 30s).",
        "error": "Process encountered an error. Check KH logs.",
    }.get(status, "Process triggered.")

    return CommandResponse(
        reply=reply,
        cards=[CardDataModel(
            id=_card_id(),
            type="health_detail",
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
    return CommandResponse(
        reply=script,
        cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": script})],
    )


async def cmd_overdue(**_) -> CommandResponse:
    try:
        with get_hub_db() as db:
            rows = db.execute(
                "SELECT t.id, t.title, t.status, t.priority, t.due_date, t.project_id, "
                "p.name as project_name "
                "FROM todos t LEFT JOIN projects p ON t.project_id = p.id "
                "WHERE t.status = 'open' AND t.due_date < date('now', 'localtime') "
                "ORDER BY t.due_date ASC LIMIT 10"
            ).fetchall()
            if not rows:
                return CommandResponse(
                    reply="Nothing overdue. You're in good shape.",
                    cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": "Nothing overdue. You're in good shape."})],
                )
            items = [dict(r) for r in rows]
            count = len(items)
            reply = f"{count} overdue item{'s' if count != 1 else ''}. "
            reply += ". ".join(r["title"] for r in items[:3])
            if count > 3:
                reply += f". And {count - 3} more."
            return CommandResponse(
                reply=reply,
                cards=[CardDataModel(
                    id=_card_id(),
                    type="todo_list",
                    data={"title": f"Overdue Items ({count})", "todos": items},
                )],
            )
    except Exception as e:
        log.warning("cmd_overdue_error", error=str(e))
        return CommandResponse(reply="Couldn't check overdue items.", cards=[])


async def cmd_decide(**_) -> CommandResponse:
    try:
        with get_hub_db() as db:
            rows = db.execute(
                "SELECT d.id, d.project_id, d.template, d.section, d.status, d.created_at, "
                "p.name as project_name "
                "FROM drafts d LEFT JOIN projects p ON d.project_id = p.id "
                "WHERE d.status = 'pending' ORDER BY d.created_at DESC LIMIT 10"
            ).fetchall()
            if not rows:
                return CommandResponse(
                    reply="No pending drafts. Your queue is clean.",
                    cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": "No pending drafts."})],
                )
            drafts = [
                {
                    "id": r["id"],
                    "title": f"{r['template']} → {r['section']}",
                    "project_name": r["project_name"] or r["project_id"] or "Unknown",
                    "draft_type": r["template"],
                    "preview": f"Draft for {r['project_name'] or r['project_id'] or 'unknown'}: {r['template']} / {r['section']}",
                }
                for r in rows
            ]
            return CommandResponse(
                reply=f"{len(drafts)} drafts pending your review.",
                cards=[CardDataModel(
                    id=_card_id(),
                    type="approval_batch",
                    data={"drafts": drafts},
                )],
            )
    except Exception as e:
        log.warning("cmd_decide_error", error=str(e))
        return CommandResponse(reply="Opening your decision queue.", action="navigate", url="/inbox", cards=[])


async def cmd_todos(**_) -> CommandResponse:
    try:
        with get_hub_db() as db:
            rows = db.execute(
                "SELECT t.id, t.title, t.status, t.priority, t.due_date, t.project_id, "
                "p.name as project_name "
                "FROM todos t LEFT JOIN projects p ON t.project_id = p.id "
                "WHERE t.status = 'open' AND t.priority = 'high' "
                "ORDER BY t.due_date ASC NULLS LAST LIMIT 10"
            ).fetchall()
            total = db.execute("SELECT COUNT(*) as cnt FROM todos WHERE status = 'open'").fetchone()
            total_count = total["cnt"] if total else 0
            items = [dict(r) for r in rows]
            reply = f"You have {total_count} open todos, {len(items)} high priority."
            return CommandResponse(
                reply=reply,
                cards=[CardDataModel(
                    id=_card_id(),
                    type="todo_list",
                    data={"title": f"High Priority ({len(items)})", "todos": items},
                )],
            )
    except Exception as e:
        log.warning("cmd_todos_error", error=str(e))
        return CommandResponse(reply="Opening your todo list.", action="navigate", url="/todos", cards=[])


async def cmd_health(**_) -> CommandResponse:
    try:
        with get_hub_db() as db:
            rows = db.execute("SELECT source_name, last_success, items_synced FROM sync_state").fetchall()
            now = datetime.now(timezone.utc)
            sources = []
            parts = []
            for r in rows:
                name = r["source_name"]
                stale_hours = None
                status = "ok"
                if r["last_success"]:
                    ts = datetime.fromisoformat(r["last_success"].replace("Z", "+00:00"))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    stale_hours = (now - ts).total_seconds() / 3600
                    if stale_hours > 24:
                        status = "red"
                        parts.append(f"{name.title()}: {stale_hours/24:.0f} days ago, needs attention")
                    else:
                        parts.append(f"{name.title()}: {stale_hours:.0f} hours ago, healthy")
                else:
                    status = "red"
                    parts.append(f"{name.title()}: never synced")
                sources.append({
                    "source": name, "status": status,
                    "stale_hours": stale_hours,
                    "last_sync": r["last_success"],
                    "items_synced": r["items_synced"] or 0,
                })
            # Overall pct
            scores = [100 if (s["stale_hours"] or 999) < 12 else 60 if (s["stale_hours"] or 999) < 24 else 20 for s in sources]
            overall = sum(scores) / len(scores) if scores else 100
            return CommandResponse(
                reply=". ".join(parts) + ".",
                cards=[CardDataModel(
                    id=_card_id(),
                    type="health_detail",
                    data={"sources": sources, "overall_pct": round(overall)},
                    actions=[CardActionModel(label="Run Process", action="process", endpoint="/home/process", method="POST")],
                )],
            )
    except Exception as e:
        log.warning("cmd_health_error", error=str(e))
        return CommandResponse(reply="Couldn't check system health.", cards=[])


async def cmd_costs(**_) -> CommandResponse:
    # Always call get_home() fresh — it queries DB directly, no cache
    data = get_home()
    costs = data.get("costs", {}) if data else {}
    today = costs.get("today_usd", 0)
    month = costs.get("month_usd", 0)
    return CommandResponse(
        reply=f"Today: ${today:.2f}. This month: ${month:.2f}.",
        cards=[CardDataModel(
            id=_card_id(),
            type="metric_grid",
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
    return CommandResponse(
        reply="Opening chat with Claude.",
        action="navigate", url="/chat",
        cards=[CardDataModel(id=_card_id(), type="navigate_hint", data={"destination": "Chat", "url": "/chat"})],
    )


async def cmd_projects(**_) -> CommandResponse:
    data = get_home()
    projects = [p for p in data.get("projects", []) if p.get("active")][:6]
    cards = []
    for p in projects:
        cards.append(CardDataModel(
            id=_card_id(),
            type="project_detail",
            data={
                "id": p["id"], "name": p["name"],
                "email_count": p.get("sources", {}).get("email", 0),
                "jira_count": p.get("sources", {}).get("jira", 0),
                "todo_open": p.get("todo_open", 0),
                "todo_done": p.get("todo_done", 0),
                "recent_activity": [],
            },
        ))
    return CommandResponse(
        reply=f"{len(projects)} active projects.",
        cards=cards,
    )


async def cmd_dismiss(**_) -> CommandResponse:
    return CommandResponse(reply="Dismissed.", cards=[])


# ─── Voice Decision Queue State ─────────────────────────────────────────────

_voice_queue_state: dict = {"current_item": None, "current_type": None, "current_id": None}


async def cmd_next_decision(**_) -> CommandResponse:
    """Fetch the next pending decision item for voice-driven queue processing."""
    # Try pending drafts first (excluding already-decided ones in platform.db)
    try:
        decided_ids: list[str] = []
        with get_platform_db() as pdb:
            rows = pdb.execute("SELECT hub_draft_id FROM draft_decisions").fetchall()
            decided_ids = [r["hub_draft_id"] for r in rows]

        with get_hub_db() as db:
            if decided_ids:
                placeholders = ",".join("?" for _ in decided_ids)
                draft = db.execute(
                    f"SELECT id, template, section, project_id, created_at FROM drafts "
                    f"WHERE status = 'pending' AND id NOT IN ({placeholders}) "
                    f"ORDER BY created_at LIMIT 1",
                    decided_ids,
                ).fetchone()
            else:
                draft = db.execute(
                    "SELECT id, template, section, project_id, created_at FROM drafts "
                    "WHERE status = 'pending' ORDER BY created_at LIMIT 1"
                ).fetchone()

            if draft:
                _voice_queue_state["current_item"] = dict(draft)
                _voice_queue_state["current_type"] = "draft"
                _voice_queue_state["current_id"] = draft["id"]
                project = draft["project_id"] or "unknown project"
                reply = f"Pending draft: {draft['template']} for {project}. Approve, reject, or defer?"
                return CommandResponse(
                    reply=reply,
                    cards=[CardDataModel(
                        id=_card_id(), type="approval_batch",
                        data={"drafts": [dict(draft)]},
                    )],
                )
    except Exception as e:
        log.warning("cmd_next_decision_drafts_error", error=str(e))

    # Try overdue todos (excluding already-overridden ones in platform.db)
    try:
        overridden_ids: list[str] = []
        with get_platform_db() as pdb:
            rows = pdb.execute(
                "SELECT hub_todo_id FROM todo_overrides WHERE status IN ('done', 'archived', 'deferred')"
            ).fetchall()
            overridden_ids = [r["hub_todo_id"] for r in rows]

        with get_hub_db() as db:
            if overridden_ids:
                placeholders = ",".join("?" for _ in overridden_ids)
                todo = db.execute(
                    f"SELECT id, title, priority, due_date FROM todos "
                    f"WHERE status = 'open' AND due_date < date('now') AND id NOT IN ({placeholders}) "
                    f"ORDER BY due_date LIMIT 1",
                    overridden_ids,
                ).fetchone()
            else:
                todo = db.execute(
                    "SELECT id, title, priority, due_date FROM todos "
                    "WHERE status = 'open' AND due_date < date('now') ORDER BY due_date LIMIT 1"
                ).fetchone()

            if todo:
                _voice_queue_state["current_item"] = dict(todo)
                _voice_queue_state["current_type"] = "todo"
                _voice_queue_state["current_id"] = todo["id"]
                reply = f"Overdue: {todo['title']}. Due {todo['due_date']}. Mark done, defer, or skip?"
                return CommandResponse(
                    reply=reply,
                    cards=[CardDataModel(
                        id=_card_id(), type="todo_list",
                        data={"title": "Overdue", "todos": [dict(todo)]},
                    )],
                )
    except Exception as e:
        log.warning("cmd_next_decision_todos_error", error=str(e))

    _voice_queue_state["current_item"] = None
    _voice_queue_state["current_type"] = None
    _voice_queue_state["current_id"] = None
    return CommandResponse(reply="Queue is clear. Nothing pending.", cards=[])


async def cmd_voice_approve(**_) -> CommandResponse:
    """Approve the most recently shown decision queue item."""
    if not _voice_queue_state["current_id"]:
        return CommandResponse(reply="Nothing to approve. Say 'next' first.", cards=[])

    item_id = _voice_queue_state["current_id"]
    item_type = _voice_queue_state["current_type"]

    if item_type == "draft":
        with get_platform_db() as pdb:
            pdb.execute(
                "INSERT OR REPLACE INTO draft_decisions (id, hub_draft_id, status, decided_by) VALUES (?, ?, 'approved', 'voice')",
                (uuid.uuid4().hex, item_id),
            )
            pdb.commit()
        _voice_queue_state["current_item"] = None
        _voice_queue_state["current_type"] = None
        _voice_queue_state["current_id"] = None
        return CommandResponse(reply="Approved. Say 'next' for the next item.", cards=[])

    elif item_type == "todo":
        with get_platform_db() as pdb:
            pdb.execute(
                "INSERT OR REPLACE INTO todo_overrides (hub_todo_id, status, updated_at) VALUES (?, 'done', datetime('now'))",
                (item_id,),
            )
            pdb.commit()
        _voice_queue_state["current_item"] = None
        _voice_queue_state["current_type"] = None
        _voice_queue_state["current_id"] = None
        return CommandResponse(reply="Marked done. Say 'next' for the next item.", cards=[])

    return CommandResponse(reply="Done.", cards=[])


async def cmd_voice_reject(**_) -> CommandResponse:
    """Reject the most recently shown decision queue item."""
    if not _voice_queue_state["current_id"]:
        return CommandResponse(reply="Nothing to reject. Say 'next' first.", cards=[])

    item_id = _voice_queue_state["current_id"]
    item_type = _voice_queue_state["current_type"]

    if item_type == "draft":
        with get_platform_db() as pdb:
            pdb.execute(
                "INSERT OR REPLACE INTO draft_decisions (id, hub_draft_id, status, decided_by) VALUES (?, ?, 'rejected', 'voice')",
                (uuid.uuid4().hex, item_id),
            )
            pdb.commit()
        _voice_queue_state["current_item"] = None
        _voice_queue_state["current_type"] = None
        _voice_queue_state["current_id"] = None
        return CommandResponse(reply="Rejected. Say 'next' for the next item.", cards=[])

    elif item_type == "todo":
        with get_platform_db() as pdb:
            pdb.execute(
                "INSERT OR REPLACE INTO todo_overrides (hub_todo_id, status, updated_at) VALUES (?, 'archived', datetime('now'))",
                (item_id,),
            )
            pdb.commit()
        _voice_queue_state["current_item"] = None
        _voice_queue_state["current_type"] = None
        _voice_queue_state["current_id"] = None
        return CommandResponse(reply="Skipped. Say 'next' for the next item.", cards=[])

    return CommandResponse(reply="Done.", cards=[])


async def cmd_voice_defer(**_) -> CommandResponse:
    """Defer the most recently shown decision queue item."""
    if not _voice_queue_state["current_id"]:
        return CommandResponse(reply="Nothing to defer. Say 'next' first.", cards=[])

    item_id = _voice_queue_state["current_id"]
    item_type = _voice_queue_state["current_type"]

    if item_type == "draft":
        # For drafts, we just clear state — no overlay record, so it will reappear next time
        _voice_queue_state["current_item"] = None
        _voice_queue_state["current_type"] = None
        _voice_queue_state["current_id"] = None
        return CommandResponse(reply="Deferred. What's next?", cards=[])

    elif item_type == "todo":
        with get_platform_db() as pdb:
            pdb.execute(
                "INSERT OR REPLACE INTO todo_overrides (hub_todo_id, status, updated_at) VALUES (?, 'deferred', datetime('now'))",
                (item_id,),
            )
            pdb.commit()
        _voice_queue_state["current_item"] = None
        _voice_queue_state["current_type"] = None
        _voice_queue_state["current_id"] = None
        return CommandResponse(reply="Deferred. What's next?", cards=[])

    _voice_queue_state["current_item"] = None
    _voice_queue_state["current_type"] = None
    _voice_queue_state["current_id"] = None
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
}


# ─── Claude fallback ─────────────────────────────────────────────────────────

async def _claude_fallback(text: str) -> CommandResponse:
    try:
        claude_path = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
        system_prompt = (
            "You are CoCo, a concise AI assistant for a PM named Rijul. "
            "Answer in 1-2 short sentences, as if spoken aloud. Be helpful and direct."
        )
        # Include recent session history as context
        history_ctx = _get_history_context()
        context_block = f"[System context]\n{system_prompt}\n"
        if history_ctx:
            context_block += f"\n[Recent conversation]\n{history_ctx}\n"
        context_block += f"\n[User message]\n{text[:2000]}"
        # Pass user text via stdin to avoid command-line injection
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
            reply=reply,
            action="suggest_chat",
            url="/chat",
            cards=[CardDataModel(
                id=_card_id(), type="text_response",
                data={"text": reply, "suggest_chat": True},
            )],
        )
    except Exception as e:
        log.warning("jarvis_claude_fallback_failed", error=str(e))
        return CommandResponse(
            reply="I didn't understand that. Try process, briefing, todos, or search.",
            cards=[CardDataModel(id=_card_id(), type="text_response", data={"text": "Try: process, briefing, todos, health, search, or ask anything."})],
        )


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/api/jarvis/command", response_model=CommandResponse)
async def jarvis_command(req: CommandRequest):
    # ─── Inline actions: create todo, approve draft ───
    todo_title = _extract_create_todo(req.text)
    if todo_title:
        log.info("jarvis_inline_action", action="create_todo", title=todo_title[:50])
        result = await _handle_create_todo(todo_title)
        _record_exchange(req.text, result.reply, result.cards)
        return result

    draft_id = _extract_approve_draft(req.text)
    if draft_id:
        log.info("jarvis_inline_action", action="approve_draft", draft_id=draft_id)
        result = await _handle_approve_draft(draft_id)
        _record_exchange(req.text, result.reply, result.cards)
        return result

    # ─── Standard command matching ───
    handler_name, remaining = _match_command(req.text)
    if handler_name and handler_name in HANDLERS:
        log.info("jarvis_command", handler=handler_name, text=req.text[:50])
        result = await HANDLERS[handler_name](remaining=remaining)
        _record_exchange(req.text, result.reply, result.cards)
        return result

    # ─── Claude fallback ───
    log.info("jarvis_command_fallback", text=req.text[:50])
    result = await _claude_fallback(req.text)
    _record_exchange(req.text, result.reply, result.cards)
    return result


@router.get("/api/jarvis/history")
def jarvis_history(limit: int = Query(default=20, ge=1, le=100)):
    """Return recent Jarvis command interactions."""
    return _get_recent_history(limit)


@router.delete("/api/jarvis/history")
def jarvis_clear_history():
    """Clear all Jarvis session history."""
    try:
        with get_platform_db() as db:
            db.execute("DELETE FROM jarvis_sessions")
            db.commit()
        return {"ok": True, "message": "History cleared."}
    except Exception as e:
        log.warning("jarvis_clear_history_failed", error=str(e))
        return {"ok": False, "message": str(e)}
