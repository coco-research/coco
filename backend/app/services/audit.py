"""Audit log service — record destructive actions to platform.db.

Public API:
    record(action, actor="user", payload=None, ip=None) -> int  # row id
    list_recent(limit=100, action=None) -> list[dict]
    count(action=None) -> int

Payloads are hashed (SHA-256, hex) before storage — we never persist raw
arguments. This protects accidental secret/PII bleed via audit rows while
still letting us verify "same action, same args" in incident review.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, insert, func, desc

from app.db.session import get_db
from app.db.tables import audit_log

# Canonical destructive action vocabulary — keep tight; new actions OK.
ACTION_QUEUE_ACK = "queue.ack"
ACTION_QUEUE_DISMISS = "queue.dismiss"
ACTION_STATION_KILL = "station.kill"
ACTION_AGENT_KILL = "agent.kill"
ACTION_BRAIN_DELETE = "brain.delete"
ACTION_SETTINGS_CHANGE = "settings.change"
ACTION_AUTH_PIN_SET = "auth.pin_set"
ACTION_AUTH_PIN_CLEAR = "auth.pin_clear"
ACTION_TELEMETRY_TOGGLE = "telemetry.toggle"


def _hash_payload(payload: Any) -> Optional[str]:
    """Stable SHA-256 hex of the payload, or None if payload is None."""
    if payload is None:
        return None
    try:
        canonical = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        canonical = str(payload)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def record(
    action: str,
    actor: str = "user",
    payload: Any = None,
    ip: Optional[str] = None,
) -> int:
    """Append an audit row. Returns the new row's `id`."""
    if not action or not isinstance(action, str):
        raise ValueError("action must be a non-empty string")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload_hash = _hash_payload(payload)
    with get_db() as conn:
        result = conn.execute(
            insert(audit_log).values(
                action=action,
                actor=actor or "user",
                payload_hash=payload_hash,
                occurred_at=now,
                ip=ip,
            )
        )
        # SQLite/SA returns lastrowid via inserted_primary_key
        pk = result.inserted_primary_key
        return int(pk[0]) if pk else 0


def list_recent(limit: int = 100, action: Optional[str] = None) -> list[dict]:
    """Return the most recent audit rows (newest first)."""
    limit = max(1, min(int(limit), 1000))
    stmt = select(
        audit_log.c.id,
        audit_log.c.action,
        audit_log.c.actor,
        audit_log.c.payload_hash,
        audit_log.c.occurred_at,
        audit_log.c.ip,
    ).order_by(desc(audit_log.c.id)).limit(limit)
    if action:
        stmt = stmt.where(audit_log.c.action == action)
    with get_db() as conn:
        rows = conn.execute(stmt).fetchall()
    return [
        {
            "id": r[0],
            "action": r[1],
            "actor": r[2],
            "payload_hash": r[3],
            "occurred_at": r[4],
            "ip": r[5],
        }
        for r in rows
    ]


def count(action: Optional[str] = None) -> int:
    stmt = select(func.count()).select_from(audit_log)
    if action:
        stmt = stmt.where(audit_log.c.action == action)
    with get_db() as conn:
        return int(conn.execute(stmt).scalar() or 0)


__all__ = [
    "record",
    "list_recent",
    "count",
    "ACTION_QUEUE_ACK",
    "ACTION_QUEUE_DISMISS",
    "ACTION_STATION_KILL",
    "ACTION_AGENT_KILL",
    "ACTION_BRAIN_DELETE",
    "ACTION_SETTINGS_CHANGE",
    "ACTION_AUTH_PIN_SET",
    "ACTION_AUTH_PIN_CLEAR",
    "ACTION_TELEMETRY_TOGGLE",
]
