from fastapi import APIRouter, Query
from app.db.connections import get_platform_db
from app.db.tree_utils import build_node_id_filter

router = APIRouter(tags=["Activity"])


@router.get("/api/activity")
def list_activity(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    agent_id: str | None = None,
    action: str | None = None,
    project_id: str | None = None,
    node_id: str | None = None,
    subtree: bool = False,
):
    try:
        conditions: list[str] = []
        params: list[str | int] = []

        if agent_id:
            conditions.append("item_id = ?")
            params.append(agent_id)
        if action:
            conditions.append("action = ?")
            params.append(action)
        if project_id:
            conditions.append("item_id IN (SELECT id FROM agents WHERE project_id = ?)")
            params.append(project_id)

        with get_platform_db() as db:
            node_frag, node_params = build_node_id_filter(db, node_id, subtree)
            if node_frag:
                conditions.append(node_frag)
                params.extend(node_params)

            where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

            rows = db.execute(
                f"SELECT id, action, item_type, item_id, autonomy_mode, confidence, decision_by, notes, created_at FROM governance_log{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []
