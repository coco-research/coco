import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import Engine, create_engine, func, or_, select
from sqlalchemy.engine import Connection

from app.config import BRAIN_JSON_PATH, QUEUE_JSON_PATH, CONFIG_JSON_PATH, BRAIN_DB_PATH
from app.db.tables import brain_decisions, brain_events, brain_tasks, brain_entities
from app.services.json_store import read_json, write_json
from app.models.brain import UpdatePersonBody

log = logging.getLogger(__name__)


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

def _is_likely_person(name: str) -> bool:
    """Filter out entity extraction noise — concepts misclassified as people.

    Root cause: brain entity_extractor.py regex matches any two capitalized words
    (e.g., "Data Flow", "Access Control") as person names. This filter catches the
    most obvious non-people at the API level until the extractor is fixed upstream.
    """
    if not name or len(name) < 3:
        return False
    # Reject names with newlines/tabs (document parsing artifacts)
    if "\n" in name or "\t" in name:
        return False
    words = name.split()
    # Real names are 2-4 words
    if len(words) < 2 or len(words) > 4:
        return False
    # Reject if any word is a common business/tech term
    _NON_PERSON_WORDS = {
        "control", "controls", "access", "policy", "policies", "system", "systems",
        "management", "process", "processes", "workflow", "workflows", "module",
        "modules", "action", "actions", "status", "review", "reviews", "compliance",
        "risk", "risks", "audit", "security", "report", "reports", "analytics",
        "criteria", "phase", "phases", "project", "projects", "board", "service",
        "services", "data", "additional", "active", "general", "internal", "external",
        "framework", "model", "models", "assessment", "testing", "inventory",
        "portal", "dashboard", "integration", "configuration", "requirements",
        "summary", "overview", "analysis", "automation", "monitoring", "tracking",
        "authentication", "authorization", "submission", "corporate", "regulatory",
        "initiatives", "metrics", "roadmap", "feed", "score", "high", "low",
        "medium", "critical", "sync", "export", "import", "login", "view",
        "records", "proposed", "automated", "sharing", "launch", "build",
        "reasoning", "context", "vision", "agenda", "product", "diagrams",
        "flow", "state", "future", "current", "initial", "final",
    }
    if any(w.lower() in _NON_PERSON_WORDS for w in words):
        return False
    # Reject 2-letter words that aren't initials (Ad, On, Or, If, etc.)
    if any(len(w) == 2 and w[1].islower() for w in words):
        return False
    # Reject if first word is a common verb (Add, Enter, View, Run, etc.)
    _VERB_STARTS = {"add", "added", "adding", "enter", "use", "run", "get", "set",
                    "check", "open", "close", "start", "stop", "update", "delete",
                    "create", "remove", "enable", "disable", "configure", "deploy",
                    "phased", "proposed", "planned", "revised", "shared"}
    if words[0].lower() in _VERB_STARTS:
        return False
    return True


@router.get("/api/brain/people")
def get_people():
    brain = read_json(BRAIN_JSON_PATH)
    people = brain.get("people", {})
    # Two-pass filter: (1) structural check, (2) require email evidence
    # Email evidence = the person appeared as a sender in at least one email
    # This is the strongest signal that someone is a real person, not a document fragment
    return {
        slug: p for slug, p in people.items()
        if _is_likely_person(p.get("full_name", ""))
        and (
            p.get("patterns", {}).get("email_from")  # has sent emails
            or p.get("source") == "manual"            # manually added
            or slug == "rijul"                         # self
        )
    }

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
    try:
        from app.services import audit as _audit
        _audit.record(_audit.ACTION_BRAIN_DELETE, actor="user", payload={"slug": slug})
    except Exception:
        pass


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
            "human_id": item.get("human_id"),
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
    return f"q-{secrets.token_hex(4)}"


# ---------------------------------------------------------------------------
# Queue CRUD
# ---------------------------------------------------------------------------

