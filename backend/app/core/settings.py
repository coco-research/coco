"""Centralized Pydantic Settings for CoCo Platform backend.

This module wraps the env-var configuration historically scattered across
``app/config.py`` into a single typed ``Settings`` object validated by
``pydantic-settings``. The existing ``app/config.py`` module continues to work
for backward compatibility; new code should prefer ``get_settings()`` here.

Usage::

    from app.core.settings import get_settings
    settings = get_settings()
    if settings.rate_limit_enabled:
        ...

The values are read once at startup (``@lru_cache``-style singleton via
``get_settings``). Override in tests with ``get_settings.cache_clear()`` after
mutating env vars.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings sourced from environment variables.

    Mirrors the variables already declared in ``app/config.py``. Defaults match
    the legacy module so behaviour is unchanged. Source of truth for new
    Phase-2+ work going forward.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Paths ----
    coco_dir: Path = Field(default_factory=lambda: Path.home() / ".coco")
    hub_dir: Path = Field(default_factory=lambda: Path.home() / ".hub")

    # ---- Server ----
    platform_port: int = Field(default=8000, ge=1, le=65535)
    max_concurrent_agents: int = Field(default=3, ge=1, le=64)
    agent_timeout_minutes: int = Field(default=30, ge=1)
    chat_timeout_minutes: int = Field(default=5, ge=1)

    # ---- Database ----
    database_url: str | None = None  # falls back to sqlite:///{coco_dir}/platform.db

    # ---- Security ----
    coco_auth_token: str = ""
    coco_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    coco_rate_limit: bool = True
    coco_rate_limit_rpm: int = Field(default=120, ge=1)

    # ---- LLM ----
    local_llm_enabled: bool = True
    local_llm_timeout: int = Field(default=120, ge=1)
    local_llm_fallback_to_cloud: bool = True
    use_agent_sdk: bool = False
    deepgram_api_key: str = ""

    # ---- Convenience accessors ----
    @property
    def platform_db_path(self) -> Path:
        return self.coco_dir / "platform.db"

    @property
    def hub_db_path(self) -> Path:
        return self.hub_dir / "hub.db"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.coco_cors_origins.split(",") if o.strip()]

    @property
    def effective_database_url(self) -> str:
        return self.database_url or f"sqlite:///{self.platform_db_path}"

    @property
    def rate_limit_enabled(self) -> bool:
        return self.coco_rate_limit


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached ``Settings`` singleton.

    Call ``get_settings.cache_clear()`` in tests if you mutate env vars.
    """
    return Settings()


__all__ = ["Settings", "get_settings"]
