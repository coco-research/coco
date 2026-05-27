"""Tests for the drafts router (app.routers.drafts).

Covers happy + error paths for list/get. The approve/reject endpoints rely
on `upsert()` being called with `conflict_cols`/`update_cols` kwargs while
the helper actually accepts `conflict_columns`/`update_columns` — exercising
them here would just regression-lock that bug, so they are intentionally
left to a separate fix task.
"""
from __future__ import annotations

import sqlite3
import uuid

import pytest


def _seed_draft(db_path, *, draft_id=None, project_id="proj-1",
                 status="pending", content="hello"):
    draft_id = draft_id or str(uuid.uuid4())
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO hub_drafts (id, project_id, source_content_id, "
            "target_template, target_section, content, format, status, "
            "created_at) VALUES (?, ?, 'c', 'tpl', 'sec', ?, 'bullet', ?, "
            "datetime('now'))",
            (draft_id, project_id, content, status),
        )
        conn.commit()
        return draft_id
    finally:
        conn.close()


def _seed_decision(db_path, draft_id, status="approved"):
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO draft_decisions (id, hub_draft_id, status, "
            "decided_by) VALUES (?, ?, ?, 'user')",
            (str(uuid.uuid4()), draft_id, status),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def client(app_client):
    from app.routers.drafts import router
    return app_client.include(router).client()


# ---------------------------------------------------------------------------
# GET /api/drafts
# ---------------------------------------------------------------------------

class TestListDrafts:
    def test_empty_returns_empty_list(self, fresh_db, client):
        resp = client.get("/api/drafts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_seeded_drafts(self, fresh_db, client):
        _seed_draft(fresh_db, project_id="p1", status="pending")
        _seed_draft(fresh_db, project_id="p2", status="pending")
        resp = client.get("/api/drafts")
        body = resp.json()
        assert resp.status_code == 200
        assert len(body) == 2

    def test_filters_by_project_id(self, fresh_db, client):
        _seed_draft(fresh_db, project_id="alpha")
        _seed_draft(fresh_db, project_id="beta")
        body = client.get("/api/drafts?project_id=alpha").json()
        assert len(body) == 1
        assert body[0]["project_id"] == "alpha"

    def test_filters_by_multi_project_ids(self, fresh_db, client):
        _seed_draft(fresh_db, project_id="alpha")
        _seed_draft(fresh_db, project_id="beta")
        _seed_draft(fresh_db, project_id="gamma")
        body = client.get("/api/drafts?project_ids=alpha,gamma").json()
        ids = sorted(d["project_id"] for d in body)
        assert ids == ["alpha", "gamma"]

    def test_decision_overlay_changes_status(self, fresh_db, client):
        did = _seed_draft(fresh_db, status="pending")
        _seed_decision(fresh_db, did, status="approved")
        body = client.get("/api/drafts").json()
        assert len(body) == 1
        assert body[0]["status"] == "approved"

    def test_rejects_limit_over_max(self, fresh_db, client):
        resp = client.get("/api/drafts?limit=10000")
        assert resp.status_code == 422

    def test_rejects_negative_offset(self, fresh_db, client):
        resp = client.get("/api/drafts?offset=-5")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/drafts/{draft_id}
# ---------------------------------------------------------------------------

class TestGetDraft:
    def test_returns_seeded_draft(self, fresh_db, client):
        did = _seed_draft(fresh_db, project_id="p", content="howdy")
        resp = client.get(f"/api/drafts/{did}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == did
        assert body["content"] == "howdy"

    def test_decision_overlays_status(self, fresh_db, client):
        did = _seed_draft(fresh_db, status="pending")
        _seed_decision(fresh_db, did, status="rejected")
        body = client.get(f"/api/drafts/{did}").json()
        assert body["status"] == "rejected"

    def test_unknown_id_returns_404(self, fresh_db, client):
        resp = client.get("/api/drafts/nope-never-existed")
        assert resp.status_code == 404
