"""Pydantic models for self-improve endpoints."""

from typing import Optional
from pydantic import BaseModel


class StartCycleBody(BaseModel):
    budget_usd: float = 5.0
    max_improvements: int = 5
    focus_areas: Optional[list[str]] = None  # e.g. ["performance", "ux", "tests"]


class CycleOut(BaseModel):
    id: str
    status: str  # idle, planning, architecting, developing, testing, reviewing, documenting, awaiting_approval, merging, integrating, completed, rejected, failed
    budget_usd: float
    spent_usd: float
    max_improvements: int
    focus_areas: list[str] | None
    improvements: list[dict]  # list of ImprovementOut
    agents_spawned: int
    started_at: str | None
    completed_at: str | None
    error: str | None


class ImprovementOut(BaseModel):
    id: str
    cycle_id: str
    title: str
    description: str
    priority: int  # 1 = highest
    category: str  # performance, ux, tests, refactor, feature, docs
    status: str  # proposed, approved, in_progress, testing, review, documenting, awaiting_approval, approved_by_human, rejected_by_human, merged, failed
    worktree_path: str | None
    branch_name: str | None
    diff_summary: str | None
    diff_stat: str | None  # e.g. "5 files changed, 120 insertions(+), 30 deletions(-)"
    test_results: dict | None  # {passed: int, failed: int, errors: int, output: str}
    review_notes: str | None
    security_scan: dict | None  # {passed: bool, issues: list[str]}
    pr_description: str | None
    agent_id: str | None  # which agent is working on it
    created_at: str
    updated_at: str


class ApproveImprovementBody(BaseModel):
    comment: str | None = None


class RejectImprovementBody(BaseModel):
    reason: str | None = None
