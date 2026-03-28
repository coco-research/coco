import json
import logging
import uuid
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Query
from app.db.connections import get_hub_db, get_platform_db
from app.config import HUB_DB_PATH, BRAIN_JSON_PATH
from app.services.dedup import similarity, find_duplicates, pick_best, group_similarity
from app.services.event_bus import event_bus
from app.models.todos import CreateTodoBody, MergeTodosBody, PatchTodoBody
from app.models.common import TransitionBody

log = logging.getLogger(__name__)


def _load_people_priorities() -> dict[str, str]:
    """Load people -> priority mapping from brain.json for priority inference."""
    try:
        data = json.loads(BRAIN_JSON_PATH.read_text())
        people = data.get("people", {})
        return {
            info.get("full_name", "").lower(): info.get("priority", "normal")
            for info in people.values()
            if info.get("full_name")
        }
    except Exception:
        return {}


def _extract_action_items_from_content(row: dict) -> list[dict]:
    """Extract action items from a content row's metadata JSON.

    Supports two metadata layouts:
    - email: metadata.extraction.action_items
    - voice: metadata.meeting_note.action_items
    """
    try:
        meta = json.loads(row.get("metadata") or "{}")
    except (json.JSONDecodeError, TypeError):
        return []

    items = []

    # Email layout
    extraction = meta.get("extraction", {})
    if extraction and isinstance(extraction.get("action_items"), list):
        items.extend(extraction["action_items"])

    # Voice memo layout
    meeting = meta.get("meeting_note", {})
    if meeting and isinstance(meeting.get("action_items"), list):
        items.extend(meeting["action_items"])

    return items


def _infer_priority(action_item: dict, people_priorities: dict) -> str:
    """Infer todo priority based on owner matching against brain.json people."""
    owner = (action_item.get("owner") or "").lower()
    if not owner:
        return "medium"
    for full_name, priority in people_priorities.items():
        if full_name in owner or owner in full_name:
            return "high" if priority == "high" else "medium"
    return "medium"


def _source_type_from_content(source: str) -> str:
    """Map content.source to todo source_type."""
    mapping = {"email": "email", "voice": "voice"}
    return mapping.get(source, "email")


router = APIRouter(tags=["Todos"])

# ---- State machine ----

TODO_STATES = {"backlog", "todo", "in_progress", "done", "archived"}

TODO_TRANSITIONS: dict[str, list[str]] = {
    "backlog": ["todo", "archived"],
    "todo": ["in_progress", "backlog", "archived"],
    "in_progress": ["done", "todo"],
    "done": ["archived", "in_progress"],
    "archived": ["backlog"],
    # Legacy states map forward
    "open": ["backlog", "todo", "in_progress", "done", "archived"],
    "dismissed": ["backlog", "archived"],
}

# ---- Hub.db column list (explicit, never SELECT *) ----

_HUB_TODO_COLS = "id, title, project_id, priority, owner, due_date, status, source_type, source_content_id, created_at"

# ---- Overlay helpers ----

# Fields in hub.db todos that can be overridden via platform.db
_OVERLAY_FIELDS = ("title", "status", "priority", "owner", "due_date", "project_id", "node_id")


def _merge_hub_todo_with_override(hub_todo: dict, override: dict | None) -> dict:
    """Apply platform.db override fields on top of a hub.db todo row."""
    if not override:
        return hub_todo
    merged = dict(hub_todo)
    for field in _OVERLAY_FIELDS:
        val = override.get(field)
        if val is not None:
            merged[field] = val
    return merged


