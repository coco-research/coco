import uuid
from fastapi import APIRouter, HTTPException
from sqlalchemy import insert, select, update, delete, text
from app.db.session import get_db
from app.db.tables import agents, agent_roles, agent_output
from app.db.tree_utils import build_node_id_filter
from app.services.process_manager import process_manager
from app.services.collaboration_context import build_collaboration_prompt, build_coco_context, build_yolo_constraints
from app.services.event_bus import event_bus
from app.models.agents import (
    CreateAgentBody,
    CreateRoleBody,
    PatchAgentBody,
    RecruitAgentBody,
    SpawnAgentBody,
)

router = APIRouter(tags=["Agents"])

_AGENT_COLS = (
    "id, name, node_id, project_id, model, role, status, task_description, "
    "system_prompt, working_directory, pid, started_at, stopped_at, "
    "last_heartbeat, exit_code, config, reports_to, created_at, updated_at"
)


def _agent_row_to_dict(row) -> dict:
    return dict(row._mapping)


@router.get("/api/agents")
def list_agents(
    project_id: str | None = None,
    node_id: str | None = None,
    subtree: bool = False,
):
    with get_db() as conn:
        conditions: list[str] = []
        params: list[str] = []

        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)

        node_frag, node_params = build_node_id_filter(conn, node_id, subtree)
        if node_frag:
            conditions.append(node_frag)
            params.extend(node_params)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents{where} ORDER BY created_at DESC",
            tuple(params),
        ).fetchall()
        return [_agent_row_to_dict(r) for r in rows]


@router.get("/api/agents/org-chart")
def get_org_chart(
    project_id: str | None = None,
    node_id: str | None = None,
):
    """Return agents structured as a tree based on reports_to relationships."""
    with get_db() as conn:
        conditions: list[str] = []
        params: list[str] = []

        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if node_id:
            conditions.append("node_id = ?")
            params.append(node_id)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents{where} ORDER BY created_at ASC",
            tuple(params),
        ).fetchall()
        agents_list = [_agent_row_to_dict(r) for r in rows]

    # Build tree: group by reports_to
    agent_map = {a["id"]: {**a, "children": []} for a in agents_list}
    roots: list[dict] = []

    for a in agents_list:
        node = agent_map[a["id"]]
        parent_id = a.get("reports_to")
        if parent_id and parent_id in agent_map:
            agent_map[parent_id]["children"].append(node)
        else:
            roots.append(node)

    if len(roots) == len(agents_list) and len(agents_list) > 1:
        lead = None
        role_priority = ["product-manager", "project-manager"]
        for role in role_priority:
            for a in agents_list:
                if a.get("role") == role:
                    lead = agent_map[a["id"]]
                    break
            if lead:
                break

        if lead:
            roots = [lead]
            for a in agents_list:
                if a["id"] != lead["id"]:
                    lead["children"].append(agent_map[a["id"]])

    return roots


@router.post("/api/agents", status_code=201)
def create_agent(body: CreateAgentBody):
    agent_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            insert(agents).values(
                id=agent_id,
                name=body.name,
                project_id=body.project_id,
                node_id=body.node_id,
                model=body.model,
                role=body.role,
                system_prompt=body.system_prompt,
                task_description=body.task_description,
                reports_to=body.reports_to,
            )
        )
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        return _agent_row_to_dict(row)


@router.get("/api/agents/{agent_id}")
def get_agent(agent_id: str):
    with get_db() as conn:
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        agent = _agent_row_to_dict(row)
        output_rows = conn.exec_driver_sql(
            "SELECT stream, chunk, timestamp FROM agent_output "
            "WHERE agent_id = ? ORDER BY timestamp DESC LIMIT 50",
            (agent_id,),
        ).fetchall()
        agent["recent_output"] = [dict(r._mapping) for r in reversed(output_rows)]
        return agent


