"""Brain ingestion classifier — 3-tier (rules → embedding → LLM).

Per DESIGN.md §3.3:

- **Tier 1 (rules):** jira_key prefix, sender_rule, learned_rule. Backed
  by hub.db sender/rule tables in production; tests inject rules directly.
- **Tier 2 (embedding similarity):** per-project centroid (mean of last 50
  chunk embeddings). Top-1 wins if cosine > 0.70. In Phase 5, callers can
  inject pre-computed centroids; the real centroid store lands with
  retrieval-v3 in Phase 6.
- **Tier 3 (LLM):** stub in Phase 5 — returns Classification with method
  ``"unknown"`` and `needs_review=True`. Real Haiku-3.5 via QB Gateway with
  Gemma-7b-4bit MLX fallback lands in Phase 7.

All three tiers return a `Classification` (see `contract.py`) with method
tag so downstream auditors know which tier fired.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from app.services.ingest.contract import Classification

# --- Tier 1: rules ------------------------------------------------------------

JIRA_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9})-(\d{1,6})\b")


@dataclass(frozen=True)
class SenderRule:
    """sender (email/slack handle) -> project_id mapping."""

    sender: str  # lowercase compare
    project_id: str
    confidence: float = 0.95


@dataclass(frozen=True)
class JiraPrefixRule:
    """Jira project key prefix -> project_id mapping."""

    prefix: str  # uppercase
    project_id: str
    confidence: float = 1.0


def classify_by_rules(
    text: str,
    sender: str | None,
    sender_rules: Sequence[SenderRule] = (),
    jira_rules: Sequence[JiraPrefixRule] = (),
) -> Classification | None:
    """Return a Classification if a tier-1 rule fires, else None.

    Precedence: sender_rule > jira_prefix. (Email senders are a stronger
    signal than a Jira key embedded in body text.)
    """
    if sender:
        s_lower = sender.lower()
        for rule in sender_rules:
            if rule.sender.lower() == s_lower:
                return Classification(
                    project_id=rule.project_id,
                    confidence=rule.confidence,
                    method="rules",
                    needs_review=False,
                    rationale=f"sender_rule:{rule.sender}",
                )

    if jira_rules and text:
        # First match wins; rules are searched in declaration order.
        match = JIRA_KEY_RE.search(text)
        if match:
            prefix = match.group(1)
            for rule in jira_rules:
                if rule.prefix.upper() == prefix:
                    return Classification(
                        project_id=rule.project_id,
                        confidence=rule.confidence,
                        method="rules",
                        needs_review=False,
                        rationale=f"jira_prefix:{prefix}",
                    )

    return None


# --- Tier 2: embedding similarity ---------------------------------------------

# Type alias: embedder takes text, returns a vector (list of floats).
Embedder = Callable[[str], Sequence[float]]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


EMBEDDING_THRESHOLD = 0.70


def classify_by_embedding(
    text: str,
    embedder: Embedder | None,
    project_centroids: dict[str, Sequence[float]],
    threshold: float = EMBEDDING_THRESHOLD,
) -> Classification | None:
    """Return a Classification if top-1 centroid cosine > threshold, else None.

    `project_centroids` is a `{project_id: centroid_vector}` dict. Caller is
    responsible for keeping centroids fresh (Phase 6 background job; tests
    inject directly).
    """
    if embedder is None or not project_centroids:
        return None

    try:
        query = embedder(text)
    except Exception:
        return None
    if not query:
        return None

    best_project: str | None = None
    best_score = -1.0
    for pid, centroid in project_centroids.items():
        score = _cosine(query, centroid)
        if score > best_score:
            best_score = score
            best_project = pid

    if best_project is None or best_score < threshold:
        return None

    return Classification(
        project_id=best_project,
        confidence=float(best_score),
        method="embedding",
        needs_review=False,
        rationale=f"centroid_cosine:{best_score:.3f}",
    )


# --- Tier 3: LLM (Phase 5 stub) -----------------------------------------------


def classify_by_llm_stub(text: str, candidate_projects: Iterable[str]) -> Classification:
    """Phase 5 stub for the LLM tier.

    Real implementation (Phase 7):
        - primary: Claude Haiku-3.5 via QB Gateway (~/.coco/.qb-gateway-key)
        - fallback: Gemma-7b-4bit local via MLX (with `mlx.lock` flock)
        - writes one row to llm_invocations
        - respects budget.is_over_budget(today) gate

    For now: return needs_review=True so the document lands in
    brain_decision_queue as a `classify_candidate` and a human can route it.
    """
    _ = list(candidate_projects)  # touched so static analysis sees the param used
    return Classification(
        project_id=None,
        confidence=0.0,
        method="unknown",
        needs_review=True,
        rationale="llm_classifier_not_yet_wired_phase_5_stub",
    )


# --- Top-level: 3-tier dispatch -----------------------------------------------


def classify(
    text: str,
    sender: str | None = None,
    sender_rules: Sequence[SenderRule] = (),
    jira_rules: Sequence[JiraPrefixRule] = (),
    embedder: Embedder | None = None,
    project_centroids: dict[str, Sequence[float]] | None = None,
    candidate_projects: Iterable[str] = (),
) -> Classification:
    """Run the 3-tier classifier. Always returns a Classification.

    The result's `method` field tells the caller which tier fired:
        - "rules"     — Tier 1 hit
        - "embedding" — Tier 2 hit
        - "unknown"   — Tier 3 stub (needs_review=True until Phase 7)
    """
    # Tier 1
    hit = classify_by_rules(text, sender, sender_rules, jira_rules)
    if hit is not None:
        return hit

    # Tier 2
    hit = classify_by_embedding(text, embedder, project_centroids or {})
    if hit is not None:
        return hit

    # Tier 3 (stub)
    return classify_by_llm_stub(text, candidate_projects)
