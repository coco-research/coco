import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from app.db.connections import get_platform_db
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
    with get_platform_db() as db:
        rows = db.execute(
            "SELECT * FROM project_context WHERE node_id = ? ORDER BY created_at",
            (node_id,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/api/nodes/{node_id}/context", status_code=201)
def create_context(node_id: str, body: CreateContextBody):
    context_id = str(uuid.uuid4())
    with get_platform_db() as db:
        db.execute(
            """INSERT INTO project_context
               (id, node_id, section, title, content, author_agent_id, author_role)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                context_id,
                node_id,
                body.section,
                body.title,
                body.content,
                body.author_agent_id,
                body.author_role,
            ),
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM project_context WHERE id = ?", (context_id,)
        ).fetchone()
        return dict(row)


@router.patch("/api/context/{context_id}")
def update_context(context_id: str, body: PatchContextBody):
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    if not updates:
        raise HTTPException(400, "No valid fields to update")

    # Bump version on content change
    version_bump = ", version = version + 1" if "content" in updates else ""
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [context_id]

    with get_platform_db() as db:
        result = db.execute(
            f"UPDATE project_context SET {set_clause}{version_bump}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(404, "Context section not found")
        row = db.execute(
            "SELECT * FROM project_context WHERE id = ?", (context_id,)
        ).fetchone()
        return dict(row)


@router.delete("/api/context/{context_id}", status_code=204)
def delete_context(context_id: str):
    with get_platform_db() as db:
        result = db.execute(
            "DELETE FROM project_context WHERE id = ?", (context_id,)
        )
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(404, "Context section not found")
        return None


# ---------------------------------------------------------------------------
# Handoff endpoints
# ---------------------------------------------------------------------------

@router.get("/api/nodes/{node_id}/handoffs")
def list_handoffs(node_id: str, status: str | None = None):
    conditions = ["node_id = ?"]
    params: list = [node_id]

    if status:
        conditions.append("status = ?")
        params.append(status)

    where = " WHERE " + " AND ".join(conditions)
    with get_platform_db() as db:
        rows = db.execute(
            f"SELECT * FROM handoffs{where} ORDER BY created_at DESC",
            params,
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/api/handoffs", status_code=201)
def create_handoff(body: CreateHandoffBody):
    handoff_id = str(uuid.uuid4())
    with get_platform_db() as db:
        db.execute(
            """INSERT INTO handoffs
               (id, node_id, workflow_id, from_agent_id, from_role, to_role, title, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                handoff_id,
                body.node_id,
                body.workflow_id,
                body.from_agent_id,
                body.from_role,
                body.to_role,
                body.title,
                body.description,
            ),
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM handoffs WHERE id = ?", (handoff_id,)
        ).fetchone()
        return dict(row)


@router.patch("/api/handoffs/{handoff_id}")
def update_handoff(handoff_id: str, body: PatchHandoffBody):
    valid_statuses = ("pending", "in_progress", "completed", "rejected", "skipped")
    if body.status not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid_statuses}")

    now = datetime.now(timezone.utc).isoformat()
    with get_platform_db() as db:
        row = db.execute(
            "SELECT * FROM handoffs WHERE id = ?", (handoff_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Handoff not found")

        extra_sets = ""
        extra_params: list = []

        if body.status == "in_progress" and not row["accepted_at"]:
            extra_sets = ", accepted_at = ?"
            extra_params.append(now)

        if body.status in ("completed", "rejected", "skipped") and not row["completed_at"]:
            extra_sets += ", completed_at = ?"
            extra_params.append(now)

        db.execute(
            f"UPDATE handoffs SET status = ?{extra_sets} WHERE id = ?",
            [body.status] + extra_params + [handoff_id],
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM handoffs WHERE id = ?", (handoff_id,)
        ).fetchone()
        return dict(row)


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------

@router.get("/api/workflow-templates")
def list_workflow_templates():
    with get_platform_db() as db:
        rows = db.execute(
            "SELECT * FROM workflow_templates ORDER BY name"
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["steps"] = json.loads(d["steps"])
            results.append(d)
        return results


@router.post("/api/nodes/{node_id}/workflows", status_code=201)
def start_workflow(node_id: str, body: StartWorkflowBody):
    with get_platform_db() as db:
        template = db.execute(
            "SELECT * FROM workflow_templates WHERE id = ?", (body.template_id,)
        ).fetchone()
        if not template:
            raise HTTPException(404, "Workflow template not found")

        steps = json.loads(template["steps"])
        workflow_id = str(uuid.uuid4())

        db.execute(
            """INSERT INTO workflows
               (id, node_id, template_name, objective, steps, current_step, status)
               VALUES (?, ?, ?, ?, ?, 0, 'active')""",
            (
                workflow_id,
                node_id,
                template["name"],
                body.objective,
                json.dumps(steps),
            ),
        )

        # Create the first handoff
        first_step = steps[0]
        handoff_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO handoffs
               (id, node_id, workflow_id, from_agent_id, from_role, to_role, title, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                handoff_id,
                node_id,
                workflow_id,
                "system",
                "system",
                first_step["role"],
                f"{template['name']}: {first_step['action']}",
                body.objective,
            ),
        )

        db.commit()

        row = db.execute(
            "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
        ).fetchone()
        result = dict(row)
        result["steps"] = json.loads(result["steps"])
        result["current_step_info"] = steps[0]
        return result


@router.get("/api/nodes/{node_id}/workflows/active")
def get_active_workflow(node_id: str):
    with get_platform_db() as db:
        row = db.execute(
            "SELECT * FROM workflows WHERE node_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (node_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "No active workflow found")

        result = dict(row)
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

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [workflow_id]

    with get_platform_db() as db:
        result = db.execute(
            f"UPDATE workflows SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        db.commit()
        if result.rowcount == 0:
            raise HTTPException(404, "Workflow not found")
        row = db.execute(
            "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
        ).fetchone()
        d = dict(row)
        d["steps"] = json.loads(d["steps"])
        return d


@router.post("/api/workflows/{workflow_id}/advance", status_code=200)
def advance_workflow(workflow_id: str):
    with get_platform_db() as db:
        row = db.execute(
            "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Workflow not found")
        if row["status"] != "active":
            raise HTTPException(400, "Workflow is not active")

        steps = json.loads(row["steps"])
        next_step = row["current_step"] + 1

        if next_step >= len(steps):
            # Workflow complete
            db.execute(
                "UPDATE workflows SET status = 'completed', current_step = ?, updated_at = datetime('now') WHERE id = ?",
                (next_step, workflow_id),
            )
            db.commit()
            result = dict(
                db.execute(
                    "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
                ).fetchone()
            )
            result["steps"] = json.loads(result["steps"])
            result["current_step_info"] = None
            return result

        step_info = steps[next_step]
        prev_step = steps[row["current_step"]]

        # Create handoff for next step
        handoff_id = str(uuid.uuid4())
        db.execute(
            """INSERT INTO handoffs
               (id, node_id, workflow_id, from_agent_id, from_role, to_role, title, description)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                handoff_id,
                row["node_id"],
                workflow_id,
                "system",
                prev_step["role"],
                step_info["role"],
                f"{row['template_name']}: {step_info['action']}",
                row["objective"],
            ),
        )

        db.execute(
            "UPDATE workflows SET current_step = ?, updated_at = datetime('now') WHERE id = ?",
            (next_step, workflow_id),
        )
        db.commit()

        result = dict(
            db.execute(
                "SELECT * FROM workflows WHERE id = ?", (workflow_id,)
            ).fetchone()
        )
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

    # Get node_id from workflow
    with get_platform_db() as db:
        row = db.execute("SELECT node_id FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Workflow not found")
        node_id = row["node_id"]

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
