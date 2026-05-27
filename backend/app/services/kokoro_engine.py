"""Kokoro TTS engine — 82M-param local model, near-ElevenLabs quality.

Lazy-loading singleton: model downloads (~330MB) on first generate() call.
"""

import hashlib
import threading
from pathlib import Path
from typing import Any

import structlog

log = structlog.get_logger()


class KokoroEngine:
    """Lazy-loading wrapper around the Kokoro TTS model."""

    VOICES = [
        {"id": "af_heart", "name": "Heart", "gender": "female", "accent": "American", "description": "Warm, friendly"},
        {"id": "am_adam", "name": "Adam", "gender": "male", "accent": "American", "description": "Neutral, clear"},
        {"id": "bf_emma", "name": "Emma (British)", "gender": "female", "accent": "British", "description": "Refined, articulate"},
        {"id": "bm_george", "name": "George", "gender": "male", "accent": "British", "description": "Deep, authoritative"},
    ]

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = cache_dir
        self._pipeline: Any | None = None
        self._lock = threading.Lock()

    # ── availability ──────────────────────────────────────────────────────

    @staticmethod
    def is_available() -> bool:
        """Check if the kokoro package is importable."""
        try:
            import kokoro  # noqa: F401, lazy import (optional dep)
            return True
        except ImportError:
            return False

    # ── lazy model loading ────────────────────────────────────────────────

    def _ensure_loaded(self) -> bool:
        """Lazy-load the Kokoro pipeline on first call. Thread-safe."""
        if self._pipeline is not None:
            return True
        with self._lock:
            # Double-check after acquiring lock
            if self._pipeline is not None:
                return True
            try:
                from kokoro import KPipeline  # noqa: lazy import (optional dep)

                log.info("kokoro_loading", msg="Loading Kokoro model (first call, may download ~330MB)...")
                self._pipeline = KPipeline(lang_code="a")  # 'a' = American English default
                log.info("kokoro_loaded")
                return True
            except Exception as e:
                log.warning("kokoro_load_failed", error=str(e))
                return False

    # ── generation ────────────────────────────────────────────────────────

    def generate(self, text: str, voice: str = "af_heart", speed: float = 1.0) -> Path | None:
        """Generate a WAV file from text. Returns file path or None on failure.

        Uses content-hash filenames so identical requests are cached.
        """
        if not self.is_available():
            return None
        if not self._ensure_loaded():
            return None

        try:
            import soundfile as sf  # noqa: lazy import (optional dep)

            # Determine lang_code from voice prefix
            lang_code = voice[0] if voice and voice[0] in ("a", "b") else "a"

            # Rebuild pipeline with correct lang_code if needed
            if self._pipeline is not None:
                current_lang = getattr(self._pipeline, "lang_code", "a")
                if current_lang != lang_code:
                    from kokoro import KPipeline  # noqa: F811, lazy import (optional dep)
                    self._pipeline = KPipeline(lang_code=lang_code)

            # Content-addressed cache filename
            key = f"{text}|{voice}|{speed}"
            digest = hashlib.sha256(key.encode()).hexdigest()[:16]
            out_path = self._cache_dir / f"kokoro_{digest}.wav"

            if out_path.exists() and out_path.stat().st_size > 100:
                return out_path

            # Generate audio samples
            samples_list = []
            for _graphemes, _phonemes, audio_chunk in self._pipeline(
                text, voice=voice, speed=speed
            ):
                if audio_chunk is not None:
                    samples_list.append(audio_chunk)

            if not samples_list:
                log.warning("kokoro_no_audio", voice=voice)
                return None

            # Concatenate all chunks
            import numpy as np  # noqa: lazy import (optional dep)
            samples = np.concatenate(samples_list)

            # Write WAV at 24kHz (Kokoro's native sample rate)
            sf.write(str(out_path), samples, 24000)

            if out_path.exists() and out_path.stat().st_size > 100:
                log.info("kokoro_generated", voice=voice, size=out_path.stat().st_size)
                return out_path

        except Exception as e:
            log.warning("kokoro_generate_failed", error=str(e))

        return None

    # ── voice listing ─────────────────────────────────────────────────────

    def get_voices(self) -> list[dict]:
        """Return available Kokoro voices with metadata."""
        return list(self.VOICES)
