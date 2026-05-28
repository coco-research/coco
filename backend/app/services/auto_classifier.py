"""Auto-classification service for Knowledge Hub content.

Classifies unsorted content into projects using:
1. Deterministic Jira-key router (highest priority, runs first)
2. Rule-based matching on subject/keywords/senders
3. LLM-based classification via Anthropic Haiku (when rules are insufficient)

Confidence >= 0.85 -> auto-classify
Confidence < 0.85 -> suggest (show in suggestions tab for user review)
"""

import json
import os
import re
import uuid
import structlog
from datetime import datetime, timezone

from sqlalchemy import select
from app.db.session import get_db
from app.db.tables import (
    hub_content, hub_project_content, hub_projects,
    content_classifications,
)
from app.db.compat import now, upsert
from app.config import BRAIN_JSON_PATH

log = structlog.get_logger()

# Confidence thresholds
AUTO_CLASSIFY_THRESHOLD = 0.85
SUGGEST_THRESHOLD = 0.50

# Deterministic Jira-prefix -> project mapping (KG audit phase 1, 2026-05-26).
# Confirmed against audit corpus in .planning/audits/kg-phase1-2026-05-26/.
# Runs BEFORE subject/keyword rules and short-circuits other classifiers.
JIRA_PREFIX_PROJECT: dict[str, str] = {
    "CROSSRISK": "reg-coe",
    "GRC": "audit-board",
    "SAIHUB": "audit-board-tax",
    "MPM": "optimize",
    "SPD": "optimize",
    "AIM": "tcre",
    "DEPL": "tcre",
    "IDAM": "tcre",
    "CCP": "tcre",
    "OTEP": "tcre",
    "MISC": "tcre",
    "ASM": "tcre",
    "PMCL": "tcre",
    "UCF": "privacy",
}

# Per-project keyword overrides. When a project_id is present here, ITS
# auto-derived keywords (from hub project name) are REPLACED by this list.
# Use sparingly — only when audit shows the auto-derived keywords are too
# broad (e.g. `acc` matched any text containing "anti", "corruption", "case",
# "management"). Phase-1 audit (2026-05-26) showed acc precision = 7%.
PROJECT_KEYWORD_OVERRIDES: dict[str, list[str]] = {
    "acc": ["anti-corruption", "fcpa", "bribery"],
}

# Per-project anti-keywords. If ANY anti-keyword appears in the content text,
# the project is disqualified for that item regardless of positive matches.
# Protects against cross-project bleed observed in the phase-1 audit (e.g.
# acc winning on tickets that obviously belong to reg-coe / optimize /
# audit-board / audit-board-tax).
PROJECT_ANTI_KEYWORDS: dict[str, list[str]] = {
    "acc": [
        "regcoe", "reg-coe", "reg coe",
        "3pi", "tpi", "aravo",
        "transfer pricing",
        "tax",
        "auditboard", "audit board", "soxhub", "grc next",
    ],
}

# Anchored at start-of-string so we only match a leading Jira key. Strip
# common email reply/forward prefixes first via _strip_subject_prefixes so
# "Re: CROSSRISK-1234" still routes correctly.
_JIRA_KEY_RE = re.compile(r"^([A-Z]+)-\d+")
_SUBJECT_PREFIX_RE = re.compile(r"^(re|fwd|fw|aw)\s*:\s*", re.IGNORECASE)


def _strip_subject_prefixes(title: str) -> str:
    """Strip leading 'Re:'/'Fwd:'/'FW:'/'AW:' so a Jira key is at index 0."""
    stripped = title or ""
    # Strip up to 4 nested reply prefixes ("Re: Fwd: Re: ...")
    for _ in range(4):
        new = _SUBJECT_PREFIX_RE.sub("", stripped).lstrip()
        if new == stripped:
            break
        stripped = new
    return stripped


def _jira_key_route(title: str) -> dict | None:
    """Deterministic router: map a Jira issue key in the title to a project.

    Returns a high-confidence (1.0) classification result if the title starts
    with a known Jira prefix, else None. This bypasses keyword/sender rules to
    avoid the false-positives observed in the phase-1 audit (e.g. `acc` keyword
    bleed onto CROSSRISK-* tickets).
    """
    if not title:
        return None
    cleaned = _strip_subject_prefixes(title)
    m = _JIRA_KEY_RE.match(cleaned)
    if not m:
        return None
    prefix = m.group(1).upper()
    project_id = JIRA_PREFIX_PROJECT.get(prefix)
    if not project_id:
        return None
    return {
        "project_id": project_id,
        "confidence": 1.0,
        "reasoning": f"jira-key router: {prefix}-* -> {project_id}",
        "method": "jira_key_router",
    }


