"""Secret loader + rotation timestamp tracking.

Reads known secrets from `~/.coco/` files (e.g. `.qb-gateway-key`) and tracks
when each was last seen — surfaces a rotation warning via `secret_status()`.

Never logs or echoes secret values. Cache uses mtime invalidation so an
external `chmod`/`echo > file` rotation is picked up automatically.
"""
from __future__ import annotations

import logging
import os
import stat as _stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.config import COCO_DIR

logger = logging.getLogger(__name__)

# Known secrets registry — name -> filename (relative to COCO_DIR)
KNOWN_SECRETS: dict[str, str] = {
    "qb_gateway_key": ".qb-gateway-key",
    "anthropic_api_key": ".anthropic-api-key",
    "openai_api_key": ".openai-api-key",
    "deepgram_api_key": ".deepgram-api-key",
}

# Rotation thresholds (days)
ROTATION_WARN_DAYS = int(os.getenv("COCO_SECRET_WARN_DAYS", "90"))
ROTATION_CRITICAL_DAYS = int(os.getenv("COCO_SECRET_CRITICAL_DAYS", "180"))


@dataclass
class SecretMeta:
    name: str
    path: Path
    present: bool
    mtime: Optional[float] = None
    age_seconds: Optional[float] = None
    status: str = "missing"  # missing | ok | warn | critical
    rotation_advice: Optional[str] = None


# Cache: name -> (mtime, value)
_cache: dict[str, tuple[float, str]] = {}


def _secret_path(name: str) -> Path:
    fname = KNOWN_SECRETS.get(name)
    if fname is None:
        raise KeyError(f"Unknown secret: {name}")
    return Path(COCO_DIR) / fname


def _is_secret_file_safe(p: Path) -> tuple[bool, Optional[str]]:
    """SEC-FIX L4-W2#4: verify the secret file is not symlinked, not
    group/other-readable, and owned by the current uid. Returns
    ``(ok, reason)``. ``reason`` is set when the file should be rejected.

    On non-POSIX platforms (no real uid/mode semantics) this is a no-op.
    """
    try:
        # Refuse symlinks outright — they can redirect to untrusted paths.
        if p.is_symlink():
            return False, "symlink"
        st = p.lstat()
    except OSError as exc:
        return False, f"stat_failed:{exc.__class__.__name__}"

    # Skip POSIX-specific checks on Windows (no meaningful mode/uid).
    if os.name != "posix":
        return True, None

    # Reject group/other readable or writable bits.
    mode = _stat.S_IMODE(st.st_mode)
    if mode & 0o077:
        return False, f"mode_too_open:0o{mode:03o}"

    # Reject foreign-owned files. (Root-owned files readable by current uid
    # are still permitted only when uid matches, by design.)
    try:
        current_uid = os.geteuid()
    except AttributeError:
        return True, None
    if st.st_uid != current_uid:
        return False, f"wrong_owner:uid={st.st_uid}"

    return True, None


def get_secret(name: str) -> Optional[str]:
    """Read a secret by name, using mtime-invalidated cache. Strips trailing
    whitespace. Returns None if absent.

    SEC-FIX L4-W2#4: refuses to read the file if it is a symlink, has group
    or other read/write bits set, or is owned by a different uid.
    """
    p = _secret_path(name)
    if not p.exists():
        # Drop cache entry if file deleted
        _cache.pop(name, None)
        return None
    safe, reason = _is_secret_file_safe(p)
    if not safe:
        _cache.pop(name, None)
        logger.warning(
            "secret_file_unsafe name=%s reason=%s path=%s",
            name,
            reason,
            str(p),
        )
        return None
    try:
        stat = p.stat()
    except OSError:
        return None
    cached = _cache.get(name)
    if cached and cached[0] == stat.st_mtime:
        return cached[1]
    try:
        value = p.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    _cache[name] = (stat.st_mtime, value)
    return value or None


def has_secret(name: str) -> bool:
    """Whether the secret file exists (does not read contents)."""
    p = _secret_path(name)
    return p.exists()


def secret_meta(name: str, *, now: Optional[float] = None) -> SecretMeta:
    """Return rotation status metadata for a known secret. Never reads value."""
    import time
    p = _secret_path(name)
    if not p.exists():
        return SecretMeta(name=name, path=p, present=False, status="missing")
    try:
        mtime = p.stat().st_mtime
    except OSError:
        return SecretMeta(name=name, path=p, present=False, status="missing")
    now = now if now is not None else time.time()
    age = max(0.0, now - mtime)
    age_days = age / 86400.0
    if age_days >= ROTATION_CRITICAL_DAYS:
        status = "critical"
        advice = f"Rotate ASAP — {age_days:.0f}d old (>= {ROTATION_CRITICAL_DAYS}d)"
    elif age_days >= ROTATION_WARN_DAYS:
        status = "warn"
        advice = f"Rotate soon — {age_days:.0f}d old (>= {ROTATION_WARN_DAYS}d)"
    else:
        status = "ok"
        advice = None
    return SecretMeta(
        name=name,
        path=p,
        present=True,
        mtime=mtime,
        age_seconds=age,
        status=status,
        rotation_advice=advice,
    )


def secret_status() -> list[dict]:
    """Return rotation status for all known secrets (no values). Safe to expose
    via an admin endpoint."""
    out: list[dict] = []
    for name in KNOWN_SECRETS:
        m = secret_meta(name)
        out.append({
            "name": name,
            "present": m.present,
            "status": m.status,
            "age_days": (m.age_seconds / 86400.0) if m.age_seconds is not None else None,
            "rotation_advice": m.rotation_advice,
        })
    return out


def clear_cache() -> None:
    """Test-only helper."""
    _cache.clear()


__all__ = [
    "KNOWN_SECRETS",
    "SecretMeta",
    "get_secret",
    "has_secret",
    "secret_meta",
    "secret_status",
    "clear_cache",
]
