# Modifications to vendored HyperFrames files

`systems/hyperframes/` is vendored from [`heygen-com/hyperframes`](https://github.com/heygen-com/hyperframes) under the Apache License 2.0 (see [`LICENSE`](LICENSE)). Section 4(b) of that licence requires every modified file to carry a prominent notice that it was changed. This file is the full list of those changes, and each modified source file also carries a notice of its own.

Everything not listed here is as vendored from upstream.

## 2026-10-04: media-use telemetry is off by default

| | |
|---|---|
| **File** | `skills/media-use/scripts/lib/telemetry.mjs` |
| **Change** | `track()` now returns immediately unless the environment variable `COCO_HYPERFRAMES_TELEMETRY` is exactly `1`. When it is unset, `track()` sends nothing over the network, prints no notice, and does not read or write `~/.hyperframes/config.json`. When it is `1`, behaviour is the upstream behaviour, and the upstream opt-outs (`DO_NOT_TRACK`, `HYPERFRAMES_NO_TELEMETRY`, CI) still apply. A notice comment was added at the top of the file. No other line of the file changed. |
| **Reason** | Upstream sends usage events to PostHog unless the user opts out. Coco ships this bundle as an optional pack that must not phone home by default, so the default is inverted: telemetry is opt-in. |
| **Files edited to match** | `skills/media-use/scripts/lib/telemetry.test.mjs` (the "tracking allowed" helper now sets the variable, an existing opt-out test sets it so it still tests the opt-outs, and two new tests prove that `fetch` is never called when it is unset and is called when it is `1`). `skills/media-use/scripts/resolve.test.mjs` (the one test that proves the interception seam sets the variable for its child process). |

Notes:

- `skills/media-use/references/meta.md` and `telemetry-dashboard.md` still describe the upstream behaviour (opt-out). In this bundle, telemetry from media-use is off unless `COCO_HYPERFRAMES_TELEMETRY=1` is set.
- The separate `hyperframes` npm CLI (run with `npx hyperframes`) is not vendored here and is not changed by this edit. It manages its own telemetry (`npx hyperframes telemetry status`, `npx hyperframes telemetry disable`).

## 2026-09-14: skill descriptions rewritten (e75f220)

| | |
|---|---|
| **Files** | `skills/motion-graphics/SKILL.md`, `skills/music-to-video/SKILL.md`, `skills/pr-to-video/SKILL.md`, `skills/remotion-to-hyperframes/SKILL.md`, `skills/slideshow/SKILL.md`, `skills/website-to-video/SKILL.md` |
| **Change** | The `description` in each file's front matter was rewritten in commit `e75f220` (2026-09-14). The same commit also changed a few body lines in three files: `music-to-video` (one sentence in the opening paragraph), `slideshow` (two copies of the presenter-notes paragraph and one reference path, `skills/slideshow/references/standalone-harness.md` to `references/standalone-harness.md`) and `website-to-video` (a deprecation note pointing to `/product-launch-video`, and two reference links moved to `../hyperframes-animation/`). Each file carries the notice `Modified by Coco, 2026-09-14: description rewritten. See MODIFICATIONS.md.` on the first line after its front matter (a line above the front matter would break the skill loader). |
| **Reason** | Coco #168 rewrote skill descriptions repo-wide so each one says when to use the skill (the trigger), not only what it is: a description is the loader's only signal for whether to open the file. |
