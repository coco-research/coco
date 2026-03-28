"""Pydantic models for project endpoints."""

from pydantic import BaseModel


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
