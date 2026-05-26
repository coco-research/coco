import json
import logging
import uuid
from collections import defaultdict
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, insert, update, delete, func
from app.db.session import get_db
from app.db.compat import now, upsert
from app.db.tables import (
    hub_todos, hub_content, hub_project_content,
    todo_overrides, todo_dependencies, entity_identifiers,
)
from app.config import HUB_DB_PATH, BRAIN_JSON_PATH
from app.services.dedup import similarity, find_duplicates, pick_best, group_similarity
from app.services.event_bus import event_bus
from app.models.todos import (
    CreateBlockedByBody,
    CreateDependencyBody,
    CreateTodoBody,
    MergeTodosBody,
    PatchTodoBody,
)
from app.models.common import TransitionBody
from app.services.id_generator import assign_display_id, resolve_display_id

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
    """Extract action items from a content row's metadata JSON."""
    try:
        meta = json.loads(row.get("metadata") or "{}")
    except (json.JSONDecodeError, TypeError):
        return []

    items = []
    extraction = meta.get("extraction", {})
    if extraction and isinstance(extraction.get("action_items"), list):
        items.extend(extraction["action_items"])
    meeting = meta.get("meeting_note", {})
    if meeting and isinstance(meeting.get("action_items"), list):
        items.extend(meeting["action_items"])
    return items


def _infer_priority(action_item: dict, people_priorities: dict) -> str:
    owner = (action_item.get("owner") or "").lower()
    if not owner:
        return "medium"
    for full_name, priority in people_priorities.items():
        if full_name in owner or owner in full_name:
            return "high" if priority == "high" else "medium"
    return "medium"


def _source_type_from_content(source: str) -> str:
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
    "open": ["backlog", "todo", "in_progress", "done", "archived"],
    "dismissed": ["backlog", "archived"],
}

# ---- Hub.db column list ----

_HUB_TODO_COLS = [
    hub_todos.c.id, hub_todos.c.title, hub_todos.c.project_id,
    hub_todos.c.priority, hub_todos.c.owner, hub_todos.c.due_date,
    hub_todos.c.status, hub_todos.c.source_type,
    hub_todos.c.source_content_id, hub_todos.c.created_at,
]

# ---- Overlay helpers ----

_OVERLAY_FIELDS = ("title", "status", "priority", "owner", "due_date", "project_id", "node_id")


def _merge_hub_todo_with_override(hub_todo: dict, override: dict | None) -> dict:
    if not override:
        return hub_todo
    merged = dict(hub_todo)
    for field in _OVERLAY_FIELDS:
        val = override.get(field)
        if val is not None:
            merged[field] = val
    return merged


