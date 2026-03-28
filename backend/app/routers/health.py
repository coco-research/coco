from fastapi import APIRouter
import time
from app.config import HUB_DB_PATH, PLATFORM_DB_PATH, BRAIN_JSON_PATH, QUEUE_JSON_PATH

router = APIRouter(tags=["System"])
_start_time = time.time()

@router.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "uptime_seconds": int(time.time() - _start_time),
        "databases": {
            "hub_db": {"exists": HUB_DB_PATH.exists()},
            "platform_db": {"exists": PLATFORM_DB_PATH.exists()},
        },
        "files": {
            "brain_json": {"exists": BRAIN_JSON_PATH.exists()},
            "queue_json": {"exists": QUEUE_JSON_PATH.exists()},
        },
    }
