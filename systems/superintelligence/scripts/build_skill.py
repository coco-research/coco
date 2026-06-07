#!/usr/bin/env python3
"""Generate SKILL.md for each team from its registry.json. python3 scripts/build_skill.py [team...]"""
import sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
TEAMS = sys.argv[1:] or ["finance", "trading", "risk-compliance", "strategy", "data-analytics", "gtm"]

for t in TEAMS:
    tdir = ROOT / t
    reg = json.loads((tdir / "registry.json").read_text())
    roster = json.loads((tdir / "roster.json").read_text())
    short = roster.get("command_short", t[:4].title())
    cells = reg.get("cells", {})
    rows = "\n".join(
        f"| `{cid}` | {c.get('personas_count', 0)} | {c.get('description', '')} |"
        for cid, c in cells.items())
    nat = reg.get("native_personas_count", reg.get("personas_count", 0))
    xl = reg.get("cross_listed_count", 0)
    doc = f"""---
name: {reg.get('team_id', t)}
team: {t}
personas: {reg.get('personas_count', 0)}
cells: {len(cells)}
command_prefix: /SI-{short}
last_updated: {reg.get('generated_at', '2026-06-01')}
---

# {reg.get('team_name', t)}

{reg.get('description', '')}

**{nat} native personas** ({xl} cross-listed) across **{len(cells)} cells**. Real public figures
rendered as illustrative composites — see `superintelligence/DISCLAIMER.md`. Built local-first +
Claude-research, validator-gated (real cited URLs, no fabrication).

## Cells

| Cell | Personas | Focus |
|---|---|---|
{rows}

## Command surface

- **Orchestrate (smart panel):** `/SI-{short}-Orchestrate "<prompt>"` → picks 16-32 personas + approval gate
- **Action verbs:** `/SI-{short}-Decide` · `-Tradeoff` · `-Pre-Mortem` · `-Review` · `-Stress-Test` · `-Plan` · `-Design` · `-Analyse` · `-Vote` · `-Debug` · `-Defend` · `-Roast` · `-Post-Mortem` · `-Re-Analyse` · `-Full-Cycle`
- **Identity:** `/SI-{short}-Ask <slug> "<q>"` · `-Huddle <cell> "<topic>"` · `-Meeting "<prompt>"` · `-Read <slug>`
- **Roster/maintenance:** `/SI-{short}-Recruit` · `-Refresh` · `-VoiceCheck` · `-Verify`

## Cross-team

For multi-domain decisions, the top-level `/SI-Orchestrate` (+ `/SI-<Verb>`) routes ACROSS teams
via `superintelligence/scripts/meta_select.py` (local nomic-embed). This team auto-joins that panel.

## Source of truth

`registry.json` (generated from persona frontmatter) + `cells/*.md` + `roster.json`.
Regenerate: `python3 {t}/scripts/build_registry.py && python3 {t}/scripts/build_cells.py`.
"""
    (tdir / "SKILL.md").write_text(doc, encoding="utf-8")
    print(f"wrote {t}/SKILL.md ({reg.get('personas_count',0)} personas, {len(cells)} cells, /SI-{short})")