def _build_platform_native_todo(row: dict) -> dict:
    out = {
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
    if row.get("human_id"):
        # human_id is the primary identifier; display_id kept for back-compat.
        out["human_id"] = row["human_id"]
        out["display_id"] = row["human_id"]
    return out


def _get_todo_by_id(todo_id: str) -> dict | None:
    """Fetch a single todo by id, merging hub + overlay or returning platform-native."""
    with get_db() as conn:
        override_row = conn.execute(
            select(todo_overrides).where(todo_overrides.c.hub_todo_id == todo_id)
        ).fetchone()
        override = dict(override_row._mapping) if override_row else None

        if override and override.get("is_platform_native"):
            return _build_platform_native_todo(override)

        # Check hub mirror
        try:
            row = conn.execute(
                select(*_HUB_TODO_COLS).where(hub_todos.c.id == todo_id)
            ).fetchone()
            if row:
                return _merge_hub_todo_with_override(dict(row._mapping), override)
        except Exception:
            pass

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
        with get_db() as conn:
            # Step 1: Read all hub mirror todos
            hub_rows: list[dict] = []
            try:
                rows = conn.execute(
                    select(*_HUB_TODO_COLS).order_by(hub_todos.c.created_at.desc())
                ).fetchall()
                hub_rows = [dict(r._mapping) for r in rows]
            except Exception as e:
                log.warning("list_todos_hub_read_failed: %s", e)

            # Step 2: Read all overrides + platform-native
            overrides: dict[str, dict] = {}
            platform_native: list[dict] = []
            display_id_map: dict[str, str] = {}
            blocked_by_counts: dict[str, int] = {}
            blocking_counts: dict[str, int] = {}

            override_rows = conn.execute(select(todo_overrides)).fetchall()
            for r in override_rows:
                row = dict(r._mapping)
                if row.get("is_platform_native"):
                    platform_native.append(_build_platform_native_todo(row))
                else:
                    overrides[row["hub_todo_id"]] = row

            # Load display IDs
            try:
                ident_rows = conn.execute(
                    select(entity_identifiers.c.entity_id, entity_identifiers.c.display_id)
                    .where(entity_identifiers.c.entity_type == "todo")
                ).fetchall()
                display_id_map = {r.entity_id: r.display_id for r in ident_rows}
            except Exception:
                pass

            # Load blocked_by counts
            try:
                dep_rows = conn.execute(
                    select(
                        todo_dependencies.c.todo_id,
                        func.count().label("cnt"),
                    )
                    .where(todo_dependencies.c.dep_type == "blocked_by")
                    .group_by(todo_dependencies.c.todo_id)
                ).fetchall()
                blocked_by_counts = {r.todo_id: r.cnt for r in dep_rows}
            except Exception:
                pass

            # Load blocking counts
            try:
                blocking_rows = conn.execute(
                    select(
                        todo_dependencies.c.depends_on,
                        func.count().label("cnt"),
                    )
                    .where(todo_dependencies.c.dep_type == "blocked_by")
                    .group_by(todo_dependencies.c.depends_on)
                ).fetchall()
                blocking_counts = {r.depends_on: r.cnt for r in blocking_rows}
            except Exception:
                pass

            # Step 3: Merge
            merged = []
            for t in hub_rows:
                merged.append(_merge_hub_todo_with_override(t, overrides.get(t["id"])))
            merged.extend(platform_native)

            # Step 4: Enrich
            for t in merged:
                tid = t.get("id")
                # Prefer explicit human_id column from override row when set.
                if not t.get("human_id") and tid in display_id_map:
                    t["human_id"] = display_id_map[tid]
                if t.get("human_id") and not t.get("display_id"):
                    t["display_id"] = t["human_id"]
                t["blocked_by_count"] = blocked_by_counts.get(tid, 0)
                t["blocking_count"] = blocking_counts.get(tid, 0)

            # Step 5: Filter
            if status:
                merged = [t for t in merged if t.get("status") == status]
            if project_id:
                merged = [t for t in merged if t.get("project_id") == project_id]
            if priority:
                merged = [t for t in merged if t.get("priority") == priority]

            # Step 6: Sort + paginate
            merged.sort(key=lambda t: t.get("created_at") or "", reverse=True)
            return merged[offset : offset + limit]
    except Exception as e:
        log.exception("list_todos failed: %s", e)
        return []


@router.get("/api/todos/by-id/{display_id}")
def get_todo_by_display_id(display_id: str):
    result = resolve_display_id(display_id)
    if not result or result.get("entity_type") != "todo":
        raise HTTPException(404, f"No todo found for display ID '{display_id}'")

    hub_todo_id = result["entity_id"]
    todo = _get_todo_by_id(hub_todo_id)
    if not todo:
        raise HTTPException(404, f"Todo {hub_todo_id} not found")

    todo["human_id"] = result["display_id"]
    todo["display_id"] = result["display_id"]
    return todo


@router.get("/api/todos/duplicates")
def find_duplicate_todos(
    threshold: float = Query(0.75, ge=0.1, le=1.0),
):
    try:
        with get_db() as conn:
            hub_rows: list[dict] = []
            try:
                rows = conn.execute(
                    select(*_HUB_TODO_COLS)
                    .where(hub_todos.c.status.notin_(["archived", "done"]))
                    .order_by(hub_todos.c.created_at.desc())
                ).fetchall()
                hub_rows = [dict(r._mapping) for r in rows]
            except Exception:
                pass

            override_rows = conn.execute(select(todo_overrides)).fetchall()

        overrides: dict[str, dict] = {}
        platform_native: list[dict] = []
        for r in override_rows:
            row = dict(r._mapping)
            if row.get("is_platform_native"):
                platform_native.append(_build_platform_native_todo(row))
            else:
                overrides[row["hub_todo_id"]] = row

        merged = []
        for t in hub_rows:
            merged.append(_merge_hub_todo_with_override(t, overrides.get(t["id"])))
        merged.extend(platform_native)

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
    keep_id = body.keep_id
    remove_ids = body.remove_ids

    kept = _get_todo_by_id(keep_id)
    if not kept:
        raise HTTPException(404, f"Todo {keep_id} not found")

    archived_count = 0
    with get_db() as conn:
        for rid in remove_ids:
            if rid == keep_id:
                continue
            conn.execute(
                upsert(
                    todo_overrides,
                    values={"hub_todo_id": rid, "status": "archived", "updated_at": now()},
                    conflict_columns=["hub_todo_id"],
                    update_columns=["status", "updated_at"],
                )
            )
            archived_count += 1

    return {"kept": kept, "archived_count": archived_count}


@router.post("/api/todos", status_code=201)
def create_todo(body: CreateTodoBody):
    title = body.title
    todo_id = str(uuid.uuid4())

    with get_db() as conn:
        try:
            conn.execute(
                insert(todo_overrides).values(
                    hub_todo_id=todo_id,
                    title=title,
                    project_id=body.project_id,
                    priority=body.priority,
                    owner=body.owner,
                    due_date=body.due_date,
                    node_id=body.node_id,
                    status="open",
                    source_type=None,
                    source_content_id=None,
                    is_platform_native=1,
                    created_at=now(),
                    updated_at=now(),
                )
            )
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

    effective_node_id = body.node_id or body.project_id
    try:
        # effective_node_id may be None — id_generator falls back to global bucket.
        display_id = assign_display_id(todo_id, effective_node_id, entity_type="todo")
        if display_id:
            result["human_id"] = display_id
            result["display_id"] = display_id
    except Exception as e:
        log.warning("assign_display_id_failed: %s", e)

    # Dedup-on-ingest
    try:
        existing_titles: list[dict] = []

        with get_db() as conn:
            # Hub todos
            try:
                hub_rows = conn.execute(
                    select(hub_todos.c.id, hub_todos.c.title)
                    .where(hub_todos.c.id != todo_id)
                    .where(hub_todos.c.status.notin_(["archived", "done"]))
                    .limit(500)
                ).fetchall()
                existing_titles.extend({"id": r.id, "title": r.title} for r in hub_rows)
            except Exception:
                pass

            # Platform-native todos
            pn_rows = conn.execute(
                select(todo_overrides.c.hub_todo_id, todo_overrides.c.title)
                .where(todo_overrides.c.hub_todo_id != todo_id)
                .where(todo_overrides.c.is_platform_native == 1)
                .where(todo_overrides.c.status.notin_(["archived", "done"]))
                .limit(500)
            ).fetchall()
            existing_titles.extend({"id": r.hub_todo_id, "title": r.title} for r in pn_rows)

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
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    if not updates:
        raise HTTPException(400, "No valid fields to update")

    existing = _get_todo_by_id(todo_id)
    if not existing:
        raise HTTPException(404, "Todo not found")

    is_native = existing.get("is_platform_native", False)

    with get_db() as conn:
        row = conn.execute(
            select(todo_overrides.c.hub_todo_id)
            .where(todo_overrides.c.hub_todo_id == todo_id)
        ).fetchone()

        if row:
            conn.execute(
                update(todo_overrides)
                .where(todo_overrides.c.hub_todo_id == todo_id)
                .values(**updates, updated_at=now())
            )
        else:
            conn.execute(
                insert(todo_overrides).values(
                    hub_todo_id=todo_id,
                    **updates,
                    is_platform_native=1 if is_native else 0,
                    updated_at=now(),
                )
            )

    todo_result = _get_todo_by_id(todo_id)
    event_bus.emit("todo.updated", {"id": todo_id, **updates})
    return todo_result


@router.delete("/api/todos/{todo_id}", status_code=200)
def delete_todo(todo_id: str):
    """Delete a todo.

    Platform-native todos are hard-deleted (override row + dependencies removed).
    Hub-backed todos are soft-deleted by recording an override with status=archived,
    since the hub mirror is read-only from this service.
    """
    existing = _get_todo_by_id(todo_id)
    if not existing:
        raise HTTPException(404, "Todo not found")

    is_native = bool(existing.get("is_platform_native"))

    with get_db() as conn:
        # Always clean up dependency edges referencing this todo
        conn.execute(
            delete(todo_dependencies).where(todo_dependencies.c.todo_id == todo_id)
        )
        conn.execute(
            delete(todo_dependencies).where(todo_dependencies.c.depends_on == todo_id)
        )

        if is_native:
            conn.execute(
                delete(todo_overrides).where(todo_overrides.c.hub_todo_id == todo_id)
            )
        else:
            # Soft delete hub-backed todo via override
            conn.execute(
                upsert(
                    todo_overrides,
                    values={
                        "hub_todo_id": todo_id,
                        "status": "archived",
                        "is_platform_native": 0,
                        "updated_at": now(),
                    },
                    conflict_cols=["hub_todo_id"],
                    update_cols=["status", "updated_at"],
                )
            )

    event_bus.emit("todo.deleted", {"id": todo_id, "hard_deleted": is_native})
    return {"id": todo_id, "deleted": True, "hard_deleted": is_native}


@router.patch("/api/todos/{todo_id}/transition")
def transition_todo(todo_id: str, body: TransitionBody):
    to_state = body.to_state
    if to_state not in TODO_STATES:
        raise HTTPException(400, f"Invalid state: {to_state}. Valid states: {sorted(TODO_STATES)}")

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

    # Check for unresolved blocking dependencies when completing
    warning = None
    if to_state == "done":
        with get_db() as conn:
            unresolved_rows = conn.execute(
                select(todo_dependencies.c.depends_on)
                .where(todo_dependencies.c.todo_id == todo_id)
                .where(todo_dependencies.c.dep_type == "blocked_by")
            ).fetchall()

        unresolved_blockers = []
        for r in unresolved_rows:
            blocker = _get_todo_by_id(r.depends_on)
            if blocker and blocker.get("status") not in ("done", "archived"):
                unresolved_blockers.append({
                    "id": blocker["id"],
                    "title": blocker.get("title", ""),
                    "status": blocker.get("status", ""),
                })

        if unresolved_blockers:
            warning = (
                f"This todo has {len(unresolved_blockers)} unresolved blocker(s) "
                f"that are not yet done."
            )

    # Upsert status.
    #
    # Atomic-transition note (409 Conflict semantics):
    #   On PostgreSQL we re-read the overlay row inside the same transaction
    #   with ``SELECT ... FOR UPDATE`` so two concurrent transitions from the
    #   same source state cannot both succeed.  If the row's status has
    #   already moved away from ``current_state`` since the pre-flight check,
    #   we raise 409.
    #
    #   SQLite does not implement row-level locks, so ``with_for_update()``
    #   is a no-op there.  Atomic transitions on SQLite rely on the surrounding
    #   transaction (BEGIN ... COMMIT) and the single-writer model — adequate
    #   for the current single-node deployment but NOT a true row lock.
    with get_db() as conn:
        locked = conn.execute(
            select(todo_overrides.c.hub_todo_id, todo_overrides.c.status)
            .where(todo_overrides.c.hub_todo_id == todo_id)
            .with_for_update()
        ).fetchone()

        if locked is not None:
            locked_status = locked._mapping.get("status") or "open"
            if locked_status != current_state and locked_status != to_state:
                raise HTTPException(
                    409,
                    f"Concurrent modification: todo is now in state "
                    f"'{locked_status}', expected '{current_state}'.",
                )

        conn.execute(
            upsert(
                todo_overrides,
                values={
                    "hub_todo_id": todo_id,
                    "status": to_state,
                    "is_platform_native": 1 if is_native else 0,
                    "updated_at": now(),
                },
                conflict_columns=["hub_todo_id"],
                update_columns=["status", "updated_at"],
            )
        )

    todo_result = _get_todo_by_id(todo_id)
    if warning:
        todo_result["warning"] = warning
    event_bus.emit("todo.updated", {"id": todo_id, "status": to_state, "from_state": current_state})
    return todo_result


@router.post("/api/todos/sync")
def sync_todos_from_kh():
    """Pull action items from Knowledge Hub content and create todos for new ones."""
    people_priorities = _load_people_priorities()
    synced = 0
    skipped = 0

    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    hub_content.c.id, hub_content.c.source, hub_content.c.title,
                    hub_content.c.metadata, hub_content.c.content_type,
                )
                .where(hub_content.c.source.in_(["email", "voice"]))
                .where(hub_content.c.metadata.isnot(None))
            ).fetchall()
    except Exception as e:
        log.error("sync_hub_read_failed", extra={"error": str(e)})
        raise HTTPException(500, f"Failed to read Knowledge Hub: {e}")

    if not rows:
        return {"synced": 0, "skipped": 0, "total": 0}

    # Gather existing source_content_ids from BOTH hub + platform
    existing_source_ids: set[str] = set()
    existing_titles: set[tuple[str, str | None]] = set()

    try:
        with get_db() as conn:
            # From hub mirror
            try:
                src_rows = conn.execute(
                    select(hub_todos.c.source_content_id)
                    .where(hub_todos.c.source_content_id.isnot(None))
                ).fetchall()
                existing_source_ids.update(r.source_content_id for r in src_rows)
            except Exception:
                pass

            try:
                title_rows = conn.execute(
                    select(
                        func.lower(func.trim(hub_todos.c.title)).label("norm_title"),
                        hub_todos.c.project_id,
                    )
                ).fetchall()
                existing_titles.update((r.norm_title, r.project_id) for r in title_rows)
            except Exception:
                pass

            # From platform
            try:
                pn_src_rows = conn.execute(
                    select(todo_overrides.c.source_content_id)
                    .where(todo_overrides.c.source_content_id.isnot(None))
                ).fetchall()
                existing_source_ids.update(r.source_content_id for r in pn_src_rows)
            except Exception:
                pass

            try:
                pn_title_rows = conn.execute(
                    select(
                        func.lower(func.trim(todo_overrides.c.title)).label("norm_title"),
                        todo_overrides.c.project_id,
                    ).where(todo_overrides.c.is_platform_native == 1)
                ).fetchall()
                existing_titles.update((r.norm_title, r.project_id) for r in pn_title_rows)
            except Exception:
                pass

            # Get project mappings from hub mirror
            pc_rows = conn.execute(
                select(hub_project_content.c.content_id, hub_project_content.c.project_id)
            ).fetchall()
            project_map = {r.content_id: r.project_id for r in pc_rows}

    except Exception:
        project_map = {}

    batch_titles: set[tuple[str, str | None]] = set()

    # Write new todos
    with get_db() as conn:
        for row in rows:
            row_dict = dict(row._mapping)
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
                priority_val = _infer_priority(item, people_priorities)
                source_type = _source_type_from_content(source)
                owner = item.get("owner") or "rijul"
                due_date = item.get("due_date")

                normalized = title.strip().lower()
                title_key = (normalized, project_id_val)
                if title_key in existing_titles or title_key in batch_titles:
                    skipped += 1
                    continue

                try:
                    conn.execute(
                        insert(todo_overrides).values(
                            hub_todo_id=todo_id,
                            title=title,
                            project_id=project_id_val,
                            priority=priority_val,
                            owner=owner,
                            due_date=due_date,
                            status="open",
                            source_type=source_type,
                            source_content_id=source_key,
                            is_platform_native=1,
                            created_at=now(),
                            updated_at=now(),
                        )
                    )
                    synced += 1
                    existing_source_ids.add(source_key)
                    batch_titles.add(title_key)
                except Exception as e:
                    log.warning("sync_todo_insert_failed", extra={"content_id": content_id, "error": str(e)})
                    skipped += 1

    log.info("todo_sync_complete", extra={"synced": synced, "skipped": skipped})
    return {"synced": synced, "skipped": skipped, "total": synced + skipped}


