---
name: strategy-super-intelligence
team: strategy
personas: 25
cells: 7
command_prefix: /SI-Strat
last_updated: 2026-06-01
---

# Strategy Super Intelligence Team

Strategy Super Intelligence Team. Named real-world personas across 7 cells. Built local-first (LM Studio) and validator-gated. Illustrative composites; see DISCLAIMER.md.

**23 native personas** (2 cross-listed) across **7 cells**. Real public figures
rendered as illustrative composites — see `superintelligence/DISCLAIMER.md`. Built local-first +
Claude-research, validator-gated (real cited URLs, no fabrication).

## Cells

| Cell | Personas | Focus |
|---|---|---|
| `competitive-strategy-advantage` | 3 | Competitive strategy, sources of durable advantage, positioning, industry structure. |
| `growth-innovation` | 6 | Growth strategy, disruption, new-market creation, innovation frameworks. |
| `corporate-portfolio-strategy` | 3 | Corporate-level strategy, portfolio, core/adjacency, where-to-play at the group level. |
| `strategy-execution-org` | 4 | Turning strategy into action: choices, simple rules, execution, org alignment. |
| `game-theory-decision` | 4 | Game theory, competitive dynamics, co-opetition, strategic decision structure. |
| `behavioral-strategy-bias` | 2 | Behavioral strategy, debiasing big decisions, narrative/halo traps. |
| `platform-ecosystem-strategy` | 3 | Platform, network-effect, ecosystem, and aggregation strategy. |

## Command surface

- **Orchestrate (smart panel):** `/SI-Strat-Orchestrate "<prompt>"` → picks 16-32 personas + approval gate
- **Action verbs:** `/SI-Strat-Decide` · `-Tradeoff` · `-Pre-Mortem` · `-Review` · `-Stress-Test` · `-Plan` · `-Design` · `-Analyse` · `-Vote` · `-Debug` · `-Defend` · `-Roast` · `-Post-Mortem` · `-Re-Analyse` · `-Full-Cycle`
- **Identity:** `/SI-Strat-Ask <slug> "<q>"` · `-Huddle <cell> "<topic>"` · `-Meeting "<prompt>"` · `-Read <slug>`
- **Roster/maintenance:** `/SI-Strat-Recruit` · `-Refresh` · `-VoiceCheck` · `-Verify`

## Cross-team

For multi-domain decisions, the top-level `/SI-Orchestrate` (+ `/SI-<Verb>`) routes ACROSS teams
via `superintelligence/scripts/meta_select.py` (local nomic-embed). This team auto-joins that panel.

## Source of truth

`registry.json` (generated from persona frontmatter) + `cells/*.md` + `roster.json`.
Regenerate: `python3 strategy/scripts/build_registry.py && python3 strategy/scripts/build_cells.py`.
