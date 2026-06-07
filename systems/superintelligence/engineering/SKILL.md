---
team_id: engineering-super-intelligence
team_name: Engineering Super Intelligence Team
personas_count: 70
cells_count: 11
cross_listed_from_ai: 9
last_updated: 2026-05-30
schema_version: 1.0
---

# Engineering Super Intelligence Team — SKILL entry

Rijul's software-engineering brain trust **and decision-making partner**. 70 named native personas across 11 cells — drawn from the people who built the cloud, the databases, the languages, the runtimes, the web platform, the security and reliability disciplines, the DevOps movement, and the AI-coding frontier — plus 9 personas cross-listed from the AI Super Intelligence Team. Reusable across any CoCo-routed prompt, invoked by the `/SI-Eng-*` slash commands. The team's primary purpose is to **help take engineering decisions**, not just review work after the fact.

> **Status:** Roster build complete (2026-05-30).
> - **Roster:** 70 native personas across 11 cells, locked after a `/ultra-think` pass on the draft 65 (added Lamport, Lattner, Torvalds, Liskov, Perlman; reclassified Ghemawat as archetype; split the former `devops-platform-ai-coding` mega-cell into `devops-platform` + `ai-assisted-coding`).
> - **Cross-listed:** 9 ML-systems / AI-coding voices carry `teams: [ai-super-intelligence, engineering-super-intelligence]` — single file, dual membership, no duplication.
> - **Commands:** 25 `/SI-Eng-*` slash commands installed at `~/.claude/commands/`, generated from the shared template by `superintelligence/ai/scripts/build_commands.py --team Eng`.

This file is the user-facing entry point. The machine source of truth is [`registry.json`](registry.json), regenerated from persona frontmatter by `python3 superintelligence/engineering/scripts/build_registry.py`.

## What this team is for

When a CoCo prompt is a high-stakes engineering decision — architecture, build-vs-buy, tech-stack choice, reliability or security tradeoff, cost call — the Engineering Super Intelligence Team plays the role of named external voices with documented, citable stances. Instead of "the panel said," every claim is attributed to a specific engineer. This lets convene synthesis:

- Surface real disagreement (DHH vs Fowler/Newman on microservices; Cantrill vs Vogels/Burns on cloud-vs-own-hardware; Harris vs Abramov on virtual-DOM-vs-compiler; Stroustrup vs Hoare on memory safety).
- Anchor stances to citable evidence (every `public_stance` in every persona carries an `evidence_url`).
- Stay honest about who drove which decision (lead-driver vs validator vs specialist vs swing).

The roster leans toward strong, opinionated, publicly-documented engineers — which makes it powerful for `decide` / `tradeoff` / `stress-test` / `roast`, and carries a known simplicity-maximalist / anti-hype tilt (Hickey, Carmack, DHH, Cantrill) that the architecture-and-process voices (Fowler, Hohpe, Newman, Kim, Forsgren) counterweight.

## Cells (11)

| Cell | Count | Focus | File |
|---|---|---|---|
| `cloud-architecture` | 8 | Cloud-scale system design, infra primitives, build-vs-managed | [cells/cloud-architecture.md](cells/cloud-architecture.md) |
| `reliability-sre-obs` | 7 | SRE practice, observability, incident response, resilience | [cells/reliability-sre-obs.md](cells/reliability-sre-obs.md) |
| `data-and-storage` | 8 | Databases, distributed data, consistency, distributed-systems theory | [cells/data-and-storage.md](cells/data-and-storage.md) |
| `security` | 6 | Security architecture, cryptography, vuln research, disclosure policy | [cells/security.md](cells/security.md) |
| `finops-cost` | 4 | Cloud cost engineering, FinOps practice | [cells/finops-cost.md](cells/finops-cost.md) |
| `languages-runtimes` | 8 | Language design, type systems, compilers, runtimes | [cells/languages-runtimes.md](cells/languages-runtimes.md) |
| `systems-programming` | 7 | Low-level, OS, performance, systems craft | [cells/systems-programming.md](cells/systems-programming.md) |
| `web-and-frontend` | 6 | Frontend frameworks, web platform, UI engineering | [cells/web-and-frontend.md](cells/web-and-frontend.md) |
| `architecture-testing-craft` | 8 | Software architecture, DDD, testing discipline, craft | [cells/architecture-testing-craft.md](cells/architecture-testing-craft.md) |
| `devops-platform` | 6 | DevOps movement, platform engineering, internal developer platforms | [cells/devops-platform.md](cells/devops-platform.md) |
| `ai-assisted-coding` | 2 (+2 cross-listed) | Agentic dev tools, codegen, the AI-coding frontier | [cells/ai-assisted-coding.md](cells/ai-assisted-coding.md) |

## Personas (70 native)

Listed by cell. Each has a YAML-frontmatter profile under `personas/<slug>.md` plus a research dump under `research/<slug>/`. Personas marked *(archetype)* use `persistent_signals` rather than recent signals (foundational figures or deliberately low-public-footprint).

