"""Opt-in telemetry recorder.

Default OFF. Toggle via the `telemetry.enabled` preference (or env var
`COCO_TELEMETRY=true`). When on, events are appended as JSON lines to a
daily-rotated file at `~/.coco/telemetry/YYYY-MM-DD.jsonl`.

No PII, no network egress. The recorder accepts a `record(event_name, props)`
call from anywhere; when telemetry is disabled, `record()` is a fast no-op.

Public API:
    is_enabled() -> bool
    set_enabled(flag, actor="user") -> bool
    record(event, props=None) -> bool   # returns True if recorded
    today_path() -> Path
    list_recent_events(limit=50) -> list[dict]
    clear_cache() -> None  # test-only
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import select, insert, update

from app.config import COCO_DIR
from app.db.session import get_db
from app.db.tables import preferences

PREF_KEY = "telemetry.enabled"
ENV_OVERRIDE = "COCO_TELEMETRY"

_lock = threading.Lock()
_cached_flag: Optional[bool] = None


def _telemetry_dir() -> Path:
    d = Path(COCO_DIR) / "telemetry"
    d.mkdir(parents=True, exist_ok=True)
    return d


def today_path(now: Optional[datetime] = None) -> Path:
    now = now or datetime.now(timezone.utc)
    return _telemetry_dir() / f"{now.strftime('%Y-%m-%d')}.jsonl"


def _read_pref_flag() -> bool:
    with get_db() as conn:
        row = conn.execute(
            select(preferences.c.value).where(preferences.c.key == PREF_KEY)
        ).fetchone()
    if not row:
        return False
    return str(row[0]).lower() in ("true", "1", "yes", "on")


def _write_pref_flag(flag: bool) -> None:
    with get_db() as conn:
        existing = conn.execute(
            select(preferences.c.key).where(preferences.c.key == PREF_KEY)
        ).fetchone()
        val = "true" if flag else "false"
        if existing:
            conn.execute(
                update(preferences).where(preferences.c.key == PREF_KEY).values(value=val)
            )
        else:
            conn.execute(insert(preferences).values(key=PREF_KEY, value=val))


def _ui_opt_out_path() -> Path:
    """Sidecar file at ``~/.coco/telemetry.json`` that records the user's
    explicit UI opt-out. SEC-FIX L4-W2#7: independent of the env var so a
    later ``COCO_TELEMETRY=true`` cannot silently re-enable telemetry.
    """
    return Path(COCO_DIR) / "telemetry.json"


def _read_ui_opt_out() -> bool:
    """Return True if the user has explicitly opted OUT via the UI."""
    p = _ui_opt_out_path()
    if not p.exists():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8") or "{}")
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("opted_out", False))


def _write_ui_opt_out(opted_out: bool) -> None:
    """Atomically persist the UI opt-out flag."""
    p = _ui_opt_out_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "opted_out": bool(opted_out),
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
    }
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, p)


def is_enabled() -> bool:
    """Resolve effective telemetry state.

    SEC-FIX L4-W2#7: precedence is now:
      1. UI opt-out wins absolutely — if the user opted out via the UI, no
         env var can re-enable.
      2. ``COCO_TELEMETRY`` may DISABLE telemetry (env=false) but cannot
         re-enable on its own when the UI flag is off.
      3. Otherwise the persisted preference table value applies.
    """
    global _cached_flag

    # 1) UI opt-out is the hard kill switch.
    if _read_ui_opt_out():
        return False

    env = os.getenv(ENV_OVERRIDE)
    if env is not None:
        env_truthy = env.lower() in ("true", "1", "yes", "on")
        # Env can only DISABLE; if env is true, it still defers to the
        # persisted preference (so a stray export can't re-enable).
        if not env_truthy:
            return False

    if _cached_flag is None:
        _cached_flag = _read_pref_flag()
    return bool(_cached_flag)


def set_enabled(flag: bool, actor: str = "user") -> bool:
    """Persist the opt-in flag. Returns the new state.

    SEC-FIX L4-W2#7: explicit ``False`` also writes a UI opt-out sidecar so
    a later ``COCO_TELEMETRY=true`` env cannot bypass the user's choice.
    Setting ``True`` clears the sidecar.
    """
    global _cached_flag
    flag = bool(flag)
    _write_pref_flag(flag)
    try:
        _write_ui_opt_out(opted_out=not flag)
    except OSError:
        # Sidecar is best-effort — preference table is authoritative.
        pass
    _cached_flag = flag
    return flag


def record(event: str, props: Optional[dict[str, Any]] = None) -> bool:
    """Record one event. Fast no-op when disabled. Returns True on write."""
    if not is_enabled():
        return False
    if not event or not isinstance(event, str):
        return False
    payload = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "event": event,
        "props": props or {},
    }
    line = json.dumps(payload, ensure_ascii=False, default=str)
    path = today_path()
    with _lock:
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            return False
    return True


def list_recent_events(limit: int = 50) -> list[dict]:
    """Read tail of today's file. Best-effort, returns [] on missing file."""
    path = today_path()
    if not path.exists():
        return []
    limit = max(1, min(int(limit), 5000))
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return []
    out: list[dict] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def clear_cache() -> None:
    """Test-only — reset cached enabled flag and the UI opt-out sidecar."""
    global _cached_flag
    _cached_flag = None
    # SEC-FIX L4-W2#7: tests rely on a clean slate; remove the opt-out file.
    try:
        p = _ui_opt_out_path()
        if p.exists():
            p.unlink()
    except OSError:
        pass


__all__ = [
    "is_enabled",
    "set_enabled",
    "record",
    "today_path",
    "list_recent_events",
    "clear_cache",
    "PREF_KEY",
    "ENV_OVERRIDE",
]