@router.post("/api/todos/dedup")
def dedup_todos():
    """Remove duplicate todos, keeping the oldest one per normalized title + project_id."""
    hub_rows: list[dict] = []
    with get_db() as conn:
        try:
            rows = conn.execute(select(*_HUB_TODO_COLS)).fetchall()
            hub_rows = [dict(r._mapping) for r in rows]
        except Exception:
            pass

        override_rows = conn.execute(select(todo_overrides)).fetchall()

    overrides: dict[str, dict] = {}
    platform_native: list[dict] = []
    for r in override_rows:
        row = dict(r._mapping)
        if row.get("is_platform_native"):
            platform_native.append(_build_platform_native_todo(row))
        else:
            overrides[row["hub_todo_id"]] = row

    all_todos: list[dict] = []
    for t in hub_rows:
        all_todos.append(_merge_hub_todo_with_override(t, overrides.get(t["id"])))
    all_todos.extend(platform_native)

    groups: dict[tuple[str, str | None], list[dict]] = defaultdict(list)
    for t in all_todos:
        norm_title = (t.get("title") or "").strip().lower()
        pid = t.get("project_id")
        groups[(norm_title, pid)].append(t)

    removed = 0
    groups_cleaned = 0

    with get_db() as conn:
        for _key, group in groups.items():
            if len(group) < 2:
                continue

            group.sort(key=lambda t: t.get("created_at") or "")
            ids_to_archive = [t["id"] for t in group[1:]]

            for tid in ids_to_archive:
                conn.execute(
                    upsert(
                        todo_overrides,
                        values={"hub_todo_id": tid, "status": "archived", "updated_at": now()},
                        conflict_columns=["hub_todo_id"],
                        update_columns=["status", "updated_at"],
                    )
                )
                removed += 1
            groups_cleaned += 1

    log.info("todo_dedup_complete", extra={"removed": removed, "groups_cleaned": groups_cleaned})
    return {"removed": removed, "groups_cleaned": groups_cleaned}


