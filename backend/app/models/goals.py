"""Pydantic models for goal endpoints."""

from pydantic import BaseModel


class GoalCreate(BaseModel):
    project_id: str | None = None
    parent_id: str | None = None
    title: str
    description: str | None = None
    status: str = "active"
    progress_pct: int = 0
    owner: str | None = None
    target_date: str | None = None


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    progress_pct: int | None = None
    owner: str | None = None
    target_date: str | None = None
    parent_id: str | None = None
