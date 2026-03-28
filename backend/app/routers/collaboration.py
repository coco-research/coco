import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import insert, select, update, delete

from app.db.session import get_db
from app.db.compat import now
from app.db.tables import project_context, handoffs, workflows, workflow_templates
from app.services.verification import verification_service
from app.models.collaboration import (
    CreateContextBody,
    CreateHandoffBody,
    PatchContextBody,
    PatchHandoffBody,
    PatchWorkflowBody,
    StartWorkflowBody,
)

router = APIRouter(tags=["Collaboration"])


# ---------------------------------------------------------------------------
# Project Context endpoints
# ---------------------------------------------------------------------------

@router.get("/api/nodes/{node_id}/context")
def list_context(node_id: str):
    with get_db() as conn:
        rows = conn.execute(
            select(project_context)
            .where(project_context.c.node_id == node_id)
            .order_by(project_context.c.created_at)
        ).fetchall()
        return [dict(r._mapping) for r in rows]


@router.post("/api/nodes/{node_id}/context", status_code=201)
def create_context(node_id: str, body: CreateContextBody):
    context_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            insert(project_context).values(
                id=context_id,
                node_id=node_id,
                section=body.section,
                title=body.title,
                content=body.content,
                author_agent_id=body.author_agent_id,
                author_role=body.author_role,
            )
        )
        row = conn.execute(
            select(project_context).where(project_context.c.id == context_id)
        ).fetchone()
        return dict(row._mapping)


