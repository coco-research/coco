"""CRUD operations for all brain domains."""

import json
import sqlite3
from .models import now_iso, row_to_dict


# ── Projects ──────────────────────────────────────────────

def create_project(conn: sqlite3.Connection, name: str, slug: str,
                   description: str = "", status: str = "active") -> dict:
    cur = conn.execute(
        "INSERT INTO projects (name, slug, status, description, created_at) VALUES (?,?,?,?,?)",
        (name, slug, status, description, now_iso()),
    )
    conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM projects WHERE id=?", (cur.lastrowid,)).fetchone())


def get_project(conn: sqlite3.Connection, slug: str) -> dict | None:
    row = conn.execute("SELECT * FROM projects WHERE slug=?", (slug,)).fetchone()
    return row_to_dict(row) if row else None


def list_projects(conn: sqlite3.Connection) -> list[dict]:
    return [row_to_dict(r) for r in conn.execute("SELECT * FROM projects ORDER BY name")]


# ── Entities ──────────────────────────────────────────────

def create_entity(conn: sqlite3.Connection, project_id: int, etype: str, name: str,
                  external_id: str | None = None, metadata: dict | None = None) -> dict:
    ts = now_iso()
    cur = conn.execute(
        "INSERT INTO entities (project_id, type, name, external_id, metadata_json, created_at, updated_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (project_id, etype, name, external_id, json.dumps(metadata or {}), ts, ts),
    )
    conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM entities WHERE id=?", (cur.lastrowid,)).fetchone())


def upsert_entity(conn: sqlite3.Connection, project_id: int, etype: str, name: str,
                  external_id: str | None = None, metadata: dict | None = None) -> dict:
    """Match by (project_id, type, external_id) or (project_id, type, name). Update or create."""
    existing = None
    if external_id:
        existing = conn.execute(
            "SELECT * FROM entities WHERE project_id=? AND type=? AND external_id=?",
            (project_id, etype, external_id),
        ).fetchone()
    if not existing:
        existing = conn.execute(
            "SELECT * FROM entities WHERE project_id=? AND type=? AND name=?",
            (project_id, etype, name),
        ).fetchone()
    if existing:
        updates = {}
        if name != existing["name"]:
            updates["name"] = name
        if external_id and external_id != existing["external_id"]:
            updates["external_id"] = external_id
        if metadata and json.dumps(metadata) != existing["metadata_json"]:
            updates["metadata_json"] = json.dumps(metadata)
        if updates:
            return update_entity(conn, existing["id"], **updates)
        return row_to_dict(existing)
    return create_entity(conn, project_id, etype, name, external_id, metadata)


def get_entity(conn: sqlite3.Connection, entity_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone()
    return row_to_dict(row) if row else None


def find_entities(conn: sqlite3.Connection, project_id: int,
                  etype: str | None = None, name_like: str | None = None) -> list[dict]:
    sql = "SELECT * FROM entities WHERE project_id=?"
    params: list = [project_id]
    if etype:
        sql += " AND type=?"
        params.append(etype)
    if name_like:
        sql += " AND name LIKE ?"
        params.append(f"%{name_like}%")
    sql += " ORDER BY type, name"
    return [row_to_dict(r) for r in conn.execute(sql, params)]


def update_entity(conn: sqlite3.Connection, entity_id: int, **kwargs) -> dict:
    old = conn.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone()
    if not old:
        raise ValueError(f"Entity {entity_id} not found")
    allowed = {"name", "external_id", "metadata_json", "type"}
    sets, params = [], []
    for k, v in kwargs.items():
        if k in allowed:
            # Log change
            log_change(conn, entity_id, k, old[k], v, "update_entity")
            sets.append(f"{k}=?")
            params.append(v)
    if sets:
        sets.append("updated_at=?")
        params.append(now_iso())
        params.append(entity_id)
        conn.execute(f"UPDATE entities SET {', '.join(sets)} WHERE id=?", params)
        conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone())


