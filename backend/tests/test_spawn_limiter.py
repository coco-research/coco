"""Tests for the claude-CLI subprocess spawn limiter (NEXT_SPRINT 1.3).

Verifies that ``spawn_limiter`` correctly caps the number of concurrent
mocked-agent tasks so we cannot OOM the host by spawning too many parallel
claude subprocesses.
"""
from __future__ import annotations

import asyncio

import pytest

from app.services import spawn_limiter


@pytest.fixture(autouse=True)
def _reset_semaphore():
    """Ensure each test starts with a fresh semaphore bound to its own loop."""
    spawn_limiter._reset_for_tests()
    yield
    spawn_limiter._reset_for_tests()


@pytest.mark.asyncio
async def test_spawn_slot_caps_concurrency_at_configured_limit():
    """More than `limit` mocked agents must NOT run concurrently."""
    limit = 5
    spawn_limiter._reset_for_tests(limit=limit)

    in_flight = 0
    max_in_flight = 0
    lock = asyncio.Lock()

    # Block all "agents" until the test releases them.
    release = asyncio.Event()

    async def fake_agent() -> None:
        nonlocal in_flight, max_in_flight
        async with spawn_limiter.spawn_slot():
            async with lock:
                in_flight += 1
                if in_flight > max_in_flight:
                    max_in_flight = in_flight
            # Hold the slot until the test releases everyone, simulating a
            # long-running claude subprocess.
            await release.wait()
            async with lock:
                in_flight -= 1

    # Spawn well over the limit — 12 vs 5.
    total = 12
    tasks = [asyncio.create_task(fake_agent()) for _ in range(total)]

    # Give the event loop a chance to schedule everything it can.
    # The semaphore should immediately admit exactly `limit` tasks.
    for _ in range(20):
        await asyncio.sleep(0)

    assert max_in_flight == limit, (
        f"Expected at most {limit} concurrent agents, saw {max_in_flight}"
    )
    assert in_flight == limit, (
        f"Expected exactly {limit} agents holding slots, saw {in_flight}"
    )

    # Let them all finish and confirm the cap was never exceeded.
    release.set()
    await asyncio.gather(*tasks)

    assert max_in_flight == limit
    assert in_flight == 0


@pytest.mark.asyncio
async def test_spawn_slot_releases_on_exception():
    """A raising agent must still release its slot so others can proceed."""
    limit = 2
    spawn_limiter._reset_for_tests(limit=limit)

    async def raising_agent() -> None:
        async with spawn_limiter.spawn_slot():
            raise RuntimeError("simulated subprocess failure")

    # Fire off `limit` failing tasks; they should all release their slots.
    for _ in range(limit):
        with pytest.raises(RuntimeError):
            await raising_agent()

    # Now the semaphore should be fully available again — a follow-up acquire
    # must complete without blocking.
    sem = spawn_limiter.get_spawn_semaphore()
    for _ in range(limit):
        await asyncio.wait_for(sem.acquire(), timeout=0.5)
    for _ in range(limit):
        sem.release()


@pytest.mark.asyncio
async def test_get_spawn_semaphore_is_singleton_per_loop():
    """Repeated calls within the same loop return the same semaphore."""
    sem_a = spawn_limiter.get_spawn_semaphore()
    sem_b = spawn_limiter.get_spawn_semaphore()
    assert sem_a is sem_b


def test_config_default_is_five(monkeypatch):
    """COCO_MAX_PARALLEL_AGENTS defaults to 5 when unset."""
    # Reload config in a controlled env to confirm the default.
    monkeypatch.delenv("COCO_MAX_PARALLEL_AGENTS", raising=False)
    import importlib

    from app import config as cfg

    importlib.reload(cfg)
    assert cfg.COCO_MAX_PARALLEL_AGENTS == 5
