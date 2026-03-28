"""Trigger engine — runs cron and file_watch triggers in background."""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import structlog

from app.db.connections import get_platform_db

log = structlog.get_logger()


class TriggerEngine:
    def __init__(self):
        self._running = False
        self._tasks: list[asyncio.Task] = []

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
        """Check cron triggers every 60 seconds."""
        while self._running:
            try:
                triggers = self._load_triggers("cron")
                now = datetime.now(timezone.utc)
                for t in triggers:
                    config = json.loads(t["config"]) if isinstance(t["config"], str) else t["config"]
                    cron_expr = config.get("cron", "")
                    if self._cron_matches(cron_expr, now):
                        await self._fire(t)
            except Exception as e:
                log.warning("cron_loop_error", error=str(e))
            await asyncio.sleep(60)

    async def _file_watch_loop(self):
        """Check file watch triggers every 5 seconds."""
        mtime_cache: dict[str, float] = {}
        while self._running:
            try:
                triggers = self._load_triggers("file_watch")
                for t in triggers:
                    config = json.loads(t["config"]) if isinstance(t["config"], str) else t["config"]
                    watch_path = config.get("path", "")
                    patterns = config.get("patterns", ["*"])
                    if not watch_path or not os.path.exists(watch_path):
                        continue

                    changed = False
                    p = Path(watch_path)
                    for pattern in patterns:
                        for f in p.glob(pattern):
                            if f.is_file():
                                mtime = f.stat().st_mtime
                                key = f"{t['id']}:{f}"
                                if key in mtime_cache and mtime_cache[key] < mtime:
                                    changed = True
                                mtime_cache[key] = mtime

                    if changed:
                        await self._fire(t)
            except Exception as e:
                log.warning("file_watch_loop_error", error=str(e))
            await asyncio.sleep(5)

    def _load_triggers(self, trigger_type: str) -> list[dict]:
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT * FROM triggers WHERE trigger_type = ? AND enabled = 1",
                (trigger_type,),
            ).fetchall()
            return [dict(r) for r in rows]

    async def _fire(self, trigger: dict):
        """Execute trigger action and log result."""
        from app.routers.triggers import _execute_trigger_action, _log_trigger_fire

        try:
            result = await _execute_trigger_action(trigger)
            with get_platform_db() as db:
                _log_trigger_fire(
                    db,
                    trigger["id"],
                    status=result.get("status", "success"),
                    result=json.dumps(result),
                )
            log.info("trigger_fired", trigger_id=trigger["id"], name=trigger["name"], status=result.get("status"))
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
        """Simple cron matching (minute, hour, day, month, weekday). Supports *, */N, and comma-separated values."""
        if not expr:
            return False
        parts = expr.strip().split()
        if len(parts) != 5:
            return False
        # weekday: cron uses 0=Sunday, Python isoweekday % 7 gives 0=Sunday
        fields = [now.minute, now.hour, now.day, now.month, now.isoweekday() % 7]
        for cron_part, current_val in zip(parts, fields):
            if cron_part == "*":
                continue
            if cron_part.startswith("*/"):
                step = int(cron_part[2:])
                if step == 0 or current_val % step != 0:
                    return False
            elif "," in cron_part:
                if current_val not in [int(x) for x in cron_part.split(",")]:
                    return False
            else:
                if current_val != int(cron_part):
                    return False
        return True


trigger_engine = TriggerEngine()
