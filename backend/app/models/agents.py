"""Pydantic models for agent endpoints."""

from typing import Optional
from pydantic import BaseModel


class CreateAgentBody(BaseModel):
    name: str
    model: str = "sonnet"
    project_id: Optional[str] = None
    node_id: Optional[str] = None
    role: str = "custom"
    system_prompt: Optional[str] = None
    task_description: Optional[str] = None
    working_directory: Optional[str] = None
    reports_to: Optional[str] = None


class PatchAgentBody(BaseModel):
    name: Optional[str] = None
    model: Optional[str] = None
    project_id: Optional[str] = None
    node_id: Optional[str] = None
    role: Optional[str] = None
    system_prompt: Optional[str] = None
    task_description: Optional[str] = None
    status: Optional[str] = None
    config: Optional[str] = None
    reports_to: Optional[str] = None


class SpawnAgentBody(BaseModel):
    task: Optional[str] = None
    yolo_mode: bool = False


class CreateRoleBody(BaseModel):
    slug: str
    name: str
    default_system_prompt: Optional[str] = None
    default_model: str = "sonnet"
    sort_order: int = 0


class RecruitAgentBody(BaseModel):
    node_id: str
    role_slug: str
    name: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
