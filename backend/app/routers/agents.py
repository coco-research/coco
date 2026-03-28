import uuid
from fastapi import APIRouter, HTTPException
from app.db.connections import get_platform_db
from app.db.tree_utils import build_node_id_filter
from app.services.process_manager import process_manager
from app.services.collaboration_context import build_collaboration_prompt
from app.services.event_bus import event_bus
from app.models.agents import (
    CreateAgentBody,
    CreateRoleBody,
    PatchAgentBody,
    RecruitAgentBody,
    SpawnAgentBody,
)

router = APIRouter(tags=["Agents"])


@router.get("/api/agents")
def list_agents(
    project_id: str | None = None,
    node_id: str | None = None,
    subtree: bool = False,
):
    with get_platform_db() as db:
        conditions: list[str] = []
        params: list[str] = []

        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)

        node_frag, node_params = build_node_id_filter(db, node_id, subtree)
        if node_frag:
            conditions.append(node_frag)
            params.extend(node_params)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = db.execute(
            f"SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents{where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


@router.get("/api/agents/org-chart")
def get_org_chart(
    project_id: str | None = None,
    node_id: str | None = None,
):
    """Return agents structured as a tree based on reports_to relationships."""
    with get_platform_db() as db:
        conditions: list[str] = []
        params: list[str] = []

        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)
        if node_id:
            conditions.append("node_id = ?")
            params.append(node_id)

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = db.execute(
            f"SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents{where} ORDER BY created_at ASC",
            params,
        ).fetchall()
        agents = [dict(r) for r in rows]

    # Build tree: group by reports_to
    agent_map = {a["id"]: {**a, "children": []} for a in agents}
    roots: list[dict] = []

    for a in agents:
        node = agent_map[a["id"]]
        parent_id = a.get("reports_to")
        if parent_id and parent_id in agent_map:
            agent_map[parent_id]["children"].append(node)
        else:
            roots.append(node)

    # Auto-detect hierarchy: if no reports_to set, infer from roles
    # Product Manager is the root, others report to them
    if len(roots) == len(agents) and len(agents) > 1:
        # Find the PM / lead
        lead = None
        role_priority = ["product-manager", "project-manager"]
        for role in role_priority:
            for a in agents:
                if a.get("role") == role:
                    lead = agent_map[a["id"]]
                    break
            if lead:
                break

        if lead:
            roots = [lead]
            for a in agents:
                if a["id"] != lead["id"]:
                    lead["children"].append(agent_map[a["id"]])

    return roots


