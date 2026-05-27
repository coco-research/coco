"""Tests for PIN auth service + middleware + router (Phase 11)."""
from __future__ import annotations

import importlib
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app_with_auth_router():
    """Build a FastAPI app with the AuthMiddleware + /api/auth router only.

    We add a stub /api/protected route to exercise the PIN-gate path.
    """
    from app.middleware.auth import AuthMiddleware
    from app.routers import auth as auth_router_mod
    importlib.reload(auth_router_mod)
    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.include_router(auth_router_mod.router)

    @app.post("/api/protected")
    def protected():
        return {"ok": True}

    @app.get("/api/protected/read")
    def protected_read():
        return {"ok": True}

    return app


def _fresh_client(isolated_db):
    return TestClient(_make_app_with_auth_router())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPinService:
    def test_default_is_open_mode(self, isolated_db):
        from app.services import auth as a
        assert a.is_pin_set() is False

    def test_set_and_verify_pin(self, isolated_db):
        from app.services import auth as a
        a.set_pin("123456")
        assert a.is_pin_set() is True
        tok = a.verify_pin("123456")
        assert tok and isinstance(tok, str)
        assert a.validate_session(tok) is True

    def test_wrong_pin_returns_none(self, isolated_db):
        from app.services import auth as a
        a.set_pin("123456")
        assert a.verify_pin("000000") is None

    def test_clear_pin_invalidates_sessions(self, isolated_db):
        from app.services import auth as a
        a.set_pin("123456")
        tok = a.verify_pin("123456")
        assert a.validate_session(tok) is True
        a.clear_pin()
        assert a.is_pin_set() is False
        assert a.validate_session(tok) is False

    def test_pin_length_validation(self, isolated_db):
        from app.services import auth as a
        with pytest.raises(ValueError):
            a.set_pin("123")  # too short
        with pytest.raises(ValueError):
            a.set_pin("x" * 100)  # too long

    def test_rate_limit_blocks_after_5_failures(self, isolated_db):
        from app.services import auth as a
        a.set_pin("123456")
        for _ in range(5):
            assert a.verify_pin("000000", client_key="abc") is None
        # 6th attempt should be blocked
        assert a.check_rate_limit_ok("abc") is False
        # Even with correct PIN, it's currently blocked (returns None)
        assert a.verify_pin("123456", client_key="abc") is None


class TestAuthRouter:
    def test_status_open_mode(self, isolated_db):
        client = _fresh_client(isolated_db)
        resp = client.get("/api/auth/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pin_set"] is False
        assert "secrets" in data
        assert "telemetry_enabled" in data

    def test_set_pin_via_router_issues_cookie(self, isolated_db):
        client = _fresh_client(isolated_db)
        resp = client.post(
            "/api/auth/pin",
            json={"action": "set", "pin": "987654"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert resp.status_code == 200, resp.text
        assert "coco_session" in resp.cookies or resp.json().get("session")

    def test_verify_pin_via_router(self, isolated_db):
        client = _fresh_client(isolated_db)
        client.post(
            "/api/auth/pin",
            json={"action": "set", "pin": "987654"},
            headers={"Origin": "http://localhost:5173"},
        )
        resp = client.post(
            "/api/auth/pin",
            json={"action": "verify", "pin": "987654"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_verify_wrong_pin_401(self, isolated_db):
        client = _fresh_client(isolated_db)
        client.post(
            "/api/auth/pin",
            json={"action": "set", "pin": "987654"},
            headers={"Origin": "http://localhost:5173"},
        )
        resp = client.post(
            "/api/auth/pin",
            json={"action": "verify", "pin": "wrongo"},
            headers={"Origin": "http://localhost:5173"},
        )
        assert resp.status_code == 401


class TestOriginCheck:
    def test_get_is_unrestricted(self, isolated_db):
        client = _fresh_client(isolated_db)
        # No Origin header
        resp = client.get("/api/auth/status")
        assert resp.status_code == 200

    def test_post_rejects_evil_origin(self, isolated_db):
        client = _fresh_client(isolated_db)
        resp = client.post(
            "/api/auth/status",
            json={},
            headers={"Origin": "https://evil.example.com"},
        )
        # 403 from origin check OR 405 from method-not-allowed; we want 403.
        assert resp.status_code == 403

    def test_post_accepts_localhost_origin(self, isolated_db):
        client = _fresh_client(isolated_db)
        resp = client.post(
            "/api/auth/pin",
            json={"action": "verify", "pin": "nothing"},
            headers={"Origin": "http://localhost:5173"},
        )
        # Origin OK, PIN not set → 401 from "Invalid PIN" (it gets to handler)
        # Actually no PIN is set so verify_pin returns None → 401
        assert resp.status_code == 401

    def test_post_accepts_127_origin(self, isolated_db):
        client = _fresh_client(isolated_db)
        resp = client.post(
            "/api/auth/pin",
            json={"action": "verify", "pin": "nothing"},
            headers={"Origin": "http://127.0.0.1:3001"},
        )
        assert resp.status_code == 401  # not 403

    def test_post_with_no_origin_allowed(self, isolated_db):
        # Non-browser clients (curl) omit Origin — must be allowed.
        client = _fresh_client(isolated_db)
        resp = client.post("/api/auth/pin", json={"action": "verify", "pin": "x"})
        assert resp.status_code in (401, 400)  # NOT 403


class TestProtectedRoute:
    def test_open_mode_allows_writes(self, isolated_db):
        client = _fresh_client(isolated_db)
        resp = client.post(
            "/api/protected",
            json={},
            headers={"Origin": "http://localhost:5173"},
        )
        assert resp.status_code == 200

    def test_pin_set_blocks_writes_without_session(self, isolated_db):
        client = _fresh_client(isolated_db)
        client.post(
            "/api/auth/pin",
            json={"action": "set", "pin": "424242"},
            headers={"Origin": "http://localhost:5173"},
        )
        # New client = no cookies
        client2 = TestClient(_make_app_with_auth_router())
        resp = client2.post(
            "/api/protected",
            json={},
            headers={"Origin": "http://localhost:5173"},
        )
        assert resp.status_code == 401

    def test_pin_session_allows_writes(self, isolated_db):
        client = _fresh_client(isolated_db)
        client.post(
            "/api/auth/pin",
            json={"action": "set", "pin": "424242"},
            headers={"Origin": "http://localhost:5173"},
        )
        # Same client carries the cookie set on PIN set
        resp = client.post(
            "/api/protected",
            json={},
            headers={"Origin": "http://localhost:5173"},
        )
        assert resp.status_code == 200


class TestSessionExpiry:
    def test_session_invalid_after_revoke(self, isolated_db):
        from app.services import auth as a
        a.set_pin("424242")
        tok = a.verify_pin("424242")
        assert a.validate_session(tok)
        a.revoke_session(tok)
        assert a.validate_session(tok) is False

    def test_session_invalid_when_expired(self, isolated_db, monkeypatch):
        from app.services import auth as a
        a.set_pin("424242")
        tok = a.verify_pin("424242")
        # Manually expire by rewinding the session expiry
        sess = a._sessions[tok]
        sess.expires_at = time.time() - 1
        assert a.validate_session(tok) is False
