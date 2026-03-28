import uuid
import structlog
from fastapi import APIRouter, HTTPException, Query
from app.db.connections import get_hub_db, get_platform_db
from app.models.content import ClassifyContentBody

log = structlog.get_logger()

router = APIRouter(tags=["Content"])


@router.get("/api/content")
def list_content(
    source: str | None = None,
    project_id: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        with get_hub_db() as db:
            # FTS search path
            if q:
                try:
                    count_row = db.execute(
                        "SELECT COUNT(*) as cnt FROM content_fts WHERE content_fts MATCH ?",
                        (q,),
                    ).fetchone()
                    total = count_row["cnt"] if count_row else 0

                    rows = db.execute(
                        """SELECT c.* FROM content c
                           JOIN content_fts f ON c.id = f.rowid
                           WHERE content_fts MATCH ?
                           ORDER BY rank
                           LIMIT ? OFFSET ?""",
                        (q, limit, offset),
                    ).fetchall()
                    return {"items": [dict(r) for r in rows], "total": total}
                except Exception as fts_err:
                    log.warning("fts5_search_fallback", query=q, error=str(fts_err),
                                msg="content_fts table missing or MATCH query failed, falling back to non-FTS query")

            conditions: list[str] = []
            params: list[str | int] = []

            if source:
                conditions.append("c.source = ?")
                params.append(source)
            if status == "unsorted":
                # Unsorted = not assigned to any project AND not classified/dismissed in platform.db
                conditions.append(
                    "c.id NOT IN (SELECT content_id FROM project_content)"
                )
                try:
                    with get_platform_db() as pdb:
                        actioned = pdb.execute(
                            "SELECT hub_content_id FROM content_classifications"
                        ).fetchall()
                        actioned_ids = [r["hub_content_id"] for r in actioned]
                        if actioned_ids:
                            placeholders = ",".join("?" for _ in actioned_ids)
                            conditions.append(f"c.id NOT IN ({placeholders})")
                            params.extend(actioned_ids)
                except Exception:
                    pass
            elif status:
                conditions.append("c.status = ?")
                params.append(status)
            if project_id:
                conditions.append(
                    "c.id IN (SELECT content_id FROM project_content WHERE project_id = ?)"
                )
                params.append(project_id)

            where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

            total_row = db.execute(
                f"SELECT COUNT(*) as cnt FROM content c{where}", params
            ).fetchone()
            total = total_row["cnt"] if total_row else 0

            rows = db.execute(
                f"SELECT c.* FROM content c{where} ORDER BY c.created_at DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()

            return {"items": [dict(r) for r in rows], "total": total}
    except Exception:
        return {"items": [], "total": 0}


@router.get("/api/content/{content_id}")
def get_content(content_id: str):
    try:
        with get_hub_db() as db:
            row = db.execute("SELECT * FROM content WHERE id = ?", (content_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Content not found")
            item = dict(row)

        # Overlay classification status from platform.db
        try:
            with get_platform_db() as pdb:
                classification = pdb.execute(
                    "SELECT action, project_id, classified_at FROM content_classifications WHERE hub_content_id = ?",
                    (content_id,),
                ).fetchone()
                if classification:
                    item["classification"] = {
                        "action": classification["action"],
                        "project_id": classification["project_id"],
                        "classified_at": classification["classified_at"],
                    }
        except Exception:
            pass

        return item
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, "Content not found")


@router.post("/api/content/{content_id}/classify")
def classify_content(content_id: str, body: ClassifyContentBody):
    """Classify content by recording in platform.db overlay (hub.db stays read-only)."""
    project_id = body.project_id
    try:
        with get_hub_db() as db:
            row = db.execute("SELECT id FROM content WHERE id = ?", (content_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Content not found")

        with get_platform_db() as pdb:
            pdb.execute(
                "INSERT OR REPLACE INTO content_classifications (id, hub_content_id, project_id, action) VALUES (?, ?, ?, 'classify')",
                (str(uuid.uuid4()), content_id, project_id),
            )
            pdb.commit()

        return {"status": "classified", "content_id": content_id, "project_id": project_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/api/content/{content_id}/dismiss")
def dismiss_content(content_id: str):
    """Dismiss content by recording in platform.db overlay (hub.db stays read-only)."""
    try:
        with get_hub_db() as db:
            row = db.execute("SELECT id FROM content WHERE id = ?", (content_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Content not found")

        with get_platform_db() as pdb:
            pdb.execute(
                "INSERT OR REPLACE INTO content_classifications (id, hub_content_id, action) VALUES (?, ?, 'dismiss')",
                (str(uuid.uuid4()), content_id),
            )
            pdb.commit()

        return {"status": "dismissed", "content_id": content_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