@router.patch("/api/agents/{agent_id}")
def update_agent(agent_id: str, body: PatchAgentBody):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    if not updates:
        raise HTTPException(400, "No valid fields to update")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [agent_id]

    with get_db() as conn:
        result = conn.exec_driver_sql(
            f"UPDATE agents SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            tuple(values),
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Agent not found")
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        return _agent_row_to_dict(row)


@router.delete("/api/agents/{agent_id}")
def delete_agent(agent_id: str):
    with get_db() as conn:
        row = conn.exec_driver_sql(
            "SELECT status FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        if row._mapping["status"] == "running":
            raise HTTPException(409, "Cannot delete a running agent")
        conn.execute(delete(agent_output).where(agent_output.c.agent_id == agent_id))
        conn.execute(delete(agents).where(agents.c.id == agent_id))
        return {"status": "deleted", "agent_id": agent_id}


@router.post("/api/agents/{agent_id}/spawn")
def spawn_agent(agent_id: str, body: SpawnAgentBody | None = None):
    with get_db() as conn:
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        agent = _agent_row_to_dict(row)

        if agent["status"] == "running":
            raise HTTPException(409, "Agent is already running")

        task = (body.task if body else None) or agent.get("task_description")
        if not task:
            raise HTTPException(400, "No task specified and no task_description on agent")

        node_id = agent.get("node_id")
        role = agent.get("role", "custom")
        yolo_mode = body.yolo_mode if body else False

        if node_id:
            collab_ctx = build_collaboration_prompt(node_id, role)
            if collab_ctx:
                task = collab_ctx + "\n\n---\n\n" + task

        model = agent.get("model", "sonnet")
        cwd = agent.get("working_directory")

        try:
            pid = process_manager.spawn(
                agent_id, task, cwd=cwd, model=model,
                node_id=node_id, role=role, yolo_mode=yolo_mode,
            )
        except RuntimeError as e:
            raise HTTPException(429, str(e))

        conn.exec_driver_sql(
            "UPDATE agents SET status = 'running', pid = ?, started_at = datetime('now'), "
            "stopped_at = NULL, exit_code = NULL, last_heartbeat = datetime('now'), "
            "updated_at = datetime('now') WHERE id = ?",
            (pid, agent_id),
        )
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        result = _agent_row_to_dict(row)

    event_bus.emit("agent.spawned", {"agent_id": agent_id, "name": result.get("name"), "pid": pid})
    return result


@router.post("/api/agents/{agent_id}/pause")
def pause_agent(agent_id: str):
    with get_db() as conn:
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        if row._mapping["status"] != "running":
            raise HTTPException(409, "Agent is not running")

        process_manager.pause(agent_id)

        conn.exec_driver_sql(
            "UPDATE agents SET status = 'paused', updated_at = datetime('now') WHERE id = ?",
            (agent_id,),
        )
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        result = _agent_row_to_dict(row)

    event_bus.emit("agent.paused", {"agent_id": agent_id, "name": result.get("name")})
    return result


@router.post("/api/agents/{agent_id}/resume")
def resume_agent(agent_id: str):
    with get_db() as conn:
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        if row._mapping["status"] != "paused":
            raise HTTPException(409, "Agent is not paused")

        process_manager.resume(agent_id)

        conn.exec_driver_sql(
            "UPDATE agents SET status = 'running', updated_at = datetime('now') WHERE id = ?",
            (agent_id,),
        )
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        result = _agent_row_to_dict(row)

    event_bus.emit("agent.resumed", {"agent_id": agent_id, "name": result.get("name")})
    return result


@router.post("/api/agents/{agent_id}/kill")
def kill_agent(agent_id: str):
    with get_db() as conn:
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        if row._mapping["status"] not in ("running", "paused"):
            raise HTTPException(409, "Agent is not running or paused")

        process_manager.kill(agent_id)

        conn.exec_driver_sql(
            "UPDATE agents SET status = 'killed', stopped_at = datetime('now'), "
            "updated_at = datetime('now') WHERE id = ?",
            (agent_id,),
        )
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        result = _agent_row_to_dict(row)

    event_bus.emit("agent.killed", {"agent_id": agent_id, "name": result.get("name")})
    return result


@router.get("/api/agent-roles")
def list_roles():
    with get_db() as conn:
        rows = conn.execute(
            select(
                agent_roles.c.slug,
                agent_roles.c.name,
                agent_roles.c.default_system_prompt,
                agent_roles.c.default_model,
                agent_roles.c.sort_order,
            ).order_by(agent_roles.c.sort_order)
        ).fetchall()
        return [dict(r._mapping) for r in rows]


@router.post("/api/agent-roles", status_code=201)
def create_role(body: CreateRoleBody):
    with get_db() as conn:
        existing = conn.execute(
            select(agent_roles.c.slug).where(agent_roles.c.slug == body.slug)
        ).fetchone()
        if existing:
            raise HTTPException(409, "Role with this slug already exists")

        conn.execute(
            insert(agent_roles).values(
                slug=body.slug,
                name=body.name,
                default_system_prompt=body.default_system_prompt,
                default_model=body.default_model,
                sort_order=body.sort_order,
            )
        )
        row = conn.execute(
            select(
                agent_roles.c.slug,
                agent_roles.c.name,
                agent_roles.c.default_system_prompt,
                agent_roles.c.default_model,
                agent_roles.c.sort_order,
            ).where(agent_roles.c.slug == body.slug)
        ).fetchone()
        return dict(row._mapping)


@router.post("/api/agents/recruit", status_code=201)
def recruit_agent(body: RecruitAgentBody):
    with get_db() as conn:
        role = conn.execute(
            select(
                agent_roles.c.slug,
                agent_roles.c.name,
                agent_roles.c.default_system_prompt,
                agent_roles.c.default_model,
            ).where(agent_roles.c.slug == body.role_slug)
        ).fetchone()
        if not role:
            raise HTTPException(404, "Role not found")

        agent_id = str(uuid.uuid4())
        agent_name = body.name or role._mapping["name"]
        agent_model = body.model or role._mapping["default_model"]
        agent_prompt = body.system_prompt or role._mapping["default_system_prompt"]

        conn.execute(
            insert(agents).values(
                id=agent_id,
                name=agent_name,
                node_id=body.node_id,
                model=agent_model,
                role=role._mapping["slug"],
                system_prompt=agent_prompt,
                status="idle",
            )
        )
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        return _agent_row_to_dict(row)


@router.get("/api/agents/{agent_id}/logs")
def get_agent_logs(agent_id: str, limit: int = 100, after_id: int = 0):
    with get_db() as conn:
        row = conn.exec_driver_sql(
            "SELECT id FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")

        rows = conn.exec_driver_sql(
            "SELECT id, stream, chunk, timestamp FROM agent_output "
            "WHERE agent_id = ? AND id > ? ORDER BY id ASC LIMIT ?",
            (agent_id, after_id, limit),
        ).fetchall()
        return [dict(r._mapping) for r in rows]
