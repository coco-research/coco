"""Session tools: coco_session_log, coco_briefing, coco_status, coco_search, coco_context, coco_approve, coco_reject."""

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.mcp.server import mcp
from app.db.compat import upsert
from app.config import SESSIONS_DIR
from app.db.session import get_db
from app.db.tables import (
    hub_todos, hub_content, hub_drafts,
    agents, tasks, goals, todo_overrides, draft_decisions,
    entity_identifiers, project_context, handoffs, workflows,
)
from app.routers.home import get_home, _build_briefing, _health_from_sync_state
from app.services.event_bus import event_bus


@mcp.tool()
def coco_session_log() -> dict:
    """Read the most recent CoCo session log. Returns start time, launch type, commands used, and focus project."""
    try:
        if not SESSIONS_DIR.exists():
            return {"error": "No sessions directory found."}

        files = sorted(
            SESSIONS_DIR.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if not files:
            return {"error": "No session files found."}

        data = json.loads(files[0].read_text())
        return {
            "file": files[0].name,
            "started_at": data.get("started_at"),
            "launch_type": data.get("launch_type"),
            "commands_used": data.get("commands_used", []),
            "focus_project": data.get("focus_project"),
            "raw": data,
        }
    except Exception as e:
        return {"error": f"Failed to read session log: {e}"}


@mcp.tool()
def coco_briefing(since: str | None = None) -> dict:
    """Generate a smart Jarvis-style briefing with structured scenes.

    Returns new items per source, key changes since last session, and action items due.

    Args:
        since: Optional ISO datetime to compare against (default: uses snapshot-based delta).
    """
    home_data = get_home()
    return _build_briefing(home_data)


@mcp.tool()
def coco_status() -> dict:
    """Compact status overview: project counts, health indicators, attention items, and costs.

    Lighter than coco_activate -- just the key numbers.
    """
    home = get_home()

    projects = home.get("projects", [])
    active_projects = [p for p in projects if p.get("active")]

    health = home.get("health", [])
    health_ok = sum(1 for h in health if h.get("status") in ("green", "ok", None))
    health_warn = sum(1 for h in health if h.get("status") in ("yellow", "warning"))
    health_bad = sum(1 for h in health if h.get("status") in ("red", "critical"))

    return {
        "projects": {"total": len(projects), "active": len(active_projects)},
        "health": {"ok": health_ok, "warning": health_warn, "critical": health_bad},
        "attention": home.get("attention", {}),
        "todos_open": home.get("todos", {}).get("total_open", 0),
        "queue_total": home.get("queue", {}).get("total", 0),
        "costs": home.get("costs", {}),
    }


@mcp.tool()
def coco_search(query: str, project: str | None = None) -> dict:
    """Search across todos, agents, tasks, goals, and content.

    Args:
        query: Search string (matched as substring against titles).
        project: Optional project_id to filter results.
    """
    results: list[dict] = []
    pattern = f"%{query}%"
    limit = 20

    with get_db() as conn:
        # Todos from hub mirror
        try:
            rows = conn.execute(
                select(hub_todos.c.id, hub_todos.c.title, hub_todos.c.project_id, hub_todos.c.status)
                .where(hub_todos.c.title.like(pattern))
                .limit(limit)
            ).fetchall()
            for r in rows:
                if project and r.project_id != project:
                    continue
                results.append({
                    "type": "todo",
                    "id": r.id,
                    "title": r.title or "(untitled)",
                    "status": r.status,
                    "project_id": r.project_id,
                })
        except Exception:
            pass

        # Agents
        try:
            rows = conn.execute(
                select(agents.c.id, agents.c.name, agents.c.status, agents.c.role)
                .where(agents.c.name.like(pattern))
                .limit(limit)
            ).fetchall()
            for r in rows:
                results.append({
                    "type": "agent",
                    "id": r.id,
                    "title": r.name or "(unnamed)",
                    "status": r.status,
                    "role": r.role,
                })
        except Exception:
            pass

        # Tasks
        try:
            rows = conn.execute(
                select(tasks.c.id, tasks.c.title, tasks.c.status, tasks.c.priority)
                .where(tasks.c.title.like(pattern))
                .limit(limit)
            ).fetchall()
            for r in rows:
                results.append({
                    "type": "task",
                    "id": r.id,
                    "title": r.title or "(untitled)",
                    "status": r.status,
                    "priority": r.priority,
                })
        except Exception:
            pass

        # Goals
        try:
            rows = conn.execute(
                select(goals.c.id, goals.c.title, goals.c.status, goals.c.progress_pct)
                .where(goals.c.title.like(pattern))
                .limit(limit)
            ).fetchall()
            for r in rows:
                results.append({
                    "type": "goal",
                    "id": r.id,
                    "title": r.title or "(untitled)",
                    "status": r.status,
                    "progress_pct": r.progress_pct,
                })
        except Exception:
            pass

        # Content from hub mirror
        try:
            rows = conn.execute(
                select(hub_content.c.id, hub_content.c.title, hub_content.c.source)
                .where(hub_content.c.title.like(pattern))
                .limit(limit)
            ).fetchall()
            for r in rows:
                results.append({
                    "type": "content",
                    "id": r.id,
                    "title": r.title or "(untitled)",
                    "source": r.source,
                })
        except Exception:
            pass

    # Sort
    q_lower = query.lower()
    results.sort(key=lambda r: (
        0 if (r.get("title") or "").lower().startswith(q_lower) else 1,
        len(r.get("title") or ""),
    ))

    return {"query": query, "results": results[:limit], "total": len(results)}


@mcp.tool()
def coco_context(project: str) -> dict:
    """Return project collaboration context: shared docs, handoffs, and active workflow.

    Args:
        project: The node_id (project/team ID) to get context for.
    """
    result: dict = {
        "node_id": project,
        "context_sections": [],
        "handoffs": [],
        "active_workflow": None,
    }

    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    project_context.c.id, project_context.c.section,
                    project_context.c.title, project_context.c.content,
                    project_context.c.author_role, project_context.c.version,
                    project_context.c.updated_at,
                )
                .where(project_context.c.node_id == project)
                .order_by(project_context.c.created_at)
            ).fetchall()
            result["context_sections"] = [dict(r._mapping) for r in rows]

            rows = conn.execute(
                select(
                    handoffs.c.id, handoffs.c.from_role, handoffs.c.to_role,
                    handoffs.c.title, handoffs.c.status, handoffs.c.created_at,
                )
                .where(handoffs.c.node_id == project)
                .order_by(handoffs.c.created_at.desc())
                .limit(10)
            ).fetchall()
            result["handoffs"] = [dict(r._mapping) for r in rows]

            row = conn.execute(
                select(
                    workflows.c.id, workflows.c.template_name, workflows.c.objective,
                    workflows.c.steps, workflows.c.current_step, workflows.c.status,
                )
                .where(workflows.c.node_id == project)
                .where(workflows.c.status == "active")
                .order_by(workflows.c.created_at.desc())
                .limit(1)
            ).fetchone()
            if row:
                wf = dict(row._mapping)
                try:
                    wf["steps"] = json.loads(wf["steps"])
                except Exception:
                    pass
                result["active_workflow"] = wf
    except Exception:
        pass

    return result


