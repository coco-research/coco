"""Pydantic models for brain/people endpoints."""

from pydantic import BaseModel


class UpdatePersonBody(BaseModel):
    """Update a person in brain.json. All fields optional -- only set fields are merged."""
    full_name: str | None = None
    priority: str | None = None
    role: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    attention_rules: list[dict] | None = None
