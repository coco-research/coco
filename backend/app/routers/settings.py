from fastapi import APIRouter, HTTPException
from app.config import CONFIG_JSON_PATH
from app.services.json_store import read_json, write_json
from app.models.settings import UpdateSettingsBody

router = APIRouter(tags=["Settings"])


@router.get("/api/settings")
def get_settings():
    return read_json(CONFIG_JSON_PATH)


@router.patch("/api/settings")
def update_settings(body: UpdateSettingsBody):
    try:
        current = read_json(CONFIG_JSON_PATH)
        patch = body.model_dump(exclude_unset=True)
        # Handle extra dict as top-level merge
        extra = patch.pop("extra", None)
        if extra:
            patch.update(extra)
        _deep_merge(current, patch)
        write_json(CONFIG_JSON_PATH, current)
        return current
    except Exception as e:
        raise HTTPException(500, f"Failed to update settings: {e}")


def _deep_merge(base: dict, patch: dict) -> dict:
    """Recursively merge patch into base. Dicts are merged, all else is replaced."""
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
