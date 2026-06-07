# Super Intelligence Teams

> **Note:** Personas reference real public figures. Profiles are synthesized from public sources, with cited evidence — but roles and facts can change or go out of date, and quoted phrasing may be paraphrased. Treat them as illustrative expert lenses, not official statements. Not affiliated with or endorsed by the named individuals. See [`DISCLAIMER.md`](DISCLAIMER.md).

Reusable rosters of **real-world thought-leader personas** that act as parallel review-and-decision panels inside the CoCo Platform. Each team is a set of named experts with documented, **citable** public stances; you summon a custom 16–32 person panel for a prompt and every line of output is attributed to a specific person — never "the panel said."

The teams are a **decision-making partner**, not just a review surface. They are invoked through `/SI-*` slash commands installed at `~/.claude/commands/`.

## Teams

| Team | Command prefix | Personas | Cells | Validated |
|---|---|---|---|---|
| AI Super Intelligence | `/SI-AI-*` | 59 | 8 | built |
| Engineering Super Intelligence | `/SI-Eng-*` | 70 (+9 cross-listed from AI) | 11 | built |
| Product & Design Super Intelligence | `/SI-PD-*` | 56 (+1 cross-listed from Eng) | 8 | built |
| Finance Super Intelligence | `/SI-Fin-*` | 39 | 7 | 33/47 PASS |
| Trading Super Intelligence | `/SI-Trade-*` | 43 | 8 | 33/46 PASS |
| Risk & Compliance (GRC) | `/SI-GRC-*` | 28 (+12 cross-listed) | 7 | 27/30 PASS |
| Strategy Super Intelligence | `/SI-Strat-*` | 23 (+2 cross-listed from P&D) | 7 | 21/29 PASS |
| Data & Analytics Super Intelligence | `/SI-Data-*` | 25 | 7 | 24/29 PASS |
| Sales, GTM & Marketing | `/SI-GTM-*` | 20 (+3 cross-listed) | 7 | 17/23 PASS |

**All 9 teams built and activated.** The first three (AI, Engineering, Product & Design) were authored by Claude research agents and are built by construction. The six newer teams were built local-first then completed by Claude research agents (see *Build pipeline* below) and gated by the validator; the **Validated** column is the share that clears the strict bar (real cited live URLs, ≥2 signals or archetype `persistent_signals`, every stance cited). Personas below the bar are still real, grounded panel members flagged for incremental top-up — not omitted.

The machine-readable meta-registry is [`registry.json`](registry.json) (`kind: superintelligence-meta`). Each team has its own `<team>/registry.json`, `<team>/SKILL.md` (human entry point), `<team>/ROSTER.md` (locked roster), `personas/`, `cells/`, `research/`, and `scripts/`.

> **Product + Design are one merged team** (`product-design`), mirroring the earlier Cloud + Code → Engineering merge: discipline-pure cells preserve depth, while the team convenes both lenses by default. The same applies to Engineering, which merged cloud and coding concerns.

## Architecture: orchestrator-first

Every **action verb** (decide, tradeoff, pre-mortem, …) calls the team's **orchestrator** first:

1. **Orchestrate** — read `<team>/registry.json`, score all personas with `0.40·domain-match + 0.30·cell-coverage + 0.30·productive-conflict-pairing`, greedily pick **16–32** personas (hard band), and present them for approval (confidence-tiered: high → auto-proceed, low → AskUserQuestion). Re-picks every invocation; no caching.
2. **Execute** — the action verb consumes the approved roster and produces its verb-specific output (decision matrix, tradeoff table, ranked failure modes, …) with **per-line attribution**.

**Identity verbs** (`ask`, `huddle`, `meeting`, `read`) skip the orchestrator for explicit manual control. Global flags `--no-orchestrate`, `--cells <list>`, `--personas <list>` bypass or scope selection on any command.

### Command surface (25 per team)

