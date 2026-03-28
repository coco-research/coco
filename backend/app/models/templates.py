"""Pydantic models for template (project export/import) endpoints."""

from typing import Optional
from pydantic import BaseModel


class SaveTemplateBody(BaseModel):
    name: str
    description: Optional[str] = None
    template: dict


class ImportTemplateBody(BaseModel):
    template: dict
    parent_node_id: str = "root"
    project_name: Optional[str] = None
