import asyncio
import json
import logging
import os
import uuid

from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse

from app.config import CHAT_TIMEOUT_MINUTES
from app.db.connections import get_platform_db
from app.services.chat_context import build_chat_context
from app.models.chat import ChatRequest, MessageOut, SessionCreate, SessionOut

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _create_session(title: str | None = None, model: str | None = "sonnet") -> dict:
    """Create a new chat session and return it as a dict."""
    session_id = str(uuid.uuid4())
    with get_platform_db() as db:
        db.execute(
            "INSERT INTO chat_sessions (id, title, model) VALUES (?, ?, ?)",
            (session_id, title or "New Chat", model),
        )
        db.commit()
        row = db.execute(
            "SELECT id, title, model, message_count, created_at, updated_at FROM chat_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    return dict(row)


def _update_session_after_message(session_id: str, title: str | None = None):
    """Increment message_count, update updated_at, and optionally set title."""
    with get_platform_db() as db:
        if title:
            db.execute(
                "UPDATE chat_sessions SET message_count = message_count + 1, "
                "updated_at = datetime('now'), title = ? WHERE id = ?",
                (title, session_id),
            )
        else:
            db.execute(
                "UPDATE chat_sessions SET message_count = message_count + 1, "
                "updated_at = datetime('now') WHERE id = ?",
                (session_id,),
            )
        db.commit()


def _save_message(
    role: str,
    content: str,
    model: str | None = None,
    tokens_used: int | None = None,
    session_id: str | None = None,
) -> str:
    """Save a chat message to platform.db and return its id."""
    msg_id = str(uuid.uuid4())
    with get_platform_db() as db:
        db.execute(
            "INSERT INTO chat_messages (id, session_id, role, content, model, tokens_used) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, session_id, role, content, model, tokens_used),
        )
        db.commit()
    return msg_id


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------

@router.get("/api/chat/sessions")
def list_sessions():
    """List all chat sessions ordered by most recently updated."""
    try:
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT id, title, model, message_count, created_at, updated_at "
                "FROM chat_sessions ORDER BY updated_at DESC"
            ).fetchall()

            sessions = [dict(r) for r in rows]

            # Check for orphan messages (no session_id) and surface as "Unsorted"
            orphan_count = db.execute(
                "SELECT COUNT(*) as cnt FROM chat_messages WHERE session_id IS NULL"
            ).fetchone()["cnt"]

            if orphan_count > 0:
                # Find the earliest and latest orphan message timestamps
                ts = db.execute(
                    "SELECT MIN(created_at) as first_at, MAX(created_at) as last_at "
                    "FROM chat_messages WHERE session_id IS NULL"
                ).fetchone()
                sessions.append({
                    "id": "__unsorted__",
                    "title": "Unsorted",
                    "model": None,
                    "message_count": orphan_count,
                    "created_at": ts["first_at"] or "",
                    "updated_at": ts["last_at"] or "",
                })

            return sessions
    except Exception as e:
        logger.exception("list_sessions failed: %s", e)
        return []


@router.post("/api/chat/sessions")
def create_session(req: SessionCreate | None = None):
    """Create a new chat session."""
    title = req.title if req else None
    model = req.model if req else "sonnet"
    return _create_session(title=title, model=model)


