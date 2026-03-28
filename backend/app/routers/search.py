"""Unified search across all entities for the Cmd+K command palette."""

import logging
from fastapi import APIRouter, Query
from app.db.connections import get_hub_db, get_platform_db

log = logging.getLogger(__name__)

router = APIRouter(tags=["Search"])


@router.get("/api/search")
def unified_search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=50),
):
    """Search across todos, agents, tasks, goals, and content.

    Returns a unified list of results sorted by relevance (exact prefix
    matches first, then substring matches).
    """
    results: list[dict] = []
    pattern = f"%{q}%"

    # --- Todos from hub.db ---
    try:
        with get_hub_db() as db:
            rows = db.execute(
                "SELECT id, title, project_id, status FROM todos "
                "WHERE title LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            # Bulk-fetch display_ids for matched todo IDs from platform.db
            todo_display_ids: dict[str, str] = {}
            if rows:
                try:
                    with get_platform_db() as pdb:
                        placeholders = ",".join("?" for _ in rows)
                        id_rows = pdb.execute(
                            f"SELECT entity_id, display_id FROM entity_identifiers "
                            f"WHERE entity_type = 'todo' AND entity_id IN ({placeholders})",
                            [r["id"] for r in rows],
                        ).fetchall()
                        todo_display_ids = {r["entity_id"]: r["display_id"] for r in id_rows}
                except Exception as e:
                    log.warning("search_hub_todo_display_ids_failed: %s", e)
            for r in rows:
                results.append({
                    "type": "todo",
                    "id": r["id"],
                    "display_id": todo_display_ids.get(r["id"]),
                    "title": r["title"] or "(untitled)",
                    "subtitle": f"Status: {r['status'] or 'open'}",
                    "url": f"/todos",
                })
    except Exception as e:
        log.warning("search_hub_todos_failed: %s", e)

    # --- Todos from platform.db (platform-native) ---
    try:
        with get_platform_db() as pdb:
            rows = pdb.execute(
                "SELECT t.hub_todo_id, t.title, t.status, ei.display_id "
                "FROM todo_overrides t "
                "LEFT JOIN entity_identifiers ei ON ei.entity_id = t.hub_todo_id AND ei.entity_type = 'todo' "
                "WHERE t.is_platform_native = 1 AND t.title LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            # Avoid duplicates (hub.db todos already included above)
            existing_ids = {r["id"] for r in results if r["type"] == "todo"}
            for r in rows:
                if r["hub_todo_id"] not in existing_ids:
                    results.append({
                        "type": "todo",
                        "id": r["hub_todo_id"],
                        "display_id": r["display_id"],
                        "title": r["title"] or "(untitled)",
                        "subtitle": f"Status: {r['status'] or 'open'}",
                        "url": f"/todos",
                    })
    except Exception as e:
        log.warning("search_platform_todos_failed: %s", e)

    # --- Agents from platform.db ---
    try:
        with get_platform_db() as pdb:
            rows = pdb.execute(
                "SELECT a.id, a.name, a.status, a.role, ei.display_id "
                "FROM agents a "
                "LEFT JOIN entity_identifiers ei ON ei.entity_id = a.id AND ei.entity_type = 'agent' "
                "WHERE a.name LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            for r in rows:
                subtitle_parts = []
                if r["role"]:
                    subtitle_parts.append(r["role"])
                if r["status"]:
                    subtitle_parts.append(r["status"])
                results.append({
                    "type": "agent",
                    "id": r["id"],
                    "display_id": r["display_id"],
                    "title": r["name"] or "(unnamed)",
                    "subtitle": " - ".join(subtitle_parts) or "Agent",
                    "url": f"/agents/{r['id']}",
                })
    except Exception as e:
        log.warning("search_agents_failed: %s", e)

    # --- Tasks from platform.db ---
    try:
        with get_platform_db() as pdb:
            rows = pdb.execute(
                "SELECT t.id, t.title, t.status, t.priority, ei.display_id "
                "FROM tasks t "
                "LEFT JOIN entity_identifiers ei ON ei.entity_id = t.id AND ei.entity_type = 'task' "
                "WHERE t.title LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            for r in rows:
                subtitle_parts = []
                if r["status"]:
                    subtitle_parts.append(r["status"])
                if r["priority"]:
                    subtitle_parts.append(r["priority"])
                results.append({
                    "type": "task",
                    "id": r["id"],
                    "display_id": r["display_id"],
                    "title": r["title"] or "(untitled)",
                    "subtitle": " - ".join(subtitle_parts) or "Task",
                    "url": f"/tasks",
                })
    except Exception as e:
        log.warning("search_tasks_failed: %s", e)

    # --- Goals from platform.db ---
    try:
        with get_platform_db() as pdb:
            rows = pdb.execute(
                "SELECT g.id, g.title, g.status, g.progress_pct, ei.display_id "
                "FROM goals g "
                "LEFT JOIN entity_identifiers ei ON ei.entity_id = g.id AND ei.entity_type = 'goal' "
                "WHERE g.title LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            for r in rows:
                pct = r["progress_pct"]
                subtitle = f"{r['status'] or 'active'}"
                if pct is not None:
                    subtitle += f" - {pct}%"
                results.append({
                    "type": "goal",
                    "id": r["id"],
                    "display_id": r["display_id"],
                    "title": r["title"] or "(untitled)",
                    "subtitle": subtitle,
                    "url": f"/goals",
                })
    except Exception as e:
        log.warning("search_goals_failed: %s", e)

    # --- Content from hub.db ---
    try:
        with get_hub_db() as db:
            rows = db.execute(
                "SELECT id, title, source, content_type FROM content "
                "WHERE title LIKE ? LIMIT ?",
                (pattern, limit),
            ).fetchall()
            for r in rows:
                subtitle_parts = []
                if r["source"]:
                    subtitle_parts.append(r["source"])
                if r["content_type"]:
                    subtitle_parts.append(r["content_type"])
                results.append({
                    "type": "content",
                    "id": r["id"],
                    "title": r["title"] or "(untitled)",
                    "subtitle": " - ".join(subtitle_parts) or "Content",
                    "url": f"/knowledge/{r['id']}",
                })
    except Exception as e:
        log.warning("search_content_failed: %s", e)

    # Sort: exact prefix matches first, then by title length (shorter = more relevant)
    q_lower = q.lower()

    def sort_key(item: dict) -> tuple[int, int]:
        title_lower = (item.get("title") or "").lower()
        is_prefix = 0 if title_lower.startswith(q_lower) else 1
        return (is_prefix, len(title_lower))

    results.sort(key=sort_key)

    return results[:limit]
