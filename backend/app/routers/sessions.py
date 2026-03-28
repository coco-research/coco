import json
from fastapi import APIRouter, HTTPException, Query
from app.config import SESSIONS_DIR

router = APIRouter(tags=["Sessions"])


@router.get("/api/sessions")
def list_sessions(limit: int = Query(20, ge=1, le=100)):
    if not SESSIONS_DIR.exists():
        return []

    sessions = []
    for f in SESSIONS_DIR.iterdir():
        if not f.suffix == ".json":
            continue
        try:
            with open(f) as fh:
                data = json.load(fh)
            # Normalize to expected fields
            session = {
                "_filename": f.name,
                "started_at": data.get("started_at"),
                "ended_at": data.get("ended_at"),
                "launch_type": data.get("launch_type", data.get("type", "manual")),
                "focus_project": data.get("focus_project", data.get("project")),
                "commands_used": data.get("commands_used", data.get("commands", [])),
            }
            # Preserve any extra fields
            for k, v in data.items():
                if k not in session:
                    session[k] = v
            sessions.append(session)
        except Exception:
            continue

    # Sort by started_at descending
    sessions.sort(key=lambda s: s.get("started_at") or "", reverse=True)
    return sessions[:limit]


@router.get("/api/sessions/{filename}")
def get_session(filename: str):
    # Sanitize: only allow .json files, no path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(400, "Invalid filename")
    if not filename.endswith(".json"):
        filename += ".json"

    path = SESSIONS_DIR / filename
    if not path.exists():
        raise HTTPException(404, "Session not found")

    try:
        with open(path) as f:
            data = json.load(f)
        data["_filename"] = filename
        return data
    except Exception as e:
        raise HTTPException(500, f"Failed to read session: {e}")
