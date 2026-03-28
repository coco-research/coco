"""Pydantic models for tree endpoints."""

from typing import Optional
from pydantic import BaseModel


class CreateNodeBody(BaseModel):
    parent_id: str
    label: str
    node_type: str = "group"
    hub_project_id: Optional[str] = None
    sort_order: Optional[int] = 0
    icon: Optional[str] = None
    color: Optional[str] = None
    folder_path: Optional[str] = None
    github_repo: Optional[str] = None
    jira_key: Optional[str] = None
    confluence_space: Optional[str] = None


class PatchNodeBody(BaseModel):
    label: Optional[str] = None
    node_type: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    folder_path: Optional[str] = None
    github_repo: Optional[str] = None
    jira_key: Optional[str] = None
    confluence_space: Optional[str] = None
    metadata: Optional[str] = None
    sort_order: Optional[int] = None


class MoveNodeBody(BaseModel):
    new_parent_id: str
    sort_order: Optional[int] = None


class ReorderItem(BaseModel):
    id: str
    sort_order: int
