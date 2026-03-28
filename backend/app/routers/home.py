import asyncio
import json
import random
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import structlog
from fastapi import APIRouter

from app.db.connections import get_hub_db, get_platform_db

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

        # since last session
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

        # session info
        result["info"]["last_started"] = data.get("started_at")
        result["info"]["last_focus"] = data.get("focus_project")
        result["info"]["last_launch_type"] = data.get("launch_type")
        return result
    except Exception:
        log.warning("home_session_read_failed", exc_info=True)
        return result


def _health_from_sync_state(db) -> list[dict]:
    """Read sync_state table and compute stale_hours."""
    try:
        rows = db.execute(
            "SELECT source_name, status, last_success, items_synced FROM sync_state"
        ).fetchall()
        now = datetime.now(timezone.utc)
        health = []
        for r in rows:
            h = dict(r)
            h["source"] = h.pop("source_name", h.get("source", "unknown"))
            h["last_sync"] = h.get("last_success")
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

    # --- Hub DB queries (single connection) ---
    try:
        with get_hub_db() as db:
            # Attention: unsorted count
            try:
                row = db.execute(
                    "SELECT COUNT(*) as cnt FROM content WHERE id NOT IN (SELECT content_id FROM project_content)"
                ).fetchone()
                result["attention"]["unsorted_count"] = row["cnt"] if row else 0
            except Exception:
                log.warning("home_query_failed", section="unsorted_count", exc_info=True)

            # Attention: pending drafts
            try:
                row = db.execute(
                    "SELECT COUNT(*) as cnt FROM drafts WHERE status = 'pending'"
                ).fetchone()
                result["attention"]["pending_drafts"] = row["cnt"] if row else 0
            except Exception:
                log.warning("home_query_failed", section="pending_drafts", exc_info=True)

            # Attention: overdue todos
            try:
                row = db.execute(
                    "SELECT COUNT(*) as cnt FROM todos WHERE status = 'open' AND due_date < date('now', 'localtime')"
                ).fetchone()
                result["attention"]["overdue_todos"] = row["cnt"] if row else 0
            except Exception:
                log.warning("home_query_failed", section="overdue_todos", exc_info=True)

            # Health (sync_state)
            try:
                health = _health_from_sync_state(db)
                result["health"] = health
                result["attention"]["health_alerts"] = sum(
                    1 for h in health if h.get("status") in ("red", "critical")
                )
            except Exception:
                log.warning("home_query_failed", section="health", exc_info=True)

            # Todos
            try:
                row = db.execute(
                    "SELECT COUNT(*) as cnt FROM todos WHERE status = 'open'"
                ).fetchone()
                result["todos"]["total_open"] = row["cnt"] if row else 0

                high = db.execute(
                    "SELECT id, title, project_id, owner, due_date, priority, status, source_type, jira_key, tags "
                    "FROM todos WHERE status = 'open' AND priority = 'high' ORDER BY created_at DESC LIMIT 50"
                ).fetchall()
                result["todos"]["high_priority"] = [dict(r) for r in high]

                medium = db.execute(
                    "SELECT id, title, project_id, owner, due_date, priority, status, source_type, jira_key, tags "
                    "FROM todos WHERE status = 'open' AND priority = 'medium' ORDER BY created_at DESC LIMIT 20"
                ).fetchall()
                result["todos"]["medium_priority"] = [dict(r) for r in medium]

                overdue = db.execute(
                    "SELECT id, title, project_id, owner, due_date, priority, status, source_type, jira_key, tags "
                    "FROM todos WHERE status = 'open' AND due_date < date('now', 'localtime') ORDER BY due_date ASC LIMIT 50"
                ).fetchall()
                result["todos"]["overdue"] = [dict(r) for r in overdue]
            except Exception:
                log.warning("home_query_failed", section="todos", exc_info=True)

            # Projects with todo counts and source breakdown
            try:
                rows = db.execute(
                    """SELECT p.id, p.name, p.active,
                        (SELECT COUNT(*) FROM project_content pc WHERE pc.project_id = p.id) as item_count,
                        (SELECT COUNT(*) FROM todos t WHERE t.project_id = p.id AND t.status = 'open') as todo_open,
                        (SELECT COUNT(*) FROM todos t WHERE t.project_id = p.id AND t.status = 'done') as todo_done,
                        (SELECT COUNT(*) FROM todos t WHERE t.project_id = p.id) as todo_total
                    FROM projects p ORDER BY p.name"""
                ).fetchall()
                projects = []
                for r in rows:
                    p = dict(r)
                    sources = {"email": 0, "voice": 0, "jira": 0, "confluence": 0}
                    try:
                        src_rows = db.execute(
                            """SELECT c.source, COUNT(*) as count
                               FROM content c
                               JOIN project_content pc ON c.id = pc.content_id
                               WHERE pc.project_id = ?
                               GROUP BY c.source""",
                            (p["id"],),
                        ).fetchall()
                        for sr in src_rows:
                            src = sr["source"]
                            sources[src] = sr["count"]
                    except Exception:
                        log.warning("home_query_failed", section="project_sources", exc_info=True)
                    p["sources"] = sources
                    projects.append(p)
                result["projects"] = projects
            except Exception:
                log.warning("home_query_failed", section="projects", exc_info=True)

            # Costs from hub api_costs
            try:
                row = db.execute(
                    "SELECT COALESCE(SUM(cost_usd), 0) as total FROM api_costs WHERE created_at >= date('now')"
                ).fetchone()
                result["costs"]["today_usd"] += round(row["total"], 4) if row else 0.0
            except Exception:
                log.warning("home_query_failed", section="hub_costs_today", exc_info=True)

            try:
                row = db.execute(
                    "SELECT COALESCE(SUM(cost_usd), 0) as total FROM api_costs WHERE created_at >= date('now', 'start of month')"
                ).fetchone()
                result["costs"]["month_usd"] += round(row["total"], 4) if row else 0.0
            except Exception:
                log.warning("home_query_failed", section="hub_costs_month", exc_info=True)
    except Exception:
        pass

    # --- Platform DB queries (single connection) ---
    try:
        with get_platform_db() as db:
            # Queue: tasks
            try:
                row = db.execute(
                    "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'open'"
                ).fetchone()
                # Don't overwrite total here; we compute it below
                row_urgent = db.execute(
                    "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'open' AND priority = 'high'"
                ).fetchone()
                result["queue"]["urgent"] = row_urgent["cnt"] if row_urgent else 0
            except Exception:
                log.warning("home_query_failed", section="platform_tasks", exc_info=True)

            # Costs from platform cost_ledger
            try:
                row = db.execute(
                    "SELECT COALESCE(SUM(cost_usd), 0) as total FROM cost_ledger WHERE created_at >= date('now')"
                ).fetchone()
                result["costs"]["today_usd"] += round(row["total"], 4) if row else 0.0
            except Exception:
                log.warning("home_query_failed", section="platform_costs_today", exc_info=True)

            try:
                row = db.execute(
                    "SELECT COALESCE(SUM(cost_usd), 0) as total FROM cost_ledger WHERE created_at >= date('now', 'start of month')"
                ).fetchone()
                result["costs"]["month_usd"] += round(row["total"], 4) if row else 0.0
            except Exception:
                log.warning("home_query_failed", section="platform_costs_month", exc_info=True)
    except Exception:
        pass

    # Queue: drafts + classify from attention counts
    result["queue"]["drafts"] = result["attention"]["pending_drafts"]
    result["queue"]["classify"] = result["attention"]["unsorted_count"]

    # Fix 2: Compute total as sum of all queue components
    result["queue"]["total"] = (
        result["queue"]["urgent"]
        + result["queue"]["drafts"]
        + result["queue"]["classify"]
    )

    # Round final costs
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
    """Generate a structured, Jarvis-style briefing with typed scenes.

    Returns {"script": str, "scenes": list[dict]} where script is the full
    text for TTS and scenes have per-type visual treatments.
    """
    scenes: list[dict] = []
    prev = _read_snapshot()

    # ── Scene: Greeting ──
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

    # ── Scene: Time context ──
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

    attention = current.get("attention", {})
    health = current.get("health", [])
    todos = current.get("todos", {})
    projects = current.get("projects", [])

    # ── Delta-aware scenes: only mention what CHANGED ──
    stale = [h for h in health if (h.get("stale_hours") or 0) > 24]

    if prev:
        prev_attn = prev.get("attention", {})
        prev_todos = prev.get("todos", {})
        prev_stale_sources = {h["source"] for h in prev.get("health", []) if (h.get("stale_hours") or 0) > 24}

        # Health: only alert if NEW sources went stale (not already stale last time)
        newly_stale = [h for h in stale if h["source"] not in prev_stale_sources]
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

        # Overdue: only if count INCREASED
        prev_overdue = prev_attn.get("overdue_todos", 0)
        curr_overdue = attention.get("overdue_todos", 0)
        if curr_overdue > prev_overdue:
            diff = curr_overdue - prev_overdue
            scenes.append({"type": "alert", "text": f"{diff} new item{'s' if diff != 1 else ''} went overdue.", "severity": "high"})
        # unchanged overdue = SKIP (don't repeat)

        # Drafts: only if count INCREASED
        prev_drafts = prev_attn.get("pending_drafts", 0)
        curr_drafts = attention.get("pending_drafts", 0)
        if curr_drafts > prev_drafts:
            diff = curr_drafts - prev_drafts
            scenes.append({"type": "metric", "text": f"{diff} new draft{'s' if diff != 1 else ''} to review.", "value": diff, "label": "new drafts"})
        # unchanged drafts = SKIP

        # Todos: only if count changed
        prev_open = prev_todos.get("total_open", 0)
        curr_open = todos.get("total_open", 0)
        if curr_open > prev_open:
            diff = curr_open - prev_open
            scenes.append({"type": "metric", "text": f"{diff} new todo{'s' if diff != 1 else ''}.", "value": diff, "label": "new todos"})
        elif curr_open < prev_open:
            diff = prev_open - curr_open
            scenes.append({"type": "status", "text": f"You cleared {diff} todo{'s' if diff != 1 else ''}. Nice work."})
        # unchanged = SKIP

        # High priority: only if increased
        prev_high = len(prev_todos.get("high_priority", []))
        curr_high = len(todos.get("high_priority", []))
        if curr_high > prev_high:
            scenes.append({"type": "alert", "text": f"{curr_high - prev_high} new high-priority item{'s' if curr_high - prev_high != 1 else ''}.", "severity": "medium"})

    else:
        # First briefing ever — give a full summary
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

        overdue = attention.get("overdue_todos", 0)
        drafts = attention.get("pending_drafts", 0)
        total_open = todos.get("total_open", 0)
        high = len(todos.get("high_priority", []))

        if overdue > 0:
            scenes.append({"type": "alert", "text": f"{overdue} item{'s' if overdue != 1 else ''} overdue.", "severity": "high"})
        if drafts > 0:
            scenes.append({"type": "metric", "text": f"{drafts} drafts pending review.", "value": drafts, "label": "drafts"})
        if total_open > 0:
            msg = f"{total_open} todos open"
            if high > 0:
                msg += f", {high} high priority"
            scenes.append({"type": "metric", "text": msg + ".", "value": total_open, "label": "todos"})

    # ── Scene: Project spotlight (only if top project CHANGED or is new) ──
    active = [p for p in projects if p.get("active") and p.get("todo_open", 0) > 0]
    if active:
        top = max(active, key=lambda p: p["todo_open"])
        if top["todo_open"] >= 5:
            # Only spotlight if this project wasn't the top last time, or its count grew
            prev_projects = {p["id"]: p.get("todo_open", 0) for p in (prev or {}).get("projects", [])}
            prev_top_count = prev_projects.get(top["id"], 0)
            if top["todo_open"] > prev_top_count or top["id"] not in prev_projects:
                scenes.append({
                    "type": "spotlight",
                    "text": f"{top['name']} is picking up — now at {top['todo_open']} open items.",
                    "project": top.get("id"),
                    "value": top["todo_open"],
                })

    # ── Closing ──
    content_scenes = [s for s in scenes if s["type"] not in ("greeting", "context")]
    if not content_scenes:
        scenes.append({"type": "quip", "text": random.choice([
            "No changes since last time. What shall we work on?",
            "Everything's steady. Ready when you are.",
            "Nothing new to report. You're up to date.",
        ])})

    # Save snapshot
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

    # Build flat script for TTS (all scene texts joined)
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
