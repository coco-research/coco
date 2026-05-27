"""Podcast briefing service — aggregates data, generates script via Haiku.

Script-only for now (no TTS). The PodcastPlayer renders the script as text.
"""

import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog
from sqlalchemy import func, select, text

from app.db.session import get_db
from app.db.tables import (
    agents,
    cost_ledger,
    hub_todos,
    podcasts,
    self_improve_cycles,
)
from app.services.event_bus import event_bus

log = structlog.get_logger()

PODCASTS_DIR = Path.home() / ".coco" / "podcasts"
PODCASTS_DIR.mkdir(parents=True, exist_ok=True)

# Hard cap
MAX_WORDS = 450


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _greeting_word() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    return "evening"


# ---------------------------------------------------------------------------
# 1. Aggregate briefing data
# ---------------------------------------------------------------------------


def aggregate_briefing_data() -> dict:
    """Query hub mirror tables for overnight/recent data."""
    data: dict = {
        "completed_agents": 0,
        "new_todos": 0,
        "completed_todos": 0,
        "cost_last_24h": 0.0,
        "todos_due_today": [],
        "recent_self_improve": 0,
        "date": datetime.now().strftime("%A, %B %d"),
    }

    with get_db() as conn:
        # Completed agents (last 24h)
        try:
            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(agents)
                .where(agents.c.status == "completed")
                .where(agents.c.stopped_at >= text("datetime('now', '-24 hours')"))
            ).fetchone()
            data["completed_agents"] = row.cnt if row else 0
        except Exception:
            log.warning("podcast_agg_failed", section="completed_agents", exc_info=True)

        # New todos (last 24h)
        try:
            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(hub_todos)
                .where(hub_todos.c.created_at >= text("datetime('now', '-24 hours')"))
            ).fetchone()
            data["new_todos"] = row.cnt if row else 0
        except Exception:
            log.warning("podcast_agg_failed", section="new_todos", exc_info=True)

        # Completed todos (last 24h)
        try:
            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(hub_todos)
                .where(hub_todos.c.status == "done")
                .where(hub_todos.c.completed_at >= text("datetime('now', '-24 hours')"))
            ).fetchone()
            data["completed_todos"] = row.cnt if row else 0
        except Exception:
            log.warning("podcast_agg_failed", section="completed_todos", exc_info=True)

        # Cost last 24h
        try:
            row = conn.execute(
                select(func.coalesce(func.sum(cost_ledger.c.cost_usd), 0.0).label("total"))
                .where(cost_ledger.c.created_at >= text("datetime('now', '-24 hours')"))
            ).fetchone()
            data["cost_last_24h"] = round(row.total, 4) if row else 0.0
        except Exception:
            log.warning("podcast_agg_failed", section="cost_last_24h", exc_info=True)

        # Todos due today
        try:
            rows = conn.execute(
                select(hub_todos.c.id, hub_todos.c.title, hub_todos.c.priority)
                .where(hub_todos.c.status == "open")
                .where(hub_todos.c.due_date == text("date('now', 'localtime')"))
                .order_by(hub_todos.c.priority.desc())
                .limit(10)
            ).fetchall()
            data["todos_due_today"] = [dict(r._mapping) for r in rows]
        except Exception:
            log.warning("podcast_agg_failed", section="todos_due_today", exc_info=True)

        # Recent self-improve cycles (last 24h)
        try:
            row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(self_improve_cycles)
                .where(self_improve_cycles.c.status == "completed")
                .where(self_improve_cycles.c.completed_at >= text("datetime('now', '-24 hours')"))
            ).fetchone()
            data["recent_self_improve"] = row.cnt if row else 0
        except Exception:
            log.warning("podcast_agg_failed", section="recent_self_improve", exc_info=True)

        # Overdue todos (due before today, still open)
        try:
            rows = conn.execute(
                select(hub_todos.c.id, hub_todos.c.title, hub_todos.c.priority, hub_todos.c.due_date, hub_todos.c.project_id)
                .where(hub_todos.c.status == "open")
                .where(hub_todos.c.due_date < text("date('now', 'localtime')"))
                .where(hub_todos.c.due_date.isnot(None))
                .order_by(hub_todos.c.priority.desc())
                .limit(10)
            ).fetchall()
            data["overdue_todos"] = [dict(r._mapping) for r in rows]
        except Exception:
            log.warning("podcast_agg_failed", section="overdue_todos", exc_info=True)

    return data


# ---------------------------------------------------------------------------
# 2. Generate script (Haiku-powered, conversational)
# ---------------------------------------------------------------------------

# Section marker for silence insertion
SECTION_BREAK = "\n\n"

