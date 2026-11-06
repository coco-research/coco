#!/usr/bin/env python3
"""Router embedding fallback: LM Studio, then Ollama, then a loud keyword path.

No network beyond a loopback fake. Patches the built-in endpoint list in-process
and points --doctor at the same list through COCO_EMBED_ENDPOINTS.

Run from anywhere: python3 tests/check-router-embed-fallback.py
"""
import contextlib
import io
import json
import os
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "systems", "superintelligence", "scripts", "meta_select.py")
WARN = "router: no embedding server, using keyword matching"

for key in list(os.environ):
    if key.startswith("COCO_EMBED") or key == "COCO_ROUTER_M0":
        os.environ.pop(key, None)

sys.path.insert(0, os.path.join(ROOT, "systems", "superintelligence", "scripts"))
import meta_select  # noqa: E402


hits = []


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        return

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(n) if n else b""
        hits.append(self.path)
        body = json.loads(raw.decode() or "{}")
        inputs = body.get("input") or [""]
        data = [{"embedding": [1.0, 0.0]} for _ in inputs]
        out = json.dumps({"data": data}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def warn_count(text):
    return sum(1 for line in text.splitlines() if line == WARN)


def closed_port():
    """A loopback port with nothing listening. Connection is refused.

    Holding the bind open is not enough: on macOS that blackholes the SYN
    until the client times out, instead of refusing.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return f"http://127.0.0.1:{port}/v1/embeddings"


def reset():
    meta_select._pinned = False
    meta_select.EMBED_URL = meta_select._IMPORT_URL
    meta_select.EMBED_MODEL = meta_select._DEFAULT_EMBED_MODEL
    os.environ.pop("COCO_EMBED_URL", None)
    os.environ.pop("COCO_EMBED_MODEL", None)
    os.environ.pop("COCO_EMBED_ENDPOINTS", None)


def route(prompt="should we ship an AI compliance product?"):
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        out = meta_select.select(prompt)
    return out, buf.getvalue()


def doctor(env):
    return subprocess.run(
        [sys.executable, SCRIPT, "--doctor"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def main():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    fake = f"http://127.0.0.1:{httpd.server_address[1]}/v1/embeddings"
    closed_a = closed_port()
    closed_b = closed_port()
    try:
        reset()
        meta_select._EMBED_ENDPOINTS = (
            (closed_a, "text-embedding-nomic-embed-text-v1.5"),
            (fake, "nomic-embed-text"),
        )
        out, err = route()
        if out.get("method") != "embed":
            fail(f"expected method embed, got {out.get('method')!r} stderr={err!r}")
        if meta_select.EMBED_URL != fake:
            fail(f"EMBED_URL is {meta_select.EMBED_URL!r}, want the fake server")
        if not hits:
            fail("fake server was never asked")
        print("PASS: closed port then fake server routes with method embed")

        reset()
        meta_select._EMBED_ENDPOINTS = (
            (closed_a, "text-embedding-nomic-embed-text-v1.5"),
            (closed_b, "nomic-embed-text"),
        )
        out, err = route()
        if out.get("method") != "keyword" or out.get("degraded") is not True:
            fail(f"expected keyword degraded, got method={out.get('method')!r} degraded={out.get('degraded')!r}")
        if warn_count(err) != 1:
            fail(f"warning count {warn_count(err)}, stderr={err!r}")
        print("PASS: both closed falls back to keyword and warns once")

        before = len(hits)
        reset()
        meta_select._EMBED_ENDPOINTS = ((fake, "nomic-embed-text"),)
        os.environ["COCO_EMBED_URL"] = closed_a
        os.environ["COCO_EMBED_ENDPOINTS"] = f"{fake}|nomic-embed-text"
        out, err = route()
        if out.get("method") != "keyword":
            fail(f"COCO_EMBED_URL should force keyword, got {out.get('method')!r}")
        if len(hits) != before:
            fail("built-in list was tried while COCO_EMBED_URL was set")
        print("PASS: COCO_EMBED_URL skips the built-in list")

        base = os.environ.copy()
        base.pop("COCO_EMBED_URL", None)
        base.pop("COCO_EMBED_MODEL", None)
        up = dict(base)
        up["COCO_EMBED_ENDPOINTS"] = (
            f"{closed_a}|text-embedding-nomic-embed-text-v1.5,{fake}|nomic-embed-text"
        )
        proc = doctor(up)
        via = f"router: embedding via {fake} (nomic-embed-text)"
        if proc.returncode != 0 or via not in proc.stdout.splitlines():
            fail(f"--doctor up: rc={proc.returncode} stdout={proc.stdout!r} stderr={proc.stderr!r}")
        print("PASS: --doctor names the fake server and exits 0")

        down = dict(base)
        down["COCO_EMBED_ENDPOINTS"] = f"{closed_a}|m,{closed_b}|m"
        proc = doctor(down)
        if proc.returncode != 1 or warn_count(proc.stderr) != 1:
            fail(f"--doctor down: rc={proc.returncode} stderr={proc.stderr!r}")
        print("PASS: --doctor exits 1 and warns once when both endpoints are closed")
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
    print("PASS: router embed fallback")


if __name__ == "__main__":
    main()
