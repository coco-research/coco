import uuid
from fastapi import APIRouter, HTTPException
import structlog

from app.db.connections import get_platform_db, get_hub_db
from app.services.event_bus import event_bus
from app.models.tree import CreateNodeBody, MoveNodeBody, PatchNodeBody, ReorderItem

log = structlog.get_logger()
router = APIRouter(tags=["Tree"])


# --- Helpers ---

def _row_to_dict(row) -> dict:
    return dict(row) if row else None


def _build_tree(nodes: list[dict]) -> list[dict]:
    """Build nested tree structure from flat list of node dicts."""
    by_id = {}
    for n in nodes:
        n["children"] = []
        by_id[n["id"]] = n

    roots = []
    for n in nodes:
        pid = n.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(n)
        else:
            roots.append(n)

    return roots


# --- Endpoints ---

@router.get("/api/tree")
def get_tree():
    with get_platform_db() as db:
        rows = db.execute(
            "SELECT id, parent_id, hub_project_id, label, node_type, "
            "sort_order, path, depth, icon, color, folder_path, github_repo, "
            "jira_key, confluence_space, metadata, created_at, updated_at "
            "FROM nodes ORDER BY depth, sort_order"
        ).fetchall()
        nodes = [dict(r) for r in rows]
        tree = _build_tree(nodes)
        return tree


@router.get("/api/tree/unplaced")
def get_unplaced():
    """Return hub.db projects not yet placed in the tree."""
    with get_platform_db() as pdb:
        placed = pdb.execute(
            "SELECT hub_project_id FROM nodes WHERE hub_project_id IS NOT NULL"
        ).fetchall()
        placed_ids = {r["hub_project_id"] for r in placed}

    try:
        with get_hub_db() as hdb:
            rows = hdb.execute("SELECT id, name FROM projects ORDER BY name").fetchall()
            return [dict(r) for r in rows if r["id"] not in placed_ids]
    except Exception:
        return []


@router.get("/api/tree/{node_id}")
def get_node(node_id: str):
    with get_platform_db() as db:
        node = db.execute(
            "SELECT id, parent_id, hub_project_id, label, node_type, "
            "sort_order, path, depth, icon, color, folder_path, github_repo, "
            "jira_key, confluence_space, metadata, created_at, updated_at "
            "FROM nodes WHERE id = ?",
            (node_id,),
        ).fetchone()
        if not node:
            raise HTTPException(404, "Node not found")
        result = dict(node)
        children = db.execute(
            "SELECT id, parent_id, hub_project_id, label, node_type, "
            "sort_order, path, depth, icon, color, folder_path, github_repo, "
            "jira_key, confluence_space, metadata, created_at, updated_at "
            "FROM nodes WHERE parent_id = ? ORDER BY sort_order",
            (node_id,),
        ).fetchall()
        result["children"] = [dict(c) for c in children]
        return result


@router.get("/api/tree/{node_id}/subtree")
def get_subtree(node_id: str):
    with get_platform_db() as db:
        node = db.execute(
            "SELECT id, parent_id, hub_project_id, label, node_type, "
            "sort_order, path, depth, icon, color, folder_path, github_repo, "
            "jira_key, confluence_space, metadata, created_at, updated_at "
            "FROM nodes WHERE id = ?",
            (node_id,),
        ).fetchone()
        if not node:
            raise HTTPException(404, "Node not found")
        node_dict = dict(node)
        path_prefix = node_dict["path"] + "/"
        descendants = db.execute(
            "SELECT id, parent_id, hub_project_id, label, node_type, "
            "sort_order, path, depth, icon, color, folder_path, github_repo, "
            "jira_key, confluence_space, metadata, created_at, updated_at "
            "FROM nodes WHERE path LIKE ? ORDER BY depth, sort_order",
            (path_prefix + "%",),
        ).fetchall()
        all_nodes = [node_dict] + [dict(d) for d in descendants]
        tree = _build_tree(all_nodes)
        # Return the root of the subtree (should be exactly one)
        return tree[0] if tree else node_dict


