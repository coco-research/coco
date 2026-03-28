"""API endpoints for the self-improvement cycle feature."""

from fastapi import APIRouter, HTTPException
from app.models.self_improve import (
    StartCycleBody,
    ApproveImprovementBody,
    RejectImprovementBody,
)
from app.services.self_improve import self_improve_service

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