def _build_platform_native_todo(row: dict) -> dict:
    """Build a todo dict from a platform-native todo_overrides row."""
    return {
        "id": row["hub_todo_id"],
        "title": row.get("title"),
        "status": row.get("status") or "open",
        "priority": row.get("priority") or "medium",
        "owner": row.get("owner"),
        "due_date": row.get("due_date"),
        "project_id": row.get("project_id"),
        "node_id": row.get("node_id"),
        "source_type": row.get("source_type"),
        "source_content_id": row.get("source_content_id"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "is_platform_native": True,
    }


def _get_todo_by_id(todo_id: str) -> dict | None:
    """Fetch a single todo by id, merging hub + overlay or returning platform-native."""
    # Check platform.db first
    with get_platform_db() as pdb:
        override_row = pdb.execute(
            "SELECT * FROM todo_overrides WHERE hub_todo_id = ?", (todo_id,)
        ).fetchone()
        override = dict(override_row) if override_row else None

    if override and override.get("is_platform_native"):
        return _build_platform_native_todo(override)

    # Check hub.db
    try:
        with get_hub_db() as db:
            row = db.execute(
                f"SELECT {_HUB_TODO_COLS} FROM todos WHERE id = ?", (todo_id,)
            ).fetchone()
            if row:
                return _merge_hub_todo_with_override(dict(row), override)
    except Exception:
        pass

    # If we have an override but no hub row, it may be orphaned -- still return it
    if override:
        return _build_platform_native_todo(override)

    return None


@router.get("/api/todos")
def list_todos(
    status: str | None = None,
    project_id: str | None = None,
    priority: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        # Step 1: Read all hub.db todos (read-only)
        hub_todos: list[dict] = []
        try:
            with get_hub_db() as db:
                rows = db.execute(
                    f"SELECT {_HUB_TODO_COLS} FROM todos ORDER BY created_at DESC"
                ).fetchall()
                hub_todos = [dict(r) for r in rows]
        except Exception as e:
            log.warning("list_todos_hub_read_failed: %s", e)

        # Step 2: Read all overrides + platform-native todos from platform.db
        overrides: dict[str, dict] = {}
        platform_native: list[dict] = []
        with get_platform_db() as pdb:
            override_rows = pdb.execute("SELECT * FROM todo_overrides").fetchall()
            for r in override_rows:
                row = dict(r)
                if row.get("is_platform_native"):
                    platform_native.append(_build_platform_native_todo(row))
                else:
                    overrides[row["hub_todo_id"]] = row

        # Step 3: Merge hub todos with overrides
        merged = []
        for t in hub_todos:
            merged.append(_merge_hub_todo_with_override(t, overrides.get(t["id"])))

        # Step 4: Add platform-native todos
        merged.extend(platform_native)

        # Step 5: Apply filters
        if status:
            merged = [t for t in merged if t.get("status") == status]
        if project_id:
            merged = [t for t in merged if t.get("project_id") == project_id]
        if priority:
            merged = [t for t in merged if t.get("priority") == priority]

        # Step 6: Sort by created_at desc, then paginate
        merged.sort(key=lambda t: t.get("created_at") or "", reverse=True)
        return merged[offset : offset + limit]
    except Exception as e:
        log.exception("list_todos failed: %s", e)
        return []


@router.get("/api/todos/duplicates")
def find_duplicate_todos(
    threshold: float = Query(0.75, ge=0.1, le=1.0),
):
    """Find groups of near-duplicate todos using fuzzy title matching.

    Returns duplicate groups with a suggested todo to keep and the rest as duplicates.
    """
    try:
        hub_todos: list[dict] = []
        try:
            with get_hub_db() as db:
                rows = db.execute(
                    f"SELECT {_HUB_TODO_COLS} FROM todos WHERE status NOT IN ('archived', 'done') ORDER BY created_at DESC"
                ).fetchall()
                hub_todos = [dict(r) for r in rows]
        except Exception:
            pass

        # Apply overrides and add platform-native
        with get_platform_db() as pdb:
            override_rows = pdb.execute("SELECT * FROM todo_overrides").fetchall()

        overrides: dict[str, dict] = {}
        platform_native: list[dict] = []
        for r in override_rows:
            row = dict(r)
            if row.get("is_platform_native"):
                platform_native.append(_build_platform_native_todo(row))
            else:
                overrides[row["hub_todo_id"]] = row

        merged = []
        for t in hub_todos:
            merged.append(_merge_hub_todo_with_override(t, overrides.get(t["id"])))
        merged.extend(platform_native)

        # Filter out archived/done
        todos = [t for t in merged if t.get("status") not in ("archived", "done")]
    except Exception as e:
        raise HTTPException(500, f"Failed to read todos: {e}")

    groups = find_duplicates(todos, threshold=threshold)
    result = []
    for group in groups:
        best = pick_best(group)
        others = [t for t in group if t["id"] != best["id"]]
        result.append({
            "suggested_keep": best,
            "duplicates": others,
            "similarity": group_similarity(group),
        })
    return result


@router.post("/api/todos/merge")
def merge_todos(body: MergeTodosBody):
    """Merge duplicate todos by keeping one and archiving the rest.

    Sets removed todos' status to 'archived' in todo_overrides (platform.db).
    """
    keep_id = body.keep_id
    remove_ids = body.remove_ids

    # Verify keep_id exists
    kept = _get_todo_by_id(keep_id)
    if not kept:
        raise HTTPException(404, f"Todo {keep_id} not found")

    # Archive each removed todo via platform.db overlay
    archived_count = 0
    with get_platform_db() as pdb:
        for rid in remove_ids:
            if rid == keep_id:
                continue
            pdb.execute(
                """INSERT INTO todo_overrides (hub_todo_id, status, updated_at)
                   VALUES (?, 'archived', datetime('now'))
                   ON CONFLICT(hub_todo_id) DO UPDATE SET status = 'archived', updated_at = datetime('now')""",
                (rid,),
            )
            archived_count += 1
        pdb.commit()

    return {
        "kept": kept,
        "archived_count": archived_count,
    }


@router.post("/api/todos", status_code=201)
def create_todo(body: CreateTodoBody):
    """Create a new todo in platform.db (never writes to hub.db)."""
    title = body.title
    todo_id = str(uuid.uuid4())

    with get_platform_db() as pdb:
        try:
            pdb.execute(
                """INSERT INTO todo_overrides
                   (hub_todo_id, title, project_id, priority, owner, due_date, node_id, status,
                    source_type, source_content_id, is_platform_native, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'open', NULL, NULL, 1, datetime('now'), datetime('now'))""",
                (
                    todo_id,
                    title,
                    body.project_id,
                    body.priority,
                    body.owner,
                    body.due_date,
                    body.node_id,
                ),
            )
            pdb.commit()
        except Exception as e:
            log.exception("create_todo failed: %s", e)
            raise HTTPException(500, f"Failed to create todo: {e}")

    result: dict = {
        "id": todo_id,
        "title": title,
        "status": "open",
        "priority": body.priority,
        "owner": body.owner,
        "due_date": body.due_date,
        "project_id": body.project_id,
        "node_id": body.node_id,
        "is_platform_native": True,
    }

    # Dedup-on-ingest: check for near-duplicates across both hub.db and platform-native todos
    try:
        existing_titles: list[dict] = []

        # Hub.db todos
        try:
            with get_hub_db() as db:
                hub_rows = db.execute(
                    "SELECT id, title FROM todos WHERE id != ? AND status NOT IN ('archived', 'done') LIMIT 500",
                    (todo_id,),
                ).fetchall()
                existing_titles.extend({"id": r["id"], "title": r["title"]} for r in hub_rows)
        except Exception:
            pass

        # Platform-native todos
        with get_platform_db() as pdb:
            pn_rows = pdb.execute(
                "SELECT hub_todo_id, title FROM todo_overrides "
                "WHERE hub_todo_id != ? AND is_platform_native = 1 AND status NOT IN ('archived', 'done') LIMIT 500",
                (todo_id,),
            ).fetchall()
            existing_titles.extend({"id": r["hub_todo_id"], "title": r["title"]} for r in pn_rows)

        best_match = None
        best_score = 0.0
        for ex in existing_titles:
            score = similarity(title, ex["title"])
            if score > best_score:
                best_score = score
                best_match = ex
        if best_match and best_score >= 0.8:
            result["possible_duplicate"] = {
                "id": best_match["id"],
                "title": best_match["title"],
                "similarity": round(best_score, 3),
            }
    except Exception:
        pass

    event_bus.emit("todo.created", {"id": todo_id, "title": title})
    return result


@router.patch("/api/todos/{todo_id}")
def update_todo(todo_id: str, body: PatchTodoBody):
    """Update a todo via platform.db overlay (never writes to hub.db)."""
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    if not updates:
        raise HTTPException(400, "No valid fields to update")

    # Check that the todo exists somewhere
    existing = _get_todo_by_id(todo_id)
    if not existing:
        raise HTTPException(404, "Todo not found")

    is_native = existing.get("is_platform_native", False)

    # Upsert into todo_overrides
    with get_platform_db() as pdb:
        row = pdb.execute(
            "SELECT hub_todo_id FROM todo_overrides WHERE hub_todo_id = ?", (todo_id,)
        ).fetchone()

        if row:
            # Update existing override row
            set_parts = [f"{k} = ?" for k in updates]
            set_parts.append("updated_at = datetime('now')")
            vals = list(updates.values()) + [todo_id]
            pdb.execute(
                f"UPDATE todo_overrides SET {', '.join(set_parts)} WHERE hub_todo_id = ?",
                vals,
            )
        else:
            # Insert new override for a hub.db todo
            col_names = list(updates.keys())
            col_str = ", ".join(["hub_todo_id"] + col_names + ["is_platform_native"])
            placeholders = ", ".join(["?"] * (len(col_names) + 2))
            vals = [todo_id] + list(updates.values()) + [1 if is_native else 0]
            pdb.execute(
                f"INSERT INTO todo_overrides ({col_str}, updated_at) VALUES ({placeholders}, datetime('now'))",
                vals,
            )
        pdb.commit()

    # Re-fetch merged result
    todo_result = _get_todo_by_id(todo_id)
    event_bus.emit("todo.updated", {"id": todo_id, **updates})
    return todo_result


@router.patch("/api/todos/{todo_id}/transition")
def transition_todo(todo_id: str, body: TransitionBody):
    """Transition a todo to a new state using the state machine.

    Validates that the transition is allowed from the current state.
    Returns 422 if the transition is invalid.
    """
    to_state = body.to_state
    if to_state not in TODO_STATES:
        raise HTTPException(400, f"Invalid state: {to_state}. Valid states: {sorted(TODO_STATES)}")

    # Get current state (merged view)
    existing = _get_todo_by_id(todo_id)
    if not existing:
        raise HTTPException(404, "Todo not found")

    current_state = existing.get("status", "open")
    allowed = TODO_TRANSITIONS.get(current_state, [])

    if to_state not in allowed:
        raise HTTPException(
            422,
            f"Cannot transition from '{current_state}' to '{to_state}'. "
            f"Allowed transitions: {allowed}",
        )

    is_native = existing.get("is_platform_native", False)

    # Upsert status into todo_overrides
    with get_platform_db() as pdb:
        pdb.execute(
            """INSERT INTO todo_overrides (hub_todo_id, status, is_platform_native, updated_at)
               VALUES (?, ?, ?, datetime('now'))
               ON CONFLICT(hub_todo_id) DO UPDATE SET status = ?, updated_at = datetime('now')""",
            (todo_id, to_state, 1 if is_native else 0, to_state),
        )
        pdb.commit()

    todo_result = _get_todo_by_id(todo_id)
    event_bus.emit("todo.updated", {"id": todo_id, "status": to_state, "from_state": current_state})
    return todo_result


@router.post("/api/todos/sync")
def sync_todos_from_kh():
    """Pull action items from Knowledge Hub content and create todos for new ones.

    Scans content table metadata for action_items (emails and voice memos),
    deduplicates against existing todos by source_content_id, and creates
    new todos with priority inferred from brain.json people graph.

    New todos are written to platform.db as platform-native (never writes to hub.db).
    """
    people_priorities = _load_people_priorities()
    synced = 0
    skipped = 0

    try:
        with get_hub_db() as hub:
            rows = hub.execute(
                "SELECT id, source, title, metadata, content_type "
                "FROM content "
                "WHERE source IN ('email', 'voice') AND metadata IS NOT NULL"
            ).fetchall()
    except Exception as e:
        log.error("sync_hub_read_failed", extra={"error": str(e)})
        raise HTTPException(500, f"Failed to read Knowledge Hub: {e}")

    if not rows:
        return {"synced": 0, "skipped": 0, "total": 0}

    # Gather existing source_content_ids from BOTH hub.db and platform.db
    existing_source_ids: set[str] = set()
    existing_titles: set[tuple[str, str | None]] = set()

    try:
        with get_hub_db() as hub:
            try:
                src_rows = hub.execute(
                    "SELECT source_content_id FROM todos WHERE source_content_id IS NOT NULL"
                ).fetchall()
                existing_source_ids.update(r["source_content_id"] for r in src_rows)
            except Exception:
                pass

            try:
                title_rows = hub.execute(
                    "SELECT LOWER(TRIM(title)) as norm_title, project_id FROM todos"
                ).fetchall()
                existing_titles.update((r["norm_title"], r["project_id"]) for r in title_rows)
            except Exception:
                pass
    except Exception:
        pass

    # From platform.db
    with get_platform_db() as pdb:
        try:
            pn_src_rows = pdb.execute(
                "SELECT source_content_id FROM todo_overrides WHERE source_content_id IS NOT NULL"
            ).fetchall()
            existing_source_ids.update(r["source_content_id"] for r in pn_src_rows)
        except Exception:
            pass

        try:
            pn_title_rows = pdb.execute(
                "SELECT LOWER(TRIM(title)) as norm_title, project_id FROM todo_overrides WHERE is_platform_native = 1"
            ).fetchall()
            existing_titles.update((r["norm_title"], r["project_id"]) for r in pn_title_rows)
        except Exception:
            pass

    # Get project mappings from hub.db
    project_map: dict[str, str] = {}
    try:
        with get_hub_db() as hub:
            pc_rows = hub.execute(
                "SELECT content_id, project_id FROM project_content"
            ).fetchall()
            project_map = {r["content_id"]: r["project_id"] for r in pc_rows}
    except Exception:
        pass

    batch_titles: set[tuple[str, str | None]] = set()

    # Write new todos to platform.db as platform-native
    with get_platform_db() as pdb:
        for row in rows:
            row_dict = dict(row)
            content_id = row_dict["id"]
            source = row_dict.get("source", "email")

            action_items = _extract_action_items_from_content(row_dict)
            if not action_items:
                continue

            for i, item in enumerate(action_items):
                source_key = content_id if len(action_items) == 1 else f"{content_id}:{i}"

                if source_key in existing_source_ids:
                    skipped += 1
                    continue

                description = item.get("description", "").strip()
                if not description:
                    continue

                todo_id = str(uuid.uuid4())
                title = description[:200]
                project_id_val = project_map.get(content_id)
                priority = _infer_priority(item, people_priorities)
                source_type = _source_type_from_content(source)
                owner = item.get("owner") or "rijul"
                due_date = item.get("due_date")

                # Title-based dedup
                normalized = title.strip().lower()
                title_key = (normalized, project_id_val)
                if title_key in existing_titles or title_key in batch_titles:
                    skipped += 1
                    continue

                try:
                    pdb.execute(
                        """INSERT INTO todo_overrides
                           (hub_todo_id, title, project_id, priority, owner, due_date, status,
                            source_type, source_content_id, is_platform_native, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, 1, datetime('now'), datetime('now'))""",
                        (todo_id, title, project_id_val, priority, owner, due_date, source_type, source_key),
                    )
                    synced += 1
                    existing_source_ids.add(source_key)
                    batch_titles.add(title_key)
                except Exception as e:
                    log.warning("sync_todo_insert_failed", extra={"content_id": content_id, "error": str(e)})
                    skipped += 1

        pdb.commit()

    log.info("todo_sync_complete", extra={"synced": synced, "skipped": skipped})
    return {"synced": synced, "skipped": skipped, "total": synced + skipped}


@router.post("/api/todos/dedup")
def dedup_todos():
    """Remove duplicate todos, keeping the oldest one per normalized title + project_id.

    Archives duplicates via todo_overrides in platform.db (never writes to hub.db).
    """
    # Gather all active todos (merged view)
    hub_todos: list[dict] = []
    try:
        with get_hub_db() as db:
            rows = db.execute(f"SELECT {_HUB_TODO_COLS} FROM todos").fetchall()
            hub_todos = [dict(r) for r in rows]
    except Exception:
        pass

    with get_platform_db() as pdb:
        override_rows = pdb.execute("SELECT * FROM todo_overrides").fetchall()

    overrides: dict[str, dict] = {}
    platform_native: list[dict] = []
    for r in override_rows:
        row = dict(r)
        if row.get("is_platform_native"):
            platform_native.append(_build_platform_native_todo(row))
        else:
            overrides[row["hub_todo_id"]] = row

    all_todos: list[dict] = []
    for t in hub_todos:
        all_todos.append(_merge_hub_todo_with_override(t, overrides.get(t["id"])))
    all_todos.extend(platform_native)

    # Group by normalized title + project_id
    groups: dict[tuple[str, str | None], list[dict]] = defaultdict(list)
    for t in all_todos:
        norm_title = (t.get("title") or "").strip().lower()
        pid = t.get("project_id")
        groups[(norm_title, pid)].append(t)

    removed = 0
    groups_cleaned = 0

    with get_platform_db() as pdb:
        for _key, group in groups.items():
            if len(group) < 2:
                continue

            # Sort by created_at ascending, keep oldest
            group.sort(key=lambda t: t.get("created_at") or "")
            ids_to_archive = [t["id"] for t in group[1:]]

            for tid in ids_to_archive:
                pdb.execute(
                    """INSERT INTO todo_overrides (hub_todo_id, status, updated_at)
                       VALUES (?, 'archived', datetime('now'))
                       ON CONFLICT(hub_todo_id) DO UPDATE SET status = 'archived', updated_at = datetime('now')""",
                    (tid,),
                )
                removed += 1
            groups_cleaned += 1

        pdb.commit()

    log.info("todo_dedup_complete", extra={"removed": removed, "groups_cleaned": groups_cleaned})
    return {"removed": removed, "groups_cleaned": groups_cleaned}
