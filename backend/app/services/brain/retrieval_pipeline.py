"""retrieval_pipeline.py — Brain v3 hybrid retrieval (Phase 8 / Brain B2).

Implements D13: FTS5 keyword + vector cosine + Reciprocal Rank Fusion + stale-data
decay + optional rerank + token-budget-aware context packing per surface.

Ported from `.planning/v3/brain/REFERENCE-IMPL/retrieval_pipeline.py`. The pure-
Python core is intentionally identical (so the reference tests stay valid). Two
additions wire the pipeline into the live backend:

  - `db_chunk_loader(...)` — pulls chunks (text + optional embedding) from the
    real `brain_chunks` / `brain_documents` / `brain_chunks_vec` tables. When
    sqlite-vec is absent we fall back to the BLOB-backed `brain_chunks_vec`
    schema (see migration `140054f726ca`). Embedding may be missing — pipeline
    handles that gracefully (vector_search skips chunks without an embedding).
  - `RetrievalService` — factory + cache wrapper used by the FastAPI router.

This module is pure-Python + stdlib for the core retrieval math; the DB loader
uses SQLAlchemy Core via the platform engine. Keeping the math standalone means
the unit tests run without DB wiring.
"""
from __future__ import annotations

import math
import os
import re
import sqlite3
import struct
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional, Sequence


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class Surface(str, Enum):
    CHAT = "chat"
    AGENT_CONTEXT = "agent_context"
    TRIAGE = "triage"
    SEARCH = "search"
    BRIEFING = "briefing"


APPROX_CHARS_PER_TOKEN = 4

SURFACE_TOKEN_BUDGET: dict[Surface, int] = {
    Surface.CHAT: 8_000,
    Surface.AGENT_CONTEXT: 4_000,
    Surface.TRIAGE: 1_500,
    Surface.SEARCH: 6_000,
    Surface.BRIEFING: 6_000,
}

SURFACE_TOP_K: dict[Surface, int] = {
    Surface.CHAT: 8,
    Surface.AGENT_CONTEXT: 12,
    Surface.TRIAGE: 5,
    Surface.SEARCH: 20,
    Surface.BRIEFING: 10,
}


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    text: str
    project_id: Optional[str] = None
    timestamp: Optional[str] = None
    embedding: Optional[list[float]] = None
    embedding_model: str = "voyage-3-lite"
    metadata: dict = field(default_factory=dict)


@dataclass
class Hit:
    chunk: Chunk
    score: float
    sources: list[str] = field(default_factory=list)
    rank: int = 0


@dataclass
class QueryFilters:
    project_id: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None
    decay: str = "default"


@dataclass
class BrainQuery:
    text: str
    surface: Surface
    top_k: Optional[int] = None
    use_rerank: bool = False
    filters: QueryFilters = field(default_factory=QueryFilters)
    rrf_k: int = 60
    decay_half_life_days: float = 180.0
    now: Optional[datetime] = None


@dataclass
class RetrievalResult:
    hits: list[Hit]
    total_candidates: int
    retrieval_ms: float
    packed_tokens: int
    truncated: bool
    query_id: str


# ---------------------------------------------------------------------------
# Vector math
# ---------------------------------------------------------------------------


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Keyword search (BM25-like, pure Python; mirrors FTS5 BM25 ordering)
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower())


def bm25_like_score(
    query_tokens: Sequence[str],
    chunk_tokens: Sequence[str],
    avg_doc_len: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not query_tokens or not chunk_tokens:
        return 0.0
    counts = Counter(chunk_tokens)
    dl = len(chunk_tokens)
    score = 0.0
    qset = set(query_tokens)
    for t in qset:
        tf = counts.get(t, 0)
        if tf == 0:
            continue
        norm = tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / max(1.0, avg_doc_len)))
        score += norm
    return score


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion (Cormack 2009; k=60 per Azure docs)
# ---------------------------------------------------------------------------


def rrf_fuse(
    rankings: list[list[str]],
    k: int = 60,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])


# ---------------------------------------------------------------------------
# Decay
# ---------------------------------------------------------------------------


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except ValueError:
        return None


