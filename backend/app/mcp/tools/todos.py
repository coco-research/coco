"""coco_todo_list, coco_todo_add, coco_todo_done -- Todo management."""

import uuid

from sqlalchemy import select, insert, update, text
from app.mcp.server import mcp
from app.db.session import get_db
from app.db.tables import hub_todos, todo_overrides


_HUB_TODO_COLS = [
    hub_todos.c.id, hub_todos.c.title, hub_todos.c.project_id,
    hub_todos.c.priority, hub_todos.c.owner, hub_todos.c.due_date,
    hub_todos.c.status, hub_todos.c.source_type,
    hub_todos.c.source_content_id, hub_todos.c.created_at,
]


@mcp.tool()
def coco_todo_list(status: str = "open", project: str | None = None) -> dict:
    """List todos with count and items, filtered by status and optional project.

    Args:
        status: Filter by status ('open', 'backlog', 'todo', 'in_progress', 'done', 'archived'). Default: 'open'.
        project: Optional project_id to filter by.
    """
    hub_items: list[dict] = []
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(*_HUB_TODO_COLS).order_by(hub_todos.c.created_at.desc())
            ).fetchall()
            hub_items = [dict(r._mapping) for r in rows]
    except Exception:
        pass

    # Read overrides + platform-native
    overrides: dict[str, dict] = {}
    platform_native: list[dict] = []
    try:
        with get_db() as conn:
            override_rows = conn.execute(select(todo_overrides)).fetchall()
            for r in override_rows:
                row = dict(r._mapping)
                if row.get("is_platform_native"):
                    platform_native.append({
                        "id": row["hub_todo_id"],
                        "title": row.get("title"),
                        "status": row.get("status") or "open",
                        "priority": row.get("priority") or "medium",
                        "owner": row.get("owner"),
                        "due_date": row.get("due_date"),
                        "project_id": row.get("project_id"),
                        "source_type": row.get("source_type"),
                        "created_at": row.get("created_at"),
                        "is_platform_native": True,
                    })
                else:
                    overrides[row["hub_todo_id"]] = row
    except Exception:
        pass

    # Merge hub todos with overrides
    merged = []
    for t in hub_items:
        override = overrides.get(t["id"])
        if override:
            for field in ("title", "status", "priority", "owner", "due_date", "project_id"):
                val = override.get(field)
                if val is not None:
                    t[field] = val
        merged.append(t)
    merged.extend(platform_native)

    # Filter
    if status:
        merged = [t for t in merged if t.get("status") == status]
    if project:
        merged = [t for t in merged if t.get("project_id") == project]

    merged.sort(key=lambda t: t.get("created_at") or "", reverse=True)

    return {
        "count": len(merged),
        "items": merged[:50],
    }


@mcp.tool()
def coco_todo_add(
    title: str,
    project: str | None = None,
    priority: str = "medium",
    owner: str | None = None,
) -> dict:
    """Create a new todo item.

    Args:
        title: The todo title/description.
        project: Optional project_id to assign it to.
        priority: Priority level ('low', 'medium', 'high'). Default: 'medium'.
        owner: Optional person to assign this todo to.
    """
    todo_id = str(uuid.uuid4())

    with get_db() as conn:
        conn.execute(
            text(
                "INSERT INTO todo_overrides "
                "(hub_todo_id, title, project_id, priority, owner, due_date, node_id, status, "
                "source_type, source_content_id, is_platform_native, created_at, updated_at) "
                "VALUES (:id, :title, :project, :priority, :owner, NULL, NULL, 'open', "
                "NULL, NULL, 1, datetime('now'), datetime('now'))"
            ),
            {"id": todo_id, "title": title, "project": project, "priority": priority, "owner": owner},
        )

    return {
        "id": todo_id,
        "title": title,
        "status": "open",
        "priority": priority,
        "owner": owner,
        "project_id": project,
        "message": f"Todo created: {title}",
    }


@mcp.tool()
def coco_todo_done(todo_id: str) -> dict:
    """Mark a todo as done.

    Args:
        todo_id: The UUID of the todo to complete.
    """
    found = False

    with get_db() as conn:
        # Check hub mirror
        try:
            row = conn.execute(
                select(hub_todos.c.id).where(hub_todos.c.id == todo_id)
            ).fetchone()
            if row:
                found = True
        except Exception:
            pass

        # Check platform
        if not found:
            row = conn.execute(
                select(todo_overrides.c.hub_todo_id)
                .where(todo_overrides.c.hub_todo_id == todo_id)
            ).fetchone()
            if row:
                found = True

    if not found:
        return {"error": f"Todo '{todo_id}' not found."}

    # Upsert override to set status = done
    with get_db() as conn:
        existing = conn.execute(
            select(todo_overrides.c.hub_todo_id)
            .where(todo_overrides.c.hub_todo_id == todo_id)
        ).fetchone()

        if existing:
            conn.execute(
                text(
                    "UPDATE todo_overrides SET status = 'done', updated_at = datetime('now') "
                    "WHERE hub_todo_id = :id"
                ),
                {"id": todo_id},
            )
        else:
            conn.execute(
                text(
                    "INSERT INTO todo_overrides "
                    "(hub_todo_id, status, is_platform_native, created_at, updated_at) "
                    "VALUES (:id, 'done', 0, datetime('now'), datetime('now'))"
                ),
                {"id": todo_id},
            )

    return {
        "id": todo_id,
        "status": "done",
        "message": f"Todo {todo_id} marked as done.",
    }
