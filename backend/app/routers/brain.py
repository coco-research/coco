from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import BRAIN_JSON_PATH, QUEUE_JSON_PATH, CONFIG_JSON_PATH
from app.services.json_store import read_json, write_json
from app.models.brain import UpdatePersonBody


# ---------------------------------------------------------------------------
# Queue item models
# ---------------------------------------------------------------------------

class QueueItemCreate(BaseModel):
    """Body for POST /api/queue — add a new item."""
    type: str = "unknown"
    priority: int = 2
    summary: str
    project: str | None = None
    person: str | None = None
    source_id: str | None = None

class QueueItemPatch(BaseModel):
    """Body for PATCH /api/queue/{index} — update an existing item."""
    status: str | None = None
    priority: int | None = None
    summary: str | None = None
    deferred_count: int | None = None

class QueueFromAgent(BaseModel):
    """Body for POST /api/queue/from-agent."""
    agent_id: str
    items: list[dict[str, Any]]  # list of partial queue items extracted by agent

class QueueFromImprovement(BaseModel):
    """Body for POST /api/queue/from-improvement."""
    improvement_id: str
    summary: str
    project: str | None = None

router = APIRouter(tags=["Brain"])

@router.get("/api/brain")
def get_brain():
    return read_json(BRAIN_JSON_PATH)

@router.get("/api/brain/people")
def get_people():
    brain = read_json(BRAIN_JSON_PATH)
    return brain.get("people", {})

@router.get("/api/brain/people/{slug}")
def get_person(slug: str):
    brain = read_json(BRAIN_JSON_PATH)
    people = brain.get("people", {})
    if slug not in people:
        raise HTTPException(404, "Person not found")
    return people[slug]


@router.patch("/api/brain/people/{slug}")
def update_person(slug: str, body: UpdatePersonBody):
    """Update a person in brain.json using atomic write."""
    brain = read_json(BRAIN_JSON_PATH)
    people = brain.get("people", {})
    if slug not in people:
        raise HTTPException(404, "Person not found")
    people[slug].update(body.model_dump(exclude_unset=True))
    brain["people"] = people
    write_json(BRAIN_JSON_PATH, brain)
    return people[slug]


@router.delete("/api/brain/people/{slug}", status_code=204)
def delete_person(slug: str):
    """Delete a person from brain.json using atomic write."""
    brain = read_json(BRAIN_JSON_PATH)
    people = brain.get("people", {})
    if slug not in people:
        raise HTTPException(404, "Person not found")
    del people[slug]
    brain["people"] = people
    write_json(BRAIN_JSON_PATH, brain)


@router.get("/api/brain/rules")
def get_rules():
    brain = read_json(BRAIN_JSON_PATH)
    return brain.get("attention_rules", [])

@router.get("/api/queue")
def get_queue():
    data = read_json(QUEUE_JSON_PATH)
    # queue.json may be a dict with an "items" key, or a raw list
    if isinstance(data, dict):
        items = data.get("items", [])
    elif isinstance(data, list):
        items = data
    else:
        items = []
    # Ensure each item has expected fields with defaults
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append({
            "id": item.get("id", ""),
            "priority": item.get("priority", "medium"),
            "type": item.get("type", "unknown"),
            "summary": item.get("summary", ""),
            "project": item.get("project"),
            "source": item.get("source"),
            "created_at": item.get("created_at"),
            "status": item.get("status", "pending"),
        })
    deferred = data.get("deferred", []) if isinstance(data, dict) else []
    auto_handled = data.get("auto_handled_since_last_session", []) if isinstance(data, dict) else []
    return {"items": normalized, "deferred": deferred, "auto_handled_since_last_session": auto_handled}

# ---------------------------------------------------------------------------
# Queue helpers
# ---------------------------------------------------------------------------

def _read_queue() -> dict:
    """Read queue.json and normalise to dict with 'items' list."""
    data = read_json(QUEUE_JSON_PATH)
    if isinstance(data, list):
        return {"version": 1, "items": data, "deferred": [], "auto_handled_since_last_session": []}
    if not isinstance(data, dict):
        return {"version": 1, "items": [], "deferred": [], "auto_handled_since_last_session": []}
    data.setdefault("items", [])
    data.setdefault("deferred", [])
    data.setdefault("auto_handled_since_last_session", [])
    return data


def _next_queue_id() -> str:
    """Generate a short queue id."""
    import secrets
    return f"q-{secrets.token_hex(4)}"


# ---------------------------------------------------------------------------
# Queue CRUD
# ---------------------------------------------------------------------------

@router.post("/api/queue", status_code=201)
def add_queue_item(body: QueueItemCreate):
    """Add a new item to queue.json."""
    q = _read_queue()
    item = {
        "id": _next_queue_id(),
        "type": body.type,
        "priority": body.priority,
        "summary": body.summary,
        "project": body.project,
        "person": body.person,
        "source_id": body.source_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deferred_count": 0,
        "status": "pending",
    }
    q["items"].append(item)
    q["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_json(QUEUE_JSON_PATH, q)
    return item


@router.patch("/api/queue/{index}")
def update_queue_item(index: int, body: QueueItemPatch):
    """Update a queue item by its list index."""
    q = _read_queue()
    if index < 0 or index >= len(q["items"]):
        raise HTTPException(404, f"Queue index {index} out of range (0..{len(q['items'])-1})")
    updates = body.model_dump(exclude_unset=True)
    q["items"][index].update(updates)
    q["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_json(QUEUE_JSON_PATH, q)
    return q["items"][index]


@router.delete("/api/queue/{index}", status_code=204)
def delete_queue_item(index: int):
    """Remove a queue item by its list index."""
    q = _read_queue()
    if index < 0 or index >= len(q["items"]):
        raise HTTPException(404, f"Queue index {index} out of range (0..{len(q['items'])-1})")
    q["items"].pop(index)
    q["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_json(QUEUE_JSON_PATH, q)


@router.post("/api/queue/from-agent", status_code=201)
def queue_from_agent(body: QueueFromAgent):
    """Accept items extracted by an agent and add them to the decision queue."""
    q = _read_queue()
    created = []
    now = datetime.now(timezone.utc).isoformat()
    for raw in body.items:
        item = {
            "id": _next_queue_id(),
            "type": raw.get("type", "agent_decision"),
            "priority": raw.get("priority", 2),
            "summary": raw.get("summary", "Agent-generated item"),
            "project": raw.get("project"),
            "person": raw.get("person"),
            "source_id": body.agent_id,
            "created_at": now,
            "deferred_count": 0,
            "status": "pending",
        }
        q["items"].append(item)
        created.append(item)
    q["last_updated"] = now
    write_json(QUEUE_JSON_PATH, q)
    return {"added": len(created), "items": created}


@router.post("/api/queue/from-improvement", status_code=201)
def queue_from_improvement(body: QueueFromImprovement):
    """Create a queue item for an improvement that needs human approval."""
    q = _read_queue()
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "id": _next_queue_id(),
        "type": "improvement_approval",
        "priority": 1,
        "summary": body.summary,
        "project": body.project,
        "person": None,
        "source_id": body.improvement_id,
        "created_at": now,
        "deferred_count": 0,
        "status": "pending",
    }
    q["items"].append(item)
    q["last_updated"] = now
    write_json(QUEUE_JSON_PATH, q)
    return item


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@router.get("/api/config")
def get_config():
    return read_json(CONFIG_JSON_PATH)
