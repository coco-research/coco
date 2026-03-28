"""Insight engine — generates cross-source insights from extracted entities.

Insight types:
- cross_reference: entity co-occurrence across 2+ source content items
- pattern: temporal proximity (48h window) + shared person/topic
- contradiction: conflicting dates/decisions across content
"""

import json
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

import structlog
from sqlalchemy import select, insert, update, func, text

from app.db.session import get_db
from app.db.tables import extracted_entities, insights, hub_content

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TEMPORAL_WINDOW_HOURS = 48


def _parse_dt(dt_str: str | None) -> datetime | None:
    """Parse an ISO datetime string, returning None on failure."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _entity_key(e: dict) -> str:
    """Normalize entity for grouping: (type, lowercase value)."""
    return f"{e['entity_type']}::{e['value'].lower().strip()}"


# ---------------------------------------------------------------------------
# Cross-reference detection
# ---------------------------------------------------------------------------

def _detect_cross_references(conn) -> list[dict]:
    """Find entities that appear across 2+ different content items."""
    # Get all entities grouped by normalized value + type
    rows = conn.execute(
        select(
            extracted_entities.c.entity_type,
            extracted_entities.c.value,
            func.count(func.distinct(extracted_entities.c.content_id)).label("content_count"),
            func.group_concat(func.distinct(extracted_entities.c.content_id)).label("content_ids_str"),
            func.max(extracted_entities.c.confidence).label("max_confidence"),
        )
        .group_by(extracted_entities.c.entity_type, extracted_entities.c.value)
        .having(func.count(func.distinct(extracted_entities.c.content_id)) >= 2)
        .order_by(func.count(func.distinct(extracted_entities.c.content_id)).desc())
        .limit(50)
    ).fetchall()

    insights_data: list[dict] = []
    for row in rows:
        content_ids = [cid.strip() for cid in (row.content_ids_str or "").split(",") if cid.strip()]

        # Fetch content titles for description
        titles: list[str] = []
        if content_ids:
            title_rows = conn.execute(
                select(hub_content.c.id, hub_content.c.title)
                .where(hub_content.c.id.in_(content_ids[:5]))
            ).fetchall()
            titles = [r.title or r.id for r in title_rows]

        entity_type = row.entity_type
        value = row.value
        count = row.content_count

        title_text = f'"{value}" appears across {count} sources'
        desc_parts = [
            f'The {entity_type} "{value}" was found in {count} different content items.',
        ]
        if titles:
            desc_parts.append("Sources: " + ", ".join(f'"{t}"' for t in titles[:5]))

        # Get entity IDs for this value
        eid_rows = conn.execute(
            select(extracted_entities.c.id)
            .where(extracted_entities.c.entity_type == entity_type)
            .where(extracted_entities.c.value == value)
        ).fetchall()
        entity_ids = [r.id for r in eid_rows]

        insights_data.append({
            "insight_type": "cross_reference",
            "title": title_text,
            "description": " ".join(desc_parts),
            "confidence": min(0.95, row.max_confidence + 0.1 * (count - 2)),
            "entity_ids": entity_ids,
            "content_ids": content_ids,
            "metadata_json": json.dumps({
                "entity_type": entity_type,
                "entity_value": value,
                "occurrence_count": count,
            }),
        })

    return insights_data


# ---------------------------------------------------------------------------
# Temporal pattern detection
# ---------------------------------------------------------------------------

def _detect_patterns(conn) -> list[dict]:
    """Find temporal proximity patterns: content items within 48h sharing person/topic."""
    # Get content with timestamps
    content_rows = conn.execute(
        select(hub_content.c.id, hub_content.c.title, hub_content.c.source, hub_content.c.created_at)
        .where(hub_content.c.created_at.isnot(None))
        .order_by(hub_content.c.created_at.desc())
        .limit(200)
    ).fetchall()

    if not content_rows:
        return []

    # Build content -> entities map
    content_entities: dict[str, list[dict]] = defaultdict(list)
    all_content_ids = [r.id for r in content_rows]

    entity_rows = conn.execute(
        select(
            extracted_entities.c.id,
            extracted_entities.c.content_id,
            extracted_entities.c.entity_type,
            extracted_entities.c.value,
        )
        .where(extracted_entities.c.content_id.in_(all_content_ids))
        .where(extracted_entities.c.entity_type.in_(["person", "topic"]))
    ).fetchall()

    for er in entity_rows:
        content_entities[er.content_id].append({
            "id": er.id,
            "type": er.entity_type,
            "value": er.value.lower().strip(),
        })

    # Compare pairs within temporal window
    insights_data: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    for i, c1 in enumerate(content_rows):
        dt1 = _parse_dt(c1.created_at)
        if not dt1:
            continue
        entities1 = content_entities.get(c1.id, [])
        if not entities1:
            continue
        values1 = {(e["type"], e["value"]) for e in entities1}

        for c2 in content_rows[i + 1:]:
            dt2 = _parse_dt(c2.created_at)
            if not dt2:
                continue

            delta = abs((dt1 - dt2).total_seconds()) / 3600
            if delta > _TEMPORAL_WINDOW_HOURS:
                continue

            pair_key = tuple(sorted([c1.id, c2.id]))
            if pair_key in seen_pairs:
                continue

            entities2 = content_entities.get(c2.id, [])
            if not entities2:
                continue
            values2 = {(e["type"], e["value"]) for e in entities2}

            shared = values1 & values2
            if not shared:
                continue

            seen_pairs.add(pair_key)

            shared_desc = ", ".join(f"{t}: {v}" for t, v in list(shared)[:5])
            entity_ids = list({
                e["id"] for e in entities1 + entities2
                if (e["type"], e["value"]) in shared
            })

            insights_data.append({
                "insight_type": "pattern",
                "title": f'Temporal pattern: "{c1.title or c1.id}" and "{c2.title or c2.id}"',
                "description": (
                    f"Two content items within {delta:.0f}h share entities: {shared_desc}. "
                    f"Sources: {c1.source or 'unknown'}, {c2.source or 'unknown'}."
                ),
                "confidence": min(0.9, 0.5 + 0.1 * len(shared)),
                "entity_ids": entity_ids,
                "content_ids": [c1.id, c2.id],
                "metadata_json": json.dumps({
                    "time_delta_hours": round(delta, 1),
                    "shared_entities": [{"type": t, "value": v} for t, v in shared],
                }),
            })

    return insights_data[:30]  # cap


# ---------------------------------------------------------------------------
# Contradiction detection
# ---------------------------------------------------------------------------

def _detect_contradictions(conn) -> list[dict]:
    """Find conflicting dates/decisions across content items sharing a topic/person."""
    # Get all date entities grouped by content
    date_rows = conn.execute(
        select(
            extracted_entities.c.id,
            extracted_entities.c.content_id,
            extracted_entities.c.value,
            extracted_entities.c.context_snippet,
        )
        .where(extracted_entities.c.entity_type == "date")
    ).fetchall()

    if not date_rows:
        return []

    # Group by content_id
    content_dates: dict[str, list[dict]] = defaultdict(list)
    for dr in date_rows:
        content_dates[dr.content_id].append({
            "id": dr.id,
            "value": dr.value,
            "context": dr.context_snippet or "",
        })

    # Get decision entities
    decision_rows = conn.execute(
        select(
            extracted_entities.c.id,
            extracted_entities.c.content_id,
            extracted_entities.c.value,
        )
        .where(extracted_entities.c.entity_type == "decision")
    ).fetchall()

    content_decisions: dict[str, list[dict]] = defaultdict(list)
    for dr in decision_rows:
        content_decisions[dr.content_id].append({
            "id": dr.id,
            "value": dr.value,
        })

    # Find content pairs that share a person/topic but have different dates
    # (simplified: look for same person mentioned with different dates)
    person_content: dict[str, list[str]] = defaultdict(list)
    person_rows = conn.execute(
        select(
            extracted_entities.c.content_id,
            extracted_entities.c.value,
        )
        .where(extracted_entities.c.entity_type == "person")
    ).fetchall()

    for pr in person_rows:
        person_content[pr.value.lower().strip()].append(pr.content_id)

    insights_data: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for person, cids in person_content.items():
        unique_cids = list(set(cids))
        if len(unique_cids) < 2:
            continue

        for i, cid1 in enumerate(unique_cids):
            dates1 = content_dates.get(cid1, [])
            decisions1 = content_decisions.get(cid1, [])
            if not dates1 and not decisions1:
                continue

            for cid2 in unique_cids[i + 1:]:
                pair_key = tuple(sorted([cid1, cid2]))
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                dates2 = content_dates.get(cid2, [])
                decisions2 = content_decisions.get(cid2, [])

                # Check for conflicting dates
                date_values1 = {d["value"] for d in dates1}
                date_values2 = {d["value"] for d in dates2}

                if dates1 and dates2 and not (date_values1 & date_values2):
                    entity_ids = [d["id"] for d in dates1 + dates2]
                    insights_data.append({
                        "insight_type": "contradiction",
                        "title": f"Possible date conflict involving {person}",
                        "description": (
                            f'Content items mention "{person}" with different dates: '
                            f'{", ".join(sorted(date_values1)[:3])} vs '
                            f'{", ".join(sorted(date_values2)[:3])}. '
                            f"Verify which dates are correct."
                        ),
                        "confidence": 0.6,
                        "entity_ids": entity_ids,
                        "content_ids": [cid1, cid2],
                        "metadata_json": json.dumps({
                            "person": person,
                            "dates_source_1": sorted(date_values1),
                            "dates_source_2": sorted(date_values2),
                        }),
                    })

    return insights_data[:20]  # cap


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_insights(limit: int = 50) -> list[dict]:
    """Run all insight detectors and store new insights.

    Returns list of newly created insight dicts.
    """
    now = datetime.utcnow().isoformat()
    all_new: list[dict] = []

    with get_db() as conn:
        cross_refs = _detect_cross_references(conn)
        patterns = _detect_patterns(conn)
        contradictions = _detect_contradictions(conn)

    candidates = cross_refs + patterns + contradictions

    # Deduplicate against existing insights by title
    with get_db() as conn:
        existing_titles: set[str] = set()
        rows = conn.execute(
            select(insights.c.title)
        ).fetchall()
        existing_titles = {r.title for r in rows}

    new_insights = [c for c in candidates if c["title"] not in existing_titles]
    new_insights = new_insights[:limit]

    if not new_insights:
        log.info("insight_generation_no_new")
        return []

    with get_db() as conn:
        for ins in new_insights:
            insight_id = str(uuid.uuid4())
            conn.execute(
                insert(insights).values(
                    id=insight_id,
                    insight_type=ins["insight_type"],
                    title=ins["title"],
                    description=ins["description"],
                    confidence=ins["confidence"],
                    status="new",
                    entity_ids=json.dumps(ins["entity_ids"]),
                    content_ids=json.dumps(ins["content_ids"]),
                    metadata_json=ins.get("metadata_json", "{}"),
                    created_at=now,
                    updated_at=now,
                )
            )
            ins["id"] = insight_id
            ins["status"] = "new"
            ins["created_at"] = now
            all_new.append(ins)

    log.info(
        "insights_generated",
        count=len(all_new),
        cross_references=len(cross_refs),
        patterns=len(patterns),
        contradictions=len(contradictions),
    )
    return all_new


def get_insight(insight_id: str) -> dict | None:
    """Fetch a single insight by ID with linked entity details."""
    with get_db() as conn:
        row = conn.execute(
            select(insights).where(insights.c.id == insight_id)
        ).fetchone()

    if not row:
        return None

    result = dict(row._mapping)

    # Parse JSON fields
    entity_ids = json.loads(result.get("entity_ids") or "[]")
    content_ids = json.loads(result.get("content_ids") or "[]")
    result["entity_ids"] = entity_ids
    result["content_ids"] = content_ids
    result["metadata_json"] = json.loads(result.get("metadata_json") or "{}")

    # Enrich with entity details
    if entity_ids:
        with get_db() as conn:
            entity_rows = conn.execute(
                select(extracted_entities)
                .where(extracted_entities.c.id.in_(entity_ids[:50]))
            ).fetchall()
        result["entities"] = [dict(r._mapping) for r in entity_rows]
    else:
        result["entities"] = []

    # Enrich with content titles
    if content_ids:
        with get_db() as conn:
            content_rows = conn.execute(
                select(hub_content.c.id, hub_content.c.title, hub_content.c.source)
                .where(hub_content.c.id.in_(content_ids[:20]))
            ).fetchall()
        result["content_items"] = [
            {"id": r.id, "title": r.title, "source": r.source}
            for r in content_rows
        ]
    else:
        result["content_items"] = []

    return result


def action_insight(insight_id: str, action: str) -> dict | None:
    """Update insight status: seen, actioned, dismissed."""
    valid_actions = {"seen", "actioned", "dismissed"}
    if action not in valid_actions:
        return None

    now = datetime.utcnow().isoformat()

    with get_db() as conn:
        row = conn.execute(
            select(insights.c.id).where(insights.c.id == insight_id)
        ).fetchone()
        if not row:
            return None

        conn.execute(
            update(insights)
            .where(insights.c.id == insight_id)
            .values(status=action, updated_at=now)
        )

    return get_insight(insight_id)
