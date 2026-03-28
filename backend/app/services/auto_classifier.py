"""Auto-classification service for Knowledge Hub content.

Classifies unsorted content into projects using either:
1. Rule-based matching (fast, no API cost)
2. LLM-based classification via Anthropic Haiku (when rules are insufficient)

Confidence >= 0.85 -> auto-classify
Confidence < 0.85 -> suggest (show in suggestions tab for user review)
"""

import json
import os
import re
import uuid
import structlog
from datetime import datetime, timezone

from app.db.connections import get_hub_db, get_platform_db
from app.config import BRAIN_JSON_PATH

log = structlog.get_logger()

# Confidence thresholds
AUTO_CLASSIFY_THRESHOLD = 0.85
SUGGEST_THRESHOLD = 0.50


def classify_single(
    content_id: str,
    title: str,
    body: str | None,
    source: str | None,
    sender: str | None,
) -> dict:
    """Classify a single content item.

    Returns: {"project_id": str|None, "confidence": float, "reasoning": str, "method": "rule"|"llm"}
    """
    # Try rule-based first
    result = _rule_based_classify(title, body, source, sender)
    if result and result["confidence"] >= SUGGEST_THRESHOLD:
        return result

    # Fall back to LLM if available
    try:
        llm_result = _llm_classify(title, body, source, sender)
        if llm_result:
            return llm_result
    except Exception as e:
        log.warning("llm_classify_failed", content_id=content_id, error=str(e))

    return {
        "project_id": None,
        "confidence": 0.0,
        "reasoning": "No matching rules or LLM unavailable",
        "method": "rule",
    }


def classify_batch(items: list[dict]) -> list[dict]:
    """Classify a batch of content items.

    Each item should have: id, title, body, source, sender
    Returns list of classification results with content_id added.
    """
    results = []
    for item in items:
        result = classify_single(
            content_id=item["id"],
            title=item.get("title", ""),
            body=item.get("body"),
            source=item.get("source"),
            sender=item.get("sender"),
        )
        result["content_id"] = item["id"]
        results.append(result)
    return results


def process_unsorted(limit: int = 50) -> dict:
    """Process unsorted content from hub.db.

    Returns: {"auto_classified": int, "suggested": int, "skipped": int}
    """
    stats = {"auto_classified": 0, "suggested": 0, "skipped": 0}

    # Get unsorted items from hub.db
    unsorted = _get_unsorted_content(limit)
    if not unsorted:
        return stats

    # Classify each
    results = classify_batch(unsorted)

    # Apply results
    for result in results:
        if result["confidence"] >= AUTO_CLASSIFY_THRESHOLD and result["project_id"]:
            _apply_classification(
                result["content_id"],
                result["project_id"],
                result["confidence"],
                result["reasoning"],
                auto=True,
            )
            stats["auto_classified"] += 1
        elif result["confidence"] >= SUGGEST_THRESHOLD and result["project_id"]:
            _save_suggestion(
                result["content_id"],
                result["project_id"],
                result["confidence"],
                result["reasoning"],
            )
            stats["suggested"] += 1
        else:
            stats["skipped"] += 1

    return stats


def _get_unsorted_content(limit: int) -> list[dict]:
    """Get unsorted content from hub.db that hasn't been classified yet."""
    try:
        with get_hub_db() as hub:
            rows = hub.execute(
                "SELECT id, title, body, source FROM content ORDER BY created_at DESC LIMIT ?",
                (limit * 3,),
            ).fetchall()

        if not rows:
            return []

        content_ids = [r["id"] for r in rows]

        # Filter out already-classified items
        with get_platform_db() as pdb:
            classified = set()
            for cid in content_ids:
                row = pdb.execute(
                    "SELECT hub_content_id FROM content_classifications WHERE hub_content_id = ?",
                    (cid,),
                ).fetchone()
                if row:
                    classified.add(cid)

        # Also filter out items already assigned to a project (hub.db)
        with get_hub_db() as hub:
            assigned = set()
            try:
                for cid in content_ids:
                    row = hub.execute(
                        "SELECT content_id FROM project_content WHERE content_id = ?",
                        (cid,),
                    ).fetchone()
                    if row:
                        assigned.add(cid)
            except Exception:
                # project_content table may not exist
                pass

        unsorted = []
        for r in rows:
            if r["id"] not in classified and r["id"] not in assigned:
                unsorted.append(dict(r))
            if len(unsorted) >= limit:
                break

        return unsorted
    except Exception as e:
        log.warning("get_unsorted_failed", error=str(e))
        return []


def _rule_based_classify(
    title: str, body: str | None, source: str | None, sender: str | None
) -> dict | None:
    """Rule-based classification using keyword and sender matching."""
    text = f"{title} {body or ''}".lower()
    sender_lower = (sender or "").lower()

    # Load project rules from brain.json
    rules = _load_classification_rules()

    best_match = None
    best_confidence = 0.0

    for project_id, project_rules in rules.items():
        confidence = 0.0
        reasons = []

        # Keyword matching
        keywords = project_rules.get("keywords", [])
        matched_keywords = [kw for kw in keywords if kw.lower() in text]
        if matched_keywords:
            keyword_conf = min(0.4 + 0.15 * len(matched_keywords), 0.85)
            confidence = max(confidence, keyword_conf)
            reasons.append(f"keywords: {', '.join(matched_keywords)}")

        # Sender matching
        senders = project_rules.get("senders", [])
        if any(s.lower() in sender_lower for s in senders if s):
            confidence = max(confidence, 0.80)
            reasons.append(f"sender match: {sender}")

        # Jira key matching
        jira_key = project_rules.get("jira_key", "")
        if jira_key and jira_key.upper() in (title or "").upper():
            confidence = max(confidence, 0.95)
            reasons.append(f"jira key: {jira_key}")

        if confidence > best_confidence:
            best_confidence = confidence
            best_match = {
                "project_id": project_id,
                "confidence": confidence,
                "reasoning": "; ".join(reasons),
                "method": "rule",
            }

    return best_match


