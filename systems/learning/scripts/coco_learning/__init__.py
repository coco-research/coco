"""Coco Learning System — instinct-based continuous learning from session observations."""

from .models import Instinct, Observation
from .storage import (
    save_instinct,
    load_instinct,
    list_instincts,
    delete_instinct,
    append_observation,
    ensure_dirs,
    get_project_dir,
    get_global_dir,
)

__all__ = [
    "Instinct",
    "Observation",
    "save_instinct",
    "load_instinct",
    "list_instincts",
    "delete_instinct",
    "append_observation",
    "ensure_dirs",
    "get_project_dir",
    "get_global_dir",
]
