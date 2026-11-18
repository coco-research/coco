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

echo "PASS: Coco SI brand assets verified"