BRIEFING_SYSTEM_PROMPT = """You are CoCo, a PM assistant generating a morning audio briefing script for Rijul.

Rules:
- Write a conversational 2-3 minute briefing (300-450 words max)
- Start with a natural greeting using the time of day and date
- Prioritize what MATTERS: overdue items first, then what's due today, then highlights
- Be specific with names, projects, and numbers — don't be vague
- Skip noise: don't mention zero-count sections or unimportant details
- End with a clear "top 3 priorities" and a brief sign-off
- Write for SPOKEN delivery: short sentences, no bullet points, no markdown
- Use section breaks (double newline) between topics for natural pauses
- If there's nothing significant, say so briefly — don't pad with filler"""


def generate_script(data: dict) -> str:
    """Generate a conversational briefing script using Claude Haiku via agent_sdk_client.

    Uses the Platform's existing LLM layer (rate limiting, cost tracking, fallback).
    Falls back to a simple template if the API call fails.
    Target: 300-450 words, 2-3 minutes at ~150 wpm.
    """
    try:
        from app.services.agent_sdk_client import create_message  # noqa: lazy import (optional dep)

        prompt_data = _format_data_for_prompt(data)

        result = create_message(
            model="haiku",
            system=BRIEFING_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_data}],
            max_tokens=800,
            purpose="briefing",  # routes to local LLM (Gemma4-26B)
        )

        script = result["content"].strip()

        # Hard cap at MAX_WORDS
        words = script.split()
        if len(words) > MAX_WORDS:
            words = words[:MAX_WORDS]
            script = " ".join(words) + "... and that's the highlights."

        log.info(
            "podcast_script_generated",
            engine="haiku",
            words=len(script.split()),
            cost_usd=result.get("cost_usd", 0),
        )
        return script

    except Exception as e:
        log.warning("haiku_script_failed_using_fallback", error=str(e))
        return _fallback_template_script(data)


def _format_data_for_prompt(data: dict) -> str:
    """Format aggregated data as a structured prompt for Haiku."""
    lines = [
        f"Date: {data.get('date', _today_str())}",
        f"Time of day: {_greeting_word()}",
        f"Completed agents (last 24h): {data.get('completed_agents', 0)}",
        f"New todos (last 24h): {data.get('new_todos', 0)}",
        f"Completed todos (last 24h): {data.get('completed_todos', 0)}",
        f"API cost (last 24h): ${data.get('cost_last_24h', 0.0):.2f}",
        f"Self-improve cycles (last 24h): {data.get('recent_self_improve', 0)}",
    ]

    todos = data.get("todos_due_today", [])
    if todos:
        lines.append(f"\nTodos due today ({len(todos)}):")
        for t in todos[:10]:
            priority = t.get("priority", "medium")
            lines.append(f"  [{priority.upper()}] {t.get('title', 'Untitled')}")
    else:
        lines.append("\nNo todos due today.")

    # Add overdue context if available
    overdue = data.get("overdue_todos", [])
    if overdue:
        lines.append(f"\nOverdue todos ({len(overdue)}):")
        for t in overdue[:10]:
            lines.append(f"  [{t.get('priority', 'medium').upper()}] {t.get('title', 'Untitled')} (due: {t.get('due_date', '?')})")

    lines.append("\nGenerate the morning briefing script now.")
    return "\n".join(lines)


def _fallback_template_script(data: dict) -> str:
    """Simple template fallback if Haiku is unavailable."""
    greeting = _greeting_word()
    date_str = data.get("date", _today_str())
    parts = [f"Good {greeting}. It's {date_str}. Here's your CoCo briefing."]

    completed = data.get("completed_agents", 0)
    new_todos = data.get("new_todos", 0)
    cost = data.get("cost_last_24h", 0.0)

    highlights = []
    if completed > 0:
        highlights.append(f"{completed} agents finished overnight.")
    if new_todos > 0:
        highlights.append(f"{new_todos} new todos came in.")
    if cost > 0.01:
        highlights.append(f"API spend was ${cost:.2f}.")

    if highlights:
        parts.append(" ".join(highlights))
    else:
        parts.append("Quiet stretch. No major activity.")

    todos = data.get("todos_due_today", [])
    if todos:
        parts.append(f"{len(todos)} items due today.")
        for t in todos[:3]:
            parts.append(f"{t.get('title', 'Untitled')}.")
    else:
        parts.append("Nothing due today. Clear runway.")

    parts.append("That's your briefing. Have a productive day.")
    return SECTION_BREAK.join(parts)


# ---------------------------------------------------------------------------
# 3. Synthesize audio (Edge-TTS — Microsoft cloud, no local models)
# ---------------------------------------------------------------------------

# Edge-TTS voice options (natural-sounding, free)
EDGE_VOICES = {
    "andrew": "en-US-AndrewNeural",       # Male, warm
    "aria": "en-US-AriaNeural",            # Female, conversational
    "guy": "en-US-GuyNeural",              # Male, professional
    "jenny": "en-US-JennyNeural",          # Female, clear
    "ryan": "en-GB-RyanNeural",            # Male, British
    "sonia": "en-GB-SoniaNeural",          # Female, British
}