# ---- Todo Dependencies ----


def _has_circular_dependency(conn, from_id: str, to_id: str) -> bool:
    visited: set[str] = set()
    queue = [to_id]
    while queue:
        current = queue.pop(0)
        if current == from_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        rows = conn.execute(
            select(todo_dependencies.c.depends_on)
            .where(todo_dependencies.c.todo_id == current)
            .where(todo_dependencies.c.dep_type == "blocked_by")
        ).fetchall()
        for r in rows:
            queue.append(r.depends_on)
    return False


def _get_blocker_ids(conn, todo_id: str) -> list[str]:
    """IDs of todos that block this todo (blocked_by edges)."""
    rows = conn.execute(
        select(todo_dependencies.c.depends_on)
        .where(todo_dependencies.c.todo_id == todo_id)
        .where(todo_dependencies.c.dep_type == "blocked_by")
    ).fetchall()
    return [r.depends_on for r in rows]


def _get_blocked_ids(conn, todo_id: str) -> list[str]:
    """IDs of todos that this todo blocks (inverse of blocked_by)."""
    rows = conn.execute(
        select(todo_dependencies.c.todo_id)
        .where(todo_dependencies.c.depends_on == todo_id)
        .where(todo_dependencies.c.dep_type == "blocked_by")
    ).fetchall()
    return [r.todo_id for r in rows]


