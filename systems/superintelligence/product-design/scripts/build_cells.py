#!/usr/bin/env python3
"""
Generate superintelligence/product-design/cells/<cell>.md for all 8 cells from
registry.json + persona frontmatter. Mirrors the AI/Engineering cell-doc format.
Re-run after persona edits or build_registry.py.

Usage:
    python3 superintelligence/product-design/scripts/build_cells.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not available. Install with: pip install pyyaml")

PD_DIR = Path(__file__).resolve().parents[1]
PERSONAS_DIR = PD_DIR / "personas"
CELLS_DIR = PD_DIR / "cells"
REGISTRY = json.loads((PD_DIR / "registry.json").read_text())
LAST_UPDATED = "2026-06-01"

CELL_TITLES = {
    "product-strategy": "Product Strategy",
    "product-discovery-research": "Product Discovery and Research",
    "growth-metrics": "Growth and Metrics",
    "design-foundations-usability": "Design Foundations and Usability",
    "design-leadership-craft": "Design Leadership and Craft",
    "ux-content-research": "UX, Content, and Research",
    "design-systems-interaction": "Design Systems and Interaction",
    "sprints-behavior-bridge": "Sprints, Behavior, and Bridge",
}

WHEN_TO_SUMMON = {
    "product-strategy": [
        "\"What is our product strategy / where do we play and how do we win?\"",
        "\"How do we position this against alternatives?\"",
        "\"Empowered team or feature factory — what are we actually running?\"",
    ],
    "product-discovery-research": [
        "\"What problem are we really solving, and for whom?\"",
        "\"What job is the customer hiring this for?\"",
        "\"How do we validate before we build?\"",
    ],
    "growth-metrics": [
        "\"What is our growth model / North Star, and is it the right one?\"",
        "\"Is this experiment trustworthy, and what does it actually say?\"",
        "\"Where does retention / activation actually break?\"",
    ],
    "design-foundations-usability": [
        "\"Is this usable, and how do we know?\"",
        "\"What does human-centered / accessible design demand here?\"",
        "\"Are we fighting the user's mental model?\"",
    ],
    "design-leadership-craft": [
        "\"Is this design any good — craft, taste, simplicity?\"",
        "\"What would great look like, and what are we settling for?\"",
        "\"How do we build a design culture that ships quality?\"",
    ],
    "ux-content-research": [
        "\"Does the content / IA make this make sense?\"",
        "\"What should this actually say, and how is it structured?\"",
        "\"Is the language clear, humane, and honest?\"",
    ],
    "design-systems-interaction": [
        "\"How do we scale design consistently across the product?\"",
        "\"Component, token, and pattern decisions — what is the system?\"",
        "\"Where do we trade flexibility for coherence?\"",
    ],
    "sprints-behavior-bridge": [
        "\"How do we move from idea to tested prototype fast?\"",
        "\"What behavior are we shaping — and should we?\"",
        "\"Engagement vs ethics: are we building habit or harm?\"",
    ],
}


def fm(slug: str) -> dict:
    p = PERSONAS_DIR / f"{slug}.md"
    t = p.read_text(encoding="utf-8")
    end = t.find("\n---\n", 4)
    return yaml.safe_load(t[4:end])


def first(v):
    if isinstance(v, list) and v:
        return str(v[0])
    return str(v) if v else ""


def main() -> None:
    CELLS_DIR.mkdir(exist_ok=True)
    cells = REGISTRY["cells"]
    written = 0
    for cell_id, info in cells.items():
        slugs = list(info["personas"])
        xl = info.get("cross_listed", [])
        title = CELL_TITLES[cell_id]
        persona_fms = {s: fm(s) for s in slugs}
        rows = []
        for s in slugs:
            f = persona_fms[s]
            name = f.get("real_name", s)
            aff = first(f.get("affiliations_2026"))
            role = f.get("cell_role", "")
            sig = first(f.get("signature_moves"))
            star = " *(archetype)*" if f.get("status") == "archetype" else ""
            rows.append(f"| `{s}` | {name}{star} | {aff} | {role} | {sig} |")
        for s in xl:
            rows.append(f"| `{s}` | *(cross-listed)* | — | specialist | see home team |")

        cellset = set(slugs)
        seen, tensions = set(), []
        for s in slugs:
            for opp in (persona_fms[s].get("productive_conflict_with") or []):
                if opp in cellset:
                    key = tuple(sorted((s, opp)))
                    if key not in seen:
                        seen.add(key)
                        a, b = key
                        tensions.append(
                            f"- **{persona_fms[a].get('real_name', a)} ↔ "
                            f"{persona_fms[b].get('real_name', b)}** (`{a}` ↔ `{b}`)"
                        )
        tension_block = "\n".join(tensions) if tensions else (
            "- No within-cell productive-conflict pairs recorded. Tension comes primarily from "
            "cross-cell pairings surfaced by the orchestrator."
        )
        summon = "\n".join(f"- {q}" for q in WHEN_TO_SUMMON[cell_id])

        doc = f"""---
cell_id: {cell_id}
team: product-design-super-intelligence
personas_count: {len(slugs)}
last_updated: {LAST_UPDATED}
---

# Cell: {title}

{info['description']}

## Personas ({len(slugs)}{f" + {len(xl)} cross-listed" if xl else ""})

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
{chr(10).join(rows)}

## When to summon the whole cell

{summon}

## Productive tensions inside the cell

{tension_block}

## How this cell maps to /SI-PD commands

Summon directly with `/SI-PD-Huddle {cell_id} "<topic>"`, or let an action verb
(`/SI-PD-Decide`, `/SI-PD-Tradeoff`, `/SI-PD-Stress-Test`, …) pull the most relevant
members into a cross-cell panel via `/SI-PD-Orchestrate`.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/product-design/scripts/build_cells.py`.
"""
        (CELLS_DIR / f"{cell_id}.md").write_text(doc, encoding="utf-8")
        written += 1
        print(f"  wrote cells/{cell_id}.md ({len(slugs)} personas, {len(tensions)} tensions)")
    print(f"Wrote {written} cell docs.")


if __name__ == "__main__":
    main()
