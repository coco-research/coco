"""Tests for the Brain ingestion v3 pipeline.

Covers:
    - source_hash canonicalization (whitespace + case stable)
    - exact dedup (and force=True bypass)
    - near-dup MinHash-lite Jaccard (writes edge, doesn't drop write)
    - 3-tier classifier dispatch (rules, embedding, LLM stub)
    - source-specific handler pre-processing (email From: extraction)
    - HTTP endpoint: missing Idempotency-Key → 400
    - HTTP endpoint: idempotency cache returns same result for replay
    - HTTP endpoint: idempotency key reuse with different body → 409
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import ingest as ingest_router
from app.services.ingest import (
    IngestRequest,
    dispatch,
    register_handler,
)
from app.services.ingest.classifier import (
    JiraPrefixRule,
    SenderRule,
    classify,
    classify_by_embedding,
    classify_by_rules,
)
from app.services.ingest.dedup import (
    canonicalize,
    find_near_duplicate,
    jaccard,
    source_hash,
)
from app.services.ingest.router import IngestDeps


# ---------------------------------------------------------------------------
# dedup.py
# ---------------------------------------------------------------------------


class TestSourceHash:
    def test_canonicalize_collapses_whitespace_and_lowercases(self):
        assert canonicalize(" Hello\n  World ") == "hello world"

    def test_source_hash_is_64_hex_chars(self):
        h = source_hash("hello world")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_source_hash_stable_across_whitespace_and_case(self):
        h1 = source_hash("Hello World")
        h2 = source_hash("  hello   WORLD\n")
        assert h1 == h2

    def test_source_hash_differs_for_different_text(self):
        assert source_hash("alpha") != source_hash("beta")


class TestNearDup:
    def test_jaccard_identical_returns_1(self):
        text = "the quick brown fox jumps over the lazy dog today"
        assert jaccard(text, text) == 1.0

    def test_jaccard_disjoint_returns_0(self):
        assert jaccard("alpha beta gamma delta epsilon", "xx yy zz qq pp") == 0.0

    def test_find_near_duplicate_above_threshold(self):
        incoming = "Project Aravo Q1 review meeting scheduled next Tuesday morning"
        candidates = [
            ("doc-1", "Completely unrelated text about cats and dogs jumping fences"),
            (
                "doc-2",
                "Project Aravo Q1 review meeting scheduled next Tuesday morning at 9am",
            ),
        ]
        result = find_near_duplicate(incoming, candidates, threshold=0.5)
        assert result is not None
        doc_id, score = result
        assert doc_id == "doc-2"
        assert score >= 0.5

    def test_find_near_duplicate_returns_none_below_threshold(self):
        incoming = "totally unique content nobody has ever written before"
        candidates = [("doc-1", "completely different words about cats")]
        assert find_near_duplicate(incoming, candidates, threshold=0.9) is None


# ---------------------------------------------------------------------------
# classifier.py
# ---------------------------------------------------------------------------


class TestClassifierRules:
    def test_sender_rule_fires_case_insensitive(self):
        rules = [SenderRule(sender="aude@example.com", project_id="proj-tax")]
        c = classify_by_rules("body text", "AUDE@example.com", rules, ())
        assert c is not None
        assert c.method == "rules"
        assert c.project_id == "proj-tax"
        assert c.confidence == 0.95

    def test_jira_prefix_rule_fires_on_body(self):
        rules = [JiraPrefixRule(prefix="CXR", project_id="proj-cross-risk")]
        c = classify_by_rules("Ticket CXR-47 escalated today", None, (), rules)
        assert c is not None
        assert c.method == "rules"
        assert c.project_id == "proj-cross-risk"

    def test_sender_rule_takes_precedence_over_jira(self):
        sender_rules = [SenderRule(sender="x@y.com", project_id="from-sender")]
        jira_rules = [JiraPrefixRule(prefix="CXR", project_id="from-jira")]
        c = classify_by_rules("CXR-99 update", "x@y.com", sender_rules, jira_rules)
        assert c is not None
        assert c.project_id == "from-sender"

    def test_no_rule_match_returns_none(self):
        c = classify_by_rules("body", "unknown@x.com", (), ())
        assert c is None


class TestClassifierEmbedding:
    def test_top_centroid_above_threshold_wins(self):
        def fake_embedder(_text: str):
            return [1.0, 0.0, 0.0]

        centroids = {
            "proj-a": [0.99, 0.1, 0.0],  # cosine ~0.99
            "proj-b": [0.0, 1.0, 0.0],
        }
        c = classify_by_embedding("anything", fake_embedder, centroids)
        assert c is not None
        assert c.method == "embedding"
        assert c.project_id == "proj-a"
        assert c.confidence > 0.7

    def test_below_threshold_returns_none(self):
        def fake_embedder(_text: str):
            return [1.0, 0.0, 0.0]

        centroids = {"proj-a": [0.0, 0.0, 1.0]}  # orthogonal
        assert classify_by_embedding("x", fake_embedder, centroids) is None

    def test_no_embedder_returns_none(self):
        assert classify_by_embedding("x", None, {"p": [1.0]}) is None


class TestClassifierThreeTier:
    def test_dispatches_to_rules_first(self):
        sender_rules = [SenderRule(sender="a@b.com", project_id="from-rules")]

        def fake_embedder(_t: str):
            return [1.0, 0.0]

        c = classify(
            text="ignore",
            sender="a@b.com",
            sender_rules=sender_rules,
            embedder=fake_embedder,
            project_centroids={"from-embedding": [1.0, 0.0]},
        )
        assert c.method == "rules"
        assert c.project_id == "from-rules"

    def test_falls_back_to_embedding_when_no_rules_fire(self):
        def fake_embedder(_t: str):
            return [1.0, 0.0]

        c = classify(
            text="x",
            sender="nobody@x.com",
            embedder=fake_embedder,
            project_centroids={"from-embedding": [1.0, 0.0]},
        )
        assert c.method == "embedding"
        assert c.project_id == "from-embedding"

    def test_falls_through_to_llm_stub_with_needs_review(self):
        c = classify(text="orphan content", sender=None)
        assert c.method == "unknown"
        assert c.needs_review is True
        assert c.project_id is None


# ---------------------------------------------------------------------------
# router.py / dispatch
# ---------------------------------------------------------------------------


def _make_request(
    *,
    raw_text: str = "Hello body of an email",
    source: str = "outlook",
    source_id: str = "msg-1",
    project_id: str | None = None,
    force: bool = False,
    metadata: dict | None = None,
) -> IngestRequest:
    return IngestRequest(
        source=source,
        source_id=source_id,
        content_type="email",
        raw_text=raw_text,
        metadata=metadata or {},
        project_id=project_id,
        force=force,
    )


class TestDispatchDedup:
    def test_exact_dedup_returns_deduped_no_write(self):
        seen = {source_hash("Same body twice")}
        persisted_calls: list[str] = []

        def persist(**kw):
            persisted_calls.append(kw["document_id"])
            return True

        deps = IngestDeps(
            seen_hashes=lambda sha: sha in seen,
            persist=persist,
        )
        req = _make_request(raw_text="Same body twice")
        result = dispatch(req, deps=deps)
        assert result.deduped is True
        assert result.persisted is False
        assert result.document_id is None
        assert persisted_calls == []
        assert "exact_dedup_hit" in result.notes

    def test_force_bypasses_exact_dedup(self):
        seen = {source_hash("Same body twice")}
        persisted_calls: list[str] = []

        def persist(**kw):
            persisted_calls.append(kw["document_id"])
            return True

        deps = IngestDeps(
            seen_hashes=lambda sha: sha in seen,
            persist=persist,
        )
        req = _make_request(raw_text="Same body twice", force=True)
        result = dispatch(req, deps=deps)
        assert result.deduped is False
        assert result.persisted is True
        assert "exact_dedup_bypassed_by_force" in result.notes
        assert len(persisted_calls) == 1

    def test_near_dup_writes_with_edge_doesnt_skip(self):
        # Long, near-identical bodies that exceed the production
        # NEAR_DUP_THRESHOLD (0.90).
        text_new = (
            "The quick brown fox jumps over the lazy dog every single morning at "
            "sunrise without fail today exactly here in this very room of the "
            "building today"
        )
        text_old = (
            "The quick brown fox jumps over the lazy dog every single morning at "
            "sunrise without fail today exactly here in this very room of the "
            "building tomorrow"
        )

        persisted_args: list[dict] = []

        def persist(**kw):
            persisted_args.append(kw)
            return True

        deps = IngestDeps(
            seen_hashes=lambda sha: False,
            near_dup_candidates=lambda req: [("doc-old", text_old)],
            persist=persist,
        )
        req = _make_request(raw_text=text_new)
        result = dispatch(req, deps=deps)
        assert result.deduped is False
        assert result.persisted is True
        assert result.near_duplicate_of == "doc-old"
        assert any(n.startswith("near_dup_jaccard:") for n in result.notes)
        assert persisted_args[0]["near_duplicate_of"] == "doc-old"


class TestDispatchClassification:
    def test_classification_attached_to_result(self):
        sender_rules = (SenderRule(sender="a@b.com", project_id="proj-x"),)
        emitted: list[tuple[str, dict]] = []

        deps = IngestDeps(
            sender_rules=sender_rules,
            persist=lambda **kw: True,
            emit=lambda et, d: emitted.append((et, d)),
        )
        req = _make_request(metadata={"sender_email": "a@b.com"})
        result = dispatch(req, deps=deps)
        assert result.classification is not None
        assert result.classification.method == "rules"
        assert result.classification.project_id == "proj-x"
        assert result.persisted is True
        # SSE event emitted
        assert any(et == "brain.ingested" for et, _ in emitted)
        topic, data = emitted[0]
        assert data["project_id"] == "proj-x"
        assert data["classification"] == "rules"

    def test_llm_stub_marks_needs_review(self):
        deps = IngestDeps(persist=lambda **kw: True)
        req = _make_request(metadata={})
        result = dispatch(req, deps=deps)
        assert result.classification is not None
        assert result.classification.method == "unknown"
        assert result.classification_needs_review is True


class TestSourceHandlers:
    def test_email_handler_extracts_from_header(self):
        raw = "From: Aude <aude@example.com>\n\nBody here"
        sender_rules = (SenderRule(sender="aude@example.com", project_id="proj-tax"),)
        deps = IngestDeps(
            sender_rules=sender_rules,
            persist=lambda **kw: True,
        )
        req = _make_request(raw_text=raw, metadata={})
        result = dispatch(req, deps=deps)
        # The email handler should have surfaced sender_email and the
        # rules tier should have fired off it.
        assert result.classification is not None
        assert result.classification.method == "rules"
        assert result.classification.project_id == "proj-tax"

    def test_custom_handler_registration(self):
        calls: list[str] = []

        def my_handler(req):
            calls.append(req.source_id)
            return req

        register_handler("manual", my_handler)
        try:
            deps = IngestDeps(persist=lambda **kw: True)
            req = _make_request(source="manual", source_id="custom-1")
            dispatch(req, deps=deps)
            assert calls == ["custom-1"]
        finally:
            # Restore default no-op handler
            from app.services.ingest.router import _doc_handler

            register_handler("manual", _doc_handler)


# ---------------------------------------------------------------------------
# HTTP endpoint
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    """Lightweight FastAPI app with just the ingest router mounted."""
    ingest_router._reset_idempotency_cache_for_tests()
    # Use a noop persist so the result reports persisted=True without DB.
    ingest_router.set_default_deps(
        IngestDeps(persist=lambda **kw: True, emit=lambda et, d: None)
    )
    app = FastAPI()
    app.include_router(ingest_router.router)
    return TestClient(app)


class TestHTTPEndpoint:
    def test_missing_idempotency_key_returns_400(self, client):
        resp = client.post(
            "/api/brain/ingest",
            json={
                "source": "manual",
                "source_id": "x",
                "content_type": "doc",
                "raw_text": "hi",
            },
        )
        assert resp.status_code == 400
        assert "Idempotency-Key" in resp.json()["detail"]

    def test_replay_returns_cached_result(self, client):
        body = {
            "source": "manual",
            "source_id": "x",
            "content_type": "doc",
            "raw_text": "Stable body",
        }
        headers = {"Idempotency-Key": "key-replay-1"}
        r1 = client.post("/api/brain/ingest", json=body, headers=headers)
        r2 = client.post("/api/brain/ingest", json=body, headers=headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Same document_id returned both times (cached).
        assert r1.json()["document_id"] == r2.json()["document_id"]

    def test_idempotency_key_reuse_with_different_body_returns_409(self, client):
        headers = {"Idempotency-Key": "key-conflict-1"}
        client.post(
            "/api/brain/ingest",
            json={
                "source": "manual",
                "source_id": "a",
                "content_type": "doc",
                "raw_text": "body one",
            },
            headers=headers,
        )
        r2 = client.post(
            "/api/brain/ingest",
            json={
                "source": "manual",
                "source_id": "b",
                "content_type": "doc",
                "raw_text": "body two — different",
            },
            headers=headers,
        )
        assert r2.status_code == 409

    def test_endpoint_returns_classification_shape(self, client):
        resp = client.post(
            "/api/brain/ingest",
            json={
                "source": "manual",
                "source_id": "shape-1",
                "content_type": "doc",
                "raw_text": "Some unclassified content",
            },
            headers={"Idempotency-Key": "shape-1-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "source_hash" in data
        assert "classification" in data
        assert data["classification"]["method"] in {
            "rules",
            "embedding",
            "unknown",
        }
        assert "persisted" in data
