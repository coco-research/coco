#!/usr/bin/env python3
"""Generate the 7 Finance cell docs from registry.json + persona frontmatter."""
from __future__ import annotations
import json, sys
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

FIN = Path(__file__).resolve().parents[1]
PERS = FIN / "personas"; CELLS = FIN / "cells"
REG = json.loads((FIN / "registry.json").read_text())
LAST = "2026-06-01"

TITLES = {
    "valuation-corporate-finance": "Valuation and Corporate Finance",
    "investing-capital-allocation": "Investing and Capital Allocation",
    "accounting-fpa-reporting": "Accounting, FP&A, and Reporting",
    "macro-economics": "Macro and Economics",
    "fintech-payments": "Fintech and Payments",
    "behavioral-decision-science": "Behavioral and Decision Science",
    "capital-markets-ma-private": "Capital Markets, M&A, and Private",
}
SUMMON = {
    "valuation-corporate-finance": ["\"What is this worth, intrinsically?\"", "\"DCF vs multiples vs market-implied expectations?\"", "\"Is the value story anchored to cash flows and ROIC?\""],
    "investing-capital-allocation": ["\"Buy, hold, or pass?\"", "\"Where is the margin of safety?\"", "\"Value or growth — and what does the cycle say?\""],
    "accounting-fpa-reporting": ["\"Do the numbers actually mean what they claim?\"", "\"Any accounting red flags / shenanigans?\"", "\"How should we run FP&A / forecast this?\""],
    "macro-economics": ["\"What does the macro regime imply for this decision?\"", "\"Rates, inflation, growth — where are we in the cycle?\"", "\"What's the policy / liquidity backdrop?\""],
    "fintech-payments": ["\"How does money/payments/embedded-finance change this?\"", "\"Build, buy, or partner on financial infrastructure?\"", "\"What's the fintech unit-economics reality?\""],
    "behavioral-decision-science": ["\"What bias is distorting this decision?\"", "\"Are we resulting, or judging the decision quality?\"", "\"How do narrative and psychology move this market?\""],
    "capital-markets-ma-private": ["\"IPO, M&A, or stay private — and at what terms?\"", "\"What do PE/VC returns and the data actually say?\"", "\"Distress / restructuring / bankruptcy risk?\""],
}


def fm(slug):
    t = (PERS / f"{slug}.md").read_text()
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
        fms = {s: fm(s) for s in slugs}
        rows = []
        for s in slugs:
            f = fms[s]
            star = " *(archetype)*" if f.get("status") == "archetype" else ""
            rows.append(f"| `{s}` | {f.get('real_name', s)}{star} | {first(f.get('affiliations_2026'))} | {f.get('cell_role', '')} | {first(f.get('signature_moves'))} |")
        cellset = set(slugs); seen = set(); tens = []
        for s in slugs:
            for opp in (fms[s].get("productive_conflict_with") or []):
                if opp in cellset and tuple(sorted((s, opp))) not in seen:
                    seen.add(tuple(sorted((s, opp))))
                    tens.append(f"- **{fms[s].get('real_name', s)} ↔ {fms[opp].get('real_name', opp)}** (`{s}` ↔ `{opp}`)")
        tb = "\n".join(tens) if tens else "- Cross-cell tension dominates; the orchestrator pairs these members with other cells."
        summon = "\n".join(f"- {q}" for q in SUMMON[cid])
        doc = f"""---
cell_id: {cid}
team: finance-super-intelligence
personas_count: {len(slugs)}
last_updated: {LAST}
---

# Cell: {TITLES[cid]}

{info['description']}

## Personas ({len(slugs)})

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
{chr(10).join(rows)}

## When to summon the whole cell

{summon}

## Productive tensions inside the cell

{tb}

## How this cell maps to /SI-Fin commands

Summon with `/SI-Fin-Huddle {cid} "<topic>"`, or let an action verb (`/SI-Fin-Decide`,
`/SI-Fin-Tradeoff`, `/SI-Fin-Stress-Test`, …) pull members into a cross-cell panel via
`/SI-Fin-Orchestrate`.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/finance/scripts/build_cells.py`.
"""
        (CELLS / f"{cid}.md").write_text(doc, encoding="utf-8")
        n += 1
        print(f"  wrote cells/{cid}.md ({len(slugs)} personas, {len(tens)} tensions)")
    print(f"Wrote {n} cell docs.")


if __name__ == "__main__":
    main()
