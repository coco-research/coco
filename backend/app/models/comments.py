"""Pydantic models for comment endpoints."""

from typing import Optional
from pydantic import BaseModel


class CreateCommentBody(BaseModel):
    entity_type: str
    entity_id: str
    parent_id: Optional[str] = None
    author: str = "user"
    body: str
    mentions: list[str] = []


class PatchCommentBody(BaseModel):
    body: Optional[str] = None
    mentions: Optional[list[str]] = None
