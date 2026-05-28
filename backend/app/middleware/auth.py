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
import re
from typing import Iterable
from urllib.parse import urlsplit

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


_ALLOWED_ORIGIN_IPV6: tuple[str, ...] = ("::1",)


def _origin_allowed(origin: str | None, *, require_present: bool = False) -> bool:
    """Validate the Origin header is localhost-bound.

    SEC-FIX L4-W2#1: Uses ``urllib.parse.urlsplit`` so IPv6 bracketed hosts
    (``http://[::1]:3001``) parse correctly. When ``require_present`` is True
    (state-changing methods), an absent Origin header is rejected — only
    explicit localhost origins pass.
    """
    if not origin:
        # State-changing methods MUST carry an Origin header — otherwise an
        # attacker-controlled non-browser client could bypass the check.
        if require_present:
            return False
        # GET / read-only: allow missing Origin (same-origin and curl).
        return True
    try:
        parts = urlsplit(origin)
        host = parts.hostname  # urlsplit handles IPv6 brackets correctly
    except (ValueError, AttributeError):
        return False
    if not host:
        return False
    host_lower = host.lower()
    if host_lower in _ALLOWED_ORIGIN_HOSTS:
        return True
    if host_lower in _ALLOWED_ORIGIN_IPV6:
        return True
    return False


def _extract_session_token(request: Request) -> str | None:
    """Look for session token in cookie first, then header."""
    tok = request.cookies.get("coco_session")
    if tok:
        return tok
    hdr = request.headers.get("X-Coco-Session") or request.headers.get("x-coco-session")
    return hdr


# SEC-FIX L4-W2#8: X-Request-ID format validation.
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def _sanitize_request_id(request: Request) -> None:
    """If the inbound X-Request-ID is malformed, strip it from the ASGI scope.

    Downstream middleware in main.py will then generate a fresh UUID rather
    than echoing attacker-controlled bytes (which could enable header
    smuggling, log injection, or response splitting).
    """
    incoming = request.headers.get("X-Request-ID") or request.headers.get(
        "x-request-id"
    )
    if incoming is None:
        return
    if _REQUEST_ID_RE.fullmatch(incoming):
        return
    # Strip from ASGI scope headers (the only authoritative source).
    raw_headers = request.scope.get("headers")
    if not isinstance(raw_headers, list):
        return
    request.scope["headers"] = [
        (name, value)
        for (name, value) in raw_headers
        if name.lower() != b"x-request-id"
    ]


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

        # SEC-FIX L4-W2#8: validate X-Request-ID format and sanitize if bogus,
        # so downstream observability middleware never echoes attacker-controlled
        # content. We strip the header from the ASGI scope; main.py will then
        # generate a fresh UUID on receipt.
        _sanitize_request_id(request)

        # 1) Origin check for state-changing methods
        # SEC-FIX L4-W2#1: parse Origin with urlsplit (IPv6 brackets ok, ::1
        # accepted). For absent Origin on /api/* writes, fall back to the
        # Sec-Fetch-Site / Sec-Fetch-Mode browser fetch-metadata signals to
        # reject obvious cross-site browser requests while still allowing
        # non-browser clients (curl, integration tests) that send neither
        # Origin nor Sec-Fetch-* headers.
        if method in STATE_CHANGING_METHODS:
            origin = request.headers.get("origin")
            if origin is not None:
                if not _origin_allowed(origin):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Origin not allowed"},
                    )
            else:
                # Missing Origin — consult fetch-metadata as a fallback.
                sec_site = (request.headers.get("sec-fetch-site") or "").lower()
                if sec_site in ("cross-site", "same-site"):
                    # Cross-origin / sibling-origin browser request → block.
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
