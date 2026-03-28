import logging
import uuid
from fastapi import APIRouter, HTTPException, Query
from app.db.connections import get_hub_db, get_platform_db
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
        with get_hub_db() as db:
            conditions: list[str] = []
            params: list[str | int] = []

            if status:
                conditions.append("d.status = ?")
                params.append(status)
            if project_ids:
                ids = [pid.strip() for pid in project_ids.split(",") if pid.strip()]
                if ids:
                    placeholders = ",".join("?" for _ in ids)
                    conditions.append(f"d.project_id IN ({placeholders})")
                    params.extend(ids)
            elif project_id:
                conditions.append("d.project_id = ?")
                params.append(project_id)

            where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
            rows = db.execute(
                f"SELECT d.* FROM drafts d{where} ORDER BY d.created_at DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()
            drafts = [dict(r) for r in rows]

        # Overlay platform.db decisions onto hub.db drafts
        if drafts:
            draft_ids = [d["id"] for d in drafts]
            with get_platform_db() as pdb:
                placeholders = ",".join("?" for _ in draft_ids)
                decisions = pdb.execute(
                    f"SELECT hub_draft_id, status FROM draft_decisions WHERE hub_draft_id IN ({placeholders})",
                    draft_ids,
                ).fetchall()
                overlay = {r["hub_draft_id"]: r["status"] for r in decisions}

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
        with get_hub_db() as db:
            row = db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Draft not found")
            draft = dict(row)

        # Overlay platform decision if exists
        with get_platform_db() as pdb:
            decision = pdb.execute(
                "SELECT status FROM draft_decisions WHERE hub_draft_id = ?", (draft_id,)
            ).fetchone()
            if decision:
                draft["status"] = decision["status"]

        return draft
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Draft not found")


@router.post("/api/drafts/{draft_id}/approve")
def approve_draft(draft_id: str):
    """Record approval in platform.db (never writes to hub.db)."""
    # Verify draft exists in hub.db
    with get_hub_db() as db:
        row = db.execute("SELECT id FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Draft not found")

    # Write decision to platform.db overlay
    with get_platform_db() as pdb:
        pdb.execute(
            "INSERT OR REPLACE INTO draft_decisions (id, hub_draft_id, status, decided_by) VALUES (?, ?, 'approved', 'user')",
            (str(uuid.uuid4()), draft_id),
        )
        pdb.commit()

    # Return the draft with overlaid status
    with get_hub_db() as db:
        row = db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        draft = dict(row) if row else {"id": draft_id}
        draft["status"] = "approved"
        event_bus.emit("draft.approved", {"draft_id": draft_id, "title": draft.get("title")})
        return draft


@router.post("/api/drafts/{draft_id}/reject")
def reject_draft(draft_id: str):
    """Record rejection in platform.db (never writes to hub.db)."""
    # Verify draft exists in hub.db
    with get_hub_db() as db:
        row = db.execute("SELECT id FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Draft not found")

    # Write decision to platform.db overlay
    with get_platform_db() as pdb:
        pdb.execute(
            "INSERT OR REPLACE INTO draft_decisions (id, hub_draft_id, status, decided_by) VALUES (?, ?, 'rejected', 'user')",
            (str(uuid.uuid4()), draft_id),
        )
        pdb.commit()

    # Return the draft with overlaid status
    with get_hub_db() as db:
        row = db.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
        draft = dict(row) if row else {"id": draft_id}
        draft["status"] = "rejected"
        event_bus.emit("draft.rejected", {"draft_id": draft_id, "title": draft.get("title")})
        return draft
