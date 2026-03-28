"""Pydantic models for Podcast endpoints."""

from pydantic import BaseModel, Field


class GeneratePodcastBody(BaseModel):
    voice: str = "andrew"


class PodcastResponse(BaseModel):
    id: str
    title: str
    script: str | None = None
    audio_path: str | None = None
    duration: float | None = None
    voice: str | None = "andrew"
    status: str | None = "pending"
    created_at: str


class PodcastListResponse(BaseModel):
    items: list[PodcastResponse]
    count: int
