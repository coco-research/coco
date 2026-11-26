import json
import os
import urllib.request

BASE_URL = os.environ.get("M0_BASE_URL", "http://127.0.0.1:8787").rstrip("/")
TRANSPORT = os.environ.get("M0_MCP_TRANSPORT", "auto").strip().lower()
HTTP_TIMEOUT = float(os.environ.get("M0_HTTP_TIMEOUT", "15"))


def send(text: str) -> bytes:
    if TRANSPORT == "direct":
        return b""
    body = {"project": os.environ.get("M0_PROJECT", "default"), "source_tool": os.environ.get("M0_SOURCE_TOOL", "mcp"), "text": text}
    req = urllib.request.Request(BASE_URL + "/api/brain/checkpoint", data=json.dumps(body).encode("utf-8"), method="POST")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return resp.read()
