"""Pydantic models for todo endpoints."""

from pydantic import BaseModel


class CreateTodoBody(BaseModel):
    title: str
    project_id: str | None = None
    priority: str = "medium"
    owner: str | None = None
    due_date: str | None = None
    node_id: str | None = None


class PatchTodoBody(BaseModel):
    title: str | None = None
    status: str | None = None
    priority: str | None = None
    owner: str | None = None
    due_date: str | None = None
    project_id: str | None = None
    node_id: str | None = None


class MergeTodosBody(BaseModel):
    keep_id: str
    remove_ids: list[str]


class CreateDependencyBody(BaseModel):
    depends_on: str
    dep_type: str = "blocked_by"


class CreateBlockedByBody(BaseModel):
    """Body for POST /api/todos/:id/blocked_by — adds a blocker to this todo."""

    blocker_id: str
