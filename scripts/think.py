#!/usr/bin/env python3
"""CoCo Think Pass — runs every 15 min via launchd.

Reads KH SQLite DB (read-only) and updates ~/.coco/queue.json.
Does NOT use MCP (runs outside Claude Code sessions).
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

COCO_DIR = Path.home() / ".coco"
BRAIN_PATH = COCO_DIR / "brain.json"
QUEUE_PATH = COCO_DIR / "queue.json"
CONFIG_PATH = COCO_DIR / "config.json"
LOGS_DIR = COCO_DIR / "logs"
HUB_DB_PATH = Path.home() / ".hub" / "hub.db"

CURRENT_BRAIN_VERSION = 1
CURRENT_QUEUE_VERSION = 1


def log(msg: str):
    """Log to stderr and think.log."""
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line, file=sys.stderr)
    log_path = LOGS_DIR / "think.log"
    with open(log_path, "a") as f:
        f.write(line + "\n")


def atomic_write_json(path: Path, data: dict):
    """Write JSON atomically: write to .tmp, then rename."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.rename(tmp, path)


def load_json(path: Path, default: dict) -> dict:
    """Load JSON file, return default if missing/corrupt."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log(f"Warning: Could not load {path}: {e}")
        return default


def get_last_think_timestamp() -> str | None:
    """Get timestamp of last think pass from queue.json."""
    queue = load_json(QUEUE_PATH, {})
    return queue.get("last_updated")


def connect_kh_db() -> sqlite3.Connection | None:
    """Connect to KH SQLite in read-only mode."""
    if not HUB_DB_PATH.exists():
        log(f"KH database not found at {HUB_DB_PATH}")
        return None
    try:
        conn = sqlite3.connect(f"file:{HUB_DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        log(f"Failed to connect to KH DB: {e}")
        return None


def get_new_items(conn: sqlite3.Connection, since: str | None) -> list[dict]:
    """Get new content items since last think pass."""
    if since is None:
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    rows = conn.execute(
        "SELECT id, source, title, status, relevance_score, metadata, created_at, updated_at "
        "FROM content WHERE updated_at > ? ORDER BY updated_at DESC LIMIT 200",
        [since],
    ).fetchall()
    return [dict(r) for r in rows]


def get_new_drafts(conn: sqlite3.Connection, since: str | None) -> list[dict]:
    """Get new pending drafts since last think pass."""
    if since is None:
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    rows = conn.execute(
        "SELECT id, project_id, target_template, target_section, status, created_at "
        "FROM drafts WHERE created_at > ? AND status = 'pending' LIMIT 50",
        [since],
    ).fetchall()
    return [dict(r) for r in rows]


def get_health(conn: sqlite3.Connection) -> list[dict]:
    """Get adapter sync state."""
    rows = conn.execute(
        "SELECT source_name, last_success, items_synced, status, error_message FROM sync_state"
    ).fetchall()
    return [dict(r) for r in rows]


def extract_person(item: dict, people: dict) -> str | None:
    """Try to match item to a known person from brain.json."""
    metadata = item.get("metadata", "{}")
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}

    sender = metadata.get("from", "") or metadata.get("sender", "")
    if not sender:
        return None

    sender_lower = sender.lower()
    for slug, person in people.items():
        for pattern in person.get("patterns", {}).get("email_from", []):
            if pattern.lower() in sender_lower:
                return slug
    return None


def calculate_priority(item: dict, person: str | None, attention_rules: list) -> int:
    """Calculate priority (1=highest) based on attention rules."""
    # Check attention rules
    for rule in attention_rules:
        match = rule.get("match", {})
        field = match.get("field")
        op = match.get("op")
        value = match.get("value")

        if field == "person" and op == "eq" and value == person:
            action = rule.get("action", "")
            if action == "flag_urgent":
                return 1
            elif action == "flag_high":
                return 2

    # Default priorities by type
    source = item.get("source", "")
    status = item.get("status", "")
    relevance = item.get("relevance_score") or 0.5

    if relevance >= 0.9:
        return 2
    elif relevance >= 0.7:
        return 3
    return 4


def should_auto_handle(item: dict, config: dict, brain: dict) -> tuple[bool, str]:
    """Determine if item should be auto-handled. Returns (should_auto, action)."""
    auto_config = config.get("auto_handle", {})
    threshold = auto_config.get("classify_above_confidence", 0.85)

    metadata = item.get("metadata", "{}")
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {}

    triage = metadata.get("triage", {})
    classification = ""
    if isinstance(triage, dict):
        classification = triage.get("classification", "")
    elif isinstance(triage, str):
        classification = triage

    # Auto-dismiss noise from unknown senders
    if auto_config.get("dismiss_noise_from_unknown", False):
        if classification == "NOISE":
            person = extract_person(item, brain.get("people", {}))
            if person is None:
                return True, "dismissed"

    # Auto-file FYI
    if auto_config.get("file_fyi_silently", False):
        if classification == "FYI":
            return True, "filed"

    return False, ""


def age_deferred(queue: dict) -> None:
    """Check deferred items and resurface if due."""
    now = datetime.now(timezone.utc)
    resurfaced = []

    for item in list(queue.get("deferred", [])):
        resurface_str = item.get("next_resurface")
        if resurface_str:
            try:
                resurface_dt = datetime.fromisoformat(resurface_str)
                if now >= resurface_dt:
                    item["status"] = "pending"
                    count = item.get("deferred_count", 0)
                    item["priority"] = max(1, item.get("priority", 3) - 1)  # bump priority
                    queue.get("items", []).append(item)
                    resurfaced.append(item)
            except (ValueError, TypeError):
                pass

    for item in resurfaced:
        queue["deferred"].remove(item)


def think():
    """Main think pass."""
    log("Think pass starting...")

    # Ensure logs dir exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Load state
    brain = load_json(BRAIN_PATH, {"version": 1, "people": {}, "attention_rules": []})
    queue = load_json(QUEUE_PATH, {"version": 1, "items": [], "deferred": [], "auto_handled_since_last_session": []})
    config = load_json(CONFIG_PATH, {})

    last_run = get_last_think_timestamp()

    # Backup brain.json before modifications
    if BRAIN_PATH.exists():
        shutil.copy2(BRAIN_PATH, BRAIN_PATH.with_suffix(".bak"))

    # Connect to KH DB (read-only)
    conn = connect_kh_db()
    if conn is None:
        log("Cannot connect to KH DB — skipping think pass")
        return

    try:
        # 1. Get new items
        new_items = get_new_items(conn, last_run)
        log(f"Found {len(new_items)} new/updated items since last think")

        # 2. Apply attention rules + auto-handle
        auto_handled = []
        queued = []

        for item in new_items:
            person = extract_person(item, brain.get("people", {}))

            auto, action = should_auto_handle(item, config, brain)
            if auto:
                auto_handled.append({
                    "action": action,
                    "summary": item.get("title", "Unknown"),
                    "source_id": item.get("id"),
                    "confidence": item.get("relevance_score", 0),
                })
            else:
                priority = calculate_priority(item, person, brain.get("attention_rules", []))
                queued.append({
                    "id": f"q-{item['id'][:8]}",
                    "type": "new_content",
                    "priority": priority,
                    "summary": item.get("title", "Unknown"),
                    "source_id": item.get("id"),
                    "project": None,
                    "person": person,
                    "created_at": item.get("created_at"),
                    "deferred_count": 0,
                    "status": "pending",
                })

        # 3. Get new drafts
        new_drafts = get_new_drafts(conn, last_run)
        for draft in new_drafts:
            queued.append({
                "id": f"q-d-{draft['id'][:8]}",
                "type": "draft_approval",
                "priority": 2,
                "summary": f"{draft.get('target_template', '')} -> {draft.get('target_section', '')}",
                "source_id": draft.get("id"),
                "project": draft.get("project_id"),
                "person": None,
                "created_at": draft.get("created_at"),
                "deferred_count": 0,
                "status": "pending",
            })

        # 4. Check health
        health = get_health(conn)
        for h in health:
            if h.get("status") == "red":
                queued.append({
                    "id": f"q-h-{h['source_name']}",
                    "type": "health",
                    "priority": 3,
                    "summary": f"{h['source_name']} adapter: {h.get('error_message', 'stale')}",
                    "source_id": None,
                    "project": None,
                    "person": None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "deferred_count": 0,
                    "status": "pending",
                })

        # 5. Age deferred items
        age_deferred(queue)

        # 6. Merge into queue (avoid duplicates by source_id)
        existing_ids = {i.get("source_id") for i in queue.get("items", []) if i.get("source_id")}
        for item in queued:
            if item.get("source_id") not in existing_ids:
                queue.get("items", []).append(item)
                existing_ids.add(item.get("source_id"))

        # 7. Update auto-handled log
        queue["auto_handled_since_last_session"] = auto_handled

        # 8. Sort queue by priority
        queue["items"].sort(key=lambda x: x.get("priority", 99))

        # 9. Save
        queue["last_updated"] = datetime.now(timezone.utc).isoformat()
        atomic_write_json(QUEUE_PATH, queue)

        # Update brain stats
        brain.setdefault("stats", {})
        brain["stats"]["items_auto_handled"] = brain["stats"].get("items_auto_handled", 0) + len(auto_handled)
        atomic_write_json(BRAIN_PATH, brain)

        log(f"Think pass complete: {len(auto_handled)} auto-handled, {len(queued)} queued, {len(new_drafts)} new drafts")

    finally:
        conn.close()


if __name__ == "__main__":
    try:
        think()
    except Exception as e:
        log(f"Think pass FAILED: {e}")
        sys.exit(1)
