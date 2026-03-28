"""Shared/common Pydantic models used across multiple routers."""

from pydantic import BaseModel


class TransitionBody(BaseModel):
    """Reusable state-machine transition request body."""
    to_state: str
