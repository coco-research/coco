"""Project Export/Import (Templates) router.

Export a project's full configuration as a reusable template, import from
a template to create a new project, and manage a local template library.
"""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.db.connections import get_platform_db, get_hub_db
from app.models.templates import ImportTemplateBody, SaveTemplateBody

router = APIRouter(tags=["Templates"])

TEMPLATE_VERSION = 1
TEMPLATE_TYPE = "coco-project-template"


# ── Helpers ──────────────────────────────────────────────────────────

def _strip_ids_and_timestamps(row: dict, keep_fields: set[str] | None = None) -> dict:
    """Remove id/timestamp fields from a row dict, keeping only template-relevant data."""
    skip = {"id", "created_at", "updated_at", "started_at", "stopped_at",
            "last_heartbeat", "pid", "exit_code", "checked_out_by", "checked_out_at"}
    if keep_fields:
        skip -= keep_fields
    return {k: v for k, v in row.items() if k not in skip}


def _export_project_data(project_id: str, node_id: str | None) -> dict:
    """Collect all exportable data for a project/node."""
    result: dict = {}

    # Get project metadata from hub.db if available
    try:
        with get_hub_db() as hub:
            proj = hub.execute(
                "SELECT id, name, jira_key, confluence_space, active FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
            if proj:
                result["project"] = {
                    "name": dict(proj)["name"],
                    "jira_key": dict(proj).get("jira_key"),
                    "confluence_space": dict(proj).get("confluence_space"),
                }
    except Exception:
        result["project"] = {"name": "Imported Project"}

    with get_platform_db() as db:
        # Agents
        agent_rows = db.execute(
            "SELECT name, model, role, system_prompt, task_description, config "
            "FROM agents WHERE node_id = ? OR project_id = ?",
            (node_id or "", project_id),
        ).fetchall()
        result["agents"] = [dict(r) for r in agent_rows]

        # Goals
        goal_rows = db.execute(
            "SELECT title, description, status, progress_pct, owner, target_date, parent_id "
            "FROM goals WHERE project_id = ?",
            (project_id,),
        ).fetchall()
        # Need to map parent goal IDs to sequential indices for re-linking
        all_goals = db.execute(
            "SELECT id, title, description, status, progress_pct, owner, target_date, parent_id "
            "FROM goals WHERE project_id = ? ORDER BY created_at",
            (project_id,),
        ).fetchall()
        goal_id_to_idx: dict[str, int] = {}
        exported_goals = []
        for idx, g in enumerate(all_goals):
            gd = dict(g)
            goal_id_to_idx[gd["id"]] = idx
            exported_goals.append({
                "title": gd["title"],
                "description": gd["description"],
                "status": "active",
                "progress_pct": 0,
                "owner": gd["owner"],
                "target_date": gd["target_date"],
                "parent_index": None,
            })
        # Second pass: set parent_index
        for idx, g in enumerate(all_goals):
            gd = dict(g)
            if gd["parent_id"] and gd["parent_id"] in goal_id_to_idx:
                exported_goals[idx]["parent_index"] = goal_id_to_idx[gd["parent_id"]]
        result["goals"] = exported_goals

        # Tasks (reset statuses)
        task_rows = db.execute(
            "SELECT title, description, priority FROM tasks WHERE project_id = ?",
            (project_id,),
        ).fetchall()
        result["tasks"] = [dict(r) for r in task_rows]

        # Tree structure (node + children)
        if node_id:
            node_row = db.execute(
                "SELECT label, node_type, icon, color, folder_path, github_repo, "
                "jira_key, confluence_space, metadata "
                "FROM nodes WHERE id = ?",
                (node_id,),
            ).fetchone()
            result["node"] = dict(node_row) if node_row else None

            child_rows = db.execute(
                "SELECT label, node_type, sort_order, icon, color, folder_path, "
                "github_repo, jira_key, confluence_space, metadata "
                "FROM nodes WHERE parent_id = ? ORDER BY sort_order",
                (node_id,),
            ).fetchall()
            result["child_nodes"] = [dict(r) for r in child_rows]
        else:
            result["node"] = None
            result["child_nodes"] = []

        # Todos from hub.db
        try:
            with get_hub_db() as hub:
                todo_rows = hub.execute(
                    "SELECT title, priority, owner, due_date FROM todos WHERE project_id = ?",
                    (project_id,),
                ).fetchall()
                result["todos"] = [dict(r) for r in todo_rows]
        except Exception:
            result["todos"] = []

    return result


# ── Export ───────────────────────────────────────────────────────────

@router.get("/api/projects/{project_id}/export")
def export_project(project_id: str):
    """Export a project as a reusable template JSON."""
    # Find the node for this project
    node_id: str | None = None
    with get_platform_db() as db:
        node = db.execute(
            "SELECT id FROM nodes WHERE hub_project_id = ?",
            (project_id,),
        ).fetchone()
        if node:
            node_id = node["id"]

    data = _export_project_data(project_id, node_id)
    if not data.get("project"):
        raise HTTPException(404, "Project not found")

    template = {
        "version": TEMPLATE_VERSION,
        "type": TEMPLATE_TYPE,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "project": data["project"],
        "agents": data["agents"],
        "goals": data["goals"],
        "tasks": data["tasks"],
        "todos": data["todos"],
        "node": data["node"],
        "child_nodes": data["child_nodes"],
    }
    return template


# ── Import ───────────────────────────────────────────────────────────

@router.post("/api/projects/import", status_code=201)
def import_project(body: ImportTemplateBody):
    """Import a template to create a new project with all associated entities."""
    tpl = body.template

    # Validate template format
    if tpl.get("type") != TEMPLATE_TYPE:
        raise HTTPException(400, f"Invalid template type. Expected '{TEMPLATE_TYPE}'")
    if not isinstance(tpl.get("version"), int) or tpl["version"] > TEMPLATE_VERSION:
        raise HTTPException(400, f"Unsupported template version: {tpl.get('version')}")
    if not tpl.get("project"):
        raise HTTPException(400, "Template is missing project data")

    project_name = body.project_name or tpl["project"].get("name", "Imported Project")
    now = datetime.now(timezone.utc).isoformat()

    with get_platform_db() as db:
        # Verify parent node exists
        parent = db.execute(
            "SELECT id, path, depth FROM nodes WHERE id = ?",
            (body.parent_node_id,),
        ).fetchone()
        if not parent:
            raise HTTPException(400, "Parent node not found")

        # Create the tree node
        new_node_id = str(uuid.uuid4())
        node_data = tpl.get("node") or {}
        new_path = parent["path"] + "/" + new_node_id
        new_depth = parent["depth"] + 1

        db.execute(
            "INSERT INTO nodes (id, parent_id, label, node_type, sort_order, path, depth, "
            "icon, color, folder_path, github_repo, jira_key, confluence_space, metadata) "
            "VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_node_id,
                body.parent_node_id,
                project_name,
                node_data.get("node_type", "project"),
                new_path,
                new_depth,
                node_data.get("icon"),
                node_data.get("color"),
                None,  # Don't import folder_path (local to original machine)
                node_data.get("github_repo"),
                node_data.get("jira_key") or tpl["project"].get("jira_key"),
                node_data.get("confluence_space") or tpl["project"].get("confluence_space"),
                node_data.get("metadata", "{}"),
            ),
        )

        # Create child nodes
        child_node_ids: list[str] = []
        for child in tpl.get("child_nodes", []):
            child_id = str(uuid.uuid4())
            child_path = new_path + "/" + child_id
            child_depth = new_depth + 1
            db.execute(
                "INSERT INTO nodes (id, parent_id, label, node_type, sort_order, path, depth, "
                "icon, color, folder_path, github_repo, jira_key, confluence_space, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    child_id,
                    new_node_id,
                    child.get("label", "Untitled"),
                    child.get("node_type", "group"),
                    child.get("sort_order", 0),
                    child_path,
                    child_depth,
                    child.get("icon"),
                    child.get("color"),
                    None,
                    child.get("github_repo"),
                    child.get("jira_key"),
                    child.get("confluence_space"),
                    child.get("metadata", "{}"),
                ),
            )
            child_node_ids.append(child_id)

        # Create agents
        agent_ids: list[str] = []
        for agent in tpl.get("agents", []):
            agent_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO agents (id, name, node_id, model, role, system_prompt, "
                "task_description, config, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'idle')",
                (
                    agent_id,
                    agent.get("name", "Agent"),
                    new_node_id,
                    agent.get("model", "sonnet"),
                    agent.get("role", "custom"),
                    agent.get("system_prompt"),
                    agent.get("task_description"),
                    agent.get("config", "{}"),
                ),
            )
            agent_ids.append(agent_id)

        # Create goals (respecting parent_index references)
        goal_ids: list[str] = []
        for goal in tpl.get("goals", []):
            goal_id = str(uuid.uuid4())
            parent_goal_id = None
            pi = goal.get("parent_index")
            if pi is not None and 0 <= pi < len(goal_ids):
                parent_goal_id = goal_ids[pi]

            db.execute(
                "INSERT INTO goals (id, project_id, parent_id, title, description, "
                "status, progress_pct, owner, target_date, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    goal_id,
                    None,  # No hub project id for imported projects
                    parent_goal_id,
                    goal.get("title", "Goal"),
                    goal.get("description"),
                    "active",
                    0,
                    goal.get("owner"),
                    goal.get("target_date"),
                    now,
                    now,
                ),
            )
            goal_ids.append(goal_id)

        # Create tasks
        task_ids: list[str] = []
        for task in tpl.get("tasks", []):
            task_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO tasks (id, title, description, node_id, priority, status) "
                "VALUES (?, ?, ?, ?, ?, 'open')",
                (
                    task_id,
                    task.get("title", "Task"),
                    task.get("description"),
                    new_node_id,
                    task.get("priority", "medium"),
                ),
            )
            task_ids.append(task_id)

        db.commit()

    return {
        "node_id": new_node_id,
        "project_name": project_name,
        "agents_created": len(agent_ids),
        "goals_created": len(goal_ids),
        "tasks_created": len(task_ids),
        "child_nodes_created": len(child_node_ids),
    }


