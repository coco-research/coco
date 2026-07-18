# SFX Analysis Summary

Source: [Kenney](https://kenney.nl/).

Use this as planning guidance for choosing tasteful SFX. Prefer low/medium high-frequency risk sounds for polished videos; reserve bright/high-risk files for tiny accents, chaotic tones, or deliberate glitches.

## Signal Guide

- `brightness`: warm / balanced / bright, based on spectral centroid and high-frequency energy.
- `highFrequencyRisk`: low / medium / high. High-risk SFX can feel sharp, hissy, clicky, or fatiguing if repeated.
- `brightBurden`: high-frequency energy weighted by level and duration. This separates sustained glassy ringing from short clicks.
- `highActiveDuration`: how long bright energy stays active above a useful level.
- `envelopeShape`: transient / textured / continuous. Continuous bright sounds are more fatiguing than sparse textured sounds.
- `transient.sharpness`: higher values feel clickier or more percussive.
- `duration`: short sounds work for UI and typing; longer sounds work for reveals and transitions.

## Safest General Picks

- `impact/impactSoft_medium_001.ogg` — 0.18s, warm, low HF risk, transient; use for hard transition, major reveal
- `impact/impactSoft_medium_004.ogg` — 0.15s, warm, low HF risk, transient; use for hard transition, major reveal
- `impact/impactSoft_medium_002.ogg` — 0.14s, warm, low HF risk, transient; use for hard transition, major reveal
- `interface/bong_001.ogg` — 0.12s, warm, low HF risk, textured; use for general accent
- `impact/impactSoft_medium_003.ogg` — 0.14s, warm, low HF risk, textured; use for hard transition, major reveal
- `impact/impactSoft_medium_000.ogg` — 0.12s, warm, low HF risk, textured; use for hard transition, major reveal
- `interface/click_003.ogg` — 0.01s, balanced, low HF risk, continuous; use for button press, selection, simulated user action
- `interface/click_002.ogg` — 0.01s, balanced, low HF risk, continuous; use for button press, selection, simulated user action
- `interface/click_005.ogg` — 0.01s, balanced, low HF risk, continuous; use for button press, selection, simulated user action
- `ui/click2.ogg` — 0.06s, balanced, low HF risk, continuous; use for button press, selection, simulated user action
- `ui/rollover2.ogg` — 0.06s, balanced, low HF risk, continuous; use for general accent
- `interface/glitch_002.ogg` — 0.03s, bright, low HF risk, continuous; use for chaotic accent, comedic interruption, tiny accent only
- `impact/impactSoft_heavy_003.ogg` — 0.54s, warm, medium HF risk, transient; use for hard transition, major reveal
- `impact/impactSoft_heavy_004.ogg` — 0.50s, warm, medium HF risk, transient; use for hard transition, major reveal
- `impact/impactSoft_heavy_002.ogg` — 0.57s, warm, medium HF risk, transient; use for hard transition, major reveal
- `impact/impactSoft_heavy_001.ogg` — 0.57s, warm, medium HF risk, transient; use for hard transition, major reveal
- `impact/impactSoft_heavy_000.ogg` — 0.51s, warm, medium HF risk, transient; use for hard transition, major reveal
- `impact/footstep_wood_004.ogg` — 0.25s, warm, medium HF risk, transient; use for general accent
- `impact/footstep_wood_002.ogg` — 0.25s, warm, medium HF risk, transient; use for general accent
- `impact/footstep_wood_000.ogg` — 0.25s, warm, medium HF risk, transient; use for general accent
- `impact/footstep_wood_001.ogg` — 0.25s, warm, medium HF risk, transient; use for general accent
- `impact/impactWood_medium_003.ogg` — 0.33s, warm, medium HF risk, transient; use for hard transition, major reveal
- `impact/impactWood_medium_001.ogg` — 0.33s, warm, medium HF risk, transient; use for hard transition, major reveal
- `impact/impactWood_medium_000.ogg` — 0.33s, warm, medium HF risk, transient; use for hard transition, major reveal

## Lower-Risk Picks By Use Case

- button press: `interface/click_003.ogg` (low), `interface/click_002.ogg` (low), `interface/click_005.ogg` (low), `ui/click2.ogg` (low), `interface/click_001.ogg` (medium)
- selection: `interface/click_003.ogg` (low), `interface/click_002.ogg` (low), `interface/click_005.ogg` (low), `ui/click2.ogg` (low), `interface/click_001.ogg` (medium)
- toggle: `interface/switch_007.ogg` (medium), `interface/switch_002.ogg` (medium), `interface/switch_006.ogg` (medium), `interface/switch_005.ogg` (medium), `ui/switch11.ogg` (medium)
- card reveal: `casino/card-slide-1.ogg` (medium), `casino/card-place-1.ogg` (high), `casino/card-fan-2.ogg` (high), `casino/card-slide-8.ogg` (high), `casino/card-slide-3.ogg` (high)
- swipe: `casino/card-slide-1.ogg` (medium), `casino/card-place-1.ogg` (high), `casino/card-fan-2.ogg` (high), `casino/card-slide-8.ogg` (high), `casino/card-slide-3.ogg` (high)
- sequential item: `casino/card-slide-1.ogg` (medium), `casino/card-place-1.ogg` (high), `casino/card-fan-2.ogg` (high), `casino/card-slide-8.ogg` (high), `casino/card-slide-3.ogg` (high)
- panel opening: `casino/cards-pack-open-1.ogg` (high), `casino/cards-pack-open-2.ogg` (high)
- soft reveal: `casino/cards-pack-open-1.ogg` (high), `casino/cards-pack-open-2.ogg` (high)
- success: `impact/impactBell_heavy_000.ogg` (medium), `impact/impactBell_heavy_003.ogg` (medium), `impact/impactBell_heavy_004.ogg` (medium)
- logo payoff: `impact/impactBell_heavy_000.ogg` (medium), `impact/impactBell_heavy_003.ogg` (medium), `impact/impactBell_heavy_004.ogg` (medium)
- reveal confirmation: `impact/impactBell_heavy_000.ogg` (medium), `impact/impactBell_heavy_003.ogg` (medium), `impact/impactBell_heavy_004.ogg` (medium)
- major reveal: `impact/impactSoft_medium_001.ogg` (low), `impact/impactSoft_medium_004.ogg` (low), `impact/impactSoft_medium_002.ogg` (low), `impact/impactSoft_medium_003.ogg` (low), `impact/impactSoft_medium_000.ogg` (low)
- hard transition: `impact/impactSoft_medium_001.ogg` (low), `impact/impactSoft_medium_004.ogg` (low), `impact/impactSoft_medium_002.ogg` (low), `impact/impactSoft_medium_003.ogg` (low), `impact/impactSoft_medium_000.ogg` (low)
- chaotic accent: `interface/glitch_002.ogg` (low), `interface/error_005.ogg` (medium), `interface/error_006.ogg` (medium), `interface/glitch_004.ogg` (medium)

## Family Summary

- `casino/`: 51 files; HF risk low/medium/high = 0/10/41; avg high-frequency energy 0.59
- `impact/`: 109 files; HF risk low/medium/high = 5/104/0; avg high-frequency energy 0.08
- `interface/`: 20 files; HF risk low/medium/high = 5/14/1; avg high-frequency energy 0.25
- `ui/`: 48 files; HF risk low/medium/high = 2/14/32; avg high-frequency energy 0.57

## Selection Rules

- Prefer low-risk SFX for repeated UI actions, text ticks, and dense sequences.
- Use medium-risk SFX for isolated reveals or when the motion needs a crisp edge.
- Avoid high-risk SFX for repeated ticks, long sequences, or polished/deadpan tones.
- Treat continuous bright SFX as more fatiguing than sparse/textured bright SFX.
- If using a bright SFX, keep it short, quiet, and isolated.
- Match SFX timing to the visual landing or start depending on the gesture: clicks at press/start, reveals at resolution/payoff.
