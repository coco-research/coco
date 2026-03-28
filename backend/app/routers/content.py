import uuid
import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, text, update
from app.db.session import get_db
from app.db.tables import (
    hub_content, hub_project_content, hub_projects,
    content_classifications,
)
from app.models.content import ClassifyContentBody

log = structlog.get_logger()

router = APIRouter(tags=["Content"])


class AcceptSuggestionBody(BaseModel):
    project_id: str | None = None


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
        with get_db() as conn:
            # FTS search path — use text() since SA doesn't support FTS5 natively
            if q:
                try:
                    count_row = conn.execute(
                        text("SELECT COUNT(*) as cnt FROM content_fts WHERE content_fts MATCH :q"),
                        {"q": q},
                    ).fetchone()
                    total = count_row.cnt if count_row else 0

                    rows = conn.execute(
                        text(
                            "SELECT c.* FROM hub_content c "
                            "JOIN content_fts f ON c.id = f.rowid "
                            "WHERE content_fts MATCH :q "
                            "ORDER BY rank "
                            "LIMIT :limit OFFSET :offset"
                        ),
                        {"q": q, "limit": limit, "offset": offset},
                    ).fetchall()
                    return {"items": [dict(r._mapping) for r in rows], "total": total}
                except Exception as fts_err:
                    log.warning("fts5_search_fallback", query=q, error=str(fts_err),
                                msg="content_fts table missing or MATCH query failed")

            conditions = []

            if source:
                conditions.append(hub_content.c.source == source)
            if status == "unsorted":
                conditions.append(
                    hub_content.c.id.notin_(select(hub_project_content.c.content_id))
                )
                try:
                    actioned = conn.execute(
                        select(content_classifications.c.hub_content_id)
                    ).fetchall()
                    actioned_ids = [r.hub_content_id for r in actioned]
                    if actioned_ids:
                        conditions.append(hub_content.c.id.notin_(actioned_ids))
                except Exception:
                    pass
            elif status:
                conditions.append(hub_content.c.status == status)
            if project_id:
                conditions.append(
                    hub_content.c.id.in_(
                        select(hub_project_content.c.content_id)
                        .where(hub_project_content.c.project_id == project_id)
                    )
                )

            stmt_count = select(func.count().label("cnt")).select_from(hub_content)
            stmt_rows = select(hub_content)
            if conditions:
                stmt_count = stmt_count.where(*conditions)
                stmt_rows = stmt_rows.where(*conditions)

            total_row = conn.execute(stmt_count).fetchone()
            total = total_row.cnt if total_row else 0

            rows = conn.execute(
                stmt_rows.order_by(hub_content.c.created_at.desc()).limit(limit).offset(offset)
            ).fetchall()

            return {"items": [dict(r._mapping) for r in rows], "total": total}
    except Exception:
        return {"items": [], "total": 0}


@router.get("/api/content/{content_id}")
def get_content(content_id: str):
    try:
        with get_db() as conn:
            row = conn.execute(
                select(hub_content).where(hub_content.c.id == content_id)
            ).fetchone()
            if not row:
                raise HTTPException(404, "Content not found")
            item = dict(row._mapping)

            # Overlay classification status
            try:
                classification = conn.execute(
                    select(
                        content_classifications.c.action,
                        content_classifications.c.project_id,
                        content_classifications.c.classified_at,
                    ).where(content_classifications.c.hub_content_id == content_id)
                ).fetchone()
                if classification:
                    item["classification"] = {
                        "action": classification.action,
                        "project_id": classification.project_id,
                        "classified_at": classification.classified_at,
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
    """Classify content by recording in platform.db overlay."""
    project_id = body.project_id
    try:
        with get_db() as conn:
            row = conn.execute(
                select(hub_content.c.id).where(hub_content.c.id == content_id)
            ).fetchone()
            if not row:
                raise HTTPException(404, "Content not found")

            conn.execute(
                text(
                    "INSERT OR REPLACE INTO content_classifications "
                    "(id, hub_content_id, project_id, action) VALUES (:id, :cid, :pid, 'classify')"
                ),
                {"id": str(uuid.uuid4()), "cid": content_id, "pid": project_id},
            )

        return {"status": "classified", "content_id": content_id, "project_id": project_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/api/content/{content_id}/dismiss")
def dismiss_content(content_id: str):
    """Dismiss content by recording in platform.db overlay."""
    try:
        with get_db() as conn:
            row = conn.execute(
                select(hub_content.c.id).where(hub_content.c.id == content_id)
            ).fetchone()
            if not row:
                raise HTTPException(404, "Content not found")

            conn.execute(
                text(
                    "INSERT OR REPLACE INTO content_classifications "
                    "(id, hub_content_id, action) VALUES (:id, :cid, 'dismiss')"
                ),
                {"id": str(uuid.uuid4()), "cid": content_id},
            )

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
    """Return items from content_classifications where status='suggested', joined with hub content."""
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    content_classifications.c.id,
                    content_classifications.c.hub_content_id,
                    content_classifications.c.classified_project_id,
                    content_classifications.c.suggested_project_id,
                    content_classifications.c.confidence,
                    content_classifications.c.reasoning,
                    content_classifications.c.status,
                    content_classifications.c.created_at,
                )
                .where(content_classifications.c.status == "suggested")
                .order_by(content_classifications.c.confidence.desc())
                .limit(limit).offset(offset)
            ).fetchall()

            total_row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(content_classifications)
                .where(content_classifications.c.status == "suggested")
            ).fetchone()
            total = total_row.cnt if total_row else 0

            if not rows:
                return {"items": [], "total": 0}

            # Enrich with hub content metadata
            hub_ids = [r.hub_content_id for r in rows]
            hub_content_map = {}
            for hid in hub_ids:
                hrow = conn.execute(
                    select(
                        hub_content.c.id, hub_content.c.title,
                        hub_content.c.body, hub_content.c.source,
                        hub_content.c.created_at,
                    ).where(hub_content.c.id == hid)
                ).fetchone()
                if hrow:
                    hub_content_map[hid] = dict(hrow._mapping)

            # Get project names
            project_rows = conn.execute(
                select(hub_projects.c.id, hub_projects.c.name)
            ).fetchall()
            project_name_map = {p.id: p.name for p in project_rows}

            suggestions = []
            for r in rows:
                item = dict(r._mapping)
                hub_data = hub_content_map.get(r.hub_content_id, {})
                item["title"] = hub_data.get("title", "Unknown")
                item["body"] = (hub_data.get("body") or "")[:300]
                item["source"] = hub_data.get("source")
                item["content_created_at"] = hub_data.get("created_at")
                proj_id = r.classified_project_id or r.suggested_project_id
                item["suggested_project_name"] = project_name_map.get(proj_id, proj_id)
                suggestions.append(item)

            return {"items": suggestions, "total": total}
    except Exception as e:
        log.warning("list_suggestions_failed", error=str(e))
        return {"items": [], "total": 0}


