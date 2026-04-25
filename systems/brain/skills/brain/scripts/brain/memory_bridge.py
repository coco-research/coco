"""
Memory Bridge — syncs brain DB writes to MemPalace (ChromaDB) and brain.json.

Called AFTER brain DB writes complete. All functions are best-effort:
if MemPalace or brain.json is unavailable, a warning is logged and execution
continues so the primary brain DB write path is never broken.
"""

import hashlib
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MEMPALACE_PATH = os.path.expanduser("~/.mempalace/palace")
BRAIN_JSON_PATH = os.path.expanduser("~/.coco/brain.json")
COLLECTION_NAME = "mempalace_drawers"
def _find_mempalace_site_packages() -> str:
    """Find the mempalace venv site-packages, regardless of Python minor version."""
    base = os.path.expanduser("~/.coco/mempalace-env/lib")
    if os.path.isdir(base):
        for entry in sorted(os.listdir(base), reverse=True):
            candidate = os.path.join(base, entry, "site-packages")
            if os.path.isdir(candidate):
                return candidate
    return os.path.expanduser("~/.coco/mempalace-env/lib/python3.13/site-packages")

MEMPALACE_ENV_SITE = _find_mempalace_site_packages()

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ChromaDB access — uses mempalace venv Python via subprocess
# (System Python may be a different version than the mempalace venv)
# ---------------------------------------------------------------------------

import subprocess

MEMPALACE_PYTHON = os.path.expanduser("~/.coco/mempalace-env/bin/python3")


