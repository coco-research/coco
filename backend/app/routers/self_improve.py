"""API endpoints for the self-improvement cycle feature."""

import json
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, insert, update

from app.models.self_improve import (
    StartCycleBody,
    ApproveImprovementBody,
    RejectImprovementBody,
    SelfImprovePreferences,
    CycleAnalyticsItem,
)
from app.services.self_improve import self_improve_service
from app.db.session import get_db
from app.db.tables import (
    self_improve_cycles,
    self_improve_improvements,
    self_improve_preferences,
)

router = APIRouter(prefix="/api/self-improve", tags=["Self-Improve"])


# ------------------------------------------------------------------
# Cycle management
# ------------------------------------------------------------------


@router.get("/cycles")
def list_cycles(limit: int = 10):
    """List recent self-improvement cycles."""
    return self_improve_service.list_cycles(limit=limit)


@router.post("/cycles", status_code=201)
def start_cycle(body: StartCycleBody):
    """Start a new self-improvement cycle."""
    try:
        return self_improve_service.start_cycle(
            budget_usd=body.budget_usd,
            max_improvements=body.max_improvements,
            focus_areas=body.focus_areas,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/cycles/active")
def get_active_cycle():
    """Get the currently active self-improvement cycle."""
    cycle = self_improve_service.get_active_cycle()
    if not cycle:
        raise HTTPException(status_code=404, detail="No active cycle")
    return cycle


@router.get("/cycles/{cycle_id}")
def get_cycle(cycle_id: str):
    """Get a self-improvement cycle by ID."""
    cycle = self_improve_service.get_cycle(cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return cycle


@router.post("/cycles/{cycle_id}/cancel")
def cancel_cycle(cycle_id: str):
    """Cancel a running self-improvement cycle."""
    try:
        return self_improve_service.cancel_cycle(cycle_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Cycle not found")
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ------------------------------------------------------------------
# Improvement actions
# ------------------------------------------------------------------


@router.get("/improvements/{improvement_id}")
def get_improvement(improvement_id: str):
    """Get a single improvement by ID."""
    imp = self_improve_service.get_improvement(improvement_id)
    if not imp:
        raise HTTPException(status_code=404, detail="Improvement not found")
    return imp


@router.get("/improvements/{improvement_id}/diff")
def get_improvement_diff(improvement_id: str):
    """Get the full diff for an improvement."""
    diff = self_improve_service.get_improvement_diff(improvement_id)
    if diff is None:
        raise HTTPException(status_code=404, detail="Improvement not found or no diff available")
    return {"diff": diff}


@router.post("/improvements/{improvement_id}/approve")
def approve_improvement(improvement_id: str, body: ApproveImprovementBody = ApproveImprovementBody()):
    """Approve an improvement — merges the worktree into main."""
    try:
        return self_improve_service.approve_improvement(improvement_id, comment=body.comment)
    except ValueError:
        raise HTTPException(status_code=404, detail="Improvement not found")
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/improvements/{improvement_id}/reject")
def reject_improvement(improvement_id: str, body: RejectImprovementBody = RejectImprovementBody()):
    """Reject an improvement — cleans up the worktree."""
    try:
        return self_improve_service.reject_improvement(improvement_id, reason=body.reason)
    except ValueError:
        raise HTTPException(status_code=404, detail="Improvement not found")
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ------------------------------------------------------------------
# Squad info
# ------------------------------------------------------------------


@router.get("/squad")
def get_squad():
    """Get the squad role template (roles and descriptions)."""
    return self_improve_service.get_squad_template()


@router.get("/cycles/{cycle_id}/agents")
def get_cycle_agents(cycle_id: str):
    """List all agents spawned for a specific cycle."""
    cycle = self_improve_service.get_cycle(cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Cycle not found")
    return self_improve_service.get_cycle_agents(cycle_id)


# ------------------------------------------------------------------
# Analytics
# ------------------------------------------------------------------


@router.get("/analytics")
def get_analytics(days: int = 30) -> list[CycleAnalyticsItem]:
    """Return aggregate stats for self-improvement cycles."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    with get_db() as conn:
        rows = conn.execute(
            select(
                self_improve_cycles.c.id,
                self_improve_cycles.c.status,
                self_improve_cycles.c.started_at,
                self_improve_cycles.c.completed_at,
                self_improve_cycles.c.spent_usd,
                self_improve_cycles.c.created_at,
            ).where(
                self_improve_cycles.c.created_at >= cutoff
            ).order_by(
                self_improve_cycles.c.created_at.asc()
            )
        ).fetchall()

        results: list[CycleAnalyticsItem] = []
        for row in rows:
            # Count improvements for this cycle
            imp_rows = conn.execute(
                select(self_improve_improvements.c.id, self_improve_improvements.c.diff_stat)
                .where(self_improve_improvements.c.cycle_id == row.id)
            ).fetchall()

            improvements_count = len(imp_rows)

            # Parse files_changed from diff_stat strings
            files_changed = 0
            for imp in imp_rows:
                ds = imp.diff_stat
                if ds and "file" in ds:
                    # e.g. "5 files changed, 120 insertions(+), 30 deletions(-)"
                    try:
                        files_changed += int(ds.split()[0])
                    except (ValueError, IndexError):
                        pass

            # Calculate duration
            duration_seconds = 0
            if row.started_at and row.completed_at:
                try:
                    start = datetime.fromisoformat(row.started_at)
                    end = datetime.fromisoformat(row.completed_at)
                    duration_seconds = int((end - start).total_seconds())
                except (ValueError, TypeError):
                    pass

            results.append(CycleAnalyticsItem(
                id=row.id,
                started_at=row.started_at,
                files_changed=files_changed,
                cost=row.spent_usd or 0.0,
                duration_seconds=duration_seconds,
                improvements_count=improvements_count,
                status=row.status,
            ))

        return results


# ------------------------------------------------------------------
# Preferences
# ------------------------------------------------------------------

_PREF_KEYS = ["auto_enabled", "cron_expression", "max_cost_per_cycle", "focus_areas"]

_PREF_DEFAULTS = SelfImprovePreferences()


@router.get("/preferences")
def get_preferences() -> SelfImprovePreferences:
    """Get self-improve auto-schedule preferences."""
    with get_db() as conn:
        rows = conn.execute(
            select(self_improve_preferences.c.key, self_improve_preferences.c.value)
            .where(self_improve_preferences.c.key.in_(_PREF_KEYS))
        ).fetchall()

        data: dict = {}
        for row in rows:
            key, value = row.key, row.value
            try:
                data[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                data[key] = value

        return SelfImprovePreferences(**data)


@router.post("/preferences")
def save_preferences(body: SelfImprovePreferences) -> SelfImprovePreferences:
    """Save self-improve auto-schedule preferences."""
    now = datetime.now(timezone.utc).isoformat()
    prefs = body.model_dump()

    with get_db() as conn:
        for key, value in prefs.items():
            serialized = json.dumps(value)
            # Upsert: try insert, on conflict update
            existing = conn.execute(
                select(self_improve_preferences.c.key)
                .where(self_improve_preferences.c.key == key)
            ).fetchone()

            if existing:
                conn.execute(
                    update(self_improve_preferences)
                    .where(self_improve_preferences.c.key == key)
                    .values(value=serialized, updated_at=now)
                )
            else:
                conn.execute(
                    insert(self_improve_preferences)
                    .values(key=key, value=serialized, updated_at=now)
                )

    return body
