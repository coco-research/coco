"""Pydantic models for task endpoints."""

from typing import Optional
from pydantic import BaseModel


class CreateTaskBody(BaseModel):
    title: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    priority: str = "medium"
    agent_id: Optional[str] = None


class PatchTaskBody(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    agent_id: Optional[str] = None
    project_id: Optional[str] = None


class CheckoutTaskBody(BaseModel):
    checked_out_by: str = "user"
