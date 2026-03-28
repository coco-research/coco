"""Entity extraction service — regex/heuristic (instant) + optional LLM (deep).

Extracts: person, project, date, decision, action_item, topic
from content text, storing results in the extracted_entities table.
"""

import re
import uuid
from datetime import datetime

import structlog
from sqlalchemy import insert, select, delete

from app.db.session import get_db
from app.db.tables import extracted_entities, hub_content

log = structlog.get_logger()

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Email addresses -> person
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+", re.IGNORECASE)

# @mentions -> person (require whitespace or start-of-line before @)
_MENTION_RE = re.compile(r"(?:^|(?<=\s))@(\w[\w.-]{1,30})", re.MULTILINE)

# ISO dates (2024-03-15, 2024/03/15)
_ISO_DATE_RE = re.compile(
    r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b"
)

# Natural dates (March 15, Jan 3rd 2025, etc.)
_NATURAL_DATE_RE = re.compile(
    r"\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"\s+\d{1,2}(?:st|nd|rd|th)?(?:[,\s]+\d{4})?)\b",
    re.IGNORECASE,
)

# Relative dates
_RELATIVE_DATE_RE = re.compile(
    r"\b(today|tomorrow|yesterday|next\s+(?:week|month|monday|tuesday|wednesday|"
    r"thursday|friday)|end\s+of\s+(?:week|month|quarter|year))\b",
    re.IGNORECASE,
)

# Decision keywords
_DECISION_RE = re.compile(
    r"(?:^|\.\s+|\n\s*)([^.!\n]*?\b(?:decided|agreed|approved|resolved|conclusion|"
    r"we(?:'ll| will)|going\s+(?:to|with)|final(?:ly|ized)?|confirmed)\b[^.!\n]*[.!]?)",
    re.IGNORECASE | re.MULTILINE,
)

# Action items
_ACTION_RE = re.compile(
    r"(?:^|\.\s+|\n\s*)([^.!\n]*?\b(?:action\s*item|TODO|FIXME|"
    r"(?:please|need\s+to|should|must|will)\s+\w+|"
    r"follow[\s-]up|assigned\s+to|deadline|by\s+(?:EOD|EOW|end\s+of))\b[^.!\n]*[.!]?)",
    re.IGNORECASE | re.MULTILINE,
)

# Project name patterns (ProjName-123, JIRA-style keys)
_PROJECT_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,8}-\d+)\b")

# Topic extraction: capitalized multi-word phrases (heuristic)
_TOPIC_RE = re.compile(
    r"\b((?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+))\b"
)


def _clip(text: str, match: re.Match, window: int = 80) -> str:
    """Extract a context snippet around a regex match."""
    start = max(0, match.start() - window)
    end = min(len(text), match.end() + window)
    return text[start:end].strip()


