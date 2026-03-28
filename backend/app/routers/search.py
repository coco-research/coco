"""Unified search across all entities for the Cmd+K command palette."""

import logging
from fastapi import APIRouter, Query
from sqlalchemy import select, outerjoin
from app.db.session import get_db
from app.db.tables import (
    hub_todos, hub_content,
    todo_overrides, entity_identifiers, agents, tasks, goals,
)

log = logging.getLogger(__name__)

router = APIRouter(tags=["Search"])


@router.get("/api/search")
def unified_search(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(10, ge=1, le=50),
):
    """Search across todos, agents, tasks, goals, and content."""
    results: list[dict] = []
    pattern = f"%{q}%"

    with get_db() as conn:
        # --- Todos from hub mirror ---
        try:
            rows = conn.execute(
                select(hub_todos.c.id, hub_todos.c.title, hub_todos.c.project_id, hub_todos.c.status)
                .where(hub_todos.c.title.like(pattern))
                .limit(limit)
            ).fetchall()
            # Bulk-fetch display_ids
            todo_display_ids: dict[str, str] = {}
            if rows:
                try:
                    id_rows = conn.execute(
                        select(entity_identifiers.c.entity_id, entity_identifiers.c.display_id)
                        .where(entity_identifiers.c.entity_type == "todo")
                        .where(entity_identifiers.c.entity_id.in_([r.id for r in rows]))
                    ).fetchall()
                    todo_display_ids = {r.entity_id: r.display_id for r in id_rows}
                except Exception as e:
                    log.warning("search_hub_todo_display_ids_failed: %s", e)
            for r in rows:
                results.append({
                    "type": "todo",
                    "id": r.id,
                    "display_id": todo_display_ids.get(r.id),
                    "title": r.title or "(untitled)",
                    "subtitle": f"Status: {r.status or 'open'}",
                    "url": f"/todos",
                })
        except Exception as e:
            log.warning("search_hub_todos_failed: %s", e)

        # --- Todos from platform (platform-native) ---
        try:
            j = outerjoin(
                todo_overrides, entity_identifiers,
                (entity_identifiers.c.entity_id == todo_overrides.c.hub_todo_id)
                & (entity_identifiers.c.entity_type == "todo"),
            )
            rows = conn.execute(
                select(
                    todo_overrides.c.hub_todo_id,
                    todo_overrides.c.title,
                    todo_overrides.c.status,
                    entity_identifiers.c.display_id,
                )
                .select_from(j)
                .where(todo_overrides.c.is_platform_native == 1)
                .where(todo_overrides.c.title.like(pattern))
                .limit(limit)
            ).fetchall()
            existing_ids = {r["id"] for r in results if r["type"] == "todo"}
            for r in rows:
                if r.hub_todo_id not in existing_ids:
                    results.append({
                        "type": "todo",
                        "id": r.hub_todo_id,
                        "display_id": r.display_id,
                        "title": r.title or "(untitled)",
                        "subtitle": f"Status: {r.status or 'open'}",
                        "url": f"/todos",
                    })
        except Exception as e:
            log.warning("search_platform_todos_failed: %s", e)

        # --- Agents ---
        try:
            j_agents = outerjoin(
                agents, entity_identifiers,
                (entity_identifiers.c.entity_id == agents.c.id)
                & (entity_identifiers.c.entity_type == "agent"),
            )
            rows = conn.execute(
                select(
                    agents.c.id, agents.c.name, agents.c.status, agents.c.role,
                    entity_identifiers.c.display_id,
                )
                .select_from(j_agents)
                .where(agents.c.name.like(pattern))
                .limit(limit)
            ).fetchall()
            for r in rows:
                subtitle_parts = []
                if r.role:
                    subtitle_parts.append(r.role)
                if r.status:
                    subtitle_parts.append(r.status)
                results.append({
                    "type": "agent",
                    "id": r.id,
                    "display_id": r.display_id,
                    "title": r.name or "(unnamed)",
                    "subtitle": " - ".join(subtitle_parts) or "Agent",
                    "url": f"/agents/{r.id}",
                })
        except Exception as e:
            log.warning("search_agents_failed: %s", e)

        # --- Tasks ---
        try:
            j_tasks = outerjoin(
                tasks, entity_identifiers,
                (entity_identifiers.c.entity_id == tasks.c.id)
                & (entity_identifiers.c.entity_type == "task"),
            )
            rows = conn.execute(
                select(
                    tasks.c.id, tasks.c.title, tasks.c.status, tasks.c.priority,
                    entity_identifiers.c.display_id,
                )
                .select_from(j_tasks)
                .where(tasks.c.title.like(pattern))
                .limit(limit)
            ).fetchall()
            for r in rows:
                subtitle_parts = []
                if r.status:
                    subtitle_parts.append(r.status)
                if r.priority:
                    subtitle_parts.append(r.priority)
                results.append({
                    "type": "task",
                    "id": r.id,
                    "display_id": r.display_id,
                    "title": r.title or "(untitled)",
                    "subtitle": " - ".join(subtitle_parts) or "Task",
                    "url": f"/tasks",
                })
        except Exception as e:
            log.warning("search_tasks_failed: %s", e)

        # --- Goals ---
        try:
            j_goals = outerjoin(
                goals, entity_identifiers,
                (entity_identifiers.c.entity_id == goals.c.id)
                & (entity_identifiers.c.entity_type == "goal"),
            )
            rows = conn.execute(
                select(
                    goals.c.id, goals.c.title, goals.c.status, goals.c.progress_pct,
                    entity_identifiers.c.display_id,
                )
                .select_from(j_goals)
                .where(goals.c.title.like(pattern))
                .limit(limit)
            ).fetchall()
            for r in rows:
                pct = r.progress_pct
                subtitle = f"{r.status or 'active'}"
                if pct is not None:
                    subtitle += f" - {pct}%"
                results.append({
                    "type": "goal",
                    "id": r.id,
                    "display_id": r.display_id,
                    "title": r.title or "(untitled)",
                    "subtitle": subtitle,
                    "url": f"/goals",
                })
        except Exception as e:
            log.warning("search_goals_failed: %s", e)

        # --- Content from hub mirror ---
        try:
            rows = conn.execute(
                select(hub_content.c.id, hub_content.c.title, hub_content.c.source)
                .where(hub_content.c.title.like(pattern))
                .limit(limit)
            ).fetchall()
            for r in rows:
                subtitle_parts = []
                if r.source:
                    subtitle_parts.append(r.source)
                results.append({
                    "type": "content",
                    "id": r.id,
                    "title": r.title or "(untitled)",
                    "subtitle": " - ".join(subtitle_parts) or "Content",
                    "url": f"/knowledge/{r.id}",
                })
        except Exception as e:
            log.warning("search_content_failed: %s", e)

    # Sort: exact prefix matches first, then by title length
    q_lower = q.lower()

    def sort_key(item: dict) -> tuple[int, int]:
        title_lower = (item.get("title") or "").lower()
        is_prefix = 0 if title_lower.startswith(q_lower) else 1
        return (is_prefix, len(title_lower))

    results.sort(key=sort_key)

    return results[:limit]
