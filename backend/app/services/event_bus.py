"""In-process async event bus for broadcasting real-time events to SSE subscribers."""

from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncGenerator


class EventBus:
    """Simple async broadcast using one asyncio.Queue per subscriber."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue] = []

    def emit(self, event_type: str, data: dict) -> None:
        """Send an event to every active subscriber.

        Safe to call from sync code — it does not await.
        """
        envelope = {
            "event": event_type,
            "data": json.dumps({**data, "type": event_type, "ts": time.time()}),
        }
        dead: list[asyncio.Queue] = []
        for q in self._subscribers:
            try:
                q.put_nowait(envelope)
            except asyncio.QueueFull:
                # Slow consumer — drop the oldest event and retry
                try:
                    q.get_nowait()
                    q.put_nowait(envelope)
                except Exception:
                    dead.append(q)
        for q in dead:
            self._subscribers.remove(q)

    async def subscribe(self) -> AsyncGenerator[dict, None]:
        """Yield SSE-ready dicts as they arrive. Call unsubscribe() on cleanup."""
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._subscribers.append(q)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            self.unsubscribe(q)

    def unsubscribe(self, q: asyncio.Queue) -> None:
        try:
            self._subscribers.remove(q)
        except ValueError:
            pass


# Module-level singleton
event_bus = EventBus()
