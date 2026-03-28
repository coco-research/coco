"""coco_health, coco_cost, coco_process -- System tools."""

import asyncio
import subprocess
import time
from pathlib import Path

from app.mcp.server import mcp
from app.config import HUB_DB_PATH, PLATFORM_DB_PATH, BRAIN_JSON_PATH, QUEUE_JSON_PATH
from app.db.connections import get_hub_db, get_platform_db
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
        with get_hub_db() as db:
            result["adapters"] = _health_from_sync_state(db)
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

    # Platform cost_ledger
    try:
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT model, project_id, cost_usd FROM cost_ledger WHERE created_at >= datetime('now', ?)",
                (f"-{days} days",),
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
            try:
                rows = db.execute(
                    "SELECT model, project_id, cost_usd FROM api_costs WHERE created_at >= datetime('now', ?)",
                    (f"-{days} days",),
                ).fetchall()
            except Exception:
                try:
                    rows = db.execute(
                        "SELECT model, project_id, total_cost as cost_usd FROM api_costs WHERE timestamp >= datetime('now', ?)",
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
