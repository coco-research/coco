"""Pydantic models for entity extraction and insight endpoints."""

from pydantic import BaseModel


class ExtractRequest(BaseModel):
    content_id: str
    content_text: str
    mode: str = "regex"


class ExtractBatchRequest(BaseModel):
    content_ids: list[str]
    mode: str = "regex"


class InsightActionBody(BaseModel):
    action: str  # seen, actioned, dismissed