@router.post("/api/tree", status_code=201)
def create_node(body: CreateNodeBody):
    import os
    if body.folder_path:
        real = os.path.realpath(os.path.expanduser(body.folder_path))
        if not real.startswith(os.path.expanduser("~")):
            raise HTTPException(400, "Folder path must be within home directory")
    with get_platform_db() as db:
        parent = db.execute("SELECT path, depth FROM nodes WHERE id = ?", (body.parent_id,)).fetchone()
        if not parent:
            raise HTTPException(400, "Parent node not found")

        new_id = str(uuid.uuid4())
        new_path = parent["path"] + "/" + new_id
        new_depth = parent["depth"] + 1

        db.execute(
            "INSERT INTO nodes (id, parent_id, hub_project_id, label, node_type, sort_order, path, depth, icon, color, folder_path, github_repo, jira_key, confluence_space) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (new_id, body.parent_id, body.hub_project_id, body.label, body.node_type,
             body.sort_order, new_path, new_depth, body.icon, body.color, body.folder_path,
             body.github_repo, body.jira_key, body.confluence_space),
        )

        # Auto-spawn default agents for project and team nodes
        spawned_agents = []
        if body.node_type in ("project", "team"):
            roles = db.execute(
                "SELECT slug, name, default_model, default_system_prompt FROM agent_roles ORDER BY sort_order"
            ).fetchall()
            for role in roles:
                agent_id = str(uuid.uuid4())
                db.execute(
                    "INSERT INTO agents (id, name, node_id, model, role, system_prompt, status) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'idle')",
                    (agent_id, role["name"], new_id, role["default_model"],
                     role["slug"], role["default_system_prompt"]),
                )
                spawned_agents.append(agent_id)

        db.commit()

        row = db.execute(
            "SELECT id, parent_id, hub_project_id, label, node_type, "
            "sort_order, path, depth, icon, color, folder_path, github_repo, "
            "jira_key, confluence_space, metadata, created_at, updated_at "
            "FROM nodes WHERE id = ?",
            (new_id,),
        ).fetchone()
        result = dict(row)

        if spawned_agents:
            agents = db.execute(
                f"SELECT * FROM agents WHERE id IN ({','.join('?' for _ in spawned_agents)})",
                spawned_agents,
            ).fetchall()
            result["agents"] = [dict(a) for a in agents]

    event_bus.emit("tree.changed", {"action": "created", "node_id": new_id, "label": body.label})
    return result


