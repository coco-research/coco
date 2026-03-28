"""Text-to-Speech endpoint.

Priority order:
1. Piper TTS with Jarvis voice (Paul Bettany) — local, free, instant
2. Edge TTS (Azure Neural voices) — free, high quality, many voices
3. OpenAI TTS — if OPENAI_API_KEY is set
4. macOS `say` — zero-cost fallback
"""

import os
import subprocess
import tempfile
from pathlib import Path

import structlog
from fastapi import APIRouter
from fastapi.responses import FileResponse, Response

from app.models.tts import TTSRequest

log = structlog.get_logger()

router = APIRouter(tags=["Voice"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TTS_CACHE_DIR = Path(tempfile.gettempdir()) / "coco-tts"
TTS_CACHE_DIR.mkdir(exist_ok=True)

JARVIS_MODEL = Path.home() / ".coco" / "voices" / "jarvis" / "en" / "en_GB" / "jarvis" / "high" / "jarvis-high.onnx"


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

# All available voices for the frontend
VOICE_CATALOG = [
    {"id": "jarvis", "name": "Jarvis (Paul Bettany)", "gender": "male", "engine": "piper", "accent": "British"},
    {"id": "ryan", "name": "Ryan", "gender": "male", "engine": "edge", "accent": "British"},
    {"id": "brian", "name": "Brian", "gender": "male", "engine": "edge", "accent": "American"},
    {"id": "andrew", "name": "Andrew", "gender": "male", "engine": "edge", "accent": "American"},
    {"id": "connor", "name": "Connor", "gender": "male", "engine": "edge", "accent": "Irish"},
    {"id": "sonia", "name": "Sonia", "gender": "female", "engine": "edge", "accent": "British"},
    {"id": "jenny", "name": "Jenny", "gender": "female", "engine": "edge", "accent": "American"},
    {"id": "aria", "name": "Aria", "gender": "female", "engine": "edge", "accent": "American"},
    {"id": "emma", "name": "Emma", "gender": "female", "engine": "edge", "accent": "American"},
    {"id": "libby", "name": "Libby", "gender": "female", "engine": "edge", "accent": "British"},
    {"id": "maisie", "name": "Maisie", "gender": "female", "engine": "edge", "accent": "British"},
]


# ─── TTS Engines ──────────────────────────────────────────────────────────────

def _piper_jarvis(text: str) -> Path | None:
    """Generate audio using local Piper TTS with Jarvis voice model."""
    if not JARVIS_MODEL.exists():
        return None
    try:
        import uuid as _uuid
        out_path = TTS_CACHE_DIR / f"piper_{_uuid.uuid4().hex[:8]}.wav"
        result = subprocess.run(
            ["piper", "--model", str(JARVIS_MODEL), "--output_file", str(out_path)],
            input=text.encode(),
            capture_output=True,
            timeout=15,
            cwd=str(Path.home() / ".coco"),
        )
        if result.returncode == 0 and out_path.exists() and out_path.stat().st_size > 100:
            return out_path
        log.warning("tts_piper_failed", stderr=result.stderr.decode()[:200])
    except FileNotFoundError:
        log.warning("tts_piper_not_installed")
    except Exception as e:
        log.warning("tts_piper_exception", error=str(e))
    return None


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


async def _openai_tts(text: str) -> bytes | None:
    """Generate audio using OpenAI TTS API."""
    if not OPENAI_API_KEY:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": "tts-1", "voice": "onyx", "input": text, "speed": 1.0, "response_format": "mp3"},
            )
            if resp.status_code == 200:
                return resp.content
    except Exception as e:
        log.warning("tts_openai_failed", error=str(e))
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
    # Mark Jarvis as unavailable if model not downloaded
    for v in catalog:
        v["available"] = True
        if v["id"] == "jarvis" and not JARVIS_MODEL.exists():
            v["available"] = False
    return {"voices": catalog}


@router.post("/api/tts")
async def text_to_speech(req: TTSRequest):
    """Generate speech audio. Cascades through engines based on voice selection."""

    voice_id = req.voice.lower()

    # ─── Jarvis (Piper local model) ───
    if voice_id == "jarvis":
        path = _piper_jarvis(req.text)
        if path:
            log.info("tts_served", engine="piper-jarvis")
            return FileResponse(str(path), media_type="audio/wav")
        # Fall through to Edge with Ryan as closest alternative
        voice_id = "ryan"

    # ─── Edge TTS ───
    edge_voice = EDGE_VOICES.get(voice_id, voice_id)
    # If it looks like a full Edge voice ID, use it directly
    if "Neural" in edge_voice or "Neural" in voice_id:
        edge_voice = voice_id if "Neural" in voice_id else edge_voice

    path = await _edge_tts(req.text, edge_voice, req.speed)
    if path:
        log.info("tts_served", engine="edge", voice=edge_voice)
        return FileResponse(str(path), media_type="audio/mpeg")

    # ─── OpenAI ───
    audio = await _openai_tts(req.text)
    if audio:
        log.info("tts_served", engine="openai")
        return Response(content=audio, media_type="audio/mpeg")

    # ─── macOS say ───
    path = _macos_say(req.text)
    if path:
        log.info("tts_served", engine="macos")
        return FileResponse(str(path), media_type="audio/aiff")

    return Response(content='{"error": "All TTS engines failed"}', media_type="application/json", status_code=503)
