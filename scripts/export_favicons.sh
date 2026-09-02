#!/usr/bin/env bash
# export_favicons.sh — derive the cocoresearch.org favicon set from
# assets/graphics-system/exports/favicons/favicon.svg (the logo.svg mark,
# square-padded). Card t_0e14a6c0. DERIVATION ONLY.
#
# Renderer discipline, same as the rest of the graphics system:
#   • rsvg-convert (librsvg) 2.62.x pinned for every PNG — the same renderer
#     as scripts/export_svg.sh, so the mark renders identically everywhere.
#   • ImageMagick is used ONLY for (a) the .ico container (multi-size) and
#     (b) the apple-touch roundrect mask — iOS composites its own mask on
#     transparent input; the artwork pixels still come from librsvg output.
#
# Usage: scripts/export_favicons.sh
set -euo pipefail

REQ_MAJOR=2
REQ_MINOR=62
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(cd "$HERE/.." && pwd)/assets/graphics-system/exports/favicons"
SRC="$OUT/favicon.svg"

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "error: rsvg-convert not found (brew install librsvg)" >&2; exit 1
fi
ver="$(rsvg-convert --version)"
major="$(printf '%s' "$ver" | awk 'NR==1{print $3}' | cut -d. -f1)"
minor="$(printf '%s' "$ver" | awk 'NR==1{print $3}' | cut -d. -f2)"
if [ "$major" != "$REQ_MAJOR" ] || [ "$minor" != "$REQ_MINOR" ]; then
  echo "error: pinned librsvg ${REQ_MAJOR}.${REQ_MINOR}.x required, found: $ver" >&2; exit 1
fi
if ! command -v magick >/dev/null 2>&1; then
  echo "error: magick not found (brew install imagemagick)" >&2; exit 1
fi

cd "$OUT"

# --- straight rasters from the SVG (full-bleed square canvas) ---------------
rsvg-convert "$SRC" -w 32  -h 32  -o favicon-32x32.png
rsvg-convert "$SRC" -w 180 -h 180 -o apple-touch-icon.png
rsvg-convert "$SRC" -w 512 -h 512 -o icon-512x512.png

# --- apple-touch-icon: SHIPPED FULL-BLEED SQUARE, OPAQUE ----------------------
# Per Apple's icon guidance: iOS applies its own superellipse mask to opaque
# square icons. Pre-rounding (or transparency) causes double-masking /
# black-corner behavior. No post-processing — straight librsvg output.

# --- .ico fallback: 16/32/48 in one container --------------------------------
magick \
  <(rsvg-convert "$SRC" -w 16 -h 16) \
  <(rsvg-convert "$SRC" -w 32 -h 32) \
  <(rsvg-convert "$SRC" -w 48 -h 48) \
  favicon.ico

printf 'favicons exported to %s\n' "${OUT#$HOME/}"
