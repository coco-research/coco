"""Tests for the dashboard router (app.routers.dashboard)."""
from __future__ import annotations

import sqlite3
import uuid

import pytest


def _exec(db_path, sql, params=()):
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def _seed_hub_project(db_path, *, project_id="proj-1", name="Demo",
                       jira_key=None, active=1):
    _exec(db_path,
          "INSERT INTO hub_projects (id, name, jira_key, active, "
          "created_at, updated_at) VALUES (?, ?, ?, ?, "
          "datetime('now'), datetime('now'))",
          (project_id, name, jira_key, active))
    return project_id


def _seed_agent(db_path, *, status="idle", node_id=None):
    _exec(db_path,
          "INSERT INTO agents (id, name, model, status, node_id, "
          "created_at, updated_at) VALUES (?, ?, 'sonnet', ?, ?, "
          "datetime('now'), datetime('now'))",
          (str(uuid.uuid4()), f"agent-{status}", status, node_id))


def _seed_task(db_path, *, status="open", priority="medium", project_id=None):
    _exec(db_path,
          "INSERT INTO tasks (id, title, status, priority, project_id, "
          "created_at, updated_at) VALUES (?, ?, ?, ?, ?, "
          "datetime('now'), datetime('now'))",
          (str(uuid.uuid4()), "T", status, priority, project_id))


def _seed_cost(db_path, *, cost_usd=1.0, days_ago=0):
    _exec(db_path,
          "INSERT INTO cost_ledger (id, model, cost_usd, source, created_at) "
          f"VALUES (?, 'm', ?, 'agent', datetime('now', '-{days_ago} days'))",
          (str(uuid.uuid4()), cost_usd))


def _seed_draft(db_path, *, status="pending"):
    _exec(db_path,
          "INSERT INTO hub_drafts (id, project_id, source_content_id, "
          "target_template, target_section, content, format, status, "
          "created_at) VALUES (?, 'p', 'c', 't', 's', 'body', 'bullet', ?, "
          "datetime('now'))",
          (str(uuid.uuid4()), status))


@pytest.fixture()
def client(app_client):
    from app.routers.dashboard import router
    return app_client.include(router).client()


# ---------------------------------------------------------------------------
# GET /api/dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_returns_full_shape_on_empty_db(self, fresh_db, client):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        body = resp.json()

        # Top-level keys all present
        for k in ("projects", "agents", "queue", "costs", "health",
                  "unsorted_count"):
            assert k in body

        assert body["projects"] == []
        assert body["agents"] == {"running": 0, "paused": 0, "idle": 0,
                                  "total": 0}
        assert body["queue"]["total"] == 0
        assert body["queue"]["drafts"] == 0
        assert body["costs"]["today_usd"] == 0.0
        assert body["costs"]["month_usd"] == 0.0
        # 7-day daily array always returned
        assert isinstance(body["costs"]["daily"], list)
        assert len(body["costs"]["daily"]) == 7

    def test_aggregates_agents_by_status(self, fresh_db, client):
        _seed_agent(fresh_db, status="running")
        _seed_agent(fresh_db, status="running")
        _seed_agent(fresh_db, status="paused")
        _seed_agent(fresh_db, status="idle")

        body = client.get("/api/dashboard").json()
        assert body["agents"]["running"] == 2
        assert body["agents"]["paused"] == 1
        assert body["agents"]["idle"] == 1
        assert body["agents"]["total"] == 4

    def test_aggregates_tasks_and_drafts(self, fresh_db, client):
        _seed_task(fresh_db, status="open", priority="high")
        _seed_task(fresh_db, status="open", priority="medium")
        _seed_task(fresh_db, status="done", priority="high")
        _seed_draft(fresh_db, status="pending")
        _seed_draft(fresh_db, status="pending")
        _seed_draft(fresh_db, status="approved")

        body = client.get("/api/dashboard").json()
        assert body["queue"]["total"] == 2
        assert body["queue"]["urgent"] == 1
        assert body["queue"]["drafts"] == 2

    def test_sums_costs_for_today_and_month(self, fresh_db, client):
        _seed_cost(fresh_db, cost_usd=1.50, days_ago=0)
        _seed_cost(fresh_db, cost_usd=2.25, days_ago=0)
        _seed_cost(fresh_db, cost_usd=10.00, days_ago=400)  # outside month

        body = client.get("/api/dashboard").json()
        assert body["costs"]["today_usd"] == pytest.approx(3.75)
        # both of today's costs land in current month, the 400-days-ago does not
        assert body["costs"]["month_usd"] == pytest.approx(3.75)

    def test_returns_projects_with_source_breakdown(self, fresh_db, client):
        _seed_hub_project(fresh_db, project_id="p1", name="Project One")
        body = client.get("/api/dashboard").json()
        assert len(body["projects"]) == 1
        p = body["projects"][0]
        assert p["id"] == "p1"
        assert p["name"] == "Project One"
        # sources dict is always populated with the four canonical keys
        assert set(p["sources"].keys()) == {"email", "voice", "jira",
                                            "confluence"}

    def test_accepts_node_filter_params(self, fresh_db, client):
        # node_id pointing at nothing should still return a valid response
        resp = client.get("/api/dashboard?node_id=nope&subtree=true")
        assert resp.status_code == 200
        body = resp.json()
        # No agents under unknown node -> all zeros
        assert body["agents"]["total"] == 0

    def test_handles_invalid_subtree_param(self, fresh_db, client):
        resp = client.get("/api/dashboard?subtree=not-a-bool")
        assert resp.status_code == 422
