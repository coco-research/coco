#!/usr/bin/env python3
"""Local skill executor. Stdlib only.

generate() posts SKILL.md as the system message and the item as the user
message to a loopback model server. stub() is the offline stand-in used by tests.

The server URL is COCO_SKILL_EXEC_URL (default http://127.0.0.1:11434).
The model is COCO_SKILL_EXEC_MODEL (default qwen3:4b-instruct-2507-q4_K_M).
The wire shape is COCO_SKILL_EXEC_API: ollama (default) posts /api/chat, openai
posts /v1/chat/completions with the same messages, temperature 0, the seed and a
max_tokens cap, and reads choices[0].message.content.
An optional bearer token is COCO_SKILL_EXEC_TOKEN. It is sent on the openai path
only, only after the loopback check has passed, and it is never logged, cached or
written to a run record.
The per-request timeout is COCO_SKILL_EXEC_TIMEOUT seconds (default 600).
Each reply is capped at COCO_SKILL_EXEC_MAX_TOKENS output tokens (default 2048).
A non-loopback host is refused, same host set as the router regression gate.
Proxy environment variables are ignored and redirects are refused.
Pass cache=False so a reply is not written under evals/skills/.cache/.
"""
import hashlib
import http.client
import json
import math
import os
import pathlib
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

# Same opener as the router, found the same way evals/routing/check_regression.py finds meta_select.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "systems" / "superintelligence" / "scripts"))
from local_http import local_opener  # noqa: E402

# Same hosts the router regression gate accepts (evals/routing/check_regression.py).
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:4b-instruct-2507-q4_K_M"
API_OLLAMA, API_OPENAI = "ollama", "openai"
EXECUTOR_APIS = (API_OLLAMA, API_OPENAI)
OPENAI_PATH = "/v1/chat/completions"
CACHE = pathlib.Path(__file__).resolve().parent / ".cache"
# ponytail: one file per distinct request, no eviction. Upgrade path: cap the directory.


def require_loopback(url):
    """Exit if url's host is not loopback. Returns url otherwise."""
    host = urllib.parse.urlparse(url).hostname
    if host not in LOOPBACK:
        sys.exit(f"refusing non-local skill executor host {host!r}")
    return url


def executor_url():
    return require_loopback(os.environ.get("COCO_SKILL_EXEC_URL", DEFAULT_URL))


def executor_model():
    return os.environ.get("COCO_SKILL_EXEC_MODEL", DEFAULT_MODEL)


def executor_api():
    """Wire shape for the request. COCO_SKILL_EXEC_API is ollama (default) or openai."""
    raw = os.environ.get("COCO_SKILL_EXEC_API", API_OLLAMA)
    if raw not in EXECUTOR_APIS:
        sys.exit(f"COCO_SKILL_EXEC_API must be one of {' or '.join(EXECUTOR_APIS)}, got {raw!r}")
    return raw


def executor_token():
    """Optional bearer token from COCO_SKILL_EXEC_TOKEN.

    Only the openai path sends it, and only after require_loopback has passed. It is
    never logged, cached or written to a run record.
    """
    return os.environ.get("COCO_SKILL_EXEC_TOKEN") or None


def executor_timeout():
    """Seconds before a request is abandoned. COCO_SKILL_EXEC_TIMEOUT, default 600."""
    raw = os.environ.get("COCO_SKILL_EXEC_TIMEOUT", "600")
    try:
        seconds = float(raw)
    except ValueError:
        seconds = None
    if seconds is None or not math.isfinite(seconds) or seconds <= 0:
        sys.exit(f"COCO_SKILL_EXEC_TIMEOUT must be a positive number, got {raw!r}")
    return seconds


MAX_TOKENS_DEFAULT = 2048  # answers past this are cut; long skills otherwise ran past the timeout


