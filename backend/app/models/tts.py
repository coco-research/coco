"""Pydantic models for TTS endpoints."""

from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    voice: str = "andrew"  # default: Edge Andrew (American, deep)
    speed: str = "-5%"   # slightly slower for gravitas
