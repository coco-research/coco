# Credits & Inspirations

CoCo stands on the shoulders of excellent open-source work. This file credits every project whose code, patterns, or ideas shaped this repo. If you find an influence that isn't listed, that's a bug — please open an issue or PR.

## Bundled / adapted systems

| Project | What CoCo took | Upstream | License |
|---|---|---|---|
| **Superpowers** by Jesse Vincent (obra) | The core engineering-discipline skill set bundled here (brainstorming, systematic-debugging, test-driven-development, writing-plans, executing-plans, using-git-worktrees, code-review flows, verification-before-completion, writing-skills, and the `using-superpowers` meta-skill) | https://github.com/obra/superpowers | See upstream |
| **GSD — Get Shit Done** | The full GSD orchestration bundle (`systems/gsd/`: 68 skills + 24 agents for phase planning, atomic execution, verification gates) | https://github.com/gsd-build/get-shit-done | See upstream |
| **ai-website-cloner-template** by JCodesMore | The site-cloning structure behind the clone-website skill | https://github.com/JCodesMore/ai-website-cloner-template | See upstream |
| **agents.md** community | The vendor-neutral agent context standard CoCo's adapters follow | https://agents.md/ | — |
| **brag** by Shunit Haviv | The `coco-ads` launch-video skill — flow, tone presets, storyboard rubric, and bundled audio (vendored and re-voiced in CoCo's style) | https://github.com/latent-spaces/brag | No license published |
| **HyperFrames** by HeyGen | The HTML-composition + local render engine `coco-ads` drives via `npx hyperframes` (lint / validate / render) | https://www.npmjs.com/package/hyperframes | See upstream |
| **"Happy Beats / Business Moves"** by ende.app | Bundled music beds used by `coco-ads` | https://ende.app | See upstream |
| **Kenney.nl** | Bundled CC0 sound effects used by `coco-ads` | https://kenney.nl | CC0 (public domain) |

## Feature inspirations

| Project | What CoCo took | Upstream | License |
|---|---|---|---|
| **synthteam** by Nick Winder | The structured multi-agent **debate protocol** that powers `--debate` deliberation in the Superintelligence council generators (re-implemented from the concept; no upstream code copied) | https://github.com/nickwinder/synthteam | No license published |
| **taste-skill** by Leonxlnx | Design-taste enforcement skills (`design-taste-frontend`, `redesign-existing-projects`) — *vendoring in progress* | https://github.com/leonxlnx/taste-skill | MIT |
| **CLI-Anything** by HKUDS | The "wrap any CLI into a structured agent skill" methodology — *adoption in progress* | https://github.com/HKUDS/CLI-Anything | Apache-2.0 |

## How we credit

- Vendored code keeps its upstream license and attribution in place.
- Re-implemented ideas get named credit here even when no code was copied.
- Evaluated-but-not-adopted projects aren't listed; influence means something shipped.