@router.post("/api/agents", status_code=201)
def create_agent(body: CreateAgentBody):
    agent_id = str(uuid.uuid4())
    with get_platform_db() as db:
        db.execute(
            """INSERT INTO agents (id, name, project_id, node_id, model, role, system_prompt, task_description, reports_to)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent_id,
                body.name,
                body.project_id,
                body.node_id,
                body.model,
                body.role,
                body.system_prompt,
                body.task_description,
                body.reports_to,
            ),
        )
        db.commit()
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        return dict(row)


@router.get("/api/agents/{agent_id}")
def get_agent(agent_id: str):
    with get_platform_db() as db:
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        agent = dict(row)
        # Include recent output
        output_rows = db.execute(
            """SELECT stream, chunk, timestamp FROM agent_output
               WHERE agent_id = ? ORDER BY timestamp DESC LIMIT 50""",
            (agent_id,),
        ).fetchall()
        agent["recent_output"] = [dict(r) for r in reversed(output_rows)]
        return agent


@router.patch("/api/agents/{agent_id}")
def update_agent(agent_id: str, body: PatchAgentBody):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    if not updates:
        raise HTTPException(400, "No valid fields to update")

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [agent_id]

    with get_platform_db() as db:
        result = db.execute(
            f"UPDATE agents SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(404, "Agent not found")
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        return dict(row)


@router.delete("/api/agents/{agent_id}")
def delete_agent(agent_id: str):
    with get_platform_db() as db:
        row = db.execute("SELECT status FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        if row["status"] == "running":
            raise HTTPException(409, "Cannot delete a running agent")
        db.execute("DELETE FROM agent_output WHERE agent_id = ?", (agent_id,))
        db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
        db.commit()
        return {"status": "deleted", "agent_id": agent_id}


@router.post("/api/agents/{agent_id}/spawn")
def spawn_agent(agent_id: str, body: SpawnAgentBody | None = None):
    with get_platform_db() as db:
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        agent = dict(row)

        if agent["status"] == "running":
            raise HTTPException(409, "Agent is already running")

        task = (body.task if body else None) or agent.get("task_description")
        if not task:
            raise HTTPException(400, "No task specified and no task_description on agent")

        # Inject collaboration context if this agent is part of a team workflow
        node_id = agent.get("node_id")
        role = agent.get("role", "custom")
        if node_id:
            collab_ctx = build_collaboration_prompt(node_id, role)
            if collab_ctx:
                task = collab_ctx + "\n\n---\n\n" + task

        model = agent.get("model", "sonnet")
        cwd = agent.get("working_directory")

        try:
            pid = process_manager.spawn(agent_id, task, cwd=cwd, model=model, node_id=node_id, role=role)
        except RuntimeError as e:
            raise HTTPException(429, str(e))

        db.execute(
            """UPDATE agents SET status = 'running', pid = ?, started_at = datetime('now'),
               stopped_at = NULL, exit_code = NULL, last_heartbeat = datetime('now'),
               updated_at = datetime('now') WHERE id = ?""",
            (pid, agent_id),
        )
        db.commit()
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        result = dict(row)

    event_bus.emit("agent.spawned", {"agent_id": agent_id, "name": result.get("name"), "pid": pid})
    return result


@router.post("/api/agents/{agent_id}/pause")
def pause_agent(agent_id: str):
    with get_platform_db() as db:
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        if row["status"] != "running":
            raise HTTPException(409, "Agent is not running")

        process_manager.pause(agent_id)

        db.execute(
            "UPDATE agents SET status = 'paused', updated_at = datetime('now') WHERE id = ?",
            (agent_id,),
        )
        db.commit()
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        result = dict(row)

    event_bus.emit("agent.paused", {"agent_id": agent_id, "name": result.get("name")})
    return result


@router.post("/api/agents/{agent_id}/resume")
def resume_agent(agent_id: str):
    with get_platform_db() as db:
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        if row["status"] != "paused":
            raise HTTPException(409, "Agent is not paused")

        process_manager.resume(agent_id)

        db.execute(
            "UPDATE agents SET status = 'running', updated_at = datetime('now') WHERE id = ?",
            (agent_id,),
        )
        db.commit()
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        result = dict(row)

    event_bus.emit("agent.resumed", {"agent_id": agent_id, "name": result.get("name")})
    return result


@router.post("/api/agents/{agent_id}/kill")
def kill_agent(agent_id: str):
    with get_platform_db() as db:
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        if row["status"] not in ("running", "paused"):
            raise HTTPException(409, "Agent is not running or paused")

        process_manager.kill(agent_id)

        db.execute(
            """UPDATE agents SET status = 'killed', stopped_at = datetime('now'),
               updated_at = datetime('now') WHERE id = ?""",
            (agent_id,),
        )
        db.commit()
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        result = dict(row)

    event_bus.emit("agent.killed", {"agent_id": agent_id, "name": result.get("name")})
    return result


@router.get("/api/agent-roles")
def list_roles():
    with get_platform_db() as db:
        rows = db.execute(
            "SELECT slug, name, default_system_prompt, default_model, sort_order "
            "FROM agent_roles ORDER BY sort_order"
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/api/agent-roles", status_code=201)
def create_role(body: CreateRoleBody):
    with get_platform_db() as db:
        existing = db.execute("SELECT slug FROM agent_roles WHERE slug = ?", (body.slug,)).fetchone()
        if existing:
            raise HTTPException(409, "Role with this slug already exists")

        db.execute(
            "INSERT INTO agent_roles (slug, name, default_system_prompt, default_model, sort_order) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                body.slug,
                body.name,
                body.default_system_prompt,
                body.default_model,
                body.sort_order,
            ),
        )
        db.commit()
        row = db.execute("SELECT slug, name, default_system_prompt, default_model, sort_order FROM agent_roles WHERE slug = ?", (body.slug,)).fetchone()
        return dict(row)


@router.post("/api/agents/recruit", status_code=201)
def recruit_agent(body: RecruitAgentBody):
    with get_platform_db() as db:
        role = db.execute(
            "SELECT slug, name, default_system_prompt, default_model FROM agent_roles WHERE slug = ?",
            (body.role_slug,),
        ).fetchone()
        if not role:
            raise HTTPException(404, "Role not found")

        agent_id = str(uuid.uuid4())
        agent_name = body.name or role["name"]
        agent_model = body.model or role["default_model"]
        agent_prompt = body.system_prompt or role["default_system_prompt"]

        db.execute(
            "INSERT INTO agents (id, name, node_id, model, role, system_prompt, status) "
            "VALUES (?, ?, ?, ?, ?, ?, 'idle')",
            (agent_id, agent_name, body.node_id, agent_model, role["slug"], agent_prompt),
        )
        db.commit()
        row = db.execute("SELECT id, name, node_id, project_id, model, role, status, task_description, system_prompt, working_directory, pid, started_at, stopped_at, last_heartbeat, exit_code, config, reports_to, created_at, updated_at FROM agents WHERE id = ?", (agent_id,)).fetchone()
        return dict(row)


@router.get("/api/agents/{agent_id}/logs")
def get_agent_logs(agent_id: str, limit: int = 100, after_id: int = 0):
    with get_platform_db() as db:
        row = db.execute("SELECT id FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")

        rows = db.execute(
            """SELECT id, stream, chunk, timestamp FROM agent_output
               WHERE agent_id = ? AND id > ?
               ORDER BY id ASC LIMIT ?""",
            (agent_id, after_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
