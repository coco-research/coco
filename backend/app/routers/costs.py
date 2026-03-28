import uuid
from fastapi import APIRouter, HTTPException, Query
from app.db.connections import get_hub_db, get_platform_db
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
    daily_totals: list[float] = []

    # Platform cost_ledger
    try:
        with get_platform_db() as db:
            conditions = ["created_at >= datetime('now', ?)"]
            params: list[str | int] = [f"-{days} days"]

            node_frag, node_params = build_node_id_filter(db, node_id, subtree)
            if node_frag:
                conditions.append(node_frag)
                params.extend(node_params)

            where = " WHERE " + " AND ".join(conditions)
            rows = db.execute(
                f"SELECT model, project_id, cost_usd FROM cost_ledger{where}",
                params,
            ).fetchall()
            for r in rows:
                cost = r["cost_usd"] or 0.0
                total_usd += cost
                model = r["model"] or "unknown"
                by_model[model] = by_model.get(model, 0.0) + cost
                proj = r["project_id"] or "unassigned"
                by_project[proj] = by_project.get(proj, 0.0) + cost
    except Exception:
        pass

    # Hub api_costs
    try:
        with get_hub_db() as db:
            # Try common column name patterns
            try:
                rows = db.execute(
                    """SELECT model, project_id, cost_usd FROM api_costs
                       WHERE created_at >= datetime('now', ?)""",
                    (f"-{days} days",),
                ).fetchall()
            except Exception:
                try:
                    rows = db.execute(
                        """SELECT model, project_id, total_cost as cost_usd FROM api_costs
                           WHERE timestamp >= datetime('now', ?)""",
                        (f"-{days} days",),
                    ).fetchall()
                except Exception:
                    rows = []

            for r in rows:
                row = dict(r)
                cost = row.get("cost_usd") or row.get("total_cost") or 0.0
                total_usd += cost
                model = row.get("model") or "unknown"
                by_model[model] = by_model.get(model, 0.0) + cost
                proj = row.get("project_id") or "unassigned"
                by_project[proj] = by_project.get(proj, 0.0) + cost
    except Exception:
        pass

    daily_avg = total_usd / max(days, 1)

    # Build daily breakdown for SpendChart
    daily_by_date: dict[str, float] = {}

    try:
        with get_platform_db() as db:
            conditions_daily = ["created_at >= datetime('now', ?)"]
            params_daily: list[str | int] = [f"-{days} days"]

            node_frag_d, node_params_d = build_node_id_filter(db, node_id, subtree)
            if node_frag_d:
                conditions_daily.append(node_frag_d)
                params_daily.extend(node_params_d)

            where_daily = " WHERE " + " AND ".join(conditions_daily)
            rows = db.execute(
                f"""SELECT date(created_at) as d, COALESCE(SUM(cost_usd), 0) as total
                   FROM cost_ledger{where_daily}
                   GROUP BY date(created_at)
                   ORDER BY d""",
                params_daily,
            ).fetchall()
            for r in rows:
                daily_by_date[r["d"]] = daily_by_date.get(r["d"], 0.0) + r["total"]
    except Exception:
        pass

    try:
        with get_hub_db() as db:
            try:
                rows = db.execute(
                    """SELECT date(created_at) as d, COALESCE(SUM(cost_usd), 0) as total
                       FROM api_costs
                       WHERE created_at >= datetime('now', ?)
                       GROUP BY date(created_at)
                       ORDER BY d""",
                    (f"-{days} days",),
                ).fetchall()
                for r in rows:
                    daily_by_date[r["d"]] = daily_by_date.get(r["d"], 0.0) + r["total"]
            except Exception:
                pass
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
    conditions: list[str] = []
    params: list[str | int] = []

    if agent_id:
        conditions.append("agent_id = ?")
        params.append(agent_id)
    if project_id:
        conditions.append("project_id = ?")
        params.append(project_id)

    try:
        with get_platform_db() as db:
            node_frag, node_params = build_node_id_filter(db, node_id, subtree)
            if node_frag:
                conditions.append(node_frag)
                params.extend(node_params)

            where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

            rows = db.execute(
                f"SELECT id, agent_id, node_id, project_id, model, input_tokens, output_tokens, cost_usd, source, created_at FROM cost_ledger{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


@router.get("/api/budgets")
def list_budgets():
    try:
        with get_platform_db() as db:
            rows = db.execute("SELECT project_id, node_id, daily_cap_usd, weekly_cap_usd, monthly_cap_usd, alert_threshold_pct FROM budgets").fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


@router.post("/api/budgets", status_code=201)
def create_or_update_budget(body: CreateBudgetBody):
    project_id = body.project_id
    monthly_cap = body.monthly_cap_usd
    alert_threshold = body.alert_threshold_pct

    with get_platform_db() as db:
        db.execute(
            """INSERT INTO budgets (project_id, monthly_cap_usd, alert_threshold_pct)
               VALUES (?, ?, ?)
               ON CONFLICT(project_id) DO UPDATE SET
                 monthly_cap_usd = excluded.monthly_cap_usd,
                 alert_threshold_pct = excluded.alert_threshold_pct""",
            (project_id, monthly_cap, alert_threshold),
        )
        db.commit()
        row = db.execute("SELECT project_id, node_id, daily_cap_usd, weekly_cap_usd, monthly_cap_usd, alert_threshold_pct FROM budgets WHERE project_id = ?", (project_id,)).fetchone()
        return dict(row)
