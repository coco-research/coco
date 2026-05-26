"""Concurrency limiter for claude-CLI subprocess spawns.

Caps the number of simultaneous `claude -p` subprocesses to prevent OOM from
too many parallel agents (NEXT_SPRINT 1.3). The cap is configured via
`COCO_MAX_PARALLEL_AGENTS` (default 5).

Use ``async with spawn_slot():`` immediately around any
``asyncio.create_subprocess_exec``/``create_subprocess_shell`` call that
launches the claude CLI.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from app.config import COCO_MAX_PARALLEL_AGENTS

# Module-level semaphore — created lazily on first use so it binds to the
# currently-running event loop. Bare ``asyncio.Semaphore(5)`` at import time
# can pin the semaphore to a loop that no longer exists (e.g. across tests).
_SPAWN_SEM: asyncio.Semaphore | None = None
_SPAWN_SEM_LIMIT: int = COCO_MAX_PARALLEL_AGENTS


def get_spawn_semaphore() -> asyncio.Semaphore:
    """Return the singleton async semaphore guarding subprocess spawns."""
    global _SPAWN_SEM
    if _SPAWN_SEM is None:
        _SPAWN_SEM = asyncio.Semaphore(_SPAWN_SEM_LIMIT)
    return _SPAWN_SEM


@asynccontextmanager
async def spawn_slot():
    """Acquire a slot from the spawn semaphore for the duration of the block.

    Callers should wrap the actual ``await create_subprocess_*`` call inside
    this context so that at most ``COCO_MAX_PARALLEL_AGENTS`` spawns are in
    flight at once.
    """
    sem = get_spawn_semaphore()
    async with sem:
        yield


def _reset_for_tests(limit: int | None = None) -> None:
    """Test-only: clear the cached semaphore so the next call rebuilds it.

    If ``limit`` is provided, the next semaphore is built with that limit
    instead of the value loaded from config at import time.
    """
    global _SPAWN_SEM, _SPAWN_SEM_LIMIT
    _SPAWN_SEM = None
    if limit is not None:
        _SPAWN_SEM_LIMIT = limit
