"""Trigger engine -- runs cron and file_watch triggers in background.

Cron triggers fire based on standard 5-field cron expressions, evaluated
once per minute (60s tick).

File-watch triggers poll a directory for mtime changes (30s tick). The
config supports {path, patterns, recursive, ignore} -- recursive=true uses
rglob, ignore is a list of substrings filtered out of the match set.

Webhook triggers fire on POST to /api/webhooks/{trigger_id}; no in-process
loop here.

Every fire is recorded in the trigger_log table by _fire() below.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog

from app.db.session import get_db

log = structlog.get_logger()

CRON_TICK_SECONDS = 60
FILE_WATCH_TICK_SECONDS = 30


class TriggerEngine:
    def __init__(self):
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._file_mtime_cache: dict[str, float] = {}
        self._cron_fired_at: dict[str, str] = {}

    async def start(self):
        """Start the trigger engine. Call from FastAPI lifespan."""
        self._running = True
        log.info("trigger_engine_starting")
        self._ensure_self_improve_trigger()
        self._tasks.append(asyncio.create_task(self._cron_loop()))
        self._tasks.append(asyncio.create_task(self._file_watch_loop()))

    async def stop(self):
        """Stop all trigger loops."""
        self._running = False
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        log.info("trigger_engine_stopped")

    async def _cron_loop(self):
        while self._running:
            try:
                triggers = self._load_triggers("cron")
                now = datetime.now(timezone.utc)
                minute_key = now.strftime("%Y-%m-%dT%H:%M")

                for t in triggers:
                    trigger_id = t["id"]
                    config = json.loads(t["config"]) if isinstance(t["config"], str) else t["config"]
                    cron_expr = config.get("expression") or config.get("cron", "")

                    if not cron_expr:
                        continue

                    if self._cron_fired_at.get(trigger_id) == minute_key:
                        continue

                    if self._cron_matches(cron_expr, now):
                        log.info("cron_trigger_matched", trigger_id=trigger_id, name=t["name"], cron=cron_expr)
                        self._cron_fired_at[trigger_id] = minute_key
                        await self._fire(t)

                self._cron_fired_at = {
                    k: v for k, v in self._cron_fired_at.items() if v == minute_key
                }
            except Exception as e:
                log.warning("cron_loop_error", error=str(e))
            await asyncio.sleep(CRON_TICK_SECONDS)

    async def _file_watch_loop(self):
        while self._running:
            try:
                triggers = self._load_triggers("file_watch")
                for t in triggers:
                    config = json.loads(t["config"]) if isinstance(t["config"], str) else t["config"]
                    watch_path = config.get("path", "")
                    patterns = config.get("patterns", ["*"]) or ["*"]
                    recursive = bool(config.get("recursive", False))
                    ignore = config.get("ignore", []) or []
                    if not watch_path or not os.path.exists(watch_path):
                        continue

                    changed_files: list[str] = []
                    p = Path(watch_path)

                    if p.is_file():
                        mtime = p.stat().st_mtime
                        key = f"{t['id']}:{p}"
                        if key in self._file_mtime_cache and self._file_mtime_cache[key] < mtime:
                            changed_files.append(str(p))
                        self._file_mtime_cache[key] = mtime
                    else:
                        glob_fn = p.rglob if recursive else p.glob
                        for pattern in patterns:
                            for f in glob_fn(pattern):
                                if not f.is_file():
                                    continue
                                # Apply ignore filters (substring match against full path).
                                if any(ig and ig in str(f) for ig in ignore):
                                    continue
                                mtime = f.stat().st_mtime
                                key = f"{t['id']}:{f}"
                                if key in self._file_mtime_cache and self._file_mtime_cache[key] < mtime:
                                    changed_files.append(str(f))
                                self._file_mtime_cache[key] = mtime

                    if changed_files:
                        log.info("file_watch_triggered", trigger_id=t["id"], changed=changed_files[:5], total=len(changed_files))
                        await self._fire(t, context={"changed_files": changed_files})
            except Exception as e:
                log.warning("file_watch_loop_error", error=str(e))
            await asyncio.sleep(FILE_WATCH_TICK_SECONDS)

    def _load_triggers(self, trigger_type: str) -> list[dict]:
        with get_db() as conn:
            rows = conn.exec_driver_sql(
                "SELECT * FROM triggers WHERE trigger_type = ? AND enabled = 1",
                (trigger_type,),
            ).fetchall()
            return [dict(r._mapping) for r in rows]

    async def _fire(self, trigger: dict, context: dict | None = None):
        """Execute trigger action and log result."""
        from app.routers.triggers import _execute_trigger_action, _log_trigger_fire  # noqa: lazy import (cycle)

        try:
            result = await _execute_trigger_action(trigger, context=context)
            status = result.get("status", "success")
            with get_db() as conn:
                _log_trigger_fire(
                    conn,
                    trigger["id"],
                    status=status,
                    result=json.dumps(result),
                    error=result.get("error"),
                )
            log.info("trigger_fired", trigger_id=trigger["id"], name=trigger["name"], status=status)
        except Exception as e:
            with get_db() as conn:
                _log_trigger_fire(
                    conn,
                    trigger["id"],
                    status="failed",
                    error=str(e),
                )
            log.warning("trigger_fire_failed", trigger_id=trigger["id"], error=str(e))

    def _ensure_self_improve_trigger(self):
        """Register the default self-improve auto trigger if it doesn't exist."""
        try:
            from app.services.self_improve_scheduler import get_self_improve_preferences  # noqa: lazy import (cycle)

            prefs = get_self_improve_preferences()

            with get_db() as conn:
                existing = conn.exec_driver_sql(
                    "SELECT id, config FROM triggers WHERE action_type = 'self_improve_auto' LIMIT 1",
                ).fetchone()

                if existing:
                    # Update cron expression if preference changed
                    current_config = json.loads(existing._mapping["config"]) if isinstance(existing._mapping["config"], str) else existing._mapping["config"]
                    if current_config.get("expression") != prefs["cron"]:
                        conn.exec_driver_sql(
                            "UPDATE triggers SET config = ?, enabled = ?, updated_at = ? WHERE id = ?",
                            (
                                json.dumps({"expression": prefs["cron"]}),
                                1 if prefs["enabled"] else 0,
                                datetime.now(timezone.utc).isoformat(),
                                existing._mapping["id"],
                            ),
                        )
                        log.info("self_improve_trigger_updated", cron=prefs["cron"], enabled=prefs["enabled"])
                else:
                    now = datetime.now(timezone.utc).isoformat()
                    conn.exec_driver_sql(
                        "INSERT INTO triggers (id, name, trigger_type, enabled, config, action_type, action_config, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            str(uuid.uuid4()),
                            "Self-Improve Auto Cycle",
                            "cron",
                            1 if prefs["enabled"] else 0,
                            json.dumps({"expression": prefs["cron"]}),
                            "self_improve_auto",
                            json.dumps({}),
                            now,
                            now,
                        ),
                    )
                    log.info("self_improve_trigger_registered", cron=prefs["cron"], enabled=prefs["enabled"])
        except Exception as e:
            log.warning("self_improve_trigger_setup_failed", error=str(e))

    @staticmethod
    def _cron_matches(expr: str, now: datetime) -> bool:
        if not expr:
            return False
        parts = expr.strip().split()
        if len(parts) != 5:
            return False

        fields = [now.minute, now.hour, now.day, now.month, now.isoweekday() % 7]

        for cron_part, current_val in zip(parts, fields):
            if not _cron_field_matches(cron_part, current_val):
                return False
        return True


def _cron_field_matches(cron_part: str, current_val: int) -> bool:
    if cron_part == "*":
        return True

    if "," in cron_part:
        return any(_cron_field_matches(sub.strip(), current_val) for sub in cron_part.split(","))

    if cron_part.startswith("*/"):
        try:
            step = int(cron_part[2:])
            return step > 0 and current_val % step == 0
        except ValueError:
            return False

    if "-" in cron_part:
        try:
            lo, hi = cron_part.split("-", 1)
            return int(lo) <= current_val <= int(hi)
        except ValueError:
            return False

    try:
        return current_val == int(cron_part)
    except ValueError:
        return False


trigger_engine = TriggerEngine()