@router.post("/api/content/{content_id}/accept-suggestion")
def accept_suggestion(content_id: str, body: AcceptSuggestionBody | None = None):
    """Accept a suggestion."""
    try:
        with get_db() as conn:
            row = conn.execute(
                select(
                    content_classifications.c.id,
                    content_classifications.c.classified_project_id,
                    content_classifications.c.suggested_project_id,
                ).where(content_classifications.c.hub_content_id == content_id)
            ).fetchone()

            if not row:
                raise HTTPException(404, "No suggestion found for this content")

            project_id = (body.project_id if body and body.project_id else None) or row.classified_project_id or row.suggested_project_id

            conn.execute(
                text(
                    "UPDATE content_classifications "
                    "SET status = 'accepted', auto_classified = 1, project_id = :pid, "
                    "classified_project_id = :pid, classified_at = datetime('now') "
                    "WHERE hub_content_id = :cid"
                ),
                {"pid": project_id, "cid": content_id},
            )

        return {"status": "accepted", "content_id": content_id, "project_id": project_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/api/content/{content_id}/reject-suggestion")
def reject_suggestion(content_id: str):
    """Reject a suggestion."""
    try:
        with get_db() as conn:
            row = conn.execute(
                select(content_classifications.c.id)
                .where(content_classifications.c.hub_content_id == content_id)
            ).fetchone()

            if not row:
                raise HTTPException(404, "No suggestion found for this content")

            conn.execute(
                text(
                    "UPDATE content_classifications "
                    "SET status = 'rejected', classified_at = datetime('now') "
                    "WHERE hub_content_id = :cid"
                ),
                {"cid": content_id},
            )

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
        with get_db() as conn:
            rows = conn.execute(
                select(
                    content_classifications.c.hub_content_id,
                    content_classifications.c.classified_project_id,
                    content_classifications.c.suggested_project_id,
                )
                .where(content_classifications.c.status == "suggested")
                .where(content_classifications.c.confidence >= min_confidence)
            ).fetchall()

            count = 0
            for r in rows:
                project_id = r.classified_project_id or r.suggested_project_id
                conn.execute(
                    text(
                        "UPDATE content_classifications "
                        "SET status = 'accepted', auto_classified = 1, project_id = :pid, "
                        "classified_project_id = :pid, classified_at = datetime('now') "
                        "WHERE hub_content_id = :cid"
                    ),
                    {"pid": project_id, "cid": r.hub_content_id},
                )
                count += 1

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
        with get_db() as conn:
            row = conn.execute(
                select(
                    hub_content.c.id, hub_content.c.title,
                    hub_content.c.body, hub_content.c.source,
                ).where(hub_content.c.id == content_id)
            ).fetchone()
            if not row:
                raise HTTPException(404, "Content not found")

        content_text = f"{row.title or ''}\n{row.body or ''}"

        from app.services.collaboration_context import create_platform_todos_from_text

        created = create_platform_todos_from_text(
            content_text,
            source_content_id=content_id,
            project_id=None,  # project_id not available on hub_content directly
        )

        return {"status": "ok", "actions_created": len(created), "actions": created}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
