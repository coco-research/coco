"""Pydantic models for chat endpoints."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    model: str | None = "sonnet"
    project_id: str | None = None
    session_id: str | None = None
    content_ids: list[str] | None = None


class SessionCreate(BaseModel):
    title: str | None = None
    model: str | None = "sonnet"


class SessionOut(BaseModel):
    id: str
    title: str | None
    model: str | None
    message_count: int
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    id: str
    session_id: str | None
    role: str
    content: str
    model: str | None
    tokens_used: int | None
    created_at: str
