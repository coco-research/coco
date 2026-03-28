import uuid
from fastapi import APIRouter, HTTPException
import structlog

from sqlalchemy import select, insert, update, delete, text
from app.db.session import get_db
from app.db.tables import (
    nodes, agents, goals, tasks, cost_ledger, budgets,
    project_context, handoffs, workflows, analysis_jobs,
    comments, agent_roles, hub_projects,
)
from app.services.event_bus import event_bus
from app.models.tree import CreateNodeBody, MoveNodeBody, PatchNodeBody, ReorderItem

log = structlog.get_logger()
router = APIRouter(tags=["Tree"])


# --- Helpers ---

def _build_tree(node_list: list[dict]) -> list[dict]:
    """Build nested tree structure from flat list of node dicts."""
    by_id = {}
    for n in node_list:
        n["children"] = []
        by_id[n["id"]] = n

    roots = []
    for n in node_list:
        pid = n.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(n)
        else:
            roots.append(n)

    return roots


_NODE_COLS = [
    nodes.c.id, nodes.c.parent_id, nodes.c.hub_project_id, nodes.c.label,
    nodes.c.node_type, nodes.c.sort_order, nodes.c.path, nodes.c.depth,
    nodes.c.icon, nodes.c.color, nodes.c.folder_path, nodes.c.github_repo,
    nodes.c.jira_key, nodes.c.confluence_space, nodes.c.prefix,
    nodes.c.metadata_json, nodes.c.created_at, nodes.c.updated_at,
]


# --- Endpoints ---

@router.get("/api/tree")
def get_tree():
    with get_db() as conn:
        rows = conn.execute(
            select(*_NODE_COLS).order_by(nodes.c.depth, nodes.c.sort_order)
        ).fetchall()
        node_list = [dict(r._mapping) for r in rows]
        tree = _build_tree(node_list)
        return tree


@router.get("/api/tree/unplaced")
def get_unplaced():
    """Return hub.db projects not yet placed in the tree."""
    with get_db() as conn:
        placed = conn.execute(
            select(nodes.c.hub_project_id).where(nodes.c.hub_project_id.isnot(None))
        ).fetchall()
        placed_ids = {r.hub_project_id for r in placed}

        try:
            rows = conn.execute(
                select(hub_projects.c.id, hub_projects.c.name)
                .order_by(hub_projects.c.name)
            ).fetchall()
            return [dict(r._mapping) for r in rows if r.id not in placed_ids]
        except Exception:
            return []


@router.get("/api/tree/{node_id}")
def get_node(node_id: str):
    with get_db() as conn:
        node = conn.execute(
            select(*_NODE_COLS).where(nodes.c.id == node_id)
        ).fetchone()
        if not node:
            raise HTTPException(404, "Node not found")
        result = dict(node._mapping)
        children = conn.execute(
            select(*_NODE_COLS)
            .where(nodes.c.parent_id == node_id)
            .order_by(nodes.c.sort_order)
        ).fetchall()
        result["children"] = [dict(c._mapping) for c in children]
        return result


@router.get("/api/tree/{node_id}/subtree")
def get_subtree(node_id: str):
    with get_db() as conn:
        node = conn.execute(
            select(*_NODE_COLS).where(nodes.c.id == node_id)
        ).fetchone()
        if not node:
            raise HTTPException(404, "Node not found")
        node_dict = dict(node._mapping)
        path_prefix = node_dict["path"] + "/"
        descendants = conn.execute(
            select(*_NODE_COLS)
            .where(nodes.c.path.like(path_prefix + "%"))
            .order_by(nodes.c.depth, nodes.c.sort_order)
        ).fetchall()
        all_nodes = [node_dict] + [dict(d._mapping) for d in descendants]
        tree = _build_tree(all_nodes)
        return tree[0] if tree else node_dict


