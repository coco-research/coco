"""brain_query.py — POST /api/brain/query (Phase 8 / Brain B2).

Wraps `RetrievalPipeline` behind the canonical `BrainQuery` → `BrainQueryResult`
contract from INTEGRATION.md §4.9.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.services.brain.retrieval_pipeline import (
    BrainQuery as _BrainQuery,
    QueryFilters,
    Surface,
    get_retrieval_service,
)


router = APIRouter(tags=["Brain"])


# ---------------------------------------------------------------------------
# Wire types — match the TypeScript contract in INTEGRATION.md §4.9
# ---------------------------------------------------------------------------


class BrainQueryFilters(BaseModel):
    source: Optional[list[str]] = None
    since: Optional[str] = None
    until: Optional[str] = None
    person_id: Optional[str] = None
    project_id: Optional[str] = None
    decay: Optional[str] = Field(
        default="default", pattern=r"^(default|none|aggressive)$"
    )


class BrainQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    project_id: Optional[str] = None
    surface: str = Field(..., pattern=r"^(chat|agent_context|triage|search|briefing)$")
    top_k: Optional[int] = Field(default=None, ge=1, le=200)
    use_rerank: bool = False
    filters: Optional[BrainQueryFilters] = None


class BrainHit(BaseModel):
    document_id: str
    chunk_id: str
    snippet: str
    score: float
    source: str
    source_id: str
    project_id: Optional[str] = None
    ts: Optional[str] = None
    mentions: list[dict] = Field(default_factory=list)
    near_dups: list[str] = Field(default_factory=list)


class BrainQueryResult(BaseModel):
    hits: list[BrainHit]
    total_candidates: int
    retrieval_ms: float
    packed_tokens: int
    truncated: bool
    query_id: str


def _snippet(text: str, max_chars: int = 200) -> str:
    s = (text or "").strip().replace("\n", " ")
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


@router.post(
    "/api/brain/query",
    response_model=BrainQueryResult,
    summary="Hybrid retrieval over brain knowledge",
    description=(
        "Hybrid FTS5 + vector + RRF + decay + optional rerank retrieval. "
        "Returns surface-budget-packed hits per the canonical "
        "`BrainQuery` → `BrainQueryResult` contract (INTEGRATION.md §4.9)."
    ),
)
async def brain_query(
    req: BrainQueryRequest,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
) -> BrainQueryResult:
    # Build the internal query object.
    try:
        surface = Surface(req.surface)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"unknown surface: {req.surface}")

    f = req.filters or BrainQueryFilters()
    # project_id can live at top-level or under filters; prefer top-level.
    project_id = req.project_id or f.project_id

    filters = QueryFilters(
        project_id=project_id,
        since=f.since,
        until=f.until,
        decay=f.decay or "default",
    )
    bq = _BrainQuery(
        text=req.query,
        surface=surface,
        top_k=req.top_k,
        use_rerank=req.use_rerank,
        filters=filters,
    )

    svc = get_retrieval_service()
    result = svc.search(bq)

    hits: list[BrainHit] = []
    for h in result.hits:
        hits.append(
            BrainHit(
                document_id=h.chunk.document_id,
                chunk_id=h.chunk.id,
                snippet=_snippet(h.chunk.text),
                score=h.score,
                source="brain",
                source_id=h.chunk.document_id,
                project_id=h.chunk.project_id,
                ts=h.chunk.timestamp,
                mentions=[],
                near_dups=[],
            )
        )

    return BrainQueryResult(
        hits=hits,
        total_candidates=result.total_candidates,
        retrieval_ms=result.retrieval_ms,
        packed_tokens=result.packed_tokens,
        truncated=result.truncated,
        query_id=result.query_id,
    )
