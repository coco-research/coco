"""Error envelope: canonical non-2xx response shape for the CoCo Platform API.

This module implements the contract documented in
.planning/v3/backend/INTEGRATION-CONTRACT.md §3:

    {
      "error":   "snake_case_code",
      "message": "Human-readable summary",
      "details": {},
      "request_id": "01HX...",
      "trace_id":  "abc123..."
    }

It exposes:

- :class:`ErrorEnvelope` — Pydantic model used by docs + tests
- :class:`DomainError` and a small library of subclasses
  (:class:`BudgetExceeded`, :class:`IdempotencyConflict`, :class:`StationNotFound`,
  :class:`Unauthorized`, :class:`TooManyStations`)
- :func:`register_exception_handlers` — registers FastAPI handlers for
  ``RequestValidationError``, ``StarletteHTTPException``,
  ``HTTPException``, our ``DomainError`` hierarchy, and a last-resort
  500 fallback.

The handlers always:
* Echo or generate ``X-Request-Id``
* Wrap detail into the envelope shape
* Preserve ``Retry-After`` for 429s
* Scrub raw error messages on the unhandled 500 path
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("coco.platform.error_envelope")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class ErrorEnvelope(BaseModel):
    """Canonical error response shape (binding contract, INTEGRATION-CONTRACT §3)."""

    model_config = ConfigDict(extra="forbid")

    error: str = Field(description="snake_case stable error code")
    message: str = Field(description="Human-readable summary, safe for UI display")
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    trace_id: str | None = None


# ---------------------------------------------------------------------------
# Domain errors
# ---------------------------------------------------------------------------

class DomainError(Exception):
    """Base class for backend domain errors. Subclasses set ``code``, ``status``."""

    code: str = "internal_error"
    status: int = 500
    headers: dict[str, str] = {}

    def __init__(self, message: str, *, details: dict[str, Any] | None = None,
                 headers: dict[str, str] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if headers:
            self.headers = {**self.headers, **headers}


class BudgetExceeded(DomainError):
    code = "budget_exceeded"
    status = 402

    def __init__(self, *, project_id: str, spend_usd: float, cap_usd: float):
        super().__init__(
            f"Daily budget of ${cap_usd:.2f} exceeded; current spend ${spend_usd:.2f}",
            details={"project_id": project_id, "spend_usd": spend_usd, "cap_usd": cap_usd},
        )


class IdempotencyConflict(DomainError):
    code = "idempotency_in_flight"
    status = 409

    def __init__(self, *, key: str):
        super().__init__(
            "Another request with this Idempotency-Key is already in flight",
            details={"idempotency_key": key},
        )


class IdempotencyMismatch(DomainError):
    code = "idempotency_mismatched_body"
    status = 422

    def __init__(self, *, key: str, original_hash: str):
        super().__init__(
            "Idempotency-Key replayed with a different request body",
            details={"idempotency_key": key, "original_request_hash": original_hash},
        )


class StationNotFound(DomainError):
    code = "station_not_found"
    status = 404

    def __init__(self, *, station_id: str):
        super().__init__(f"Station {station_id!r} not found",
                         details={"station_id": station_id})


class Unauthorized(DomainError):
    code = "unauthorized"
    status = 401

    def __init__(self, *, reason: str = "PIN required"):
        super().__init__(reason, details={"reason": reason})


class TooManyStations(DomainError):
    code = "too_many_stations"
    status = 429

    def __init__(self, *, running: int, max_: int, retry_after_s: int = 15):
        super().__init__(
            f"Concurrency cap reached ({running}/{max_}); retry after {retry_after_s}s",
            details={"running": running, "max": max_},
            headers={"Retry-After": str(retry_after_s)},
        )


class RateLimited(DomainError):
    code = "rate_limited"
    status = 429

    def __init__(self, *, retry_after_s: int = 1):
        super().__init__(
            "Rate limit exceeded",
            details={"retry_after_s": retry_after_s},
            headers={"Retry-After": str(retry_after_s)},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _request_id(request: Request) -> str:
    """Echo X-Request-Id from the request, else mint one."""
    rid = request.headers.get("x-request-id")
    if rid and len(rid) <= 128:
        return rid
    return uuid.uuid4().hex


def _envelope_response(
    *, status: int, code: str, message: str,
    details: dict[str, Any] | None, request: Request,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    env = ErrorEnvelope(
        error=code,
        message=message,
        details=details or {},
        request_id=_request_id(request),
        trace_id=request.headers.get("x-trace-id"),
    )
    resp_headers = {"X-Request-Id": env.request_id or ""}
    if headers:
        resp_headers.update(headers)
    return JSONResponse(
        status_code=status,
        content=jsonable_encoder(env),
        headers=resp_headers,
    )


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """422 — Pydantic body/query validation."""
    fields = []
    for err in exc.errors():
        fields.append({
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    return _envelope_response(
        status=422,
        code="validation_failed",
        message="Request validation failed",
        details={"fields": fields},
        request=request,
    )


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Map standard HTTPException to the envelope. Preserves status."""
    # Sensible default code mapping based on status
    code_by_status = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_failed",
        429: "rate_limited",
        500: "internal_error",
        503: "service_unavailable",
    }
    code = code_by_status.get(exc.status_code, "http_error")

    # detail may be a string (Starlette) or arbitrary JSON (FastAPI)
    detail = exc.detail
    if isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("detail") or "HTTP error")
        details: dict[str, Any] = {k: v for k, v in detail.items() if k != "message"}
    else:
        message = str(detail) if detail is not None else "HTTP error"
        details = {}

    headers = getattr(exc, "headers", None) or None
    return _envelope_response(
        status=exc.status_code,
        code=code,
        message=message,
        details=details,
        request=request,
        headers=headers,
    )


async def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return _envelope_response(
        status=exc.status,
        code=exc.code,
        message=exc.message,
        details=exc.details,
        request=request,
        headers=exc.headers or None,
    )


async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler. Scrubs the message; full stack is logged only."""
    log.exception("unhandled exception in request", extra={"path": str(request.url)})
    return _envelope_response(
        status=500,
        code="internal_error",
        message="An internal error occurred. Please retry.",
        details={},
        request=request,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire up all envelope-producing handlers on a FastAPI app."""
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(DomainError, _domain_error_handler)
    # Order matters: register specific subclasses first if they need custom mapping,
    # then a generic Exception fallback last.
    app.add_exception_handler(Exception, _unhandled_handler)


__all__ = [
    "ErrorEnvelope",
    "DomainError",
    "BudgetExceeded",
    "IdempotencyConflict",
    "IdempotencyMismatch",
    "StationNotFound",
    "Unauthorized",
    "TooManyStations",
    "RateLimited",
    "register_exception_handlers",
]
