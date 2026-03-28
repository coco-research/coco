from fastapi import APIRouter, HTTPException
from app.config import BRAIN_JSON_PATH, QUEUE_JSON_PATH, CONFIG_JSON_PATH
from app.services.json_store import read_json, write_json
from app.models.brain import UpdatePersonBody

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

@router.get("/api/config")
def get_config():
    return read_json(CONFIG_JSON_PATH)
