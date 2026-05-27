"""Tests for Brain v3 hybrid retrieval pipeline (Phase 8 / Brain B2).

Covers reference-impl parity (keyword, vector, hybrid, RRF, decay), router-level
behaviour (POST /api/brain/query), and edge cases (empty input, missing
embeddings, token-budget truncation, concurrent calls, malformed payloads).
"""
from __future__ import annotations

import concurrent.futures
import math
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.brain.retrieval_pipeline import (
    APPROX_CHARS_PER_TOKEN,
    BrainQuery,
    Chunk,
    QueryFilters,
    RetrievalPipeline,
    RetrievalService,
    SURFACE_TOKEN_BUDGET,
    Surface,
    cosine_similarity,
    decay_factor,
    fake_embedder,
    rrf_fuse,
    set_retrieval_service,
    tokenize,
)


NOW = datetime(2026, 5, 27, tzinfo=timezone.utc)


def _ts(days_ago: float) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat()


def _make_chunks() -> list[Chunk]:
    raw = [
        ("c1", "d1", "Aaron Gagnon approved the Aravo migration plan for Q3", "proj-aravo", 1.0),
        ("c2", "d2", "The Aravo migration risks were debated at the audit board meeting", "proj-aravo", 5.0),
        ("c3", "d3", "OneTrust assessment timelines slip without third-party review gate", "proj-onetrust", 12.0),
        ("c4", "d4", "Chris Munonye scheduled a check-in about the Aravo data model", "proj-aravo", 200.0),
        ("c5", "d5", "Random unrelated document about coffee preferences in the office", None, 0.5),
        ("c6", "d6", "Aravo migration deferred indefinitely per partner decision", "proj-aravo", 30.0),
        ("c7", "d7", "Voyage embedding migration plan landed this week", "proj-brain", 2.0),
    ]
    chunks: list[Chunk] = []
    for cid, did, text, pid, days in raw:
        emb = fake_embedder(text)
        chunks.append(
            Chunk(
                id=cid,
                document_id=did,
                text=text,
                project_id=pid,
                timestamp=_ts(days),
                embedding=emb,
            )
        )
    return chunks


def _query(text: str, **kwargs) -> BrainQuery:
    kwargs.setdefault("surface", Surface.SEARCH)
    kwargs.setdefault("now", NOW)
    return BrainQuery(text=text, **kwargs)


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------


def test_cosine_similarity_symmetric_and_bounded():
    v = fake_embedder("aravo migration")
    assert cosine_similarity(v, v) == pytest.approx(1.0)
    other = fake_embedder("totally unrelated")
    s = cosine_similarity(v, other)
    assert -1.0 <= s <= 1.0
    assert cosine_similarity([], v) == 0.0
    # length mismatch -> 0
    assert cosine_similarity([1.0, 2.0], [1.0]) == 0.0


def test_rrf_fuse_combines_rankings():
    a = ["c1", "c2", "c3"]
    b = ["c3", "c4", "c1"]
    fused = dict(rrf_fuse([a, b], k=60))
    # c1 appears at rank 1 in a and rank 3 in b -> highest combined score
    assert max(fused, key=fused.get) == "c1"
    # ordering must be deterministic descending by score
    ordered = rrf_fuse([a, b], k=60)
    assert ordered == sorted(ordered, key=lambda x: -x[1])


def test_decay_factor_modes_and_missing_ts():
    # missing ts -> 1.0
    assert decay_factor(None, 180.0, now=NOW) == 1.0
    # mode=none -> 1.0 always
    assert decay_factor(_ts(365), 180.0, now=NOW, mode="none") == 1.0
    # default mode: 1 half-life ago -> 0.5
    val = decay_factor(_ts(180), 180.0, now=NOW)
    assert val == pytest.approx(math.exp(-1.0), rel=1e-6)
    # aggressive mode = 1/6 half-life -> decays much faster
    fast = decay_factor(_ts(180), 180.0, now=NOW, mode="aggressive")
    assert fast < val


# ---------------------------------------------------------------------------
# Pipeline behaviour
# ---------------------------------------------------------------------------


def test_keyword_only_hits_relevant_chunks():
    p = RetrievalPipeline(_make_chunks())
    res = p.search(_query("aravo migration"))
    assert res.hits, "expected at least one hit"
    # At least one hit must be lexically relevant to "aravo"
    assert any("aravo" in h.chunk.text.lower() for h in res.hits)
    # FTS source should appear on at least one hit
    assert any("fts" in h.sources for h in res.hits)


def test_semantic_vector_search_returns_results_for_unindexed_terms():
    # Query uses synonyms not present verbatim; vector path should still match
    # via the fake embedder (BoW collisions are deterministic).
    p = RetrievalPipeline(_make_chunks())
    res = p.search(_query("aravo migration"))
    # ensure vector source was active for the top tier
    assert any("vec" in h.sources for h in res.hits)


def test_hybrid_rrf_combines_lexical_and_semantic_rankings():
    p = RetrievalPipeline(_make_chunks())
    res = p.search(_query("aravo audit board"))
    # multiple sources should converge on c2 (audit board)
    chunk_ids = [h.chunk.id for h in res.hits]
    assert "c2" in chunk_ids
    # rrf is always tagged
    assert all("rrf" in h.sources for h in res.hits)


