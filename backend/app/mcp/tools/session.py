"""Session tools: coco_session_log, coco_briefing, coco_status, coco_search, coco_context, coco_approve, coco_reject."""

import json
import uuid
from datetime import datetime, timezone

from app.mcp.server import mcp
from app.config import SESSIONS_DIR
from app.db.connections import get_hub_db, get_platform_db
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

    # Count projects
    projects = home.get("projects", [])
    active_projects = [p for p in projects if p.get("active")]

    # Health summary
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

    # Todos from hub.db
    try:
        with get_hub_db() as db:
            rows = db.execute(
                "SELECT id, title, project_id, status FROM todos WHERE title LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            for r in rows:
                if project and r["project_id"] != project:
                    continue
                results.append({
                    "type": "todo",
                    "id": r["id"],
                    "title": r["title"] or "(untitled)",
                    "status": r["status"],
                    "project_id": r["project_id"],
                })
    except Exception:
        pass

    # Agents from platform.db
    try:
        with get_platform_db() as pdb:
            rows = pdb.execute(
                "SELECT id, name, status, role FROM agents WHERE name LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "type": "agent",
                    "id": r["id"],
                    "title": r["name"] or "(unnamed)",
                    "status": r["status"],
                    "role": r["role"],
                })
    except Exception:
        pass

    # Tasks from platform.db
    try:
        with get_platform_db() as pdb:
            rows = pdb.execute(
                "SELECT id, title, status, priority FROM tasks WHERE title LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "type": "task",
                    "id": r["id"],
                    "title": r["title"] or "(untitled)",
                    "status": r["status"],
                    "priority": r["priority"],
                })
    except Exception:
        pass

    # Goals from platform.db
    try:
        with get_platform_db() as pdb:
            rows = pdb.execute(
                "SELECT id, title, status, progress_pct FROM goals WHERE title LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "type": "goal",
                    "id": r["id"],
                    "title": r["title"] or "(untitled)",
                    "status": r["status"],
                    "progress_pct": r["progress_pct"],
                })
    except Exception:
        pass

    # Content from hub.db
    try:
        with get_hub_db() as db:
            rows = db.execute(
                "SELECT id, title, source, content_type FROM content WHERE title LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            for r in rows:
                results.append({
                    "type": "content",
                    "id": r["id"],
                    "title": r["title"] or "(untitled)",
                    "source": r["source"],
                    "content_type": r["content_type"],
                })
    except Exception:
        pass

    # Sort: prefix matches first, then shorter titles
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
        with get_platform_db() as db:
            # Context sections
            rows = db.execute(
                "SELECT id, section, title, content, author_role, version, updated_at "
                "FROM project_context WHERE node_id = ? ORDER BY created_at",
                (project,),
            ).fetchall()
            result["context_sections"] = [dict(r) for r in rows]

            # Recent handoffs
            rows = db.execute(
                "SELECT id, from_role, to_role, title, status, created_at "
                "FROM handoffs WHERE node_id = ? ORDER BY created_at DESC LIMIT 10",
                (project,),
            ).fetchall()
            result["handoffs"] = [dict(r) for r in rows]

            # Active workflow
            row = db.execute(
                "SELECT id, template_name, objective, steps, current_step, status "
                "FROM workflows WHERE node_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
                (project,),
            ).fetchone()
            if row:
                wf = dict(row)
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
    # Verify draft exists
    try:
        with get_hub_db() as db:
            row = db.execute("SELECT id, title FROM drafts WHERE id = ?", (draft_id,)).fetchone()
            if not row:
                return {"error": f"Draft '{draft_id}' not found."}
            title = row["title"]
    except Exception:
        return {"error": f"Failed to look up draft '{draft_id}'."}

    # Write decision
    with get_platform_db() as pdb:
        pdb.execute(
            "INSERT OR REPLACE INTO draft_decisions (id, hub_draft_id, status, decided_by) VALUES (?, ?, 'approved', 'user')",
            (str(uuid.uuid4()), draft_id),
        )
        pdb.commit()

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
    # Verify draft exists
    try:
        with get_hub_db() as db:
            row = db.execute("SELECT id, title FROM drafts WHERE id = ?", (draft_id,)).fetchone()
            if not row:
                return {"error": f"Draft '{draft_id}' not found."}
            title = row["title"]
    except Exception:
        return {"error": f"Failed to look up draft '{draft_id}'."}

    # Write decision
    with get_platform_db() as pdb:
        pdb.execute(
            "INSERT OR REPLACE INTO draft_decisions (id, hub_draft_id, status, decided_by) VALUES (?, ?, 'rejected', 'user')",
            (str(uuid.uuid4()), draft_id),
        )
        pdb.commit()

    event_bus.emit("draft.rejected", {"draft_id": draft_id, "title": title, "reason": reason})

    return {
        "draft_id": draft_id,
        "title": title,
        "status": "rejected",
        "reason": reason,
        "message": f"Draft '{title}' rejected." + (f" Reason: {reason}" if reason else ""),
    }
