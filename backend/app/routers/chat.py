import asyncio
import json
import logging
import os
import uuid

from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from sqlalchemy import select, insert, update, delete, func

from app.config import CHAT_TIMEOUT_MINUTES, USE_AGENT_SDK
from app.db.session import get_db
from app.db.tables import chat_sessions, chat_messages, hub_content
from app.db.compat import now
from app.services.chat_context import build_chat_context
from app.services.spawn_limiter import get_spawn_semaphore
from app.models.chat import ChatRequest, MessageOut, SessionCreate, SessionOut

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _create_session(title: str | None = None, model: str | None = "sonnet") -> dict:
    session_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            insert(chat_sessions).values(id=session_id, title=title or "New Chat", model=model)
        )
        row = conn.execute(
            select(
                chat_sessions.c.id, chat_sessions.c.title, chat_sessions.c.model,
                chat_sessions.c.message_count, chat_sessions.c.created_at, chat_sessions.c.updated_at,
            ).where(chat_sessions.c.id == session_id)
        ).fetchone()
    return dict(row._mapping)


def _update_session_after_message(session_id: str, title: str | None = None):
    with get_db() as conn:
        values: dict = {
            "message_count": chat_sessions.c.message_count + 1,
            "updated_at": now(),
        }
        if title:
            values["title"] = title
        conn.execute(
            update(chat_sessions)
            .where(chat_sessions.c.id == session_id)
            .values(**values)
        )


def _save_message(
    role: str,
    content: str,
    model: str | None = None,
    tokens_used: int | None = None,
    session_id: str | None = None,
) -> str:
    msg_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            insert(chat_messages).values(
                id=msg_id, session_id=session_id, role=role,
                content=content, model=model, tokens_used=tokens_used,
            )
        )
    return msg_id


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------

@router.get("/api/chat/sessions")
def list_sessions():
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    chat_sessions.c.id, chat_sessions.c.title, chat_sessions.c.model,
                    chat_sessions.c.message_count, chat_sessions.c.created_at, chat_sessions.c.updated_at,
                ).order_by(chat_sessions.c.updated_at.desc())
            ).fetchall()

            sessions = [dict(r._mapping) for r in rows]

            orphan_count_row = conn.execute(
                select(func.count().label("cnt"))
                .select_from(chat_messages)
                .where(chat_messages.c.session_id.is_(None))
            ).fetchone()
            orphan_count = orphan_count_row.cnt if orphan_count_row else 0

            if orphan_count > 0:
                ts = conn.execute(
                    select(
                        func.min(chat_messages.c.created_at).label("first_at"),
                        func.max(chat_messages.c.created_at).label("last_at"),
                    )
                    .where(chat_messages.c.session_id.is_(None))
                ).fetchone()
                sessions.append({
                    "id": "__unsorted__",
                    "title": "Unsorted",
                    "model": None,
                    "message_count": orphan_count,
                    "created_at": ts.first_at or "",
                    "updated_at": ts.last_at or "",
                })

            return sessions
    except Exception as e:
        logger.exception("list_sessions failed: %s", e)
        return []


@router.post("/api/chat/sessions")
def create_session(req: SessionCreate | None = None):
    title = req.title if req else None
    model = req.model if req else "sonnet"
    return _create_session(title=title, model=model)


