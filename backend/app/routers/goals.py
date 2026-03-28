from fastapi import APIRouter, HTTPException
from app.db.connections import get_platform_db
from app.db.tree_utils import build_node_id_filter
from app.services.event_bus import event_bus
from app.models.goals import GoalCreate, GoalUpdate
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/goals", tags=["Goals"])


@router.get("")
def list_goals(
    project_id: str | None = None,
    project_ids: str | None = None,
    node_id: str | None = None,
    subtree: bool = False,
):
    with get_platform_db() as db:
        conditions: list[str] = []
        params: list[str] = []

        if project_ids:
            ids = [pid.strip() for pid in project_ids.split(",") if pid.strip()]
            if ids:
                placeholders = ",".join("?" for _ in ids)
                conditions.append(f"project_id IN ({placeholders})")
                params.extend(ids)
        elif project_id:
            conditions.append("project_id = ?")
            params.append(project_id)

        node_frag, node_params = build_node_id_filter(db, node_id, subtree)
        if node_frag:
            conditions.append(node_frag)
            params.extend(node_params)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = db.execute(
            f"SELECT id, project_id, node_id, parent_id, title, description, status, progress_pct, owner, target_date, created_at, updated_at FROM goals{where} ORDER BY created_at",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("", status_code=201)
def create_goal(body: GoalCreate):
    goal_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_platform_db() as db:
        db.execute(
            """INSERT INTO goals (id, project_id, parent_id, title, description, status, progress_pct, owner, target_date, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (goal_id, body.project_id, body.parent_id, body.title, body.description,
             body.status, body.progress_pct, body.owner, body.target_date, now, now),
        )
        db.commit()
        row = db.execute("SELECT id, project_id, node_id, parent_id, title, description, status, progress_pct, owner, target_date, created_at, updated_at FROM goals WHERE id = ?", (goal_id,)).fetchone()
        result = dict(row)

    event_bus.emit("goal.created", {"id": goal_id, "title": body.title})
    return result


@router.get("/{goal_id}")
def get_goal(goal_id: str):
    with get_platform_db() as db:
        row = db.execute("SELECT id, project_id, node_id, parent_id, title, description, status, progress_pct, owner, target_date, created_at, updated_at FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Goal not found")
        return dict(row)


@router.patch("/{goal_id}")
def update_goal(goal_id: str, body: GoalUpdate):
    with get_platform_db() as db:
        existing = db.execute("SELECT id, project_id, node_id, parent_id, title, description, status, progress_pct, owner, target_date, created_at, updated_at FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Goal not found")

        updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            return dict(existing)

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [goal_id]
        db.execute(f"UPDATE goals SET {set_clause} WHERE id = ?", values)
        db.commit()
        row = db.execute("SELECT id, project_id, node_id, parent_id, title, description, status, progress_pct, owner, target_date, created_at, updated_at FROM goals WHERE id = ?", (goal_id,)).fetchone()
        result = dict(row)

    event_bus.emit("goal.updated", {"id": goal_id, **{k: v for k, v in updates.items() if k != "updated_at"}})
    return result


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: str):
    with get_platform_db() as db:
        existing = db.execute("SELECT id, project_id, node_id, parent_id, title, description, status, progress_pct, owner, target_date, created_at, updated_at FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Goal not found")
        db.execute("DELETE FROM goals WHERE parent_id = ?", (goal_id,))
        db.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        db.commit()
