"""QueueService — decisions queue backed by ~/.coco/queue.json + idempotency keys.

Ported from .planning/v3/backend/REFERENCE-IMPL/services/queue_service.py
per DESIGN.md §Service Layer + INTEGRATION-CONTRACT §6.1 + D-04 + D-09.

* Atomic-rename writes (tmp + fsync + rename) under ``fcntl.flock``
* Read-merge-write semantics — additive merge for new items, status-only
  mutations for existing items
* Idempotency keys for approve/reject/defer/cancel
* Cursor-paginated dequeue
* Replay (re-emit prior decision) via persisted history
* Backpressure: ``MAX_QUEUE_SIZE`` returns a structured error
* Schema-version pin (``version: 2``)
* Hash-check on read (RT v1-F-04) — JSON decode failure raises ``TornFileDetected``
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 2
MAX_QUEUE_SIZE = 10_000  # safety backstop


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class QueueError(Exception):
    """Base class for QueueService errors."""


class TornFileDetected(QueueError):
    """queue.json failed to decode — assume mid-write race; restore from backup."""


class QueueFull(QueueError):
    """MAX_QUEUE_SIZE reached."""


class ItemNotFound(QueueError):
    pass


class DuplicateItem(QueueError):
    pass


class IdempotencyReplay(QueueError):
    """Same Idempotency-Key reused with matching body — caller should replay."""

    def __init__(self, original_result: dict[str, Any]):
        super().__init__("idempotency replay")
        self.result = original_result


class IdempotencyConflict(QueueError):
    """Same Idempotency-Key reused with mismatched body."""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _ulid() -> str:
    return uuid.uuid4().hex.upper()[:26]


@dataclass
class QueueItem:
    id: str
    project_id: str
    kind: str
    summary: str
    priority: int = 5
    status: str = "pending"          # pending|approved|rejected|deferred|cancelled
    created_at: str = field(default_factory=_utcnow_iso)
    deferred_until: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    last_idem_key: str | None = None
    last_idem_hash: str | None = None
    last_action_at: str | None = None
    last_result: dict[str, Any] | None = None


def _hash_body(body: dict[str, Any]) -> str:
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Atomic JSON store helper
# ---------------------------------------------------------------------------

class JsonStore:
    """flock + atomic-rename store for a single JSON file.

    Concurrent processes (think.py, CoCo CLI) honor the same lock by convention.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    @contextlib.contextmanager
    def locked(self, *, timeout: float = 5.0):
        # Touch lock file then flock it exclusively.
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            deadline = time.monotonic() + timeout
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"lock timeout on {self.lock_path}")
                    time.sleep(0.02)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": SCHEMA_VERSION, "items": []}
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise TornFileDetected(f"queue.json decode failed: {e}") from e
        if not isinstance(data, dict) or "items" not in data:
            raise TornFileDetected("queue.json missing 'items'")
        return data

    def write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8",
            dir=str(self.path.parent), prefix=self.path.name + ".",
            suffix=".tmp", delete=False,
        )
        try:
            json.dump(data, tmp, ensure_ascii=False, separators=(",", ":"))
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, str(self.path))  # atomic POSIX rename
        except Exception:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(tmp.name)
            raise


# ---------------------------------------------------------------------------
# QueueService
# ---------------------------------------------------------------------------

