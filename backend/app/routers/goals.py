from fastapi import APIRouter, HTTPException
from sqlalchemy import insert, select, delete
from app.db.session import get_db
from app.db.tables import goals
from app.db.tree_utils import build_node_id_filter
from app.services.event_bus import event_bus
from app.models.goals import GoalCreate, GoalUpdate
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/goals", tags=["Goals"])

_GOAL_COLS = (
    "id, project_id, node_id, parent_id, title, description, status, "
    "progress_pct, owner, target_date, created_at, updated_at"
)


@router.get("")
def list_goals(
    project_id: str | None = None,
    project_ids: str | None = None,
    node_id: str | None = None,
    subtree: bool = False,
):
    with get_db() as conn:
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

        node_frag, node_params = build_node_id_filter(conn, node_id, subtree)
        if node_frag:
            conditions.append(node_frag)
            params.extend(node_params)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.exec_driver_sql(
            f"SELECT {_GOAL_COLS} FROM goals{where} ORDER BY created_at",
            tuple(params),
        ).fetchall()
        return [dict(r._mapping) for r in rows]


@router.post("", status_code=201)
def create_goal(body: GoalCreate):
    goal_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            insert(goals).values(
                id=goal_id,
                project_id=body.project_id,
                parent_id=body.parent_id,
                title=body.title,
                description=body.description,
                status=body.status,
                progress_pct=body.progress_pct,
                owner=body.owner,
                target_date=body.target_date,
                created_at=now,
                updated_at=now,
            )
        )
        row = conn.exec_driver_sql(
            f"SELECT {_GOAL_COLS} FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
        result = dict(row._mapping)

    event_bus.emit("goal.created", {"id": goal_id, "title": body.title})
    return result


@router.get("/{goal_id}")
def get_goal(goal_id: str):
    with get_db() as conn:
        row = conn.exec_driver_sql(
            f"SELECT {_GOAL_COLS} FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Goal not found")
        return dict(row._mapping)


@router.patch("/{goal_id}")
def update_goal(goal_id: str, body: GoalUpdate):
    with get_db() as conn:
        existing = conn.exec_driver_sql(
            f"SELECT {_GOAL_COLS} FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Goal not found")

        updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
        if not updates:
            return dict(existing._mapping)

        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [goal_id]
        conn.exec_driver_sql(f"UPDATE goals SET {set_clause} WHERE id = ?", tuple(values))
        row = conn.exec_driver_sql(
            f"SELECT {_GOAL_COLS} FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
        result = dict(row._mapping)

    event_bus.emit("goal.updated", {"id": goal_id, **{k: v for k, v in updates.items() if k != "updated_at"}})
    return result


@router.delete("/{goal_id}", status_code=204)
def delete_goal(goal_id: str):
    with get_db() as conn:
        existing = conn.exec_driver_sql(
            f"SELECT {_GOAL_COLS} FROM goals WHERE id = ?", (goal_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Goal not found")
        conn.execute(delete(goals).where(goals.c.parent_id == goal_id))
        conn.execute(delete(goals).where(goals.c.id == goal_id))
