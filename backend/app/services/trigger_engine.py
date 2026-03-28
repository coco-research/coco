"""Trigger engine — runs cron and file_watch triggers in background.

Cron triggers fire based on standard 5-field cron expressions.
File-watch triggers poll directories for mtime changes.
Both types log every fire to the trigger_log table.
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

import structlog

from app.db.connections import get_platform_db

log = structlog.get_logger()


class TriggerEngine:
    def __init__(self):
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._file_mtime_cache: dict[str, float] = {}
        # Track which cron triggers already fired in the current minute
        # Key: trigger_id, Value: minute timestamp string "YYYY-MM-DDTHH:MM"
        self._cron_fired_at: dict[str, str] = {}

    async def start(self):
        """Start the trigger engine. Call from FastAPI lifespan."""
        self._running = True
        log.info("trigger_engine_starting")
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
        """Check cron triggers every 30 seconds.

        Uses minute-level dedup to avoid double-firing within the same minute.
        """
        while self._running:
            try:
                triggers = self._load_triggers("cron")
                now = datetime.now(timezone.utc)
                minute_key = now.strftime("%Y-%m-%dT%H:%M")

                for t in triggers:
                    trigger_id = t["id"]
                    config = json.loads(t["config"]) if isinstance(t["config"], str) else t["config"]
                    # Accept both "expression" (frontend) and "cron" (legacy) keys
                    cron_expr = config.get("expression") or config.get("cron", "")

                    if not cron_expr:
                        continue

                    # Skip if already fired this minute
                    if self._cron_fired_at.get(trigger_id) == minute_key:
                        continue

                    if self._cron_matches(cron_expr, now):
                        log.info("cron_trigger_matched", trigger_id=trigger_id, name=t["name"], cron=cron_expr)
                        self._cron_fired_at[trigger_id] = minute_key
                        await self._fire(t)

                # Prune old entries from dedup cache (keep only current minute)
                self._cron_fired_at = {
                    k: v for k, v in self._cron_fired_at.items() if v == minute_key
                }
            except Exception as e:
                log.warning("cron_loop_error", error=str(e))
            await asyncio.sleep(30)

    async def _file_watch_loop(self):
        """Check file watch triggers every 30 seconds."""
        while self._running:
            try:
                triggers = self._load_triggers("file_watch")
                for t in triggers:
                    config = json.loads(t["config"]) if isinstance(t["config"], str) else t["config"]
                    watch_path = config.get("path", "")
                    patterns = config.get("patterns", ["*"])
                    if not watch_path or not os.path.exists(watch_path):
                        continue

                    changed_files: list[str] = []
                    p = Path(watch_path)

                    # Check if it's a file or directory
                    if p.is_file():
                        mtime = p.stat().st_mtime
                        key = f"{t['id']}:{p}"
                        if key in self._file_mtime_cache and self._file_mtime_cache[key] < mtime:
                            changed_files.append(str(p))
                        self._file_mtime_cache[key] = mtime
                    else:
                        for pattern in patterns:
                            for f in p.glob(pattern):
                                if f.is_file():
                                    mtime = f.stat().st_mtime
                                    key = f"{t['id']}:{f}"
                                    if key in self._file_mtime_cache and self._file_mtime_cache[key] < mtime:
                                        changed_files.append(str(f))
                                    self._file_mtime_cache[key] = mtime

                    if changed_files:
                        log.info("file_watch_triggered", trigger_id=t["id"], changed=changed_files[:5])
                        await self._fire(t, context={"changed_files": changed_files})
            except Exception as e:
                log.warning("file_watch_loop_error", error=str(e))
            await asyncio.sleep(30)

    def _load_triggers(self, trigger_type: str) -> list[dict]:
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT * FROM triggers WHERE trigger_type = ? AND enabled = 1",
                (trigger_type,),
            ).fetchall()
            return [dict(r) for r in rows]

    async def _fire(self, trigger: dict, context: dict | None = None):
        """Execute trigger action and log result."""
        from app.routers.triggers import _execute_trigger_action, _log_trigger_fire

        try:
            result = await _execute_trigger_action(trigger, context=context)
            status = result.get("status", "success")
            with get_platform_db() as db:
                _log_trigger_fire(
                    db,
                    trigger["id"],
                    status=status,
                    result=json.dumps(result),
                    error=result.get("error"),
                )
            log.info("trigger_fired", trigger_id=trigger["id"], name=trigger["name"], status=status)
        except Exception as e:
            with get_platform_db() as db:
                _log_trigger_fire(
                    db,
                    trigger["id"],
                    status="failed",
                    error=str(e),
                )
            log.warning("trigger_fire_failed", trigger_id=trigger["id"], error=str(e))

    @staticmethod
    def _cron_matches(expr: str, now: datetime) -> bool:
        """Simple cron matching (minute, hour, day, month, weekday).

        Supports: *, */N, N, N-M ranges, and comma-separated values.
        Weekday: 0=Sunday (cron convention). Python isoweekday() % 7 maps correctly.
        """
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
    """Check if a single cron field matches the current value.

    Supports: *, */N, N, N-M, and comma-separated combinations.
    """
    if cron_part == "*":
        return True

    # Comma-separated: any sub-part matching is sufficient
    if "," in cron_part:
        return any(_cron_field_matches(sub.strip(), current_val) for sub in cron_part.split(","))

    # Step: */N
    if cron_part.startswith("*/"):
        try:
            step = int(cron_part[2:])
            return step > 0 and current_val % step == 0
        except ValueError:
            return False

    # Range: N-M
    if "-" in cron_part:
        try:
            lo, hi = cron_part.split("-", 1)
            return int(lo) <= current_val <= int(hi)
        except ValueError:
            return False

    # Exact value
    try:
        return current_val == int(cron_part)
    except ValueError:
        return False


trigger_engine = TriggerEngine()
