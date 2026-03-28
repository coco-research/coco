import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from app.db.connections import get_platform_db
from app.db.tree_utils import build_node_id_filter
from app.services.event_bus import event_bus
from app.models.tasks import CheckoutTaskBody, CreateTaskBody, PatchTaskBody
from app.models.common import TransitionBody

router = APIRouter(tags=["Tasks"])

# ---- State machine ----

TASK_STATES = {"backlog", "todo", "in_progress", "in_review", "done", "archived"}

TASK_TRANSITIONS: dict[str, list[str]] = {
    "backlog": ["todo", "archived"],
    "todo": ["in_progress", "backlog", "archived"],
    "in_progress": ["in_review", "done", "todo"],
    "in_review": ["done", "in_progress"],
    "done": ["archived", "in_progress"],
    "archived": ["backlog"],
    # Legacy states map forward
    "open": ["backlog", "todo", "in_progress", "done", "archived"],
    "checked_out": ["in_progress", "backlog"],
    "review": ["done", "in_progress"],
    "cancelled": ["backlog", "archived"],
}


@router.get("/api/tasks")
def list_tasks(
    agent_id: str | None = None,
    status: str | None = None,
    project_id: str | None = None,
    priority: str | None = None,
    node_id: str | None = None,
    subtree: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    conditions: list[str] = []
    params: list[str | int] = []

    if agent_id:
        conditions.append("agent_id = ?")
        params.append(agent_id)
    if status:
        conditions.append("status = ?")
        params.append(status)
    if project_id:
        conditions.append("project_id = ?")
        params.append(project_id)
    if priority:
        conditions.append("priority = ?")
        params.append(priority)

    with get_platform_db() as db:
        node_frag, node_params = build_node_id_filter(db, node_id, subtree)
        if node_frag:
            conditions.append(node_frag)
            params.extend(node_params)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        rows = db.execute(
            f"SELECT id, title, description, agent_id, node_id, project_id, status, priority, checked_out_by, checked_out_at, created_at, updated_at FROM tasks{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/api/tasks", status_code=201)
def create_task(body: CreateTaskBody):
    task_id = str(uuid.uuid4())
    with get_platform_db() as db:
        db.execute(
            """INSERT INTO tasks (id, title, description, project_id, priority, agent_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                body.title,
                body.description,
                body.project_id,
                body.priority,
                body.agent_id,
            ),
        )
        db.commit()
        row = db.execute("SELECT id, title, description, agent_id, node_id, project_id, status, priority, checked_out_by, checked_out_at, created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        result = dict(row)

    event_bus.emit("task.created", {"id": task_id, "title": body.title})
    return result


@router.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    with get_platform_db() as db:
        row = db.execute("SELECT id, title, description, agent_id, node_id, project_id, status, priority, checked_out_by, checked_out_at, created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Task not found")
        return dict(row)


@router.patch("/api/tasks/{task_id}")
def update_task(task_id: str, body: PatchTaskBody):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    if not updates:
        raise HTTPException(400, "No valid fields to update")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [task_id]

    with get_platform_db() as db:
        result = db.execute(
            f"UPDATE tasks SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(404, "Task not found")
        row = db.execute("SELECT id, title, description, agent_id, node_id, project_id, status, priority, checked_out_by, checked_out_at, created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        task_result = dict(row)

    event_bus.emit("task.updated", {"id": task_id, **updates})
    return task_result


@router.patch("/api/tasks/{task_id}/transition")
def transition_task(task_id: str, body: TransitionBody):
    """Transition a task to a new state using the state machine.

    Validates that the transition is allowed from the current state.
    Returns 422 if the transition is invalid.
    """
    to_state = body.to_state
    if to_state not in TASK_STATES:
        raise HTTPException(400, f"Invalid state: {to_state}. Valid states: {sorted(TASK_STATES)}")

    with get_platform_db() as db:
        row = db.execute("SELECT id, title, description, agent_id, node_id, project_id, status, priority, checked_out_by, checked_out_at, created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Task not found")

        current_state = dict(row).get("status", "open")
        allowed = TASK_TRANSITIONS.get(current_state, [])

        if to_state not in allowed:
            raise HTTPException(
                422,
                f"Cannot transition from '{current_state}' to '{to_state}'. "
                f"Allowed transitions: {allowed}",
            )

        db.execute(
            "UPDATE tasks SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (to_state, task_id),
        )
        db.commit()

        updated = db.execute("SELECT id, title, description, agent_id, node_id, project_id, status, priority, checked_out_by, checked_out_at, created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        task_result = dict(updated) if updated else {"id": task_id, "status": to_state}

    event_bus.emit("task.updated", {"id": task_id, "status": to_state, "from_state": current_state})
    return task_result


@router.post("/api/tasks/{task_id}/checkout")
def checkout_task(task_id: str, body: CheckoutTaskBody | None = None):
    checked_out_by = body.checked_out_by if body else "user"

    with get_platform_db() as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status, checked_out_by FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not row:
                db.execute("ROLLBACK")
                raise HTTPException(404, "Task not found")
            if row["checked_out_by"] is not None:
                db.execute("ROLLBACK")
                raise HTTPException(409, f"Task already checked out by {row['checked_out_by']}")
            db.execute(
                """UPDATE tasks SET status = 'checked_out',
                   checked_out_by = ?, checked_out_at = ?,
                   updated_at = datetime('now')
                   WHERE id = ?""",
                (checked_out_by, datetime.now(timezone.utc).isoformat(), task_id),
            )
            db.execute("COMMIT")
        except HTTPException:
            raise
        except Exception:
            db.execute("ROLLBACK")
            raise

        row = db.execute("SELECT id, title, description, agent_id, node_id, project_id, status, priority, checked_out_by, checked_out_at, created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row)


@router.post("/api/tasks/{task_id}/release")
def release_task(task_id: str):
    with get_platform_db() as db:
        row = db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Task not found")
        db.execute(
            """UPDATE tasks SET status = 'open',
               checked_out_by = NULL, checked_out_at = NULL,
               updated_at = datetime('now')
               WHERE id = ?""",
            (task_id,),
        )
        db.commit()
        row = db.execute("SELECT id, title, description, agent_id, node_id, project_id, status, priority, checked_out_by, checked_out_at, created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return dict(row)
