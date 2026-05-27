"""Brain ingestion router — source-aware dispatch.

Each `IngestRequest` is routed to a source-specific handler that knows how
to pre-process the envelope (extract sender, normalize body, surface links).
After that the *unified* pipeline runs: dedup → classify → write → event.

Handlers are registered via `register_handler(source, fn)`. Built-in
handlers for the v3 sources live below. Tests can register a fake handler
and unregister it cleanly.

Phase 5 status:
    - dedup: in-memory + persistent-store hook (defaults to in-memory)
    - classify: 3-tier with LLM stubbed
    - write: hook (`PersistFn`); the real `brain_documents` writer lands
      when the Alembic migration ships (Phase 5.5 / Phase 6)
    - event: `brain.ingested` SSE via `event_bus.emit`
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Protocol, Sequence
from uuid import uuid4

from app.services.ingest.classifier import (
    JiraPrefixRule,
    SenderRule,
    classify,
)
from app.services.ingest.contract import (
    Classification,
    IngestRequest,
    IngestResult,
)
from app.services.ingest.dedup import (
    find_near_duplicate,
    source_hash as compute_source_hash,
)

# Phase 7 / Brain B3: identity-resolution hook. Imported lazily-safe; the
# resolver itself has no DB deps so the import is cheap.
from app.services.brain.entity_resolver import (
    EntityResolver,
    InMemoryStore,
    resolve_person_for_ingest,
)


# --- Hooks --------------------------------------------------------------------


class PersistFn(Protocol):
    """Pluggable writer for `brain_documents`. Real impl lands in Phase 5.5."""

    def __call__(
        self,
        *,
        document_id: str,
        request: IngestRequest,
        source_hash: str,
        classification: Classification,
        near_duplicate_of: str | None,
    ) -> bool:
        ...


class SeenHashesFn(Protocol):
    """Returns True if `source_hash` has been ingested before."""

    def __call__(self, sha: str) -> bool:
        ...


class NearDupCandidatesFn(Protocol):
    """Returns recent `(doc_id, text)` pairs to compare against for near-dup."""

    def __call__(self, request: IngestRequest) -> Sequence[tuple[str, str]]:
        ...


class EmitFn(Protocol):
    def __call__(self, event_type: str, data: dict) -> None:
        ...


@dataclass
class IngestDeps:
    """Dependency bundle for `dispatch`.

    Defaults are safe in-memory stubs so the router is fully testable without
    DB/SSE wiring. The FastAPI endpoint binds production implementations.
    """

    seen_hashes: SeenHashesFn = field(
        default_factory=lambda: (lambda sha: False)  # noqa: E731
    )
    near_dup_candidates: NearDupCandidatesFn = field(
        default_factory=lambda: (lambda request: [])  # noqa: E731
    )
    persist: PersistFn | None = None
    emit: EmitFn | None = None
    sender_rules: Sequence[SenderRule] = field(default_factory=tuple)
    jira_rules: Sequence[JiraPrefixRule] = field(default_factory=tuple)
    project_centroids: dict[str, Sequence[float]] = field(default_factory=dict)
    embedder: Callable[[str], Sequence[float]] | None = None
    candidate_projects: Sequence[str] = field(default_factory=tuple)
    # Phase 7 / Brain B3: identity resolver. When supplied, the dispatcher
    # resolves the envelope's sender → canonical person_id *before* persist,
    # and maintains the bidirectional `person ↔ document` link in the
    # resolver's store after a successful write.
    resolver: EntityResolver | None = None


# --- Source-specific handlers -------------------------------------------------

SourceHandler = Callable[[IngestRequest], IngestRequest]

_HANDLERS: dict[str, SourceHandler] = {}


def register_handler(source: str, handler: SourceHandler) -> None:
    """Register a per-source pre-processor (e.g. extract email From: header)."""
    _HANDLERS[source] = handler


def unregister_handler(source: str) -> None:
    _HANDLERS.pop(source, None)


_EMAIL_FROM_RE = re.compile(r"^From:\s*(.+?)\s*$", re.MULTILINE | re.IGNORECASE)
_EMAIL_ADDR_RE = re.compile(r"<([^>]+@[^>]+)>")


def _email_handler(req: IngestRequest) -> IngestRequest:
    """Pull `sender_email` out of email body From: header if not in metadata."""
    md = dict(req.metadata)
    if not md.get("sender_email"):
        m = _EMAIL_FROM_RE.search(req.raw_text)
        if m:
            raw_from = m.group(1).strip()
            addr_m = _EMAIL_ADDR_RE.search(raw_from)
            md["sender_email"] = (addr_m.group(1) if addr_m else raw_from).lower()
    return req.model_copy(update={"metadata": md})


def _slack_handler(req: IngestRequest) -> IngestRequest:
    """Normalize `sender_handle` to lowercase (Slack handles are case-insensitive)."""
    md = dict(req.metadata)
    if "sender_handle" in md and isinstance(md["sender_handle"], str):
        md["sender_handle"] = md["sender_handle"].lower().lstrip("@")
    return req.model_copy(update={"metadata": md})


def _doc_handler(req: IngestRequest) -> IngestRequest:
    """No-op for now — confluence/doc/manual content arrives well-formed."""
    return req


def _link_handler(req: IngestRequest) -> IngestRequest:
    """No-op — link normalization happens in adapter before queueing."""
    return req


def _audio_handler(req: IngestRequest) -> IngestRequest:
    """Voice-memo transcripts arrive as raw_text already. Keep `voice` source tag."""
    return req


# Built-in registrations. Tests can override per-source.
register_handler("outlook", _email_handler)
register_handler("slack", _slack_handler)
register_handler("confluence", _doc_handler)
register_handler("jira", _doc_handler)
register_handler("manual", _doc_handler)
register_handler("voice", _audio_handler)
register_handler("screenshot", _link_handler)


# --- Main dispatch ------------------------------------------------------------


def _extract_sender(req: IngestRequest) -> str | None:
    md = req.metadata or {}
    return md.get("sender_email") or md.get("sender_handle") or md.get("sender")


def _resolve_sender_to_person(
    req: IngestRequest, resolver: EntityResolver | None
) -> str | None:
    """Phase 7 / Brain B3: resolve the envelope's sender to a canonical
    person_id using the EntityResolver. Returns None if no resolver is
    bound or nothing matched.
    """
    if resolver is None:
        return None
    md = req.metadata or {}
    return resolve_person_for_ingest(
        resolver,
        sender_email=md.get("sender_email"),
        sender_handle=md.get("sender_handle"),
        sender_name=md.get("sender_name") or md.get("sender"),
        candidate_project=req.project_id,
    )


def dispatch(request: IngestRequest, deps: IngestDeps | None = None) -> IngestResult:
    """Run a single envelope through the unified pipeline.

    Steps (DESIGN.md §3.2):
        1. Source-specific pre-processor
        2. Compute `source_hash` if not provided
        3. Exact dedup (skip if `force=True`)
        4. Near-dup check (records edge, does not skip write unless force=False
           AND jaccard==1.0 — which is exact and already handled at step 3)
        5. Three-tier classifier
        6. Persist (hook; no-op when persist=None — useful for tests)
        7. Emit `brain.ingested` SSE event (hook)
    """
    deps = deps or IngestDeps()

    # 1. Pre-process per source
    handler = _HANDLERS.get(request.source)
    if handler is None:
        # Unknown source — pass through without raising (we still want a
        # result row in activity_log; the caller can decide to reject upstream).
        request = request.model_copy()
    else:
        request = handler(request)

    # 2. Compute source_hash if absent
    sha = request.source_hash or compute_source_hash(request.raw_text)
    notes: list[str] = []

    # 3. Exact dedup
    if not request.force and deps.seen_hashes(sha):
        return IngestResult(
            document_id=None,
            source_hash=sha,
            deduped=True,
            near_duplicate_of=None,
            classification=None,
            classification_needs_review=False,
            persisted=False,
            notes=["exact_dedup_hit"],
        )
    if request.force and deps.seen_hashes(sha):
        notes.append("exact_dedup_bypassed_by_force")

    # 4. Near-dup pass (does not skip write; records edge)
    near: tuple[str, float] | None = None
    try:
        candidates = list(deps.near_dup_candidates(request))
    except Exception:
        candidates = []
    if candidates:
        near = find_near_duplicate(request.raw_text, candidates)
        if near is not None:
            notes.append(f"near_dup_jaccard:{near[1]:.3f}")

    # 5. Classify
    classification = classify(
        text=request.raw_text,
        sender=_extract_sender(request),
        sender_rules=deps.sender_rules,
        jira_rules=deps.jira_rules,
        embedder=deps.embedder,
        project_centroids=deps.project_centroids,
        candidate_projects=deps.candidate_projects,
    )

    # If the caller hinted at a project_id and the classifier didn't beat
    # the hint, keep the hint but tag needs_review=True.
    if request.project_id and classification.method == "unknown":
        classification = classification.model_copy(
            update={
                "project_id": request.project_id,
                "rationale": (classification.rationale or "") + ";caller_hint_used",
            }
        )

    # 5b. Identity resolution (Phase 7 / Brain B3) — runs *before* persist
    # so the resolved person_id is observable even when persist is a no-op.
    resolved_person_id: str | None = None
    try:
        resolved_person_id = _resolve_sender_to_person(request, deps.resolver)
    except Exception as exc:  # pragma: no cover
        notes.append(f"resolver_error:{type(exc).__name__}")
        resolved_person_id = None
    if resolved_person_id is not None:
        notes.append(f"resolved_person:{resolved_person_id}")

    # 6. Persist
    document_id = f"doc_{uuid4().hex[:24]}"
    persisted = False
    if deps.persist is not None:
        try:
            persisted = bool(
                deps.persist(
                    document_id=document_id,
                    request=request,
                    source_hash=sha,
                    classification=classification,
                    near_duplicate_of=near[0] if near else None,
                )
            )
        except Exception as exc:  # pragma: no cover - logged but not fatal
            notes.append(f"persist_error:{type(exc).__name__}")
            persisted = False

    # 6b. Bidirectional link maintenance — only after successful persist
    if persisted and resolved_person_id and deps.resolver is not None:
        try:
            deps.resolver.store.link_document(resolved_person_id, document_id)
        except Exception as exc:  # pragma: no cover
            notes.append(f"bidi_link_error:{type(exc).__name__}")

    # 7. Emit SSE
    if deps.emit is not None and persisted:
        try:
            deps.emit(
                "brain.ingested",
                {
                    "document_id": document_id,
                    "source": request.source,
                    "project_id": classification.project_id,
                    "classification": classification.method,
                    "near_duplicate_of": near[0] if near else None,
                    "person_id": resolved_person_id,
                },
            )
        except Exception as exc:  # pragma: no cover
            notes.append(f"emit_error:{type(exc).__name__}")

    return IngestResult(
        document_id=document_id if persisted else None,
        source_hash=sha,
        deduped=False,
        near_duplicate_of=near[0] if near else None,
        classification=classification,
        classification_needs_review=classification.needs_review,
        persisted=persisted,
        notes=notes,
    )
