"""Pydantic models for Jarvis command endpoints."""

from pydantic import BaseModel, Field


class CommandRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    project_id: str | None = None
    context: list[dict] | None = None  # recent command-response pairs from frontend


class CardActionModel(BaseModel):
    label: str
    action: str
    endpoint: str | None = None
    method: str | None = None
    payload: dict | None = None


class CardDataModel(BaseModel):
    id: str
    type: str
    data: dict
    actions: list[CardActionModel] = []


class CommandResponse(BaseModel):
    reply: str
    action: str | None = None
    url: str | None = None
    cards: list[CardDataModel] = []
