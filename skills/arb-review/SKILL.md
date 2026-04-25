---
name: pmstudio-arb
description: Generate an Architecture Review Board (ARB) presentation in Coco Inc's standard 11-slide format. Use when someone asks to "create an ARB deck", "architecture review presentation", "prepare for architecture review board", "ARB slides", or needs to present a product/platform architecture for sign-off. Reads PRD, architecture maps, and project memory to pre-fill technical content. Produces a self-contained HTML slide deck.
---

# ARB Review — Architecture Review Board Presentation

## Purpose

Generates an 11-slide architecture review presentation following Coco Inc's standard ARB format. Used when a product needs architecture sign-off for a new instance, major integration, platform migration, or periodic review.

## Process

### Step 1: Read Context

**Required sources (read all that exist):**
- `CLAUDE.local.md` — project context, architecture decisions, stakeholders, ProdID
- `PRD/*.html` or `PRD/*.md` — requirements, NFRs, technical considerations, integrations, data model
- `Architecture/` or `*Architecture*.html` — existing diagrams, maps

**Optional sources:**
- `.sync-watch.json` — project name
- `Operational/DR-Plan*.html` — RTO/RPO targets (for slide 8)
- `Data/Stakeholder-Directory.*` — presenter and audience names

### Step 2: Ask Discovery Questions

Only ask what cannot be inferred from context:

1. **Review type?** New Product / Major Change / Periodic Review / Decommission
2. **Data classification?** Purple / Red / Yellow / Green (if not in PRD)
3. **Audience?** Firm-level ARB / Department-level / Technical review
4. **Known constraints or mandates?** (e.g., "must use existing Snowflake instance")
5. **Decision you need?** Approve / Approve-with-conditions / Defer — what specifically?

### Step 3: Generate 11-Slide Deck

**Output:** `Presentations/ARB-Review-{ProductName}-{Date}.html`

Self-contained HTML file with:
- System fonts (no CDN dependencies)
- Click/keyboard navigation between slides
- Print CSS for PDF export
- Mermaid.js (CDN) for architecture diagrams

**Slide structure — see `references/arb-format.md` for section details:**

| # | Slide | Key Content |
|---|-------|-------------|
| 1 | Title & Context | Product name, ProdID, review type, date, presenters |
| 2 | Business Context | Problem statement, strategic alignment, sponsor |
| 3 | Current State | AS-IS architecture (Mermaid diagram), pain points |
| 4 | Proposed Architecture | TO-BE architecture (Mermaid diagram), what changes |
| 5 | Data Architecture | Data classification, flows, retention, residency |
| 6 | Security & Access | AuthN/AuthZ, RBAC, encryption, CUECs |
| 7 | Integration Points | Upstream/downstream, protocols, error handling |
| 8 | NFRs & SLAs | Performance, availability, RTO/RPO, scalability |
| 9 | Risk Assessment | Architecture risks, mitigations, residual acceptance |
| 10 | Implementation Plan | Phases, timeline, rollback, blast radius |
| 11 | Decision Request | What you need from the board, options, recommendation |

### Step 4: Populate Content

For each slide, pull from project sources:

- **Slide 1**: Product name and ProdID from CLAUDE.local.md. Review type from Step 2. Presenters from stakeholder directory.
- **Slides 3-4**: Generate Mermaid diagrams from PRD architecture section and Architecture maps. If current-state diagram exists, use it. If not, build from PRD integrations and technical considerations.
- **Slide 5**: Data classification from PRD or discovery. Data flows from integrations section. Retention from NFRs.
- **Slide 6**: RBAC from PRD. CUECs from operationalization section. SSO/AuthN from technical considerations.
- **Slide 7**: Extract all integration points from PRD. Add protocol, frequency, error handling.
- **Slide 8**: Pull NFRs directly from PRD table. RTO/RPO from DR plan if it exists.
- **Slide 9**: Pull risks from PRD risk section. Add architecture-specific risks.
- **Slide 10**: Pull timeline from PRD. Add rollback strategy.
- **Slide 11**: Decision request from Step 2. Frame options with recommendation.

### Step 5: Present for Review

Show the deck outline with key content per slide. Ask:
- "Does this cover the right scope?"
- "Any slides that need different emphasis?"
- "Who are the presenters for slide 1?"

Apply feedback, then write the file.

## Critical Rules

1. **Mermaid diagrams are mandatory** for slides 3 and 4. Architecture reviews without diagrams fail.
2. **Data classification must be explicit.** If unknown, mark as "TBD — requires classification" in red. Never assume.
3. **Slide 11 must have a clear ask.** Not "please review" but "approve this architecture for production deployment" or "approve with condition: validate cascading before Phase 2."
4. **No implementation details on architecture slides.** Show components, interfaces, and data flows — not code, configs, or step-by-step procedures.
5. **Keep it to 11 slides.** If more content is needed, add appendix slides clearly labeled "APPENDIX" after slide 11.
