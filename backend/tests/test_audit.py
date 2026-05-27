"""Tests for audit log + telemetry services (Phase 11)."""
from __future__ import annotations

import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

class TestAuditRecord:
    def test_record_returns_id(self, isolated_db):
        from app.services import audit as a
        rid = a.record(a.ACTION_STATION_KILL, payload={"agent_id": "abc"})
        assert isinstance(rid, int)
        assert rid >= 1

    def test_payload_hashed_not_raw(self, isolated_db):
        from app.services import audit as a
        rid = a.record("test.action", payload={"secret": "sk-ant-XXXX"})
        rows = a.list_recent(limit=10)
        assert rows[0]["id"] == rid
        # Hash must NOT equal the secret string
        ph = rows[0]["payload_hash"]
        assert ph and len(ph) == 64
        assert "sk-ant-" not in ph
        # And it must be reproducible for the same payload
        import hashlib
        expected = hashlib.sha256(
            json.dumps({"secret": "sk-ant-XXXX"}, sort_keys=True).encode("utf-8")
        ).hexdigest()
        assert ph == expected

    def test_list_recent_orders_newest_first(self, isolated_db):
        from app.services import audit as a
        a.record("action.one", payload={"n": 1})
        a.record("action.two", payload={"n": 2})
        a.record("action.three", payload={"n": 3})
        rows = a.list_recent(limit=10)
        assert [r["action"] for r in rows[:3]] == ["action.three", "action.two", "action.one"]

    def test_count_filter(self, isolated_db):
        from app.services import audit as a
        a.record("kill", payload={"x": 1})
        a.record("kill", payload={"x": 2})
        a.record("dismiss", payload={"y": 1})
        assert a.count() == 3
        assert a.count(action="kill") == 2
        assert a.count(action="dismiss") == 1

    def test_record_requires_action(self, isolated_db):
        from app.services import audit as a
        import pytest
        with pytest.raises(ValueError):
            a.record("", payload={"x": 1})

    def test_none_payload_yields_null_hash(self, isolated_db):
        from app.services import audit as a
        rid = a.record("no.payload", payload=None)
        row = a.list_recent(limit=1)[0]
        assert row["id"] == rid
        assert row["payload_hash"] is None


# ---------------------------------------------------------------------------
# Telemetry (opt-in, default off)
# ---------------------------------------------------------------------------

class TestTelemetry:
    def test_default_off(self, isolated_db, monkeypatch):
        monkeypatch.delenv("COCO_TELEMETRY", raising=False)
        from app.services import telemetry as t
        t.clear_cache()
        assert t.is_enabled() is False
        # record() should be a no-op
        assert t.record("ignored.event", {"k": 1}) is False

    def test_opt_in_persists(self, isolated_db, monkeypatch):
        monkeypatch.delenv("COCO_TELEMETRY", raising=False)
        from app.services import telemetry as t
        t.clear_cache()
        t.set_enabled(True)
        assert t.is_enabled() is True
        # Roundtrip via fresh read
        t.clear_cache()
        assert t.is_enabled() is True

    def test_record_writes_jsonl(self, isolated_db, monkeypatch):
        monkeypatch.delenv("COCO_TELEMETRY", raising=False)
        from app.services import telemetry as t
        t.clear_cache()
        t.set_enabled(True)
        ok = t.record("ui.opened", {"page": "home"})
        assert ok is True
        path = t.today_path()
        assert Path(path).exists()
        events = t.list_recent_events(limit=10)
        assert len(events) >= 1
        assert events[-1]["event"] == "ui.opened"
        assert events[-1]["props"]["page"] == "home"

    def test_env_override_forces_off(self, isolated_db, monkeypatch):
        from app.services import telemetry as t
        t.clear_cache()
        t.set_enabled(True)  # pref says yes
        monkeypatch.setenv("COCO_TELEMETRY", "false")
        assert t.is_enabled() is False
