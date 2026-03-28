import logging

from fastapi import APIRouter
from sqlalchemy import select, func, text
from app.db.session import get_db
from app.db.tables import (
    hub_projects, hub_content, hub_project_content, hub_drafts,
    hub_api_costs, hub_sync_state,
    agents, tasks, cost_ledger, content_classifications, nodes,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard"])


def _project_source_counts(conn, project_id: str) -> dict:
    """Get per-source content counts for a project."""
    counts = {"email": 0, "voice": 0, "jira": 0, "confluence": 0}
    try:
        rows = conn.execute(
            select(hub_content.c.source, func.count().label("count"))
            .join(hub_project_content, hub_content.c.id == hub_project_content.c.content_id)
            .where(hub_project_content.c.project_id == project_id)
            .group_by(hub_content.c.source)
        ).fetchall()
        for r in rows:
            counts[r.source] = r.count
    except Exception:
        pass
    return counts


def _project_last_activity(conn, project_id: str) -> str | None:
    """Get the most recent content created_at for a project."""
    try:
        row = conn.execute(
            select(func.max(hub_content.c.created_at).label("last_activity"))
            .join(hub_project_content, hub_content.c.id == hub_project_content.c.content_id)
            .where(hub_project_content.c.project_id == project_id)
        ).fetchone()
        return row.last_activity if row else None
    except Exception:
        return None


@router.get("/api/dashboard")
def get_dashboard(node_id: str | None = None, subtree: bool = True):
    result: dict = {
        "projects": [],
        "agents": {"running": 0, "paused": 0, "idle": 0, "total": 0},
        "queue": {"total": 0, "urgent": 0, "drafts": 0, "classify": 0},
        "costs": {"today_usd": 0.0, "month_usd": 0.0, "daily": []},
        "health": [],
        "unsorted_count": 0,
    }

    with get_db() as conn:
        # Projects from hub mirror (with per-source counts and last_activity)
        try:
            item_count_sq = (
                select(func.count())
                .select_from(hub_project_content)
                .where(hub_project_content.c.project_id == hub_projects.c.id)
                .correlate(hub_projects)
                .scalar_subquery()
                .label("item_count")
            )
            rows = conn.execute(
                select(
                    hub_projects.c.id,
                    hub_projects.c.name,
                    hub_projects.c.jira_key,
                    hub_projects.c.active,
                    item_count_sq,
                ).order_by(hub_projects.c.name)
            ).fetchall()
            projects = []
            for r in rows:
                p = dict(r._mapping)
                p["sources"] = _project_source_counts(conn, p["id"])
                p["last_activity"] = _project_last_activity(conn, p["id"])
                projects.append(p)
            result["projects"] = projects
        except Exception as e:
            logger.exception("dashboard: failed to load projects: %s", e)

        # Unsorted content count
        try:
            actioned_ids: list[str] = []
            try:
                actioned = conn.execute(
                    select(content_classifications.c.hub_content_id)
                ).fetchall()
                actioned_ids = [r.hub_content_id for r in actioned]
            except Exception:
                pass

            # Content not in project_content and not classified
            conditions = [
                hub_content.c.id.notin_(
                    select(hub_project_content.c.content_id)
                )
            ]
            if actioned_ids:
                conditions.append(hub_content.c.id.notin_(actioned_ids))

            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(hub_content)
                .where(*conditions)
            ).fetchone()
            result["unsorted_count"] = row.cnt if row else 0
        except Exception:
            pass

        # Sync health from hub mirror
        try:
            rows = conn.execute(select(hub_sync_state)).fetchall()
            health = []
            for r in rows:
                h = dict(r._mapping)
                # Normalize key names for frontend
                if "source_name" in h and "source" not in h:
                    h["source"] = h.pop("source_name")
                if "source" not in h:
                    h["source"] = h.get("source", "unknown")
                if "last_sync" not in h:
                    h["last_sync"] = h.get("last_synced") or h.get("synced_at") or None
                health.append(h)
            result["health"] = health
        except Exception:
            pass

        # Drafts count for queue
        try:
            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(hub_drafts)
                .where(hub_drafts.c.status == "pending")
            ).fetchone()
            result["queue"]["drafts"] = row.cnt if row else 0
        except Exception:
            pass

        # Resolve node filter
        node_ids: list[str] | None = None
        try:
            if node_id:
                node_ids = _resolve_node_ids(conn, node_id, subtree)
        except Exception:
            pass

        # Agents
        try:
            stmt = select(agents.c.status, func.count().label("cnt"))
            if node_ids is not None:
                stmt = stmt.where(agents.c.node_id.in_(node_ids))
            stmt = stmt.group_by(agents.c.status)
            rows = conn.execute(stmt).fetchall()
            total = 0
            for r in rows:
                s = r.status
                c = r.cnt
                total += c
                if s in result["agents"]:
                    result["agents"][s] = c
            result["agents"]["total"] = total
        except Exception:
            pass

        # Queue tasks
        try:
            stmt = select(func.count().label("cnt")).select_from(tasks).where(tasks.c.status == "open")
            if node_ids is not None:
                stmt = stmt.where(tasks.c.node_id.in_(node_ids))
            row = conn.execute(stmt).fetchone()
            result["queue"]["total"] = row.cnt if row else 0

            stmt = select(func.count().label("cnt")).select_from(tasks).where(tasks.c.status == "open", tasks.c.priority == "high")
            if node_ids is not None:
                stmt = stmt.where(tasks.c.node_id.in_(node_ids))
            row = conn.execute(stmt).fetchone()
            result["queue"]["urgent"] = row.cnt if row else 0
        except Exception:
            pass

        result["queue"]["classify"] = result["unsorted_count"]

        # Costs — today + month totals
        try:
            stmt = select(func.coalesce(func.sum(cost_ledger.c.cost_usd), 0).label("total")).where(cost_ledger.c.created_at >= text("date('now')"))
            if node_ids is not None:
                stmt = stmt.where(cost_ledger.c.node_id.in_(node_ids))
            row = conn.execute(stmt).fetchone()
            result["costs"]["today_usd"] = round(row.total, 4) if row else 0.0

            stmt = select(func.coalesce(func.sum(cost_ledger.c.cost_usd), 0).label("total")).where(cost_ledger.c.created_at >= text("date('now', 'start of month')"))
            if node_ids is not None:
                stmt = stmt.where(cost_ledger.c.node_id.in_(node_ids))
            row = conn.execute(stmt).fetchone()
            result["costs"]["month_usd"] = round(row.total, 4) if row else 0.0
        except Exception:
            pass

        # Hub api_costs
        try:
            row = conn.execute(
                select(func.coalesce(func.sum(hub_api_costs.c.cost_usd), 0).label("total"))
                .where(hub_api_costs.c.created_at >= text("date('now')"))
            ).fetchone()
            result["costs"]["today_usd"] += round(row.total, 4) if row else 0.0

            row = conn.execute(
                select(func.coalesce(func.sum(hub_api_costs.c.cost_usd), 0).label("total"))
                .where(hub_api_costs.c.created_at >= text("date('now', 'start of month')"))
            ).fetchone()
            result["costs"]["month_usd"] += round(row.total, 4) if row else 0.0
        except Exception:
            pass

        result["costs"]["today_usd"] = round(result["costs"]["today_usd"], 4)
        result["costs"]["month_usd"] = round(result["costs"]["month_usd"], 4)

        # Daily costs (last 7 days)
        daily_map: dict[str, float] = {}
        try:
            stmt = (
                select(
                    func.date(cost_ledger.c.created_at).label("d"),
                    func.coalesce(func.sum(cost_ledger.c.cost_usd), 0).label("total"),
                )
                .where(cost_ledger.c.created_at >= text("date('now', '-7 days')"))
            )
            if node_ids is not None:
                stmt = stmt.where(cost_ledger.c.node_id.in_(node_ids))
            stmt = stmt.group_by(text("d")).order_by(text("d"))
            for r in conn.execute(stmt).fetchall():
                daily_map[r.d] = daily_map.get(r.d, 0.0) + r.total
        except Exception:
            pass

        try:
            stmt = (
                select(
                    func.date(hub_api_costs.c.created_at).label("d"),
                    func.coalesce(func.sum(hub_api_costs.c.cost_usd), 0).label("total"),
                )
                .where(hub_api_costs.c.created_at >= text("date('now', '-7 days')"))
                .group_by(text("d"))
                .order_by(text("d"))
            )
            for r in conn.execute(stmt).fetchall():
                daily_map[r.d] = daily_map.get(r.d, 0.0) + r.total
        except Exception:
            pass

        from datetime import date, timedelta
        today = date.today()
        daily = []
        for i in range(6, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            daily.append(round(daily_map.get(d, 0.0), 4))
        result["costs"]["daily"] = daily

    return result


def _resolve_node_ids(conn, node_id: str, subtree: bool) -> list[str]:
    """Resolve node_id to list of IDs (including subtree if requested)."""
    if not subtree:
        return [node_id]
    row = conn.execute(
        select(nodes.c.path).where(nodes.c.id == node_id)
    ).fetchone()
    if not row:
        return [node_id]
    rows = conn.execute(
        select(nodes.c.id).where(nodes.c.path.like(row.path + "%"))
    ).fetchall()
    return [r.id for r in rows]
