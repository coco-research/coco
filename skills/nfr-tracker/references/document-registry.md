# Document Registry — All Tracked Document Types

## Document Types

| # | Type | Source Skill | Category | File Patterns | Required When | Staleness Threshold |
|---|------|-------------|----------|--------------|---------------|-------------------|
| 1 | PRD | `/prd-generator` | pm-core | `PRD/*.html`, `PRD/*.md`, `*/PRD/*.html` | Always | 30 days |
| 2 | Project Memory | (auto) | pm-core | `CLAUDE.local.md` | Always | 7 days |
| 3 | Main Presentation | `/project-docs` | pm-core | `Presentations/*.html`, `*/Presentations/*.html` | Recommended | 30 days |
| 4 | Architecture Map | `/project-docs` | pm-core | `Architecture/*.html`, `*Architecture*.html`, `*Architecture-Map*` | If PRD has arch section | 60 days |
| 5 | Stakeholder Directory | `/project-docs` | pm-core | `Data/Stakeholder*.xlsx`, `Data/Stakeholder*.md` | If >5 stakeholders | 30 days |
| 6 | Meeting Notes | (manual) | source | `Meeting-Notes/*.md`, `*/Meeting-Notes/*.md` | Recommended | 14 days (activity indicator) |
| 7 | Research | (manual) | source | `Research/*.md`, `*/Research/*.md` | Optional | N/A |
| 8 | Verification Report | `/project-docs` | pm-core | `Verification/*.md`, `*/Verification/*.md` | Before milestones | 60 days |
| 9 | Sync Config | `/doc-sync` | pm-core | `.sync-watch.json` | If doc-sync used | N/A |
| 10 | Change Log | `/change-log` | pm-ops | `Data/Change-Log*.md` | Recommended | 14 days |
| 11 | ARB Presentation | `/arb-review` | pm-ops | `Presentations/ARB-*.html` | Before arch review | 90 days |
| 12 | DR Plan | `/dr-plan` | pm-ops | `Operational/DR-Plan*.html` | If production | 180 days |
| 13 | Incident Response Plan | `/irp` | pm-ops | `Operational/IRP-*.html` | If production | 180 days |
| 14 | Recovery Procedures | `/recovery-plan` | pm-ops | `Operational/Recovery-*.html` | If DR plan exists | 180 days |
| 15 | Stakeholder Comms | `/stakeholder-comms` | pm-ops | `Comms/*.md` | Optional | N/A (event-driven) |

## Lifecycle Applicability

| Stage | Required Docs | Recommended Docs |
|-------|--------------|-----------------|
| **Ideate** | PRD, Project Memory | Presentation, Stakeholder Directory |
| **Build** | PRD, Project Memory, Architecture Map | Presentation, ARB, Change Log, Verification |
| **Production** | PRD, Project Memory, DR Plan, IRP | All of the above + Recovery Procedures |
| **Decommission** | Project Memory, Change Log | ARB (decommission type) |

## Completeness Check (Deep Mode)

When running `--deep`, check these key sections per document:

### PRD Completeness
- [ ] Executive Summary present
- [ ] Problem Statement present
- [ ] User Stories with acceptance criteria
- [ ] Success Metrics defined
- [ ] Timeline with milestones
- [ ] Risks with mitigations
- [ ] Open Questions section
- [ ] Version/change log

### DR Plan Completeness
- [ ] RTO/RPO targets (specific numbers)
- [ ] At least 3 disaster scenarios
- [ ] Recovery procedures per scenario
- [ ] Communication plan
- [ ] Manual workarounds documented
- [ ] Testing schedule with dates
- [ ] Contact list current

### IRP Completeness
- [ ] Severity matrix with 4 levels
- [ ] Escalation matrix with real names
- [ ] Response playbooks per severity
- [ ] Communication protocol
- [ ] Evidence preservation procedures
- [ ] PIR template
- [ ] Vendor escalation path

### ARB Completeness
- [ ] Architecture diagrams (AS-IS and TO-BE)
- [ ] Data classification stated
- [ ] Integration points listed
- [ ] NFR targets specified
- [ ] Risk assessment present
- [ ] Clear decision request on final slide
