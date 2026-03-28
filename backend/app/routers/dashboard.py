import logging

from fastapi import APIRouter
from app.db.connections import get_hub_db, get_platform_db
from app.db.tree_utils import build_node_id_filter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard"])


def _project_source_counts(db, project_id: str) -> dict:
    """Get per-source content counts for a project."""
    counts = {"email": 0, "voice": 0, "jira": 0, "confluence": 0}
    try:
        rows = db.execute(
            """SELECT c.source, COUNT(*) as count
               FROM content c
               JOIN project_content pc ON c.id = pc.content_id
               WHERE pc.project_id = ?
               GROUP BY c.source""",
            (project_id,),
        ).fetchall()
        for r in rows:
            src = r["source"]
            if src in counts:
                counts[src] = r["count"]
            else:
                counts[src] = r["count"]
    except Exception:
        pass
    return counts


def _project_last_activity(db, project_id: str) -> str | None:
    """Get the most recent content created_at for a project."""
    try:
        row = db.execute(
            """SELECT MAX(c.created_at) as last_activity
               FROM content c
               JOIN project_content pc ON c.id = pc.content_id
               WHERE pc.project_id = ?""",
            (project_id,),
        ).fetchone()
        return row["last_activity"] if row else None
    except Exception:
        return None


def _daily_costs_platform(db, days: int = 7, node_where: str = "", node_params: list | None = None) -> dict:
    """Get daily cost totals from platform cost_ledger for the last N days."""
    try:
        params: list = [f"-{days} days"] + (node_params or [])
        rows = db.execute(
            f"""SELECT date(created_at) as d, COALESCE(SUM(cost_usd), 0) as total
               FROM cost_ledger
               WHERE created_at >= date('now', ?){node_where}
               GROUP BY date(created_at)
               ORDER BY d""",
            params,
        ).fetchall()
        return {r["d"]: r["total"] for r in rows}
    except Exception:
        return {}