def classify_single(
    content_id: str,
    title: str,
    body: str | None,
    source: str | None,
    sender: str | None,
) -> dict:
    """Classify a single content item.

    Pipeline order:
      1. Deterministic Jira-key router (short-circuits if matched)
      2. Rule-based subject/keyword/sender matching
      3. LLM fallback
    """
    jira_result = _jira_key_route(title)
    if jira_result is not None:
        return jira_result

    result = _rule_based_classify(title, body, source, sender)
    if result and result["confidence"] >= SUGGEST_THRESHOLD:
        return result

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
    stats = {"auto_classified": 0, "suggested": 0, "skipped": 0}

    unsorted = _get_unsorted_content(limit)
    if not unsorted:
        return stats

    results = classify_batch(unsorted)

    for result in results:
        if result["confidence"] >= AUTO_CLASSIFY_THRESHOLD and result["project_id"]:
            _apply_classification(
                result["content_id"], result["project_id"],
                result["confidence"], result["reasoning"], auto=True,
            )
            stats["auto_classified"] += 1
        elif result["confidence"] >= SUGGEST_THRESHOLD and result["project_id"]:
            _save_suggestion(
                result["content_id"], result["project_id"],
                result["confidence"], result["reasoning"],
            )
            stats["suggested"] += 1
        else:
            stats["skipped"] += 1

    return stats


def _get_unsorted_content(limit: int) -> list[dict]:
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(hub_content.c.id, hub_content.c.title, hub_content.c.body, hub_content.c.source)
                .order_by(hub_content.c.created_at.desc())
                .limit(limit * 3)
            ).fetchall()

            if not rows:
                return []

            content_ids = [r.id for r in rows]

            # Filter out already-classified items
            classified = set()
            for cid in content_ids:
                row = conn.execute(
                    select(content_classifications.c.hub_content_id)
                    .where(content_classifications.c.hub_content_id == cid)
                ).fetchone()
                if row:
                    classified.add(cid)

            # Filter out items already assigned to a project
            assigned = set()
            try:
                for cid in content_ids:
                    row = conn.execute(
                        select(hub_project_content.c.content_id)
                        .where(hub_project_content.c.content_id == cid)
                    ).fetchone()
                    if row:
                        assigned.add(cid)
            except Exception:
                pass

        unsorted = []
        for r in rows:
            if r.id not in classified and r.id not in assigned:
                unsorted.append(dict(r._mapping))
            if len(unsorted) >= limit:
                break

        return unsorted
    except Exception as e:
        log.warning("get_unsorted_failed", error=str(e))
        return []


def _rule_based_classify(
    title: str, body: str | None, source: str | None, sender: str | None
) -> dict | None:
    """Subject/keyword/sender classifier.

    Collects ALL candidate projects with non-zero confidence, then enforces
    the single-assignment invariant: pick the highest-confidence candidate
    and log the alternates (project_id + confidence) into the `reasoning`
    string so downstream stores (content_classifications) keep a record
    without needing a new table.
    """
    text_combined = f"{title} {body or ''}".lower()
    sender_lower = (sender or "").lower()

    rules = _load_classification_rules()

    candidates: list[dict] = []

    for project_id, project_rules in rules.items():
        # Anti-keyword disqualification: if any anti-keyword for this project
        # appears in the text, skip this project entirely. Prevents cross-
        # project keyword bleed identified in the phase-1 KG audit.
        anti_keywords = project_rules.get("anti_keywords", [])
        if anti_keywords and any(ak.lower() in text_combined for ak in anti_keywords):
            continue

        confidence = 0.0
        reasons = []

        keywords = project_rules.get("keywords", [])
        matched_keywords = [kw for kw in keywords if kw.lower() in text_combined]
        if matched_keywords:
            keyword_conf = min(0.4 + 0.15 * len(matched_keywords), 0.85)
            confidence = max(confidence, keyword_conf)
            reasons.append(f"keywords: {', '.join(matched_keywords)}")

        senders = project_rules.get("senders", [])
        if any(s.lower() in sender_lower for s in senders if s):
            confidence = max(confidence, 0.80)
            reasons.append(f"sender match: {sender}")

        jira_key = project_rules.get("jira_key", "")
        if jira_key and jira_key.upper() in (title or "").upper():
            confidence = max(confidence, 0.95)
            reasons.append(f"jira key: {jira_key}")

        if confidence > 0.0:
            candidates.append({
                "project_id": project_id,
                "confidence": confidence,
                "reasoning": "; ".join(reasons),
                "method": "rule",
            })

    if not candidates:
        return None

    # Single-assignment invariant: deterministic tie-break by (-confidence,
    # project_id) so the same content always lands in the same project across
    # runs. Stable + reproducible for audit.
    candidates.sort(key=lambda c: (-c["confidence"], c["project_id"]))
    winner = candidates[0]

    # Surface alternates in reasoning + a structured `alternates` field so
    # audit/review tooling can see which other projects competed without
    # needing a separate table.
    alternates = candidates[1:]
    if alternates:
        alt_str = ", ".join(
            f"{c['project_id']}@{c['confidence']:.2f}" for c in alternates[:5]
        )
        winner = {
            **winner,
            "reasoning": f"{winner['reasoning']} | alternates: {alt_str}",
            "alternates": [
                {"project_id": c["project_id"], "confidence": c["confidence"]}
                for c in alternates
            ],
        }

    return winner