@router.patch("/api/context/{context_id}")
def update_context(context_id: str, body: PatchContextBody):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    if not updates:
        raise HTTPException(400, "No valid fields to update")

    values = dict(updates)
    values["updated_at"] = now()
    if "content" in updates:
        values["version"] = project_context.c.version + 1

    with get_db() as conn:
        result = conn.execute(
            update(project_context)
            .where(project_context.c.id == context_id)
            .values(**values)
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Context section not found")
        row = conn.execute(
            select(project_context).where(project_context.c.id == context_id)
        ).fetchone()
        return dict(row._mapping)


@router.delete("/api/context/{context_id}", status_code=204)
def delete_context(context_id: str):
    with get_db() as conn:
        result = conn.execute(
            delete(project_context).where(project_context.c.id == context_id)
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Context section not found")
        return None


# ---------------------------------------------------------------------------
# Handoff endpoints
# ---------------------------------------------------------------------------

@router.get("/api/nodes/{node_id}/handoffs")
def list_handoffs(node_id: str, status: str | None = None):
    with get_db() as conn:
        stmt = select(handoffs).where(handoffs.c.node_id == node_id)
        if status:
            stmt = stmt.where(handoffs.c.status == status)
        stmt = stmt.order_by(handoffs.c.created_at.desc())
        rows = conn.execute(stmt).fetchall()
        return [dict(r._mapping) for r in rows]


@router.post("/api/handoffs", status_code=201)
def create_handoff(body: CreateHandoffBody):
    handoff_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            insert(handoffs).values(
                id=handoff_id,
                node_id=body.node_id,
                workflow_id=body.workflow_id,
                from_agent_id=body.from_agent_id,
                from_role=body.from_role,
                to_role=body.to_role,
                title=body.title,
                description=body.description,
            )
        )
        row = conn.execute(
            select(handoffs).where(handoffs.c.id == handoff_id)
        ).fetchone()
        return dict(row._mapping)


@router.patch("/api/handoffs/{handoff_id}")
def update_handoff(handoff_id: str, body: PatchHandoffBody):
    valid_statuses = ("pending", "in_progress", "completed", "rejected", "skipped")
    if body.status not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid_statuses}")

    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        row = conn.execute(
            select(handoffs).where(handoffs.c.id == handoff_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Handoff not found")
        row_map = row._mapping

        extra_vals = {}
        if body.status == "in_progress" and not row_map["accepted_at"]:
            extra_vals["accepted_at"] = now
        if body.status in ("completed", "rejected", "skipped") and not row_map["completed_at"]:
            extra_vals["completed_at"] = now

        conn.execute(
            update(handoffs)
            .where(handoffs.c.id == handoff_id)
            .values(status=body.status, **extra_vals)
        )
        row = conn.execute(
            select(handoffs).where(handoffs.c.id == handoff_id)
        ).fetchone()
        return dict(row._mapping)


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------

@router.get("/api/workflow-templates")
def list_workflow_templates():
    with get_db() as conn:
        rows = conn.execute(
            select(workflow_templates).order_by(workflow_templates.c.name)
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r._mapping)
            d["steps"] = json.loads(d["steps"])
            results.append(d)
        return results


@router.post("/api/nodes/{node_id}/workflows", status_code=201)
def start_workflow(node_id: str, body: StartWorkflowBody):
    with get_db() as conn:
        template = conn.execute(
            select(workflow_templates).where(workflow_templates.c.id == body.template_id)
        ).fetchone()
        if not template:
            raise HTTPException(404, "Workflow template not found")

        tmpl = template._mapping
        steps = json.loads(tmpl["steps"])
        workflow_id = str(uuid.uuid4())

        conn.execute(
            insert(workflows).values(
                id=workflow_id,
                node_id=node_id,
                template_name=tmpl["name"],
                objective=body.objective,
                steps=json.dumps(steps),
                current_step=0,
                status="active",
            )
        )

        first_step = steps[0]
        handoff_id = str(uuid.uuid4())
        conn.execute(
            insert(handoffs).values(
                id=handoff_id,
                node_id=node_id,
                workflow_id=workflow_id,
                from_agent_id="system",
                from_role="system",
                to_role=first_step["role"],
                title=f"{tmpl['name']}: {first_step['action']}",
                description=body.objective,
            )
        )

        row = conn.execute(
            select(workflows).where(workflows.c.id == workflow_id)
        ).fetchone()
        result = dict(row._mapping)
        result["steps"] = json.loads(result["steps"])
        result["current_step_info"] = steps[0]
        return result


@router.get("/api/nodes/{node_id}/workflows/active")
def get_active_workflow(node_id: str):
    with get_db() as conn:
        row = conn.execute(
            select(workflows)
            .where(workflows.c.node_id == node_id, workflows.c.status == "active")
            .order_by(workflows.c.created_at.desc())
            .limit(1)
        ).fetchone()
        if not row:
            raise HTTPException(404, "No active workflow found")

        result = dict(row._mapping)
        steps = json.loads(result["steps"])
        result["steps"] = steps
        current = result["current_step"]
        if 0 <= current < len(steps):
            result["current_step_info"] = steps[current]
        else:
            result["current_step_info"] = None
        return result


@router.patch("/api/workflows/{workflow_id}")
def update_workflow(workflow_id: str, body: PatchWorkflowBody):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    if not updates:
        raise HTTPException(400, "No valid fields to update")

    if "status" in updates:
        valid = ("active", "completed", "paused", "cancelled")
        if updates["status"] not in valid:
            raise HTTPException(400, f"Invalid status. Must be one of: {valid}")

    updates["updated_at"] = now()

    with get_db() as conn:
        result = conn.execute(
            update(workflows)
            .where(workflows.c.id == workflow_id)
            .values(**updates)
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Workflow not found")
        row = conn.execute(
            select(workflows).where(workflows.c.id == workflow_id)
        ).fetchone()
        d = dict(row._mapping)
        d["steps"] = json.loads(d["steps"])
        return d


@router.post("/api/workflows/{workflow_id}/advance", status_code=200)
def advance_workflow(workflow_id: str):
    with get_db() as conn:
        row = conn.execute(
            select(workflows).where(workflows.c.id == workflow_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Workflow not found")
        wf = row._mapping
        if wf["status"] != "active":
            raise HTTPException(400, "Workflow is not active")

        steps = json.loads(wf["steps"])
        next_step = wf["current_step"] + 1

        if next_step >= len(steps):
            conn.execute(
                update(workflows)
                .where(workflows.c.id == workflow_id)
                .values(status="completed", current_step=next_step, updated_at=now())
            )
            result = dict(conn.execute(
                select(workflows).where(workflows.c.id == workflow_id)
            ).fetchone()._mapping)
            result["steps"] = json.loads(result["steps"])
            result["current_step_info"] = None
            return result

        step_info = steps[next_step]
        prev_step = steps[wf["current_step"]]

        handoff_id = str(uuid.uuid4())
        conn.execute(
            insert(handoffs).values(
                id=handoff_id,
                node_id=wf["node_id"],
                workflow_id=workflow_id,
                from_agent_id="system",
                from_role=prev_step["role"],
                to_role=step_info["role"],
                title=f"{wf['template_name']}: {step_info['action']}",
                description=wf["objective"],
            )
        )

        conn.execute(
            update(workflows)
            .where(workflows.c.id == workflow_id)
            .values(current_step=next_step, updated_at=now())
        )

        result = dict(conn.execute(
            select(workflows).where(workflows.c.id == workflow_id)
        ).fetchone()._mapping)
        result["steps"] = json.loads(result["steps"])
        result["current_step_info"] = step_info
        return result


# ---------------------------------------------------------------------------
# Verification Gate endpoints
# ---------------------------------------------------------------------------

@router.post("/api/workflows/{workflow_id}/verify", tags=["Collaboration"])
def verify_workflow_step(workflow_id: str, body: dict):
    """Run a verification gate on a workflow step."""
    gate_name = body.get("gate", "G3_implementation")
    input_data = body.get("input_data", {})
    output_data = body.get("output_data", {})

    with get_db() as conn:
        row = conn.execute(
            select(workflows.c.node_id).where(workflows.c.id == workflow_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Workflow not found")
        node_id = row._mapping["node_id"]

    result = verification_service.run_gate(
        gate_name=gate_name,
        input_data=input_data,
        output_data=output_data,
        node_id=node_id,
        entity_type="workflow",
        entity_id=workflow_id,
    )
    return result.to_dict()


@router.get("/api/verification/history", tags=["Collaboration"])
def get_verification_history(entity_type: str | None = None, entity_id: str | None = None,
                             node_id: str | None = None, limit: int = 20):
    """Retrieve verification gate history."""
    return verification_service.get_history(entity_type, entity_id, node_id, limit)
