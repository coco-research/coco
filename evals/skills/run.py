#!/usr/bin/env python3
"""Local skill executor. Stdlib only.

generate() posts SKILL.md as the system message and the item as the user
message to Ollama /api/chat. stub() is the offline stand-in used by tests.

The server URL is COCO_SKILL_EXEC_URL (default http://127.0.0.1:11434).
The model is COCO_SKILL_EXEC_MODEL (default qwen3:4b-instruct-2507-q4_K_M).
A non-loopback host is refused, same host set as the router regression gate.
Proxy environment variables are ignored and redirects are refused.
Pass cache=False so a reply is not written under evals/skills/.cache/.
"""
import hashlib
import json
import os
import pathlib
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


def chat_options(seed):
    return {"temperature": 0, "seed": seed, "num_ctx": 16384}


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


def generate(skill_md: str, user_input: str, *, model: str, seed: int = 0, url: str, cache: bool = True) -> str:
    """Call Ollama /api/chat. url is required and must be loopback. seed defaults to 0.

    cache=False does not read or write the on-disk cache.
    """
    require_loopback(url)
    options = chat_options(seed)
    path = None
    if cache:
        path = CACHE / (cache_digest(model, seed, options, skill_md, user_input) + ".json")
        if path.is_file():
            cached = _read_cache(path)
            if isinstance(cached, str):
                return cached
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": skill_md},
            {"role": "user", "content": user_input},
        ],
        "stream": False,
        "options": options,
    }).encode()
    req = urllib.request.Request(
        url.rstrip("/") + "/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with local_opener().open(req, timeout=600) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"skill executor HTTP {e.code}")
    except urllib.error.URLError as e:
        sys.exit(f"skill executor request failed: {e.reason}")
    try:
        output = payload["message"]["content"]
    except (KeyError, TypeError):
        sys.exit("skill executor returned no message content")
    if not isinstance(output, str):
        sys.exit("skill executor returned a non-string message")
    if cache:
        _write_cache(path, output)
    return output


def stub(skill_md: str, user_input: str, *, model: str, seed: int = 0, url: str) -> str:
    """Offline executor. Deterministic and no network. Output is built from the user input.

    model, url, seed, and skill_md match generate()'s signature so the two executors swap.
    """
    return "stub:" + user_input
