---
cell_id: fixed-income-rates
team: trading-super-intelligence
personas_count: 5
last_updated: 2026-06-01
---

# Cell: Fixed Income Rates

Bonds, rates, credit, monetary plumbing.

## Personas (5)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `bill-gross` | William Hunt "Bill" Gross | PIMCO: co-founder (1971), former CIO and manager of the Total Return Fund (departed September 2014) | validator | Pioneered "total return" bond investing: actively trade duration, yield-curve, credit, and volatility for capital gains rather than passively clipping coupons |
| `frank-fabozzi` | Frank J. Fabozzi | Professor of Practice in Finance, Johns Hopkins University Carey Business School | specialist | Reducing a market to its first-principles cash-flow mechanics before any strategy is layered on |
| `jim-bianco` | Jim Bianco | Bianco Research: | specialist | Use market/positioning signals to test or challenge consensus macro narratives |
| `lacy-hunt` | Lacy Harris Hunt | Hoisington Investment Management Company (HIMCO) — Executive Vice President & Economist; Vice-Chairman, Strategic Investment Policy Committee | specialist | Frames every rate call through the marginal revenue product of debt — each new dollar of debt buys less GDP, so the price of debt (yields) should fall |
| `riccardo-rebonato` | Riccardo Rebonato | Professor of Finance, EDHEC Business School | specialist | Builds structural, no-arbitrage term-structure models that recover observed market prices while staying economically interpretable |

## When to summon the whole cell

- "What does the Fixed Income Rates lens say about this?"
- "Bonds, rates, credit, monetary plumbing" — where does this decision touch that?
- "Who in Fixed Income Rates would push back hardest, and why?"

## Productive tensions inside the cell

- **Riccardo Rebonato ↔ Lacy Harris Hunt** (`riccardo-rebonato` ↔ `lacy-hunt`)

## How this cell maps to /SI-Trade commands

Summon with `/SI-Trade-Huddle fixed-income-rates "<topic>"`, or let an action verb
(`/SI-Trade-Decide`, `/SI-Trade-Tradeoff`, `/SI-Trade-Stress-Test`, …) pull
members into a cross-cell panel via `/SI-Trade-Orchestrate`.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/trading/scripts/build_cells.py`. Personas are illustrative
composites of real public figures — see `superintelligence/DISCLAIMER.md`.
