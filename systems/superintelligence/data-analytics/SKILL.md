---
name: data-analytics-super-intelligence
team: data-analytics
personas: 25
cells: 7
command_prefix: /SI-Data
last_updated: 2026-06-01
---

# Data & Analytics Super Intelligence Team

Data & Analytics Super Intelligence Team. Named real-world personas across 7 cells. Built local-first (LM Studio) and validator-gated. Illustrative composites; see DISCLAIMER.md.

**25 native personas** (0 cross-listed) across **7 cells**. Real public figures
rendered as illustrative composites — see `superintelligence/DISCLAIMER.md`. Built local-first +
Claude-research, validator-gated (real cited URLs, no fabrication).

## Cells

| Cell | Personas | Focus |
|---|---|---|
| `data-engineering-architecture` | 4 | Pipelines, warehouses, lakehouse, data mesh, modeling, orchestration. |
| `analytics-engineering-modern-stack` | 3 | dbt-era analytics engineering, the modern data stack, metrics layers. |
| `mlops-ml-systems` | 4 | Productionizing ML, ML system design, applied-ML engineering, eval. |
| `data-science-statistics` | 4 | Statistical practice, data-science tooling, decision intelligence. |
| `data-visualization` | 4 | Visualization theory, dataviz craft, communicating with data. |
| `data-governance-quality` | 4 | Data quality, observability, governance, contracts, leadership. |
| `experimentation-causal-inference` | 2 | A/B testing, controlled experiments, causal inference. |

## Command surface

- **Orchestrate (smart panel):** `/SI-Data-Orchestrate "<prompt>"` → picks 16-32 personas + approval gate
- **Action verbs:** `/SI-Data-Decide` · `-Tradeoff` · `-Pre-Mortem` · `-Review` · `-Stress-Test` · `-Plan` · `-Design` · `-Analyse` · `-Vote` · `-Debug` · `-Defend` · `-Roast` · `-Post-Mortem` · `-Re-Analyse` · `-Full-Cycle`
- **Identity:** `/SI-Data-Ask <slug> "<q>"` · `-Huddle <cell> "<topic>"` · `-Meeting "<prompt>"` · `-Read <slug>`
- **Roster/maintenance:** `/SI-Data-Recruit` · `-Refresh` · `-VoiceCheck` · `-Verify`

## Cross-team

For multi-domain decisions, the top-level `/SI-Orchestrate` (+ `/SI-<Verb>`) routes ACROSS teams
via `superintelligence/scripts/meta_select.py` (local nomic-embed). This team auto-joins that panel.

## Source of truth

`registry.json` (generated from persona frontmatter) + `cells/*.md` + `roster.json`.
Regenerate: `python3 data-analytics/scripts/build_registry.py && python3 data-analytics/scripts/build_cells.py`.