@router.get("/api/chat/sessions/{session_id}/messages")
def get_session_messages(
    session_id: str,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    try:
        with get_db() as conn:
            _msg_cols = [
                chat_messages.c.id, chat_messages.c.session_id, chat_messages.c.role,
                chat_messages.c.content, chat_messages.c.model, chat_messages.c.tokens_used,
                chat_messages.c.created_at,
            ]
            if session_id == "__unsorted__":
                rows = conn.execute(
                    select(*_msg_cols)
                    .where(chat_messages.c.session_id.is_(None))
                    .order_by(chat_messages.c.created_at.asc())
                    .limit(limit).offset(offset)
                ).fetchall()
            else:
                rows = conn.execute(
                    select(*_msg_cols)
                    .where(chat_messages.c.session_id == session_id)
                    .order_by(chat_messages.c.created_at.asc())
                    .limit(limit).offset(offset)
                ).fetchall()
            return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.exception("get_session_messages failed for session %s: %s", session_id, e)
        return []


@router.delete("/api/chat/sessions/{session_id}")
def delete_session(session_id: str):
    try:
        with get_db() as conn:
            if session_id == "__unsorted__":
                conn.execute(
                    delete(chat_messages).where(chat_messages.c.session_id.is_(None))
                )
            else:
                conn.execute(
                    delete(chat_messages).where(chat_messages.c.session_id == session_id)
                )
                conn.execute(
                    delete(chat_sessions).where(chat_sessions.c.id == session_id)
                )
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Claude CLI helpers
# ---------------------------------------------------------------------------

async def _check_claude_available() -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            "which", "claude",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
        return proc.returncode == 0
    except Exception:
        return False


async def _sdk_chat_event_generator(message: str, model: str, system_prompt: str, session_id: str | None = None):
    from app.services.agent_sdk_client import agent_sdk

    full_response = ""
    input_tokens = 0
    output_tokens = 0
    response_model = model

    try:
        async for event in agent_sdk.stream_chat(
            prompt=message, model=model, system=system_prompt, max_tokens=8192,
        ):
            event_type = event.get("type")
            if event_type == "token":
                token = event.get("content", "")
                full_response += token
                yield {"event": "token", "data": json.dumps({"type": "token", "content": token})}
            elif event_type == "usage":
                input_tokens = event.get("input_tokens", 0)
                output_tokens = event.get("output_tokens", 0)
                response_model = event.get("model", model)
            elif event_type == "done":
                if not full_response:
                    full_response = event.get("content", "")
    except Exception as e:
        logger.exception("SDK chat stream error: %s", e)
        yield {"event": "error", "data": json.dumps({"type": "error", "message": f"SDK stream error: {str(e)}"})}
        if full_response:
            _save_message("assistant", full_response, model, session_id=session_id)
            if session_id:
                _update_session_after_message(session_id)
        return

    tokens_used = input_tokens + output_tokens
    if full_response:
        _save_message("assistant", full_response, model, tokens_used, session_id=session_id)
        if session_id:
            with get_db() as conn:
                row = conn.execute(
                    select(chat_sessions.c.title).where(chat_sessions.c.id == session_id)
                ).fetchone()
                if row and row.title == "New Chat":
                    auto_title = message[:50].strip()
                    if len(message) > 50:
                        auto_title += "..."
                    _update_session_after_message(session_id, title=auto_title)
                else:
                    _update_session_after_message(session_id)

    if input_tokens or output_tokens:
        from app.services.agent_sdk_client import record_sdk_cost
        record_sdk_cost(
            model=response_model, input_tokens=input_tokens,
            output_tokens=output_tokens, source="chat",
        )

    yield {"event": "done", "data": json.dumps({"type": "done", "content": full_response, "session_id": session_id})}


async def chat_event_generator(message: str, model: str, system_prompt: str, session_id: str | None = None):
    if USE_AGENT_SDK:
        from app.services.agent_sdk_client import agent_sdk
        if agent_sdk.is_available():
            async for evt in _sdk_chat_event_generator(message, model, system_prompt, session_id):
                yield evt
            return

    env = {**os.environ}
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)

    cmd = ["claude", "-p", "--verbose", "--output-format", "stream-json"]
    if model:
        cmd.extend(["--model", model])
    full_prompt = f"[System context]\n{system_prompt}\n\n[User message]\n{message}"
    cmd.append(full_prompt)

    # Cap concurrent claude-CLI spawns to prevent OOM (NEXT_SPRINT 1.3).
    # The slot is held for the lifetime of the subprocess (released in the
    # outer finally below) so that simultaneous running agents are bounded
    # by COCO_MAX_PARALLEL_AGENTS, not just simultaneous spawn calls.
    _spawn_sem = get_spawn_semaphore()
    await _spawn_sem.acquire()
    _spawn_slot_held = True
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.environ.get("HOME", "/tmp"),
            env=env,
            limit=1024 * 1024,
        )
    except FileNotFoundError:
        _spawn_sem.release()
        _spawn_slot_held = False
        yield {"event": "error", "data": json.dumps({"type": "error", "message": "claude CLI not found on PATH"})}
        return
    except Exception as e:
        _spawn_sem.release()
        _spawn_slot_held = False
        yield {"event": "error", "data": json.dumps({"type": "error", "message": f"Failed to start claude: {str(e)}"})}
        return

    full_response = ""
    timeout_seconds = CHAT_TIMEOUT_MINUTES * 60
    timed_out = False

    try:
        deadline = asyncio.get_event_loop().time() + timeout_seconds

        async for line in proc.stdout:
            if asyncio.get_event_loop().time() > deadline:
                timed_out = True
                break

            line_text = line.decode("utf-8", errors="replace").strip()
            if not line_text:
                continue

            try:
                chunk = json.loads(line_text)
                if not isinstance(chunk, dict):
                    continue

                chunk_type = chunk.get("type")

                if chunk_type == "assistant":
                    assistant_message = chunk.get("message")
                    if isinstance(assistant_message, dict):
                        content_blocks = assistant_message.get("content", [])
                        for block in content_blocks:
                            if isinstance(block, dict) and block.get("type") == "text":
                                token = block.get("text", "")
                                full_response += token
                                yield {"event": "token", "data": json.dumps({"type": "token", "content": token})}

                elif chunk_type == "content_block_delta":
                    delta = chunk.get("delta", {})
                    if isinstance(delta, dict) and delta.get("type") == "text_delta":
                        token = delta.get("text", "")
                        full_response += token
                        yield {"event": "token", "data": json.dumps({"type": "token", "content": token})}

                elif chunk_type == "result":
                    result_val = chunk.get("result")
                    if isinstance(result_val, str):
                        if not full_response:
                            full_response = result_val
                            yield {"event": "token", "data": json.dumps({"type": "token", "content": result_val})}
                    elif isinstance(result_val, dict):
                        content_blocks = result_val.get("content", [])
                        for block in content_blocks:
                            if isinstance(block, dict) and block.get("type") == "text":
                                token = block.get("text", "")
                                if not full_response:
                                    full_response = token
                                    yield {"event": "token", "data": json.dumps({"type": "token", "content": token})}

            except json.JSONDecodeError:
                continue

        if timed_out:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
            yield {"event": "error", "data": json.dumps({"type": "error", "message": f"Chat timed out after {CHAT_TIMEOUT_MINUTES} minutes"})}
            if full_response:
                _save_message("assistant", full_response, model, session_id=session_id)
                if session_id:
                    _update_session_after_message(session_id)
            return

        await proc.wait()

        if proc.returncode != 0 and not full_response:
            stderr_bytes = await proc.stderr.read()
            stderr_text = stderr_bytes.decode("utf-8", errors="replace").strip()
            yield {"event": "error", "data": json.dumps({"type": "error", "message": f"claude exited with code {proc.returncode}: {stderr_text[:500]}"})}
            return

    except Exception as e:
        yield {"event": "error", "data": json.dumps({"type": "error", "message": f"Stream error: {str(e)}"})}
        if full_response:
            _save_message("assistant", full_response, model, session_id=session_id)
            if session_id:
                _update_session_after_message(session_id)
        return

    finally:
        if proc.returncode is None:
            try:
                proc.terminate()
            except Exception:
                pass
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except (asyncio.TimeoutError, Exception):
                try:
                    proc.kill()
                except Exception:
                    pass
        # Release the spawn semaphore slot now that the subprocess has exited
        # (NEXT_SPRINT 1.3 — cap concurrent claude-CLI agents).
        if _spawn_slot_held:
            _spawn_sem.release()
            _spawn_slot_held = False

    tokens_used = len(full_response.split()) if full_response else 0
    if full_response:
        _save_message("assistant", full_response, model, tokens_used, session_id=session_id)
        if session_id:
            with get_db() as conn:
                row = conn.execute(
                    select(chat_sessions.c.title).where(chat_sessions.c.id == session_id)
                ).fetchone()
                if row and row.title == "New Chat":
                    auto_title = message[:50].strip()
                    if len(message) > 50:
                        auto_title += "..."
                    _update_session_after_message(session_id, title=auto_title)
                else:
                    _update_session_after_message(session_id)

    yield {"event": "done", "data": json.dumps({"type": "done", "content": full_response, "session_id": session_id})}


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------

