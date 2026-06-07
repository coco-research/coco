---
cell_id: quant-systematic
team: trading-super-intelligence
personas_count: 7
last_updated: 2026-06-01
---

# Cell: Quant Systematic

Systematic/quant strategies, factors, ML-in-markets.

## Personas (7)

| Slug | Name | Affiliation (2026) | Cell role | Signature |
|---|---|---|---|---|
| `andrew-lo` | Andrew W. Lo | MIT Sloan: Charles E. and Susan T. Harris Professor | specialist | Reconcile opposing camps (efficient markets vs behavioral) via evolutionary dynamics |
| `cliff-asness` | Clifford Scott Asness | AQR Capital Management — Founder, Managing Principal & Chief Investment Officer | lead-driver | Pairs value and momentum together because their drawdowns are negatively correlated — diversifying the behavioral risk of each |
| `ed-thorp` | Edward O. Thorp | President, Edward O. Thorp & Associates (Newport Beach, California) | validator | Demand a specific, definable, mathematically expressible edge before risking capital — otherwise default to index funds |
| `ernest-chan` | Ernest P. Chan | Founder & Chief Scientist, PredictNow.ai | specialist | Reframes ML's job from predicting market direction to predicting the probability that a given trade or strategy will work in the current regime (Corrective AI / meta-labeling) |
| `jim-simons` | James Harris "Jim" Simons *(archetype)* | Renaissance Technologies (founder, 1978; Medallion Fund est. 1988) — legacy | validator | Treat price action as a noisy signal-processing problem, not an economic narrative |
| `marcos-lopez-de-prado` | Marcos Lopez de Prado | Abu Dhabi Investment Authority (ADIA) — Global Head of Quantitative Research & Development | specialist | Demand a causal theory before the backtest — 'absent a theory, claims are associational and likely false' |
| `robert-litterman` | Robert B. Litterman | Kepos Capital (founding partner, chairman of the Risk Committee) | specialist | Make expected returns an output, not an input — start from market equilibrium, then blend in views with confidence weights |

## When to summon the whole cell

- "What does the Quant Systematic lens say about this?"
- "Systematic/quant strategies, factors, ML-in-markets" — where does this decision touch that?
- "Who in Quant Systematic would push back hardest, and why?"

## Productive tensions inside the cell

- **Ernest P. Chan ↔ James Harris "Jim" Simons** (`ernest-chan` ↔ `jim-simons`)
- **Marcos Lopez de Prado ↔ Edward O. Thorp** (`marcos-lopez-de-prado` ↔ `ed-thorp`)
- **Marcos Lopez de Prado ↔ Ernest P. Chan** (`marcos-lopez-de-prado` ↔ `ernest-chan`)

## How this cell maps to /SI-Trade commands

Summon with `/SI-Trade-Huddle quant-systematic "<topic>"`, or let an action verb
(`/SI-Trade-Decide`, `/SI-Trade-Tradeoff`, `/SI-Trade-Stress-Test`, …) pull
members into a cross-cell panel via `/SI-Trade-Orchestrate`.

## Source of truth

Generated from `registry.json` + persona frontmatter by
`superintelligence/trading/scripts/build_cells.py`. Personas are illustrative
composites of real public figures — see `superintelligence/DISCLAIMER.md`.
