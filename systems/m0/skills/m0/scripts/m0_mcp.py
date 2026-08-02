#!/usr/bin/env python3
"""M0 MCP server - exposes the M0 memory protocol as two tools over stdio.

Tools:
    m0_remember   write one entry to the operational thread (idempotent)
    m0_recall     read the most recent entries, newest first

Transport is JSON-RPC 2.0 over stdin/stdout, one message per line, which is
what MCP stdio clients speak. Standard library only.

The tools wrap the M0 HTTP endpoints (POST /api/brain/checkpoint and
GET /api/brain/thread). If no server is listening and M0_MCP_TRANSPORT is
"auto" (the default), the tools fall back to the local SQLite store directly,
so memory still works when no daemon is running. Every response reports which
path served it under "via".

Register with Claude Code:
    claude mcp add coco-m0 -- python3 <this file>

Environment:
    M0_BASE_URL         M0 server base URL (default http://127.0.0.1:8787)
    M0_MCP_TRANSPORT    auto (default) | http | direct
    M0_PROJECT          default project when a call omits it
    M0_SOURCE_TOOL      stamped onto writes (default "mcp")
    M0_HTTP_TIMEOUT     HTTP timeout in seconds (default 15)
    plus every M0_* variable understood by m0_server.py for the direct path

MIT licensed, part of the Coco M0 bundle.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import m0_server  # noqa: E402  (local module, same directory)

SERVER_NAME = "coco-m0"
SERVER_VERSION = m0_server.VERSION
DEFAULT_PROTOCOL = "2025-06-18"
BASE_URL = os.environ.get("M0_BASE_URL", "http://127.0.0.1:8787").rstrip("/")
TRANSPORT = os.environ.get("M0_MCP_TRANSPORT", "auto").strip().lower()
HTTP_TIMEOUT = float(os.environ.get("M0_HTTP_TIMEOUT", "15"))

START_HINT = (
    "No M0 server is listening at "
    + BASE_URL
    + ". Start one with:  python3 "
    + str(Path(__file__).resolve().parent / "m0_server.py")
    + " serve"
)

# meta accepts a JSON object. It is declared as type "object" on purpose: a
# client that hands the tool structured metadata gets it through unchanged.
# Declaring it as a string is the bug this server exists not to have - clients
# coerce a JSON string argument into a dict before the tool sees it, so a
# string-typed parameter rejects every valid value and is unusable. Strings are
# still accepted here for compatibility (see m0_server.Store.canonical_meta).
META_SCHEMA = {
    "type": "object",
    "description": (
        "Optional structured metadata, as a JSON object (not a JSON string). "
        "Example: {\"pr\": 42, \"tests\": \"green\"}. A JSON-encoded string is "
        "also accepted and parsed; any other string is stored as "
        "{\"note\": \"...\"} rather than rejected."
    ),
    "additionalProperties": True,
}

TOOLS = [
    {
        "name": "m0_remember",
        "description": (
            "Write one entry to the M0 operational thread so the next session - in "
            "this tool or any other - can pick the work up. Use it after finishing a "
            "step, making a decision, or before a session ends. Idempotent: writing "
            "the same content twice creates one row."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "What happened, in one or two plain sentences.",
                },
                "project": {
                    "type": "string",
                    "description": "Project key. Defaults to $M0_PROJECT, then the current directory name.",
                },
                "kind": {
                    "type": "string",
                    "enum": list(m0_server.KINDS),
                    "default": m0_server.DEFAULT_KIND,
                    "description": (
                        "step_done for a fact or decision (default); compact_checkpoint "
                        "for a session handoff; session_end when a session closes; "
                        "lane_dispatched / lane_result for delegated work; ambient_signal "
                        "for passively observed context."
                    ),
                },
                "next_step": {
                    "type": "string",
                    "description": "The single next action a fresh session should take.",
                },
                "last_verified": {
                    "type": "string",
                    "description": "What was actually verified, and how (not what was assumed).",
                },
                "session_id": {"type": "string", "description": "Session identifier, if known."},
                "branch": {"type": "string", "description": "Git branch, if relevant."},
                "head_sha": {"type": "string", "description": "Git HEAD sha, if relevant."},
                "meta": META_SCHEMA,
            },
            "required": ["text"],
        },
    },
    {
        "name": "m0_recall",
        "description": (
            "Read the most recent M0 operational-thread entries for a project, newest "
            "first. Call this at the start of a session, or when picking up work started "
            "in another tool, before asking the user to repeat context."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Project key. Defaults to $M0_PROJECT, then the current directory name.",
                },
                "limit": {
                    "type": "integer",
                    "default": m0_server.DEFAULT_LIMIT,
                    "minimum": 1,
                    "maximum": m0_server.MAX_LIMIT,
                    "description": "How many entries to return (newest first).",
                },
                "kind": {
                    "type": "string",
                    "enum": list(m0_server.KINDS),
                    "description": "Optional filter. Omit for the whole thread.",
                },
            },
        },
    },
]


# ------------------------------------------------------------------ transports


def _http(method: str, path: str, payload: dict | None = None,
          query: dict | None = None) -> dict:
    url = BASE_URL + path
    if query:
        clean = {k: v for k, v in query.items() if v not in (None, "")}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"ok": False, "error": body.strip() or str(exc)}
        parsed.setdefault("ok", False)
        parsed["http_status"] = exc.code
        return parsed


_store = None


def store() -> m0_server.Store:
    global _store
    if _store is None:
        _store = m0_server.Store()
    return _store


def call_write(payload: dict) -> dict:
    if TRANSPORT != "direct":
        try:
            result = _http("POST", "/api/brain/checkpoint", payload=payload)
            result["via"] = "http"
            return result
        except (urllib.error.URLError, OSError) as exc:
            if TRANSPORT == "http":
                return {"ok": False, "error": f"{START_HINT} ({exc})", "via": "http"}
    result = store().write(payload)
    result["via"] = "direct"
    return result


def call_read(project: str | None, limit: int, kind: str | None) -> dict:
    query = {"project": project, "limit": limit, "kind": kind}
    if TRANSPORT != "direct":
        try:
            result = _http("GET", "/api/brain/thread", query=query)
            result["via"] = "http"
            return result
        except (urllib.error.URLError, OSError) as exc:
            if TRANSPORT == "http":
                return {"ok": False, "error": f"{START_HINT} ({exc})", "via": "http"}
    result = store().read(project=project, limit=limit, kind=kind)
    result["via"] = "direct"
    return result


# ----------------------------------------------------------------- tool bodies


def default_project(given) -> str:
    for candidate in (given, os.environ.get("M0_PROJECT"), Path.cwd().name):
        if candidate and str(candidate).strip():
            return str(candidate).strip()
    return "default"


def normalize_meta(args: dict):
    """Accept meta or meta_json, as an object or a string. Never reject."""
    raw = args.get("meta")
    if raw is None:
        raw = args.get("meta_json")
    return m0_server.Store.canonical_meta(raw)


def tool_remember(args: dict) -> tuple[str, dict]:
    text = args.get("text")
    if not text or not str(text).strip():
        raise ValueError("'text' is required and must be non-empty")
    payload = {
        "project": default_project(args.get("project")),
        "text": str(text).strip(),
        "kind": args.get("kind") or m0_server.DEFAULT_KIND,
        "next_step": args.get("next_step"),
        "last_verified": args.get("last_verified"),
        "session_id": args.get("session_id"),
        "source_tool": args.get("source_tool") or os.environ.get("M0_SOURCE_TOOL") or "mcp",
        "branch": args.get("branch"),
        "head_sha": args.get("head_sha"),
        "meta_json": normalize_meta(args),
    }
    result = call_write({k: v for k, v in payload.items() if v is not None})
    if not result.get("ok"):
        raise ValueError(result.get("error") or "write failed")
    lines = [
        f"Remembered in project '{payload['project']}' as {payload['kind']}.",
        f"  id  {result.get('id')}",
        f"  ts  {result.get('ts')}",
        f"  via {result.get('via')}"
        + ("  (deferred to sidecar - the store was busy; it lands on next drain)"
           if result.get("deferred") else ""),
    ]
    return "\n".join(lines), result


def tool_recall(args: dict) -> tuple[str, dict]:
    project = default_project(args.get("project"))
    try:
        limit = int(args.get("limit") or m0_server.DEFAULT_LIMIT)
    except (TypeError, ValueError):
        raise ValueError(f"'limit' must be an integer, got {args.get('limit')!r}")
    kind = args.get("kind") or None
    result = call_read(project, limit, kind)
    if result.get("ok") is False:
        raise ValueError(result.get("error") or "read failed")

    entries = result.get("entries") or []
    header = f"M0 thread for '{project}'"
    if kind:
        header += f" (kind={kind})"
    header += f" - {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}, newest first"
    if result.get("degraded"):
        header += f"  [degraded: {result['degraded']}]"
    lines = [header, ""]
    if not entries:
        lines.append("(nothing recorded yet - write with m0_remember)")
    for entry in entries:
        stamp = entry.get("ts") or "?"
        marks = []
        if entry.get("source_tool"):
            marks.append(entry["source_tool"])
        if entry.get("branch"):
            marks.append(entry["branch"])
        if entry.get("pending"):
            marks.append("pending")
        suffix = f"  [{' | '.join(marks)}]" if marks else ""
        lines.append(f"- {stamp}  ({entry.get('kind')}){suffix}")
        lines.append(f"    {entry.get('text')}")
        if entry.get("next_step"):
            lines.append(f"    next: {entry['next_step']}")
        if entry.get("last_verified"):
            lines.append(f"    verified: {entry['last_verified']}")
        if entry.get("meta_json"):
            lines.append(f"    meta: {entry['meta_json']}")
    return "\n".join(lines), result


HANDLERS = {"m0_remember": tool_remember, "m0_recall": tool_recall}


# ------------------------------------------------------------------ jsonrpc io


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def reply(request_id, result: dict) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "result": result})


def fail(request_id, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def handle(message: dict) -> None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}
    is_notification = "id" not in message

    if method == "initialize":
        requested = str(params.get("protocolVersion") or "")
        version = requested if len(requested) == 10 and requested.count("-") == 2 else DEFAULT_PROTOCOL
        reply(request_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": (
                "Call m0_recall at the start of a session to pick up the operational "
                "thread, and m0_remember after each meaningful step so the next session "
                "or tool can continue without re-reading the whole history."
            ),
        })
        return

    if method in ("notifications/initialized", "initialized", "notifications/cancelled"):
        return

    if method == "ping":
        reply(request_id, {})
        return

    if method == "tools/list":
        reply(request_id, {"tools": TOOLS})
        return

    if method in ("resources/list", "prompts/list"):
        reply(request_id, {"resources": []} if method.startswith("resources") else {"prompts": []})
        return

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        handler = HANDLERS.get(name)
        if handler is None:
            reply(request_id, {
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                "isError": True,
            })
            return
        try:
            text, structured = handler(args if isinstance(args, dict) else {})
        except Exception as exc:  # tool errors travel in the result, per MCP
            reply(request_id, {
                "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                "isError": True,
            })
            return
        reply(request_id, {
            "content": [{"type": "text", "text": text}],
            "structuredContent": structured,
            "isError": False,
        })
        return

    if is_notification:
        return
    fail(request_id, -32601, f"Method not found: {method}")


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(None, -32700, f"Parse error: {exc}")
            continue
        if not isinstance(message, dict):
            fail(None, -32600, "Invalid Request: expected a JSON object")
            continue
        try:
            handle(message)
        except Exception as exc:  # pragma: no cover - last-resort guard
            if "id" in message:
                fail(message.get("id"), -32603, f"Internal error: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