class QueueService:
    """Decisions queue: enqueue / dequeue / ack / cancel / replay."""

    def __init__(self, store: JsonStore, *, max_size: int = MAX_QUEUE_SIZE):
        self.store = store
        self.max_size = max_size

    # ----- helpers -----

    def _load(self) -> dict[str, Any]:
        return self.store.read()

    def _save(self, data: dict[str, Any]) -> None:
        data["version"] = SCHEMA_VERSION
        self.store.write(data)

    def _find(self, items: list[dict[str, Any]], item_id: str) -> int:
        for i, it in enumerate(items):
            if it["id"] == item_id:
                return i
        return -1

    # ----- public API -----

    def enqueue(self, *, project_id: str, kind: str, summary: str,
                priority: int = 5, metadata: dict[str, Any] | None = None,
                item_id: str | None = None) -> QueueItem:
        with self.store.locked():
            data = self._load()
            items = data.get("items", [])
            if len(items) >= self.max_size:
                raise QueueFull(f"queue >= {self.max_size}")
            new_id = item_id or _ulid()
            if any(it["id"] == new_id for it in items):
                raise DuplicateItem(new_id)
            qi = QueueItem(id=new_id, project_id=project_id, kind=kind,
                           summary=summary, priority=priority,
                           metadata=metadata or {})
            items.append(asdict(qi))
            data["items"] = items
            self._save(data)
            return qi

    def list(self, *, status: str | None = None,
             limit: int = 50, cursor: int = 0) -> tuple[list[QueueItem], int]:
        """Cursor-paginated read. Cursor is an integer offset (opaque to UI)."""
        data = self._load()
        items = data.get("items", [])
        if status is not None:
            items = [it for it in items if it.get("status") == status]
        items.sort(key=lambda it: (-int(it.get("priority", 5)), it.get("created_at", "")))
        page = items[cursor:cursor + limit]
        next_cursor = cursor + len(page)
        return [QueueItem(**{k: v for k, v in it.items() if k in QueueItem.__dataclass_fields__})
                for it in page], next_cursor

    def dequeue(self) -> QueueItem | None:
        """Pop the highest-priority pending item.

        We deliberately do not delete from the file — instead we mark
        status='approved' implicitly. Use the explicit ack/reject/defer methods
        from a caller that wants finer control. ``dequeue`` is mostly used in
        smoke tests + a future batch consumer."""
        with self.store.locked():
            data = self._load()
            items = data.get("items", [])
            for it in sorted(items, key=lambda x: (-int(x.get("priority", 5)), x.get("created_at", ""))):
                if it.get("status") == "pending":
                    it["status"] = "approved"
                    it["last_action_at"] = _utcnow_iso()
                    self._save(data)
                    return QueueItem(**{k: v for k, v in it.items() if k in QueueItem.__dataclass_fields__})
            return None

    def _apply_status(self, item_id: str, *, new_status: str, body: dict[str, Any],
                      idem_key: str | None) -> dict[str, Any]:
        with self.store.locked():
            data = self._load()
            items = data["items"]
            idx = self._find(items, item_id)
            if idx < 0:
                raise ItemNotFound(item_id)
            it = items[idx]

            body_hash = _hash_body(body)

            # Idempotency check (D-09)
            if idem_key:
                if it.get("last_idem_key") == idem_key:
                    if it.get("last_idem_hash") == body_hash:
                        # Replay: return previous result
                        prior = it.get("last_result") or {}
                        raise IdempotencyReplay(prior)
                    raise IdempotencyConflict(idem_key)

            it["status"] = new_status
            if new_status == "deferred":
                it["deferred_until"] = body.get("until")
            it["last_action_at"] = _utcnow_iso()
            if idem_key:
                it["last_idem_key"] = idem_key
                it["last_idem_hash"] = body_hash
            result = {"id": it["id"], "status": new_status,
                      "deferred_until": it.get("deferred_until")}
            it["last_result"] = result
            self._save(data)
            return result

    def approve(self, item_id: str, *, idem_key: str | None = None) -> dict[str, Any]:
        return self._apply_status(item_id, new_status="approved", body={}, idem_key=idem_key)

    def reject(self, item_id: str, *, reason: str | None = None,
               idem_key: str | None = None) -> dict[str, Any]:
        return self._apply_status(item_id, new_status="rejected",
                                  body={"reason": reason or ""}, idem_key=idem_key)

    def defer(self, item_id: str, *, until: str,
              idem_key: str | None = None) -> dict[str, Any]:
        return self._apply_status(item_id, new_status="deferred",
                                  body={"until": until}, idem_key=idem_key)

    def cancel(self, item_id: str) -> dict[str, Any]:
        return self._apply_status(item_id, new_status="cancelled", body={}, idem_key=None)

    def replay(self, item_id: str) -> dict[str, Any] | None:
        """Return the last result for an item (for idempotency replay paths)."""
        data = self._load()
        idx = self._find(data.get("items", []), item_id)
        if idx < 0:
            raise ItemNotFound(item_id)
        return data["items"][idx].get("last_result")

    def merge_from_external(self, external_items: Iterable[dict[str, Any]]) -> int:
        """Additive merge: think.py / CLI may append items; only NEW ids
        are accepted. Existing ids are not overwritten. Returns count added."""
        added = 0
        with self.store.locked():
            data = self._load()
            items = data.get("items", [])
            existing_ids = {it["id"] for it in items}
            for ext in external_items:
                if ext.get("id") in existing_ids:
                    continue
                items.append(ext)
                existing_ids.add(ext["id"])
                added += 1
            data["items"] = items
            self._save(data)
        return added


__all__ = [
    "QueueService",
    "QueueItem",
    "JsonStore",
    "QueueError",
    "TornFileDetected",
    "QueueFull",
    "ItemNotFound",
    "DuplicateItem",
    "IdempotencyReplay",
    "IdempotencyConflict",
    "SCHEMA_VERSION",
    "MAX_QUEUE_SIZE",
]
