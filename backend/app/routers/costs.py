import uuid
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func, text
from app.db.session import get_db
from app.db.tables import cost_ledger, budgets, hub_api_costs
from app.db.compat import days_ago, date_trunc_day
from app.db.tree_utils import build_node_id_filter
from app.models.costs import CreateBudgetBody

router = APIRouter(tags=["Costs"])


@router.get("/api/costs/summary")
def cost_summary(
    days: int = Query(30, ge=1, le=365),
    node_id: str | None = None,
    subtree: bool = False,
):
    total_usd = 0.0
    by_model: dict[str, float] = {}
    by_project: dict[str, float] = {}
    daily_by_date: dict[str, float] = {}

    with get_db() as conn:
        # Platform cost_ledger
        try:
            node_ids = _resolve_node_ids(conn, node_id, subtree)
            conditions = [cost_ledger.c.created_at >= days_ago(days)]
            if node_ids is not None:
                conditions.append(cost_ledger.c.node_id.in_(node_ids))

            stmt = select(
                cost_ledger.c.model,
                cost_ledger.c.project_id,
                cost_ledger.c.cost_usd,
            ).where(*conditions)
            rows = conn.execute(stmt).fetchall()
            for r in rows:
                cost = r.cost_usd or 0.0
                total_usd += cost
                model = r.model or "unknown"
                by_model[model] = by_model.get(model, 0.0) + cost
                proj = r.project_id or "unassigned"
                by_project[proj] = by_project.get(proj, 0.0) + cost
        except Exception:
            pass

        # Hub api_costs (mirror)
        try:
            stmt = select(
                hub_api_costs.c.model,
                hub_api_costs.c.cost_usd,
            ).where(hub_api_costs.c.created_at >= days_ago(days))
            rows = conn.execute(stmt).fetchall()
            for r in rows:
                cost = r.cost_usd or 0.0
                total_usd += cost
                model = r.model or "unknown"
                by_model[model] = by_model.get(model, 0.0) + cost
        except Exception:
            pass

        daily_avg = total_usd / max(days, 1)

        # Daily breakdown — platform
        try:
            conditions_d = [cost_ledger.c.created_at >= days_ago(days)]
            if node_ids is not None:
                conditions_d.append(cost_ledger.c.node_id.in_(node_ids))

            d_col = date_trunc_day(cost_ledger.c.created_at).label("d")
            stmt = (
                select(
                    d_col,
                    func.coalesce(func.sum(cost_ledger.c.cost_usd), 0).label("total"),
                )
                .where(*conditions_d)
                .group_by(d_col)
                .order_by(d_col)
            )
            rows = conn.execute(stmt).fetchall()
            for r in rows:
                daily_by_date[r.d] = daily_by_date.get(r.d, 0.0) + r.total
        except Exception:
            pass

        # Daily breakdown — hub
        try:
            d_col2 = date_trunc_day(hub_api_costs.c.created_at).label("d")
            stmt = (
                select(
                    d_col2,
                    func.coalesce(func.sum(hub_api_costs.c.cost_usd), 0).label("total"),
                )
                .where(hub_api_costs.c.created_at >= days_ago(days))
                .group_by(d_col2)
                .order_by(d_col2)
            )
            rows = conn.execute(stmt).fetchall()
            for r in rows:
                daily_by_date[r.d] = daily_by_date.get(r.d, 0.0) + r.total
        except Exception:
            pass

    daily = [
        {"date": d, "cost_usd": round(v, 4)}
        for d, v in sorted(daily_by_date.items())
    ]

    return {
        "total_usd": round(total_usd, 4),
        "daily_avg": round(daily_avg, 4),
        "by_model": {k: round(v, 4) for k, v in by_model.items()},
        "by_project": {k: round(v, 4) for k, v in by_project.items()},
        "daily": daily,
    }


@router.get("/api/costs/events")
def cost_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    agent_id: str | None = None,
    project_id: str | None = None,
    node_id: str | None = None,
    subtree: bool = False,
):
    try:
        with get_db() as conn:
            conditions = []
            if agent_id:
                conditions.append(cost_ledger.c.agent_id == agent_id)
            if project_id:
                conditions.append(cost_ledger.c.project_id == project_id)

            node_ids = _resolve_node_ids(conn, node_id, subtree)
            if node_ids is not None:
                conditions.append(cost_ledger.c.node_id.in_(node_ids))

            stmt = select(cost_ledger)
            if conditions:
                stmt = stmt.where(*conditions)
            stmt = stmt.order_by(cost_ledger.c.created_at.desc()).limit(limit).offset(offset)
            rows = conn.execute(stmt).fetchall()
            return [dict(r._mapping) for r in rows]
    except Exception:
        return []


@router.get("/api/budgets")
def list_budgets():
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    budgets.c.project_id,
                    budgets.c.node_id,
                    budgets.c.daily_cap_usd,
                    budgets.c.weekly_cap_usd,
                    budgets.c.monthly_cap_usd,
                    budgets.c.alert_threshold_pct,
                )
            ).fetchall()
            return [dict(r._mapping) for r in rows]
    except Exception:
        return []


@router.post("/api/budgets", status_code=201)
def create_or_update_budget(body: CreateBudgetBody):
    project_id = body.project_id
    monthly_cap = body.monthly_cap_usd
    alert_threshold = body.alert_threshold_pct

    with get_db() as conn:
        conn.execute(
            text(
                "INSERT INTO budgets (project_id, monthly_cap_usd, alert_threshold_pct) "
                "VALUES (:pid, :cap, :thresh) "
                "ON CONFLICT(project_id) DO UPDATE SET "
                "monthly_cap_usd = excluded.monthly_cap_usd, "
                "alert_threshold_pct = excluded.alert_threshold_pct"
            ),
            {"pid": project_id, "cap": monthly_cap, "thresh": alert_threshold},
        )
        row = conn.execute(
            select(
                budgets.c.project_id,
                budgets.c.node_id,
                budgets.c.daily_cap_usd,
                budgets.c.weekly_cap_usd,
                budgets.c.monthly_cap_usd,
                budgets.c.alert_threshold_pct,
            ).where(budgets.c.project_id == project_id)
        ).fetchone()
        return dict(row._mapping)


def _resolve_node_ids(conn, node_id: str | None, subtree: bool) -> list[str] | None:
    """Resolve node_id filter to list of IDs, or None if no filtering needed."""
    if not node_id:
        return None
    if subtree:
        from app.db.tables import nodes
        row = conn.execute(
            select(nodes.c.path).where(nodes.c.id == node_id)
        ).fetchone()
        if not row:
            return [node_id]
        rows = conn.execute(
            select(nodes.c.id).where(nodes.c.path.like(row.path + "%"))
        ).fetchall()
        return [r.id for r in rows]
    return [node_id]
