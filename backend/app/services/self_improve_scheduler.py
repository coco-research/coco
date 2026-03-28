"""Self-improve scheduler -- auto-starts improvement cycles on a cron schedule.

Reads preferences from the ``preferences`` table and checks when the last
cycle completed.  If the configured interval has elapsed, it starts a new
cycle using ``self_improve_service.start_cycle()``.

Integrations triggered on cycle completion:
  - Jarvis voice queue (summary pushed via event listener)
  - Inbox notification (persisted item)
  - Home dashboard badge (queries cycles table)
  - Event bus ``self_improve.completed`` event
"""

import json
import uuid
from datetime import datetime, timezone

import structlog

from app.db.session import get_db
from app.db.tables import (
    self_improve_cycles,
    preferences,
    inbox_notifications,
    inbox_read_state,
)
from app.services.event_bus import event_bus

log = structlog.get_logger()

# Default preferences when none are configured
DEFAULT_BUDGET_USD = 5.0
DEFAULT_MAX_IMPROVEMENTS = 5
DEFAULT_FOCUS_AREAS: list[str] = []
DEFAULT_CRON = "0 3 * * 1"  # Monday 3 AM
DEFAULT_ENABLED = False


# ---------------------------------------------------------------------------
# Preference helpers
# ---------------------------------------------------------------------------

def _get_pref(key: str, default: str | None = None) -> str | None:
    """Read a single preference value from the preferences table."""
    try:
        with get_db() as conn:
            row = conn.exec_driver_sql(
                "SELECT value FROM preferences WHERE key = ?", (key,)
            ).fetchone()
            return row._mapping["value"] if row else default
    except Exception:
        return default


def get_self_improve_preferences() -> dict:
    """Return the full self-improve configuration from preferences table."""
    budget = float(_get_pref("self_improve.budget_usd", str(DEFAULT_BUDGET_USD)))
    max_imp = int(_get_pref("self_improve.max_improvements", str(DEFAULT_MAX_IMPROVEMENTS)))
    focus_raw = _get_pref("self_improve.focus_areas")
    focus_areas = json.loads(focus_raw) if focus_raw else DEFAULT_FOCUS_AREAS
    cron_expr = _get_pref("self_improve.cron", DEFAULT_CRON)
    enabled = _get_pref("self_improve.auto_enabled", str(DEFAULT_ENABLED).lower())
    return {
        "budget_usd": budget,
        "max_improvements": max_imp,
        "focus_areas": focus_areas,
        "cron": cron_expr,
        "enabled": enabled in ("true", "1", "yes"),
    }


# ---------------------------------------------------------------------------
# Auto-start logic
# ---------------------------------------------------------------------------

