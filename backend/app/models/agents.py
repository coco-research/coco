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


class ResumeFromCheckpointBody(BaseModel):
    task: Optional[str] = None
    checkpoint_data: Optional[dict] = None


class SpawnSubagentBody(BaseModel):
    task: str
    model: str = "sonnet"
    role: Optional[str] = None


# ---------------------------------------------------------------------------
# Inter-agent delegation
# ---------------------------------------------------------------------------


class CreateAgentTaskBody(BaseModel):
    """Body for `POST /api/agents/{to_id}/tasks` — Agent A delegates to Agent B."""
    prompt: str
    from_agent_id: Optional[str] = None


class CompleteAgentTaskBody(BaseModel):
    """Body for `PATCH /api/agent_tasks/{id}` — mark done or failed with a result."""
    status: str  # 'done' or 'failed'
    result: Optional[str] = None
