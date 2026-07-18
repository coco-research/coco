---
name: coco-ads
description: Turn the project you just shipped into a short, polished, shareable launch video (an "ad") using HyperFrames. Use when someone says "/coco-ads", "make a launch video", "brag about this", "turn this into a promo", "make an ad for this", or wants to share what they built. Reads the project code directly — no live URL or screenshots needed. Renders locally.
argument-hint: "[--tone <preset|freeform>] [--format landscape|vertical|square] [--duration <s>] [--no-music] [--title <name>]"
user-invocable: true
---

# /coco-ads — launch videos from your repo

You built it. Now let CoCo make the ad.

`/coco-ads` turns the current project into a short (15–25s), polished, shareable launch video using the HyperFrames toolchain, rendered **locally**. It is narrow, opinionated, and fast.

> **Credit / lineage.** This skill adapts the launch-video flow from [**brag** by Shunit Haviv](https://github.com/latent-spaces/brag) and runs on the [**HyperFrames**](https://www.npmjs.com/package/hyperframes) HTML-composition + render engine by HeyGen. Bundled music is "Happy Beats / Business Moves" by ende.app; bundled SFX are CC0 (Kenney.nl). See [`CREDITS.md`](../../CREDITS.md). Re-implemented in CoCo's voice with attribution; upstream `brag` ships without an explicit license.

## Requirements

The render path is fully local (HeyGen cloud/Lambda paths are never used). It needs:

- **Node 22+** and **FFmpeg** on `PATH`.
- The **HyperFrames** CLI, run via `npx hyperframes …` (auto-fetched on first use). The composition skills install once with `npx hyperframes skills`.
- A quick environment check: `npx hyperframes doctor` (Chrome headless-shell + FFmpeg). "Docker not running" is fine — Docker is only for distributed cloud renders, which this skill does not use.

No data leaves the machine on the default render path. If `GEMINI_API_KEY` is set, the optional snapshot frame-analysis would call Gemini — keep it off (`--describe false`) when bragging about anything you would not paste in public.

## What this skill does

1. Reads the current project code to understand the app.
2. Plans a short concept specific to this project.
3. Scripts and storyboards the video.
4. Hands a focused composition brief to HyperFrames.
5. Validates, renders locally, and writes share copy.

## Parsing the invocation

```
/coco-ads
/coco-ads --tone chaotic
/coco-ads --tone polished --format vertical
/coco-ads this. Make it feel like a ridiculous startup launch.
```

| Option | Values | Default |
|---|---|---|
| `--tone` | preset or freeform description | inferred |
| `--format` | `landscape`, `vertical`, `square` | `landscape` |
| `--duration` | seconds | auto (15-25s) |
| `--no-music` | flag | music on |
| `--no-sfx` | flag | sfx on |
| `--title` | string | inferred from project |

Tone can be a preset (`default`, `polished`, `yc-parody`, `chaotic`, `deadpan`, `cinematic`, `app-store`) or a creative direction such as "fake Series A launch from 2016". When the user gives freeform direction, map it to the nearest preset for pacing and structure, but preserve the user's direction in the plan and composition brief.

---

## Output directory

By default, output goes to `coco-ads-output/`. To avoid overwriting previous runs, use a timestamped directory (`coco-ads-output-YYYY-MM-DD-HHmmss/`) when the user asks for a new run or one already exists. Generate the timestamp once at the start of the run and use it consistently for the plan, brief, composition, render, and share copy. Keep `coco-ads-output/` out of version control.

---

## Step 1: Inspect the project

**Read:** [references/step-1-inspect.md](references/step-1-inspect.md)

Scan the project directory and extract what you need to plan the video.

**Gate:** You can answer all 9 questions in the planning rubric.

---

## Step 2: Plan and storyboard

**Read:** [references/step-2-plan.md](references/step-2-plan.md)

Write `<output-dir>/coco-ads-plan.md`. Answer the planning rubric, commit to a creative angle, and write the beat-by-beat storyboard (scenes, text, timing, transitions, SFX cues). Include a compact `Music cue guidance` section when music is selected.

**Gate:** `<output-dir>/coco-ads-plan.md` exists with a full storyboard; scene durations sum to 15–25 seconds.

---

## Step 3: Hand off to HyperFrames

**Read:** the installed HyperFrames composition skills (`npx hyperframes skills` if absent), then [references/step-3-compose.md](references/step-3-compose.md) and [references/audio.md](references/audio.md).

Write `<output-dir>/composition-brief.md`, then build the composition in `<output-dir>/composition/`. `/coco-ads` owns product angle, source material, storyboard, tone, format, audio selection, and delivery; HyperFrames owns the concrete composition structure, animation mechanics, and render workflow.

**Gate:** `npx hyperframes lint` passes with zero errors inside `<output-dir>/composition/`.

---

## Step 4: Validate, render, and deliver

**Read:** [references/step-4-deliver.md](references/step-4-deliver.md)

Validate (`npx hyperframes validate` + `inspect`), render to `<output-dir>/brag.mp4`, and write `<output-dir>/share-copy.txt`.

**Gate:** the rendered MP4 exists and share copy is written.

---

## Tone system

Seven presets ship with `/coco-ads`. Each changes scripting energy, pacing, typography personality, and transition style. Presets are defaults, not limits — always allow a freeform creative direction to refine or override.

Full definitions: [references/tones.md](references/tones.md)

| Tone | Energy | One-liner |
|---|---|---|
| `default` | Playful, clean, postable | The good-vibes default |
| `polished` | Serious, elegant | For projects that are not jokes |
| `yc-parody` | Deadpan startup energy | Fake seriousness applied to absurd projects |
| `chaotic` | Fast, loud, aggressive | Over-the-top and unhinged |
| `deadpan` | Calm, dry, understated | The joke is that nothing is a joke |
| `cinematic` | Dramatic, trailer-scale | Big motion, bigger claims |
| `app-store` | Smooth, feature-card clean | Corporate but not boring |

---

## Creative laws

These apply to every video regardless of tone.

**Short.** 15–25 seconds. Not one second more without a reason.

**Readable.** Keep the pace high through motion and cuts, never by flashing text. Every line a viewer must read holds long enough to read it (short label ~0.8s settled; a sentence ~0.3s per word). Fast-in, then hold — never fast-in, then gone.

**Specific.** The video must feel like it was made for this exact project, not any project.

**Show the thing.** At least one scene must display actual UI, copy, or a key visual from the product. No abstract filler.

**No generic SaaS language.** "Streamline your workflow" is banned. Use the project's actual copy and claims.

**The hook is everything.** The first 2 seconds decide whether someone keeps watching. Plan the hook before anything else.

**Funny earns its place.** Humor should come from the project's absurdity, not from trying to be funny.

**Pattern:**
```
Hook (2-3s) → Reveal (2-4s) → 2-3 sharp highlights (5-12s) → Punchline/outro (2-4s)
```

Adapt this. The pattern is a starting shape, not a template.