@router.get("/api/todos/{todo_id}/dependencies")
def list_dependencies(todo_id: str):
    existing = _get_todo_by_id(todo_id)
    if not existing:
        raise HTTPException(404, "Todo not found")

    with get_db() as conn:
        blocked_by_rows = conn.execute(
            select(
                todo_dependencies.c.id,
                todo_dependencies.c.todo_id,
                todo_dependencies.c.depends_on,
                todo_dependencies.c.dep_type,
                todo_dependencies.c.created_at,
            )
            .where(todo_dependencies.c.todo_id == todo_id)
            .where(todo_dependencies.c.dep_type == "blocked_by")
            .order_by(todo_dependencies.c.created_at)
        ).fetchall()

        blocking_rows = conn.execute(
            select(
                todo_dependencies.c.id,
                todo_dependencies.c.todo_id,
                todo_dependencies.c.depends_on,
                todo_dependencies.c.dep_type,
                todo_dependencies.c.created_at,
            )
            .where(todo_dependencies.c.depends_on == todo_id)
            .where(todo_dependencies.c.dep_type == "blocked_by")
            .order_by(todo_dependencies.c.created_at)
        ).fetchall()

        related_rows = conn.execute(
            select(
                todo_dependencies.c.id,
                todo_dependencies.c.todo_id,
                todo_dependencies.c.depends_on,
                todo_dependencies.c.dep_type,
                todo_dependencies.c.created_at,
            )
            .where(
                ((todo_dependencies.c.todo_id == todo_id) | (todo_dependencies.c.depends_on == todo_id))
                & (todo_dependencies.c.dep_type == "related_to")
            )
            .order_by(todo_dependencies.c.created_at)
        ).fetchall()

    dep_ids: set[str] = set()
    for r in blocked_by_rows:
        dep_ids.add(r.depends_on)
    for r in blocking_rows:
        dep_ids.add(r.todo_id)
    for r in related_rows:
        dep_ids.add(r.todo_id)
        dep_ids.add(r.depends_on)
    dep_ids.discard(todo_id)

    title_map: dict[str, str] = {}
    status_map: dict[str, str] = {}
    for did in dep_ids:
        t = _get_todo_by_id(did)
        if t:
            title_map[did] = t.get("title", "")
            status_map[did] = t.get("status", "")

    def _enrich(row, related_id: str):
        d = dict(row._mapping)
        d["related_title"] = title_map.get(related_id, "")
        d["related_status"] = status_map.get(related_id, "")
        d["related_id"] = related_id
        return d

    return {
        "blocked_by": [_enrich(r, r.depends_on) for r in blocked_by_rows],
        "blocking": [_enrich(r, r.todo_id) for r in blocking_rows],
        "related_to": [
            _enrich(r, r.depends_on if r.todo_id == todo_id else r.todo_id)
            for r in related_rows
        ],
    }


