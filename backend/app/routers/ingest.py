"""POST /api/brain/ingest — single endpoint over the unified ingest pipeline.

Per INTEGRATION-CONTRACT.md §2.5, Brain has single-writer discipline: side
processes (adapters, think.py, stations) MUST POST envelopes here and never
touch platform.db directly.

Idempotency:
    The `Idempotency-Key` header is **required**. The handler stores
    `(idem_key, source_hash) -> IngestResult` in an LRU (16k entries) so
    the same envelope replayed via retry returns the cached result without
    re-ingesting. A mismatch (same key, different body) returns HTTP 409.

    A dedicated middleware will replace this in-router cache when the
    persistent idempotency store lands (Phase 5.5).
"""

from __future__ import annotations

from collections import OrderedDict
from threading import Lock

from fastapi import APIRouter, Header, HTTPException

from app.services.event_bus import event_bus
from app.services.ingest import dispatch
from app.services.ingest.contract import IngestRequest, IngestResult
from app.services.ingest.dedup import (
    idempotency_cache_key,
    source_hash as compute_source_hash,
)
from app.services.ingest.router import IngestDeps

router = APIRouter(prefix="/api/brain", tags=["Brain"])


# --- Idempotency cache (in-process, LRU) -------------------------------------

_IDEM_MAX = 16_384
_idem_cache: "OrderedDict[str, IngestResult]" = OrderedDict()
_idem_key_to_hash: dict[str, str] = {}
_idem_lock = Lock()


def _idem_get(idem_key: str, sha: str) -> IngestResult | None:
    """Return cached result if `(idem_key, sha)` was seen, else None.

    If `idem_key` was seen with a *different* sha → KeyError signal via
    `_idem_key_to_hash` mismatch (handler raises 409).
    """
    with _idem_lock:
        prior_sha = _idem_key_to_hash.get(idem_key)
        if prior_sha is None:
            return None
        if prior_sha != sha:
            raise ValueError("idempotency_key_body_mismatch")
        ck = idempotency_cache_key(idem_key, sha)
        return _idem_cache.get(ck)


def _idem_put(idem_key: str, sha: str, result: IngestResult) -> None:
    with _idem_lock:
        _idem_key_to_hash[idem_key] = sha
        ck = idempotency_cache_key(idem_key, sha)
        _idem_cache[ck] = result
        _idem_cache.move_to_end(ck)
        while len(_idem_cache) > _IDEM_MAX:
            oldest_ck, _ = _idem_cache.popitem(last=False)
            # Composite key is `<idem_key>:<source_hash>`. Idempotency-Key
            # itself may contain colons, so we must strip the fixed sha
            # suffix from the right rather than splitting on the first ':'.
            stale_key = oldest_ck.rsplit(":", 1)[0]
            # Only drop the key->hash entry if it still points to that ck
            if _idem_key_to_hash.get(stale_key) and oldest_ck.endswith(
                _idem_key_to_hash[stale_key]
            ):
                _idem_key_to_hash.pop(stale_key, None)


def _reset_idempotency_cache_for_tests() -> None:
    """Test-only helper. Not exposed in OpenAPI."""
    with _idem_lock:
        _idem_cache.clear()
        _idem_key_to_hash.clear()


# --- Production deps ---------------------------------------------------------

# In Phase 5 the persistent stores aren't yet wired. We default to in-memory
# stubs and let Phase 5.5 swap in the real `brain_writer` + `seen_hashes`
# via a small `set_default_deps()` shim if needed. For now: the dispatcher
# accepts no persistence (persisted=False) but still classifies and emits.
_default_deps_holder: dict[str, IngestDeps] = {
    "deps": IngestDeps(emit=event_bus.emit)
}


def set_default_deps(deps: IngestDeps) -> None:
    """Inject production wiring (used by main.py once writer lands)."""
    _default_deps_holder["deps"] = deps


def get_default_deps() -> IngestDeps:
    return _default_deps_holder["deps"]


# --- Endpoint ----------------------------------------------------------------


@router.post("/ingest", response_model=IngestResult, status_code=200)
def ingest(
    body: IngestRequest,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        description=(
            "Required. Caller-supplied UUID/ULID. The same key + body returns "
            "the cached result; same key + different body returns 409."
        ),
    ),
) -> IngestResult:
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(
            status_code=400, detail="Idempotency-Key header is required"
        )
    idem_key = idempotency_key.strip()

    # Compute sha once so the idempotency check matches what dispatch will use.
    sha = body.source_hash or compute_source_hash(body.raw_text)
    canonical_body = body.model_copy(update={"source_hash": sha})

    try:
        cached = _idem_get(idem_key, sha)
    except ValueError:
        raise HTTPException(
            status_code=409,
            detail="Idempotency-Key already used with a different body",
        )
    if cached is not None:
        return cached

    deps = get_default_deps()
    result = dispatch(canonical_body, deps=deps)

    _idem_put(idem_key, sha, result)
    return result
