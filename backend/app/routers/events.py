import asyncio
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from app.config import EVENTS_JSONL_PATH
from app.db.session import get_db
from app.services.event_bus import event_bus

router = APIRouter(tags=["Events"])


async def _jsonl_tail_generator():
    """Tail events.jsonl and yield new lines as SSE-ready dicts."""
    last_pos = 0

    if EVENTS_JSONL_PATH.exists():
        last_pos = EVENTS_JSONL_PATH.stat().st_size

    poll_interval = 1  # seconds

    while True:
        if EVENTS_JSONL_PATH.exists():
            current_size = EVENTS_JSONL_PATH.stat().st_size

            if current_size > last_pos:
                with open(EVENTS_JSONL_PATH) as f:
                    f.seek(last_pos)
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                yield {
                                    "event": data.get("type", "message"),
                                    "data": json.dumps(data),
                                }
                            except json.JSONDecodeError:
                                yield {"event": "raw", "data": line}
                    last_pos = f.tell()
            elif current_size < last_pos:
                # File was truncated/rotated
                last_pos = 0
                continue

        await asyncio.sleep(poll_interval)


async def _merged_event_generator(since: str | None = None):
    """Merge events from the in-process EventBus AND the external events.jsonl file.

    If *since* is provided (ISO-8601 timestamp), replays persisted events from
    the DB first so that reconnecting clients don't miss anything, then switches
    to live streaming.
    """
    heartbeat_interval = 15  # seconds
    poll_interval = 1  # seconds

    # --- Replay missed events from DB ---
    if since:
        for evt in event_bus.replay(since):
            yield evt

    # Set up EventBus subscription
    bus_queue: asyncio.Queue = asyncio.Queue(maxsize=256)
    event_bus._subscribers.append(bus_queue)

    # JSONL tail state
    last_pos = 0
    if EVENTS_JSONL_PATH.exists():
        last_pos = EVENTS_JSONL_PATH.stat().st_size

    since_heartbeat = 0.0

    try:
        while True:
            # 1. Drain all pending EventBus events (non-blocking)
            while True:
                try:
                    evt = bus_queue.get_nowait()
                    yield evt
                    since_heartbeat = 0.0
                except asyncio.QueueEmpty:
                    break

            # 2. Check for new JSONL lines
            if EVENTS_JSONL_PATH.exists():
                current_size = EVENTS_JSONL_PATH.stat().st_size
                if current_size > last_pos:
                    with open(EVENTS_JSONL_PATH) as f:
                        f.seek(last_pos)
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    data = json.loads(line)
                                    yield {
                                        "event": data.get("type", "message"),
                                        "data": json.dumps(data),
                                    }
                                except json.JSONDecodeError:
                                    yield {"event": "raw", "data": line}
                        last_pos = f.tell()
                    since_heartbeat = 0.0
                elif current_size < last_pos:
                    last_pos = 0
                    continue

            # 3. Wait briefly for a bus event, or fall through for next poll cycle
            try:
                evt = await asyncio.wait_for(bus_queue.get(), timeout=poll_interval)
                yield evt
                since_heartbeat = 0.0
            except asyncio.TimeoutError:
                since_heartbeat += poll_interval

            # 4. Heartbeat
            if since_heartbeat >= heartbeat_interval:
                yield {"event": "heartbeat", "data": ""}
                since_heartbeat = 0.0

    finally:
        event_bus.unsubscribe(bus_queue)


@router.get("/api/events/stream")
async def event_stream(since: Optional[str] = Query(None, description="ISO-8601 timestamp to replay events from")):
    return EventSourceResponse(_merged_event_generator(since=since))


async def _agent_status_generator():
    """Stream live agent status changes via the EventBus."""
    # 1. Send initial snapshot of all agents
    with get_db() as conn:
        rows = conn.exec_driver_sql(
            "SELECT id, name, status, role, pid, started_at, stopped_at, last_heartbeat "
            "FROM agents ORDER BY created_at DESC"
        ).fetchall()
        snapshot = [dict(r._mapping) for r in rows]

    yield {
        "event": "agent.snapshot",
        "data": json.dumps({"agents": snapshot, "type": "agent.snapshot"}),
    }

    # 2. Stream status deltas filtered to agent.* events
    async for event in event_bus.subscribe(event_prefix="agent."):
        yield event


@router.get("/api/events/agents")
async def agent_status_stream():
    """SSE endpoint for live agent status updates."""
    return EventSourceResponse(_agent_status_generator())


async def _agent_output_generator(agent_id: str):
    """Poll agent_output table and emit new rows as SSE events."""
    last_id = 0

    while True:
        with get_db() as conn:
            rows = conn.exec_driver_sql(
                "SELECT id, stream, chunk, timestamp FROM agent_output "
                "WHERE agent_id = ? AND id > ? ORDER BY id ASC LIMIT 50",
                (agent_id, last_id),
            ).fetchall()

            for row in rows:
                r = dict(row._mapping)
                last_id = r["id"]
                yield {
                    "id": str(r["id"]),
                    "event": "output",
                    "data": json.dumps(r),
                }

            # Check if agent is still active
            agent = conn.exec_driver_sql(
                "SELECT status FROM agents WHERE id = ?", (agent_id,)
            ).fetchone()

            if agent and agent._mapping["status"] in ("completed", "failed", "killed"):
                yield {
                    "event": "status",
                    "data": json.dumps({"status": agent._mapping["status"]}),
                }
                return

        await asyncio.sleep(1)


@router.get("/api/events/agents/{agent_id}")
async def agent_event_stream(agent_id: str):
    with get_db() as conn:
        row = conn.exec_driver_sql("SELECT id FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
    return EventSourceResponse(_agent_output_generator(agent_id))