@mcp.tool()
def coco_approve(draft_id: str) -> dict:
    """Approve a Knowledge Hub draft.

    Records approval in platform.db (never writes to hub.db directly).

    Args:
        draft_id: The UUID of the draft to approve.
    """
    try:
        with get_db() as conn:
            row = conn.execute(
                select(hub_drafts.c.id, hub_drafts.c.content)
                .where(hub_drafts.c.id == draft_id)
            ).fetchone()
            if not row:
                return {"error": f"Draft '{draft_id}' not found."}
            title = getattr(row, "title", None) or draft_id

            conn.execute(
                upsert(
                    draft_decisions,
                    values={
                        "id": str(uuid.uuid4()),
                        "hub_draft_id": draft_id,
                        "status": "approved",
                        "decided_by": "user",
                    },
                    conflict_cols=["hub_draft_id"],
                    update_cols=["status", "decided_by"],
                )
            )
    except Exception:
        return {"error": f"Failed to look up draft '{draft_id}'."}

    event_bus.emit("draft.approved", {"draft_id": draft_id, "title": title})

    return {
        "draft_id": draft_id,
        "title": title,
        "status": "approved",
        "message": f"Draft '{title}' approved.",
    }


@mcp.tool()
def coco_reject(draft_id: str, reason: str | None = None) -> dict:
    """Reject a Knowledge Hub draft.

    Records rejection in platform.db (never writes to hub.db directly).

    Args:
        draft_id: The UUID of the draft to reject.
        reason: Optional reason for rejection.
    """
    try:
        with get_db() as conn:
            row = conn.execute(
                select(hub_drafts.c.id, hub_drafts.c.content)
                .where(hub_drafts.c.id == draft_id)
            ).fetchone()
            if not row:
                return {"error": f"Draft '{draft_id}' not found."}
            title = getattr(row, "title", None) or draft_id

            conn.execute(
                upsert(
                    draft_decisions,
                    values={
                        "id": str(uuid.uuid4()),
                        "hub_draft_id": draft_id,
                        "status": "rejected",
                        "decided_by": "user",
                    },
                    conflict_cols=["hub_draft_id"],
                    update_cols=["status", "decided_by"],
                )
            )
    except Exception:
        return {"error": f"Failed to look up draft '{draft_id}'."}

    event_bus.emit("draft.rejected", {"draft_id": draft_id, "title": title, "reason": reason})

    return {
        "draft_id": draft_id,
        "title": title,
        "status": "rejected",
        "reason": reason,
        "message": f"Draft '{title}' rejected." + (f" Reason: {reason}" if reason else ""),
    }
