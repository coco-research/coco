"""Authentication + origin-check middleware.

Two-layered, optional design — CoCo is designed for single-user local use:

1. **Origin check** (always-on for state-changing methods): rejects
   non-localhost Origin headers on POST/PUT/PATCH/DELETE. Localhost
   variants (`http://localhost*`, `http://127.0.0.1*`) and missing Origin
   (same-origin / non-browser clients) are allowed.

2. **PIN session OR bearer token** (active only when configured):
   - If `COCO_AUTH_TOKEN` env var is set → require Bearer header (back-compat).
   - Else if a PIN is set via `services.auth.set_pin` → require a valid
     `coco_session` cookie (or `X-Coco-Session` header) for /api/* writes.
   - Else → open mode (no auth required).

Exempt paths (no auth, no origin check): /api/health/*, /api/auth/*,
/api/edition, /docs, /openapi.json, /redoc, static assets.
"""
from __future__ import annotations

import os
from typing import Iterable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services import auth as auth_service

AUTH_TOKEN = os.getenv("COCO_AUTH_TOKEN", "")

# Paths that never require auth
PUBLIC_PATHS = {
    "/api/health",
    "/api/edition",
    "/api/auth/pin",
    "/api/auth/status",
    "/api/auth/logout",
    "/docs",
    "/openapi.json",
    "/redoc",
}

PUBLIC_PREFIXES: tuple[str, ...] = (
    "/api/health/",  # /api/health/ready, /api/health/detail
    "/api/auth/",
)

STATE_CHANGING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Allowed Origin host substrings (case-insensitive prefix match on host part)
_ALLOWED_ORIGIN_HOSTS: tuple[str, ...] = (
    "localhost",
    "127.0.0.1",
)


def _is_public_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    if not path.startswith("/api/"):
        # Static frontend, etc.
        return True
    return False


def _origin_allowed(origin: str | None) -> bool:
    """Validate the Origin header is localhost-bound."""
    if not origin:
        # Same-origin requests and non-browser clients (curl) omit Origin.
        return True
    # Origin format: scheme://host[:port]
    try:
        rest = origin.split("://", 1)[1]
        host = rest.split("/", 1)[0]
        host_only = host.split(":", 1)[0].lower()
    except (IndexError, ValueError):
        return False
    return host_only in _ALLOWED_ORIGIN_HOSTS


def _extract_session_token(request: Request) -> str | None:
    """Look for session token in cookie first, then header."""
    tok = request.cookies.get("coco_session")
    if tok:
        return tok
    hdr = request.headers.get("X-Coco-Session") or request.headers.get("x-coco-session")
    return hdr


class AuthMiddleware(BaseHTTPMiddleware):
    """Combined origin-check + (token | PIN-session) middleware.

    Backward-compatible: when neither `COCO_AUTH_TOKEN` is set nor a PIN is
    configured, only the origin check runs.
    """

    def __init__(self, app, *, public_paths: Iterable[str] | None = None):
        super().__init__(app)
        if public_paths:
            self._extra_public = set(public_paths)
        else:
            self._extra_public = set()

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        method = request.method.upper()

        # 1) Origin check for state-changing methods
        if method in STATE_CHANGING_METHODS:
            if not _origin_allowed(request.headers.get("origin")):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Origin not allowed"},
                )

        # 2) Public paths bypass auth
        if _is_public_path(path) or path in self._extra_public:
            return await call_next(request)

        # 3) Bearer token mode (legacy, env-configured)
        if AUTH_TOKEN:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing or invalid Authorization header"},
                )
            token = auth_header[7:]
            if token != AUTH_TOKEN:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid authentication token"},
                )
            return await call_next(request)

        # 4) PIN-session mode (active only when a PIN is configured)
        if auth_service.is_pin_set():
            sess_tok = _extract_session_token(request)
            if not auth_service.validate_session(sess_tok):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "PIN required"},
                )
            return await call_next(request)

        # 5) Open mode — no auth configured
        return await call_next(request)