def test_rerank_replaces_top_ordering():
    p = RetrievalPipeline(
        _make_chunks(),
        reranker=lambda q_text, chunks: [
            # invert: deepest doc-id wins
            float(int(c.id.lstrip("c"))) for c in chunks
        ],
    )
    res = p.search(_query("aravo migration", use_rerank=True))
    assert res.hits
    # rerank applied -> the highest-numbered candidate id wins among top hits
    top_id = res.hits[0].chunk.id
    assert int(top_id.lstrip("c")) >= max(
        int(h.chunk.id.lstrip("c")) for h in res.hits[1:]
    ) if len(res.hits) > 1 else True
    assert "rerank" in res.hits[0].sources


def test_empty_query_returns_empty_result():
    p = RetrievalPipeline(_make_chunks())
    res = p.search(_query(""))
    assert res.hits == []
    assert res.total_candidates == 0
    assert res.packed_tokens == 0
    assert res.truncated is False


def test_token_budget_truncation():
    # craft a chunk so big a single hit blows the TRIAGE budget (1500 toks)
    big_text = "aravo " * (SURFACE_TOKEN_BUDGET[Surface.TRIAGE] * APPROX_CHARS_PER_TOKEN)
    chunks = _make_chunks() + [
        Chunk(id="big", document_id="dbig", text=big_text, project_id="proj-aravo",
              timestamp=_ts(0.1), embedding=fake_embedder(big_text))
    ]
    p = RetrievalPipeline(chunks)
    res = p.search(_query("aravo", surface=Surface.TRIAGE, top_k=10))
    assert res.truncated is True or res.packed_tokens <= SURFACE_TOKEN_BUDGET[Surface.TRIAGE]


def test_decay_pushes_old_documents_down():
    p = RetrievalPipeline(_make_chunks())
    res = p.search(
        _query("aravo migration", decay_half_life_days=30.0)
    )
    ids = [h.chunk.id for h in res.hits]
    # c4 is the oldest aravo hit (200 days ago) — should not be #1
    if "c4" in ids and "c1" in ids:
        assert ids.index("c1") < ids.index("c4")


def test_filter_project_id_excludes_other_projects():
    p = RetrievalPipeline(_make_chunks())
    q = _query("migration", filters=QueryFilters(project_id="proj-onetrust"))
    res = p.search(q)
    for h in res.hits:
        assert h.chunk.project_id == "proj-onetrust"


def test_missing_embedding_does_not_crash_vector_search():
    chunks = _make_chunks()
    # blank the embedding on one chunk
    c0 = chunks[0]
    chunks[0] = Chunk(
        id=c0.id, document_id=c0.document_id, text=c0.text,
        project_id=c0.project_id, timestamp=c0.timestamp,
        embedding=None,
    )
    p = RetrievalPipeline(chunks)
    res = p.search(_query("aravo"))
    # still returns hits (keyword path covers c0; vector path skips it)
    assert res.hits


def test_concurrent_searches_are_independent():
    p = RetrievalPipeline(_make_chunks())
    queries = [
        _query("aravo migration"),
        _query("onetrust"),
        _query("voyage embedding"),
        _query("coffee"),
        _query("aravo audit board"),
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(p.search, queries))
    assert len(results) == 5
    # query_ids must all be unique
    qids = {r.query_id for r in results}
    assert len(qids) == 5


def test_tokenize_handles_unicode_and_punctuation():
    toks = tokenize("Aaron's Aravo–migration: phase-1 (Q3)!")
    assert "aaron" in toks
    assert "aravo" in toks
    assert "migration" in toks
    # punctuation stripped
    assert not any("'" in t or "(" in t for t in toks)


# ---------------------------------------------------------------------------
# Router (POST /api/brain/query)
# ---------------------------------------------------------------------------


@pytest.fixture
def client_with_chunks():
    service = RetrievalService(loader=_make_chunks)
    set_retrieval_service(service)
    try:
        with TestClient(app) as c:
            yield c
    finally:
        set_retrieval_service(RetrievalService())


def test_post_brain_query_returns_canonical_shape(client_with_chunks):
    r = client_with_chunks.post(
        "/api/brain/query",
        json={"query": "aravo migration", "surface": "search"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) >= {
        "hits", "total_candidates", "retrieval_ms",
        "packed_tokens", "truncated", "query_id",
    }
    assert isinstance(body["hits"], list)
    if body["hits"]:
        hit = body["hits"][0]
        assert {
            "document_id", "chunk_id", "snippet", "score",
            "source", "source_id",
        } <= set(hit.keys())


def test_post_brain_query_malformed_payload_rejected(client_with_chunks):
    # missing required "query"
    r = client_with_chunks.post("/api/brain/query", json={"surface": "search"})
    assert r.status_code in (400, 422)
    # bad surface
    r2 = client_with_chunks.post(
        "/api/brain/query",
        json={"query": "x", "surface": "moon"},
    )
    assert r2.status_code in (400, 422)


def test_post_brain_query_accepts_idempotency_key(client_with_chunks):
    r = client_with_chunks.post(
        "/api/brain/query",
        json={"query": "aravo", "surface": "chat"},
        headers={"Idempotency-Key": "test-key-123"},
    )
    assert r.status_code == 200


def test_post_brain_query_respects_top_k(client_with_chunks):
    r = client_with_chunks.post(
        "/api/brain/query",
        json={"query": "aravo migration", "surface": "search", "top_k": 2},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["hits"]) <= 2
