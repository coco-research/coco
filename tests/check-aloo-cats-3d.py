#!/usr/bin/env python3
"""Gate for 3D Three.js Aloo Mannu page stage + deterministic repo banners."""
from __future__ import annotations

from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ALOO_HTML = ROOT / "aloomannu" / "index.html"
README_PNG = ROOT / "aloomannu" / "banner-readme.png"
SOCIAL_PNG = ROOT / "aloomannu" / "social-preview-1280x640.png"
CSS_PATH = ROOT / "assets" / "css" / "product.css"
PARTS_JS = ROOT / "assets" / "js" / "aloo-cats-parts.js"
MODELS_JS = ROOT / "assets" / "js" / "aloo-cats-models.js"
SCENE_JS = ROOT / "assets" / "js" / "aloo-cats-scene.js"
RENDER_BANNERS = ROOT / "assets" / "js" / "render-aloo-banners.py"

PNG_SIG = b"\x89PNG\r\n\x1a\n"
ALLOWED_CHUNKS = {b"IHDR", b"IDAT", b"IEND", b"sRGB", b"gAMA", b"pHYs"}
FORBIDDEN_BYTES = re.compile(b"(?:/" + b"Users/|/home/|/private/var/folders/)", re.I)

failures: list[str] = []


def check(cond: bool, ok_msg: str, err_msg: str) -> None:
    if cond:
        print(f"  PASS: {ok_msg}")
    else:
        print(f"  FAIL: {err_msg}")
        failures.append(err_msg)


def inspect_png(path: Path) -> tuple[bool, int, int, list[bytes]]:
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != PNG_SIG:
        return False, 0, 0, []
    pos = 8
    width = height = 0
    chunks: list[bytes] = []
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        ctype = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        chunks.append(ctype)
        if ctype == b"IHDR" and len(body) >= 8:
            width, height = struct.unpack(">II", body[:8])
        pos += 12 + length
        if ctype == b"IEND":
            break
    return True, width, height, chunks


def verify_banner_png(path: Path, label: str, expected_size: tuple[int, int] | None = None) -> None:
    check(path.is_file(), f"{label} exists", f"missing {path.relative_to(ROOT)}")
    if not path.is_file():
        return
    raw = path.read_bytes()
    check(0 < len(raw) < 1_000_000, f"{label} under 1 MB ({len(raw)} bytes)", f"{label} exceeds 1 MB ({len(raw)} bytes)")
    ok, w, h, chunks = inspect_png(path)
    check(ok and w > 0 and h > 0, f"{label} is valid PNG ({w}x{h})", f"{label} is not a valid PNG")
    if expected_size is not None:
        check((w, h) == expected_size, f"{label} dimensions {w}x{h} == {expected_size[0]}x{expected_size[1]}",
              f"{label} dimensions {w}x{h} != {expected_size[0]}x{expected_size[1]}")
    extra = [c.decode("latin1", "replace") for c in chunks if c not in ALLOWED_CHUNKS]
    check(not extra, f"{label} stripped of metadata chunks", f"{label} has unexpected PNG chunks: {extra}")
    check(FORBIDDEN_BYTES.search(raw) is None, f"{label} free of internal names/paths", f"{label} leaks internal bytes")


