---
name: gtm-super-intelligence
team: gtm
personas: 23
cells: 7
command_prefix: /SI-GTM
last_updated: 2026-06-01
---

# Sales, GTM & Marketing Super Intelligence Team

Sales, GTM & Marketing Super Intelligence Team. Named real-world personas across 7 cells. Built local-first (LM Studio) and validator-gated. Illustrative composites; see DISCLAIMER.md.

**20 native personas** (3 cross-listed) across **7 cells**. Real public figures
rendered as illustrative composites — see `superintelligence/DISCLAIMER.md`. Built local-first +
Claude-research, validator-gated (real cited URLs, no fabrication).

## Cells

| Cell | Personas | Focus |
|---|---|---|
| `category-design-positioning` | 4 | Category creation, positioning, market framing, crossing the chasm. |
| `demand-gen-content-marketing` | 4 | Demand generation, content, SEO, audience building, inbound. |
| `sales-methodology-negotiation` | 6 | Sales process, methodology, enablement, negotiation. |
| `product-led-growth` | 1 | PLG, self-serve, freemium, product-as-the-go-to-market. |
| `brand-strategy` | 4 | Brand building, distinctiveness, marketing effectiveness science. |
| `pricing-monetization` | 2 | Pricing strategy, packaging, monetization, willingness-to-pay. |
| `customer-success-retention` | 2 | Post-sale expansion, retention, net revenue retention, CS as a discipline. |

## Command surface

- **Orchestrate (smart panel):** `/SI-GTM-Orchestrate "<prompt>"` → picks 16-32 personas + approval gate
- **Action verbs:** `/SI-GTM-Decide` · `-Tradeoff` · `-Pre-Mortem` · `-Review` · `-Stress-Test` · `-Plan` · `-Design` · `-Analyse` · `-Vote` · `-Debug` · `-Defend` · `-Roast` · `-Post-Mortem` · `-Re-Analyse` · `-Full-Cycle`
- **Identity:** `/SI-GTM-Ask <slug> "<q>"` · `-Huddle <cell> "<topic>"` · `-Meeting "<prompt>"` · `-Read <slug>`
- **Roster/maintenance:** `/SI-GTM-Recruit` · `-Refresh` · `-VoiceCheck` · `-Verify`

## Cross-team

For multi-domain decisions, the top-level `/SI-Orchestrate` (+ `/SI-<Verb>`) routes ACROSS teams
via `superintelligence/scripts/meta_select.py` (local nomic-embed). This team auto-joins that panel.

## Source of truth

`registry.json` (generated from persona frontmatter) + `cells/*.md` + `roster.json`.
Regenerate: `python3 gtm/scripts/build_registry.py && python3 gtm/scripts/build_cells.py`.
