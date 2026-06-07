#!/usr/bin/env python3
"""
Team-generic cell-doc builder. Drop into superintelligence/<team>/scripts/ and run
AFTER build_registry.py. Generates <team>/cells/<cell>.md from registry.json + persona
frontmatter. Titles + summon prompts are derived from the roster cell descriptions
(no curated per-cell prose, no fabrication). Cross-listed personas render as references.

    python3 superintelligence/<team>/scripts/build_cells.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.exit("pip install --break-system-packages pyyaml")

TEAM_DIR = Path(__file__).resolve().parents[1]
TEAM = TEAM_DIR.name
PERS = TEAM_DIR / "personas"; CELLS = TEAM_DIR / "cells"
REG = json.loads((TEAM_DIR / "registry.json").read_text())
ROSTER = json.loads((TEAM_DIR / "roster.json").read_text())
LAST = str(REG.get("generated_at", ""))
TEAM_ID = REG["team_id"]
SHORT = ROSTER.get("command_short", "".join(w[:1] for w in TEAM.split("-")).upper())

_ABBR = {"fpa": "FP&A", "ma": "M&A", "ai": "AI", "grc": "GRC", "erm": "ERM",
         "aml": "AML", "ux": "UX", "sre": "SRE", "hft": "HFT"}


def titleize(cid: str) -> str:
    words = []
    for w in cid.split("-"):
        words.append(_ABBR.get(w, w.capitalize()))
    return " ".join(words)


def fm(slug):
    p = PERS / f"{slug}.md"
    if not p.exists():
        return None
    t = p.read_text()
    return yaml.safe_load(t[4:t.find(chr(10) + "---" + chr(10), 4)])


def first(v):
    return str(v[0]) if isinstance(v, list) and v else (str(v) if v else "")


def main():
    CELLS.mkdir(exist_ok=True)
    n = 0
    for cid, info in REG["cells"].items():
        slugs = info["personas"]
        if not slugs:
            continue
        title = titleize(cid)
        fms = {s: fm(s) for s in slugs}
        rows = []
        for s in slugs:
            f = fms[s]
            if f is None:  # cross-listed — file lives in another team
                rec = REG["personas"].get(s, {})
                home = rec.get("home_team", "").replace("-super-intelligence", "")
                rows.append(f"| `{s}` | *(cross-listed from {home})* | — | reference | see home team |")
                continue
            star = " *(archetype)*" if f.get("status") == "archetype" else ""
            rows.append(f"| `{s}` | {f.get('real_name', s)}{star} | {first(f.get('affiliations_2026'))} | "
                        f"{f.get('cell_role', '')} | {first(f.get('signature_moves'))} |")
        # productive tensions among LOCAL members only
        local = [s for s in slugs if fms[s] is not None]
        cellset = set(local); seen = set(); tens = []
        for s in local:
            for opp in (fms[s].get("productive_conflict_with") or []):
                if opp in cellset and tuple(sorted((s, opp))) not in seen:
                    seen.add(tuple(sorted((s, opp))))
                    tens.append(f"- **{fms[s].get('real_name', s)} ↔ {fms[opp].get('real_name', opp)}** "
                                f"(`{s}` ↔ `{opp}`)")
        tb = "\n".join(tens) if tens else \
            "- Cross-cell tension dominates; the orchestrator pairs these members with other cells."
        summon = (f"- \"What does the {title} lens say about this?\"\n"
                  f"- \"{info['description'].rstrip('.')}\" — where does this decision touch that?\n"
                  f"- \"Who in {title} would push back hardest, and why?\"")
        doc = f"""---
cell_id: {cid}
team: {TEAM_ID}
personas_count: {len(slugs)}
last_updated: {LAST}
---

# Cell: {title}

{info['description']}

## Personas ({len(slugs)})

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
{chr(10).join(rows)}

## When to summon the whole cell

{summon}

## Productive tensions inside the cell

{tb}

## How this cell maps to /SI-{SHORT} commands

Summon with `/SI-{SHORT}-Huddle {cid} "<topic>"`, or let an action verb
(`/SI-{SHORT}-Decide`, `/SI-{SHORT}-Tradeoff`, `/SI-{SHORT}-Stress-Test`, …) pull
members into a cross-cell panel via `/SI-{SHORT}-Orchestrate`.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/{TEAM}/scripts/build_cells.py`. Personas are illustrative
composites of real public figures — see `superintelligence/DISCLAIMER.md`.
"""
        (CELLS / f"{cid}.md").write_text(doc, encoding="utf-8")
        n += 1
        print(f"  wrote cells/{cid}.md ({len(slugs)} personas, {len(tens)} tensions)")
    print(f"Wrote {n} cell docs.")


if __name__ == "__main__":
    main()