def _load_classification_rules() -> dict:
    rules: dict = {}

    try:
        brain_path = str(BRAIN_JSON_PATH)
        if os.path.exists(brain_path):
            with open(brain_path) as f:
                brain = json.load(f)

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

    # Load project info from hub mirror
    try:
        with get_db() as conn:
            projects = conn.execute(
                select(hub_projects.c.id, hub_projects.c.name, hub_projects.c.jira_key)
                .where(hub_projects.c.active == 1)
            ).fetchall()
            for p in projects:
                pid = p.id
                if pid not in rules:
                    rules[pid] = {"keywords": [], "senders": [], "jira_key": ""}
                name_words = [w.lower() for w in (p.name or "").split() if len(w) > 2]
                rules[pid]["keywords"].extend(name_words)
                if p.jira_key:
                    rules[pid]["jira_key"] = p.jira_key
    except Exception as e:
        log.debug("hub_rules_load_failed", error=str(e))

    # Apply per-project keyword overrides (replace auto-derived keywords for
    # narrowly-scoped projects flagged by the phase-1 KG audit). The override
    # list FULLY REPLACES auto-derived keywords for the listed project.
    for pid, kw_list in PROJECT_KEYWORD_OVERRIDES.items():
        if pid in rules:
            rules[pid]["keywords"] = list(kw_list)
        else:
            rules[pid] = {"keywords": list(kw_list), "senders": [], "jira_key": ""}

    # Stamp anti-keyword lists onto each project. _rule_based_classify
    # disqualifies the project when ANY anti-keyword appears in the text.
    for pid, anti in PROJECT_ANTI_KEYWORDS.items():
        if pid not in rules:
            rules[pid] = {"keywords": [], "senders": [], "jira_key": ""}
        rules[pid]["anti_keywords"] = list(anti)

    return rules


def _llm_classify(
    title: str, body: str | None, source: str | None, sender: str | None
) -> dict | None:
    try:
        from app.services.agent_sdk_client import agent_sdk, record_sdk_cost
    except ImportError:
        return None

    if not agent_sdk.is_available():
        return None

    try:
        with get_db() as conn:
            projects = conn.execute(
                select(hub_projects.c.id, hub_projects.c.name)
                .where(hub_projects.c.active == 1)
            ).fetchall()
        project_list = "\n".join(f"- {p.id}: {p.name}" for p in projects)
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
        result = agent_sdk.quick_command(prompt, model="haiku", max_tokens=256, task_type="classification")
        content = result["content"].strip()

        record_sdk_cost(
            model=result.get("model", "haiku"),
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
            source="classifier",
        )
    except Exception as e:
        log.warning("llm_classify_api_failed", error=str(e))
        return None

    try:
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
    content_id: str, project_id: str, confidence: float, reasoning: str, auto: bool = False,
):
    try:
        with get_db() as conn:
            conn.execute(
                upsert(
                    content_classifications,
                    values={
                        "id": str(uuid.uuid4()),
                        "hub_content_id": content_id,
                        "classified_project_id": project_id,
                        "project_id": project_id,
                        "confidence": confidence,
                        "reasoning": reasoning,
                        "auto_classified": 1 if auto else 0,
                        "status": "accepted",
                        "action": "classify",
                        "classified_at": now(),
                        "created_at": now(),
                    },
                    conflict_cols=["hub_content_id"],
                    update_cols=[
                        "classified_project_id", "project_id", "confidence",
                        "reasoning", "auto_classified", "status", "action", "classified_at",
                    ],
                )
            )
    except Exception as e:
        log.warning("apply_classification_failed", content_id=content_id, error=str(e))


def _save_suggestion(content_id: str, project_id: str, confidence: float, reasoning: str):
    try:
        with get_db() as conn:
            conn.execute(
                upsert(
                    content_classifications,
                    values={
                        "id": str(uuid.uuid4()),
                        "hub_content_id": content_id,
                        "classified_project_id": project_id,
                        "suggested_project_id": project_id,
                        "confidence": confidence,
                        "reasoning": reasoning,
                        "auto_classified": 0,
                        "status": "suggested",
                        "action": "classify",
                        "classified_at": now(),
                        "created_at": now(),
                    },
                    conflict_cols=["hub_content_id"],
                    update_cols=[
                        "classified_project_id", "suggested_project_id", "confidence",
                        "reasoning", "auto_classified", "status", "action", "classified_at",
                    ],
                )
            )
    except Exception as e:
        log.warning("save_suggestion_failed", content_id=content_id, error=str(e))
