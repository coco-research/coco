"""Brain ingestion v3 — unified ingest pipeline.

Implements the contract from `.planning/v3/brain/INTEGRATION-CONTRACT.md` and
the design from `.planning/v3/brain/DESIGN.md` §Ingestion.

Public surface:
    - contract.IngestRequest / IngestResult — Pydantic envelope per source adapter
    - router.dispatch(request) — routes to source-specific handler
    - dedup.source_hash(text) / dedup.near_dup(...) — exact + near-dup detection
    - classifier.classify(text, projects) — 3-tier (rules / embedding / LLM)

LLM tier is a stub in this phase (Phase 5) — returns ("unknown", needs_review)
when rules + embedding fail. Real LLM (QB Gateway Haiku + Gemma MLX fallback)
lands in Phase 7.
"""

from app.services.ingest.contract import (
    IngestRequest,
    IngestResult,
    Classification,
)
from app.services.ingest.router import dispatch, register_handler

__all__ = [
    "IngestRequest",
    "IngestResult",
    "Classification",
    "dispatch",
    "register_handler",
]
