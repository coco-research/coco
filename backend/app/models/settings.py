"""Pydantic models for settings endpoints."""

from pydantic import BaseModel


class UpdateSettingsBody(BaseModel):
    """Flexible settings update body.

    All fields are optional -- only provided fields are merged
    into the existing config.json via deep merge.
    """
    autonomy_level: str | None = None
    default_model: str | None = None
    theme: str | None = None
    notifications_enabled: bool | None = None
    tts_voice: str | None = None
    tts_enabled: bool | None = None
    max_concurrent_agents: int | None = None
    budget_alert_threshold: float | None = None
    extra: dict | None = None
