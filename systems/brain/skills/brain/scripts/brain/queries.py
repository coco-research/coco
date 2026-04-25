"""Read-only context builders for CoCo and agent consumption."""

import sqlite3
from .models import row_to_dict


def session_context(conn: sqlite3.Connection, project_slug: str) -> dict:
    """Full session briefing for CoCo."""
    proj = conn.execute("SELECT * FROM projects WHERE slug=?", (project_slug,)).fetchone()
    if not proj:
        return {"error": f"Project '{project_slug}' not found"}
    pid = proj["id"]

    open_tasks = [row_to_dict(r) for r in conn.execute(
        "SELECT t.*, e.name as owner_name FROM tasks t "
        "LEFT JOIN entities e ON t.owner_entity_id=e.id "
        "WHERE t.project_id=? AND t.status IN ('open','in_progress','blocked','waiting') "
        "ORDER BY t.priority ASC, t.created_at DESC", (pid,)
    )]

    recent_decisions = [row_to_dict(r) for r in conn.execute(
        "SELECT * FROM decisions WHERE project_id=? ORDER BY date DESC LIMIT 10", (pid,)
    )]

    active_threads = []
    for r in conn.execute(
        "SELECT th.*, (SELECT COUNT(*) FROM thread_items ti WHERE ti.thread_id=th.id) as item_count "
        "FROM threads th WHERE th.project_id=? AND th.status='open' ORDER BY th.created_at DESC", (pid,)
    ):
        active_threads.append(row_to_dict(r))

    recent_events = [row_to_dict(r) for r in conn.execute(
        "SELECT * FROM events WHERE project_id=? ORDER BY date DESC LIMIT 10", (pid,)
    )]

    entity_counts = {}
    for r in conn.execute(
        "SELECT type, COUNT(*) as cnt FROM entities WHERE project_id=? GROUP BY type", (pid,)
    ):
        entity_counts[r["type"]] = r["cnt"]

    stats = conn.execute(
        "SELECT "
        "(SELECT COUNT(*) FROM entities WHERE project_id=?) as entities, "
        "(SELECT COUNT(*) FROM tasks WHERE project_id=?) as tasks, "
        "(SELECT COUNT(*) FROM decisions WHERE project_id=?) as decisions, "
        "(SELECT COUNT(*) FROM events WHERE project_id=?) as events, "
        "(SELECT COUNT(*) FROM threads WHERE project_id=?) as threads, "
        "(SELECT COUNT(*) FROM relationships r JOIN entities e ON r.source_id=e.id WHERE e.project_id=?) as relationships",
        (pid, pid, pid, pid, pid, pid),
    ).fetchone()

    return {
        "project": row_to_dict(proj),
        "open_tasks": open_tasks,
        "recent_decisions": recent_decisions,
        "active_threads": active_threads,
        "recent_events": recent_events,
        "entity_summary": entity_counts,
        "stats": row_to_dict(stats),
    }


def entity_graph(conn: sqlite3.Connection, entity_id: int) -> dict:
    """Entity with all relationships expanded."""
    entity = conn.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone()
    if not entity:
        return {"error": f"Entity {entity_id} not found"}

    rels = []
    for r in conn.execute(
        "SELECT r.*, e.name as target_name, e.type as target_type "
        "FROM relationships r JOIN entities e ON r.target_id=e.id WHERE r.source_id=?",
        (entity_id,),
    ):
        rels.append({"direction": "outgoing", **row_to_dict(r)})
    for r in conn.execute(
        "SELECT r.*, e.name as source_name, e.type as source_type "
        "FROM relationships r JOIN entities e ON r.source_id=e.id WHERE r.target_id=?",
        (entity_id,),
    ):
        rels.append({"direction": "incoming", **row_to_dict(r)})

    tasks = [row_to_dict(r) for r in conn.execute(
        "SELECT * FROM tasks WHERE owner_entity_id=? AND status != 'done'", (entity_id,)
    )]

    from .operations import get_tags
    tags = get_tags(conn, "entity", entity_id)

    return {
        "entity": row_to_dict(entity),
        "relationships": rels,
        "tasks_owned": tasks,
        "tags": tags,
    }


def thread_detail(conn: sqlite3.Connection, thread_id: int) -> dict:
    """Thread with all linked items resolved."""
    thread = conn.execute("SELECT * FROM threads WHERE id=?", (thread_id,)).fetchone()
    if not thread:
        return {"error": f"Thread {thread_id} not found"}

    items = []
    for ti in conn.execute("SELECT * FROM thread_items WHERE thread_id=? ORDER BY id", (thread_id,)):
        item_type = ti["item_type"]
        item_id = ti["item_id"]
        table_map = {"task": "tasks", "decision": "decisions", "event": "events", "entity": "entities"}
        table = table_map.get(item_type)
        if table:
            row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (item_id,)).fetchone()
            if row:
                items.append({"type": item_type, "data": row_to_dict(row)})

    return {"thread": row_to_dict(thread), "items": items}


def search_brain(conn: sqlite3.Connection, query: str, project_slug: str | None = None) -> dict:
    """Full-text search across names, titles, decisions."""
    pattern = f"%{query}%"
    pid_filter = ""
    params_base: list = [pattern]

    if project_slug:
        proj = conn.execute("SELECT id FROM projects WHERE slug=?", (project_slug,)).fetchone()
        if proj:
            pid_filter = " AND project_id=?"
            params_base.append(proj["id"])

    entities = [row_to_dict(r) for r in conn.execute(
        f"SELECT * FROM entities WHERE name LIKE ?{pid_filter} LIMIT 20", params_base
    )]
    tasks = [row_to_dict(r) for r in conn.execute(
        f"SELECT * FROM tasks WHERE title LIKE ?{pid_filter} LIMIT 20", params_base
    )]
    decisions = [row_to_dict(r) for r in conn.execute(
        f"SELECT * FROM decisions WHERE decision LIKE ?{pid_filter} LIMIT 20", params_base
    )]
    events = [row_to_dict(r) for r in conn.execute(
        f"SELECT * FROM events WHERE title LIKE ?{pid_filter} LIMIT 20", params_base
    )]

    return {
        "query": query,
        "results": {
            "entities": entities,
            "tasks": tasks,
            "decisions": decisions,
            "events": events,
        },
    }
