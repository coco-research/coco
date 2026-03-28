"""Speech-to-Text endpoints — Deepgram integration."""
import os
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = structlog.get_logger()
router = APIRouter(tags=["Voice"])

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")

class STTConfig(BaseModel):
    model: str = "nova-3"
    language: str = "en"
    smart_format: bool = True
    interim_results: bool = True
    utterance_end_ms: int = 1500
    vad_events: bool = True

@router.get("/api/stt/config")
def get_stt_config():
    """Return STT configuration and availability status."""
    available = bool(DEEPGRAM_API_KEY)
    return {
        "available": available,
        "provider": "deepgram" if available else "web_speech_api",
        "config": STTConfig().model_dump() if available else None,
        "websocket_url": "wss://api.deepgram.com/v1/listen" if available else None,
    }

@router.post("/api/stt/token")
def create_stt_token():
    """Create a temporary Deepgram API key for client-side WebSocket connection.

    In production, this would create a scoped temporary key via Deepgram's API.
    For now, returns the API key directly (acceptable for localhost single-user).
    """
    if not DEEPGRAM_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Deepgram API key not configured. Set DEEPGRAM_API_KEY environment variable. Falling back to Web Speech API.",
        )

    return {
        "token": DEEPGRAM_API_KEY,
        "expires_in": 600,  # 10 minutes
        "websocket_url": "wss://api.deepgram.com/v1/listen",
        "config": STTConfig().model_dump(),
    }