@router.get("/api/todos/all-dependencies")
def list_all_dependencies():
    with get_db() as conn:
        rows = conn.execute(
            select(
                todo_dependencies.c.id,
                todo_dependencies.c.todo_id,
                todo_dependencies.c.depends_on,
                todo_dependencies.c.dep_type,
                todo_dependencies.c.created_at,
            )
            .order_by(todo_dependencies.c.created_at)
        ).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/api/todos/{todo_id}")
def get_todo(todo_id: str):
    """Fetch a single todo with its blocker / blocking dependency ids."""
    todo = _get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(404, "Todo not found")

    with get_db() as conn:
        todo["blocked_by"] = _get_blocker_ids(conn, todo_id)
        todo["blocks"] = _get_blocked_ids(conn, todo_id)
    return todo


@router.post("/api/todos/{todo_id}/dependencies", status_code=201)
def create_dependency(todo_id: str, body: CreateDependencyBody):
    existing = _get_todo_by_id(todo_id)
    if not existing:
        raise HTTPException(404, "Todo not found")

    dep_todo = _get_todo_by_id(body.depends_on)
    if not dep_todo:
        raise HTTPException(404, f"Dependency todo '{body.depends_on}' not found")

    if todo_id == body.depends_on:
        raise HTTPException(400, "A todo cannot depend on itself")

    if body.dep_type == "blocked_by":
        with get_db() as conn:
            if _has_circular_dependency(conn, todo_id, body.depends_on):
                raise HTTPException(
                    422,
                    f"Circular dependency detected: '{body.depends_on}' is already transitively "
                    f"blocked by '{todo_id}'. Adding this dependency would create a cycle.",
                )

    dep_id = str(uuid.uuid4())

    with get_db() as conn:
        try:
            conn.execute(
                insert(todo_dependencies).values(
                    id=dep_id,
                    todo_id=todo_id,
                    depends_on=body.depends_on,
                    dep_type=body.dep_type,
                )
            )
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                raise HTTPException(409, "Dependency already exists")
            raise HTTPException(500, f"Failed to create dependency: {e}")

    event_bus.emit("todo.dependency.created", {
        "todo_id": todo_id,
        "depends_on": body.depends_on,
        "dep_type": body.dep_type,
    })
    return {
        "id": dep_id,
        "todo_id": todo_id,
        "depends_on": body.depends_on,
        "dep_type": body.dep_type,
        "related_title": dep_todo.get("title", ""),
    }


