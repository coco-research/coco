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
    ResumeFromCheckpointBody,
    SpawnAgentBody,
    SpawnSubagentBody,
)
from app.services.agent_session_store import (
    get_session as get_agent_session,
    save_session,
    update_checkpoint,
)
from app.services.subagent_manager import (
    spawn_subagent,
    list_subagents,
    kill_subagent,
)

router = APIRouter(tags=["Agents"])

_AGENT_COLS = (
    "id, name, node_id, project_id, model, role, status, task_description, "
    "system_prompt, working_directory, pid, started_at, stopped_at, "
    "last_heartbeat, exit_code, config, reports_to, human_id, created_at, updated_at"
)


def _agent_row_to_dict(row) -> dict:
    out = dict(row._mapping)
    # human_id is the user-facing identifier; UUID `id` stays secondary.
    if out.get("human_id"):
        out["display_id"] = out["human_id"]
    return out


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
        agents_out = [_agent_row_to_dict(r) for r in rows]

        # Attach lifetime cost per agent from cost_ledger
        if agents_out:
            ids = [a["id"] for a in agents_out]
            placeholders = ",".join(["?"] * len(ids))
            cost_rows = conn.exec_driver_sql(
                f"SELECT agent_id, COALESCE(SUM(cost_usd), 0.0) AS total "
                f"FROM cost_ledger WHERE agent_id IN ({placeholders}) GROUP BY agent_id",
                tuple(ids),
            ).fetchall()
            cost_by_agent = {r._mapping["agent_id"]: float(r._mapping["total"] or 0.0) for r in cost_rows}
            for a in agents_out:
                a["lifetime_cost_usd"] = cost_by_agent.get(a["id"], 0.0)

        return agents_out


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


@router.post("/api/agents/fix-hierarchy")
def fix_hierarchy(node_id: str | None = None):
    """Repair reports_to for all agents (or one node) based on DEFAULT_HIERARCHY.

    Sets reports_to for agents whose role is in the default hierarchy but
    who currently have no reports_to set. Does not overwrite existing
    relationships.
    """
    with get_db() as conn:
        if node_id:
            node_ids = [node_id]
        else:
            rows = conn.exec_driver_sql(
                "SELECT DISTINCT node_id FROM agents WHERE node_id IS NOT NULL"
            ).fetchall()
            node_ids = [r.node_id for r in rows]

        fixed = 0
        for nid in node_ids:
            agents_in_node = conn.exec_driver_sql(
                "SELECT id, role, reports_to FROM agents WHERE node_id = ?", (nid,)
            ).fetchall()

            role_to_id: dict[str, str] = {}
            for a in agents_in_node:
                if a.role:
                    role_to_id[a.role] = a.id

            for a in agents_in_node:
                if a.reports_to:
                    continue  # already has a hierarchy
                parent_role = DEFAULT_HIERARCHY.get(a.role)
                if parent_role is None:
                    continue  # root role, no parent needed
                parent_id = role_to_id.get(parent_role)
                if parent_id:
                    conn.exec_driver_sql(
                        "UPDATE agents SET reports_to = ? WHERE id = ?",
                        (parent_id, a.id),
                    )
                    fixed += 1

        return {"fixed": fixed, "nodes_checked": len(node_ids)}


@router.post("/api/agents", status_code=201)
def create_agent(body: CreateAgentBody):
    from app.services.id_generator import assign_display_id

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

    # Mint a human_id (writeback to agents.human_id happens inside the helper).
    try:
        assign_display_id(agent_id, body.node_id or body.project_id, entity_type="agent")
    except Exception:
        pass

    with get_db() as conn:
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


# ---------------------------------------------------------------------------
# Default org chart hierarchy — defines reports_to relationships
# ---------------------------------------------------------------------------

# Maps role_slug -> parent role_slug. Root roles have None.
DEFAULT_HIERARCHY: dict[str, str | None] = {
    "chief-of-staff": None,                       # root
    "product-manager": "chief-of-staff",
    "project-manager": "chief-of-staff",
    "technical-architect": "chief-of-staff",
    "qa-reviewer": "chief-of-staff",
    "communications-specialist": "chief-of-staff",
    "developer": "technical-architect",
    "user-researcher": "product-manager",
    "data-analyst": "product-manager",
    "scribe": "project-manager",
}


