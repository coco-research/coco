"""Runtime feature gate for Core vs Studio editions."""
import os
from fastapi import HTTPException

COCO_EDITION = os.getenv("COCO_EDITION", "core").lower()

STUDIO_FEATURES = [
    "jarvis", "tts", "stt", "replay", "podcast",
    "self_improve", "analysis", "coco_orb",
]


def is_studio() -> bool:
    """Return True if running Studio edition."""
    return COCO_EDITION == "studio"


def require_studio():
    """FastAPI dependency that raises 403 if not Studio edition."""
    if not is_studio():
        raise HTTPException(
            status_code=403,
            detail="This feature requires CoCo Studio edition. Set COCO_EDITION=studio to enable.",
        )
