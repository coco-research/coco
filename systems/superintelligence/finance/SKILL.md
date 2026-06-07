---
name: finance-super-intelligence
team: finance
personas: 39
cells: 7
command_prefix: /SI-Fin
last_updated: 2026-06-01
---

# Finance Super Intelligence Team

Rijul's finance brain trust and decision partner. Named personas across 7 cells: valuation/corporate finance, investing, accounting/FP&A, macro, fintech, behavioral, and capital markets/M&A/private. Markets/quant/derivatives are reserved for the Trading team. Built local-first (LM Studio) and validator-gated. Invoked by /SI-Fin commands.

**39 native personas** (0 cross-listed) across **7 cells**. Real public figures
rendered as illustrative composites — see `superintelligence/DISCLAIMER.md`. Built local-first +
Claude-research, validator-gated (real cited URLs, no fabrication).

## Cells

| Cell | Personas | Focus |
|---|---|---|
| `valuation-corporate-finance` | 6 | Valuation, corporate finance, intrinsic value, capital structure. |
| `investing-capital-allocation` | 7 | Value / discretionary investing and capital allocation. |
| `accounting-fpa-reporting` | 4 | Forensic accounting, financial reporting, and FP&A practice. |
| `macro-economics` | 7 | Macro economists and policy / markets framing. |
| `fintech-payments` | 5 | Fintech, payments, banking-as-a-service, fintech investing. |
| `behavioral-decision-science` | 6 | Behavioral finance and decision-making under uncertainty. |
| `capital-markets-ma-private` | 4 | IPOs, M&A, private equity / VC finance, distress and restructuring. |

## Command surface

- **Orchestrate (smart panel):** `/SI-Fin-Orchestrate "<prompt>"` → picks 16-32 personas + approval gate
- **Action verbs:** `/SI-Fin-Decide` · `-Tradeoff` · `-Pre-Mortem` · `-Review` · `-Stress-Test` · `-Plan` · `-Design` · `-Analyse` · `-Vote` · `-Debug` · `-Defend` · `-Roast` · `-Post-Mortem` · `-Re-Analyse` · `-Full-Cycle`
- **Identity:** `/SI-Fin-Ask <slug> "<q>"` · `-Huddle <cell> "<topic>"` · `-Meeting "<prompt>"` · `-Read <slug>`
- **Roster/maintenance:** `/SI-Fin-Recruit` · `-Refresh` · `-VoiceCheck` · `-Verify`

## Cross-team

For multi-domain decisions, the top-level `/SI-Orchestrate` (+ `/SI-<Verb>`) routes ACROSS teams
via `superintelligence/scripts/meta_select.py` (local nomic-embed). This team auto-joins that panel.

## Source of truth

`registry.json` (generated from persona frontmatter) + `cells/*.md` + `roster.json`.
Regenerate: `python3 finance/scripts/build_registry.py && python3 finance/scripts/build_cells.py`.