def _resolve_reports_to(conn, node_id: str, role_slug: str) -> str | None:
    """Find the agent ID this role should report to, based on DEFAULT_HIERARCHY."""
    parent_role = DEFAULT_HIERARCHY.get(role_slug)
    if not parent_role:
        return None
    row = conn.exec_driver_sql(
        "SELECT id FROM agents WHERE node_id = ? AND role = ? LIMIT 1",
        (node_id, parent_role),
    ).fetchone()
    return row.id if row else None


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
        reports_to = _resolve_reports_to(conn, body.node_id, role._mapping["slug"])

        conn.execute(
            insert(agents).values(
                id=agent_id,
                name=agent_name,
                node_id=body.node_id,
                model=agent_model,
                role=role._mapping["slug"],
                system_prompt=agent_prompt,
                status="idle",
                reports_to=reports_to,
            )
        )

    # Mint a human_id outside the transaction so we re-fetch with it populated.
    try:
        from app.services.id_generator import assign_display_id
        assign_display_id(agent_id, body.node_id, entity_type="agent")
    except Exception:
        pass

    with get_db() as conn:
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


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.get("/api/agents/{agent_id}/session")
def get_session(agent_id: str):
    """Return SDK session metadata for an agent."""
    with get_db() as conn:
        row = conn.exec_driver_sql(
            "SELECT id FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")

    session = get_agent_session(agent_id)
    if not session:
        raise HTTPException(404, "No active session for this agent")
    return session


@router.post("/api/agents/{agent_id}/resume-checkpoint")
def resume_from_checkpoint(agent_id: str, body: ResumeFromCheckpointBody | None = None):
    """Resume an agent from its last checkpoint.

    Optionally provide new checkpoint_data or a follow-up task.
    """
    with get_db() as conn:
        row = conn.exec_driver_sql(
            f"SELECT {_AGENT_COLS} FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
        agent = _agent_row_to_dict(row)

    # Get existing session
    session = get_agent_session(agent_id)
    if not session:
        raise HTTPException(404, "No session to resume from")

    # Update checkpoint if provided
    if body and body.checkpoint_data:
        update_checkpoint(agent_id, body.checkpoint_data)
        session = get_agent_session(agent_id)

    # Build resume task from checkpoint context
    checkpoint = session.get("checkpoint_data", {})
    original_task = agent.get("task_description", "")
    resume_task = body.task if (body and body.task) else None

    if not resume_task:
        resume_task = (
            f"Resume from checkpoint. Original task: {original_task}\n"
            f"Messages so far: {session.get('message_count', 0)}\n"
            f"Checkpoint context: {checkpoint}"
        )

    # Spawn the agent with the resume task
    from app.services.process_manager import process_manager  # noqa: lazy import (cycle)
    node_id = agent.get("node_id")
    role = agent.get("role", "custom")
    model = agent.get("model", "sonnet")
    cwd = agent.get("working_directory")

    try:
        pid = process_manager.spawn(
            agent_id, resume_task, cwd=cwd, model=model,
            node_id=node_id, role=role,
        )
    except RuntimeError as e:
        raise HTTPException(429, str(e))

    with get_db() as conn:
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

    event_bus.emit("agent.resumed", {"agent_id": agent_id, "name": result.get("name"), "pid": pid})
    return {"agent": result, "session": get_agent_session(agent_id)}


# ---------------------------------------------------------------------------
# Subagent endpoints
# ---------------------------------------------------------------------------


@router.get("/api/agents/{agent_id}/subagents")
def get_subagents(agent_id: str):
    """List all child agents of a parent."""
    with get_db() as conn:
        row = conn.exec_driver_sql(
            "SELECT id FROM agents WHERE id = ?", (agent_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
    return list_subagents(agent_id)


@router.post("/api/agents/{agent_id}/subagents", status_code=201)
def create_subagent(agent_id: str, body: SpawnSubagentBody):
    """Spawn a child agent under a parent. Max 3 active subagents."""
    try:
        child = spawn_subagent(
            parent_id=agent_id,
            task=body.task,
            model=body.model,
            role=body.role,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    event_bus.emit("agent.subagent_spawned", {
        "parent_id": agent_id,
        "child_id": child["id"],
        "child_name": child.get("name"),
    })
    return child


@router.delete("/api/agents/{agent_id}/subagents/{subagent_id}")
def delete_subagent(agent_id: str, subagent_id: str):
    """Kill a specific subagent."""
    try:
        result = kill_subagent(subagent_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # Verify it belongs to the specified parent
    if result.get("reports_to") != agent_id:
        raise HTTPException(400, f"Subagent {subagent_id} does not belong to agent {agent_id}")

    event_bus.emit("agent.subagent_killed", {
        "parent_id": agent_id,
        "child_id": subagent_id,
    })
    return result
