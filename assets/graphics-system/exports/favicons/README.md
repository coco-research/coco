# cocoresearch.org favicon set — derived from assets/logo.svg

Card t_0e14a6c0 (design derivation). Audit source:
`assets/graphics-system/FAVICON-ICON-AUDIT.md` (P4, finding #1).
Colors are NOT new decisions: mark + gradient + canvas are `assets/logo.svg`
verbatim (see `favicon.svg` header); accent ruling t_c431fdb6 c286 untouched.
Nia glance: form factor only.

## Contents (this directory)

| file | size | role |
|---|---|---|
| `favicon.svg` | 512 viewBox | modern browsers (`rel="icon" type="image/svg+xml"`) |
| `favicon.ico` | 16+32+48 frames | legacy fallback at site root `/favicon.ico` |
| `favicon-32x32.png` | 32×32 | `rel="icon"` PNG fallback |
| `apple-touch-icon.png` | 180×180 | iOS home screen — full-bleed square, opaque; iOS applies its own mask |
| `icon-512x512.png` | 512×512 | PWA-grade raster master (not wired by P4) |
| `site.webmanifest` | — | install identity + theme colors (`#0A0F1F`) |

Regenerate: `scripts/export_favicons.sh` (librsvg 2.62.x pinned for every
PNG, ImageMagick only for the multi-frame `.ico` container).

## Deployment targets (per pike's wiring spec, t_1d2598c5 comment 2026-09-02)

Pike owns the site wiring (stacked on site PR #131). Served locations:

| file (here) | served as | surface |
|---|---|---|
| `favicon.svg` | `/assets/site/favicon.svg` | swaps into #131's SVG slot (file swap, no head churn) |
| `favicon-32x32.png` | `/assets/site/favicon-32.png` | PNG fallback link on both index.html + coco/ |
| `site.webmanifest` | `/assets/site/site.webmanifest` | manifest link; src paths inside match the paths above |
| `favicon.ico` | `/favicon.ico` | site root (card acceptance: must 200; legacy fallback) |
| `apple-touch-icon.png` | `/apple-touch-icon.png` | site root (acceptance: must 200; legacy iOS fallback) |
| `icon-512x512.png` | (not wired by P4) | PWA-grade master, available for future manifest sizes |

Reference head shape (pike's PR is authoritative):

```html
<link rel="icon" href="/favicon.ico">
<link rel="icon" type="image/svg+xml" href="/assets/site/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/site/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/assets/site/site.webmanifest">
<meta name="theme-color" content="#0A0F1F">
```

## Verification record (this card)

- Contrast gate `scripts/contrast_gate_svg.py`: ALL PASS, exit 0, 0 warnings
  (favicon.svg is text-free by design — no <text> survives favicon sizes).
- Vision review, 3 passes (r2 caught the apple-touch pre-rounding defect —
  removed per Apple guidance; r3 clean): mark faithful/centered/unclipped at
  512+180, legible at 64/32, opaque square corners on touch icon.
- Pixel-measured: mark centered at every size (equal L/R margins), pad-not-crop.
- Known limit: the 16px `.ico` frame is inherently soft (straight downscale of
  the two-arc mark). A simplified 16px glyph would be a NEW brand decision →
  out of scope here; fold into t_bd462e10 (on-brand icon redesign) if wanted.
