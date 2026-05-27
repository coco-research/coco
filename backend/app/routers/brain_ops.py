"""brain_ops.py — Admin endpoints for graph repair tooling.

Surface for the operator UI / CLI to:

  - detect orphaned aliases, broken bidirectional links, stray duplicates
  - repair bidirectional indexes
  - undo a recorded entity merge inside its reversible window

These endpoints sit behind the same `AuthMiddleware` as the rest of the
admin surface. They operate on the process-resident `EntityResolver`
singleton; the resolver itself persists its state into `platform.db`
through the existing tables (`brain_people`, `brain_person_aliases`,
`brain_merge_audit`, and — added in Phase 11 — `brain_merge_log`).

Routes are namespaced under `/api/brain/ops/...` to keep them off the
public `/api/brain` surface.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.brain import EntityResolver, InMemoryStore, make_resolver
from app.services.brain.entity_resolver import install_merge_log_hook
from app.services.brain.graph_ops import (
    detect_broken_bidirectional,
    detect_orphaned_aliases,
    detect_stray_duplicates,
    dedupe_strays,
    merge_log_rows,
    repair_bidirectional,
    repair_orphaned_aliases,
    undo_merge,
)


log = logging.getLogger(__name__)

router = APIRouter(tags=["Brain Ops"])


# ---------------------------------------------------------------------------
# Process-resident resolver singleton.
#
# In production this is replaced by a DI-injected, SQL-backed resolver;
# tests reach in via the `set_resolver` helper to install a fresh
# InMemoryStore before each case.
# ---------------------------------------------------------------------------

_STORE: Optional[InMemoryStore] = None
_RESOLVER: Optional[EntityResolver] = None


def _ensure_resolver() -> EntityResolver:
    global _STORE, _RESOLVER
    if _RESOLVER is None:
        _STORE, _RESOLVER = make_resolver()
        install_merge_log_hook()
    return _RESOLVER


def set_resolver(store: InMemoryStore, resolver: EntityResolver) -> None:
    """Inject a resolver — used by tests to start from a clean store."""
    global _STORE, _RESOLVER
    _STORE = store
    _RESOLVER = resolver
    install_merge_log_hook()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class DetectResponse(BaseModel):
    orphaned_aliases: list[dict]
    broken_bidi: list[dict]
    stray_duplicates: list[dict]
    merge_log_size: int


class RepairRequest(BaseModel):
    kind: str = Field(
        ..., description="One of: 'bidirectional' | 'orphaned_aliases'"
    )
    drop_orphans: bool = Field(
        False,
        description="When kind=orphaned_aliases, actually drop them (else dry-run)",
    )


class RepairResponse(BaseModel):
    fixed_count: int
    skipped_count: int
    notes: list[str]


class UndoRequest(BaseModel):
    merge_id: str
    restored_person_name: Optional[str] = None
    restored_person_email: Optional[str] = None


class UndoResponse(BaseModel):
    merge_id: str
    canonical_id: str
    aliases_dropped: int
    success: bool
    error: Optional[str] = None


class DedupeRequest(BaseModel):
    threshold: float = Field(0.90, ge=0.0, le=1.0)


class DedupeResponse(BaseModel):
    candidates: list[dict]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/api/brain/ops/detect", response_model=DetectResponse)
def detect() -> DetectResponse:
    """Surface graph drift to the operator."""
    resolver = _ensure_resolver()
    store = resolver.store

    return DetectResponse(
        orphaned_aliases=[
            {
                "alias_id": o.alias_id,
                "alias_value": o.alias_value,
                "alias_type": o.alias_type,
                "missing_canonical_id": o.missing_canonical_id,
            }
            for o in detect_orphaned_aliases(store)
        ],
        broken_bidi=[
            {
                "subject_id": b.subject_id,
                "subject_type": b.subject_type,
                "object_id": b.object_id,
                "object_type": b.object_type,
                "predicate": b.predicate,
            }
            for b in detect_broken_bidirectional(store)
        ],
        stray_duplicates=[
            {
                "person_a_id": s.person_a_id,
                "person_b_id": s.person_b_id,
                "similarity": s.similarity,
                "reason": s.reason,
            }
            for s in detect_stray_duplicates(store)
        ],
        merge_log_size=len(merge_log_rows()),
    )


@router.post("/api/brain/ops/repair", response_model=RepairResponse)
def repair(body: RepairRequest) -> RepairResponse:
    """Run a repair pass against the brain graph."""
    resolver = _ensure_resolver()
    store = resolver.store

    if body.kind == "bidirectional":
        outcome = repair_bidirectional(store)
    elif body.kind == "orphaned_aliases":
        outcome = repair_orphaned_aliases(store, drop=body.drop_orphans)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"unknown repair kind: {body.kind!r}",
        )

    return RepairResponse(
        fixed_count=outcome.fixed_count,
        skipped_count=outcome.skipped_count,
        notes=list(outcome.notes),
    )


@router.post("/api/brain/ops/undo", response_model=UndoResponse)
def undo(body: UndoRequest) -> UndoResponse:
    """Reverse a recorded entity merge."""
    resolver = _ensure_resolver()
    outcome = undo_merge(
        resolver,
        body.merge_id,
        restored_person_name=body.restored_person_name,
        restored_person_email=body.restored_person_email,
    )
    if not outcome.success:
        # 404 for unknown merges, 409 for already-undone, 500 otherwise.
        status = 404 if outcome.error == "unknown merge_id" else 409
        raise HTTPException(status_code=status, detail=outcome.error)

    return UndoResponse(
        merge_id=outcome.merge_id,
        canonical_id=outcome.canonical_id,
        aliases_dropped=outcome.aliases_dropped,
        success=outcome.success,
        error=outcome.error,
    )


@router.post("/api/brain/ops/dedupe", response_model=DedupeResponse)
def dedupe(body: DedupeRequest) -> DedupeResponse:
    """Surface stray duplicate candidates for human review."""
    resolver = _ensure_resolver()
    candidates = dedupe_strays(resolver.store, threshold=body.threshold)
    return DedupeResponse(
        candidates=[
            {
                "person_a_id": c.person_a_id,
                "person_b_id": c.person_b_id,
                "similarity": c.similarity,
                "reason": c.reason,
            }
            for c in candidates
        ]
    )
