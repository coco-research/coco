"""Brain ingestion dedup — exact (sha256) + near-dup (MinHash-lite).

Two layers, per DESIGN.md §3.4:

1. **Exact:** `source_hash = sha256(canonical_text)`. Rejected at SQL via
   `UNIQUE(source_hash)`. Bypassed by `force=True`.
2. **Near-dup:** background pass using token-shingle Jaccard (a MinHash-lite
   approximation that needs no external deps — full MinHash with datasketch
   lands when we wire the background worker in Phase 5.5). Threshold 0.90.

Both layers honor the `force` flag end-to-end (the eff2b97 fix is now
structural: see `force` in `IngestRequest` and propagated by `router.dispatch`).
"""

from __future__ import annotations

import hashlib
import re
from typing import Iterable

# --- Exact dedup --------------------------------------------------------------

_WS = re.compile(r"\s+")


def canonicalize(text: str) -> str:
    """Canonical form for hashing.

    Strip leading/trailing whitespace, collapse internal whitespace runs to
    a single space, lowercase. Keeps the hash stable across cosmetic edits
    (e.g. " hello\n world " and "hello world" hash identically).
    """
    if not text:
        return ""
    return _WS.sub(" ", text.strip()).lower()


def source_hash(text: str) -> str:
    """sha256 of the canonicalized text, hex digest (64 chars)."""
    return hashlib.sha256(canonicalize(text).encode("utf-8")).hexdigest()


# --- Near-dup (token-shingle Jaccard) -----------------------------------------

_TOKEN = re.compile(r"[a-z0-9]+")


def _shingles(text: str, k: int = 5) -> set[str]:
    """k-shingles of tokens. Token = [a-z0-9]+ on lowercased text.

    k=5 matches the default in datasketch examples for short-to-medium docs.
    For very short text (< k tokens) we fall back to single tokens.
    """
    tokens = _TOKEN.findall(text.lower())
    if len(tokens) < k:
        return set(tokens)
    return {" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def jaccard(a: str, b: str, k: int = 5) -> float:
    """Token-shingle Jaccard similarity in [0, 1]."""
    sa = _shingles(a, k=k)
    sb = _shingles(b, k=k)
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


NEAR_DUP_THRESHOLD = 0.90


def find_near_duplicate(
    incoming_text: str,
    candidates: Iterable[tuple[str, str]],
    threshold: float = NEAR_DUP_THRESHOLD,
) -> tuple[str, float] | None:
    """Return (doc_id, score) for the best near-dup if any, else None.

    `candidates` is an iterable of `(doc_id, text)`. Called with the recent-N
    window in production (typically last 500 docs from the same project +
    source) to keep cost bounded.
    """
    best: tuple[str, float] | None = None
    for doc_id, text in candidates:
        score = jaccard(incoming_text, text)
        if score >= threshold and (best is None or score > best[1]):
            best = (doc_id, score)
    return best


# --- Idempotency key helpers --------------------------------------------------


def idempotency_cache_key(idem_key: str, sha: str) -> str:
    """Compose the cache key for an Idempotency-Key + source_hash pair.

    Two requests with the same Idempotency-Key but different bodies are a
    client error (HTTP 409). The full sha is part of the key so the router
    can detect that mismatch without storing the full body.
    """
    return f"{idem_key}:{sha}"