@router.delete("/api/todos/{todo_id}/dependencies/{dep_id}")
def delete_dependency(todo_id: str, dep_id: str):
    with get_db() as conn:
        row = conn.execute(
            select(todo_dependencies.c.id)
            .where(todo_dependencies.c.id == dep_id)
            .where(todo_dependencies.c.todo_id == todo_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Dependency not found")

        conn.execute(
            delete(todo_dependencies).where(todo_dependencies.c.id == dep_id)
        )

    event_bus.emit("todo.dependency.deleted", {"todo_id": todo_id, "dep_id": dep_id})
    return {"ok": True}


# ---- Convenience endpoints (GAP M9): blocked_by alias ----
# These mirror /dependencies but with the blocker-centric vocabulary requested
# by the GAP M9 spec: "todo B blocked by todo A".


@router.post("/api/todos/{todo_id}/blocked_by", status_code=201)
def add_blocked_by(todo_id: str, body: CreateBlockedByBody):
    """Mark `todo_id` as blocked_by `blocker_id`.

    Equivalent to POST /api/todos/{todo_id}/dependencies with
    {depends_on: blocker_id, dep_type: 'blocked_by'} but expressed in the
    blocker-centric vocabulary.
    """
    blocker_id = body.blocker_id

    existing = _get_todo_by_id(todo_id)
    if not existing:
        raise HTTPException(404, "Todo not found")

    blocker = _get_todo_by_id(blocker_id)
    if not blocker:
        raise HTTPException(404, f"Blocker todo '{blocker_id}' not found")

    if todo_id == blocker_id:
        raise HTTPException(400, "A todo cannot block itself")

    with get_db() as conn:
        if _has_circular_dependency(conn, todo_id, blocker_id):
            raise HTTPException(
                422,
                f"Circular dependency detected: '{blocker_id}' is already "
                f"transitively blocked by '{todo_id}'. Adding this dependency "
                "would create a cycle.",
            )

    dep_id = str(uuid.uuid4())

    with get_db() as conn:
        try:
            conn.execute(
                insert(todo_dependencies).values(
                    id=dep_id,
                    todo_id=todo_id,
                    depends_on=blocker_id,
                    dep_type="blocked_by",
                )
            )
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                raise HTTPException(409, "Dependency already exists")
            raise HTTPException(500, f"Failed to create dependency: {e}")

    event_bus.emit("todo.dependency.created", {
        "todo_id": todo_id,
        "depends_on": blocker_id,
        "dep_type": "blocked_by",
    })
    return {
        "id": dep_id,
        "todo_id": todo_id,
        "blocker_id": blocker_id,
        "depends_on": blocker_id,
        "dep_type": "blocked_by",
        "blocker_title": blocker.get("title", ""),
        "blocker_status": blocker.get("status", ""),
    }


@router.delete("/api/todos/{todo_id}/blocked_by/{blocker_id}", status_code=204)
def remove_blocked_by(todo_id: str, blocker_id: str):
    """Remove the blocked_by edge from `todo_id` to `blocker_id`."""
    with get_db() as conn:
        row = conn.execute(
            select(todo_dependencies.c.id)
            .where(todo_dependencies.c.todo_id == todo_id)
            .where(todo_dependencies.c.depends_on == blocker_id)
            .where(todo_dependencies.c.dep_type == "blocked_by")
        ).fetchone()
        if not row:
            raise HTTPException(404, "blocked_by edge not found")

        conn.execute(
            delete(todo_dependencies).where(todo_dependencies.c.id == row.id)
        )

    event_bus.emit("todo.dependency.deleted", {
        "todo_id": todo_id,
        "dep_id": row.id,
        "blocker_id": blocker_id,
    })
    return None