`<prefix>` (dispatcher) · `-Orchestrate` · identity: `-Ask -Huddle -Meeting -Read` · roster: `-Recruit` · action (15): `-Analyse -Decide -Review -Re-Analyse -Pre-Mortem -Post-Mortem -Full-Cycle -Tradeoff -Plan -Design -Vote -Debug -Stress-Test -Defend -Roast` · maintenance: `-Refresh -Verify -VoiceCheck`.

> The `/SI-*` command files live in `~/.claude/commands/` (user-global), **outside this repo**. The repo carries the **generator** plus all persona/registry data, so the commands can be regenerated anywhere.

## Cross-team meta-orchestrator

The hardest decisions span domains ("ship an AI compliance product" → AI + GRC + Engineering + Product + Finance). The **meta-orchestrator** is a top-level router with **no team segment** that assembles one panel **across** teams:

| Command | Role |
|---|---|
| `/SI` | Dispatcher — lists built teams + the cross-team verbs. |
| `/SI-Orchestrate "<prompt>"` | Cross-team selection + approval gate; returns the merged roster. |
| `/SI-<Verb> "<prompt>"` | The 15 action verbs at the cross-team level (`/SI-Decide`, `/SI-Tradeoff`, `/SI-Pre-Mortem`, `/SI-Review`, `/SI-Stress-Test`, `/SI-Plan`, `/SI-Design`, `/SI-Analyse`, `/SI-Vote`, `/SI-Debug`, `/SI-Defend`, `/SI-Roast`, `/SI-Post-Mortem`, `/SI-Re-Analyse`, `/SI-Full-Cycle`). Each calls `/SI-Orchestrate` first. |

**Stage-A routing is deterministic + local.** [`scripts/meta_select.py`](scripts/meta_select.py) embeds the prompt against each built team's profile + cell descriptions using a local `nomic-embed` model and ranks → the top 1–4 relevant teams + candidate cells + proportional weights. It never loads persona files — the light layer that avoids the "load everything" trap. `/SI-Orchestrate` then drills into only the selected teams, allocates the 16–32 panel by relevance weight, runs a cross-team tension pass, and attributes every line to **persona + team**. Auto-delegates to a single team's orchestrator when one domain clearly dominates.

```bash
# example: cross-team panel decides a cross-cutting question
/SI-Decide "Should we build and sell an AI-powered audit-automation product?"
#   -> meta_select routes to GRC + AI + Engineering + Finance + Product
#   -> ~24-persona panel, approval gate, decision matrix with cross-team dissent
```

Generated by [`scripts/build_meta_commands.py`](scripts/build_meta_commands.py), which reads the meta-registry live — teams auto-join the cross-team surface the moment their `built` flag flips.

## Build pipeline (how the six newer teams were built)

Persona generation was an explicit cost/quality experiment, settled by evidence:

1. **Local-first** (`build_local.py`, qwen3.6 via LM Studio) + free retrieval (`retriever.py`: DuckDuckGo + trafilatura, deep + recency-filtered). ~$0, but low instruction-following yield.
2. **gpt-5.4-nano** (`build_nano.py`, QB AI Gateway) — fast, ~$0.003/persona, 20-parallel; retrieval-capped.
3. **gemini-3.5-flash** (`build_cursor.py`, Cursor headless agent) — top quality, but agent-latency-flaky at batch scale.
4. **Claude research agents (WebSearch)** — the quality winner; built the pending tail via a fan-out workflow.

Plus cheap repair/recalibration: `yaml_repair.py` + `topup_cheap.py` (fix malformed YAML, prune dead URLs), and a **recalibrated validator** ([`*/scripts/validate_persona.py`](finance/scripts/validate_persona.py)) that keeps the anti-fabrication core (≥4 **live** real URLs, every stance cited, no invented quotes) while relaxing arbitrary quotas and tolerating link-rot. `activate_teams.py` flips `built=true` + regenerates commands for teams clearing threshold. Full write-up in [`QUALITY-FINDINGS.md`](QUALITY-FINDINGS.md).

