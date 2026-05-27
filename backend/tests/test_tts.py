"""Tests for app.routers.tts cache-key composition.

Covers NEXT_SPRINT 1.x / 3.8: same text rendered with different backends or
voices must map to distinct cache files. Bumping CACHE_VERSION must also
invalidate every existing entry.
"""

from app.routers import tts


def test_cache_key_is_deterministic():
    a = tts._cache_key("edge", "en-US-AndrewNeural", "-5%", "hello world")
    b = tts._cache_key("edge", "en-US-AndrewNeural", "-5%", "hello world")
    assert a == b


def test_cache_key_differs_by_voice():
    """Same backend + text, different voice → distinct keys."""
    andrew = tts._cache_key("edge", "en-US-AndrewNeural", "-5%", "hello world")
    aria = tts._cache_key("edge", "en-US-AriaNeural", "-5%", "hello world")
    assert andrew != aria


def test_cache_key_differs_by_backend():
    """Same voice id + text, different backend → distinct keys (Piper/Edge collision guard)."""
    edge = tts._cache_key("edge", "andrew", "-5%", "hello world")
    say = tts._cache_key("say", "andrew", "-5%", "hello world")
    assert edge != say


def test_cache_key_differs_by_speed():
    fast = tts._cache_key("edge", "en-US-AndrewNeural", "+10%", "hello world")
    slow = tts._cache_key("edge", "en-US-AndrewNeural", "-10%", "hello world")
    assert fast != slow


def test_cache_key_differs_by_text():
    a = tts._cache_key("edge", "en-US-AndrewNeural", "-5%", "hello world")
    b = tts._cache_key("edge", "en-US-AndrewNeural", "-5%", "goodbye world")
    assert a != b


def test_cache_version_prefix_invalidates_old_entries():
    """Changing CACHE_VERSION must produce a different hash for the same tuple.

    Simulates a future v3 by recomputing the raw form. If this property holds,
    upgrading the prefix automatically orphans all stale on-disk files.
    """
    import hashlib

    backend, voice, speed, text = "edge", "en-US-AndrewNeural", "-5%", "hello"
    current = tts._cache_key(backend, voice, speed, text)
    future = hashlib.sha256(
        f"v3:{backend}:{voice}:{speed}:{text}".encode("utf-8")
    ).hexdigest()
    assert current != future


def test_cache_key_is_sha256_hex():
    """Filenames are safe (hex only) and full sha256 length."""
    key = tts._cache_key("edge", "en-US-AndrewNeural", "-5%", "hello world")
    assert len(key) == 64
    assert all(c in "0123456789abcdef" for c in key)
