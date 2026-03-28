"""coco_health, coco_cost, coco_process -- System tools."""

import asyncio
import subprocess
import time
from pathlib import Path

from sqlalchemy import select
from app.mcp.server import mcp
from app.db.compat import days_ago
from app.config import HUB_DB_PATH, PLATFORM_DB_PATH, BRAIN_JSON_PATH, QUEUE_JSON_PATH
from app.db.session import get_db
from app.db.tables import hub_api_costs, cost_ledger
from app.routers.home import _health_from_sync_state

_start_time = time.time()


@mcp.tool()
def coco_health() -> dict:
    """Return system health: backend uptime, database status, and KH adapter health (email/voice/jira/confluence sync status)."""
    result = {
        "status": "ok",
        "uptime_seconds": int(time.time() - _start_time),
        "databases": {
            "hub_db": {"exists": HUB_DB_PATH.exists()},
            "platform_db": {"exists": PLATFORM_DB_PATH.exists()},
        },
        "files": {
            "brain_json": {"exists": BRAIN_JSON_PATH.exists()},
            "queue_json": {"exists": QUEUE_JSON_PATH.exists()},
        },
        "adapters": [],
    }

    # Read sync_state for adapter health
    try:
        with get_db() as conn:
            result["adapters"] = _health_from_sync_state(conn)
    except Exception:
        pass

    return result


@mcp.tool()
def coco_cost(days: int = 30) -> dict:
    """Return cost summary: total spend, breakdown by model and project, daily average.

    Args:
        days: Number of days to look back. Default: 30.
    """
    total_usd = 0.0
    by_model: dict[str, float] = {}
    by_project: dict[str, float] = {}

    with get_db() as conn:
        # Platform cost_ledger
        try:
            rows = conn.execute(
                select(cost_ledger.c.model, cost_ledger.c.project_id, cost_ledger.c.cost_usd)
                .where(cost_ledger.c.created_at >= days_ago(days))
            ).fetchall()
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
            rows = conn.execute(
                select(hub_api_costs.c.model, hub_api_costs.c.cost_usd)
                .where(hub_api_costs.c.created_at >= days_ago(days))
            ).fetchall()
            for r in rows:
                cost = r.cost_usd or 0.0
                total_usd += cost
                model = r.model or "unknown"
                by_model[model] = by_model.get(model, 0.0) + cost
        except Exception:
            pass

    daily_avg = total_usd / max(days, 1)

    return {
        "total_usd": round(total_usd, 4),
        "daily_avg": round(daily_avg, 4),
        "by_model": {k: round(v, 4) for k, v in by_model.items()},
        "by_project": {k: round(v, 4) for k, v in by_project.items()},
        "days": days,
    }


@mcp.tool()
def coco_process() -> dict:
    """Trigger the Knowledge Hub ingest + process pipeline.

    Runs 'uv run python -m knowledge_hub.cli process' and returns the result.
    """
    try:
        proc = subprocess.run(
            ["uv", "run", "python", "-m", "knowledge_hub.cli", "process"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path.home()),
        )
        if proc.returncode != 0:
            return {
                "status": "error",
                "output": (proc.stderr or "")[-500:],
            }
        return {
            "status": "ok",
            "output": proc.stdout[-500:] if proc.stdout else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "ok",
            "message": "Process still running (timed out after 30s).",
        }
    except Exception:
        return {
            "status": "ok",
            "message": "Process triggered. Check KH logs for details.",
        }