## Persona schema

Every persona is a Markdown file with YAML frontmatter + narrative sections, conforming to [`templates/persona.md`](templates/persona.md). Key invariants:

- `teams: [...]` array + `home_team` — a persona can belong to multiple teams via a single file (no duplication). Cross-team members are referenced from the other team's registry by relative path.
- Every `public_stance` carries an `evidence_url`. No uncited claims.
- Validator (recalibrated): ≥4 **live** real URLs, ≥2 `recent_signal_12mo` (each with a real url), every `public_stance` cited. Foundational / low-public-footprint / deceased figures are `status: archetype` and use ≥2 `persistent_signals` instead. Dead/404 URLs are tolerated as link-rot (pruned, not failed).
- `productive_conflict_with` wires the disagreements the orchestrator mines for tension (e.g. Hinton↔LeCun, DHH↔Fowler, Eyal↔Harris).

## Regenerating

```bash
# Per-team commands (omit --team for all): AI | Eng | PD | Fin | Trade | GRC | Strat | Data | GTM
python3 superintelligence/ai/scripts/build_commands.py --team Fin

# Cross-team meta commands (/SI, /SI-Orchestrate, /SI-<Verb>) — reads the meta-registry live:
python3 superintelligence/scripts/build_meta_commands.py

# Registry + cell docs + SKILL for a team (run after editing any persona file):
python3 superintelligence/<team>/scripts/build_registry.py
python3 superintelligence/<team>/scripts/build_cells.py
python3 superintelligence/scripts/build_skill.py <team>

# Re-validate + (re)activate a team once its PASS rate clears threshold:
python3 superintelligence/<team>/scripts/validate_all.py
THRESHOLD=0.70 python3 superintelligence/scripts/activate_teams.py
```

`build_commands.py` is the single source of truth for the command surface; all teams are stamped from one shared template, so a fix there propagates to every team. Per-team specifics (cells, gap doc, counts) live in its `TEAMS` dict.

## Conventions

- **Schema source of truth:** `templates/persona.md`. Edit there first.
- **Attribution mandatory:** every claim names a persona or a cell.
- **Documentation is always full English prose** (no caveman compression) — applies to persona files, cell docs, SKILL files, and this README.
- **Cross-team personas:** one file, `teams: [...]` + `home_team`; never duplicate.

## Layout

```
superintelligence/
├── README.md                  This file.
├── registry.json              Meta-registry (9 teams, default_team, build status).
├── DISCLAIMER.md              Real-figure / illustrative-composite disclaimer.
├── QUALITY-FINDINGS.md        Build-pipeline experiment + validator recalibration write-up.
├── ACTIVATION-REPORT.md       Per-team PASS rates + activation decisions.
├── META-ORCHESTRATOR-DESIGN.md  Cross-team router design + locked decisions.
├── templates/                 Shared persona.md + convene.md.
├── scripts/                   Cross-team: meta_select.py, build_meta_commands.py,
│                              build_nano/build_cursor, yaml_repair, topup_cheap,
│                              activate_teams, build_skill, validate/registry generics.
├── ai/                        AI team (59 personas, 8 cells) + scripts.
├── engineering/               Engineering team (70, 11 cells) + scripts.
├── product-design/            Product & Design team (56, 8 cells) + scripts.
├── finance/                   Finance team (39, 7 cells) + scripts.
├── trading/                   Trading team (43, 8 cells) + scripts.
├── risk-compliance/           Risk & Compliance / GRC (28 +12 x-listed, 7 cells) + scripts.
├── strategy/                  Strategy team (23 +2 x-listed, 7 cells) + scripts.
├── data-analytics/            Data & Analytics team (25, 7 cells) + scripts.
└── gtm/                       Sales, GTM & Marketing team (20 +3 x-listed, 7 cells) + scripts.
```
Each team dir: `registry.json`, `roster.json` (locked), `SKILL.md`, `personas/`, `cells/`, `research/` (gitignored), `scripts/`.