@router.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(req.message) > 50000:
        raise HTTPException(status_code=400, detail="Message too long (max 50,000 characters)")

    sdk_available = False
    if USE_AGENT_SDK:
        from app.services.agent_sdk_client import agent_sdk
        sdk_available = agent_sdk.is_available()
    if not sdk_available and not await _check_claude_available():
        raise HTTPException(status_code=503, detail="claude CLI is not installed or not on PATH (set USE_AGENT_SDK=true to use API instead)")

    model = req.model or "sonnet"

    session_id = req.session_id
    if not session_id:
        auto_title = req.message[:50].strip()
        if len(req.message) > 50:
            auto_title += "..."
        session = _create_session(title=auto_title, model=model)
        session_id = session["id"]

    _save_message("user", req.message, model, session_id=session_id)
    _update_session_after_message(session_id)

    system_prompt = build_chat_context(project_id=req.project_id)

    # If content_ids are attached, fetch them from hub mirror
    message_with_context = req.message
    if req.content_ids:
        context_parts: list[str] = []
        for cid in req.content_ids[:10]:
            try:
                with get_db() as conn:
                    row = conn.execute(
                        select(
                            hub_content.c.title, hub_content.c.summary,
                            hub_content.c.body, hub_content.c.source,
                        ).where(hub_content.c.id == cid)
                    ).fetchone()
                    if row:
                        part = f"--- Attached: {row.title or 'Untitled'} (source: {row.source or 'unknown'}) ---\n"
                        if row.summary:
                            part += f"{row.summary}\n"
                        if row.body:
                            part += f"{row.body}\n"
                        context_parts.append(part)
            except Exception:
                pass
        if context_parts:
            attached_context = "\n".join(context_parts)
            message_with_context = f"[The user has attached the following Knowledge Hub content for context:]\n\n{attached_context}\n\n[User message:]\n{req.message}"

    async def event_gen():
        yield {"event": "session", "data": json.dumps({"type": "session", "session_id": session_id})}
        async for evt in chat_event_generator(message_with_context, model, system_prompt, session_id=session_id):
            yield evt

    return EventSourceResponse(
        event_gen(),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# Legacy history endpoints
# ---------------------------------------------------------------------------

@router.get("/api/chat/history")
def chat_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    chat_messages.c.id, chat_messages.c.session_id, chat_messages.c.role,
                    chat_messages.c.content, chat_messages.c.model, chat_messages.c.tokens_used,
                    chat_messages.c.created_at,
                )
                .order_by(chat_messages.c.created_at.asc())
                .limit(limit).offset(offset)
            ).fetchall()
            return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.exception("chat_history failed: %s", e)
        return []


@router.delete("/api/chat/history")
def clear_chat_history():
    try:
        with get_db() as conn:
            conn.execute(delete(chat_messages))
            conn.execute(delete(chat_sessions))
        return {"status": "ok", "message": "Chat history cleared"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
