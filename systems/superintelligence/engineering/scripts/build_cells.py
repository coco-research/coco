#!/usr/bin/env python3
"""
Generate superintelligence/engineering/cells/<cell>.md for all 11 Engineering
cells from registry.json + persona frontmatter. Mirrors the AI team's cell-doc
format (frontmatter, roster table, when-to-summon, within-cell productive
tensions). Re-run after persona edits or build_registry.py.

Usage:
    python3 superintelligence/engineering/scripts/build_cells.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not available. Install with: pip install pyyaml")

ENG_DIR = Path(__file__).resolve().parents[1]
PERSONAS_DIR = ENG_DIR / "personas"
CELLS_DIR = ENG_DIR / "cells"
REGISTRY = json.loads((ENG_DIR / "registry.json").read_text())

LAST_UPDATED = "2026-05-30"

CELL_TITLES = {
    "cloud-architecture": "Cloud Architecture",
    "reliability-sre-obs": "Reliability, SRE, and Observability",
    "data-and-storage": "Data and Storage",
    "security": "Security",
    "finops-cost": "FinOps and Cost",
    "languages-runtimes": "Languages and Runtimes",
    "systems-programming": "Systems Programming",
    "web-and-frontend": "Web and Frontend",
    "architecture-testing-craft": "Architecture, Testing, and Craft",
    "devops-platform": "DevOps and Platform Engineering",
    "ai-assisted-coding": "AI-Assisted Coding",
}

WHEN_TO_SUMMON = {
    "cloud-architecture": [
        "\"Build it ourselves or use the managed service?\"",
        "\"How does this behave at cloud scale / under partial failure?\"",
        "\"What are the real cost and reliability economics of this infra choice?\"",
    ],
    "reliability-sre-obs": [
        "\"How do we know this is healthy in production?\"",
        "\"What is our SLO / error budget, and are we spending it wisely?\"",
        "\"How do we run the incident and learn from it afterwards?\"",
    ],
    "data-and-storage": [
        "\"What consistency model does this actually need?\"",
        "\"Relational, document, or something else — and why?\"",
        "\"How does this data system behave when the network partitions?\"",
    ],
    "security": [
        "\"What is the threat model, and what is the real attack surface?\"",
        "\"Is this cryptography / disclosure / policy choice sound?\"",
        "\"Are we adding security or just security theater?\"",
    ],
    "finops-cost": [
        "\"What is this actually costing us, per unit of value?\"",
        "\"Where is the cloud bill leaking, and who owns it?\"",
        "\"Is this spend an investment or waste?\"",
    ],
    "languages-runtimes": [
        "\"Which language / runtime fits this problem, and what do we trade away?\"",
        "\"Static or dynamic typing here — what is the real cost?\"",
        "\"Is this language-design or governance decision sustainable?\"",
    ],
    "systems-programming": [
        "\"Why is this slow, and where does the time actually go?\"",
        "\"Own the hardware/OS layer or abstract it away?\"",
        "\"Is this complexity essential or accidental?\"",
    ],
    "web-and-frontend": [
        "\"Which frontend framework / rendering model fits this product?\"",
        "\"Compiler, virtual DOM, or signals — what is the real tradeoff?\"",
        "\"How do we keep the web app fast and maintainable at scale?\"",
    ],
    "architecture-testing-craft": [
        "\"Monolith or microservices — and are we tall enough for the latter?\"",
        "\"How do we test this without coupling tests to implementation?\"",
        "\"Where are the real domain boundaries?\"",
    ],
    "devops-platform": [
        "\"How do we ship faster without breaking reliability?\"",
        "\"What do the DORA / DevEx metrics say, and what do they miss?\"",
        "\"Do we need a platform team here, and what is its product?\"",
    ],
    "ai-assisted-coding": [
        "\"How does AI change how this gets built?\"",
        "\"Agentic IDE, Copilot-style assist, or neither?\"",
        "\"What does 'engineering at a higher level of abstraction' mean for this team?\"",
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
        slugs = info["personas"]
        title = CELL_TITLES[cell_id]
        rows = []
        persona_fms = {s: fm(s) for s in slugs}
        for s in slugs:
            f = persona_fms[s]
            name = f.get("real_name", s)
            aff = first(f.get("affiliations_2026"))
            role = f.get("cell_role", "")
            sig = first(f.get("signature_moves"))
            status = f.get("status", "active")
            star = " *(archetype)*" if status == "archetype" else ""
            rows.append(f"| `{s}` | {name}{star} | {aff} | {role} | {sig} |")

        # within-cell productive tensions
        tensions = []
        cellset = set(slugs)
        seen = set()
        for s in slugs:
            for opp in (persona_fms[s].get("productive_conflict_with") or []):
                if opp in cellset:
                    key = tuple(sorted((s, opp)))
                    if key not in seen:
                        seen.add(key)
                        a, b = key
                        tensions.append(
                            f"- **{persona_fms[a].get('real_name', a)} ↔ "
                            f"{persona_fms[b].get('real_name', b)}** "
                            f"(`{a}` ↔ `{b}`)"
                        )
        tension_block = "\n".join(tensions) if tensions else (
            "- No within-cell productive-conflict pairs recorded. Tension in this "
            "cell comes primarily from cross-cell pairings surfaced by the orchestrator."
        )

        summon = "\n".join(f"- {q}" for q in WHEN_TO_SUMMON[cell_id])

        doc = f"""---
cell_id: {cell_id}
team: engineering-super-intelligence
personas_count: {len(slugs)}
last_updated: {LAST_UPDATED}
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

{tension_block}

## How this cell maps to /SI-Eng commands

This cell is one lens the orchestrator (`/SI-Eng-Orchestrate`) draws on when scoring
a 16–32 persona team for a prompt. Summon it directly with
`/SI-Eng-Huddle {cell_id} "<topic>"` when the question lands squarely in this domain,
or let an action verb (`/SI-Eng-Decide`, `/SI-Eng-Tradeoff`, `/SI-Eng-Stress-Test`, …)
pull the most relevant members into a cross-cell panel.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/engineering/scripts/build_cells.py`. Re-run after persona edits.
"""
        (CELLS_DIR / f"{cell_id}.md").write_text(doc, encoding="utf-8")
        written += 1
        print(f"  wrote cells/{cell_id}.md ({len(slugs)} personas, {len(tensions)} tensions)")
    print(f"Wrote {written} cell docs.")


if __name__ == "__main__":
    main()
