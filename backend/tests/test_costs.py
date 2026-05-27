"""Tests for the costs router (app.routers.costs)."""
from __future__ import annotations

import sqlite3
import uuid

import pytest


# ---------------------------------------------------------------------------
# Helpers — insert raw cost ledger / budget rows into the fresh DB
# ---------------------------------------------------------------------------

def _insert_cost(db_path, *, model="claude-sonnet-4-5", project_id=None,
                 node_id=None, cost_usd=0.10, source="agent",
                 created_at_offset_days=0):
    """Insert one cost_ledger row dated `created_at_offset_days` ago."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO cost_ledger (id, model, project_id, node_id, "
            "cost_usd, source, created_at) VALUES (?, ?, ?, ?, ?, ?, "
            f"datetime('now', '-{created_at_offset_days} days'))",
            (str(uuid.uuid4()), model, project_id, node_id, cost_usd, source),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_hub_api_cost(db_path, *, model="gpt-5-nano", cost_usd=0.05,
                          created_at_offset_days=0):
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO hub_api_costs (id, timestamp, model, feature, "
            "input_tokens, output_tokens, cost_usd) "
            f"VALUES (?, datetime('now', '-{created_at_offset_days} days'), ?, 'test', 100, 50, ?)",
            (str(uuid.uuid4()), model, cost_usd),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture()
def client(app_client):
    from app.routers.costs import router
    return app_client.include(router).client()


# ---------------------------------------------------------------------------
# GET /api/costs/summary
# ---------------------------------------------------------------------------

class TestCostSummary:
    def test_empty_db_returns_zero_totals(self, fresh_db, client):
        resp = client.get("/api/costs/summary?days=30")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_usd"] == 0.0
        assert body["daily_avg"] == 0.0
        assert body["by_model"] == {}
        assert body["by_project"] == {}
        assert body["daily"] == []

    def test_sums_costs_within_window(self, fresh_db, client):
        _insert_cost(fresh_db, cost_usd=1.50, project_id="proj-a", model="m1")
        _insert_cost(fresh_db, cost_usd=2.50, project_id="proj-b", model="m1")
        _insert_cost(fresh_db, cost_usd=0.25, project_id="proj-a", model="m2")

        resp = client.get("/api/costs/summary?days=30")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_usd"] == pytest.approx(4.25)
        assert body["by_model"]["m1"] == pytest.approx(4.00)
        assert body["by_model"]["m2"] == pytest.approx(0.25)
        assert body["by_project"]["proj-a"] == pytest.approx(1.75)
        assert body["by_project"]["proj-b"] == pytest.approx(2.50)

    def test_excludes_costs_outside_window(self, fresh_db, client):
        _insert_cost(fresh_db, cost_usd=1.00, created_at_offset_days=0)
        _insert_cost(fresh_db, cost_usd=9.99, created_at_offset_days=60)

        resp = client.get("/api/costs/summary?days=7")
        assert resp.status_code == 200
        assert resp.json()["total_usd"] == pytest.approx(1.00)

    def test_includes_hub_api_costs(self, fresh_db, client):
        _insert_cost(fresh_db, cost_usd=1.00, model="claude")
        _insert_hub_api_cost(fresh_db, cost_usd=0.50, model="gpt-5-nano")

        resp = client.get("/api/costs/summary?days=30")
        body = resp.json()
        assert body["total_usd"] == pytest.approx(1.50)
        assert body["by_model"]["gpt-5-nano"] == pytest.approx(0.50)

    def test_rejects_invalid_days(self, fresh_db, client):
        resp = client.get("/api/costs/summary?days=0")
        assert resp.status_code == 422

    def test_rejects_days_above_limit(self, fresh_db, client):
        resp = client.get("/api/costs/summary?days=10000")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/costs/events
# ---------------------------------------------------------------------------

class TestCostEvents:
    def test_returns_recent_events(self, fresh_db, client):
        _insert_cost(fresh_db, cost_usd=1.00, project_id="p1")
        _insert_cost(fresh_db, cost_usd=2.00, project_id="p1")

        resp = client.get("/api/costs/events?limit=10")
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) == 2

    def test_filters_by_project_id(self, fresh_db, client):
        _insert_cost(fresh_db, cost_usd=1.00, project_id="p1")
        _insert_cost(fresh_db, cost_usd=2.00, project_id="p2")

        resp = client.get("/api/costs/events?project_id=p1")
        events = resp.json()
        assert len(events) == 1
        assert events[0]["project_id"] == "p1"

    def test_rejects_negative_offset(self, fresh_db, client):
        resp = client.get("/api/costs/events?offset=-1")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET / POST /api/budgets
# ---------------------------------------------------------------------------

class TestBudgets:
    def test_list_returns_empty_on_fresh_db(self, fresh_db, client):
        resp = client.get("/api/budgets")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_then_list_roundtrip(self, fresh_db, client):
        resp = client.post(
            "/api/budgets",
            json={
                "project_id": "proj-x",
                "monthly_cap_usd": 100.0,
                "alert_threshold_pct": 0.75,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["project_id"] == "proj-x"
        assert body["monthly_cap_usd"] == 100.0
        assert body["alert_threshold_pct"] == 0.75

        listed = client.get("/api/budgets").json()
        assert len(listed) == 1
        assert listed[0]["project_id"] == "proj-x"

    def test_create_is_idempotent_upsert(self, fresh_db, client):
        client.post("/api/budgets", json={
            "project_id": "proj-x", "monthly_cap_usd": 50.0,
            "alert_threshold_pct": 0.5,
        })
        client.post("/api/budgets", json={
            "project_id": "proj-x", "monthly_cap_usd": 200.0,
            "alert_threshold_pct": 0.9,
        })
        listed = client.get("/api/budgets").json()
        assert len(listed) == 1
        assert listed[0]["monthly_cap_usd"] == 200.0

    def test_rejects_missing_project_id(self, fresh_db, client):
        resp = client.post(
            "/api/budgets",
            json={"monthly_cap_usd": 100.0, "alert_threshold_pct": 0.8},
        )
        assert resp.status_code == 422
