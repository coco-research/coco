import asyncio
import json
import random
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import structlog
from fastapi import APIRouter
from sqlalchemy import select, func, text

from app.db.session import get_db
from app.db.tables import (
    hub_content, hub_project_content, hub_drafts, hub_todos,
    hub_projects, hub_api_costs, hub_sync_state,
    tasks, cost_ledger,
)

log = structlog.get_logger()

router = APIRouter(tags=["Home"])

SESSIONS_DIR = Path.home() / ".coco" / "sessions"


def _greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    return "Good evening"


def _formatted_date() -> str:
    now = datetime.now()
    return f"{now.strftime('%A, %B')} {now.day}"


def _session_data() -> dict:
    """Read most recent session file once, return all needed fields."""
    result = {
        "since": {"hours_ago": None, "label": None},
        "info": {"last_started": None, "last_focus": None, "last_launch_type": None},
    }
    try:
        if not SESSIONS_DIR.exists():
            return result
        files = sorted(
            SESSIONS_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if not files:
            return result
        data = json.loads(files[0].read_text())

        started = data.get("started_at")
        if started:
            started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            hours = (
                datetime.now(started_dt.tzinfo or timezone.utc) - started_dt
            ).total_seconds() / 3600
            hours = round(hours, 1)
            result["since"]["hours_ago"] = hours
            if hours < 1:
                result["since"]["label"] = f"{int(hours * 60)}m ago"
            elif hours < 24:
                result["since"]["label"] = f"{hours:.1f}h ago"
            else:
                result["since"]["label"] = f"{hours / 24:.1f}d ago"

        result["info"]["last_started"] = data.get("started_at")
        result["info"]["last_focus"] = data.get("focus_project")
        result["info"]["last_launch_type"] = data.get("launch_type")
        return result
    except Exception:
        log.warning("home_session_read_failed", exc_info=True)
        return result


def _health_from_sync_state(conn) -> list[dict]:
    """Read hub_sync_state table and compute stale_hours."""
    try:
        rows = conn.execute(
            select(hub_sync_state)
        ).fetchall()
        now = datetime.now(timezone.utc)
        health = []
        for r in rows:
            h = dict(r._mapping)
            # Normalize field names
            h["source"] = h.pop("source", h.get("source_name", "unknown"))
            h["last_sync"] = h.get("last_sync") or h.get("last_success")
            # Compute stale_hours
            stale_hours = None
            if h.get("last_sync"):
                try:
                    ts = datetime.fromisoformat(
                        h["last_sync"].replace("Z", "+00:00")
                    )
                    stale_hours = round((now - ts).total_seconds() / 3600, 1)
                except Exception:
                    pass
            h["stale_hours"] = stale_hours
            health.append(h)
        return health
    except Exception:
        log.warning("home_health_query_failed", exc_info=True)
        return []


@router.get("/api/home")
def get_home():
    session = _session_data()

    result: dict = {
        "greeting": _greeting(),
        "date": _formatted_date(),
        "since_last_session": session["since"],
        "attention": {
            "unsorted_count": 0,
            "pending_drafts": 0,
            "overdue_todos": 0,
            "health_alerts": 0,
        },
        "health": [],
        "todos": {
            "total_open": 0,
            "high_priority": [],
            "medium_priority": [],
            "overdue": [],
        },
        "projects": [],
        "queue": {"total": 0, "urgent": 0, "drafts": 0, "classify": 0},
        "costs": {"today_usd": 0.0, "month_usd": 0.0},
        "session": session["info"],
    }

    with get_db() as conn:
        # --- Hub mirror queries ---

        # Attention: unsorted count
        try:
            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(hub_content)
                .where(hub_content.c.id.notin_(select(hub_project_content.c.content_id)))
            ).fetchone()
            result["attention"]["unsorted_count"] = row.cnt if row else 0
        except Exception:
            log.warning("home_query_failed", section="unsorted_count", exc_info=True)

        # Attention: pending drafts
        try:
            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(hub_drafts)
                .where(hub_drafts.c.status == "pending")
            ).fetchone()
            result["attention"]["pending_drafts"] = row.cnt if row else 0
        except Exception:
            log.warning("home_query_failed", section="pending_drafts", exc_info=True)

        # Attention: overdue todos
        try:
            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(hub_todos)
                .where(hub_todos.c.status == "open")
                .where(hub_todos.c.due_date < text("date('now', 'localtime')"))
            ).fetchone()
            result["attention"]["overdue_todos"] = row.cnt if row else 0
        except Exception:
            log.warning("home_query_failed", section="overdue_todos", exc_info=True)

        # Health
        try:
            health = _health_from_sync_state(conn)
            result["health"] = health
            result["attention"]["health_alerts"] = sum(
                1 for h in health if h.get("status") in ("red", "critical")
            )
        except Exception:
            log.warning("home_query_failed", section="health", exc_info=True)

        # Todos
        try:
            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(hub_todos)
                .where(hub_todos.c.status == "open")
            ).fetchone()
            result["todos"]["total_open"] = row.cnt if row else 0

            _todo_cols = [
                hub_todos.c.id, hub_todos.c.title, hub_todos.c.project_id,
                hub_todos.c.owner, hub_todos.c.due_date, hub_todos.c.priority,
                hub_todos.c.status, hub_todos.c.source_type, hub_todos.c.jira_key,
                hub_todos.c.tags,
            ]

            high = conn.execute(
                select(*_todo_cols)
                .where(hub_todos.c.status == "open", hub_todos.c.priority == "high")
                .order_by(hub_todos.c.created_at.desc())
                .limit(50)
            ).fetchall()
            result["todos"]["high_priority"] = [dict(r._mapping) for r in high]

            medium = conn.execute(
                select(*_todo_cols)
                .where(hub_todos.c.status == "open", hub_todos.c.priority == "medium")
                .order_by(hub_todos.c.created_at.desc())
                .limit(20)
            ).fetchall()
            result["todos"]["medium_priority"] = [dict(r._mapping) for r in medium]

            overdue = conn.execute(
                select(*_todo_cols)
                .where(hub_todos.c.status == "open")
                .where(hub_todos.c.due_date < text("date('now', 'localtime')"))
                .order_by(hub_todos.c.due_date.asc())
                .limit(50)
            ).fetchall()
            result["todos"]["overdue"] = [dict(r._mapping) for r in overdue]
        except Exception:
            log.warning("home_query_failed", section="todos", exc_info=True)

        # Projects with todo counts and source breakdown
        try:
            todo_open_sq = (
                select(func.count())
                .select_from(hub_todos)
                .where(hub_todos.c.project_id == hub_projects.c.id, hub_todos.c.status == "open")
                .correlate(hub_projects)
                .scalar_subquery()
                .label("todo_open")
            )
            todo_done_sq = (
                select(func.count())
                .select_from(hub_todos)
                .where(hub_todos.c.project_id == hub_projects.c.id, hub_todos.c.status == "done")
                .correlate(hub_projects)
                .scalar_subquery()
                .label("todo_done")
            )
            todo_total_sq = (
                select(func.count())
                .select_from(hub_todos)
                .where(hub_todos.c.project_id == hub_projects.c.id)
                .correlate(hub_projects)
                .scalar_subquery()
                .label("todo_total")
            )
            item_count_sq = (
                select(func.count())
                .select_from(hub_project_content)
                .where(hub_project_content.c.project_id == hub_projects.c.id)
                .correlate(hub_projects)
                .scalar_subquery()
                .label("item_count")
            )

            rows = conn.execute(
                select(
                    hub_projects.c.id,
                    hub_projects.c.name,
                    hub_projects.c.active,
                    item_count_sq,
                    todo_open_sq,
                    todo_done_sq,
                    todo_total_sq,
                ).order_by(hub_projects.c.name)
            ).fetchall()
            projects = []
            for r in rows:
                p = dict(r._mapping)
                sources = {"email": 0, "voice": 0, "jira": 0, "confluence": 0}
                try:
                    src_rows = conn.execute(
                        select(hub_content.c.source, func.count().label("count"))
                        .join(hub_project_content, hub_content.c.id == hub_project_content.c.content_id)
                        .where(hub_project_content.c.project_id == p["id"])
                        .group_by(hub_content.c.source)
                    ).fetchall()
                    for sr in src_rows:
                        sources[sr.source] = sr.count
                except Exception:
                    log.warning("home_query_failed", section="project_sources", exc_info=True)
                p["sources"] = sources
                projects.append(p)
            result["projects"] = projects
        except Exception:
            log.warning("home_query_failed", section="projects", exc_info=True)

        # Costs from hub api_costs mirror
        try:
            row = conn.execute(
                select(func.coalesce(func.sum(hub_api_costs.c.cost_usd), 0).label("total"))
                .where(hub_api_costs.c.created_at >= text("date('now')"))
            ).fetchone()
            result["costs"]["today_usd"] += round(row.total, 4) if row else 0.0
        except Exception:
            log.warning("home_query_failed", section="hub_costs_today", exc_info=True)

        try:
            row = conn.execute(
                select(func.coalesce(func.sum(hub_api_costs.c.cost_usd), 0).label("total"))
                .where(hub_api_costs.c.created_at >= text("date('now', 'start of month')"))
            ).fetchone()
            result["costs"]["month_usd"] += round(row.total, 4) if row else 0.0
        except Exception:
            log.warning("home_query_failed", section="hub_costs_month", exc_info=True)

        # --- Platform queries ---

        # Queue: tasks
        try:
            row_urgent = conn.execute(
                select(func.count().label("cnt"))
                .select_from(tasks)
                .where(tasks.c.status == "open", tasks.c.priority == "high")
            ).fetchone()
            result["queue"]["urgent"] = row_urgent.cnt if row_urgent else 0
        except Exception:
            log.warning("home_query_failed", section="platform_tasks", exc_info=True)

        # Costs from platform cost_ledger
        try:
            row = conn.execute(
                select(func.coalesce(func.sum(cost_ledger.c.cost_usd), 0).label("total"))
                .where(cost_ledger.c.created_at >= text("date('now')"))
            ).fetchone()
            result["costs"]["today_usd"] += round(row.total, 4) if row else 0.0
        except Exception:
            log.warning("home_query_failed", section="platform_costs_today", exc_info=True)

        try:
            row = conn.execute(
                select(func.coalesce(func.sum(cost_ledger.c.cost_usd), 0).label("total"))
                .where(cost_ledger.c.created_at >= text("date('now', 'start of month')"))
            ).fetchone()
            result["costs"]["month_usd"] += round(row.total, 4) if row else 0.0
        except Exception:
            log.warning("home_query_failed", section="platform_costs_month", exc_info=True)

    # Queue: drafts + classify from attention counts
    result["queue"]["drafts"] = result["attention"]["pending_drafts"]
    result["queue"]["classify"] = result["attention"]["unsorted_count"]
    result["queue"]["total"] = (
        result["queue"]["urgent"]
        + result["queue"]["drafts"]
        + result["queue"]["classify"]
    )

    result["costs"]["today_usd"] = round(result["costs"]["today_usd"], 4)
    result["costs"]["month_usd"] = round(result["costs"]["month_usd"], 4)

    return result


