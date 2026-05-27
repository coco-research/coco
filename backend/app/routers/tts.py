"""Text-to-Speech endpoint.

Engine priority:
1. Edge TTS (Microsoft Azure Neural voices) — free, high quality, cloud API
2. macOS `say` — zero-cost local fallback

No downloaded model weights (Kokoro, Piper removed per project rules).

Cache strategy:
    Filenames are deterministic — sha256 of (cache_version, backend, voice, speed, text).
    This makes repeated requests cheap (file-exists short-circuit) AND guarantees
    that different (backend, voice) pairs never collide on the same text.

    The ``CACHE_VERSION`` prefix bumps any time the keying scheme changes — old
    entries on disk are then ignored automatically because their hash differs.

    Writes are race-safe: each generator writes to a unique <key>.<uuid>.tmp
    sibling then atomically renames to <key>.<ext> via os.replace(). Concurrent
    writers for the same key cannot leave partial files behind.

    A per-cache-key asyncio.Lock coalesces concurrent same-text requests so we
    don't redundantly call the upstream TTS engine.
"""

import asyncio
import hashlib
import os
import subprocess
import tempfile
import uuid as _uuid
from pathlib import Path

import structlog
from fastapi import APIRouter
from fastapi.responses import FileResponse, Response

from app.models.tts import TTSRequest

log = structlog.get_logger()

router = APIRouter(tags=["Voice"])

TTS_CACHE_DIR = Path(tempfile.gettempdir()) / "coco-tts"
TTS_CACHE_DIR.mkdir(exist_ok=True)

# Bump this when the cache-key composition changes — old entries become
# unreachable (their hashes no longer match) and get garbage-collected on
# normal /tmp cleanup. v2 = includes backend+voice+speed (was: voice-naive uuid).
CACHE_VERSION = "v2"


def _cache_key(backend: str, voice: str, speed: str, text: str) -> str:
    """Deterministic cache key for a (backend, voice, speed, text) tuple.

    Including ``backend`` and ``voice`` prevents collisions where the same text
    rendered by different voices would otherwise share a file (Piper/Edge bug
    flagged in NEXT_SPRINT 3.8).
    """
    raw = f"{CACHE_VERSION}:{backend}:{voice}:{speed}:{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _atomic_tmp_path(final: Path) -> Path:
    """Unique tmp sibling for `final`; atomic rename target is `final` via os.replace()."""
    return final.with_suffix(final.suffix + f".{_uuid.uuid4().hex[:8]}.tmp")


# ─── Per-cache-key locks ──────────────────────────────────────────────────────
# Coalesces concurrent requests for the same text so we don't fire the
# upstream engine N times. Locks are reference-counted and removed when no
# waiters remain to bound memory growth.

_cache_locks: dict[str, asyncio.Lock] = {}
_cache_lock_refcount: dict[str, int] = {}
_locks_guard = asyncio.Lock()


async def _acquire_key_lock(key: str) -> asyncio.Lock:
    async with _locks_guard:
        lock = _cache_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            _cache_locks[key] = lock
        _cache_lock_refcount[key] = _cache_lock_refcount.get(key, 0) + 1
    return lock


async def _release_key_lock(key: str) -> None:
    async with _locks_guard:
        n = _cache_lock_refcount.get(key, 0) - 1
        if n <= 0:
            _cache_lock_refcount.pop(key, None)
            _cache_locks.pop(key, None)
        else:
            _cache_lock_refcount[key] = n


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
    """Generate audio using edge-tts (free Azure Neural voices).

    Cache key includes backend+voice+speed+text so different voices never
    collide on the same text. Atomic-write + per-key lock prevents partial
    files and coalesces concurrent same-text requests.
    """
    try:
        import edge_tts

        key = _cache_key("edge", voice, speed, text)
        out_path = TTS_CACHE_DIR / f"edge_{key}.mp3"
        if out_path.exists() and out_path.stat().st_size > 100:
            log.info("tts_cache_hit", engine="edge", voice=voice)
            return out_path

        lock = await _acquire_key_lock(key)
        try:
            async with lock:
                # Re-check under lock — another waiter may have produced the file.
                if out_path.exists() and out_path.stat().st_size > 100:
                    log.info("tts_cache_hit", engine="edge", voice=voice, coalesced=True)
                    return out_path
                tmp_path = _atomic_tmp_path(out_path)
                try:
                    communicate = edge_tts.Communicate(text, voice, rate=speed)
                    await communicate.save(str(tmp_path))
                    if tmp_path.exists() and tmp_path.stat().st_size > 100:
                        os.replace(str(tmp_path), str(out_path))
                        return out_path
                finally:
                    # Best-effort cleanup of orphan tmp if rename didn't happen.
                    if tmp_path.exists():
                        try:
                            tmp_path.unlink()
                        except OSError:
                            pass
        finally:
            await _release_key_lock(key)
    except Exception as e:
        log.warning("tts_edge_failed", error=str(e))
    return None


def _macos_say(text: str, voice: str = "Daniel", speed: str = "180") -> Path | None:
    """Generate audio using macOS say command. Text passed via stdin to avoid injection.

    Cache key includes backend+voice+speed+text — fixes the prior bug where
    every macOS-voice request shared a single 'say_*.aiff' bucket. Atomic-write
    via tmp + os.replace() prevents partial files on concurrent invocations.
    """
    try:
        key = _cache_key("say", voice, speed, text)
        out_path = TTS_CACHE_DIR / f"say_{key}.aiff"
        if out_path.exists() and out_path.stat().st_size > 100:
            log.info("tts_cache_hit", engine="macos", voice=voice)
            return out_path
        tmp_path = _atomic_tmp_path(out_path)
        try:
            result = subprocess.run(
                ["say", "-v", voice, "-r", speed, "-o", str(tmp_path)],
                input=text, text=True,
                capture_output=True, timeout=15,
            )
            if result.returncode == 0 and tmp_path.exists():
                os.replace(str(tmp_path), str(out_path))
                return out_path
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
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
    edge_key = _cache_key("edge", edge_voice, req.speed, req.text)
    edge_cached = TTS_CACHE_DIR / f"edge_{edge_key}.mp3"
    edge_was_hit = edge_cached.exists() and edge_cached.stat().st_size > 100
    log.info(
        "tts_prefetch",
        backend="edge",
        voice=edge_voice,
        cache_hit=edge_was_hit,
        text_hash=edge_key[:16],
    )
    path = await _edge_tts(req.text, edge_voice, req.speed)
    if path:
        log.info("tts_served", engine="edge", voice=edge_voice, cache_hit=edge_was_hit)
        return FileResponse(str(path), media_type="audio/mpeg")

    # ─── macOS say (fallback) ───
    say_key = _cache_key("say", "Daniel", "180", req.text)
    say_cached = TTS_CACHE_DIR / f"say_{say_key}.aiff"
    say_was_hit = say_cached.exists() and say_cached.stat().st_size > 100
    log.info(
        "tts_prefetch",
        backend="macos",
        voice="Daniel",
        cache_hit=say_was_hit,
        text_hash=say_key[:16],
    )
    path = _macos_say(req.text)
    if path:
        log.info("tts_served", engine="macos", cache_hit=say_was_hit)
        return FileResponse(str(path), media_type="audio/aiff")

    return Response(
        content='{"error": "All TTS engines failed"}',
        media_type="application/json",
        status_code=503,
    )
