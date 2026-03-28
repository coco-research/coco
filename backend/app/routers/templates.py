"""Project Export/Import (Templates) router."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, insert, delete, text

from app.db.session import get_db
from app.db.tables import (
    hub_projects, hub_todos,
    nodes, agents, goals, tasks, templates, agent_roles,
)
from app.models.templates import ImportTemplateBody, SaveTemplateBody

router = APIRouter(tags=["Templates"])

TEMPLATE_VERSION = 1
TEMPLATE_TYPE = "coco-project-template"


# -- Helpers --

def _strip_ids_and_timestamps(row: dict, keep_fields: set[str] | None = None) -> dict:
    skip = {"id", "created_at", "updated_at", "started_at", "stopped_at",
            "last_heartbeat", "pid", "exit_code", "checked_out_by", "checked_out_at"}
    if keep_fields:
        skip -= keep_fields
    return {k: v for k, v in row.items() if k not in skip}


def _export_project_data(project_id: str, node_id: str | None) -> dict:
    result: dict = {}

    with get_db() as conn:
        # Get project metadata from hub mirror
        try:
            proj = conn.execute(
                select(hub_projects.c.id, hub_projects.c.name, hub_projects.c.jira_key, hub_projects.c.confluence_space)
                .where(hub_projects.c.id == project_id)
            ).fetchone()
            if proj:
                result["project"] = {
                    "name": proj.name,
                    "jira_key": proj.jira_key,
                    "confluence_space": proj.confluence_space,
                }
        except Exception:
            result["project"] = {"name": "Imported Project"}

        # Agents
        agent_rows = conn.execute(
            select(agents.c.name, agents.c.model, agents.c.role,
                   agents.c.system_prompt, agents.c.task_description, agents.c.config)
            .where((agents.c.node_id == (node_id or "")) | (agents.c.project_id == project_id))
        ).fetchall()
        result["agents"] = [dict(r._mapping) for r in agent_rows]

        # Goals
        all_goals = conn.execute(
            select(goals.c.id, goals.c.title, goals.c.description, goals.c.status,
                   goals.c.progress_pct, goals.c.owner, goals.c.target_date, goals.c.parent_id)
            .where(goals.c.project_id == project_id)
            .order_by(goals.c.created_at)
        ).fetchall()
        goal_id_to_idx: dict[str, int] = {}
        exported_goals = []
        for idx, g in enumerate(all_goals):
            goal_id_to_idx[g.id] = idx
            exported_goals.append({
                "title": g.title,
                "description": g.description,
                "status": "active",
                "progress_pct": 0,
                "owner": g.owner,
                "target_date": g.target_date,
                "parent_index": None,
            })
        for idx, g in enumerate(all_goals):
            if g.parent_id and g.parent_id in goal_id_to_idx:
                exported_goals[idx]["parent_index"] = goal_id_to_idx[g.parent_id]
        result["goals"] = exported_goals

        # Tasks
        task_rows = conn.execute(
            select(tasks.c.title, tasks.c.description, tasks.c.priority)
            .where(tasks.c.project_id == project_id)
        ).fetchall()
        result["tasks"] = [dict(r._mapping) for r in task_rows]

        # Tree structure
        if node_id:
            node_row = conn.execute(
                select(nodes.c.label, nodes.c.node_type, nodes.c.icon, nodes.c.color,
                       nodes.c.folder_path, nodes.c.github_repo, nodes.c.jira_key,
                       nodes.c.confluence_space, nodes.c.metadata_json)
                .where(nodes.c.id == node_id)
            ).fetchone()
            result["node"] = dict(node_row._mapping) if node_row else None

            child_rows = conn.execute(
                select(nodes.c.label, nodes.c.node_type, nodes.c.sort_order,
                       nodes.c.icon, nodes.c.color, nodes.c.folder_path,
                       nodes.c.github_repo, nodes.c.jira_key, nodes.c.confluence_space,
                       nodes.c.metadata_json)
                .where(nodes.c.parent_id == node_id)
                .order_by(nodes.c.sort_order)
            ).fetchall()
            result["child_nodes"] = [dict(r._mapping) for r in child_rows]
        else:
            result["node"] = None
            result["child_nodes"] = []

        # Todos from hub mirror
        try:
            todo_rows = conn.execute(
                select(hub_todos.c.title, hub_todos.c.priority, hub_todos.c.owner, hub_todos.c.due_date)
                .where(hub_todos.c.project_id == project_id)
            ).fetchall()
            result["todos"] = [dict(r._mapping) for r in todo_rows]
        except Exception:
            result["todos"] = []

    return result


# -- Export --

@router.get("/api/projects/{project_id}/export")
def export_project(project_id: str):
    """Export a project as a reusable template JSON."""
    node_id: str | None = None
    with get_db() as conn:
        node = conn.execute(
            select(nodes.c.id).where(nodes.c.hub_project_id == project_id)
        ).fetchone()
        if node:
            node_id = node.id

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


# -- Import --

@router.post("/api/projects/import", status_code=201)
def import_project(body: ImportTemplateBody):
    """Import a template to create a new project with all associated entities."""
    tpl = body.template

    if tpl.get("type") != TEMPLATE_TYPE:
        raise HTTPException(400, f"Invalid template type. Expected '{TEMPLATE_TYPE}'")
    if not isinstance(tpl.get("version"), int) or tpl["version"] > TEMPLATE_VERSION:
        raise HTTPException(400, f"Unsupported template version: {tpl.get('version')}")
    if not tpl.get("project"):
        raise HTTPException(400, "Template is missing project data")

    project_name = body.project_name or tpl["project"].get("name", "Imported Project")
    now = datetime.now(timezone.utc).isoformat()

    with get_db() as conn:
        parent = conn.execute(
            select(nodes.c.id, nodes.c.path, nodes.c.depth).where(nodes.c.id == body.parent_node_id)
        ).fetchone()
        if not parent:
            raise HTTPException(400, "Parent node not found")

        new_node_id = str(uuid.uuid4())
        node_data = tpl.get("node") or {}
        new_path = parent.path + "/" + new_node_id
        new_depth = parent.depth + 1

        conn.execute(
            insert(nodes).values(
                id=new_node_id, parent_id=body.parent_node_id, label=project_name,
                node_type=node_data.get("node_type", "project"), sort_order=0,
                path=new_path, depth=new_depth,
                icon=node_data.get("icon"), color=node_data.get("color"),
                folder_path=None,
                github_repo=node_data.get("github_repo"),
                jira_key=node_data.get("jira_key") or tpl["project"].get("jira_key"),
                confluence_space=node_data.get("confluence_space") or tpl["project"].get("confluence_space"),
                metadata_json=node_data.get("metadata_json", "{}"),
            )
        )

        # Create child nodes
        child_node_ids: list[str] = []
        for child in tpl.get("child_nodes", []):
            child_id = str(uuid.uuid4())
            child_path = new_path + "/" + child_id
            child_depth = new_depth + 1
            conn.execute(
                insert(nodes).values(
                    id=child_id, parent_id=new_node_id,
                    label=child.get("label", "Untitled"),
                    node_type=child.get("node_type", "group"),
                    sort_order=child.get("sort_order", 0),
                    path=child_path, depth=child_depth,
                    icon=child.get("icon"), color=child.get("color"),
                    folder_path=None,
                    github_repo=child.get("github_repo"),
                    jira_key=child.get("jira_key"),
                    confluence_space=child.get("confluence_space"),
                    metadata_json=child.get("metadata_json", "{}"),
                )
            )
            child_node_ids.append(child_id)

        # Create agents
        agent_ids: list[str] = []
        for agent in tpl.get("agents", []):
            agent_id = str(uuid.uuid4())
            conn.execute(
                insert(agents).values(
                    id=agent_id, name=agent.get("name", "Agent"), node_id=new_node_id,
                    model=agent.get("model", "sonnet"), role=agent.get("role", "custom"),
                    system_prompt=agent.get("system_prompt"),
                    task_description=agent.get("task_description"),
                    config=agent.get("config", "{}"), status="idle",
                )
            )
            agent_ids.append(agent_id)

        # Create goals
        goal_ids: list[str] = []
        for goal in tpl.get("goals", []):
            goal_id = str(uuid.uuid4())
            parent_goal_id = None
            pi = goal.get("parent_index")
            if pi is not None and 0 <= pi < len(goal_ids):
                parent_goal_id = goal_ids[pi]

            conn.execute(
                insert(goals).values(
                    id=goal_id, project_id=None, parent_id=parent_goal_id,
                    title=goal.get("title", "Goal"), description=goal.get("description"),
                    status="active", progress_pct=0,
                    owner=goal.get("owner"), target_date=goal.get("target_date"),
                    created_at=now, updated_at=now,
                )
            )
            goal_ids.append(goal_id)

        # Create tasks
        task_ids: list[str] = []
        for task in tpl.get("tasks", []):
            task_id = str(uuid.uuid4())
            conn.execute(
                insert(tasks).values(
                    id=task_id, title=task.get("title", "Task"),
                    description=task.get("description"), node_id=new_node_id,
                    priority=task.get("priority", "medium"), status="open",
                )
            )
            task_ids.append(task_id)

    return {
        "node_id": new_node_id,
        "project_name": project_name,
        "agents_created": len(agent_ids),
        "goals_created": len(goal_ids),
        "tasks_created": len(task_ids),
        "child_nodes_created": len(child_node_ids),
    }


# -- Template Library --

@router.get("/api/templates")
def list_templates():
    with get_db() as conn:
        rows = conn.execute(
            select(templates.c.id, templates.c.name, templates.c.description, templates.c.created_at)
            .order_by(templates.c.created_at.desc())
        ).fetchall()
        return [dict(r._mapping) for r in rows]


@router.get("/api/templates/{template_id}")
def get_template(template_id: str):
    with get_db() as conn:
        row = conn.execute(
            select(templates.c.id, templates.c.name, templates.c.description,
                   templates.c.template_json, templates.c.created_at)
            .where(templates.c.id == template_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Template not found")
        result = dict(row._mapping)
        result["template"] = json.loads(result.pop("template_json"))
        return result


@router.post("/api/templates", status_code=201)
def save_template(body: SaveTemplateBody):
    tpl = body.template
    if tpl.get("type") != TEMPLATE_TYPE:
        raise HTTPException(400, f"Invalid template type. Expected '{TEMPLATE_TYPE}'")

    template_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            insert(templates).values(
                id=template_id, name=body.name,
                description=body.description, template_json=json.dumps(tpl),
            )
        )
    return {"id": template_id, "name": body.name}


@router.delete("/api/templates/{template_id}")
def delete_template(template_id: str):
    with get_db() as conn:
        result = conn.execute(
            delete(templates).where(templates.c.id == template_id)
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Template not found")
    return {"status": "deleted", "id": template_id}