def _extract_regex(content_text: str) -> list[dict]:
    """Run all regex patterns and return entity dicts."""
    entities: list[dict] = []

    # Person: email addresses
    for m in _EMAIL_RE.finditer(content_text):
        entities.append({
            "entity_type": "person",
            "value": m.group(0).lower(),
            "confidence": 0.9,
            "context_snippet": _clip(content_text, m),
        })

    # Person: @mentions
    for m in _MENTION_RE.finditer(content_text):
        entities.append({
            "entity_type": "person",
            "value": m.group(1),
            "confidence": 0.8,
            "context_snippet": _clip(content_text, m),
        })

    # Dates: ISO
    for m in _ISO_DATE_RE.finditer(content_text):
        entities.append({
            "entity_type": "date",
            "value": m.group(1),
            "confidence": 0.95,
            "context_snippet": _clip(content_text, m),
        })

    # Dates: natural
    for m in _NATURAL_DATE_RE.finditer(content_text):
        entities.append({
            "entity_type": "date",
            "value": m.group(1),
            "confidence": 0.85,
            "context_snippet": _clip(content_text, m),
        })

    # Dates: relative
    for m in _RELATIVE_DATE_RE.finditer(content_text):
        entities.append({
            "entity_type": "date",
            "value": m.group(1).lower(),
            "confidence": 0.7,
            "context_snippet": _clip(content_text, m),
        })

    # Decisions
    for m in _DECISION_RE.finditer(content_text):
        text_val = m.group(1).strip()
        if len(text_val) > 15:  # skip very short false positives
            entities.append({
                "entity_type": "decision",
                "value": text_val[:300],
                "confidence": 0.7,
                "context_snippet": _clip(content_text, m, window=120),
            })

    # Action items
    for m in _ACTION_RE.finditer(content_text):
        text_val = m.group(1).strip()
        if len(text_val) > 10:
            entities.append({
                "entity_type": "action_item",
                "value": text_val[:300],
                "confidence": 0.7,
                "context_snippet": _clip(content_text, m, window=120),
            })

    # Projects (JIRA-style keys)
    for m in _PROJECT_KEY_RE.finditer(content_text):
        entities.append({
            "entity_type": "project",
            "value": m.group(1),
            "confidence": 0.85,
            "context_snippet": _clip(content_text, m),
        })

    # Topics (capitalized multi-word phrases)
    seen_topics: set[str] = set()
    for m in _TOPIC_RE.finditer(content_text):
        topic = m.group(1)
        topic_lower = topic.lower()
        if topic_lower not in seen_topics and len(topic) > 5:
            seen_topics.add(topic_lower)
            entities.append({
                "entity_type": "topic",
                "value": topic,
                "confidence": 0.5,
                "context_snippet": _clip(content_text, m),
            })

    return entities


def _dedup_entities(entities: list[dict]) -> list[dict]:
    """Remove duplicate entities by (type, normalized value)."""
    seen: set[tuple[str, str]] = set()
    result: list[dict] = []
    for e in entities:
        key = (e["entity_type"], e["value"].lower().strip())
        if key not in seen:
            seen.add(key)
            result.append(e)
    return result


def extract_entities(
    content_id: str,
    content_text: str,
    mode: str = "regex",
) -> list[dict]:
    """Extract entities from content text and store in DB.

    Args:
        content_id: The hub content ID this text comes from.
        content_text: The raw text to extract from.
        mode: 'regex' (instant) or 'llm' (deep, future).

    Returns:
        List of extracted entity dicts.
    """
    if not content_text or not content_text.strip():
        return []

    raw_entities = _extract_regex(content_text)
    entities = _dedup_entities(raw_entities)

    if not entities:
        return []

    now = datetime.utcnow().isoformat()

    # Store in DB — delete old extractions for this content first, then insert
    with get_db() as conn:
        conn.execute(
            delete(extracted_entities).where(
                extracted_entities.c.content_id == content_id
            )
        )
        for e in entities:
            conn.execute(
                insert(extracted_entities).values(
                    id=str(uuid.uuid4()),
                    content_id=content_id,
                    entity_type=e["entity_type"],
                    value=e["value"],
                    confidence=e["confidence"],
                    source_mode=mode,
                    context_snippet=e.get("context_snippet"),
                    created_at=now,
                )
            )

    log.info(
        "entities_extracted",
        content_id=content_id,
        count=len(entities),
        mode=mode,
    )

    return entities


def extract_batch(content_ids: list[str], mode: str = "regex") -> dict:
    """Extract entities from multiple content items.

    Fetches content text from hub_content mirror table.

    Returns:
        Dict with 'total_entities', 'content_count', 'errors'.
    """
    total_entities = 0
    processed = 0
    errors: list[str] = []

    with get_db() as conn:
        rows = conn.execute(
            select(hub_content.c.id, hub_content.c.body)
            .where(hub_content.c.id.in_(content_ids))
        ).fetchall()

    for row in rows:
        cid = row.id
        text_val = row.body or ""
        try:
            entities = extract_entities(cid, text_val, mode=mode)
            total_entities += len(entities)
            processed += 1
        except Exception as e:
            log.warning("batch_extract_failed", content_id=cid, error=str(e))
            errors.append(f"{cid}: {e}")

    return {
        "total_entities": total_entities,
        "content_count": processed,
        "errors": errors,
    }