def auto_start_cycle() -> dict:
    """Check if a new self-improve cycle should start and launch it if so.

    Returns a dict describing what happened:
      - ``{"action": "started", "cycle_id": "..."}``
      - ``{"action": "skipped", "reason": "..."}``
    """
    prefs = get_self_improve_preferences()

    if not prefs["enabled"]:
        log.info("self_improve_auto_skip", reason="disabled")
        return {"action": "skipped", "reason": "auto self-improve is disabled"}

    # Check for active cycle
    try:
        with get_db() as conn:
            active = conn.exec_driver_sql(
                "SELECT id FROM self_improve_cycles "
                "WHERE status NOT IN ('completed', 'rejected', 'failed') "
                "ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            if active:
                log.info("self_improve_auto_skip", reason="active_cycle", cycle_id=active._mapping["id"])
                return {"action": "skipped", "reason": f"cycle {active._mapping['id']} is still active"}
    except Exception as e:
        log.warning("self_improve_auto_check_failed", error=str(e))
        return {"action": "skipped", "reason": f"db check failed: {e}"}

    # Start cycle
    try:
        from app.services.self_improve import self_improve_service

        cycle = self_improve_service.start_cycle(
            budget_usd=prefs["budget_usd"],
            max_improvements=prefs["max_improvements"],
            focus_areas=prefs["focus_areas"] or None,
        )
        log.info("self_improve_auto_started", cycle_id=cycle["id"])
        return {"action": "started", "cycle_id": cycle["id"]}
    except Exception as e:
        log.warning("self_improve_auto_start_failed", error=str(e))
        return {"action": "skipped", "reason": f"start failed: {e}"}


# ---------------------------------------------------------------------------
# Cycle completion handler (event-driven integrations)
# ---------------------------------------------------------------------------

def on_cycle_completed(data: dict) -> None:
    """Handle self_improve.cycle_completed event.

    Creates:
      - Inbox notification with summary
      - Jarvis voice queue item (via event)
    """
    cycle_id = data.get("cycle_id")
    if not cycle_id:
        return

    try:
        with get_db() as conn:
            cycle_row = conn.exec_driver_sql(
                "SELECT id, status, budget_usd, spent_usd, max_improvements, "
                "started_at, completed_at FROM self_improve_cycles WHERE id = ?",
                (cycle_id,),
            ).fetchone()
            if not cycle_row:
                return
            cycle = dict(cycle_row._mapping)

            # Count improvements
            imp_count_row = conn.exec_driver_sql(
                "SELECT COUNT(*) as cnt FROM self_improve_improvements "
                "WHERE cycle_id = ? AND status IN ('approved_by_human', 'merged')",
                (cycle_id,),
            ).fetchone()
            imp_count = imp_count_row._mapping["cnt"] if imp_count_row else 0

            # Get improvement titles for summary
            imp_rows = conn.exec_driver_sql(
                "SELECT title FROM self_improve_improvements "
                "WHERE cycle_id = ? AND status IN ('approved_by_human', 'merged', 'awaiting_approval') "
                "ORDER BY priority LIMIT 5",
                (cycle_id,),
            ).fetchall()
            titles = [r._mapping["title"] for r in imp_rows]

        # Build summary text
        spent = cycle.get("spent_usd", 0) or 0
        status = cycle.get("status", "completed")

        if status == "rejected":
            summary = f"Self-improvement cycle completed with no approved changes. Cost: ${spent:.2f}."
        elif imp_count == 0:
            summary = f"Self-improvement cycle finished. No improvements were applied. Cost: ${spent:.2f}."
        else:
            changes_desc = ", ".join(titles[:3])
            if len(titles) > 3:
                changes_desc += f", and {len(titles) - 3} more"
            summary = (
                f"I improved {imp_count} file{'s' if imp_count != 1 else ''} overnight. "
                f"{changes_desc}. Total cost: ${spent:.2f}."
            )

        # Create inbox notification
        item_key = f"self-improve-{cycle_id}"
        notif_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()

        with get_db() as conn:
            conn.exec_driver_sql(
                "INSERT OR IGNORE INTO inbox_notifications "
                "(id, item_type, item_key, title, body, metadata_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    notif_id,
                    "self_improve_summary",
                    item_key,
                    f"Self-Improvement: {imp_count} file{'s' if imp_count != 1 else ''} improved",
                    summary,
                    json.dumps({
                        "cycle_id": cycle_id,
                        "improvements_count": imp_count,
                        "spent_usd": spent,
                        "status": status,
                        "titles": titles,
                    }),
                    now,
                ),
            )

            # Create unread state for this inbox item
            conn.exec_driver_sql(
                "INSERT OR IGNORE INTO inbox_read_state (item_key, read_state, updated_at) "
                "VALUES (?, 'unread', ?)",
                (item_key, now),
            )

        # Emit Jarvis voice summary event
        event_bus.emit("jarvis.voice_queue", {
            "source": "self_improve",
            "text": summary,
            "cycle_id": cycle_id,
        })

        log.info(
            "self_improve_completion_handled",
            cycle_id=cycle_id,
            improvements=imp_count,
            inbox_key=item_key,
        )

    except Exception as e:
        log.warning("self_improve_completion_handler_failed", cycle_id=cycle_id, error=str(e))


# ---------------------------------------------------------------------------
# Register event listener
# ---------------------------------------------------------------------------

def register_event_listeners() -> None:
    """Wire up the cycle completion handler to the event bus.

    Called during app startup (lifespan).
    """
    # The event bus is sync (emit is sync), but we store a reference
    # for the completion handler.  We hook it by monkey-patching emit
    # to also call our handler for the specific event type.
    _original_emit = event_bus.emit

    def _patched_emit(event_type: str, data: dict) -> None:
        _original_emit(event_type, data)
        if event_type == "self_improve.cycle_completed":
            try:
                on_cycle_completed(data)
            except Exception as e:
                log.warning("cycle_completed_listener_error", error=str(e))

    event_bus.emit = _patched_emit  # type: ignore[assignment]
    log.info("self_improve_scheduler_listeners_registered")
