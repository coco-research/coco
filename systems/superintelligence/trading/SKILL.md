---
name: trading-super-intelligence
team: trading
personas: 43
cells: 8
command_prefix: /SI-Trade
last_updated: 2026-06-01
---

# Trading Super Intelligence Team

Trading Super Intelligence Team. Named real-world personas across 8 cells. Built local-first (LM Studio) and validator-gated. Illustrative composites; see DISCLAIMER.md.

**43 native personas** (0 cross-listed) across **8 cells**. Real public figures
rendered as illustrative composites — see `superintelligence/DISCLAIMER.md`. Built local-first +
Claude-research, validator-gated (real cited URLs, no fabrication).

## Cells

| Cell | Personas | Focus |
|---|---|---|
| `macro-discretionary` | 8 | Discretionary global-macro and hedge-fund trading. |
| `quant-systematic` | 7 | Systematic/quant strategies, factors, ML-in-markets. |
| `derivatives-volatility` | 6 | Options, volatility, tail risk, derivatives. |
| `microstructure-execution` | 4 | Market microstructure, execution, HFT, technical trading. |
| `fixed-income-rates` | 5 | Bonds, rates, credit, monetary plumbing. |
| `risk-systemic` | 4 | Trading/market risk management and systemic risk. |
| `crypto-digital-assets` | 5 | Crypto/digital-asset trading and market structure. |
| `trader-craft-psychology` | 4 | What makes great traders — psychology, discipline, the meta-craft. |

## Command surface

- **Orchestrate (smart panel):** `/SI-Trade-Orchestrate "<prompt>"` → picks 16-32 personas + approval gate
- **Action verbs:** `/SI-Trade-Decide` · `-Tradeoff` · `-Pre-Mortem` · `-Review` · `-Stress-Test` · `-Plan` · `-Design` · `-Analyse` · `-Vote` · `-Debug` · `-Defend` · `-Roast` · `-Post-Mortem` · `-Re-Analyse` · `-Full-Cycle`
- **Identity:** `/SI-Trade-Ask <slug> "<q>"` · `-Huddle <cell> "<topic>"` · `-Meeting "<prompt>"` · `-Read <slug>`
- **Roster/maintenance:** `/SI-Trade-Recruit` · `-Refresh` · `-VoiceCheck` · `-Verify`

## Cross-team

For multi-domain decisions, the top-level `/SI-Orchestrate` (+ `/SI-<Verb>`) routes ACROSS teams
via `superintelligence/scripts/meta_select.py` (local nomic-embed). This team auto-joins that panel.

## Source of truth

`registry.json` (generated from persona frontmatter) + `cells/*.md` + `roster.json`.
Regenerate: `python3 trading/scripts/build_registry.py && python3 trading/scripts/build_cells.py`.