@router.patch("/api/tree/{node_id}")
def patch_node(node_id: str, body: PatchNodeBody):
    import os
    if body.folder_path:
        real = os.path.realpath(os.path.expanduser(body.folder_path))
        if not real.startswith(os.path.expanduser("~")):
            raise HTTPException(400, "Folder path must be within home directory")
    with get_platform_db() as db:
        existing = db.execute("SELECT id FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if not existing:
            raise HTTPException(404, "Node not found")

        updates = []
        params = []
        for field in ("label", "node_type", "icon", "color", "folder_path", "github_repo", "jira_key", "confluence_space", "metadata", "sort_order"):
            if field in body.model_fields_set:
                val = getattr(body, field)
                updates.append(f"{field} = ?")
                params.append(val)

        if not updates:
            raise HTTPException(400, "No fields to update")

        updates.append("updated_at = datetime('now')")
        params.append(node_id)

        db.execute(
            f"UPDATE nodes SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        db.commit()

        row = db.execute(
            "SELECT id, parent_id, hub_project_id, label, node_type, "
            "sort_order, path, depth, icon, color, folder_path, github_repo, "
            "jira_key, confluence_space, metadata, created_at, updated_at "
            "FROM nodes WHERE id = ?",
            (node_id,),
        ).fetchone()
        result = dict(row)

    event_bus.emit("tree.changed", {"action": "updated", "node_id": node_id})
    return result


@router.delete("/api/tree/{node_id}")
def delete_node(node_id: str):
    if node_id == "root":
        raise HTTPException(400, "Cannot delete root node")

    with get_platform_db() as db:
        existing = db.execute("SELECT id FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if not existing:
            raise HTTPException(404, "Node not found")

        children = db.execute("SELECT id FROM nodes WHERE parent_id = ?", (node_id,)).fetchone()
        if children:
            raise HTTPException(400, "Cannot delete node with children. Remove or move children first.")

        # Collect agent IDs for cascading deletes on child tables
        agent_rows = db.execute("SELECT id FROM agents WHERE node_id = ?", (node_id,)).fetchall()
        agent_ids = [r["id"] for r in agent_rows]

        # Cascade: delete records referencing this node or its agents
        if agent_ids:
            placeholders = ",".join("?" for _ in agent_ids)
            db.execute(f"DELETE FROM comments WHERE entity_id IN ({placeholders})", agent_ids)
        db.execute("DELETE FROM cost_ledger WHERE node_id = ?", (node_id,))
        db.execute("DELETE FROM budgets WHERE node_id = ?", (node_id,))
        db.execute("DELETE FROM project_context WHERE node_id = ?", (node_id,))
        db.execute("DELETE FROM handoffs WHERE node_id = ?", (node_id,))
        db.execute("DELETE FROM workflows WHERE node_id = ?", (node_id,))
        db.execute("DELETE FROM analysis_jobs WHERE node_id = ?", (node_id,))

        db.execute("DELETE FROM agents WHERE node_id = ?", (node_id,))
        db.execute("DELETE FROM goals WHERE node_id = ?", (node_id,))
        db.execute("DELETE FROM tasks WHERE node_id = ?", (node_id,))
        db.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        db.commit()

    event_bus.emit("tree.changed", {"action": "deleted", "node_id": node_id})
    return {"ok": True}


@router.post("/api/tree/{node_id}/move")
def move_node(node_id: str, body: MoveNodeBody):
    if node_id == "root":
        raise HTTPException(400, "Cannot move root node")

    with get_platform_db() as db:
        node = db.execute("SELECT id, path, depth FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if not node:
            raise HTTPException(404, "Node not found")

        new_parent = db.execute("SELECT id, path, depth FROM nodes WHERE id = ?", (body.new_parent_id,)).fetchone()
        if not new_parent:
            raise HTTPException(400, "New parent node not found")

        # Prevent moving a node under itself
        if new_parent["path"].startswith(node["path"] + "/") or new_parent["id"] == node_id:
            raise HTTPException(400, "Cannot move a node under itself")

        old_path = node["path"]
        new_path = new_parent["path"] + "/" + node_id
        new_depth = new_parent["depth"] + 1
        depth_diff = new_depth - node["depth"]

        # Update the node itself
        sort_order_val = body.sort_order if body.sort_order is not None else 0
        db.execute(
            "UPDATE nodes SET parent_id = ?, path = ?, depth = ?, sort_order = ?, updated_at = datetime('now') "
            "WHERE id = ?",
            (body.new_parent_id, new_path, new_depth, sort_order_val, node_id),
        )

        # Update all descendants: replace old_path prefix with new_path, adjust depth
        descendants = db.execute(
            "SELECT id, path, depth FROM nodes WHERE path LIKE ?",
            (old_path + "/%",),
        ).fetchall()
        for desc in descendants:
            desc_new_path = new_path + desc["path"][len(old_path):]
            desc_new_depth = desc["depth"] + depth_diff
            db.execute(
                "UPDATE nodes SET path = ?, depth = ?, updated_at = datetime('now') WHERE id = ?",
                (desc_new_path, desc_new_depth, desc["id"]),
            )

        db.commit()

        row = db.execute(
            "SELECT id, parent_id, hub_project_id, label, node_type, "
            "sort_order, path, depth, icon, color, folder_path, github_repo, "
            "jira_key, confluence_space, metadata, created_at, updated_at "
            "FROM nodes WHERE id = ?",
            (node_id,),
        ).fetchone()
        result = dict(row)

    event_bus.emit("tree.changed", {"action": "moved", "node_id": node_id})
    return result


@router.post("/api/tree/reorder")
def reorder_nodes(items: list[ReorderItem]):
    with get_platform_db() as db:
        for item in items:
            db.execute(
                "UPDATE nodes SET sort_order = ?, updated_at = datetime('now') WHERE id = ?",
                (item.sort_order, item.id),
            )
        db.commit()

    event_bus.emit("tree.changed", {"action": "reordered"})
    return {"ok": True}


@router.get("/api/tree/{node_id}/folder")
def get_folder_contents(node_id: str):
    """Return folder listing for a node's linked folder_path."""
    import os
    with get_platform_db() as db:
        row = db.execute("SELECT folder_path FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Node not found")
        folder_path = row[0]
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
    resolved = os.path.realpath(resolved)  # resolve symlinks
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