@router.post("/api/tree", status_code=201)
def create_node(body: CreateNodeBody):
    import os
    if body.folder_path:
        real = os.path.realpath(os.path.expanduser(body.folder_path))
        if not real.startswith(os.path.expanduser("~")):
            raise HTTPException(400, "Folder path must be within home directory")
    with get_db() as conn:
        parent = conn.execute(
            select(nodes.c.path, nodes.c.depth).where(nodes.c.id == body.parent_id)
        ).fetchone()
        if not parent:
            raise HTTPException(400, "Parent node not found")

        new_id = str(uuid.uuid4())
        new_path = parent.path + "/" + new_id
        new_depth = parent.depth + 1

        conn.execute(
            insert(nodes).values(
                id=new_id, parent_id=body.parent_id, hub_project_id=body.hub_project_id,
                label=body.label, node_type=body.node_type, sort_order=body.sort_order,
                path=new_path, depth=new_depth, icon=body.icon, color=body.color,
                folder_path=body.folder_path, github_repo=body.github_repo,
                jira_key=body.jira_key, confluence_space=body.confluence_space,
            )
        )

        # Auto-spawn default agents for project and team nodes
        spawned_agents = []
        if body.node_type in ("project", "team"):
            role_rows = conn.execute(
                select(
                    agent_roles.c.slug, agent_roles.c.name,
                    agent_roles.c.default_model, agent_roles.c.default_system_prompt,
                ).order_by(agent_roles.c.sort_order)
            ).fetchall()
            for role in role_rows:
                agent_id = str(uuid.uuid4())
                conn.execute(
                    insert(agents).values(
                        id=agent_id, name=role.name, node_id=new_id,
                        model=role.default_model, role=role.slug,
                        system_prompt=role.default_system_prompt, status="idle",
                    )
                )
                spawned_agents.append(agent_id)

        row = conn.execute(
            select(*_NODE_COLS).where(nodes.c.id == new_id)
        ).fetchone()
        result = dict(row._mapping)

        if spawned_agents:
            agent_rows = conn.execute(
                select(agents).where(agents.c.id.in_(spawned_agents))
            ).fetchall()
            result["agents"] = [dict(a._mapping) for a in agent_rows]

    event_bus.emit("tree.changed", {"action": "created", "node_id": new_id, "label": body.label})
    return result


@router.patch("/api/tree/{node_id}")
def patch_node(node_id: str, body: PatchNodeBody):
    import os
    if body.folder_path:
        real = os.path.realpath(os.path.expanduser(body.folder_path))
        if not real.startswith(os.path.expanduser("~")):
            raise HTTPException(400, "Folder path must be within home directory")
    with get_db() as conn:
        existing = conn.execute(
            select(nodes.c.id).where(nodes.c.id == node_id)
        ).fetchone()
        if not existing:
            raise HTTPException(404, "Node not found")

        updates = {}
        # Map model field names to DB column names (metadata -> metadata_json)
        field_map = {
            "label": "label", "node_type": "node_type", "icon": "icon",
            "color": "color", "folder_path": "folder_path",
            "github_repo": "github_repo", "jira_key": "jira_key",
            "confluence_space": "confluence_space", "prefix": "prefix",
            "metadata": "metadata_json", "sort_order": "sort_order",
        }
        for model_field, db_col in field_map.items():
            if model_field in body.model_fields_set:
                updates[db_col] = getattr(body, model_field)

        if not updates:
            raise HTTPException(400, "No fields to update")

        conn.execute(
            update(nodes)
            .where(nodes.c.id == node_id)
            .values(**updates, updated_at=text("datetime('now')"))
        )

        row = conn.execute(
            select(*_NODE_COLS).where(nodes.c.id == node_id)
        ).fetchone()
        result = dict(row._mapping)

    event_bus.emit("tree.changed", {"action": "updated", "node_id": node_id})
    return result


@router.delete("/api/tree/{node_id}")
def delete_node(node_id: str):
    if node_id == "root":
        raise HTTPException(400, "Cannot delete root node")

    with get_db() as conn:
        existing = conn.execute(
            select(nodes.c.id).where(nodes.c.id == node_id)
        ).fetchone()
        if not existing:
            raise HTTPException(404, "Node not found")

        children = conn.execute(
            select(nodes.c.id).where(nodes.c.parent_id == node_id)
        ).fetchone()
        if children:
            raise HTTPException(400, "Cannot delete node with children. Remove or move children first.")

        agent_rows = conn.execute(
            select(agents.c.id).where(agents.c.node_id == node_id)
        ).fetchall()
        agent_ids = [r.id for r in agent_rows]

        if agent_ids:
            conn.execute(
                delete(comments).where(comments.c.entity_id.in_(agent_ids))
            )
        conn.execute(delete(cost_ledger).where(cost_ledger.c.node_id == node_id))
        conn.execute(delete(budgets).where(budgets.c.node_id == node_id))
        conn.execute(delete(project_context).where(project_context.c.node_id == node_id))
        conn.execute(delete(handoffs).where(handoffs.c.node_id == node_id))
        conn.execute(delete(workflows).where(workflows.c.node_id == node_id))
        conn.execute(delete(analysis_jobs).where(analysis_jobs.c.node_id == node_id))

        conn.execute(delete(agents).where(agents.c.node_id == node_id))
        conn.execute(delete(goals).where(goals.c.node_id == node_id))
        conn.execute(delete(tasks).where(tasks.c.node_id == node_id))
        conn.execute(delete(nodes).where(nodes.c.id == node_id))

    event_bus.emit("tree.changed", {"action": "deleted", "node_id": node_id})
    return {"ok": True}