def main() -> int:
    check(MODELS_JS.is_file(), "aloo-cats-models.js exists", "missing assets/js/aloo-cats-models.js")
    check(SCENE_JS.is_file(), "aloo-cats-scene.js exists", "missing assets/js/aloo-cats-scene.js")
    check(RENDER_BANNERS.is_file(), "render-aloo-banners.py exists next to scene", "missing assets/js/render-aloo-banners.py")
    check(ALOO_HTML.is_file(), "aloomannu/index.html exists", "missing aloomannu/index.html")

    html_txt = ALOO_HTML.read_text(encoding="utf-8") if ALOO_HTML.is_file() else ""
    css_txt = CSS_PATH.read_text(encoding="utf-8") if CSS_PATH.is_file() else ""
    parts_txt = PARTS_JS.read_text(encoding="utf-8") if PARTS_JS.is_file() else ""
    models_txt = MODELS_JS.read_text(encoding="utf-8") if MODELS_JS.is_file() else ""
    scene_txt = SCENE_JS.read_text(encoding="utf-8") if SCENE_JS.is_file() else ""
    render_txt = RENDER_BANNERS.read_text(encoding="utf-8") if RENDER_BANNERS.is_file() else ""
    js_all = parts_txt + "\n" + models_txt + "\n" + scene_txt + "\n" + render_txt

    check('id="aloo-cats-canvas"' in html_txt, "HTML mounts #aloo-cats-canvas", "missing #aloo-cats-canvas")
    check('../assets/js/aloo-cats-scene.js' in html_txt, "HTML loads aloo-cats-scene.js module", "missing aloo-cats-scene.js tag")
    check("from 'three'" in models_txt and "from 'three'" in scene_txt, "3D cat modules use pinned three import", "missing three import")

    body_part = html_txt.split("<body>", 1)[1] if "<body>" in html_txt else html_txt
    banner_block = body_part.split('id="what-it-is"', 1)[0] if 'id="what-it-is"' in body_part else body_part
    pasted_img = re.search(r'<img\b|aloo-mannu-banner|IMG_7267|\.jpe?g\b', banner_block, re.I)
    check(pasted_img is None and not re.search(r'\.jpe?g\b|IMG_7267', js_all, re.I),
          "banner uses 100% coded 3D geometry/canvas textures (zero pasted photos)",
          "banner references a pasted photo instead of pure 3D code")

    check("Good conversations start here." in html_txt, "tagline 'Good conversations start here.' in HTML overlay", "missing tagline")
    check('class="aloo-banner-title"' in html_txt and ">Aloo<" in html_txt and ">Mannu<" in html_txt,
          "stacked cream serif Aloo / Mannu HTML display overlay present", "missing Aloo / Mannu overlay")
    check("buildLeftCat" in models_txt and "buildRightCat" in models_txt and "buildCreamLedge" in models_txt,
          "both cats and cream ledge modeled in aloo-cats-models.js", "missing cat/ledge builders")
    check('"ow ow"' in scene_txt and '"meh"' in scene_txt,
          "call-and-answer speech bubbles ('ow ow' and 'meh') implemented", "missing speech bubble text")

    forbidden_cat_label = re.compile(
        r'\b(?:left\s+cat\s+is\s+(?:aloo|mannu)|right\s+cat\s+is\s+(?:aloo|mannu)|'
        r'aloo\s*\((?:left|right|smaller|taller)\)|mannu\s*\((?:left|right|smaller|taller)\))\b',
        re.I,
    )
    check(not forbidden_cat_label.search(html_txt) and not forbidden_cat_label.search(js_all),
          "neither cat is labeled as Aloo or Mannu", "found forbidden cat name assignment")
    check(FORBIDDEN_BYTES.search(js_all.encode("utf-8")) is None,
          "scene & render script free of internal Lab names/paths", "internal name/path leaked in scene or render script")

    check("prefers-reduced-motion: reduce" in scene_txt and "renderFrame(" in scene_txt,
          "aloo-cats-scene.js renders still frame under prefers-reduced-motion: reduce", "missing reduced-motion still frame")
    pause_btn = re.search(r'<button[^>]*data-cats-motion-toggle[^>]*>', html_txt)
    check(pause_btn is not None and "aria-pressed" not in pause_btn.group(0),
          "WCAG 2.2.2 Pause/Play button present without aria-pressed", "invalid Pause/Play button")
    check(".aloo-banner" in css_txt and "color-scheme: dark" in css_txt,
          "product.css scopes color-scheme: dark with explicit colors on .aloo-banner", "missing color-scheme: dark")

    verify_banner_png(README_PNG, "README header PNG", (1280, 560))
    verify_banner_png(SOCIAL_PNG, "Social preview PNG", (1280, 640))

    proc = subprocess.run([sys.executable, str(ROOT / "tests" / "check-product-pages.py")], cwd=str(ROOT), capture_output=True, text=True)
    check(proc.returncode == 0, "tests/check-product-pages.py passes all 12 pages & unlinked invariants",
          f"tests/check-product-pages.py failed:\n{proc.stdout[-600:]}\n{proc.stderr[-400:]}")

    if failures:
        print(f"\nFAILED: {len(failures)} check(s) failed")
        return 1
    print("\nPASS: all 3D Aloo Mannu Three.js checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
