"""Subagent Manager — parent-child agent relationships with budget enforcement.

Hard cap: max 3 subagents per parent.
Subagents inherit node_id from parent for cost tracking.
"""

import uuid
import structlog
from sqlalchemy import insert, select, update, delete, func

from app.db.session import get_db
from app.db.tables import agents, cost_ledger, budgets

log = structlog.get_logger()

MAX_SUBAGENTS_PER_PARENT = 3


def spawn_subagent(
    parent_id: str,
    task: str,
    model: str = "sonnet",
    role: str | None = None,
) -> dict:
    """Register a child agent under parent_id.

    Raises:
        ValueError: if parent not found, cap exceeded, or budget exceeded.
    """
    with get_db() as conn:
        # 1. Validate parent exists
        parent_row = conn.exec_driver_sql(
            "SELECT id, name, node_id, project_id, model FROM agents WHERE id = ?",
            (parent_id,),
        ).fetchone()
        if not parent_row:
            raise ValueError(f"Parent agent {parent_id} not found")
        parent = dict(parent_row._mapping)

        # 2. Check subagent cap
        count_row = conn.execute(
            select(func.count())
            .select_from(agents)
            .where(agents.c.reports_to == parent_id)
            .where(agents.c.status.in_(("idle", "running", "paused")))
        ).fetchone()
        active_count = count_row[0] if count_row else 0

        if active_count >= MAX_SUBAGENTS_PER_PARENT:
            raise ValueError(
                f"Subagent cap reached: {active_count}/{MAX_SUBAGENTS_PER_PARENT} "
                f"active subagents under parent {parent_id}"
            )

        # 3. Budget check — use parent's node_id
        node_id = parent.get("node_id")
        project_id = parent.get("project_id")
        if node_id:
            _check_budget(conn, node_id, project_id)

        # 4. Create child agent
        child_id = uuid.uuid4().hex
        child_name = f"{parent.get('name', 'Agent')}-sub-{active_count + 1}"
        conn.execute(
            insert(agents).values(
                id=child_id,
                name=child_name,
                node_id=node_id,
                project_id=project_id,
                model=model,
                role=role or "custom",
                status="idle",
                task_description=task,
                reports_to=parent_id,
            )
        )

        child_row = conn.exec_driver_sql(
            "SELECT id, name, node_id, project_id, model, role, status, "
            "task_description, reports_to, created_at, updated_at "
            "FROM agents WHERE id = ?",
            (child_id,),
        ).fetchone()
        result = dict(child_row._mapping)

    log.info(
        "subagent_spawned",
        parent_id=parent_id,
        child_id=child_id,
        model=model,
        role=role,
    )
    return result


def list_subagents(parent_id: str) -> list[dict]:
    """Return all direct children of a parent agent."""
    with get_db() as conn:
        rows = conn.exec_driver_sql(
            "SELECT id, name, node_id, project_id, model, role, status, "
            "task_description, reports_to, created_at, updated_at "
            "FROM agents WHERE reports_to = ? ORDER BY created_at ASC",
            (parent_id,),
        ).fetchall()
        return [dict(r._mapping) for r in rows]


def kill_subagent(subagent_id: str) -> dict:
    """Mark a subagent as killed and stop it.

    Raises ValueError if not found or not a subagent.
    """
    with get_db() as conn:
        row = conn.exec_driver_sql(
            "SELECT id, name, reports_to, status FROM agents WHERE id = ?",
            (subagent_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Agent {subagent_id} not found")
        agent = dict(row._mapping)
        if not agent.get("reports_to"):
            raise ValueError(f"Agent {subagent_id} is not a subagent (no reports_to)")

        # Try to kill the process if running
        if agent["status"] in ("running", "paused"):
            try:
                from app.services.process_manager import process_manager  # noqa: lazy import (cycle)
                process_manager.kill(subagent_id)
            except Exception as e:
                log.warning("subagent_kill_process_failed", id=subagent_id, error=str(e))

        conn.exec_driver_sql(
            "UPDATE agents SET status = 'killed', stopped_at = datetime('now'), "
            "updated_at = datetime('now') WHERE id = ?",
            (subagent_id,),
        )

        updated = conn.exec_driver_sql(
            "SELECT id, name, node_id, project_id, model, role, status, "
            "task_description, reports_to, created_at, updated_at "
            "FROM agents WHERE id = ?",
            (subagent_id,),
        ).fetchone()
        result = dict(updated._mapping)

    log.info("subagent_killed", id=subagent_id, parent_id=agent.get("reports_to"))
    return result


# ---------------------------------------------------------------------------
# Budget helper
# ---------------------------------------------------------------------------

def _check_budget(conn, node_id: str, project_id: str | None) -> None:
    """Raise ValueError if daily budget is exceeded for the node/project."""
    budget_row = conn.execute(
        select(budgets.c.daily_cap_usd)
        .where(
            (budgets.c.node_id == node_id)
            | (budgets.c.project_id == project_id)
        )
    ).fetchone()
    if not budget_row or not budget_row._mapping.get("daily_cap_usd"):
        return  # No budget cap set

    daily_cap = budget_row._mapping["daily_cap_usd"]

    spent_row = conn.exec_driver_sql(
        "SELECT COALESCE(SUM(cost_usd), 0) as total "
        "FROM cost_ledger "
        "WHERE (node_id = ? OR project_id = ?) "
        "AND created_at >= datetime('now', '-1 day')",
        (node_id, project_id),
    ).fetchone()
    spent = spent_row._mapping["total"] if spent_row else 0.0

    if spent >= daily_cap:
        raise ValueError(
            f"Daily budget exceeded: ${spent:.2f} spent of ${daily_cap:.2f} cap"
        )