**Cloud Architecture (8):** [james-hamilton](personas/james-hamilton.md) · [werner-vogels](personas/werner-vogels.md) · [adrian-cockcroft](personas/adrian-cockcroft.md) · [marc-brooker](personas/marc-brooker.md) · [brendan-burns](personas/brendan-burns.md) · [eric-brewer](personas/eric-brewer.md) · [colm-maccarthaigh](personas/colm-maccarthaigh.md) · [radia-perlman](personas/radia-perlman.md)

**Reliability, SRE, Observability (7):** [ben-treynor-sloss](personas/ben-treynor-sloss.md) · [betsy-beyer](personas/betsy-beyer.md) *(archetype)* · [charity-majors](personas/charity-majors.md) · [cindy-sridharan](personas/cindy-sridharan.md) *(archetype)* · [liz-fong-jones](personas/liz-fong-jones.md) · [nora-jones](personas/nora-jones.md) · [tammy-butow](personas/tammy-butow.md) *(archetype)*

**Data and Storage (8):** [martin-kleppmann](personas/martin-kleppmann.md) · [jeff-dean](personas/jeff-dean.md) · [sanjay-ghemawat](personas/sanjay-ghemawat.md) *(archetype)* · [pat-helland](personas/pat-helland.md) · [michael-stonebraker](personas/michael-stonebraker.md) · [andy-pavlo](personas/andy-pavlo.md) · [joe-hellerstein](personas/joe-hellerstein.md) · [leslie-lamport](personas/leslie-lamport.md)

**Security (6):** [bruce-schneier](personas/bruce-schneier.md) · [alex-stamos](personas/alex-stamos.md) · [window-snyder](personas/window-snyder.md) · [matthew-green](personas/matthew-green.md) · [tavis-ormandy](personas/tavis-ormandy.md) · [katie-moussouris](personas/katie-moussouris.md)

**FinOps and Cost (4):** [corey-quinn](personas/corey-quinn.md) · [jr-storment](personas/jr-storment.md) · [mike-fuller](personas/mike-fuller.md) · [erik-peterson](personas/erik-peterson.md)

**Languages and Runtimes (8):** [guido-van-rossum](personas/guido-van-rossum.md) · [anders-hejlsberg](personas/anders-hejlsberg.md) · [rich-hickey](personas/rich-hickey.md) · [graydon-hoare](personas/graydon-hoare.md) · [brendan-eich](personas/brendan-eich.md) · [yukihiro-matsumoto](personas/yukihiro-matsumoto.md) · [bjarne-stroustrup](personas/bjarne-stroustrup.md) · [chris-lattner](personas/chris-lattner.md)

**Systems Programming (7):** [john-carmack](personas/john-carmack.md) · [bryan-cantrill](personas/bryan-cantrill.md) · [jonathan-blow](personas/jonathan-blow.md) · [mitchell-hashimoto](personas/mitchell-hashimoto.md) · [ryan-dahl](personas/ryan-dahl.md) · [brian-kernighan](personas/brian-kernighan.md) *(archetype)* · [linus-torvalds](personas/linus-torvalds.md)

**Web and Frontend (6):** [evan-you](personas/evan-you.md) · [dan-abramov](personas/dan-abramov.md) · [rich-harris](personas/rich-harris.md) · [guillermo-rauch](personas/guillermo-rauch.md) · [ryan-carniato](personas/ryan-carniato.md) · [adam-wathan](personas/adam-wathan.md)

**Architecture, Testing, Craft (8):** [martin-fowler](personas/martin-fowler.md) · [kent-beck](personas/kent-beck.md) · [eric-evans](personas/eric-evans.md) · [sam-newman](personas/sam-newman.md) · [michael-feathers](personas/michael-feathers.md) · [dhh](personas/dhh.md) · [gregor-hohpe](personas/gregor-hohpe.md) · [barbara-liskov](personas/barbara-liskov.md) *(archetype)*

**DevOps and Platform (6):** [gene-kim](personas/gene-kim.md) · [jez-humble](personas/jez-humble.md) · [nicole-forsgren](personas/nicole-forsgren.md) · [kelsey-hightower](personas/kelsey-hightower.md) · [matthew-skelton](personas/matthew-skelton.md) · [solomon-hykes](personas/solomon-hykes.md)

**AI-Assisted Coding (2 native + 2 cross-listed):** [michael-truell](personas/michael-truell.md) · [nat-friedman](personas/nat-friedman.md) · andrej-karpathy *(cross-listed from AI)* · sasha-rush *(cross-listed from AI)*

## Cross-listed from the AI team (9)

These carry `teams: [ai-super-intelligence, engineering-super-intelligence]` and `home_team: ai-super-intelligence`. Their files live under `superintelligence/ai/personas/`; the Engineering registry references them via the `cross_listed_from_ai` field. No duplication.

`andrej-karpathy` · `sasha-rush` · `tri-dao` · `bryan-catanzaro` · `andrew-feldman` · `albert-gu` · `horace-he` · `woosuk-kwon` · `tim-dettmers`

