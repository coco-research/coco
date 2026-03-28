import asyncio
import json
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from app.config import EVENTS_JSONL_PATH
from app.db.connections import get_platform_db
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


async def _merged_event_generator():
    """Merge events from the in-process EventBus AND the external events.jsonl file.

    Uses asyncio.wait to select whichever source produces an event first,
    plus a periodic heartbeat so the SSE connection stays alive.
    """
    heartbeat_interval = 15  # seconds
    poll_interval = 1  # seconds

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
async def event_stream():
    return EventSourceResponse(_merged_event_generator())


async def _agent_status_generator():
    """Stream live agent status changes via the EventBus.

    On connect, emits a snapshot of all current agents so the client
    can hydrate without a separate REST call, then streams deltas.
    """
    # 1. Send initial snapshot of all agents
    with get_platform_db() as db:
        rows = db.execute(
            "SELECT id, name, status, role, pid, started_at, stopped_at, last_heartbeat "
            "FROM agents ORDER BY created_at DESC"
        ).fetchall()
        snapshot = [dict(r) for r in rows]

    yield {
        "event": "agent.snapshot",
        "data": json.dumps({"agents": snapshot, "type": "agent.snapshot"}),
    }

    # 2. Stream status deltas filtered to agent.* events
    async for event in event_bus.subscribe(event_prefix="agent."):
        yield event


@router.get("/api/events/agents")
async def agent_status_stream():
    """SSE endpoint for live agent status updates.

    Emits an initial ``agent.snapshot`` event with all agents, then
    streams ``agent.spawned``, ``agent.paused``, ``agent.resumed``,
    ``agent.killed``, ``agent.completed``, and ``agent.failed`` events
    as they occur.
    """
    return EventSourceResponse(_agent_status_generator())


async def _agent_output_generator(agent_id: str):
    """Poll agent_output table and emit new rows as SSE events."""
    last_id = 0

    while True:
        with get_platform_db() as db:
            rows = db.execute(
                """SELECT id, stream, chunk, timestamp FROM agent_output
                   WHERE agent_id = ? AND id > ?
                   ORDER BY id ASC LIMIT 50""",
                (agent_id, last_id),
            ).fetchall()

            for row in rows:
                r = dict(row)
                last_id = r["id"]
                yield {
                    "id": str(r["id"]),
                    "event": "output",
                    "data": json.dumps(r),
                }

            # Check if agent is still active
            agent = db.execute(
                "SELECT status FROM agents WHERE id = ?", (agent_id,)
            ).fetchone()

            if agent and agent["status"] in ("completed", "failed", "killed"):
                # Emit final status event
                yield {
                    "event": "status",
                    "data": json.dumps({"status": agent["status"]}),
                }
                return

        await asyncio.sleep(1)


@router.get("/api/events/agents/{agent_id}")
async def agent_event_stream(agent_id: str):
    with get_platform_db() as db:
        row = db.execute("SELECT id FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Agent not found")
    return EventSourceResponse(_agent_output_generator(agent_id))
