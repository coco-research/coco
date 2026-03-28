"""Insights router — entity extraction + cross-source insight generation."""

import json
import structlog
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func

from app.db.session import get_db
from app.db.tables import extracted_entities, insights, hub_content
from app.models.insights import ExtractRequest, ExtractBatchRequest, InsightActionBody
from app.services.entity_extractor import extract_entities, extract_batch
from app.services.insight_engine import (
    generate_insights,
    get_insight,
    action_insight,
)

log = structlog.get_logger()

router = APIRouter(tags=["Insights"])

# ---------------------------------------------------------------------------
# Entity endpoints
# ---------------------------------------------------------------------------


@router.get("/api/entities")
def list_entities(
    content_id: str | None = None,
    type: str | None = Query(None, alias="type"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List extracted entities, optionally filtered by content_id and/or type."""
    with get_db() as conn:
        q = select(extracted_entities).order_by(
            extracted_entities.c.confidence.desc(),
            extracted_entities.c.created_at.desc(),
        )
        if content_id:
            q = q.where(extracted_entities.c.content_id == content_id)
        if type:
            q = q.where(extracted_entities.c.entity_type == type)
        q = q.limit(limit).offset(offset)

        rows = conn.execute(q).fetchall()

        # Get total count
        count_q = select(func.count()).select_from(extracted_entities)
        if content_id:
            count_q = count_q.where(extracted_entities.c.content_id == content_id)
        if type:
            count_q = count_q.where(extracted_entities.c.entity_type == type)
        total = conn.execute(count_q).scalar() or 0

    return {
        "items": [dict(r._mapping) for r in rows],
        "total": total,
    }


@router.post("/api/entities/extract")
def extract_from_content(body: ExtractRequest):
    """Extract entities from a single content item."""
    entities = extract_entities(
        content_id=body.content_id,
        content_text=body.content_text,
        mode=body.mode,
    )
    return {
        "content_id": body.content_id,
        "entities": entities,
        "count": len(entities),
    }


@router.post("/api/entities/extract-batch")
def extract_batch_endpoint(body: ExtractBatchRequest):
    """Bulk extract entities from multiple content items (reads text from hub_content)."""
    result = extract_batch(content_ids=body.content_ids, mode=body.mode)
    return result


# ---------------------------------------------------------------------------
# Insight endpoints
# ---------------------------------------------------------------------------


@router.get("/api/insights")
def list_insights(
    type: str | None = Query(None, alias="type"),
    status: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List insights with optional filters."""
    with get_db() as conn:
        q = select(insights).order_by(
            insights.c.confidence.desc(),
            insights.c.created_at.desc(),
        )
        if type:
            q = q.where(insights.c.insight_type == type)
        if status:
            q = q.where(insights.c.status == status)
        q = q.limit(limit).offset(offset)

        rows = conn.execute(q).fetchall()

        # Get total
        count_q = select(func.count()).select_from(insights)
        if type:
            count_q = count_q.where(insights.c.insight_type == type)
        if status:
            count_q = count_q.where(insights.c.status == status)
        total = conn.execute(count_q).scalar() or 0

    items = []
    for r in rows:
        d = dict(r._mapping)
        d["entity_ids"] = json.loads(d.get("entity_ids") or "[]")
        d["content_ids"] = json.loads(d.get("content_ids") or "[]")
        d["metadata_json"] = json.loads(d.get("metadata_json") or "{}")
        items.append(d)

    return {
        "items": items,
        "total": total,
    }


@router.get("/api/insights/summary")
def insights_summary():
    """Aggregate stats for the insights dashboard."""
    with get_db() as conn:
        # Count by type
        type_rows = conn.execute(
            select(
                insights.c.insight_type,
                func.count().label("count"),
            ).group_by(insights.c.insight_type)
        ).fetchall()
        by_type = {r.insight_type: r.count for r in type_rows}

        # Count by status
        status_rows = conn.execute(
            select(
                insights.c.status,
                func.count().label("count"),
            ).group_by(insights.c.status)
        ).fetchall()
        by_status = {r.status: r.count for r in status_rows}

        # Total entities
        entity_count = conn.execute(
            select(func.count()).select_from(extracted_entities)
        ).scalar() or 0

        # Entity type breakdown
        entity_type_rows = conn.execute(
            select(
                extracted_entities.c.entity_type,
                func.count().label("count"),
            ).group_by(extracted_entities.c.entity_type)
        ).fetchall()
        entities_by_type = {r.entity_type: r.count for r in entity_type_rows}

        # Average confidence
        avg_conf = conn.execute(
            select(func.avg(insights.c.confidence))
        ).scalar()

    total_insights = sum(by_type.values())
    return {
        "total_insights": total_insights,
        "by_type": by_type,
        "by_status": by_status,
        "total_entities": entity_count,
        "entities_by_type": entities_by_type,
        "average_confidence": round(avg_conf, 3) if avg_conf else 0,
    }


@router.get("/api/insights/{insight_id}")
def get_insight_detail(insight_id: str):
    """Get a single insight with linked entity details."""
    result = get_insight(insight_id)
    if not result:
        raise HTTPException(404, f"Insight {insight_id} not found")
    return result


@router.post("/api/insights/{insight_id}/action")
def action_insight_endpoint(insight_id: str, body: InsightActionBody):
    """Mark an insight as seen/actioned/dismissed."""
    valid = {"seen", "actioned", "dismissed"}
    if body.action not in valid:
        raise HTTPException(400, f"Invalid action '{body.action}'. Valid: {sorted(valid)}")

    result = action_insight(insight_id, body.action)
    if not result:
        raise HTTPException(404, f"Insight {insight_id} not found")
    return result


@router.post("/api/insights/generate")
def trigger_generate():
    """Trigger an insight generation cycle."""
    new_insights = generate_insights(limit=50)
    return {
        "generated": len(new_insights),
        "insights": new_insights,
    }