## Files in this team

```
superintelligence/engineering/
├── SKILL.md                   This file — user-facing entry.
├── ROSTER.md                  Locked roster ground-truth + build-wave manifest.
├── registry.json              Machine source of truth. Read by slash commands.
├── personas/                  70 *.md files, one per native persona. YAML frontmatter + narrative sections.
├── cells/                     11 *.md cell summaries (generated by build_cells.py).
├── research/                  70 directories, one per persona. Raw research dumps.
└── scripts/
    ├── build_registry.py      Regenerates registry.json from persona frontmatter.
    └── build_cells.py         Regenerates the 11 cell docs from registry + frontmatter.
```

Templates (`persona.md`, `convene.md`) are shared one level up at `superintelligence/templates/`.

## Slash commands (25 — installed)

25 `/SI-Eng-*` command files live at `~/.claude/commands/`, generated from the shared template by `python3 superintelligence/ai/scripts/build_commands.py --team Eng`. Architecture is **orchestrator-first**: every action verb invokes `/SI-Eng-Orchestrate` to pick a custom 16–32 persona team and gate on user approval before executing.

### Dispatcher + Orchestrator
- `/SI-Eng` — no args → roster + cell heatmap; with a subcommand, routes; with free text, defaults to `:meeting`.
- `/SI-Eng-Orchestrate "<prompt>"` — scores all 70 personas (domain match 40% + cell coverage 30% + productive-conflict pairing 30%), picks 16–32, approval gate via AskUserQuestion, hard 16–32 band, re-picks every invocation.

### Identity surface — explicit overrides (skip the orchestrator)
- `/SI-Eng-Ask <slug> "<question>"` — one persona in voice.
- `/SI-Eng-Huddle <cell-slug> "<topic>"` — whole cell synthesizes.
- `/SI-Eng-Meeting "<prompt>"` — full convene with mandatory attribution.
- `/SI-Eng-Read <slug>` — print persona file inline.

### Roster management
- `/SI-Eng-Recruit <domain> "<why>"` — propose new persona candidates for an under-covered domain.

### Action surface (15, orchestrator-first)
`/SI-Eng-Analyse` · `/SI-Eng-Decide` *(primary)* · `/SI-Eng-Review` · `/SI-Eng-Re-Analyse` · `/SI-Eng-Pre-Mortem` · `/SI-Eng-Post-Mortem` · `/SI-Eng-Full-Cycle` · `/SI-Eng-Tradeoff` · `/SI-Eng-Plan` · `/SI-Eng-Design` · `/SI-Eng-Vote` · `/SI-Eng-Debug` · `/SI-Eng-Stress-Test` · `/SI-Eng-Defend` · `/SI-Eng-Roast`

### Maintenance
- `/SI-Eng-Refresh` · `/SI-Eng-Verify` · `/SI-Eng-VoiceCheck`

### Global flags (every command)
- `--no-orchestrate` — skip orchestrator; use all 70 personas.
- `--cells <comma-list>` — manually scope to cells.
- `--personas <comma-list>` — manually scope to slugs.

## Conventions

- **Schema source of truth:** `superintelligence/templates/persona.md`. Edit there first.
- **Registry regeneration:** `python3 superintelligence/engineering/scripts/build_registry.py` after any persona edit; then `build_cells.py` for the cell docs.
- **Attribution at every line.** No "the team said" — name a persona or a cell.
- **Citation is mandatory.** Every `public_stance` has an `evidence_url`. No uncited claims.
- **Caveman mode does NOT apply** to persona files, cell files, or this SKILL.md. Documentation is always full English prose per the project rule.
- **Cross-team personas** are single-file with a `teams: [...]` array and a `home_team` pointer. Never duplicate a persona file across teams.

## Build provenance

- Built 2026-05-30 by Rijul Kalra during a /coco session, immediately after the AI Super Intelligence Team.
- Roster scrutinized via `/ultra-think` before build: 5 canon adds, Ghemawat → archetype, mega-cell split, two all-male cells de-skewed (Liskov → craft, Perlman → cloud-architecture).
- 70 native personas built by parallel research sub-agents across staged waves (cloud, reliability, data, security, finops, languages, systems, web, ai-coding, craft, devops). A mid-build rate-limit reset 18 craft/devops/systems/web personas; they were re-run cleanly.
- Quality bar matched the AI team's Karpathy reference (≥8 cited URLs, ≥3 recent signals, every public_stance cited, full 6-section narrative). Many agents corrected stale title/affiliation assumptions against verified 2026 facts (e.g., Hamilton SVP not VP; Brooker promoted to VP; Stamos now CSO at Corridor; Kleppmann back at Cambridge; Liz Fong-Jones now Technical Fellow; Forsgren single-employer Microsoft; Nat Friedman confirmed at Meta Superintelligence Labs).
- All persona files written in full English prose. Caveman mode active in chat throughout.