# ── Relationships ─────────────────────────────────────────

def create_relationship(conn: sqlite3.Connection, source_id: int, target_id: int,
                        rel_type: str, context: str | None = None,
                        valid_from: str | None = None, valid_to: str | None = None) -> dict:
    # Idempotent: skip if exists
    existing = conn.execute(
        "SELECT * FROM relationships WHERE source_id=? AND target_id=? AND rel_type=?",
        (source_id, target_id, rel_type),
    ).fetchone()
    if existing:
        return row_to_dict(existing)
    cur = conn.execute(
        "INSERT INTO relationships (source_id, target_id, rel_type, context, valid_from, valid_to) "
        "VALUES (?,?,?,?,?,?)",
        (source_id, target_id, rel_type, context, valid_from, valid_to),
    )
    conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM relationships WHERE id=?", (cur.lastrowid,)).fetchone())


def get_relationships(conn: sqlite3.Connection, entity_id: int,
                      direction: str = "both") -> list[dict]:
    results = []
    if direction in ("both", "outgoing"):
        rows = conn.execute(
            "SELECT r.*, e.name as target_name, e.type as target_type "
            "FROM relationships r JOIN entities e ON r.target_id=e.id WHERE r.source_id=?",
            (entity_id,),
        )
        results.extend({"direction": "outgoing", **row_to_dict(r)} for r in rows)
    if direction in ("both", "incoming"):
        rows = conn.execute(
            "SELECT r.*, e.name as source_name, e.type as source_type "
            "FROM relationships r JOIN entities e ON r.source_id=e.id WHERE r.target_id=?",
            (entity_id,),
        )
        results.extend({"direction": "incoming", **row_to_dict(r)} for r in rows)
    return results


# ── Tasks ─────────────────────────────────────────────────

def create_task(conn: sqlite3.Connection, project_id: int, title: str,
                owner_entity_id: int | None = None, priority: int = 3,
                due_date: str | None = None, notes: str | None = None) -> dict:
    cur = conn.execute(
        "INSERT INTO tasks (project_id, title, status, owner_entity_id, priority, due_date, notes, created_at) "
        "VALUES (?,?,'open',?,?,?,?,?)",
        (project_id, title, owner_entity_id, priority, due_date, notes, now_iso()),
    )
    conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM tasks WHERE id=?", (cur.lastrowid,)).fetchone())


def update_task(conn: sqlite3.Connection, task_id: int, **kwargs) -> dict:
    allowed = {"status", "title", "owner_entity_id", "priority", "due_date", "notes", "blocked_by_task_id"}
    sets, params = [], []
    for k, v in kwargs.items():
        if k in allowed:
            sets.append(f"{k}=?")
            params.append(v)
    if kwargs.get("status") == "done":
        sets.append("completed_at=?")
        params.append(now_iso())
    if sets:
        params.append(task_id)
        conn.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id=?", params)
        conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())


def list_tasks(conn: sqlite3.Connection, project_id: int,
               status: str | None = None) -> list[dict]:
    sql = "SELECT * FROM tasks WHERE project_id=?"
    params: list = [project_id]
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY priority ASC, created_at DESC"
    return [row_to_dict(r) for r in conn.execute(sql, params)]


# ── Threads ───────────────────────────────────────────────

def create_thread(conn: sqlite3.Connection, project_id: int, title: str,
                  category: str | None = None, status: str = "open") -> dict:
    cur = conn.execute(
        "INSERT INTO threads (project_id, title, status, category, created_at) VALUES (?,?,?,?,?)",
        (project_id, title, status, category, now_iso()),
    )
    conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM threads WHERE id=?", (cur.lastrowid,)).fetchone())