@router.post("/api/tree/{node_id}/move")
def move_node(node_id: str, body: MoveNodeBody):
    if node_id == "root":
        raise HTTPException(400, "Cannot move root node")

    with get_db() as conn:
        node = conn.execute(
            select(nodes.c.id, nodes.c.path, nodes.c.depth).where(nodes.c.id == node_id)
        ).fetchone()
        if not node:
            raise HTTPException(404, "Node not found")

        new_parent = conn.execute(
            select(nodes.c.id, nodes.c.path, nodes.c.depth).where(nodes.c.id == body.new_parent_id)
        ).fetchone()
        if not new_parent:
            raise HTTPException(400, "New parent node not found")

        if new_parent.path.startswith(node.path + "/") or new_parent.id == node_id:
            raise HTTPException(400, "Cannot move a node under itself")

        old_path = node.path
        new_path = new_parent.path + "/" + node_id
        new_depth = new_parent.depth + 1
        depth_diff = new_depth - node.depth

        sort_order_val = body.sort_order if body.sort_order is not None else 0
        conn.execute(
            update(nodes)
            .where(nodes.c.id == node_id)
            .values(parent_id=body.new_parent_id, path=new_path, depth=new_depth,
                    sort_order=sort_order_val, updated_at=text("datetime('now')"))
        )

        descendants = conn.execute(
            select(nodes.c.id, nodes.c.path, nodes.c.depth)
            .where(nodes.c.path.like(old_path + "/%"))
        ).fetchall()
        for desc in descendants:
            desc_new_path = new_path + desc.path[len(old_path):]
            desc_new_depth = desc.depth + depth_diff
            conn.execute(
                update(nodes)
                .where(nodes.c.id == desc.id)
                .values(path=desc_new_path, depth=desc_new_depth, updated_at=text("datetime('now')"))
            )

        row = conn.execute(
            select(*_NODE_COLS).where(nodes.c.id == node_id)
        ).fetchone()
        result = dict(row._mapping)

    event_bus.emit("tree.changed", {"action": "moved", "node_id": node_id})
    return result


@router.post("/api/tree/reorder")
def reorder_nodes(items: list[ReorderItem]):
    with get_db() as conn:
        for item in items:
            conn.execute(
                update(nodes)
                .where(nodes.c.id == item.id)
                .values(sort_order=item.sort_order, updated_at=text("datetime('now')"))
            )

    event_bus.emit("tree.changed", {"action": "reordered"})
    return {"ok": True}


@router.get("/api/tree/{node_id}/folder")
def get_folder_contents(node_id: str):
    """Return folder listing for a node's linked folder_path."""
    import os
    with get_db() as conn:
        row = conn.execute(
            select(nodes.c.folder_path).where(nodes.c.id == node_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Node not found")
        folder_path = row.folder_path
        if not folder_path or not os.path.isdir(folder_path):
            return {"path": folder_path, "exists": False, "files": []}

        home = os.path.expanduser("~")
        real_path = os.path.realpath(folder_path)
        if not real_path.startswith(home):
            return {"path": folder_path, "exists": False, "files": [], "error": "Path outside home directory"}

        files = []
        try:
            for entry in sorted(os.scandir(folder_path), key=lambda e: (not e.is_dir(), e.name.lower())):
                if entry.name.startswith('.'):
                    continue
                stat = entry.stat()
                files.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if not entry.is_dir() else None,
                    "modified": stat.st_mtime,
                })
        except PermissionError:
            pass

        return {"path": folder_path, "exists": True, "files": files[:50]}


@router.get("/api/filesystem/browse")
def browse_filesystem(path: str = "~"):
    """Browse local filesystem directories for the folder picker."""
    import os
    resolved = os.path.expanduser(path)
    home = os.path.expanduser("~")
    resolved = os.path.realpath(resolved)
    if not resolved.startswith(home):
        raise HTTPException(403, "Cannot browse outside home directory")
    if not os.path.isdir(resolved):
        return {"path": resolved, "exists": False, "dirs": [], "parent": None}

    parent = os.path.dirname(resolved) if resolved != "/" else None
    dirs = []
    try:
        for entry in sorted(os.scandir(resolved), key=lambda e: e.name.lower()):
            if entry.name.startswith('.'):
                continue
            if entry.is_dir():
                dirs.append({"name": entry.name, "path": entry.path})
    except PermissionError:
        pass

    return {"path": resolved, "exists": True, "dirs": dirs[:100], "parent": parent}