def _chromadb_available() -> bool:
    """Check if we can reach ChromaDB via the mempalace venv Python."""
    if not os.path.isfile(MEMPALACE_PYTHON):
        return False
    try:
        result = subprocess.run(
            [MEMPALACE_PYTHON, "-c", "import chromadb; print('ok')"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip() == "ok"
    except Exception:
        return False


def _run_chromadb_op(script: str) -> dict | None:
    """Run a Python script in the mempalace venv and parse JSON output."""
    try:
        result = subprocess.run(
            [MEMPALACE_PYTHON, "-c", script],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            log.warning("memory_bridge: chromadb op failed — %s", result.stderr[:200])
            return None
        return json.loads(result.stdout)
    except Exception as exc:
        log.warning("memory_bridge: chromadb subprocess error — %s", exc)
        return None


def _upsert_drawer_via_subprocess(text: str, wing: str, room: str) -> str | None:
    """Write one drawer to ChromaDB via subprocess. Returns drawer_id on success."""
    drawer_id = _drawer_id(wing, room, text)
    timestamp = _now_iso()
    # Escape text for safe embedding in Python string
    escaped_text = json.dumps(text)
    escaped_meta = json.dumps({
        "wing": wing, "room": room,
        "source_file": "brain-sync", "filed_at": timestamp,
    })
    script = f"""
import json, chromadb
client = chromadb.PersistentClient(path={json.dumps(MEMPALACE_PATH)})
col = client.get_collection({json.dumps(COLLECTION_NAME)})
col.upsert(
    ids=[{json.dumps(drawer_id)}],
    documents=[{escaped_text}],
    metadatas=[json.loads({json.dumps(escaped_meta)})],
)
print(json.dumps({{"id": {json.dumps(drawer_id)}, "status": "ok"}}))
"""
    result = _run_chromadb_op(script)
    if result and result.get("status") == "ok":
        return result.get("id")
    return None


def _batch_upsert_drawers(items: list[dict]) -> int:
    """
    Upsert multiple drawers to ChromaDB in a single subprocess call.

    Each item must have keys: "id", "text", "wing", "room".

    Spawns ONE Python process that opens the ChromaDB collection and calls
    col.upsert() once for all items. Returns the count of successfully
    upserted items (0 on any failure).
    """
    if not items:
        return 0

    timestamp = _now_iso()

    # Build parallel lists for the batch upsert
    ids = []
    documents = []
    metadatas = []
    for item in items:
        ids.append(item["id"])
        documents.append(item["text"])
        metadatas.append({
            "wing": item["wing"],
            "room": item["room"],
            "source_file": "brain-sync",
            "filed_at": timestamp,
        })

    # Serialize as JSON so the subprocess script never has raw strings embedded
    ids_json = json.dumps(ids)
    documents_json = json.dumps(documents)
    metadatas_json = json.dumps(metadatas)
    count = len(ids)

    script = f"""
import json, chromadb
client = chromadb.PersistentClient(path={json.dumps(MEMPALACE_PATH)})
col = client.get_collection({json.dumps(COLLECTION_NAME)})
ids = json.loads({json.dumps(ids_json)})
documents = json.loads({json.dumps(documents_json)})
metadatas = json.loads({json.dumps(metadatas_json)})
col.upsert(ids=ids, documents=documents, metadatas=metadatas)
print(json.dumps({{"upserted": len(ids), "status": "ok"}}))
"""
    try:
        result = subprocess.run(
            [MEMPALACE_PYTHON, "-c", script],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            log.warning(
                "memory_bridge: batch upsert failed — %s", result.stderr[:200]
            )
            return 0
        data = json.loads(result.stdout)
        if data.get("status") == "ok":
            return int(data.get("upserted", 0))
        return 0
    except Exception as exc:
        log.warning("memory_bridge: batch upsert subprocess error — %s", exc)
        return 0


# Keep compatibility with existing function signatures
def _get_collection():
    """Compatibility stub — returns a sentinel if ChromaDB is reachable, None otherwise."""
    if _chromadb_available():
        return True  # sentinel — actual ops use subprocess
    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _drawer_id(wing: str, room: str, text: str) -> str:
    """Deterministic drawer ID from content hash."""
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:24]
    return f"drawer_{wing}_{room}_{text_hash}"


def _upsert_drawer(col, text: str, wing: str, room: str) -> str | None:
    """Write one drawer to ChromaDB via subprocess. Returns drawer_id on success."""
    return _upsert_drawer_via_subprocess(text, wing, room)


def _format_entity_text(entity: dict, project_slug: str) -> str:
    """Format an entity dict as a human-readable description for MemPalace."""
    meta_raw = entity.get("metadata_json", "{}")
    try:
        meta = json.loads(meta_raw) if isinstance(meta_raw, str) else (meta_raw or {})
    except (json.JSONDecodeError, TypeError):
        meta = {}

    lines = [
        f"Entity: {entity.get('name', 'Unknown')}",
        f"Type: {entity.get('type', 'unknown')}",
        f"Project: {project_slug}",
    ]
    if meta:
        for k, v in meta.items():
            lines.append(f"{k}: {v}")
    if entity.get("external_id"):
        lines.append(f"external_id: {entity['external_id']}")
    if entity.get("created_at"):
        lines.append(f"created_at: {entity['created_at']}")
    return "\n".join(lines)


def _format_decision_text(decision: dict, project_slug: str) -> str:
    """Format a decision dict as human-readable text for MemPalace."""
    lines = [
        f"Decision: {decision.get('decision', '')}",
        f"Project: {project_slug}",
        f"Date: {decision.get('date', '')}",
    ]
    if decision.get("context"):
        lines.append(f"Context: {decision['context']}")
    if decision.get("decided_by"):
        lines.append(f"Decided by: {decision['decided_by']}")
    if decision.get("impact"):
        lines.append(f"Impact: {decision['impact']}")
    return "\n".join(lines)


def _format_event_text(event: dict, project_slug: str) -> str:
    """Format an event dict as human-readable text for MemPalace."""
    lines = [
        f"Event: {event.get('title', '')}",
        f"Project: {project_slug}",
        f"Date: {event.get('date', '')}",
        f"Type: {event.get('type', '')}",
    ]
    if event.get("summary"):
        lines.append(f"Summary: {event['summary']}")
    if event.get("source"):
        lines.append(f"Source: {event['source']}")
    participants_raw = event.get("participants_json", "[]")
    try:
        participants = (
            json.loads(participants_raw)
            if isinstance(participants_raw, str)
            else (participants_raw or [])
        )
        if participants:
            lines.append(f"Participants: {', '.join(str(p) for p in participants)}")
    except (json.JSONDecodeError, TypeError):
        pass
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public sync functions
# ---------------------------------------------------------------------------

def sync_entity_to_mempalace(entity_dict: dict, project_slug: str) -> str | None:
    """
    Write a person/system/team entity as a MemPalace drawer.

    Wing  = project_slug
    Room  = entity type (e.g. "person", "system", "team")
    Text  = formatted entity description

    Returns drawer_id on success, None if MemPalace is unavailable.
    """
    col = _get_collection()
    if col is None:
        return None

    wing = project_slug or "general"
    room = entity_dict.get("type", "entity")
    text = _format_entity_text(entity_dict, project_slug)
    drawer_id = _upsert_drawer(col, text, wing, room)
    if drawer_id:
        log.debug("memory_bridge: synced entity '%s' → %s", entity_dict.get("name"), drawer_id)
    return drawer_id


def sync_decision_to_mempalace(decision_dict: dict, project_slug: str) -> str | None:
    """
    Write a decision as a MemPalace drawer.

    Wing  = project_slug
    Room  = "decisions"

    Returns drawer_id on success, None if MemPalace is unavailable.
    """
    col = _get_collection()
    if col is None:
        return None

    wing = project_slug or "general"
    room = "decisions"
    text = _format_decision_text(decision_dict, project_slug)
    drawer_id = _upsert_drawer(col, text, wing, room)
    if drawer_id:
        log.debug("memory_bridge: synced decision → %s", drawer_id)
    return drawer_id


def sync_event_to_mempalace(event_dict: dict, project_slug: str) -> str | None:
    """
    Write an event as a MemPalace drawer.

    Wing  = project_slug
    Room  = "events"

    Returns drawer_id on success, None if MemPalace is unavailable.
    """
    col = _get_collection()
    if col is None:
        return None

    wing = project_slug or "general"
    room = "events"
    text = _format_event_text(event_dict, project_slug)
    drawer_id = _upsert_drawer(col, text, wing, room)
    if drawer_id:
        log.debug("memory_bridge: synced event '%s' → %s", event_dict.get("title"), drawer_id)
    return drawer_id


def sync_brain_json(db_path: str | Path) -> bool:
    """
    Rebuild ~/.coco/brain.json people section from ALL person entities in brain DB.

    Rules:
    - Reads every project's person entities from db_path.
    - Preserves all non-people keys (version, attention_rules, preferences,
      classification_hints, owner_matching, stats).
    - Merges: entries with "source": "taught" in the existing brain.json are
      preserved as-is (they may have richer transcription_aliases etc.).
      Brain DB entries fill in or create entries that don't already have
      "source": "taught".
    - Updates stats.last_sync to now.

    Returns True on success, False on failure.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        log.warning("memory_bridge: brain DB not found at %s", db_path)
        return False

    # Load existing brain.json (or start from scratch)
    brain_json_path = Path(BRAIN_JSON_PATH)
    existing: dict = {}
    if brain_json_path.exists():
        try:
            with open(brain_json_path, "r") as f:
                existing = json.load(f)
        except Exception as exc:
            log.warning("memory_bridge: could not read brain.json — %s", exc)
            existing = {}

    # Extract the "taught" entries — these must be preserved verbatim
    taught_people: dict[str, dict] = {}
    for key, person in existing.get("people", {}).items():
        if person.get("source") == "taught":
            taught_people[key] = person

    # Query brain DB: all person entities across all projects
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")

        rows = conn.execute(
            "SELECT e.*, p.slug AS project_slug "
            "FROM entities e "
            "JOIN projects p ON e.project_id = p.id "
            "WHERE e.type = 'person' "
            "ORDER BY e.name"
        ).fetchall()
        conn.close()
    except Exception as exc:
        log.warning("memory_bridge: failed to query brain DB for people — %s", exc)
        return False

    # Group entities by name (key = lowercase first word or full name)
    # Multiple projects may have the same person — merge their project lists
    from_db: dict[str, dict] = {}
    for row in rows:
        d = dict(row)
        name: str = d.get("name", "Unknown")
        key = name.lower().split()[0] if name else "unknown"

        meta_raw = d.get("metadata_json", "{}")
        try:
            meta = json.loads(meta_raw) if isinstance(meta_raw, str) else (meta_raw or {})
        except (json.JSONDecodeError, TypeError):
            meta = {}

        project_slug: str = d.get("project_slug", "")

        if key not in from_db:
            email = meta.get("email", "")
            from_db[key] = {
                "full_name": name,
                "role": meta.get("role", d.get("type", "person")),
                "priority": "medium",
                "projects": [project_slug] if project_slug else [],
                "patterns": {
                    "email_from": [email] if email else [],
                    "frequency": "unknown",
                    "typical_topics": [],
                },
                "learned_at": (d.get("created_at", "") or "")[:10],
                "source": "brain-sync",
            }
        else:
            # Merge project into existing entry
            if project_slug and project_slug not in from_db[key]["projects"]:
                from_db[key]["projects"].append(project_slug)

    # Build merged people dict: taught entries take precedence
    merged_people: dict[str, dict] = {}

    # Start with all DB-derived entries
    for key, entry in from_db.items():
        if key in taught_people:
            # Taught entry wins; but we can enrich projects list
            taught = dict(taught_people[key])
            for proj in entry.get("projects", []):
                if proj and proj not in taught.get("projects", []):
                    taught.setdefault("projects", []).append(proj)
            merged_people[key] = taught
        else:
            merged_people[key] = entry

    # Also keep all taught entries that weren't in brain DB at all
    for key, taught in taught_people.items():
        if key not in merged_people:
            merged_people[key] = taught

    # Assemble new brain.json preserving all non-people keys
    new_brain_json: dict = {
        "version": existing.get("version", 1),
        "people": merged_people,
        "attention_rules": existing.get("attention_rules", []),
        "preferences": existing.get("preferences", {}),
        "classification_hints": existing.get("classification_hints", {}),
        "owner_matching": existing.get("owner_matching", {}),
        "stats": {
            **existing.get("stats", {}),
            "last_sync": _now_iso(),
        },
    }

    # Write atomically via a temp file + rename
    try:
        tmp_path = brain_json_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(new_brain_json, f, indent=2)
        tmp_path.replace(brain_json_path)
        log.debug(
            "memory_bridge: brain.json rebuilt — %d people (%d taught, %d from DB)",
            len(merged_people),
            len(taught_people),
            len(from_db),
        )
        return True
    except Exception as exc:
        log.warning("memory_bridge: failed to write brain.json — %s", exc)
        return False


def full_sync(db_path: str | Path, project_slug: str) -> dict:
    """
    Run a full sync for one project:
      1. Sync all person/system/team entities to MemPalace.
      2. Sync all decisions to MemPalace.
      3. Sync all events to MemPalace.
      4. Rebuild brain.json from ALL projects in the brain DB.

    Called at the end of /brain-update.

    Returns a summary dict with counts and status.
    """
    db_path = Path(db_path)
    summary = {
        "project_slug": project_slug,
        "db_path": str(db_path),
        "entities_synced": 0,
        "decisions_synced": 0,
        "events_synced": 0,
        "brain_json_rebuilt": False,
        "errors": [],
    }

    if not db_path.exists():
        summary["errors"].append(f"brain DB not found at {db_path}")
        return summary

    # Open DB
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception as exc:
        summary["errors"].append(f"cannot open brain DB: {exc}")
        return summary

    try:
        # Resolve project_id
        proj_row = conn.execute(
            "SELECT * FROM projects WHERE slug = ?", (project_slug,)
        ).fetchone()
        if not proj_row:
            summary["errors"].append(f"project '{project_slug}' not found in brain DB")
            conn.close()
            # Still rebuild brain.json even if project not found
            summary["brain_json_rebuilt"] = sync_brain_json(db_path)
            return summary

        project_id = proj_row["id"]

        # --- Batch sync: entities + decisions + events in ONE subprocess call ---
        if not _chromadb_available():
            summary["errors"].append("MemPalace collection unavailable — entity/decision/event sync skipped")
        else:
            wing = project_slug or "general"
            batch_items: list[dict] = []

            # Collect entities
            entity_rows = conn.execute(
                "SELECT * FROM entities WHERE project_id = ?", (project_id,)
            ).fetchall()
            entity_dicts = [dict(row) for row in entity_rows]
            for d in entity_dicts:
                text = _format_entity_text(d, project_slug)
                room = d.get("type", "entity")
                batch_items.append({
                    "id": _drawer_id(wing, room, text),
                    "text": text,
                    "wing": wing,
                    "room": room,
                })

            # Collect decisions
            decision_rows = conn.execute(
                "SELECT * FROM decisions WHERE project_id = ?", (project_id,)
            ).fetchall()
            decision_dicts = [dict(row) for row in decision_rows]
            for d in decision_dicts:
                text = _format_decision_text(d, project_slug)
                batch_items.append({
                    "id": _drawer_id(wing, "decisions", text),
                    "text": text,
                    "wing": wing,
                    "room": "decisions",
                })

            # Collect events
            event_rows = conn.execute(
                "SELECT * FROM events WHERE project_id = ?", (project_id,)
            ).fetchall()
            event_dicts = [dict(row) for row in event_rows]
            for d in event_dicts:
                text = _format_event_text(d, project_slug)
                batch_items.append({
                    "id": _drawer_id(wing, "events", text),
                    "text": text,
                    "wing": wing,
                    "room": "events",
                })

            # Single subprocess call for all items
            total_upserted = _batch_upsert_drawers(batch_items)

            if total_upserted == 0 and batch_items:
                summary["errors"].append(
                    f"batch upsert returned 0 — {len(batch_items)} items may not have synced"
                )
            else:
                # Distribute upserted count across the three categories
                n_entities = len(entity_dicts)
                n_decisions = len(decision_dicts)
                n_events = len(event_dicts)
                # total_upserted == len(batch_items) on full success; distribute proportionally
                if total_upserted >= len(batch_items):
                    summary["entities_synced"] = n_entities
                    summary["decisions_synced"] = n_decisions
                    summary["events_synced"] = n_events
                else:
                    # Partial success — attribute what we know
                    summary["entities_synced"] = min(n_entities, total_upserted)
                    remaining = max(0, total_upserted - n_entities)
                    summary["decisions_synced"] = min(n_decisions, remaining)
                    remaining = max(0, remaining - n_decisions)
                    summary["events_synced"] = min(n_events, remaining)

            log.debug(
                "memory_bridge: batch upserted %d items (entities=%d, decisions=%d, events=%d)",
                total_upserted,
                summary["entities_synced"],
                summary["decisions_synced"],
                summary["events_synced"],
            )

    except Exception as exc:
        summary["errors"].append(f"unexpected error during sync: {exc}")
        log.warning("memory_bridge: full_sync error — %s", exc)
    finally:
        try:
            conn.close()
        except Exception:
            pass

    # Rebuild brain.json (independent of MemPalace availability)
    summary["brain_json_rebuilt"] = sync_brain_json(db_path)

    return summary


# ---------------------------------------------------------------------------
# Drift detection & health check
# ---------------------------------------------------------------------------

def verify_sync(db_path: Path, project_slug: str) -> dict:
    """
    Check that brain DB entities/decisions/events have corresponding MemPalace drawers.

    Algorithm:
    1. Query brain DB for all entities, decisions, events for the project.
    2. For each, compute the expected drawer_id using _drawer_id(wing, room, formatted_text).
    3. Query MemPalace for all drawer IDs in the project wing (ONE subprocess call).
    4. Compare expected vs actual sets.

    Returns:
        {
            "ok": bool,
            "expected": int,
            "actual": int,
            "missing": int,
            "extra": int,
            "missing_ids": [... first 5 ...],
        }
    """
    db_path = Path(db_path)
    result = {
        "ok": False,
        "expected": 0,
        "actual": 0,
        "missing": 0,
        "extra": 0,
        "missing_ids": [],
    }

    if not db_path.exists():
        log.warning("verify_sync: brain DB not found at %s", db_path)
        return result

    # --- Step 1 & 2: build expected drawer ID set from brain DB ---
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")

        proj_row = conn.execute(
            "SELECT * FROM projects WHERE slug = ?", (project_slug,)
        ).fetchone()
        if not proj_row:
            log.warning("verify_sync: project '%s' not found in brain DB", project_slug)
            conn.close()
            return result

        project_id = proj_row["id"]
        wing = project_slug or "general"
        expected_ids: set[str] = set()

        # Entities
        entity_rows = conn.execute(
            "SELECT * FROM entities WHERE project_id = ?", (project_id,)
        ).fetchall()
        for row in entity_rows:
            d = dict(row)
            text = _format_entity_text(d, project_slug)
            room = d.get("type", "entity")
            expected_ids.add(_drawer_id(wing, room, text))

        # Decisions
        decision_rows = conn.execute(
            "SELECT * FROM decisions WHERE project_id = ?", (project_id,)
        ).fetchall()
        for row in decision_rows:
            d = dict(row)
            text = _format_decision_text(d, project_slug)
            expected_ids.add(_drawer_id(wing, "decisions", text))

        # Events
        event_rows = conn.execute(
            "SELECT * FROM events WHERE project_id = ?", (project_id,)
        ).fetchall()
        for row in event_rows:
            d = dict(row)
            text = _format_event_text(d, project_slug)
            expected_ids.add(_drawer_id(wing, "events", text))

        conn.close()
    except Exception as exc:
        log.warning("verify_sync: failed to query brain DB — %s", exc)
        return result

    result["expected"] = len(expected_ids)

    # --- Step 3: fetch all MemPalace drawer IDs for this project wing (ONE subprocess) ---
    script = f"""
import json, chromadb
client = chromadb.PersistentClient(path={json.dumps(MEMPALACE_PATH)})
col = client.get_collection({json.dumps(COLLECTION_NAME)})
results = col.get(where={{"wing": {json.dumps(project_slug)}}}, limit=10000)
print(json.dumps(results["ids"]))
"""
    actual_ids_raw = _run_chromadb_op(script)
    if actual_ids_raw is None:
        log.warning("verify_sync: could not query MemPalace for project '%s'", project_slug)
        # Return partial result with expected count but zeros for actual
        return result

    actual_ids: set[str] = set(actual_ids_raw)
    result["actual"] = len(actual_ids)

    # --- Step 4: compare sets ---
    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids

    result["missing"] = len(missing)
    result["extra"] = len(extra)
    result["missing_ids"] = sorted(missing)[:5]
    result["ok"] = len(missing) == 0

    return result


def health_check(db_path: Path, project_slug: str) -> dict:
    """
    Return a comprehensive health report for the brain <-> MemPalace bridge.

    Report structure:
        {
            "brain_db": {"exists": bool, "entities": int, "decisions": int, "events": int},
            "mempalace": {"available": bool, "total_drawers": int, "project_drawers": int},
            "brain_json": {"exists": bool, "people_count": int, "last_sync": str},
            "sync_status": <verify_sync result>,
            "recommendations": ["list of issues to fix"],
        }
    """
    db_path = Path(db_path)
    report: dict = {
        "brain_db": {"exists": False, "entities": 0, "decisions": 0, "events": 0},
        "mempalace": {"available": False, "total_drawers": 0, "project_drawers": 0},
        "brain_json": {"exists": False, "people_count": 0, "last_sync": ""},
        "sync_status": {},
        "recommendations": [],
    }
    recommendations: list[str] = []

    # --- brain_db section ---
    if db_path.exists():
        report["brain_db"]["exists"] = True
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")

            proj_row = conn.execute(
                "SELECT * FROM projects WHERE slug = ?", (project_slug,)
            ).fetchone()

            if proj_row:
                project_id = proj_row["id"]
                report["brain_db"]["entities"] = conn.execute(
                    "SELECT COUNT(*) as c FROM entities WHERE project_id = ?", (project_id,)
                ).fetchone()["c"]
                report["brain_db"]["decisions"] = conn.execute(
                    "SELECT COUNT(*) as c FROM decisions WHERE project_id = ?", (project_id,)
                ).fetchone()["c"]
                report["brain_db"]["events"] = conn.execute(
                    "SELECT COUNT(*) as c FROM events WHERE project_id = ?", (project_id,)
                ).fetchone()["c"]
            else:
                recommendations.append(
                    f"Project '{project_slug}' not found in brain DB — run 'brain add-project' first."
                )

            conn.close()
        except Exception as exc:
            log.warning("health_check: failed to query brain DB — %s", exc)
            recommendations.append(f"brain DB read error: {exc}")
    else:
        recommendations.append(
            f"brain DB not found at {db_path} — run 'brain init' first."
        )

    # --- mempalace section (ONE subprocess for total + project counts) ---
    mempalace_script = f"""
import json, chromadb
client = chromadb.PersistentClient(path={json.dumps(MEMPALACE_PATH)})
col = client.get_collection({json.dumps(COLLECTION_NAME)})
total = col.count()
project = len(col.get(where={{"wing": {json.dumps(project_slug)}}}, limit=10000)["ids"])
print(json.dumps({{"total": total, "project": project}}))
"""
    mempalace_stats = _run_chromadb_op(mempalace_script)
    if mempalace_stats is not None:
        report["mempalace"]["available"] = True
        report["mempalace"]["total_drawers"] = mempalace_stats.get("total", 0)
        report["mempalace"]["project_drawers"] = mempalace_stats.get("project", 0)
    else:
        recommendations.append(
            "MemPalace (ChromaDB) is unavailable — check that the mempalace venv is installed "
            f"at {MEMPALACE_PYTHON}."
        )

    # --- brain_json section ---
    brain_json_path = Path(BRAIN_JSON_PATH)
    if brain_json_path.exists():
        report["brain_json"]["exists"] = True
        try:
            with open(brain_json_path, "r") as f:
                bj = json.load(f)
            report["brain_json"]["people_count"] = len(bj.get("people", {}))
            report["brain_json"]["last_sync"] = bj.get("stats", {}).get("last_sync", "")
        except Exception as exc:
            log.warning("health_check: could not read brain.json — %s", exc)
            recommendations.append(f"brain.json exists but could not be parsed: {exc}")
    else:
        recommendations.append(
            f"brain.json not found at {BRAIN_JSON_PATH} — run 'brain full-sync' to create it."
        )

    # --- sync_status section ---
    sync_status = verify_sync(db_path, project_slug)
    report["sync_status"] = sync_status

    if not sync_status.get("ok", False):
        missing = sync_status.get("missing", 0)
        if missing > 0:
            recommendations.append(
                f"{missing} brain DB record(s) are missing from MemPalace — "
                "run 'brain full-sync <project>' to repair."
            )
        extra = sync_status.get("extra", 0)
        if extra > 0:
            recommendations.append(
                f"{extra} MemPalace drawer(s) have no corresponding brain DB record "
                "(orphaned drawers — may be safe to ignore)."
            )

    # --- final recommendations ---
    if not recommendations:
        recommendations.append("All systems nominal — brain DB and MemPalace are in sync.")

    report["recommendations"] = recommendations
    return report
