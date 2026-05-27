"""Brain ingestion contract — IngestRequest / IngestResult.

Mirrors the `IngestionEnvelope` dataclass from DESIGN.md §3.1 in Pydantic so
HTTP callers (and tests) can validate at the API boundary.

Per INTEGRATION-CONTRACT.md §2.1, all ingestion writes flow through the
FastAPI process (single-writer discipline). This module defines only the
data shapes — the actual write happens inside `router.dispatch`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# Closed set of source adapters (DESIGN.md §3.1)
SourceType = Literal[
    "outlook",
    "slack",
    "confluence",
    "jira",
    "voice",
    "screenshot",
    "manual",
]

# Closed set of content types
ContentType = Literal[
    "email",
    "voice_memo",
    "doc",
    "link",
    "image",
    "chat_message",
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class IngestRequest(BaseModel):
    """Source-adapter envelope. One row per item adapters drop into the queue.

    Mirrors `IngestionEnvelope` (DESIGN.md §3.1). Keyed by `source_hash`
    (sha256 of canonical text) at the storage layer — duplicate inserts
    are rejected unless `force=True`.
    """

    source: SourceType
    source_id: str = Field(min_length=1, max_length=512)
    source_hash: str | None = Field(
        default=None,
        description=(
            "Optional pre-computed sha256 of canonical text. If omitted, the "
            "dispatcher computes it from raw_text."
        ),
    )
    content_type: ContentType
    raw_text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str | None = Field(
        default=None,
        description="ISO8601 of original event. Defaults to now() if omitted.",
    )
    attachments: list[str] = Field(default_factory=list)
    project_id: str | None = Field(
        default=None,
        description=(
            "Optional caller-supplied project hint. The classifier may "
            "override based on rules / embedding similarity / LLM."
        ),
    )
    force: bool = Field(
        default=False,
        description=(
            "Bypass exact + near-dup checks. Honored end-to-end (eff2b97 "
            "fix is structural in v3 — every write call propagates this "
            "bit down to the SQL INSERT)."
        ),
    )

    @field_validator("timestamp")
    @classmethod
    def _normalize_ts(cls, v: str | None) -> str:
        return v or _iso_now()

    @field_validator("source_hash")
    @classmethod
    def _validate_hash(cls, v: str | None) -> str | None:
        if v is None:
            return None
        # sha256 hex = 64 lowercase hex chars
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("source_hash must be 64-char hex (sha256)")
        return v.lower()


class Classification(BaseModel):
    """Output of the 3-tier classifier (DESIGN.md §3.3)."""

    project_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    method: Literal["rules", "embedding", "llm", "unknown"]
    needs_review: bool = False
    rationale: str | None = None


class IngestResult(BaseModel):
    """Outcome of a single envelope's pass through the pipeline."""

    document_id: str | None = Field(
        default=None,
        description="ULID assigned to the new brain_documents row. None on dedup hit.",
    )
    source_hash: str
    deduped: bool = Field(
        default=False,
        description="True if exact source_hash hit and force=False.",
    )
    near_duplicate_of: str | None = Field(
        default=None,
        description=(
            "If a near-duplicate (Jaccard > 0.90) was found, the doc_id of "
            "the canonical document. The new envelope is still ingested; an "
            "edge `near_dup_of` is written. None when no near-dup found."
        ),
    )
    classification: Classification | None = None
    classification_needs_review: bool = False
    ingested_at: str = Field(default_factory=_iso_now)
    persisted: bool = Field(
        default=False,
        description=(
            "True if a row was written. False on dedup hit (no write) or "
            "on backpressure / maintenance flag (envelope re-queued)."
        ),
    )
    notes: list[str] = Field(default_factory=list)