@router.get("/api/chat/sessions/{session_id}/messages")
def get_session_messages(
    session_id: str,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Get messages for a specific session."""
    try:
        with get_platform_db() as db:
            if session_id == "__unsorted__":
                rows = db.execute(
                    "SELECT id, session_id, role, content, model, tokens_used, created_at "
                    "FROM chat_messages WHERE session_id IS NULL "
                    "ORDER BY created_at ASC LIMIT ? OFFSET ?",
                    (limit, offset),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT id, session_id, role, content, model, tokens_used, created_at "
                    "FROM chat_messages WHERE session_id = ? "
                    "ORDER BY created_at ASC LIMIT ? OFFSET ?",
                    (session_id, limit, offset),
                ).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.exception("get_session_messages failed for session %s: %s", session_id, e)
        return []


@router.delete("/api/chat/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session and all its messages."""
    try:
        with get_platform_db() as db:
            if session_id == "__unsorted__":
                db.execute("DELETE FROM chat_messages WHERE session_id IS NULL")
            else:
                db.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
                db.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            db.commit()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Claude CLI helpers
# ---------------------------------------------------------------------------

async def _check_claude_available() -> bool:
    """Check if the claude CLI is available on PATH."""
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


async def chat_event_generator(message: str, model: str, system_prompt: str, session_id: str | None = None):
    """Async generator yielding SSE event dicts for EventSourceResponse."""
    env = {**os.environ}
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)

    cmd = ["claude", "-p", "--verbose", "--output-format", "stream-json"]
    if model:
        cmd.extend(["--model", model])
    full_prompt = f"[System context]\n{system_prompt}\n\n[User message]\n{message}"
    cmd.append(full_prompt)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.environ.get("HOME", "/tmp"),
            env=env,
            limit=1024 * 1024,  # 1MB line buffer (default 64KB too small for stream-json)
        )
    except FileNotFoundError:
        yield {"event": "error", "data": json.dumps({"type": "error", "message": "claude CLI not found on PATH"})}
        return
    except Exception as e:
        yield {"event": "error", "data": json.dumps({"type": "error", "message": f"Failed to start claude: {str(e)}"})}
        return

    full_response = ""
    timeout_seconds = CHAT_TIMEOUT_MINUTES * 60
    timed_out = False

    try:
        deadline = asyncio.get_event_loop().time() + timeout_seconds

        async for line in proc.stdout:  # noqa: E501
            if asyncio.get_event_loop().time() > deadline:
                timed_out = True
                break

            text = line.decode("utf-8", errors="replace").strip()
            if not text:
                continue

            try:
                chunk = json.loads(text)
                if not isinstance(chunk, dict):
                    continue

                chunk_type = chunk.get("type")

                # Handle assistant message content blocks
                if chunk_type == "assistant":
                    assistant_message = chunk.get("message")
                    if isinstance(assistant_message, dict):
                        content_blocks = assistant_message.get("content", [])
                        for block in content_blocks:
                            if isinstance(block, dict) and block.get("type") == "text":
                                token = block.get("text", "")
                                full_response += token
                                yield {"event": "token", "data": json.dumps({"type": "token", "content": token})}

                # Handle content_block_delta streaming events
                elif chunk_type == "content_block_delta":
                    delta = chunk.get("delta", {})
                    if isinstance(delta, dict) and delta.get("type") == "text_delta":
                        token = delta.get("text", "")
                        full_response += token
                        yield {"event": "token", "data": json.dumps({"type": "token", "content": token})}

                # Handle result type (final assembled message — result can be a string or dict)
                elif chunk_type == "result":
                    result_val = chunk.get("result")
                    if isinstance(result_val, str):
                        # result is the plain text response
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

                # Skip system, rate_limit_event, etc. silently

            except json.JSONDecodeError:
                continue

        if timed_out:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
            yield {"event": "error", "data": json.dumps({"type": "error", "message": f"Chat timed out after {CHAT_TIMEOUT_MINUTES} minutes"})}
            # Still save whatever we got
            if full_response:
                _save_message("assistant", full_response, model, session_id=session_id)
                if session_id:
                    _update_session_after_message(session_id)
            return

        await proc.wait()

        # Check for errors
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
        # CRITICAL: Kill the claude subprocess if it is still running when the
        # generator is closed (e.g., client disconnects, CancelledError, GeneratorExit).
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

    # Save assistant message and send done event
    tokens_used = len(full_response.split()) if full_response else 0  # rough estimate
    if full_response:
        _save_message("assistant", full_response, model, tokens_used, session_id=session_id)
        if session_id:
            # Auto-title: if session title is still "New Chat", set it from user message
            with get_platform_db() as db:
                row = db.execute("SELECT title FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
                if row and row["title"] == "New Chat":
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
    """Stream a chat response from Claude via SSE."""
    # Validate
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(req.message) > 50000:
        raise HTTPException(status_code=400, detail="Message too long (max 50,000 characters)")

    # Check claude is available
    if not await _check_claude_available():
        raise HTTPException(status_code=503, detail="claude CLI is not installed or not on PATH")

    model = req.model or "sonnet"

    # Resolve or create session
    session_id = req.session_id
    if not session_id:
        # Auto-create a session
        auto_title = req.message[:50].strip()
        if len(req.message) > 50:
            auto_title += "..."
        session = _create_session(title=auto_title, model=model)
        session_id = session["id"]

    # Save user message
    _save_message("user", req.message, model, session_id=session_id)
    _update_session_after_message(session_id)

    # Build system prompt with full context injection
    system_prompt = build_chat_context(project_id=req.project_id)

    # Return SSE stream — include session_id in first event so frontend can track it
    async def event_gen():
        # Emit session_id as the first event so the frontend knows which session this belongs to
        yield {"event": "session", "data": json.dumps({"type": "session", "session_id": session_id})}
        async for evt in chat_event_generator(req.message, model, system_prompt, session_id=session_id):
            yield evt

    return EventSourceResponse(
        event_gen(),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# Legacy history endpoints (backward compat)
# ---------------------------------------------------------------------------

@router.get("/api/chat/history")
def chat_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Return chat messages in chronological order (oldest first)."""
    try:
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT id, session_id, role, content, model, tokens_used, created_at "
                "FROM chat_messages ORDER BY created_at ASC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logger.exception("chat_history failed: %s", e)
        return []


@router.delete("/api/chat/history")
def clear_chat_history():
    """Delete all chat messages."""
    try:
        with get_platform_db() as db:
            db.execute("DELETE FROM chat_messages")
            db.execute("DELETE FROM chat_sessions")
            db.commit()
        return {"status": "ok", "message": "Chat history cleared"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
