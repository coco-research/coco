# Super Intelligence Teams

> **Note:** Personas reference real public figures. Profiles are synthesized from public sources, with cited evidence — but roles and facts can change or go out of date, and quoted phrasing may be paraphrased. Treat them as illustrative expert lenses, not official statements. Not affiliated with or endorsed by the named individuals. See [`DISCLAIMER.md`](DISCLAIMER.md).

Reusable rosters of **real-world thought-leader personas** that act as parallel review-and-decision panels inside the CoCo Platform. Each team is a set of named experts with documented, **citable** public stances; you summon a custom 16–32 person panel for a prompt and every line of output is attributed to a specific person — never "the panel said."

The teams are a **decision-making partner**, not just a review surface. They are invoked through `/SI-*` slash commands installed at `~/.claude/commands/`.

## Teams

| Team | Command prefix | Personas | Cells | Status |
|---|---|---|---|---|
| AI Super Intelligence | `/SI-AI-*` | 59 | 8 | built |
| Engineering Super Intelligence | `/SI-Eng-*` | 70 (+9 cross-listed from AI) | 11 | built |
| Product & Design Super Intelligence | `/SI-PD-*` | 56 (+1 cross-listed from Eng) | 8 | built |
| Finance Super Intelligence | `/SI-Fin-*` | — | — | planned |
| Compliance Super Intelligence | `/SI-Comp-*` | — | — | planned |

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

## Persona schema

Every persona is a Markdown file with YAML frontmatter + narrative sections, conforming to [`templates/persona.md`](templates/persona.md). Key invariants:

- `teams: [...]` array + `home_team` — a persona can belong to multiple teams via a single file (no duplication). Cross-team members are referenced from the other team's registry by relative path.
- Every `public_stance` carries an `evidence_url`. No uncited claims.
- Active personas need ≥3 `recent_signal_12mo`; foundational / low-public-footprint figures are `status: archetype` and use `persistent_signals` instead.
- `productive_conflict_with` wires the disagreements the orchestrator mines for tension (e.g. Hinton↔LeCun, DHH↔Fowler, Eyal↔Harris).

## Regenerating

```bash
# Commands for one team (or all if --team omitted):
python3 superintelligence/ai/scripts/build_commands.py --team AI   # | Eng | PD

# Registry + cell docs for a team (run after editing any persona file):
python3 superintelligence/<team>/scripts/build_registry.py
python3 superintelligence/<team>/scripts/build_cells.py
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
├── registry.json              Meta-registry (known teams, default_team, build status).
├── templates/                 Shared persona.md + convene.md.
├── ai/                        AI team (59 personas, 8 cells) + scripts.
├── engineering/               Engineering team (70 personas, 11 cells) + scripts.
└── product-design/            Product & Design team (56 personas, 8 cells) + scripts.
```
