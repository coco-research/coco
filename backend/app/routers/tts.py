"""Text-to-Speech endpoint.

Engine priority:
1. Edge TTS (Microsoft Azure Neural voices) — free, high quality, cloud API
2. macOS `say` — zero-cost local fallback

No downloaded model weights (Kokoro, Piper removed per project rules).
"""

import subprocess
import tempfile
from pathlib import Path

import structlog
from fastapi import APIRouter
from fastapi.responses import FileResponse, Response

from app.models.tts import TTSRequest

log = structlog.get_logger()

router = APIRouter(tags=["Voice"])

TTS_CACHE_DIR = Path(tempfile.gettempdir()) / "coco-tts"
TTS_CACHE_DIR.mkdir(exist_ok=True)


# ─── Voice Registry ───────────────────────────────────────────────────────────

EDGE_VOICES = {
    # Male
    "ryan": "en-GB-RyanNeural",
    "brian": "en-US-BrianNeural",
    "andrew": "en-US-AndrewNeural",
    "connor": "en-IE-ConnorNeural",
    "liam": "en-CA-LiamNeural",
    "william": "en-AU-WilliamMultilingualNeural",
    # Female
    "sonia": "en-GB-SoniaNeural",
    "jenny": "en-US-JennyNeural",
    "aria": "en-US-AriaNeural",
    "emma": "en-US-EmmaNeural",
    "libby": "en-GB-LibbyNeural",
    "maisie": "en-GB-MaisieNeural",
}

VOICE_CATALOG = [
    {"id": "andrew", "name": "Andrew", "gender": "male", "engine": "edge", "accent": "American"},
    {"id": "brian", "name": "Brian", "gender": "male", "engine": "edge", "accent": "American"},
    {"id": "ryan", "name": "Ryan", "gender": "male", "engine": "edge", "accent": "British"},
    {"id": "connor", "name": "Connor", "gender": "male", "engine": "edge", "accent": "Irish"},
    {"id": "liam", "name": "Liam", "gender": "male", "engine": "edge", "accent": "Canadian"},
    {"id": "william", "name": "William", "gender": "male", "engine": "edge", "accent": "Australian"},
    {"id": "aria", "name": "Aria", "gender": "female", "engine": "edge", "accent": "American"},
    {"id": "jenny", "name": "Jenny", "gender": "female", "engine": "edge", "accent": "American"},
    {"id": "emma", "name": "Emma", "gender": "female", "engine": "edge", "accent": "American"},
    {"id": "sonia", "name": "Sonia", "gender": "female", "engine": "edge", "accent": "British"},
    {"id": "libby", "name": "Libby", "gender": "female", "engine": "edge", "accent": "British"},
    {"id": "maisie", "name": "Maisie", "gender": "female", "engine": "edge", "accent": "British"},
]


# ─── TTS Engines ──────────────────────────────────────────────────────────────

async def _edge_tts(text: str, voice: str, speed: str) -> Path | None:
    """Generate audio using edge-tts (free Azure Neural voices)."""
    try:
        import edge_tts
        import uuid as _uuid

        out_path = TTS_CACHE_DIR / f"edge_{_uuid.uuid4().hex[:8]}.mp3"
        communicate = edge_tts.Communicate(text, voice, rate=speed)
        await communicate.save(str(out_path))
        if out_path.exists() and out_path.stat().st_size > 100:
            return out_path
    except Exception as e:
        log.warning("tts_edge_failed", error=str(e))
    return None


def _macos_say(text: str) -> Path | None:
    """Generate audio using macOS say command. Text passed via stdin to avoid injection."""
    try:
        import uuid as _uuid
        out_path = TTS_CACHE_DIR / f"say_{_uuid.uuid4().hex[:8]}.aiff"
        result = subprocess.run(
            ["say", "-v", "Daniel", "-r", "180", "-o", str(out_path)],
            input=text, text=True,
            capture_output=True, timeout=15,
        )
        if result.returncode == 0 and out_path.exists():
            return out_path
    except Exception as e:
        log.warning("tts_say_failed", error=str(e))
    return None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/api/tts/voices")
def list_voices():
    """List all available TTS voices."""
    catalog = list(VOICE_CATALOG)
    for v in catalog:
        v["available"] = True
    return {"voices": catalog}


@router.post("/api/tts")
async def text_to_speech(req: TTSRequest):
    """Generate speech audio. Edge-TTS primary, macOS say fallback."""

    voice_id = req.voice.lower()

    # Resolve to Edge voice ID
    edge_voice = EDGE_VOICES.get(voice_id)
    if not edge_voice:
        # If the voice_id is already a full Neural voice ID, use it
        if "Neural" in voice_id:
            edge_voice = voice_id
        else:
            # Default to Andrew
            edge_voice = EDGE_VOICES["andrew"]

    # ─── Edge TTS (primary) ───
    path = await _edge_tts(req.text, edge_voice, req.speed)
    if path:
        log.info("tts_served", engine="edge", voice=edge_voice)
        return FileResponse(str(path), media_type="audio/mpeg")

    # ─── macOS say (fallback) ───
    path = _macos_say(req.text)
    if path:
        log.info("tts_served", engine="macos")
        return FileResponse(str(path), media_type="audio/aiff")

    return Response(
        content='{"error": "All TTS engines failed"}',
        media_type="application/json",
        status_code=503,
    )
