"""Idempotency middleware.

Implements Stripe-style idempotency on mutating HTTP methods. See
.planning/v3/backend/DESIGN.md §7 and .planning/v3/INTEGRATION.md §C-4.

- Header: `Idempotency-Key` (≤255 chars, recommended UUIDv4).
- Storage: `idempotency_keys(key, route, request_hash, response_status,
  response_body, created_at)`. UNIQUE(key, route).
- TTL: 24h. Pruning is handled by a background scheduler (out of scope here).
- Required on:
    POST /api/stations/{id}/spawn
    POST /api/queue/{id}/{action}
    POST /api/ingest
    POST /api/chat
  Optional but honored on any other mutating method.

Behavior:
- First request with a given key+route → execute downstream, persist response.
- Replay (same key, same route, same body hash) → return persisted response
  (status + body) without re-executing.
- Same key+route with different body hash → 422 idempotency_mismatched_body.
- Concurrency for in-flight execution is best-effort: this middleware
  uses INSERT-after-completion semantics; concurrent first-shots may both
  execute, but only one row will persist (UNIQUE constraint). The second
  inserter detects the conflict and returns the persisted response.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import time
from typing import Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.config import PLATFORM_DB_PATH


# SEC-FIX L4-W2#3: serialization envelope for storing arbitrary response
# bytes + content-type into the existing TEXT column.
# Format: a leading sentinel + JSON envelope (v=1). Legacy un-enveloped rows
# are decoded as UTF-8 application/json, preserving backwards compatibility.
_ENVELOPE_SENTINEL = "\x00coco-idem-v1:"


def _encode_envelope(body: bytes, content_type: str) -> str:
    """Pack raw response bytes + content-type into a TEXT-safe envelope."""
    payload = {
        "v": 1,
        "ctype": content_type or "application/json",
        "b64": base64.b64encode(body or b"").decode("ascii"),
    }
    return _ENVELOPE_SENTINEL + json.dumps(payload, separators=(",", ":"))


def _decode_envelope(stored: str) -> tuple[bytes, str]:
    """Reverse of ``_encode_envelope``. Legacy rows (no sentinel) decode as
    UTF-8 / application/json so old idempotency records keep working."""
    if not stored:
        return b"", "application/json"
    if stored.startswith(_ENVELOPE_SENTINEL):
        try:
            payload = json.loads(stored[len(_ENVELOPE_SENTINEL):])
            return (
                base64.b64decode(payload.get("b64", "")),
                str(payload.get("ctype") or "application/json"),
            )
        except (ValueError, TypeError):
            # Corrupt envelope — treat as legacy UTF-8 fallback.
            pass
    return stored.encode("utf-8", errors="replace"), "application/json"

# Methods that may carry an Idempotency-Key
MUTATING_METHODS: frozenset[str] = frozenset({"POST", "PUT", "DELETE", "PATCH"})

# Routes where the header is REQUIRED (missing → 400)
REQUIRED_ROUTE_PREFIXES: tuple[str, ...] = (
    "/api/stations/",     # POST .../spawn — required only for spawn, but
                          # we enforce 'present-or-not-required' at handler
                          # level; here we treat all station POSTs as honored.
    "/api/queue/",        # POST .../{action}
    "/api/ingest",
    "/api/chat",
)

# Routes whose responses contain sensitive material (session tokens, PIN-related
# state) and MUST NOT be persisted to idempotency_keys.response_body. Requests
# to these paths are passed through to the handler but the response is never
# cached — even if the client supplied an Idempotency-Key.
# SEC-FIX L4#1: see .planning/v3/reanalyse for context.
IDEMPOTENCY_AUTH_DENY_PATHS: tuple[str, ...] = (
    "/api/auth/",
)


def _is_auth_deny(path: str) -> bool:
    return any(path.startswith(p) for p in IDEMPOTENCY_AUTH_DENY_PATHS)

# Routes that explicitly REQUIRE the header on mutating verbs.
# (Spawn is the only required station mutator per DESIGN §7.)
def _is_required(method: str, path: str) -> bool:
    if method != "POST":
        return False
    if path.endswith("/spawn") and path.startswith("/api/stations/"):
        return True
    if path.startswith("/api/queue/"):
        # POST /api/queue/{id}/{action}
        return True
    if path == "/api/ingest" or path.startswith("/api/ingest/"):
        return True
    if path == "/api/chat" or path.startswith("/api/chat/"):
        return True
    return False


_MAX_KEY_LEN = 255


def _hash_body(body: bytes) -> str:
    return hashlib.sha256(body or b"").hexdigest()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(PLATFORM_DB_PATH), timeout=5.0, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _lookup(
    conn: sqlite3.Connection, key: str, route: str
) -> tuple[str, int, bytes, str] | None:
    """Return (request_hash, response_status, body_bytes, content_type) or None.

    SEC-FIX L4-W2#3: response body is unpacked via the envelope decoder so
    binary payloads replay byte-perfect with their original content-type.
    Legacy un-enveloped rows decode as UTF-8 / application/json.
    """
    row = conn.execute(
        "SELECT request_hash, response_status, response_body "
        "FROM idempotency_keys WHERE key = ? AND route = ?",
        (key, route),
    ).fetchone()
    if not row:
        return None
    req_hash, status, stored = row
    body_bytes, ctype = _decode_envelope(stored if isinstance(stored, str) else "")
    return req_hash, int(status), body_bytes, ctype


def _persist(
    conn: sqlite3.Connection,
    key: str,
    route: str,
    request_hash: str,
    status: int,
    body: bytes,
    content_type: str,
) -> bool:
    """Insert idempotency row. Returns True on success, False on UNIQUE conflict.

    SEC-FIX L4-W2#3: body is wrapped in a base64 envelope along with its
    content-type so binary payloads round-trip without UTF-8 corruption
    and replay returns the original media-type.
    """
    envelope = _encode_envelope(body or b"", content_type or "application/json")
    try:
        conn.execute(
            "INSERT INTO idempotency_keys "
            "(key, route, request_hash, response_status, response_body, created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (key, route, request_hash, int(status), envelope),
        )
        return True
    except sqlite3.IntegrityError:
        return False


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """ASGI middleware enforcing Idempotency-Key on mutating endpoints."""

    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        path = request.url.path

        # Only mutating methods on /api/* are candidates
        if method not in MUTATING_METHODS or not path.startswith("/api/"):
            return await call_next(request)

        # SEC-FIX L4#1: Never cache responses for auth endpoints (session tokens leak).
        # If the client sends an Idempotency-Key for /api/auth/*, ignore it
        # and pass straight through — do NOT persist the response body.
        if _is_auth_deny(path):
            return await call_next(request)

        key = request.headers.get("Idempotency-Key")
        required = _is_required(method, path)

        if not key:
            if required:
                return JSONResponse(
                    {
                        "error": "idempotency_key_required",
                        "message": (
                            "Idempotency-Key header is required on this endpoint. "
                            "Provide a UUIDv4 (≤255 chars)."
                        ),
                    },
                    status_code=400,
                )
            return await call_next(request)

        # SEC-FIX L4-W2#6: enforce byte length, not char length. Multi-byte
        # Unicode could otherwise smuggle ≤255-char keys that exceed the DB
        # column width (and silently truncate on insert).
        if len(key.encode("utf-8")) > _MAX_KEY_LEN:
            return JSONResponse(
                {
                    "error": "idempotency_key_too_long",
                    "message": f"Idempotency-Key must be ≤{_MAX_KEY_LEN} bytes.",
                },
                status_code=400,
            )

        # Read body once; reuse downstream by stashing on request.
        body = await request.body()
        request_hash = _hash_body(body)
        route = f"{method} {path}"

        # Lookup existing record
        try:
            conn = _connect()
        except sqlite3.Error as e:
            # SEC-FIX L4#6: fail CLOSED on required-set routes (return 503).
            # Idempotency guarantees are load-bearing for spawn/ingest/chat/queue —
            # silently bypassing them allows duplicate side effects.
            if required:
                import structlog as _s
                try:
                    _s.get_logger().warning(
                        "idempotency_db_unavailable_fail_closed",
                        path=path,
                        error=str(e),
                    )
                except Exception:
                    pass
                return JSONResponse(
                    {
                        "error": "idempotency_unavailable",
                        "message": (
                            "Idempotency store is temporarily unavailable. "
                            "Retry with the same Idempotency-Key shortly."
                        ),
                    },
                    status_code=503,
                )
            # Non-required routes: fail open (don't break the API).
            return await call_next(request)
        try:
            existing = _lookup(conn, key, route)
            if existing is not None:
                prev_hash, prev_status, prev_body, prev_ctype = existing
                if prev_hash != request_hash:
                    return JSONResponse(
                        {
                            "error": "idempotency_mismatched_body",
                            "message": (
                                "Idempotency-Key has been used before on this route "
                                "with a different request body."
                            ),
                        },
                        status_code=422,
                    )
                # SEC-FIX L4-W2#3: replay with the original content-type and
                # binary-safe bytes — no forced application/json.
                return Response(
                    content=prev_body,
                    status_code=prev_status,
                    media_type=prev_ctype or "application/json",
                    headers={"Idempotency-Replay": "true"},
                )
        finally:
            conn.close()

        # First execution. Re-inject body so downstream handlers can read it.
        async def _receive():
            return {"type": "http.request", "body": body, "more_body": False}
        request._receive = _receive  # type: ignore[attr-defined]

        response = await call_next(request)

        # Buffer the response so we can persist + replay later.
        chunks: list[bytes] = []
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            chunks.append(chunk)
        body_out = b"".join(chunks)

        # Capture original content-type for accurate replay (SEC-FIX L4-W2#3).
        resp_ctype = (
            response.media_type
            or response.headers.get("content-type", "application/json")
        )

        # Persist only successful responses (2xx) to avoid caching transient errors.
        if 200 <= response.status_code < 300:
            try:
                conn = _connect()
                try:
                    ok = _persist(
                        conn,
                        key,
                        route,
                        request_hash,
                        response.status_code,
                        body_out,
                        resp_ctype,
                    )
                    if not ok:
                        # Concurrent insert won: replay the stored one to keep clients consistent.
                        existing = _lookup(conn, key, route)
                        if existing is not None:
                            prev_hash, prev_status, prev_body, prev_ctype = existing
                            return Response(
                                content=prev_body,
                                status_code=prev_status,
                                media_type=prev_ctype or "application/json",
                                headers={"Idempotency-Replay": "true"},
                            )
                finally:
                    conn.close()
            except sqlite3.Error:
                # Best-effort persistence; don't fail the original request.
                pass

        return Response(
            content=body_out,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


__all__: Iterable[str] = ["IdempotencyMiddleware"]
