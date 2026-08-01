# Credits & Inspirations

CoCo stands on the shoulders of excellent open-source work. This file credits every project whose code, patterns, or ideas shaped this repo. If you find an influence that isn't listed, that's a bug — please open an issue or PR.

## Bundled / adapted systems

| Project | What CoCo took | Upstream | License |
|---|---|---|---|
| **Superpowers** by Jesse Vincent (obra) | The core engineering-discipline skill set bundled here (brainstorming, systematic-debugging, test-driven-development, writing-plans, executing-plans, using-git-worktrees, code-review flows, verification-before-completion, writing-skills, and the `using-superpowers` meta-skill) | https://github.com/obra/superpowers | See upstream |
| **GSD — Get Shit Done** | The full GSD orchestration bundle (`systems/gsd/`: 68 skills + 24 agents for phase planning, atomic execution, verification gates) | https://github.com/gsd-build/get-shit-done | See upstream |
| **humanizer** by Siqi Chen | The `humanizer` skill — detects and rewrites signs of AI-generated text (vendored, pinned at v2.8.0; upstream is at v2.9.x, ordinary version drift) | https://github.com/blader/humanizer | MIT |
| **andrej-karpathy-skills** by forrestchang | The `karpathy-guidelines` skill — behavioral guidelines to reduce common LLM coding mistakes | https://github.com/multica-ai/andrej-karpathy-skills | MIT (per the plugin manifest; upstream has no LICENSE file, so no copyright line is quoted — see `skills/karpathy-guidelines/LICENSE`) |
| **visual-explainer** by nicobailon | The `visual-explainer` skill — generates self-contained HTML diagrams, reviews, plans, recaps, and slide decks | https://github.com/nicobailon/visual-explainer | MIT |
| **ai-website-cloner-template** by JCodesMore | The site-cloning structure behind the clone-website skill | https://github.com/JCodesMore/ai-website-cloner-template | See upstream |
| **agents.md** community | The vendor-neutral agent context standard CoCo's adapters follow | https://agents.md/ | — |
| **brag** by Shunit Haviv Hakimi | The `coco-ads` launch-video skill — flow, tone presets, storyboard rubric, and bundled audio (vendored and re-voiced in CoCo's style); upstream MIT notice retained at `skills/coco-ads/LICENSE` | https://github.com/latent-spaces/brag | MIT (Copyright (c) 2026 Shunit Haviv Hakimi) |
| **HyperFrames** by HeyGen | The HTML-composition + local render engine `coco-ads` drives via `npx hyperframes` (lint / validate / render) | https://www.npmjs.com/package/hyperframes | See upstream |
| **"Happy Beats / Business Moves"** by ende.app | Bundled music beds used by `coco-ads` | https://ende.app | See upstream |
| **Kenney.nl** | Bundled CC0 sound effects used by `coco-ads` | https://kenney.nl | CC0 (public domain) |

## Feature inspirations

| Project | What CoCo took | Upstream | License |
|---|---|---|---|
| **synthteam** by Nick Winder | The structured multi-agent **debate protocol** that powers `--debate` deliberation in the Superintelligence council generators (re-implemented from the concept; no upstream code copied) | https://github.com/nickwinder/synthteam | No license published |
| **taste-skill** by Leonxlnx | Design-taste enforcement skills (`design-taste-frontend`, `redesign-existing-projects`) — *vendoring in progress* | https://github.com/leonxlnx/taste-skill | MIT |
| **CLI-Anything** by HKUDS | The "wrap any CLI into a structured agent skill" methodology — *adoption in progress* | https://github.com/HKUDS/CLI-Anything | Apache-2.0 |
| **Vercel Engineering** | `vercel-react-best-practices` — React/Next.js performance guidelines (57 rules) built on Vercel's public engineering guidance | https://vercel.com | See upstream |
| **web-interface-guidelines** by Vercel Labs | `web-design-guidelines` — reviews UI code against the Web Interface Guidelines | https://github.com/vercel-labs/web-interface-guidelines | MIT |

## Reference material & SDKs

Some skills teach or wrap third-party platforms. These are original write-ups built on public documentation; the platforms, SDKs, and their docs belong to their owners.

| Source | Skill(s) | Upstream |
|---|---|---|
| **Apple** — Liquid Glass design system (WWDC 2025) | `axiom-liquid-glass`, `swiftui-liquid-glass` | https://developer.apple.com |
| **OpenAI** — Agents SDK, Realtime / Chat / Batch APIs, Whisper | `openai-agents`, `openai-api`, `openai-apps-mcp`, `openai-whisper` | https://platform.openai.com/docs |
| **Microsoft** — Agent Lightning (RL agent training) | `agent-lightning` | https://github.com/microsoft/agent-lightning |
| **Cognee** by topoteretes (Apache-2.0) — knowledge-graph memory engine the `systems/cognee/` bundle wraps over its local HTTP API (no upstream code vendored; the bundle's skills are CoCo's own write-ups) | `cognee`, `cognee-store`, `cognee-recall` | https://github.com/topoteretes/cognee |

## How we credit

- Vendored code keeps its upstream license and attribution in place.
- Re-implemented ideas get named credit here even when no code was copied.
- Evaluated-but-not-adopted projects aren't listed; influence means something shipped.
