#!/usr/bin/env python3
"""Render deterministic Aloo Mannu repo banners from the 3D Three.js scene (code in, image out).

Outputs:
  - <out-dir>/banner-readme.png           (1280x560, rounded alpha card, < 1 MB, 0 metadata chunks)
  - <out-dir>/social-preview-1280x640.png (1280x640, social preview card, < 1 MB, 0 metadata chunks)
"""
from __future__ import annotations

import argparse
from functools import partial
import html
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import zlib

PNG_SIG = b"\x89PNG\r\n\x1a\n"
KEEP_CHUNKS = {b"IHDR", b"sRGB", b"gAMA", b"IDAT", b"IEND"}


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return


def strip_png_metadata(path: Path) -> tuple[int, int, int]:
    raw = path.read_bytes()
    if raw[:8] != PNG_SIG:
        raise ValueError(f"{path}: not a PNG file")
    out = bytearray(PNG_SIG)
    pos = 8
    width = height = 0
    saw_iend = False
    while pos + 8 <= len(raw):
        length = struct.unpack(">I", raw[pos : pos + 4])[0]
        if pos + 12 + length > len(raw):
            raise ValueError(f"{path}: truncated PNG chunk")
        ctype = raw[pos + 4 : pos + 8]
        body = raw[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR" and len(body) >= 8:
            width, height = struct.unpack(">II", body[:8])
        if ctype in KEEP_CHUNKS:
            crc = zlib.crc32(ctype + body) & 0xFFFFFFFF
            out.extend(struct.pack(">I", length))
            out.extend(ctype)
            out.extend(body)
            out.extend(struct.pack(">I", crc))
        if ctype == b"IEND":
            saw_iend = True
            break
    if not saw_iend or width <= 0 or height <= 0:
        raise ValueError(f"{path}: missing IHDR or IEND chunk")
    cleaned = bytes(out)
    if len(cleaned) >= 1_000_000:
        raise ValueError(f"{path}: {len(cleaned)} bytes exceeds 1 MB cap")
    path.write_bytes(cleaned)
    return width, height, len(cleaned)


def find_playwright_node_pkg() -> Path | None:
    pw_bin = shutil.which("playwright")
    if not pw_bin:
        return None
    resolved = Path(pw_bin).resolve()
    for parent in resolved.parents:
        cand = parent / "node_modules" / "playwright"
        if cand.is_dir():
            return cand
        if parent.name == "playwright" and (parent / "index.js").is_file():
            return parent
    return None


def capture_with_playwright(jobs: list[dict[str, object]]) -> None:
    pw_pkg = find_playwright_node_pkg()
    node_bin = shutil.which("node")
    if pw_pkg and node_bin:
        js = """
const fs = require('fs');
const pw = require(process.argv[2]);
const jobs = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
(async () => {
  const browser = await pw.chromium.launch({ channel: 'chrome' }).catch(() => pw.chromium.launch());
  try {
    for (const j of jobs) {
      const ctx = await browser.newContext({
        viewport: { width: j.width, height: j.height },
        deviceScaleFactor: j.dpr || 1,
        colorScheme: j.scheme || 'dark',
        reducedMotion: j.reducedMotion ? 'reduce' : 'no-preference',
      });
      const page = await ctx.newPage();
      await page.goto(j.url, { waitUntil: 'networkidle' });
      if (j.waitReady) {
        await page.waitForFunction(() => window.__ALOO_BANNER_READY === true, null, { timeout: 8000 }).catch(() => {});
      }
      await page.waitForTimeout(j.waitMs || 450);
      await page.screenshot({ path: j.out, omitBackground: Boolean(j.omitBg) });
      await ctx.close();
    }
  } finally {
    await browser.close();
  }
})();
"""
        with tempfile.TemporaryDirectory() as td:
            script_p = Path(td) / "capture.cjs"
            jobs_p = Path(td) / "jobs.json"
            script_p.write_text(js, encoding="utf-8")
            jobs_p.write_text(json.dumps(jobs), encoding="utf-8")
            subprocess.run([node_bin, str(script_p), str(pw_pkg), str(jobs_p)], check=True)
        return

    pw_cli = shutil.which("playwright")
    if not pw_cli:
        raise RuntimeError("playwright CLI not found on PATH")
    for j in jobs:
        cmd = [
            pw_cli, "screenshot", "--channel", "chrome",
            "--color-scheme", str(j.get("scheme", "dark")),
            "--viewport-size", f"{j['width']},{j['height']}",
            "--wait-for-timeout", str(j.get("waitMs", 900)),
            str(j["url"]), str(j["out"]),
        ]
        subprocess.run(cmd, check=True)


def write_readme_preview_html(preview_html: Path, banner_rel: str) -> None:
    safe_src = html.escape(banner_rel, quote=True)
    preview_html.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Aloo Mannu README Preview</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    margin: 0; padding: 36px 24px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: #ffffff; color: #1f2328; line-height: 1.55;
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #0d1117; color: #e6edf3; }}
    .md-box {{ border-color: #30363d !important; background: #0d1117 !important; }}
    h1, h2 {{ border-bottom-color: #21262d !important; }}
    pre {{ background: #161b22 !important; color: #e6edf3 !important; }}
  }}
  .md-box {{
    max-width: 980px; margin: 0 auto; padding: 32px;
    border: 1px solid #d0d7de; border-radius: 8px; background: #ffffff;
  }}
  .banner {{ display: block; width: 100%; height: auto; margin: 0 0 22px; }}
  h1 {{ font-size: 2rem; padding-bottom: 0.3em; border-bottom: 1px solid #d8dee4; margin: 0 0 16px; }}
  h2 {{ font-size: 1.45rem; padding-bottom: 0.3em; border-bottom: 1px solid #d8dee4; margin: 24px 0 12px; }}
  p {{ margin: 0 0 14px; font-size: 1rem; }}
  pre {{ padding: 14px 16px; border-radius: 6px; background: #f6f8fa; font-size: 0.88rem; overflow: auto; }}
</style>
</head>
<body>
  <article class="md-box">
    <img class="banner" src="{safe_src}" alt="Aloo Mannu — Good conversations start here.">
    <h1>Aloo Mannu</h1>
    <p>Aloo Mannu is the local message and wake layer for coding agents. It routes asks, replies and updates between agent sessions through local files and hooks, and keeps one record of open asks.</p>
    <p>Local-first, Python standard library only, with no cloud account and no model calls in Aloo Mannu itself.</p>
  </article>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=repo_root / "aloomannu", help="Output directory for repo banner PNGs")
    ap.add_argument("--bubbles", choices=("story", "outline"), default="story", help="Render bubble text or pure outlines")
    ap.add_argument("--proof-dir", type=Path, default=None, help="Optional directory to write page & README proof screenshots")
    args = ap.parse_args()

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    readme_png = out_dir / "banner-readme.png"
    social_png = out_dir / "social-preview-1280x640.png"
    b_query = "&bubbles=outline" if args.bubbles == "outline" else ""

    handler = partial(QuietHandler, directory=str(repo_root))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        base = f"http://127.0.0.1:{port}/aloomannu/"
        jobs: list[dict[str, object]] = [
            {"url": f"{base}?banner=readme{b_query}", "out": str(readme_png), "width": 1280, "height": 560, "dpr": 1, "scheme": "dark", "omitBg": True, "waitReady": True, "waitMs": 350},
            {"url": f"{base}?banner=social{b_query}", "out": str(social_png), "width": 1280, "height": 640, "dpr": 1, "scheme": "dark", "omitBg": False, "waitReady": True, "waitMs": 350},
        ]
        if args.proof_dir is not None:
            pdir = args.proof_dir.resolve()
            pdir.mkdir(parents=True, exist_ok=True)
            jobs.extend([
                {"url": f"{base}?theme=dark", "out": str(pdir / "aloo-mannu-desktop-dark.png"), "width": 1440, "height": 900, "dpr": 1, "scheme": "dark", "waitMs": 650},
                {"url": f"{base}?theme=light", "out": str(pdir / "aloo-mannu-desktop-light.png"), "width": 1440, "height": 900, "dpr": 1, "scheme": "light", "waitMs": 650},
                {"url": f"{base}?theme=dark", "out": str(pdir / "aloo-mannu-phone-dark.png"), "width": 390, "height": 844, "dpr": 1, "scheme": "dark", "waitMs": 650},
                {"url": f"{base}?theme=light", "out": str(pdir / "aloo-mannu-phone-light.png"), "width": 390, "height": 844, "dpr": 1, "scheme": "light", "waitMs": 650},
            ])
        capture_with_playwright(jobs)

        rw, rh, rbytes = strip_png_metadata(readme_png)
        sw, sh, sbytes = strip_png_metadata(social_png)
        print(f"rendered {readme_png.name}: {rw}x{rh}, {rbytes} bytes")
        print(f"rendered {social_png.name}: {sw}x{sh}, {sbytes} bytes")

        if args.proof_dir is not None:
            pdir = args.proof_dir.resolve()
            with tempfile.TemporaryDirectory() as td:
                td_path = Path(td)
                shutil.copy2(readme_png, td_path / "banner-readme.png")
                write_readme_preview_html(td_path / "index.html", "banner-readme.png")
                p_httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(td_path)))
                p_port = p_httpd.server_address[1]
                threading.Thread(target=p_httpd.serve_forever, daemon=True).start()
                try:
                    p_url = f"http://127.0.0.1:{p_port}/"
                    capture_with_playwright([
                        {"url": p_url, "out": str(pdir / "aloo-mannu-readme-rendered-dark.png"), "width": 1120, "height": 860, "dpr": 1, "scheme": "dark", "waitMs": 250},
                        {"url": p_url, "out": str(pdir / "aloo-mannu-readme-rendered-light.png"), "width": 1120, "height": 860, "dpr": 1, "scheme": "light", "waitMs": 250},
                    ])
                finally:
                    p_httpd.shutdown()
            shutil.copy2(readme_png, pdir / "aloo-mannu-banner-readme.png")
            shutil.copy2(social_png, pdir / "aloo-mannu-social-preview-1280x640.png")
    finally:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