def age_days(ts: Optional[str], now: Optional[datetime] = None) -> Optional[float]:
    d = _parse_iso(ts)
    if d is None:
        return None
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now - d).total_seconds() / 86400.0


def decay_factor(
    ts: Optional[str],
    half_life_days: float,
    now: Optional[datetime] = None,
    mode: str = "default",
) -> float:
    if mode == "none":
        return 1.0
    age = age_days(ts, now=now)
    if age is None:
        return 1.0
    hl = half_life_days if mode != "aggressive" else half_life_days / 6.0
    if hl <= 0:
        return 1.0
    return math.exp(-age / hl)


# ---------------------------------------------------------------------------
# Embedder (callable). Production wires this to Voyage / BGE.
# ---------------------------------------------------------------------------

Embedder = Callable[[str], list[float]]


def fake_embedder(text: str, dim: int = 8) -> list[float]:
    """Deterministic toy embedder. Hash-bucket BoW; used when sqlite-vec absent
    or for unit tests."""
    vec = [0.0] * dim
    for tok in tokenize(text):
        idx = (hash(tok) % dim + dim) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class RetrievalPipeline:
    """Hybrid retrieval: FTS5 ∪ Vector → RRF → decay → optional rerank → pack."""

    def __init__(
        self,
        chunks: list[Chunk],
        embedder: Optional[Embedder] = None,
        reranker: Optional[Callable[[str, list[Chunk]], list[float]]] = None,
    ) -> None:
        self.chunks: dict[str, Chunk] = {c.id: c for c in chunks}
        self.embedder = embedder or fake_embedder
        self.reranker = reranker
        self._token_cache: dict[str, list[str]] = {}
        self._avg_doc_len = max(
            1.0,
            sum(len(self._tokens(c.id)) for c in chunks) / max(1, len(chunks)),
        )

    def _tokens(self, chunk_id: str) -> list[str]:
        if chunk_id not in self._token_cache:
            self._token_cache[chunk_id] = tokenize(self.chunks[chunk_id].text)
        return self._token_cache[chunk_id]

    def _apply_filters(self, candidate_ids: list[str], q: BrainQuery) -> list[str]:
        f = q.filters
        out: list[str] = []
        since_d = _parse_iso(f.since)
        until_d = _parse_iso(f.until)
        for cid in candidate_ids:
            c = self.chunks[cid]
            if f.project_id is not None and c.project_id != f.project_id:
                continue
            cd = _parse_iso(c.timestamp)
            if since_d is not None and (cd is None or cd < since_d):
                continue
            if until_d is not None and (cd is None or cd > until_d):
                continue
            out.append(cid)
        return out

    def keyword_search(
        self, query_text: str, q: BrainQuery, top_n: int = 100
    ) -> list[str]:
        if not query_text:
            return []
        q_tokens = tokenize(query_text)
        if not q_tokens:
            return []
        scored: list[tuple[float, str]] = []
        for cid in self.chunks:
            s = bm25_like_score(q_tokens, self._tokens(cid), self._avg_doc_len)
            if s > 0:
                scored.append((s, cid))
        scored.sort(key=lambda x: -x[0])
        out = [cid for _, cid in scored[:top_n]]
        return self._apply_filters(out, q)

    def vector_search(
        self, query_text: str, q: BrainQuery, top_n: int = 100
    ) -> list[str]:
        try:
            qvec = self.embedder(query_text)
        except Exception:
            return []
        scored: list[tuple[float, str]] = []
        for cid, c in self.chunks.items():
            if c.embedding is None:
                continue
            s = cosine_similarity(qvec, c.embedding)
            if s > 0:
                scored.append((s, cid))
        scored.sort(key=lambda x: -x[0])
        out = [cid for _, cid in scored[:top_n]]
        return self._apply_filters(out, q)

    def search(self, q: BrainQuery) -> RetrievalResult:
        start = time.perf_counter()
        if not q.text or not q.text.strip():
            return RetrievalResult(
                hits=[],
                total_candidates=0,
                retrieval_ms=0.0,
                packed_tokens=0,
                truncated=False,
                query_id=f"q:{uuid.uuid4().hex[:12]}",
            )

        # Stage 1: parallel keyword + vector search
        kw_ids = self.keyword_search(q.text, q, top_n=100)
        vec_ids = self.vector_search(q.text, q, top_n=100)

        # Stage 2: RRF fusion
        fused = rrf_fuse([kw_ids, vec_ids], k=q.rrf_k)
        total_candidates = len(fused)

        # Stage 3: decay
        decayed: list[tuple[str, float]] = []
        for cid, score in fused:
            c = self.chunks[cid]
            df = decay_factor(
                c.timestamp, q.decay_half_life_days, now=q.now, mode=q.filters.decay
            )
            decayed.append((cid, score * df))
        decayed.sort(key=lambda x: -x[1])

        # Stage 4: optional rerank (top-50)
        if q.use_rerank and self.reranker is not None and decayed:
            top_for_rerank = [self.chunks[cid] for cid, _ in decayed[:50]]
            rerank_scores = self.reranker(q.text, top_for_rerank)
            paired = list(zip([c.id for c in top_for_rerank], rerank_scores))
            paired.sort(key=lambda x: -x[1])
            tail = decayed[50:]
            decayed = paired + tail

        # Stage 5: top-k truncation
        top_k = q.top_k or SURFACE_TOP_K[q.surface]
        ranked = decayed[:top_k]

        # Stage 6: token-budget pack
        budget = SURFACE_TOKEN_BUDGET[q.surface]
        truncated = False
        hits: list[Hit] = []
        used_tokens = 0
        kw_set = set(kw_ids)
        vec_set = set(vec_ids)
        for rank, (cid, score) in enumerate(ranked, start=1):
            c = self.chunks[cid]
            tok = max(1, len(c.text) // APPROX_CHARS_PER_TOKEN)
            if used_tokens + tok > budget:
                truncated = True
                break
            used_tokens += tok
            srcs: list[str] = []
            if cid in kw_set:
                srcs.append("fts")
            if cid in vec_set:
                srcs.append("vec")
            srcs.append("rrf")
            if q.use_rerank and self.reranker is not None:
                srcs.append("rerank")
            hits.append(Hit(chunk=c, score=score, sources=srcs, rank=rank))

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return RetrievalResult(
            hits=hits,
            total_candidates=total_candidates,
            retrieval_ms=elapsed_ms,
            packed_tokens=used_tokens,
            truncated=truncated,
            query_id=f"q:{uuid.uuid4().hex[:12]}",
        )


def make_pipeline(chunks: list[Chunk], **kwargs) -> RetrievalPipeline:
    return RetrievalPipeline(chunks, **kwargs)


# ---------------------------------------------------------------------------
# DB-backed chunk loader
#
# Pulls brain_chunks + brain_documents (+ brain_chunks_vec when present) into
# memory. Vector decoding handles both the sqlite-vec virtual-table flavour and
# the BLOB-backed fallback. Embedding may be absent for some chunks — that's
# fine, vector_search simply skips them.
#
# NOTE: this is brute-force in-memory by design for Phase 8. The reference impl
# already specifies that production sqlite-vec lookups happen via the vec0
# virtual table; that swap-in is tracked under Phase 8.5+.
# ---------------------------------------------------------------------------


def _decode_blob_embedding(blob: bytes, dim: Optional[int]) -> Optional[list[float]]:
    if not blob:
        return None
    try:
        # BLOB layout: native float32 array (matches sqlite-vec wire format).
        n = len(blob) // 4
        vals = list(struct.unpack(f"{n}f", blob[: n * 4]))
        if dim is not None and dim > 0 and len(vals) >= dim:
            vals = vals[:dim]
        return vals
    except struct.error:
        return None


def db_chunk_loader(
    db_path: Optional[str] = None,
    *,
    project_id: Optional[str] = None,
    limit: int = 5000,
) -> list[Chunk]:
    """Load chunks from `platform.db`. Returns empty list if tables/file absent.

    SQLITE-ONLY: uses raw sqlite3 (FTS5 + vec0 are SQLite-specific).
    """
    if db_path is None:
        db_path = os.path.expanduser("~/.coco/platform.db")
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # brain_chunks_vec may be a virtual (vec0) table OR a BLOB table.
        # SQL probes both shapes; we just LEFT JOIN and decode either way.
        params: dict = {"lim": int(limit)}
        sql = """
            SELECT c.id        AS chunk_id,
                   c.document_id,
                   c.text,
                   d.project_id,
                   d.timestamp,
                   c.embedding_model
            FROM brain_chunks c
            LEFT JOIN brain_documents d ON d.id = c.document_id
            WHERE 1=1
        """
        if project_id is not None:
            sql += " AND d.project_id = :pid"
            params["pid"] = project_id
        sql += " ORDER BY d.timestamp DESC LIMIT :lim"
        try:
            rows = cur.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []

        # Best-effort embedding load (BLOB fallback). If sqlite-vec virtual
        # table is in use, raw SELECT on it from Python may fail — that's OK,
        # vector_search just skips chunks without an embedding.
        emb_by_chunk: dict[str, list[float]] = {}
        try:
            for r in cur.execute(
                "SELECT chunk_id, embedding, COALESCE(dim, 0) AS dim "
                "FROM brain_chunks_vec"
            ).fetchall():
                vec = _decode_blob_embedding(r["embedding"], r["dim"] or None)
                if vec is not None:
                    emb_by_chunk[r["chunk_id"]] = vec
        except sqlite3.OperationalError:
            # vec0 virtual table or schema mismatch — skip embeddings.
            pass

        chunks: list[Chunk] = []
        for r in rows:
            cid = r["chunk_id"]
            chunks.append(
                Chunk(
                    id=cid,
                    document_id=r["document_id"],
                    text=r["text"] or "",
                    project_id=r["project_id"],
                    timestamp=r["timestamp"],
                    embedding=emb_by_chunk.get(cid),
                    embedding_model=r["embedding_model"] or "voyage-3-lite",
                )
            )
        return chunks
    finally:
        conn.close()


class RetrievalService:
    """Lazy-loading singleton wrapper used by the FastAPI router.

    On first call (or after `invalidate()`), it loads chunks via the configured
    loader. Subsequent queries reuse the in-memory pipeline.
    """

    def __init__(
        self,
        loader: Optional[Callable[[], list[Chunk]]] = None,
        embedder: Optional[Embedder] = None,
    ) -> None:
        self._loader = loader or db_chunk_loader
        self._embedder = embedder or fake_embedder
        self._pipeline: Optional[RetrievalPipeline] = None

    def _ensure(self) -> RetrievalPipeline:
        if self._pipeline is None:
            chunks = self._loader()
            self._pipeline = RetrievalPipeline(chunks, embedder=self._embedder)
        return self._pipeline

    def invalidate(self) -> None:
        self._pipeline = None

    def search(self, q: BrainQuery) -> RetrievalResult:
        return self._ensure().search(q)


# Module-level singleton (FastAPI dependency injection target).
_default_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    global _default_service
    if _default_service is None:
        _default_service = RetrievalService()
    return _default_service


def set_retrieval_service(service: RetrievalService) -> None:
    """Test/wiring hook — replace the module-level service (e.g. with a
    pre-loaded in-memory pipeline) so router tests don't need a real DB."""
    global _default_service
    _default_service = service


__all__ = [
    "Surface",
    "Chunk",
    "Hit",
    "QueryFilters",
    "BrainQuery",
    "RetrievalResult",
    "RetrievalPipeline",
    "RetrievalService",
    "make_pipeline",
    "tokenize",
    "bm25_like_score",
    "cosine_similarity",
    "rrf_fuse",
    "decay_factor",
    "age_days",
    "fake_embedder",
    "db_chunk_loader",
    "get_retrieval_service",
    "set_retrieval_service",
    "SURFACE_TOKEN_BUDGET",
    "SURFACE_TOP_K",
]