def executor_max_tokens():
    """Output-token cap per reply. COCO_SKILL_EXEC_MAX_TOKENS, default 2048."""
    raw = os.environ.get("COCO_SKILL_EXEC_MAX_TOKENS", str(MAX_TOKENS_DEFAULT))
    if not raw.isdigit() or int(raw) <= 0:
        sys.exit(f"COCO_SKILL_EXEC_MAX_TOKENS must be a positive integer, got {raw!r}")
    return int(raw)


def chat_options(seed):
    return {"temperature": 0, "seed": seed, "num_ctx": 16384, "num_predict": executor_max_tokens()}


def openai_options(seed):
    """OpenAI-shaped options. The different key set keeps the two cache keys apart."""
    return {"temperature": 0, "seed": seed, "max_tokens": executor_max_tokens()}


def cache_digest(model, seed, options, skill_md, user_input):
    """sha256 of (model, seed, options, skill_md, user_input)."""
    payload = {
        "model": model,
        "seed": seed,
        "options": options,
        "skill_md": skill_md,
        "user_input": user_input,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def _read_cache(path):
    try:
        return json.loads(path.read_text())["output"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return None


def _write_cache(path, output):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"output": output}) + "\n")
    tmp.replace(path)


def generate(skill_md: str, user_input: str, *, model: str, seed: int = 0, url: str,
             cache: bool = True, api: str = API_OLLAMA) -> str:
    """Call the local model server. url is required and must be loopback. seed defaults to 0.

    api picks the wire shape: ollama posts /api/chat, openai posts /v1/chat/completions.
    cache=False does not read or write the on-disk cache.
    """
    require_loopback(url)
    if api not in EXECUTOR_APIS:
        sys.exit(f"unknown skill executor api {api!r}")
    if api == API_OPENAI:
        options, path_suffix = openai_options(seed), OPENAI_PATH
    else:
        options, path_suffix = chat_options(seed), "/api/chat"
    cache_path = None
    if cache:
        cache_path = CACHE / (cache_digest(model, seed, options, skill_md, user_input) + ".json")
        if cache_path.is_file():
            cached = _read_cache(cache_path)
            if isinstance(cached, str):
                return cached
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": skill_md},
            {"role": "user", "content": user_input},
        ],
        "stream": False,
    }
    if api == API_OPENAI:
        body.update(options)
    else:
        body["options"] = options
    headers = {"Content-Type": "application/json"}
    # require_loopback is the gate the token passes: a non-loopback URL exits above, and
    # the opener refuses redirects, so the header cannot be replayed at another host.
    token = executor_token() if api == API_OPENAI else None
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(
        url.rstrip("/") + path_suffix,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    timeout = executor_timeout()
    try:
        with local_opener().open(req, timeout=timeout) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"skill executor HTTP {e.code}")
    except urllib.error.URLError as e:
        sys.exit(f"skill executor request failed: {e.reason}")
    except (TimeoutError, socket.timeout):
        sys.exit(f"skill executor timed out after {timeout:g}s")
    except json.JSONDecodeError:
        sys.exit("skill executor returned invalid JSON")
    except (OSError, http.client.HTTPException, UnicodeDecodeError) as e:
        # e.g. the server dropped the connection mid-reply; TimeoutError is caught above
        sys.exit(f"skill executor connection failed: {type(e).__name__}")
    try:
        if api == API_OPENAI:
            output = payload["choices"][0]["message"]["content"]
        else:
            output = payload["message"]["content"]
    except (KeyError, IndexError, TypeError):
        sys.exit("skill executor returned no message content")
    if not isinstance(output, str):
        sys.exit("skill executor returned a non-string message")
    if cache:
        _write_cache(cache_path, output)
    return output


def stub(skill_md: str, user_input: str, *, model: str, seed: int = 0, url: str) -> str:
    """Offline executor. Deterministic and no network. Output is built from the user input.

    model, url, seed, and skill_md match generate()'s signature so the two executors swap.
    """
    return "stub:" + user_input
