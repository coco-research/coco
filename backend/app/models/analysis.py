"""Pydantic models for analysis pipeline endpoints."""

from typing import Optional
from pydantic import BaseModel


class AnalyzeFolderBody(BaseModel):
    folder_path: Optional[str] = None
    analysis_type: str = "full"  # full | summary | extract-actions | custom
    custom_prompt: Optional[str] = None
    file_patterns: Optional[list[str]] = None
    max_files: int = 50
