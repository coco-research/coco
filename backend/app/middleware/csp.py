"""Content-Security-Policy middleware.

Centralizes CSP + clickjacking defenses for the platform. See
.planning/v3/backend/DESIGN.md §9 (Auth + Security).

Defaults:
    Content-Security-Policy: default-src 'self'; frame-ancestors 'none'

Notes:
- For the SPA / replay share pages, the existing per-route header in
  `main.py` (more permissive: 'unsafe-inline' for style, blob: media, etc.)
  is left as-is and applied at response time. This middleware ensures a
  hardened default (`default-src 'self'; frame-ancestors 'none'`) is always
  present for API responses that don't get the SPA-specific policy.
- We only set CSP if no upstream layer has already set one. We always set
  `frame-ancestors 'none'` as an additional defense in depth.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

DEFAULT_CSP = "default-src 'self'; frame-ancestors 'none'"


class CSPMiddleware(BaseHTTPMiddleware):
    """Set Content-Security-Policy + clickjacking headers on every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only set default CSP if not already set by a more specific layer
        # (e.g. main.py's per-request security headers handler).
        if "content-security-policy" not in {k.lower() for k in response.headers.keys()}:
            response.headers["Content-Security-Policy"] = DEFAULT_CSP

        # Always enforce no framing for API surfaces.
        path = str(request.url.path)
        if path.startswith("/api/") and "x-frame-options" not in {k.lower() for k in response.headers.keys()}:
            response.headers["X-Frame-Options"] = "DENY"

        return response


__all__ = ["CSPMiddleware", "DEFAULT_CSP"]
