import uuid
import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.db.connections import get_hub_db, get_platform_db
from app.models.content import ClassifyContentBody

log = structlog.get_logger()

router = APIRouter(tags=["Content"])


# ---------------------------------------------------------------------------
# Pydantic models for suggestions
# ---------------------------------------------------------------------------


class AcceptSuggestionBody(BaseModel):
    project_id: str | None = None  # optional override


class ExtractActionsBody(BaseModel):
    pass


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


# ---------------------------------------------------------------------------
# Suggestions API
# ---------------------------------------------------------------------------


@router.get("/api/content/suggestions")
def list_suggestions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Return items from content_classifications where status='suggested', joined with hub.db content."""
    try:
        with get_platform_db() as pdb:
            rows = pdb.execute(
                """SELECT id, hub_content_id, classified_project_id, suggested_project_id,
                          confidence, reasoning, status, created_at
                   FROM content_classifications
                   WHERE status = 'suggested'
                   ORDER BY confidence DESC
                   LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()

            total_row = pdb.execute(
                "SELECT COUNT(*) as cnt FROM content_classifications WHERE status = 'suggested'"
            ).fetchone()
            total = total_row["cnt"] if total_row else 0

        if not rows:
            return {"items": [], "total": 0}

        # Enrich with hub.db content metadata
        suggestions = []
        hub_ids = [r["hub_content_id"] for r in rows]

        hub_content_map = {}
        try:
            with get_hub_db() as hub:
                for hid in hub_ids:
                    hrow = hub.execute(
                        "SELECT id, title, body, source, created_at FROM content WHERE id = ?",
                        (hid,),
                    ).fetchone()
                    if hrow:
                        hub_content_map[hid] = dict(hrow)
        except Exception:
            pass

        # Get project names
        project_name_map = {}
        try:
            with get_hub_db() as hub:
                projects = hub.execute("SELECT id, name FROM projects").fetchall()
                project_name_map = {p["id"]: p["name"] for p in projects}
        except Exception:
            pass

        for r in rows:
            item = dict(r)
            hub_data = hub_content_map.get(r["hub_content_id"], {})
            item["title"] = hub_data.get("title", "Unknown")
            item["body"] = (hub_data.get("body") or "")[:300]
            item["source"] = hub_data.get("source")
            item["content_created_at"] = hub_data.get("created_at")
            proj_id = r["classified_project_id"] or r["suggested_project_id"]
            item["suggested_project_name"] = project_name_map.get(proj_id, proj_id)
            suggestions.append(item)

        return {"items": suggestions, "total": total}
    except Exception as e:
        log.warning("list_suggestions_failed", error=str(e))
        return {"items": [], "total": 0}


@router.post("/api/content/{content_id}/accept-suggestion")
def accept_suggestion(content_id: str, body: AcceptSuggestionBody | None = None):
    """Accept a suggestion (moves to auto_classified=1, status='accepted')."""
    try:
        with get_platform_db() as pdb:
            row = pdb.execute(
                "SELECT id, classified_project_id, suggested_project_id FROM content_classifications WHERE hub_content_id = ?",
                (content_id,),
            ).fetchone()

            if not row:
                raise HTTPException(404, "No suggestion found for this content")

            project_id = (body.project_id if body and body.project_id else None) or row["classified_project_id"] or row["suggested_project_id"]

            pdb.execute(
                """UPDATE content_classifications
                   SET status = 'accepted', auto_classified = 1, project_id = ?,
                       classified_project_id = ?, classified_at = datetime('now')
                   WHERE hub_content_id = ?""",
                (project_id, project_id, content_id),
            )
            pdb.commit()

        return {"status": "accepted", "content_id": content_id, "project_id": project_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/api/content/{content_id}/reject-suggestion")
def reject_suggestion(content_id: str):
    """Reject a suggestion (status='rejected')."""
    try:
        with get_platform_db() as pdb:
            row = pdb.execute(
                "SELECT id FROM content_classifications WHERE hub_content_id = ?",
                (content_id,),
            ).fetchone()

            if not row:
                raise HTTPException(404, "No suggestion found for this content")

            pdb.execute(
                "UPDATE content_classifications SET status = 'rejected', classified_at = datetime('now') WHERE hub_content_id = ?",
                (content_id,),
            )
            pdb.commit()

        return {"status": "rejected", "content_id": content_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/api/content/run-classifier")
def run_classifier(limit: int = Query(50, ge=1, le=200)):
    """Manually trigger the auto-classifier to process unsorted content."""
    try:
        from app.services.auto_classifier import process_unsorted

        stats = process_unsorted(limit=limit)
        return {"status": "ok", **stats}
    except Exception as e:
        log.warning("run_classifier_failed", error=str(e))
        raise HTTPException(500, str(e))


@router.post("/api/content/batch-accept-suggestions")
def batch_accept_suggestions(min_confidence: float = Query(0.90)):
    """Accept all suggestions with confidence >= threshold."""
    try:
        with get_platform_db() as pdb:
            rows = pdb.execute(
                """SELECT hub_content_id, classified_project_id, suggested_project_id
                   FROM content_classifications
                   WHERE status = 'suggested' AND confidence >= ?""",
                (min_confidence,),
            ).fetchall()

            count = 0
            for r in rows:
                project_id = r["classified_project_id"] or r["suggested_project_id"]
                pdb.execute(
                    """UPDATE content_classifications
                       SET status = 'accepted', auto_classified = 1, project_id = ?,
                           classified_project_id = ?, classified_at = datetime('now')
                       WHERE hub_content_id = ?""",
                    (project_id, project_id, r["hub_content_id"]),
                )
                count += 1

            pdb.commit()

        return {"status": "ok", "accepted_count": count, "min_confidence": min_confidence}
    except Exception as e:
        raise HTTPException(500, str(e))


# ---------------------------------------------------------------------------
# Content-to-Action extraction
# ---------------------------------------------------------------------------


@router.post("/api/content/{content_id}/extract-actions")
def extract_actions(content_id: str):
    """Extract action items from a content item and create platform-native todos."""
    try:
        # Get content from hub.db
        with get_hub_db() as hub:
            row = hub.execute(
                "SELECT id, title, body, source, project_id FROM content WHERE id = ?",
                (content_id,),
            ).fetchone()
            if not row:
                raise HTTPException(404, "Content not found")

        text = f"{row['title'] or ''}\n{row['body'] or ''}"

        from app.services.collaboration_context import create_platform_todos_from_text

        created = create_platform_todos_from_text(
            text,
            source_content_id=content_id,
            project_id=row.get("project_id"),
        )

        return {"status": "ok", "actions_created": len(created), "actions": created}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
