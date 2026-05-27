"""PIN authentication endpoints.

Endpoints:
  GET  /api/auth/status         → {pin_set, sessions, secrets, telemetry}
  POST /api/auth/pin            → set/verify PIN; sets session cookie on verify
  POST /api/auth/logout         → revoke current session
  POST /api/auth/telemetry      → toggle opt-in
  GET  /api/auth/secrets        → secret rotation status (no values)

All destructive operations are recorded to the audit log.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.services import auth as auth_service
from app.services import audit as audit_service
from app.services import telemetry as telemetry_service
from app.services import secrets as secrets_service

router = APIRouter(prefix="/api/auth", tags=["System"])


class PinSetRequest(BaseModel):
    action: str = Field(..., description="set | verify | clear")
    pin: Optional[str] = None
    current_pin: Optional[str] = Field(
        None,
        description="Required for 'set' rotation and 'clear' when a PIN is already set",
    )


class TelemetryToggleRequest(BaseModel):
    enabled: bool


def _client_key(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "default"


def _client_ip(request: Request) -> Optional[str]:
    if request.client and request.client.host:
        return request.client.host
    return None


@router.get("/status")
def auth_status():
    """Lightweight status — does NOT require a session."""
    return {
        "pin_set": auth_service.is_pin_set(),
        "sessions": auth_service.sessions_count(),
        "telemetry_enabled": telemetry_service.is_enabled(),
        "secrets": secrets_service.secret_status(),
    }


@router.post("/pin")
def pin_action(payload: PinSetRequest, request: Request, response: Response):
    """Set, verify, or clear the PIN.

    - `set`: requires `pin`; if PIN already exists, also requires `current_pin`.
    - `verify`: requires `pin`; on success issues a session cookie.
    - `clear`: requires `current_pin` if a PIN is set.
    """
    action = (payload.action or "").lower().strip()
    ip = _client_ip(request)
    ck = _client_key(request)

    if action == "set":
        if not payload.pin:
            raise HTTPException(400, "pin is required for 'set'")
        if auth_service.is_pin_set():
            # Rotation requires proving current PIN
            if not payload.current_pin or not auth_service.verify_pin(payload.current_pin, client_key=ck):
                raise HTTPException(401, "current_pin invalid")
        try:
            result = auth_service.set_pin(payload.pin)
        except ValueError as e:
            raise HTTPException(400, str(e))
        audit_service.record(
            audit_service.ACTION_AUTH_PIN_SET,
            actor="user",
            payload={"action": "set"},
            ip=ip,
        )
        # Issue session for convenience
        tok = auth_service.verify_pin(payload.pin, client_key=ck)
        if tok:
            response.set_cookie(
                key="coco_session",
                value=tok,
                httponly=True,
                samesite="strict",
                max_age=auth_service.SESSION_TTL_SECONDS,
                path="/",
            )
            return {**result, "session": tok}
        return result

    if action == "verify":
        if not payload.pin:
            raise HTTPException(400, "pin is required for 'verify'")
        if not auth_service.check_rate_limit_ok(ck):
            raise HTTPException(429, "Too many attempts; try again in a minute")
        tok = auth_service.verify_pin(payload.pin, client_key=ck)
        if not tok:
            raise HTTPException(401, "Invalid PIN")
        response.set_cookie(
            key="coco_session",
            value=tok,
            httponly=True,
            samesite="strict",
            max_age=auth_service.SESSION_TTL_SECONDS,
            path="/",
        )
        return {"status": "ok", "session": tok}

    if action == "clear":
        if auth_service.is_pin_set():
            if not payload.current_pin or not auth_service.verify_pin(payload.current_pin, client_key=ck):
                raise HTTPException(401, "current_pin invalid")
        auth_service.clear_pin()
        audit_service.record(
            audit_service.ACTION_AUTH_PIN_CLEAR,
            actor="user",
            payload={"action": "clear"},
            ip=ip,
        )
        response.delete_cookie("coco_session", path="/")
        return {"status": "cleared", "pin_set": False}

    raise HTTPException(400, f"unknown action '{action}' — use set | verify | clear")


@router.post("/logout")
def logout(request: Request, response: Response):
    tok = request.cookies.get("coco_session") or request.headers.get("X-Coco-Session")
    if tok:
        auth_service.revoke_session(tok)
    response.delete_cookie("coco_session", path="/")
    return {"status": "ok"}


@router.post("/telemetry")
def telemetry_toggle(payload: TelemetryToggleRequest, request: Request):
    new_state = telemetry_service.set_enabled(payload.enabled)
    audit_service.record(
        audit_service.ACTION_TELEMETRY_TOGGLE,
        actor="user",
        payload={"enabled": new_state},
        ip=_client_ip(request),
    )
    return {"telemetry_enabled": new_state}


@router.get("/secrets")
def secrets_status():
    """Rotation status only — never returns secret values."""
    return {"secrets": secrets_service.secret_status()}