# ── Template Library ─────────────────────────────────────────────────

@router.get("/api/templates")
def list_templates():
    """List all saved templates."""
    with get_platform_db() as db:
        rows = db.execute(
            "SELECT id, name, description, created_at FROM templates ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


@router.get("/api/templates/{template_id}")
def get_template(template_id: str):
    """Get a single template including its full JSON."""
    with get_platform_db() as db:
        row = db.execute(
            "SELECT id, name, description, template_json, created_at FROM templates WHERE id = ?",
            (template_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "Template not found")
        result = dict(row)
        result["template"] = json.loads(result.pop("template_json"))
        return result


@router.post("/api/templates", status_code=201)
def save_template(body: SaveTemplateBody):
    """Save a template to the library."""
    tpl = body.template
    if tpl.get("type") != TEMPLATE_TYPE:
        raise HTTPException(400, f"Invalid template type. Expected '{TEMPLATE_TYPE}'")

    template_id = str(uuid.uuid4())
    with get_platform_db() as db:
        db.execute(
            "INSERT INTO templates (id, name, description, template_json) VALUES (?, ?, ?, ?)",
            (template_id, body.name, body.description, json.dumps(tpl)),
        )
        db.commit()
    return {"id": template_id, "name": body.name}


@router.delete("/api/templates/{template_id}")
def delete_template(template_id: str):
    """Remove a template from the library."""
    with get_platform_db() as db:
        result = db.execute("DELETE FROM templates WHERE id = ?", (template_id,))
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(404, "Template not found")
    return {"status": "deleted", "id": template_id}