def add_thread_item(conn: sqlite3.Connection, thread_id: int,
                    item_type: str, item_id: int) -> dict:
    cur = conn.execute(
        "INSERT INTO thread_items (thread_id, item_type, item_id) VALUES (?,?,?)",
        (thread_id, item_type, item_id),
    )
    conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM thread_items WHERE id=?", (cur.lastrowid,)).fetchone())


def list_threads(conn: sqlite3.Connection, project_id: int,
                 status: str | None = None) -> list[dict]:
    sql = "SELECT * FROM threads WHERE project_id=?"
    params: list = [project_id]
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    return [row_to_dict(r) for r in conn.execute(sql, params)]


# ── Decisions ─────────────────────────────────────────────

def create_decision(conn: sqlite3.Connection, project_id: int, date: str,
                    decision: str, context: str | None = None,
                    decided_by: str | None = None, impact: str | None = None,
                    thread_id: int | None = None) -> dict:
    cur = conn.execute(
        "INSERT INTO decisions (project_id, thread_id, date, decision, context, decided_by, impact) "
        "VALUES (?,?,?,?,?,?,?)",
        (project_id, thread_id, date, decision, context, decided_by, impact),
    )
    conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM decisions WHERE id=?", (cur.lastrowid,)).fetchone())


def list_decisions(conn: sqlite3.Connection, project_id: int, limit: int = 20) -> list[dict]:
    return [row_to_dict(r) for r in conn.execute(
        "SELECT * FROM decisions WHERE project_id=? ORDER BY date DESC LIMIT ?",
        (project_id, limit),
    )]


# ── Events ────────────────────────────────────────────────

def create_event(conn: sqlite3.Connection, project_id: int, date: str, etype: str,
                 title: str, summary: str | None = None, source: str | None = None,
                 participants: list | None = None) -> dict:
    cur = conn.execute(
        "INSERT INTO events (project_id, date, type, title, summary, source, participants_json) "
        "VALUES (?,?,?,?,?,?,?)",
        (project_id, date, etype, title, summary, source, json.dumps(participants or [])),
    )
    conn.commit()
    return row_to_dict(conn.execute("SELECT * FROM events WHERE id=?", (cur.lastrowid,)).fetchone())


def list_events(conn: sqlite3.Connection, project_id: int,
                etype: str | None = None, limit: int = 20) -> list[dict]:
    sql = "SELECT * FROM events WHERE project_id=?"
    params: list = [project_id]
    if etype:
        sql += " AND type=?"
        params.append(etype)
    sql += " ORDER BY date DESC LIMIT ?"
    params.append(limit)
    return [row_to_dict(r) for r in conn.execute(sql, params)]


# ── Tags ──────────────────────────────────────────────────

def ensure_tag(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM tags WHERE name=?", (name,)).fetchone()
    if row:
        return row["id"]
    cur = conn.execute("INSERT INTO tags (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def tag_item(conn: sqlite3.Connection, taggable_type: str,
             taggable_id: int, tag_name: str) -> None:
    tag_id = ensure_tag(conn, tag_name)
    conn.execute(
        "INSERT OR IGNORE INTO taggables (taggable_type, taggable_id, tag_id) VALUES (?,?,?)",
        (taggable_type, taggable_id, tag_id),
    )
    conn.commit()


def get_tags(conn: sqlite3.Connection, taggable_type: str, taggable_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT t.name FROM tags t JOIN taggables tg ON t.id=tg.tag_id "
        "WHERE tg.taggable_type=? AND tg.taggable_id=?",
        (taggable_type, taggable_id),
    )
    return [r["name"] for r in rows]


# ── Changelog ─────────────────────────────────────────────

def log_change(conn: sqlite3.Connection, entity_id: int, field: str,
               old_value, new_value, source: str | None = None) -> None:
    conn.execute(
        "INSERT INTO changelog (entity_id, field, old_value, new_value, source, timestamp) "
        "VALUES (?,?,?,?,?,?)",
        (entity_id, field, str(old_value) if old_value else None,
         str(new_value) if new_value else None, source, now_iso()),
    )
