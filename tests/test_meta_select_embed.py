"""embed() stays on loopback: proxy env vars are ignored and a 302 is refused."""

import json
import os
import socket
import sys
import threading
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "systems", "superintelligence", "scripts"))

import meta_select  # noqa: E402

_PROXY_KEYS = (
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
    "NO_PROXY", "no_proxy",
)


def _start(handler):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread


def _stop(httpd, thread):
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=5)


def _reserve():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    return sock


class _Quiet(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _read(self):
        n = int(self.headers.get("Content-Length", "0") or "0")
        if n:
            return self.rfile.read(n)
        return b""


def _embed_handler():
    class Handler(_Quiet):
        def do_POST(self):
            req = json.loads(self._read().decode() or "{}")
            data = [{"embedding": [float(i), 0.5]} for i, _ in enumerate(req.get("input") or [""])]
            body = json.dumps({"data": data}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def _redirect_handler(location):
    class Handler(_Quiet):
        def do_POST(self):
            self._read()
            self.send_response(302)
            self.send_header("Location", location)
            self.send_header("Content-Length", "0")
            self.end_headers()

    return Handler


def _sink_handler(hits):
    class Handler(_Quiet):
        def do_GET(self):
            hits.append(("GET", self.path))
            body = b'{"data":[{"embedding":[9]}]}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            self._read()
            hits.append(("POST", self.path))
            body = b'{"data":[{"embedding":[9]}]}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


class EmbedLocalOpenerTest(unittest.TestCase):
    def setUp(self):
        self._old = {k: os.environ.get(k) for k in _PROXY_KEYS}
        self._servers = []
        self._socks = []

    def tearDown(self):
        for key, value in self._old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        for sock in self._socks:
            sock.close()
        for httpd, thread in self._servers:
            _stop(httpd, thread)

    def _serve(self, handler):
        httpd, thread = _start(handler)
        self._servers.append((httpd, thread))
        return httpd

    def _dead_proxy(self):
        sock = _reserve()
        self._socks.append(sock)
        dead = f"http://127.0.0.1:{sock.getsockname()[1]}"
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
            os.environ[key] = dead
        os.environ["NO_PROXY"] = ""
        os.environ["no_proxy"] = ""

    def test_embed_ignores_proxy_env(self):
        httpd = self._serve(_embed_handler())
        self._dead_proxy()
        url = f"http://127.0.0.1:{httpd.server_address[1]}/v1/embeddings"
        with mock.patch.object(meta_select, "EMBED_URL", url):
            vecs = meta_select.embed(["ping", "pong"])
        self.assertEqual(vecs, [[0.0, 0.5], [1.0, 0.5]])

    def test_embed_refuses_redirect(self):
        hits = []
        sink = self._serve(_sink_handler(hits))
        location = f"http://127.0.0.1:{sink.server_address[1]}/v1/embeddings"
        httpd = self._serve(_redirect_handler(location))
        url = f"http://127.0.0.1:{httpd.server_address[1]}/v1/embeddings"
        with mock.patch.object(meta_select, "EMBED_URL", url):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                meta_select.embed(["ping"])
        self.assertEqual(caught.exception.code, 302)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
