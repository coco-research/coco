# Step 4: Validate, render, and deliver

## Validate

```bash
cd coco-ads-output/composition
npx hyperframes lint       # static checks: track overlaps, unregistered timelines, missing ids
npx hyperframes validate   # loads in headless Chrome: WCAG contrast audit + console errors
npx hyperframes inspect    # text / container overflow across the timeline
```

Fix all errors. The contrast warnings come from `validate` (`lint` is static-only): fix anything below 3:1 for large text or 4.5:1 for body text. Accept borderline cases (3:1–4:1) — brag videos are not accessibility documents, but text must be legible. `inspect` backstops the "keep all text readable" creative law — fix any reported overflow.

For a visual gut-check before rendering, optionally capture key frames:

```bash
npx hyperframes snapshot   # PNG key frames (adds Gemini frame analysis when GEMINI_API_KEY is set)
```

## Preview

```bash
npx hyperframes preview
```

Tell the user the preview is running and give them the localhost URL. Invite them to check it before rendering. The preview hot-reloads on file changes.

If the user approves or asks to render:

## Render

```bash
npx hyperframes render --output ../coco-ads.mp4
```

This outputs to `coco-ads-output/coco-ads.mp4` (one level up from the composition directory).

For a faster iteration render:
```bash
npx hyperframes render --quality draft --output ../coco-ads.mp4
```

For final delivery:
```bash
npx hyperframes render --quality high --output ../coco-ads.mp4
```

## Write share copy

Write `coco-ads-output/share-copy.txt`.

The share copy should be:
- One to three sentences max
- Postable as-is to Twitter/X, LinkedIn, or Discord
- Specific to the project — no generic "excited to share" language
- Tone-matched to the brag video

`share-copy.txt` is the canonical single caption. Do not put multi-platform variants, long launch notes, or Product Hunt copy in this file.

If variants are useful, write them to a separate optional file:

```text
coco-ads-output/share-copy-variants.md
```

### Share copy by tone

**`default`:**
```
Made [App Name]. It's [what it does, in the project's own absurd terms].
[The best line from the product.]
```

**`polished`:**
```
Introducing [App Name]: [clean one-liner from the site].
Built with [stack if notable].
```

**`yc-parody`:**
```
We built [App Name] to solve [problem stated completely seriously].
[Deadpan feature or stat.]
```

**`chaotic`:**
```
[ALL CAPS CLAIM].
[App Name] is [wildly overstated description].
Link below.
```

**`deadpan`:**
```
I made [App Name].
It [what it does].
```

**`cinematic`:**
```
[App Name].
[Tagline from the site, verbatim or lightly adapted.]
```

**`app-store`:**
```
[App Name] is now live.
[Feature 1], [Feature 2], and [Feature 3] — all in one place.
```

### Example: Taxi for Taxis

```
Every day, taxis carry us. But who carries the taxis?
Taxi for Taxis: the ride-hailing app for ride-hailing assets.
Available in 12 metros.
```

## Final output structure

After this step, `coco-ads-output/` should contain:

```
coco-ads-output/
  brag.mp4                — the rendered video
  coco-ads-plan.md            — the plan and storyboard
  composition-brief.md    — the Hyperframes handoff brief
  share-copy.txt          — the share caption
  composition/            — the Hyperframes project
    index.html
    DESIGN.md
    ...
```

## Telling the user

After everything is done, tell the user:
- Where the video is (`coco-ads-output/coco-ads.mp4`)
- Where the share copy is
- One sentence on what the video does creatively
- Optionally: offer to re-roll a scene, change tone, or try a different angle