SNAPSHOT_PATH = Path.home() / ".coco" / "jarvis_snapshot.json"


def _read_snapshot() -> dict | None:
    try:
        if SNAPSHOT_PATH.exists():
            return json.loads(SNAPSHOT_PATH.read_text())
    except Exception:
        pass
    return None


def _write_snapshot(data: dict) -> None:
    try:
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = SNAPSHOT_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        tmp.rename(SNAPSHOT_PATH)
    except Exception:
        log.warning("jarvis_snapshot_write_failed", exc_info=True)


SOURCE_DISPLAY = {"jira": "Jira", "confluence": "Confluence", "email": "Email", "voice": "Voice"}


def _display_source(name: str) -> str:
    return SOURCE_DISPLAY.get(name, name.title())


def _build_briefing(current: dict) -> dict:
    """Generate a structured, Jarvis-style briefing with typed scenes."""
    scenes: list[dict] = []
    prev = _read_snapshot()

    hour = datetime.now().hour
    greetings = {
        "morning": [
            "Good morning, sir.",
            "Morning, Rijul. Systems are online.",
            "Good morning. Let's see what we're working with.",
        ],
        "afternoon": [
            "Good afternoon, sir.",
            "Afternoon, Rijul. Here's your status.",
            "Welcome back. Let me catch you up.",
        ],
        "evening": [
            "Good evening, sir.",
            "Evening, Rijul. Quick update before you settle in.",
            "Good evening. Still at it, I see.",
        ],
    }
    period = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
    greeting_text = random.choice(greetings[period])
    scenes.append({"type": "greeting", "text": greeting_text})

    since = current.get("since_last_session", {})
    hours_ago = since.get("hours_ago")
    if hours_ago is not None:
        if hours_ago < 0.5:
            scenes.append({"type": "context", "text": "You just stepped out for a moment."})
        elif hours_ago < 2:
            scenes.append({"type": "context", "text": f"You've been away about {int(hours_ago * 60)} minutes."})
        elif hours_ago < 24:
            scenes.append({"type": "context", "text": f"It's been {hours_ago:.0f} hours since your last session."})
        else:
            days = hours_ago / 24
            scenes.append({"type": "context", "text": f"It's been {days:.0f} day{'s' if days >= 2 else ''} since we last spoke."})

    attention = current.get("attention") or {}
    health = current.get("health") or []
    todos = current.get("todos") or {}
    projects = current.get("projects") or []

    stale = [h for h in health if h and (h.get("stale_hours") or 0) > 24]

    if prev:
        prev_attn = prev.get("attention") or {}
        prev_todos = prev.get("todos") or {}
        prev_health = prev.get("health") or []
        prev_stale_sources = {h.get("source", "") for h in prev_health if h and (h.get("stale_hours") or 0) > 24}

        newly_stale = [h for h in stale if h.get("source", "") not in prev_stale_sources]
        if newly_stale:
            names = " and ".join(_display_source(h["source"]) for h in newly_stale)
            hrs = newly_stale[0].get("stale_hours")
            scenes.append({
                "type": "alert",
                "text": f"{names} {'has' if len(newly_stale) == 1 else 'have'} gone stale — last sync {hrs / 24:.0f} days ago." if hrs and hrs > 48
                    else f"{names} sync is falling behind.",
                "severity": "high",
            })
            scenes.append({"type": "action", "text": "Want me to run a process?", "action": "process"})

        prev_overdue = prev_attn.get("overdue_todos") or 0
        curr_overdue = attention.get("overdue_todos") or 0
        if curr_overdue > prev_overdue:
            diff = curr_overdue - prev_overdue
            scenes.append({"type": "alert", "text": f"{diff} new item{'s' if diff != 1 else ''} went overdue.", "severity": "high"})

        prev_drafts = prev_attn.get("pending_drafts") or 0
        curr_drafts = attention.get("pending_drafts") or 0
        if curr_drafts > prev_drafts:
            diff = curr_drafts - prev_drafts
            scenes.append({"type": "metric", "text": f"{diff} new draft{'s' if diff != 1 else ''} to review.", "value": diff, "label": "new drafts"})

        prev_open = prev_todos.get("total_open") or 0
        curr_open = todos.get("total_open") or 0
        if curr_open > prev_open:
            diff = curr_open - prev_open
            scenes.append({"type": "metric", "text": f"{diff} new todo{'s' if diff != 1 else ''}.", "value": diff, "label": "new todos"})
        elif curr_open < prev_open:
            diff = prev_open - curr_open
            scenes.append({"type": "status", "text": f"You cleared {diff} todo{'s' if diff != 1 else ''}. Nice work."})

        prev_high = len(prev_todos.get("high_priority", []))
        curr_high = len(todos.get("high_priority", []))
        if curr_high > prev_high:
            scenes.append({"type": "alert", "text": f"{curr_high - prev_high} new high-priority item{'s' if curr_high - prev_high != 1 else ''}.", "severity": "medium"})

    else:
        if stale:
            names = " and ".join(_display_source(h["source"]) for h in stale)
            hrs = stale[0].get("stale_hours")
            scenes.append({
                "type": "alert",
                "text": f"{names} {'has' if len(stale) == 1 else 'have'} gone dark — last sync was {hrs / 24:.0f} days ago." if hrs and hrs > 48
                    else f"{names} {'is' if len(stale) == 1 else 'are'} behind on sync.",
                "severity": "high",
            })
            scenes.append({"type": "action", "text": "I'd recommend running a process.", "action": "process"})

        overdue = attention.get("overdue_todos") or 0
        drafts = attention.get("pending_drafts") or 0
        total_open = todos.get("total_open") or 0
        high = len(todos.get("high_priority") or [])

        if overdue > 0:
            scenes.append({"type": "alert", "text": f"{overdue} item{'s' if overdue != 1 else ''} overdue.", "severity": "high"})
        if drafts > 0:
            scenes.append({"type": "metric", "text": f"{drafts} drafts pending review.", "value": drafts, "label": "drafts"})
        if total_open > 0:
            msg = f"{total_open} todos open"
            if high > 0:
                msg += f", {high} high priority"
            scenes.append({"type": "metric", "text": msg + ".", "value": total_open, "label": "todos"})

    active = [p for p in projects if p and p.get("active") and (p.get("todo_open") or 0) > 0]
    if active:
        top = max(active, key=lambda p: p.get("todo_open") or 0)
        top_open = top.get("todo_open") or 0
        top_id = top.get("id")
        if top_open >= 5 and top_id is not None:
            prev_proj_list = (prev or {}).get("projects") or []
            prev_projects = {p.get("id"): p.get("todo_open", 0) for p in prev_proj_list if p}
            prev_top_count = prev_projects.get(top_id, 0)
            if top_open > prev_top_count or top_id not in prev_projects:
                scenes.append({
                    "type": "spotlight",
                    "text": f"{top.get('name', 'A project')} is picking up — now at {top_open} open items.",
                    "project": top_id,
                    "value": top_open,
                })

    content_scenes = [s for s in scenes if s["type"] not in ("greeting", "context")]
    if not content_scenes:
        scenes.append({"type": "quip", "text": random.choice([
            "No changes since last time. What shall we work on?",
            "Everything's steady. Ready when you are.",
            "Nothing new to report. You're up to date.",
        ])})

    _write_snapshot({
        "attention": attention,
        "health": health,
        "todos": {
            "total_open": todos.get("total_open", 0),
            "high_priority": todos.get("high_priority", []),
        },
        "projects": [
            {"id": p.get("id"), "name": p.get("name"), "todo_open": p.get("todo_open", 0)}
            for p in projects
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    script = " ".join(s["text"] for s in scenes)

    return {"script": script, "scenes": scenes}


@router.get("/api/home/briefing")
def get_briefing():
    """Generate a smart Jarvis-style briefing with structured scenes."""
    home_data = get_home()
    return _build_briefing(home_data)


@router.post("/api/home/process")
async def trigger_process():
    """Trigger KH ingest + process pipeline."""
    try:
        proc = await asyncio.to_thread(
            subprocess.run,
            ["uv", "run", "python", "-m", "knowledge_hub.cli", "process"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path.home()),
        )
        if proc.returncode != 0:
            return {
                "status": "error",
                "output": (proc.stderr or "")[-500:],
            }
        return {
            "status": "ok",
            "output": proc.stdout[-500:] if proc.stdout else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "ok",
            "message": "Process still running (timed out after 30s).",
        }
    except Exception:
        return {
            "status": "ok",
            "message": "Process triggered. Check KH logs for details.",
        }