@router.post("/api/queue", status_code=201)
def add_queue_item(body: QueueItemCreate):
    """Add a new item to queue.json."""
    q = _read_queue()
    item_id = _next_queue_id()

    # Mint a human_id (e.g. CXR-47). Falls back to None if id_sequences is
    # unreachable — never block queue inserts on this.
    human_id: str | None = None
    try:
        from app.services.id_generator import assign_display_id
        # Decisions have no per-node bucket; pass project so a matching node
        # prefix is reused when one exists, otherwise the global "CXR" bucket.
        node_id = _resolve_node_for_project(body.project) if body.project else None
        human_id = assign_display_id(item_id, node_id, entity_type="decision")
    except Exception as e:
        log.warning("queue_human_id_assign_failed: %s", e)

    item = {
        "id": item_id,
        "human_id": human_id,
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


def _resolve_node_for_project(project: str | None) -> str | None:
    """Best-effort lookup of a node_id for a given project label/id."""
    if not project:
        return None
    try:
        from app.db.session import get_db
        with get_db() as conn:
            row = conn.exec_driver_sql(
                "SELECT id FROM nodes WHERE id = ? OR label = ? LIMIT 1",
                (project, project),
            ).fetchone()
            return row[0] if row else None
    except Exception:
        return None


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
    removed = q["items"].pop(index)
    q["last_updated"] = datetime.now(timezone.utc).isoformat()
    write_json(QUEUE_JSON_PATH, q)
    try:
        from app.services import audit as _audit
        _audit.record(
            _audit.ACTION_QUEUE_DISMISS,
            actor="user",
            payload={"index": index, "item_id": (removed or {}).get("id")},
        )
    except Exception:
        pass


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


# ---------------------------------------------------------------------------
# Brain DB endpoints (project_brain.db — read-only SA Core engine)
# ---------------------------------------------------------------------------

_brain_engine: Engine | None = None


def _get_brain_engine() -> Engine | None:
    """Return a memoized read-only SA engine for project_brain.db.

    Returns None if the brain DB file does not exist, so callers can short-
    circuit to empty results without touching the disk on every request.
    """
    global _brain_engine
    if not BRAIN_DB_PATH.exists():
        return None
    if _brain_engine is None:
        # SQLite read-only via URI. The SA URL form uses the `uri=true` query
        # param to pass through to sqlite3's connect(uri=True).
        url = f"sqlite:///file:{BRAIN_DB_PATH}?mode=ro&uri=true"
        _brain_engine = create_engine(url, connect_args={"timeout": 5})
    return _brain_engine


def _brain_db_conn() -> Connection | None:
    """Open a read-only SA Connection to project_brain.db.

    Returns None if the file does not exist so callers can return empty results.
    """
    eng = _get_brain_engine()
    if eng is None:
        return None
    return eng.connect()


def _rows_to_dicts(rows) -> list[dict]:
    """Convert SA Row objects to plain dicts, parsing JSON columns."""
    results = []
    for row in rows:
        d = dict(row._mapping)
        # Parse known JSON columns if present
        for json_col in ("participants_json", "metadata_json"):
            if json_col in d and isinstance(d[json_col], str):
                try:
                    d[json_col] = json.loads(d[json_col])
                except (json.JSONDecodeError, TypeError):
                    pass
        results.append(d)
    return results


@router.get("/api/brain/decisions")
def get_brain_decisions(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: str = Query("", max_length=200),
):
    """List decisions from project_brain.db with optional text search."""
    conn = _brain_db_conn()
    if conn is None:
        return {"items": [], "total": 0}
    try:
        base_where = brain_decisions.c.project_id == 1
        if search.strip():
            pattern = f"%{search.strip()}%"
            search_clause = or_(
                brain_decisions.c.decision.like(pattern),
                brain_decisions.c.context.like(pattern),
                brain_decisions.c.decided_by.like(pattern),
            )
            where_clause = base_where & search_clause
        else:
            where_clause = base_where

        total = conn.execute(
            select(func.count()).select_from(brain_decisions).where(where_clause)
        ).scalar() or 0
        rows = conn.execute(
            select(brain_decisions)
            .where(where_clause)
            .order_by(brain_decisions.c.date.desc())
            .limit(limit)
            .offset(offset)
        ).fetchall()
        return {"items": _rows_to_dicts(rows), "total": total}
    except Exception:
        log.exception("brain_decisions_error")
        raise HTTPException(500, "Failed to read decisions from brain database")
    finally:
        conn.close()


@router.get("/api/brain/events")
def get_brain_events(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    type: str = Query("", max_length=50, alias="type"),
):
    """List events from project_brain.db with optional type filter."""
    conn = _brain_db_conn()
    if conn is None:
        return {"items": [], "total": 0}
    try:
        base_where = brain_events.c.project_id == 1
        if type.strip():
            where_clause = base_where & (brain_events.c.type == type.strip())
        else:
            where_clause = base_where

        total = conn.execute(
            select(func.count()).select_from(brain_events).where(where_clause)
        ).scalar() or 0
        rows = conn.execute(
            select(brain_events)
            .where(where_clause)
            .order_by(brain_events.c.date.desc())
            .limit(limit)
            .offset(offset)
        ).fetchall()
        return {"items": _rows_to_dicts(rows), "total": total}
    except Exception:
        log.exception("brain_events_error")
        raise HTTPException(500, "Failed to read events from brain database")
    finally:
        conn.close()


@router.get("/api/brain/tasks")
def get_brain_tasks(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str = Query("", max_length=50),
):
    """List tasks from project_brain.db with optional status filter."""
    conn = _brain_db_conn()
    if conn is None:
        return {"items": [], "total": 0, "by_status": {}}
    try:
        # Status breakdown
        status_rows = conn.execute(
            select(brain_tasks.c.status, func.count().label("cnt"))
            .where(brain_tasks.c.project_id == 1)
            .group_by(brain_tasks.c.status)
        ).fetchall()
        by_status = {r._mapping["status"]: r._mapping["cnt"] for r in status_rows}

        base_where = brain_tasks.c.project_id == 1
        if status.strip():
            where_clause = base_where & (brain_tasks.c.status == status.strip())
        else:
            where_clause = base_where

        total = conn.execute(
            select(func.count()).select_from(brain_tasks).where(where_clause)
        ).scalar() or 0
        rows = conn.execute(
            select(brain_tasks)
            .where(where_clause)
            .order_by(
                brain_tasks.c.priority,
                brain_tasks.c.status,
                brain_tasks.c.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        ).fetchall()
        return {"items": _rows_to_dicts(rows), "total": total, "by_status": by_status}
    except Exception:
        log.exception("brain_tasks_error")
        raise HTTPException(500, "Failed to read tasks from brain database")
    finally:
        conn.close()


@router.get("/api/brain/stats")
def get_brain_stats():
    """Aggregate counts from project_brain.db."""
    conn = _brain_db_conn()
    if conn is None:
        return {
            "available": False,
            "entities": 0,
            "decisions": 0,
            "events": 0,
            "tasks": {"total": 0, "open": 0, "done": 0},
        }
    try:
        entities = conn.execute(
            select(func.count())
            .select_from(brain_entities)
            .where(brain_entities.c.project_id == 1)
        ).scalar() or 0
        decisions = conn.execute(
            select(func.count())
            .select_from(brain_decisions)
            .where(brain_decisions.c.project_id == 1)
        ).scalar() or 0
        events_count = conn.execute(
            select(func.count())
            .select_from(brain_events)
            .where(brain_events.c.project_id == 1)
        ).scalar() or 0
        task_total = conn.execute(
            select(func.count())
            .select_from(brain_tasks)
            .where(brain_tasks.c.project_id == 1)
        ).scalar() or 0
        status_rows = conn.execute(
            select(brain_tasks.c.status, func.count().label("cnt"))
            .where(brain_tasks.c.project_id == 1)
            .group_by(brain_tasks.c.status)
        ).fetchall()
        task_by_status = {r._mapping["status"]: r._mapping["cnt"] for r in status_rows}

        return {
            "available": True,
            "entities": entities,
            "decisions": decisions,
            "events": events_count,
            "tasks": {
                "total": task_total,
                **task_by_status,
            },
        }
    except Exception:
        log.exception("brain_stats_error")
        raise HTTPException(500, "Failed to read stats from brain database")
    finally:
        conn.close()