def _daily_costs_hub(db, days: int = 7) -> dict:
    """Get daily cost totals from hub api_costs for the last N days."""
    try:
        rows = db.execute(
            """SELECT date(created_at) as d, COALESCE(SUM(cost_usd), 0) as total
               FROM api_costs
               WHERE created_at >= date('now', ?)
               GROUP BY date(created_at)
               ORDER BY d""",
            (f"-{days} days",),
        ).fetchall()
        return {r["d"]: r["total"] for r in rows}
    except Exception:
        return {}


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

    # Projects from hub.db (with per-source counts and last_activity)
    try:
        with get_hub_db() as db:
            rows = db.execute("""
                SELECT p.id, p.name, p.jira_key, p.active,
                    (SELECT COUNT(*) FROM project_content pc WHERE pc.project_id = p.id) as item_count
                FROM projects p ORDER BY p.name
            """).fetchall()
            projects = []
            for r in rows:
                p = dict(r)
                p["sources"] = _project_source_counts(db, p["id"])
                p["last_activity"] = _project_last_activity(db, p["id"])
                projects.append(p)
            result["projects"] = projects
    except Exception as e:
        logger.exception("dashboard: failed to load projects: %s", e)

    # Unsorted content count (exclude items classified/dismissed in platform.db)
    try:
        excluded_ids: list[str] = []
        try:
            with get_platform_db() as pdb:
                actioned = pdb.execute(
                    "SELECT hub_content_id FROM content_classifications"
                ).fetchall()
                excluded_ids = [r["hub_content_id"] for r in actioned]
        except Exception:
            pass

        with get_hub_db() as db:
            extra_filter = ""
            extra_params: list[str] = []
            if excluded_ids:
                placeholders = ",".join("?" for _ in excluded_ids)
                extra_filter = f" AND id NOT IN ({placeholders})"
                extra_params = excluded_ids

            row = db.execute(
                f"""SELECT COUNT(*) as cnt FROM content
                    WHERE id NOT IN (SELECT content_id FROM project_content){extra_filter}""",
                extra_params,
            ).fetchone()
            result["unsorted_count"] = row["cnt"] if row else 0
    except Exception:
        pass

    # Sync health — use explicit columns, normalize to "source" key
    try:
        with get_hub_db() as db:
            # Discover column names from the table
            try:
                sample = db.execute("SELECT * FROM sync_state LIMIT 1").fetchone()
                if sample:
                    col_names = sample.keys()
                else:
                    col_names = []
            except Exception:
                col_names = []

            rows = db.execute("SELECT * FROM sync_state").fetchall()
            health = []
            for r in rows:
                h = dict(r)
                # Normalize: frontend expects "source", not "source_name"
                if "source_name" in h and "source" not in h:
                    h["source"] = h.pop("source_name")
                # Ensure "last_sync" key exists
                if "last_sync" not in h:
                    h["last_sync"] = h.get("last_synced") or h.get("synced_at") or None
                health.append(h)
            result["health"] = health
    except Exception:
        pass

    # Drafts count for queue
    try:
        with get_hub_db() as db:
            row = db.execute("SELECT COUNT(*) as cnt FROM drafts WHERE status = 'pending'").fetchone()
            result["queue"]["drafts"] = row["cnt"] if row else 0
    except Exception:
        pass

    # Resolve node filter once for all platform.db queries
    node_where = ""
    node_params: list[str] = []
    try:
        if node_id:
            with get_platform_db() as db:
                node_frag, node_params = build_node_id_filter(db, node_id, subtree)
                if node_frag:
                    node_where = " AND " + node_frag
    except Exception:
        pass

    # Agents from platform.db
    try:
        with get_platform_db() as db:
            rows = db.execute(
                f"SELECT status, COUNT(*) as cnt FROM agents WHERE 1=1{node_where} GROUP BY status",
                node_params,
            ).fetchall()
            total = 0
            for r in rows:
                s = r["status"]
                c = r["cnt"]
                total += c
                if s in result["agents"]:
                    result["agents"][s] = c
            result["agents"]["total"] = total
    except Exception:
        pass

    # Queue tasks
    try:
        with get_platform_db() as db:
            row = db.execute(
                f"SELECT COUNT(*) as cnt FROM tasks WHERE status = 'open'{node_where}",
                node_params,
            ).fetchone()
            result["queue"]["total"] = row["cnt"] if row else 0
            row = db.execute(
                f"SELECT COUNT(*) as cnt FROM tasks WHERE status = 'open' AND priority = 'high'{node_where}",
                node_params,
            ).fetchone()
            result["queue"]["urgent"] = row["cnt"] if row else 0
    except Exception:
        pass

    # Classify count (unsorted content)
    result["queue"]["classify"] = result["unsorted_count"]

    # Costs — today + month totals
    try:
        with get_platform_db() as db:
            row = db.execute(
                f"SELECT COALESCE(SUM(cost_usd), 0) as total FROM cost_ledger WHERE created_at >= date('now'){node_where}",
                node_params,
            ).fetchone()
            result["costs"]["today_usd"] = round(row["total"], 4) if row else 0.0

            row = db.execute(
                f"SELECT COALESCE(SUM(cost_usd), 0) as total FROM cost_ledger WHERE created_at >= date('now', 'start of month'){node_where}",
                node_params,
            ).fetchone()
            result["costs"]["month_usd"] = round(row["total"], 4) if row else 0.0
    except Exception:
        pass

    # Also add hub api_costs to cost totals
    try:
        with get_hub_db() as db:
            try:
                row = db.execute(
                    "SELECT COALESCE(SUM(cost_usd), 0) as total FROM api_costs WHERE created_at >= date('now')"
                ).fetchone()
                result["costs"]["today_usd"] += round(row["total"], 4) if row else 0.0
            except Exception:
                pass
            try:
                row = db.execute(
                    "SELECT COALESCE(SUM(cost_usd), 0) as total FROM api_costs WHERE created_at >= date('now', 'start of month')"
                ).fetchone()
                result["costs"]["month_usd"] += round(row["total"], 4) if row else 0.0
            except Exception:
                pass
    except Exception:
        pass

    result["costs"]["today_usd"] = round(result["costs"]["today_usd"], 4)
    result["costs"]["month_usd"] = round(result["costs"]["month_usd"], 4)

    # Daily costs (last 7 days) — merge platform + hub
    daily_map: dict[str, float] = {}
    try:
        with get_platform_db() as db:
            for d, v in _daily_costs_platform(db, 7, node_where, node_params).items():
                daily_map[d] = daily_map.get(d, 0.0) + v
    except Exception:
        pass
    try:
        with get_hub_db() as db:
            for d, v in _daily_costs_hub(db, 7).items():
                daily_map[d] = daily_map.get(d, 0.0) + v
    except Exception:
        pass

    # Build sorted daily array (last 7 days, fill gaps with 0)
    from datetime import date, timedelta
    today = date.today()
    daily = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        daily.append(round(daily_map.get(d, 0.0), 4))
    result["costs"]["daily"] = daily

    return result
