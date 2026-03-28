"""Pydantic models for cost/budget endpoints."""

from pydantic import BaseModel


class CreateBudgetBody(BaseModel):
    project_id: str
    monthly_cap_usd: float
    alert_threshold_pct: float = 0.8
