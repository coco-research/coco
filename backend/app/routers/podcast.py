"""Podcast briefing API — generate, list, serve, delete morning briefings."""

from pathlib import Path

import structlog
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse

from app.models.podcast import (
    GeneratePodcastBody,
    PodcastListResponse,
    PodcastResponse,
)
from app.services import podcast as podcast_service

log = structlog.get_logger()

router = APIRouter(prefix="/api/podcasts", tags=["Podcasts"])


@router.get("/", response_model=PodcastListResponse)
def list_podcasts(limit: int = 10):
    """List recent podcasts, newest first."""
    items = podcast_service.list_podcasts(limit=limit)
    return PodcastListResponse(
        items=[PodcastResponse(**p) for p in items],
        count=len(items),
    )


@router.post("/", response_model=PodcastResponse)
async def generate_podcast(body: GeneratePodcastBody | None = None):
    """Generate a new morning briefing podcast."""
    voice = body.voice if body else "andrew"
    result = await podcast_service.generate_podcast(voice=voice)
    return PodcastResponse(**result)


@router.get("/{podcast_id}", response_model=PodcastResponse)
def get_podcast(podcast_id: str):
    """Get a single podcast by ID."""
    record = podcast_service.get_podcast(podcast_id)
    if not record:
        raise HTTPException(404, "Podcast not found")
    return PodcastResponse(**record)


@router.get("/{podcast_id}/audio")
def get_podcast_audio(podcast_id: str):
    """Serve the audio file for a podcast."""
    record = podcast_service.get_podcast(podcast_id)
    if not record:
        raise HTTPException(404, "Podcast not found")

    audio_path = record.get("audio_path")
    if not audio_path:
        raise HTTPException(404, "No audio available for this podcast")

    path = Path(audio_path)
    if not path.exists():
        raise HTTPException(404, "Audio file not found on disk")

    # Determine content type
    suffix = path.suffix.lower()
    media_type = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".aiff": "audio/aiff",
    }.get(suffix, "audio/wav")

    return FileResponse(str(path), media_type=media_type)


@router.get("/{podcast_id}/script")
def get_podcast_script(podcast_id: str):
    """Return the raw script text for a podcast."""
    record = podcast_service.get_podcast(podcast_id)
    if not record:
        raise HTTPException(404, "Podcast not found")

    script = record.get("script")
    if not script:
        raise HTTPException(404, "No script available for this podcast")

    return PlainTextResponse(script)


@router.delete("/{podcast_id}")
def delete_podcast(podcast_id: str):
    """Delete a podcast and its audio file."""
    deleted = podcast_service.delete_podcast(podcast_id)
    if not deleted:
        raise HTTPException(404, "Podcast not found")
    return {"status": "deleted", "id": podcast_id}
