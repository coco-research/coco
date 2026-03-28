"""Pydantic models for collaboration endpoints (context, handoffs, workflows)."""

from typing import Optional
from pydantic import BaseModel


class CreateContextBody(BaseModel):
    section: str
    title: Optional[str] = None
    content: str
    author_agent_id: Optional[str] = None
    author_role: Optional[str] = None


class PatchContextBody(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author_agent_id: Optional[str] = None
    author_role: Optional[str] = None


class CreateHandoffBody(BaseModel):
    node_id: str
    from_agent_id: str
    from_role: Optional[str] = None
    to_role: str
    title: str
    description: Optional[str] = None
    workflow_id: Optional[str] = None


class PatchHandoffBody(BaseModel):
    status: str


class StartWorkflowBody(BaseModel):
    template_id: str
    objective: Optional[str] = None


class PatchWorkflowBody(BaseModel):
    status: Optional[str] = None
    current_step: Optional[int] = None
