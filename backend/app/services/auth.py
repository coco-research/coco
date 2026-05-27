"""PIN-based authentication service (optional).

Single-user local app. PIN is hashed (PBKDF2-HMAC-SHA256) and stored in the
`preferences` table under key `auth.pin_hash`. Sessions are in-memory tokens
with TTL.

If no PIN is set, all requests are allowed (default open mode — preserves
the existing optional-auth flow). Setting a PIN flips the mode to required.

Public API:
    set_pin(pin, actor="user") -> dict
    verify_pin(pin) -> str | None    # returns a session token on success
    is_pin_set() -> bool
    validate_session(token) -> bool
    revoke_session(token) -> None
    clear_pin(actor="user") -> None  # remove PIN (back to open mode)
    sessions_count() -> int
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select, insert, delete, update

from app.db.session import get_db
from app.db.tables import preferences

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PIN_PREF_KEY = "auth.pin_hash"
PIN_SALT_KEY = "auth.pin_salt"
PBKDF2_ITERATIONS = 100_000
SESSION_TTL_SECONDS = int(os.getenv("COCO_AUTH_SESSION_TTL", str(8 * 3600)))  # 8h
MIN_PIN_LENGTH = 4
MAX_PIN_LENGTH = 32

# Rate limiting: track failed attempts per "client" (in-memory)
_failed_attempts: dict[str, list[float]] = {}
_MAX_ATTEMPTS_PER_MINUTE = 5


# ---------------------------------------------------------------------------
# In-memory session store
# ---------------------------------------------------------------------------

@dataclass
class _Session:
    token: str
    issued_at: float
    expires_at: float


_sessions: dict[str, _Session] = {}


def _purge_expired() -> None:
    """Remove expired sessions (called on access)."""
    now = time.time()
    expired = [tok for tok, s in _sessions.items() if s.expires_at <= now]
    for tok in expired:
        _sessions.pop(tok, None)


# ---------------------------------------------------------------------------
# PIN hashing
# ---------------------------------------------------------------------------

def _hash_pin(pin: str, salt: bytes) -> str:
    """PBKDF2-HMAC-SHA256."""
    dk = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return dk.hex()


def _read_pref(key: str) -> Optional[str]:
    with get_db() as conn:
        row = conn.execute(
            select(preferences.c.value).where(preferences.c.key == key)
        ).fetchone()
        return row[0] if row else None


def _write_pref(key: str, value: str) -> None:
    with get_db() as conn:
        existing = conn.execute(
            select(preferences.c.key).where(preferences.c.key == key)
        ).fetchone()
        if existing:
            conn.execute(
                update(preferences).where(preferences.c.key == key).values(value=value)
            )
        else:
            conn.execute(insert(preferences).values(key=key, value=value))


def _delete_pref(key: str) -> None:
    with get_db() as conn:
        conn.execute(delete(preferences).where(preferences.c.key == key))


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def _check_rate_limit(client_key: str = "default") -> bool:
    """Return True if attempt is allowed (under 5/min). Records the attempt."""
    now = time.time()
    window = 60.0
    attempts = _failed_attempts.setdefault(client_key, [])
    # Drop attempts outside window
    attempts[:] = [t for t in attempts if now - t < window]
    if len(attempts) >= _MAX_ATTEMPTS_PER_MINUTE:
        return False
    return True


def _record_failed_attempt(client_key: str = "default") -> None:
    _failed_attempts.setdefault(client_key, []).append(time.time())


def _reset_attempts(client_key: str = "default") -> None:
    _failed_attempts.pop(client_key, None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_pin_set() -> bool:
    """Whether a PIN is currently configured."""
    return _read_pref(PIN_PREF_KEY) is not None


def set_pin(pin: str, actor: str = "user") -> dict:
    """Set or rotate the PIN. Returns metadata."""
    if not isinstance(pin, str):
        raise ValueError("pin must be a string")
    if len(pin) < MIN_PIN_LENGTH or len(pin) > MAX_PIN_LENGTH:
        raise ValueError(
            f"pin length must be {MIN_PIN_LENGTH}-{MAX_PIN_LENGTH} chars"
        )
    salt = secrets.token_bytes(16)
    pin_hash = _hash_pin(pin, salt)
    _write_pref(PIN_SALT_KEY, salt.hex())
    _write_pref(PIN_PREF_KEY, pin_hash)
    # Invalidate all existing sessions on PIN change
    _sessions.clear()
    return {"status": "set", "pin_set": True, "actor": actor}


def clear_pin(actor: str = "user") -> None:
    """Remove PIN — system returns to open mode."""
    _delete_pref(PIN_PREF_KEY)
    _delete_pref(PIN_SALT_KEY)
    _sessions.clear()


def verify_pin(pin: str, client_key: str = "default") -> Optional[str]:
    """Verify PIN. On success returns a new session token (and clears attempts).
    On failure returns None and records an attempt. Returns None and raises
    nothing on rate-limit; caller can call check_rate_limit_ok() to inspect.
    """
    if not _check_rate_limit(client_key):
        return None
    stored_hash = _read_pref(PIN_PREF_KEY)
    stored_salt_hex = _read_pref(PIN_SALT_KEY)
    if not stored_hash or not stored_salt_hex:
        # No PIN set — verify is not meaningful
        return None
    try:
        salt = bytes.fromhex(stored_salt_hex)
    except ValueError:
        return None
    candidate = _hash_pin(pin, salt)
    if hmac.compare_digest(candidate, stored_hash):
        _reset_attempts(client_key)
        return _issue_session()
    _record_failed_attempt(client_key)
    return None


def check_rate_limit_ok(client_key: str = "default") -> bool:
    """Inspect-only: would the next attempt be allowed?"""
    now = time.time()
    attempts = _failed_attempts.get(client_key, [])
    fresh = [t for t in attempts if now - t < 60.0]
    return len(fresh) < _MAX_ATTEMPTS_PER_MINUTE


def _issue_session() -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    _sessions[token] = _Session(
        token=token, issued_at=now, expires_at=now + SESSION_TTL_SECONDS
    )
    return token


def validate_session(token: Optional[str]) -> bool:
    """Returns True if token is a known, non-expired session."""
    if not token:
        return False
    _purge_expired()
    sess = _sessions.get(token)
    if not sess:
        return False
    if sess.expires_at <= time.time():
        _sessions.pop(token, None)
        return False
    return True


def revoke_session(token: str) -> None:
    _sessions.pop(token, None)


def sessions_count() -> int:
    _purge_expired()
    return len(_sessions)


def reset_state_for_tests() -> None:
    """Test-only helper to wipe sessions and attempt tracking."""
    _sessions.clear()
    _failed_attempts.clear()


__all__ = [
    "is_pin_set",
    "set_pin",
    "verify_pin",
    "clear_pin",
    "validate_session",
    "revoke_session",
    "sessions_count",
    "check_rate_limit_ok",
    "reset_state_for_tests",
    "SESSION_TTL_SECONDS",
]
