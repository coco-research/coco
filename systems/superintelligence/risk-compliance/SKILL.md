---
name: risk-compliance-super-intelligence
team: risk-compliance
personas: 40
cells: 7
command_prefix: /SI-GRC
last_updated: 2026-06-01
---

# Risk & Compliance (GRC) Super Intelligence Team

Risk & Compliance (GRC) Super Intelligence Team. Named real-world personas across 7 cells. Built local-first (LM Studio) and validator-gated. Illustrative composites; see DISCLAIMER.md.

**28 native personas** (12 cross-listed) across **7 cells**. Real public figures
rendered as illustrative composites — see `superintelligence/DISCLAIMER.md`. Built local-first +
Claude-research, validator-gated (real cited URLs, no fabrication).

## Cells

| Cell | Personas | Focus |
|---|---|---|
| `privacy-data-protection` | 6 | Privacy law, data protection, GDPR/CCPA, privacy-by-design. |
| `ai-governance-responsible-ai` | 8 | AI governance, responsible AI, algorithmic accountability, EU AI Act / NIST RMF. |
| `regulatory-tech-policy` | 6 | Tech regulation, antitrust, platform policy, algorithmic-accountability journalism/law. |
| `security-governance` | 5 | Security governance, disclosure, threat policy (cross-listed from Engineering). |
| `erm-grc-leadership` | 6 | Enterprise risk management, GRC frameworks, internal audit, three-lines model. |
| `financial-crime-aml` | 4 | AML/KYC, sanctions, financial-crime compliance. |
| `model-systemic-risk` | 5 | Model risk, validation (SR 11-7), systemic/financial-stability risk (cross-listed from Trading). |

## Command surface

- **Orchestrate (smart panel):** `/SI-GRC-Orchestrate "<prompt>"` → picks 16-32 personas + approval gate
- **Action verbs:** `/SI-GRC-Decide` · `-Tradeoff` · `-Pre-Mortem` · `-Review` · `-Stress-Test` · `-Plan` · `-Design` · `-Analyse` · `-Vote` · `-Debug` · `-Defend` · `-Roast` · `-Post-Mortem` · `-Re-Analyse` · `-Full-Cycle`
- **Identity:** `/SI-GRC-Ask <slug> "<q>"` · `-Huddle <cell> "<topic>"` · `-Meeting "<prompt>"` · `-Read <slug>`
- **Roster/maintenance:** `/SI-GRC-Recruit` · `-Refresh` · `-VoiceCheck` · `-Verify`

## Cross-team

For multi-domain decisions, the top-level `/SI-Orchestrate` (+ `/SI-<Verb>`) routes ACROSS teams
via `superintelligence/scripts/meta_select.py` (local nomic-embed). This team auto-joins that panel.

## Source of truth

`registry.json` (generated from persona frontmatter) + `cells/*.md` + `roster.json`.
Regenerate: `python3 risk-compliance/scripts/build_registry.py && python3 risk-compliance/scripts/build_cells.py`.
