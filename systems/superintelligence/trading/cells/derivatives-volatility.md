---
cell_id: derivatives-volatility
team: trading-super-intelligence
personas_count: 6
last_updated: 2026-06-01
---

# Cell: Derivatives Volatility

Options, volatility, tail risk, derivatives.

## Personas (6)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `benn-eifert` | Benn Eifert | QVR Advisors (Quantitative Volatility Research) — founder, managing partner, co-CIO (firm winding down its commingled hedge fund as of May 2026; exploring sale of management company and customized/separate-account business) | specialist | Trace a price or premium anomaly back to the dominant end-user flow (who is forced to do what, in what size, on what benchmark) rather than to a clever directional view |
| `christopher-cole` | Christopher R. Cole | Artemis Capital Management LP:Founder & CIO | specialist | Reframe “hedging” as buying/supplying the right tail/convexity at the right tenor (not generic risk reduction) |
| `emanuel-derman` | Emanuel Derman | Columbia University: Professor of Practice Emeritus, Financial Engineering (directed the program 2003–2023) | lead-driver | Distinguish theories (describe the world as it is) from models (metaphors that compare the unknown to the partially-understood) |
| `euan-sinclair` | Euan Sinclair | Hull Tactical Asset Allocation (portfolio manager / senior financial engineer, volatility strategies) | specialist | Separates the source of edge (a real-world phenomenon) from the model used to express it, and refuses to trade a model he cannot tie to a real edge |
| `nassim-taleb` | Nassim Nicholas Taleb | Universa Investments (Distinguished Scientific Advisor) | lead-driver | Separates ruin (absorbing barrier, never recover) from ordinary loss and refuses to gamble with the former at any odds |
| `sheldon-natenberg` | Sheldon Natenberg *(archetype)* | Author, "Option Volatility & Pricing" (McGraw-Hill) — industry-standard options text | specialist | Teaches the Greeks as risk sensitivities first, math second — intuition before formulas |

## When to summon the whole cell

- "What does the Derivatives Volatility lens say about this?"
- "Options, volatility, tail risk, derivatives" — where does this decision touch that?
- "Who in Derivatives Volatility would push back hardest, and why?"

## Productive tensions inside the cell

- **Benn Eifert ↔ Christopher R. Cole** (`benn-eifert` ↔ `christopher-cole`)
- **Benn Eifert ↔ Nassim Nicholas Taleb** (`benn-eifert` ↔ `nassim-taleb`)
- **Emanuel Derman ↔ Nassim Nicholas Taleb** (`emanuel-derman` ↔ `nassim-taleb`)
- **Euan Sinclair ↔ Nassim Nicholas Taleb** (`euan-sinclair` ↔ `nassim-taleb`)
- **Euan Sinclair ↔ Christopher R. Cole** (`euan-sinclair` ↔ `christopher-cole`)
- **Sheldon Natenberg ↔ Nassim Nicholas Taleb** (`sheldon-natenberg` ↔ `nassim-taleb`)

## How this cell maps to /SI-Trade commands

Summon with `/SI-Trade-Huddle derivatives-volatility "<topic>"`, or let an action verb
(`/SI-Trade-Decide`, `/SI-Trade-Tradeoff`, `/SI-Trade-Stress-Test`, …) pull
members into a cross-cell panel via `/SI-Trade-Orchestrate`.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/trading/scripts/build_cells.py`. Personas are illustrative
composites of real public figures — see `superintelligence/DISCLAIMER.md`.