DEFAULT_VOICE = "andrew"


async def synthesize_audio(
    script: str,
    voice: str = DEFAULT_VOICE,
    podcast_id: str | None = None,
) -> tuple[str, float] | None:
    """Synthesize audio from script using Edge-TTS (Microsoft cloud).

    Returns (file_path, duration_seconds) or None if synthesis fails.
    """
    import edge_tts  # noqa: lazy import (optional dep)

    if podcast_id is None:
        podcast_id = uuid.uuid4().hex[:12]

    out_path = PODCASTS_DIR / f"{podcast_id}.mp3"

    # Resolve voice name to Edge-TTS voice ID
    voice_id = EDGE_VOICES.get(voice, EDGE_VOICES[DEFAULT_VOICE])

    try:
        communicate = edge_tts.Communicate(script, voice_id, rate="-5%")
        await communicate.save(str(out_path))

        if not out_path.exists() or out_path.stat().st_size < 100:
            log.warning("edge_tts_empty_output", voice=voice_id)
            return None

        # Estimate duration from word count (~150 wpm)
        word_count = len(script.split())
        duration = round(word_count / 150 * 60, 1)

        log.info(
            "podcast_audio_synthesized",
            engine="edge-tts",
            voice=voice_id,
            path=str(out_path),
            duration=duration,
            word_count=word_count,
        )

        return str(out_path), duration

    except Exception as e:
        log.error("edge_tts_failed", error=str(e), exc_info=True)
        return None


# ---------------------------------------------------------------------------
# 4. Orchestrator
# ---------------------------------------------------------------------------


async def generate_podcast(voice: str = DEFAULT_VOICE) -> dict:
    """Full pipeline: aggregate -> Haiku script -> Edge-TTS audio -> persist -> notify."""
    podcast_id = uuid.uuid4().hex[:12]
    now = _iso_now()
    title = f"Morning Brief — {datetime.now().strftime('%b %d, %Y')}"

    # Create initial record
    with get_db() as conn:
        conn.execute(
            podcasts.insert().values(
                id=podcast_id,
                title=title,
                status="generating",
                voice=voice,
                created_at=now,
            )
        )

    try:
        # 1. Aggregate data
        data = aggregate_briefing_data()

        # 2. Generate script (Haiku with template fallback)
        script = generate_script(data)

        # 3. Synthesize audio (Edge-TTS)
        result = await synthesize_audio(script, voice=voice, podcast_id=podcast_id)

        audio_path = result[0] if result else None
        duration = result[1] if result else None
        status = "ready"

        # 4. Update DB record
        with get_db() as conn:
            conn.execute(
                podcasts.update()
                .where(podcasts.c.id == podcast_id)
                .values(
                    script=script,
                    audio_path=audio_path,
                    duration=duration,
                    status=status,
                )
            )

        record = {
            "id": podcast_id,
            "title": title,
            "script": script,
            "audio_path": audio_path,
            "duration": duration,
            "voice": voice,
            "status": status,
            "created_at": now,
        }

        # 5. Emit event
        event_bus.emit("podcast.ready", {"podcast_id": podcast_id, "title": title})

        # 6. macOS notification
        _send_notification(title)

        return record

    except Exception as e:
        log.error("podcast_generation_failed", error=str(e), exc_info=True)
        with get_db() as conn:
            conn.execute(
                podcasts.update()
                .where(podcasts.c.id == podcast_id)
                .values(status="failed")
            )
        return {
            "id": podcast_id,
            "title": title,
            "script": None,
            "audio_path": None,
            "duration": None,
            "voice": voice,
            "status": "failed",
            "created_at": now,
        }


# ---------------------------------------------------------------------------
# 5. Queries
# ---------------------------------------------------------------------------


def list_podcasts(limit: int = 10) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            select(podcasts).order_by(podcasts.c.created_at.desc()).limit(limit)
        ).fetchall()
        return [dict(r._mapping) for r in rows]


def get_podcast(podcast_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            select(podcasts).where(podcasts.c.id == podcast_id)
        ).fetchone()
        return dict(row._mapping) if row else None


def delete_podcast(podcast_id: str) -> bool:
    """Delete a podcast record and its audio file."""
    record = get_podcast(podcast_id)
    if not record:
        return False

    # Delete audio file
    if record.get("audio_path"):
        try:
            Path(record["audio_path"]).unlink(missing_ok=True)
        except Exception:
            pass

    with get_db() as conn:
        conn.execute(podcasts.delete().where(podcasts.c.id == podcast_id))

    return True


# ---------------------------------------------------------------------------
# 6. macOS notification
# ---------------------------------------------------------------------------


def _send_notification(title: str) -> None:
    """Send macOS desktop notification."""
    try:
        subprocess.Popen(
            [
                "osascript",
                "-e",
                f'display notification "Your morning brief is ready" with title "CoCo" subtitle "{title}"',
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass  # Best effort
