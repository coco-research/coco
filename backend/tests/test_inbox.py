"""Tests for the inbox router (app.routers.inbox)."""
from __future__ import annotations

import json
import sqlite3
import uuid

import pytest


def _insert_notification(db_path, *, item_type="self_improve_summary",
                         item_key=None, title="x", body="b",
                         metadata=None):
    """Insert one inbox_notifications row."""
    item_key = item_key or f"key-{uuid.uuid4().hex[:8]}"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO inbox_notifications "
            "(id, item_type, item_key, title, body, metadata_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), item_type, item_key, title, body,
             json.dumps(metadata or {})),
        )
        conn.commit()
        return item_key
    finally:
        conn.close()


@pytest.fixture()
def client(app_client):
    from app.routers.inbox import router
    return app_client.include(router).client()


# ---------------------------------------------------------------------------
# GET /api/inbox/read-states
# ---------------------------------------------------------------------------

class TestGetReadStates:
    def test_empty_returns_empty_dict(self, fresh_db, client):
        resp = client.get("/api/inbox/read-states")
        assert resp.status_code == 200
        assert resp.json() == {}

    def test_returns_dict_of_states_after_writes(self, fresh_db, client):
        client.patch("/api/inbox/read-state",
                     json={"item_key": "a", "read_state": "seen"})
        client.patch("/api/inbox/read-state",
                     json={"item_key": "b", "read_state": "dismissed"})

        body = client.get("/api/inbox/read-states").json()
        assert body == {"a": "seen", "b": "dismissed"}


# ---------------------------------------------------------------------------
# PATCH /api/inbox/read-state
# ---------------------------------------------------------------------------

class TestPatchReadState:
    def test_sets_state_and_echoes_back(self, fresh_db, client):
        resp = client.patch(
            "/api/inbox/read-state",
            json={"item_key": "abc", "read_state": "seen"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"item_key": "abc", "read_state": "seen"}

    def test_upserts_on_repeat_call(self, fresh_db, client):
        client.patch("/api/inbox/read-state",
                     json={"item_key": "k", "read_state": "seen"})
        client.patch("/api/inbox/read-state",
                     json={"item_key": "k", "read_state": "dismissed"})
        states = client.get("/api/inbox/read-states").json()
        assert states == {"k": "dismissed"}

    def test_rejects_unknown_read_state(self, fresh_db, client):
        resp = client.patch(
            "/api/inbox/read-state",
            json={"item_key": "x", "read_state": "deleted"},
        )
        assert resp.status_code == 400

    def test_rejects_missing_item_key(self, fresh_db, client):
        resp = client.patch(
            "/api/inbox/read-state",
            json={"read_state": "seen"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/inbox/read-states/batch
# ---------------------------------------------------------------------------

class TestBatchPatch:
    def test_updates_multiple_keys(self, fresh_db, client):
        resp = client.patch(
            "/api/inbox/read-states/batch",
            json={"item_keys": ["a", "b", "c"], "read_state": "seen"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"updated": 3, "read_state": "seen"}

        states = client.get("/api/inbox/read-states").json()
        assert states == {"a": "seen", "b": "seen", "c": "seen"}

    def test_rejects_invalid_state(self, fresh_db, client):
        resp = client.patch(
            "/api/inbox/read-states/batch",
            json={"item_keys": ["a"], "read_state": "garbage"},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/inbox/mark-all-seen
# ---------------------------------------------------------------------------

class TestMarkAllSeen:
    def test_flips_unread_to_seen(self, fresh_db, client):
        # seed an unread row
        client.patch("/api/inbox/read-state",
                     json={"item_key": "u1", "read_state": "unread"})
        client.patch("/api/inbox/read-state",
                     json={"item_key": "u2", "read_state": "unread"})
        # plus one already-seen
        client.patch("/api/inbox/read-state",
                     json={"item_key": "s1", "read_state": "seen"})

        resp = client.post("/api/inbox/mark-all-seen")
        assert resp.status_code == 200
        assert resp.json()["updated"] == 2

        states = client.get("/api/inbox/read-states").json()
        assert states["u1"] == "seen"
        assert states["u2"] == "seen"
        assert states["s1"] == "seen"

    def test_idempotent_on_empty_db(self, fresh_db, client):
        resp = client.post("/api/inbox/mark-all-seen")
        assert resp.status_code == 200
        assert resp.json()["updated"] == 0


# ---------------------------------------------------------------------------
# GET /api/inbox/notifications
# ---------------------------------------------------------------------------

class TestGetNotifications:
    def test_returns_persisted_items(self, fresh_db, client):
        _insert_notification(fresh_db, item_type="self_improve_summary",
                             title="t1", body="b1",
                             metadata={"cycle_id": "c-1"})
        _insert_notification(fresh_db, item_type="other",
                             title="t2", body="b2")

        items = client.get("/api/inbox/notifications").json()
        assert len(items) == 2
        # default read_state is 'unread'
        assert all(it["read_state"] == "unread" for it in items)
        # metadata_json parsed into metadata dict
        for it in items:
            assert isinstance(it["metadata"], dict)

    def test_filters_by_item_type(self, fresh_db, client):
        _insert_notification(fresh_db, item_type="self_improve_summary",
                             title="t1")
        _insert_notification(fresh_db, item_type="other_type", title="t2")

        items = client.get(
            "/api/inbox/notifications?item_type=self_improve_summary"
        ).json()
        assert len(items) == 1
        assert items[0]["item_type"] == "self_improve_summary"

    def test_rejects_limit_out_of_range(self, fresh_db, client):
        resp = client.get("/api/inbox/notifications?limit=500")
        assert resp.status_code == 422
