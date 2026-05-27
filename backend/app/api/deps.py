"""FastAPI dependency-injection factories for service-layer singletons.

Per .planning/v3/backend/DESIGN.md §Service Layer: each service is constructed
once per process (module-level) and exposed to routers through ``Depends(...)``.

Routers MUST NOT instantiate services directly — always use:

    from app.api.deps import get_queue_service, get_station_manager
    @router.post(...)
    async def handler(svc: QueueService = Depends(get_queue_service)): ...

This module avoids any import of routers so it can be imported from tests
without triggering FastAPI app construction.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.config import QUEUE_JSON_PATH
from app.services.queue_service import (
    JsonStore,
    MAX_QUEUE_SIZE,
    QueueService,
)
from app.services.station_manager import (
    DEFAULT_ALLOWED_ROOTS,
    DefaultProcessRunner,
    InMemoryBus,
    StationManager,
    StationRepo,
)


# ---------------------------------------------------------------------------
# QueueService
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _queue_service_singleton() -> QueueService:
    """Construct the QueueService backed by ~/.coco/queue.json."""
    store = JsonStore(Path(QUEUE_JSON_PATH))
    return QueueService(store, max_size=MAX_QUEUE_SIZE)


def get_queue_service() -> QueueService:
    """FastAPI dependency — returns the process-wide QueueService.

    Tests can override by calling ``app.dependency_overrides[get_queue_service] = ...``
    or by passing a custom instance directly.
    """
    return _queue_service_singleton()


# ---------------------------------------------------------------------------
# StationManager
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _event_bus_singleton() -> InMemoryBus:
    return InMemoryBus()


@lru_cache(maxsize=1)
def _station_manager_singleton() -> StationManager:
    """Construct the StationManager wired to the live platform.db engine.

    Lazily imports ``app.db.engine`` + ``psutil`` so that test modules can
    import this file without dragging in DB initialization.
    """
    from app.db.engine import engine  # local import to avoid eager DB connect
    import psutil

    repo = StationRepo(engine)
    bus = _event_bus_singleton()
    runner = DefaultProcessRunner()
    return StationManager(
        repo=repo,
        bus=bus,
        runner=runner,
        psutil_mod=psutil,
        max_concurrent=3,
        allowed_roots=DEFAULT_ALLOWED_ROOTS,
    )


def get_station_manager() -> StationManager:
    """FastAPI dependency — returns the process-wide StationManager."""
    return _station_manager_singleton()


def get_event_bus() -> InMemoryBus:
    """FastAPI dependency — returns the process-wide in-memory event bus."""
    return _event_bus_singleton()


__all__ = [
    "get_queue_service",
    "get_station_manager",
    "get_event_bus",
]
