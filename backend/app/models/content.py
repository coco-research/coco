"""Pydantic models for content endpoints."""

from pydantic import BaseModel


class ClassifyContentBody(BaseModel):
    project_id: str
