import logging
import uuid
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, insert
from app.db.session import get_db
from app.db.tables import hub_drafts, draft_decisions
from app.db.compat import upsert
from app.services.event_bus import event_bus

log = logging.getLogger(__name__)

router = APIRouter(tags=["Drafts"])


@router.get("/api/drafts")
def list_drafts(
    status: str | None = None,
    project_id: str | None = None,
    project_ids: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        with get_db() as conn:
            conditions = []
            if status:
                conditions.append(hub_drafts.c.status == status)
            if project_ids:
                ids = [pid.strip() for pid in project_ids.split(",") if pid.strip()]
                if ids:
                    conditions.append(hub_drafts.c.project_id.in_(ids))
            elif project_id:
                conditions.append(hub_drafts.c.project_id == project_id)

            stmt = select(hub_drafts)
            if conditions:
                stmt = stmt.where(*conditions)
            stmt = stmt.order_by(hub_drafts.c.created_at.desc()).limit(limit).offset(offset)
            rows = conn.execute(stmt).fetchall()
            drafts = [dict(r._mapping) for r in rows]

            # Overlay platform.db decisions onto hub.db drafts
            if drafts:
                draft_ids = [d["id"] for d in drafts]
                dec_rows = conn.execute(
                    select(draft_decisions.c.hub_draft_id, draft_decisions.c.status)
                    .where(draft_decisions.c.hub_draft_id.in_(draft_ids))
                ).fetchall()
                overlay = {r.hub_draft_id: r.status for r in dec_rows}

                for d in drafts:
                    if d["id"] in overlay:
                        d["status"] = overlay[d["id"]]

            # Apply status filter post-overlay if needed
            if status and drafts:
                drafts = [d for d in drafts if d["status"] == status]

            return drafts
    except Exception:
        return []


@router.get("/api/drafts/{draft_id}")
def get_draft(draft_id: str):
    try:
        with get_db() as conn:
            row = conn.execute(
                select(hub_drafts).where(hub_drafts.c.id == draft_id)
            ).fetchone()
            if not row:
                raise HTTPException(404, "Draft not found")
            draft = dict(row._mapping)

            # Overlay platform decision if exists
            decision = conn.execute(
                select(draft_decisions.c.status)
                .where(draft_decisions.c.hub_draft_id == draft_id)
            ).fetchone()
            if decision:
                draft["status"] = decision.status

            return draft
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Draft not found")


@router.post("/api/drafts/{draft_id}/approve")
def approve_draft(draft_id: str):
    """Record approval in platform.db (never writes to hub.db)."""
    with get_db() as conn:
        # Verify draft exists
        row = conn.execute(
            select(hub_drafts.c.id).where(hub_drafts.c.id == draft_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Draft not found")

        # Write decision
        conn.execute(
            upsert(
                draft_decisions,
                values={
                    "id": str(uuid.uuid4()),
                    "hub_draft_id": draft_id,
                    "status": "approved",
                    "decided_by": "user",
                },
                conflict_columns=["hub_draft_id"],
                update_columns=["status", "decided_by"],
            )
        )

        # Return the draft with overlaid status
        row = conn.execute(
            select(hub_drafts).where(hub_drafts.c.id == draft_id)
        ).fetchone()
        draft = dict(row._mapping) if row else {"id": draft_id}
        draft["status"] = "approved"
        event_bus.emit("draft.approved", {"draft_id": draft_id, "title": draft.get("title")})
        return draft


@router.post("/api/drafts/{draft_id}/reject")
def reject_draft(draft_id: str):
    """Record rejection in platform.db (never writes to hub.db)."""
    with get_db() as conn:
        # Verify draft exists
        row = conn.execute(
            select(hub_drafts.c.id).where(hub_drafts.c.id == draft_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Draft not found")

        # Write decision
        conn.execute(
            upsert(
                draft_decisions,
                values={
                    "id": str(uuid.uuid4()),
                    "hub_draft_id": draft_id,
                    "status": "rejected",
                    "decided_by": "user",
                },
                conflict_columns=["hub_draft_id"],
                update_columns=["status", "decided_by"],
            )
        )

        # Return the draft with overlaid status
        row = conn.execute(
            select(hub_drafts).where(hub_drafts.c.id == draft_id)
        ).fetchone()
        draft = dict(row._mapping) if row else {"id": draft_id}
        draft["status"] = "rejected"
        event_bus.emit("draft.rejected", {"draft_id": draft_id, "title": draft.get("title")})
        return draft
