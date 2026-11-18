#!/usr/bin/env bash
# Verify Coco Research SI brand assets (pure-orb <=32px favicons, 1280x640 OG card,
# and README dark/light <picture> banner).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 - <<'PY'
import pathlib, struct, zlib

root = pathlib.Path(".")

def check_png(rel: str, want_w: int, want_h: int, zero_wordmark: bool = False) -> None:
    p = root / rel
    assert p.is_file(), f"missing {rel}"
    raw = p.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", f"{rel}: invalid PNG magic"
    w, h, depth, ctype = struct.unpack(">IIBB", raw[16:26])
    assert (w, h, depth) == (want_w, want_h, 8), f"{rel}: got {(w, h, depth)}, expected {(want_w, want_h, 8)}"
    if not zero_wordmark:
        return
    channels = 4 if ctype == 6 else 3
    idat = []
    pos = 8
    while pos + 8 <= len(raw):
        ln = struct.unpack(">I", raw[pos : pos + 4])[0]
        tp = raw[pos + 4 : pos + 8]
        if tp == b"IDAT":
            idat.append(raw[pos + 8 : pos + 8 + ln])
        if tp == b"IEND":
            break
        pos += 12 + ln
    dec = zlib.decompress(b"".join(idat))
    stride = w * channels
    recon = bytearray(h * stride)
    for y in range(h):
        flt = dec[y * (stride + 1)]
        rin = y * (stride + 1) + 1
        rout = y * stride
        for i in range(stride):
            x = dec[rin + i]
            a = recon[rout + i - channels] if i >= channels else 0
            b = recon[rout - stride + i] if y > 0 else 0
            c = recon[rout - stride + i - channels] if y > 0 and i >= channels else 0
            if flt == 1:
                val = (x + a) & 0xFF
            elif flt == 2:
                val = (x + b) & 0xFF
            elif flt == 3:
                val = (x + ((a + b) >> 1)) & 0xFF
            elif flt == 4:
                pr_p = a + b - c
                pa, pb, pc = abs(pr_p - a), abs(pr_p - b), abs(pr_p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                val = (x + pr) & 0xFF
            else:
                val = x
            recon[rout + i] = val
    y_start = max(0, h - max(3, (h * 16 + 99) // 100))
    bright = 0
    for y in range(y_start, h):
        for x in range(w):
            idx = (y * w + x) * channels
            r, g, b_ch = recon[idx], recon[idx + 1], recon[idx + 2]
            alpha = recon[idx + 3] / 255.0 if channels == 4 else 1.0
            if (0.2126 * r + 0.7152 * g + 0.0722 * b_ch) * alpha > 115:
                bright += 1
    assert bright == 0, f"{rel}: expected 0 wordmark pixels in bottom band, found {bright}"

check_png("assets/favicon-16x16.png", 16, 16, zero_wordmark=True)
check_png("assets/favicon-32x32.png", 32, 32, zero_wordmark=True)
check_png("assets/site/favicon-32.png", 32, 32, zero_wordmark=True)
check_png("assets/graphics-system/exports/favicons/favicon-16x16.png", 16, 16, zero_wordmark=True)
check_png("assets/graphics-system/exports/favicons/favicon-32x32.png", 32, 32, zero_wordmark=True)
check_png("assets/apple-touch-icon.png", 180, 180)
check_png("apple-touch-icon.png", 180, 180)
check_png("assets/banner-si-dark.png", 1500, 500)
check_png("assets/banner-si-light.png", 1500, 500)
check_png("assets/og-image.png", 1280, 640)

for ico in ("favicon.ico", "assets/favicon.ico", "assets/graphics-system/exports/favicons/favicon.ico"):
    raw = (root / ico).read_bytes()
    rsv, typ, count = struct.unpack("<HHH", raw[:6])
    assert (rsv, typ, count) == (0, 1, 3), f"{ico}: invalid ICO header {(rsv, typ, count)}"

readme = (root / "README.md").read_text(encoding="utf-8")
assert "assets/banner-si-dark.png" in readme and "assets/banner-si-light.png" in readme
PY

VER_OUT=$(COCO_NO_UPDATE_CHECK=1 node bin/coco.js --version)
echo "$VER_OUT" | grep -q "Coco Super Intelligence" || { echo "FAIL: --version missing product name"; exit 1; }
echo "$VER_OUT" | grep -q "Coco Research (cocoresearch.org)" || { echo "FAIL: --version missing org line"; exit 1; }

HELP_OUT=$(COCO_NO_UPDATE_CHECK=1 node bin/coco.js --help)
echo "$HELP_OUT" | grep -q "Coco Super Intelligence · Coco Research (cocoresearch.org)" || { echo "FAIL: --help missing identity line"; exit 1; }

python3 - <<'PY'
import os, pty, shutil, subprocess, tempfile

with tempfile.TemporaryDirectory() as td:
    bindir = os.path.join(td, "bin")
    cwd = os.path.join(td, "cwd")
    home = os.path.join(td, "home")
    os.makedirs(bindir)
    os.makedirs(cwd)
    os.makedirs(home)
    git_stub = os.path.join(bindir, "git")
    with open(git_stub, "w", encoding="utf-8") as f:
        f.write('#!/bin/sh\nfor a; do d="$a"; done\nmkdir -p "$d" && echo "exit 0" > "$d/install.sh"\n')
    os.chmod(git_stub, 0o755)
    base_env = {
        **os.environ,
        "HOME": home,
        "COCO_NO_UPDATE_CHECK": "1",
        "PATH": bindir + ":" + os.environ.get("PATH", ""),
    }
    env_tty = dict(base_env)
    env_tty.pop("NO_COLOR", None)

    master, slave = pty.openpty()
    proc = subprocess.Popen(
        ["node", os.path.abspath("bin/coco.js"), "install"],
        cwd=cwd, env=env_tty, stdin=subprocess.DEVNULL, stdout=slave, stderr=slave, close_fds=True,
    )
    os.close(slave)
    chunks = []
    while True:
        try:
            b = os.read(master, 4096)
        except OSError:
            break
        if not b:
            break
        chunks.append(b)
    os.close(master)
    proc.wait(timeout=15)
    tty_out = b"".join(chunks).decode("utf-8", "replace")
    assert "COCO RESEARCH" in tty_out and "SUPER INTELLIGENCE" in tty_out, tty_out
    assert "\x1b[1;38;2;91;141;255m" in tty_out, "expected ANSI brand header on TTY"

    shutil.rmtree(cwd)
    os.makedirs(cwd)
    master2, slave2 = pty.openpty()
    env_nc = {**env_tty, "NO_COLOR": "1"}
    proc2 = subprocess.Popen(
        ["node", os.path.abspath("bin/coco.js"), "install"],
        cwd=cwd, env=env_nc, stdin=subprocess.DEVNULL, stdout=slave2, stderr=slave2, close_fds=True,
    )
    os.close(slave2)
    chunks2 = []
    while True:
        try:
            b = os.read(master2, 4096)
        except OSError:
            break
        if not b:
            break
        chunks2.append(b)
    os.close(master2)
    proc2.wait(timeout=15)
    nc_out = b"".join(chunks2).decode("utf-8", "replace")
    assert "COCO RESEARCH · SUPER INTELLIGENCE" in nc_out, nc_out
    assert "\x1b[" not in nc_out, "expected zero ANSI escapes under NO_COLOR=1"
PY

echo "PASS: Coco SI brand assets and CLI banner verified"