def _load_classification_rules() -> dict:
    """Load classification rules from brain.json and hub.db projects."""
    rules: dict = {}

    # Load from brain.json
    try:
        brain_path = str(BRAIN_JSON_PATH)
        if os.path.exists(brain_path):
            with open(brain_path) as f:
                brain = json.load(f)

            # Extract sender->project mappings from people
            people = brain.get("people", {})
            if isinstance(people, dict):
                for name, info in people.items():
                    if isinstance(info, dict):
                        for proj in info.get("projects", []):
                            if proj not in rules:
                                rules[proj] = {"keywords": [], "senders": [], "jira_key": ""}
                            rules[proj]["senders"].append(name)
                            if info.get("full_name"):
                                rules[proj]["senders"].append(info["full_name"])
    except Exception as e:
        log.debug("brain_rules_load_failed", error=str(e))

    # Load project info from hub.db
    try:
        with get_hub_db() as hub:
            projects = hub.execute(
                "SELECT id, name, jira_project_key FROM projects WHERE active = 1"
            ).fetchall()
            for p in projects:
                pid = p["id"]
                if pid not in rules:
                    rules[pid] = {"keywords": [], "senders": [], "jira_key": ""}
                # Add project name words as keywords
                name_words = [w.lower() for w in (p["name"] or "").split() if len(w) > 2]
                rules[pid]["keywords"].extend(name_words)
                if p.get("jira_project_key"):
                    rules[pid]["jira_key"] = p["jira_project_key"]
    except Exception as e:
        log.debug("hub_rules_load_failed", error=str(e))

    return rules


def _llm_classify(
    title: str, body: str | None, source: str | None, sender: str | None
) -> dict | None:
    """Use Anthropic API (Haiku) to classify content. Returns None if unavailable."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    # Get available projects
    try:
        with get_hub_db() as hub:
            projects = hub.execute(
                "SELECT id, name FROM projects WHERE active = 1"
            ).fetchall()
        project_list = "\n".join(f"- {p['id']}: {p['name']}" for p in projects)
    except Exception:
        return None

    if not project_list:
        return None

    prompt = f"""Classify this content into one of the following projects. Return JSON only.

Projects:
{project_list}

Content:
Title: {title}
Source: {source or 'unknown'}
Sender: {sender or 'unknown'}
Body excerpt: {(body or '')[:500]}

Return exactly this JSON format (no other text):
{{"project_id": "the-project-id", "confidence": 0.85, "reasoning": "brief reason"}}

If no project matches, return: {{"project_id": null, "confidence": 0.0, "reasoning": "no match"}}"""

    try:
        import httpx

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 256,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("content", [{}])[0].get("text", "").strip()
    except Exception as e:
        log.warning("llm_classify_api_failed", error=str(e))
        return None

    # Parse JSON from response
    try:
        # Handle markdown code blocks
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        parsed = json.loads(content)
        return {
            "project_id": parsed.get("project_id"),
            "confidence": float(parsed.get("confidence", 0.0)),
            "reasoning": parsed.get("reasoning", "LLM classification"),
            "method": "llm",
        }
    except (json.JSONDecodeError, ValueError):
        log.warning("llm_classify_parse_failed", content=content[:200])
        return None


def _apply_classification(
    content_id: str,
    project_id: str,
    confidence: float,
    reasoning: str,
    auto: bool = False,
):
    """Save classification to platform.db."""
    try:
        with get_platform_db() as db:
            db.execute(
                """INSERT OR REPLACE INTO content_classifications
                   (id, hub_content_id, classified_project_id, project_id, confidence, reasoning,
                    auto_classified, status, action, classified_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'accepted', 'classify', datetime('now'), datetime('now'))""",
                (
                    str(uuid.uuid4()),
                    content_id,
                    project_id,
                    project_id,
                    confidence,
                    reasoning,
                    1 if auto else 0,
                ),
            )
            db.commit()
    except Exception as e:
        log.warning("apply_classification_failed", content_id=content_id, error=str(e))


def _save_suggestion(
    content_id: str, project_id: str, confidence: float, reasoning: str
):
    """Save a classification suggestion for user review."""
    try:
        with get_platform_db() as db:
            db.execute(
                """INSERT OR REPLACE INTO content_classifications
                   (id, hub_content_id, classified_project_id, suggested_project_id, confidence,
                    reasoning, auto_classified, status, action, classified_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 0, 'suggested', 'classify', datetime('now'), datetime('now'))""",
                (
                    str(uuid.uuid4()),
                    content_id,
                    project_id,
                    project_id,
                    confidence,
                    reasoning,
                ),
            )
            db.commit()
    except Exception as e:
        log.warning("save_suggestion_failed", content_id=content_id, error=str(e))
