---
team_id: ai-super-intelligence
team_name: AI Super Intelligence Team
personas_count: 59
cells_count: 8
last_updated: 2026-05-28
schema_version: 1.0
---

# AI Super Intelligence Team — SKILL entry

Rijul's AI research + engineering brain trust **and decision-making partner**. 59 named personas drawn from the world's frontier model labs (US, UK, China, France), top AI universities, the open-source ecosystem, the independent-evaluation and AI-governance ecosystem, and product-history archetypes. Reusable across any CoCo-routed prompt — invoked by `/superintelligenceTeam-*` slash commands. The team's primary purpose is to **help take decisions**, not just review work after the fact — every cell carries a decision-relevant lens that convene synthesis explicitly draws on.

> **Status:** All three phases complete.
> - **Phase 1:** 49 personas across 8 cells (baseline roster + Marvin v2 panelists).
> - **Phase 2:** 10 priority additions from the [EXPANSION.md](EXPANSION.md) gap analysis (roster grew to 59).
> - **Phase 3:** 22 slash commands installed at `~/.claude/commands/superintelligenceTeam*.md` — orchestrator-first action surface plus explicit-override identity surface. See [Slash Commands](#slash-commands) section below.

This file is the user-facing entry point for the team. The machine source of truth is [`registry.json`](registry.json), regenerated from persona frontmatter by `python3 superintelligenceTeam/scripts/build_registry.py`.

## What this team is for

When a CoCo prompt is high-stakes enough to deserve a parallel review panel, the AI Super Intelligence Team plays the role of named external voices. Instead of "the panel said," every claim is attributed to a specific researcher with documented stances. This lets convene synthesis:

- Surface real disagreement (Hinton vs LeCun on existential risk; Karpathy vs Schulman on RL).
- Anchor stances to citable evidence (every public_stance in every persona has an `evidence_url`).
- Stay honest about who actually drove which decision (lead-driver vs validator vs specialist vs swing).

The 5-cell × 4-persona Marvin Memory v2 panel from May 26-27, 2026 was the **first consumer**. This team supersedes that roster: five of those panelists (Karpathy, Wei, LeCun, Tri Dao, Hyung Won Chung) continue here with their `v2_panel_attribution` records preserved. The rest of the Marvin v2 panel (memory / cloud / security / privacy personas) belong to future Super Intelligence Teams (Memory Systems, Cloud, Data, Compliance) and are not part of this AI-focused roster.

## Cells (8)

| Cell | Count | Focus | File |
|---|---|---|---|
| `frontier-labs-research` | 6 | CSO / co-founder tier at frontier labs (US, China, France) | [cells/frontier-labs-research.md](cells/frontier-labs-research.md) |
| `applied-ai-leadership` | 7 | Product / strategy founders shipping AI (incl. archetypes) | [cells/applied-ai-leadership.md](cells/applied-ai-leadership.md) |
| `model-architects` | 7 | Pretraining + scaling + model design + retrieval + open-source | [cells/model-architects.md](cells/model-architects.md) |
| `reasoning-rl-agents` | 7 | Post-training, RL, agentic systems, test-time compute | [cells/reasoning-rl-agents.md](cells/reasoning-rl-agents.md) |
| `alignment-interp-safety` | 9 | Alignment + mech interp + safety policy + independent evals + governance | [cells/alignment-interp-safety.md](cells/alignment-interp-safety.md) |
| `theory-science` | 9 | DL theory + science + Turing laureates + AI-for-science + common-sense | [cells/theory-science.md](cells/theory-science.md) |
| `multimodal-embodied` | 7 | Vision + diffusion + robotics + embodied | [cells/multimodal-embodied.md](cells/multimodal-embodied.md) |
| `systems-kernels-serving` | 7 | Kernels + serving + GPU + quantization + anti-NVIDIA silicon | [cells/systems-kernels-serving.md](cells/systems-kernels-serving.md) |

## Personas (59)

Listed by cell. Each has a YAML-frontmatter profile under `personas/<slug>.md` plus a research dump under `research/<slug>/`. **Bold** marks Phase 2 additions (built 2026-05-28 from `EXPANSION.md`).

**Frontier Labs Research (6):** [ilya-sutskever](personas/ilya-sutskever.md) · [dario-amodei](personas/dario-amodei.md) · [demis-hassabis](personas/demis-hassabis.md) · [jakub-pachocki](personas/jakub-pachocki.md) · **[liang-wenfeng](personas/liang-wenfeng.md)** · **[arthur-mensch](personas/arthur-mensch.md)**

**Applied AI Leadership (7):** [sam-altman](personas/sam-altman.md) · [mira-murati](personas/mira-murati.md) · [greg-brockman](personas/greg-brockman.md) · [aravind-srinivas](personas/aravind-srinivas.md) · [aidan-gomez](personas/aidan-gomez.md) · [elon-musk](personas/elon-musk.md) · [steve-jobs](personas/steve-jobs.md) *(archetype, deceased 2011)*

**Model Architects (7):** [andrej-karpathy](personas/andrej-karpathy.md) · [jared-kaplan](personas/jared-kaplan.md) · [noam-shazeer](personas/noam-shazeer.md) · [jason-wei](personas/jason-wei.md) · [sebastian-raschka](personas/sebastian-raschka.md) · **[patrick-lewis](personas/patrick-lewis.md)** · **[thomas-wolf](personas/thomas-wolf.md)**

**Reasoning, RL, Agents (7):** [john-schulman](personas/john-schulman.md) · **[noam-brown](personas/noam-brown.md)** · [hyung-won-chung](personas/hyung-won-chung.md) · [nathan-lambert](personas/nathan-lambert.md) · [barret-zoph](personas/barret-zoph.md) · [karina-nguyen](personas/karina-nguyen.md) · [sasha-rush](personas/sasha-rush.md)

**Alignment, Interp, Safety (9):** [chris-olah](personas/chris-olah.md) · [paul-christiano](personas/paul-christiano.md) · [jan-leike](personas/jan-leike.md) · [dan-hendrycks](personas/dan-hendrycks.md) · [stuart-russell](personas/stuart-russell.md) · [neel-nanda](personas/neel-nanda.md) · [lilian-weng](personas/lilian-weng.md) · **[beth-barnes](personas/beth-barnes.md)** · **[helen-toner](personas/helen-toner.md)**

**Theory and Science (9):** [yann-lecun](personas/yann-lecun.md) · [yoshua-bengio](personas/yoshua-bengio.md) · [geoffrey-hinton](personas/geoffrey-hinton.md) · **[john-jumper](personas/john-jumper.md)** · [percy-liang](personas/percy-liang.md) · [christopher-manning](personas/christopher-manning.md) · **[yejin-choi](personas/yejin-choi.md)** · [sara-hooker](personas/sara-hooker.md) · [aleksander-madry](personas/aleksander-madry.md)

**Multimodal, Embodied (7):** [fei-fei-li](personas/fei-fei-li.md) · [pieter-abbeel](personas/pieter-abbeel.md) · [sergey-levine](personas/sergey-levine.md) · [chelsea-finn](personas/chelsea-finn.md) · [robin-rombach](personas/robin-rombach.md) · [aditya-ramesh](personas/aditya-ramesh.md) · [prafulla-dhariwal](personas/prafulla-dhariwal.md)

**Systems, Kernels, Serving (7):** [tri-dao](personas/tri-dao.md) · [bryan-catanzaro](personas/bryan-catanzaro.md) · **[andrew-feldman](personas/andrew-feldman.md)** · [albert-gu](personas/albert-gu.md) · [horace-he](personas/horace-he.md) · [woosuk-kwon](personas/woosuk-kwon.md) · [tim-dettmers](personas/tim-dettmers.md)

## Files in this team

```
superintelligenceTeam/
├── SKILL.md                   This file — user-facing entry.
├── registry.json              Machine source of truth. Read by slash commands.
├── EXPANSION.md               (Phase 2) Gap-analysis and roster-expansion candidates.
├── templates/
│   ├── persona.md             Schema source-of-truth for every persona file.
│   └── convene.md             Multi-persona session template.
├── personas/                  59 *.md files, one per persona. YAML frontmatter + 6 narrative sections.
├── cells/                     8 *.md cell summaries.
├── research/                  59 directories, one per persona. Raw research dumps so future re-syntheses don't recrawl.
└── scripts/
    └── build_registry.py      Regenerates registry.json from persona frontmatter. Run after any persona edit.
```

<a id="slash-commands"></a>
## Slash commands (Phase 3 — installed)

22 slash command files live at `~/.claude/commands/superintelligenceTeam*.md` (user-global install, parallel to the existing `/team` family). Each is auto-registered as a discoverable Skill — no separate `SKILL.md` registration is needed. The architecture is **orchestrator-first**: every action verb invokes the orchestrator to pick a custom 16-32 persona team and gate on user approval before executing.

### Dispatcher (1)

| Command | Purpose |
|---|---|
| `/superintelligenceTeam` | No args → print roster + cell heatmap. With a subcommand as first token, routes to the sibling file. With free text and no subcommand, defaults to `:meeting`. |

### Orchestrator (1)

| Command | Purpose |
|---|---|
| `/superintelligenceTeam:orchestrate "<prompt>"` | **Standalone team selection.** Reads `registry.json`, scores all 59 personas via domain match (40%) + cell coverage (30%) + productive-conflict pairing (30%), picks 16-32, asks for user approval via AskUserQuestion with per-persona one-line rationale. Hard 16-32 size enforcement. Re-picks every invocation. Does NOT load CoCo. |

### Identity surface — explicit overrides (4)

| Command | Purpose | Skips orchestrator? |
|---|---|---|
| `/superintelligenceTeam:ask <slug> "<question>"` | 1-on-1 with one persona in their voice. | Yes |
| `/superintelligenceTeam:huddle <cell-slug> "<topic>"` | Whole cell (4-9 personas) synthesizes. | Yes |
| `/superintelligenceTeam:meeting "<prompt>"` | Full 59-persona convene with mandatory attribution. | Yes |
| `/superintelligenceTeam:read <slug>` | Print the persona file inline (not voice-channeled). | Yes |

### Roster management (1)

| Command | Purpose |
|---|---|
| `/superintelligenceTeam:recruit <domain> "<why>"` | Propose 2-3 new persona candidates for an under-covered domain. Reads EXPANSION.md to avoid re-proposing. Does not write personas itself. |

### Action surface (15) — orchestrator-first by default

All 15 invoke `/superintelligenceTeam:orchestrate` first unless `--no-orchestrate`, `--cells`, or `--personas` flag is supplied.

| Command | Output shape |
|---|---|
| `/superintelligenceTeam:analyse "<topic>"` | Per-persona analysis + synthesis table of strongest signals |
| `/superintelligenceTeam:decide "<question>"` | **Primary verb.** Decision matrix: options × personas × verdict + recommendation + named dissent |
| `/superintelligenceTeam:review <target>` | Multi-persona findings classified CRITICAL/MAJOR/MINOR/SUGGESTION + ship verdict |
| `/superintelligenceTeam:re-analyse "<topic>" [--prior <path>] [--evidence <text>]` | Updated stances + diff vs prior analysis |
| `/superintelligenceTeam:pre-mortem "<plan>"` | Ranked failure modes + early warning signs + mitigations |
| `/superintelligenceTeam:post-mortem "<what failed>"` | Per-persona 5 Whys + most-likely root cause + remediation plan |
| `/superintelligenceTeam:full-cycle "<topic>"` | **Heaviest verb.** Chains `:review → :analyse → mitigate-risk → :decide → finalize` as real subcommand invocations. 5× latency. Finalized action plan. |
| `/superintelligenceTeam:tradeoff "<A vs B>"` | Side-by-side dimensions × options table + most-opposed cell named |
| `/superintelligenceTeam:plan "<goal>"` | Phased plan with owner cell + dissenting voices per phase |
| `/superintelligenceTeam:design "<feature>"` | Component-level architecture with per-decision attribution |
| `/superintelligenceTeam:vote "<binary question>"` | Yes/no per persona + tally by cell + recommendation |
| `/superintelligenceTeam:debug "<problem>"` | Ranked root-cause hypotheses + diagnostic test order |
| `/superintelligenceTeam:stress-test "<proposal>"` | Adversarial attacks per persona + severity matrix + SHIP/HARDEN-THEN-SHIP/REFRAME/DO-NOT-SHIP verdict |
| `/superintelligenceTeam:defend "<position>" [as <slug>]` | Steelman with sharpened claim + counter-objection rebuttal + "what would change my mind" |
| `/superintelligenceTeam:roast "<thing>"` | One-line cutting roast per persona + single line that hurt most + convergent critique |

### Global flags

Every command accepts these:

| Flag | Effect |
|---|---|
| `--no-orchestrate` | Skip orchestrator; use all 59 personas |
| `--cells <comma-list>` | Manually scope to specific cells; skip orchestrator |
| `--personas <comma-list>` | Manually scope to specific persona slugs; skip orchestrator |

### Conventions enforced by every command

1. **Registry is source of truth.** Re-read every invocation; no caching.
2. **Attribution at every line.** No "the team said" — name a persona or a cell.
3. **Approval gate mandatory for action verbs** unless an explicit flag bypasses.
4. **Hard 16-32 size band** on orchestrator output.
5. **Full English prose** — no caveman compression in command output.

## Cross-team note

This is the **first** Super Intelligence Team in CoCo. Planned follow-ons:

- `cloud-super-intelligence` — AWS / GCP / Azure architecture
- `finance-super-intelligence` — FP&A, accounting, finance ops
- `coding-super-intelligence` — software-engineering practice
- `design-super-intelligence` — UX, design systems, visual design
- `product-super-intelligence` — PM craft, product strategy

All teams share the same schema (`teams: [...]` array on each persona, functional cell slugs, slash-command surface). A persona may belong to multiple teams — Karpathy will likely also appear in a future coding-super-intelligence team because of his pedagogical reach into engineering practice. The `teams:` field is an array exactly so this is cheap.

## Conventions

- **Schema source of truth:** `templates/persona.md`. Edit there first; persona files conform.
- **Registry regeneration:** run `python3 superintelligenceTeam/scripts/build_registry.py` after any persona edit.
- **Caveman mode does NOT apply** to persona files, cell files, or this SKILL.md. Documentation is always full English prose per the project rule.
- **Citation is mandatory.** Every `public_stance` has an `evidence_url`. No uncited claims.
- **v2 panel preservation.** Personas with `v2_panel_attribution` entries anchor to actual material from the Marvin Memory v2 synthesis on 2026-05-26. Convene uses those first.
- **Confidence calibration.** `confidence < 0.85` means we suspect identifier or biographical detail may need re-verification. Persona is still usable but flag in convene.

## Build provenance

- Forged 2026-05-27 by Rijul Kalra during /coco session.
- Quality bar set by Karpathy reference (12 cited URLs, 5 recent_signal_12mo entries, full 6-section narrative).
- 46 remaining personas built by parallel research sub-agents in 6 waves (8 + 8 + 8 + 8 + 8 + 6).
- Several agent runs corrected the user-supplied hints with verified facts (e.g., Lilian Weng's PhD = Indiana not NYU; Sergey Levine's PhD advisor = Vladlen Koltun not Pieter Abbeel; Barret Zoph fired from TML Jan 2026 and returned to OpenAI; Aditya Ramesh stayed at OpenAI Worldsim VP not TML).
- All persona files written in full English prose. Caveman mode active in chat throughout.
