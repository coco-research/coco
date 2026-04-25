# Deliverable Pipeline Workflow

> One PRD, many outputs. Generate an entire documentation suite from a single source of truth.

## The Concept

A well-written PRD contains all the information needed to produce a dozen different deliverables. Instead of writing each document from scratch, you generate them from the PRD — each deliverable pulls from specific PRD sections and reshapes the content for a different audience and purpose.

This approach guarantees consistency. When the PRD changes, every downstream deliverable can be regenerated with the updated information. No more conflicting details between your presentation deck and your technical architecture document.

---

## The Source of Truth

The PRD's 13 sections map to downstream deliverables as follows:

| PRD Section | Feeds Into |
|-------------|-----------|
| Overview + Problem Statement | Presentation deck (intro slides), Launch email (opening paragraph) |
| Goals + Success Metrics | Presentation deck (outcomes slide), Governance docs |
| User Personas + Stories | Presentation deck (user slide), Release notes (user-facing language) |
| Functional Requirements | Technical Architecture doc, Test plans |
| Non-Functional Requirements | Disaster Recovery Plan, Architecture Review Board deck |
| Technical Architecture | Architecture doc, ARB deck, DR Plan |
| Data Model | Architecture doc, DR Plan (backup scope) |
| API Design | Architecture doc, Integration guides |
| UI/UX Requirements | Presentation deck (demo slides), Design specs |
| Timeline + Milestones | Presentation deck (roadmap slide), Release notes (version plan) |
| Risks + Mitigations | DR Plan, Incident Response Plan, ARB deck (risk slide) |

---

## Deliverable Types

### 1. Presentation Deck
**Audience:** Stakeholders, leadership, cross-functional teams
**Sections pulled from PRD:** Overview, Problem Statement, Goals, Personas, UI/UX, Timeline, Risks
**Structure:**
- Title slide with product name and one-line value proposition
- Problem slide — the pain point with data
- Solution slide — what the product does (high-level)
- User slide — who benefits and how
- Demo/mockup slides — key screens or flows
- Architecture slide — simplified system diagram
- Roadmap slide — phased delivery timeline
- Ask slide — what you need (approval, resources, feedback)

**Tips:**
- Keep slides visual. Move details to speaker notes.
- One idea per slide. If a slide needs two minutes to explain, split it.
- Include a "what we are NOT building" slide to manage scope expectations.

### 2. Technical Architecture Document
**Audience:** Engineering team, architecture review board
**Sections pulled from PRD:** Technical Architecture, Data Model, API Design, Non-Functional Requirements
**Structure:**
- System overview and context diagram (C4 Level 1)
- Container diagram (C4 Level 2) — services, databases, external systems
- Component diagram for complex services (C4 Level 3)
- Data flow diagrams for key workflows
- Technology choices with rationale
- Non-functional requirements and how the architecture meets them
- Deployment architecture (environments, CI/CD, monitoring)

### 3. Disaster Recovery Plan (DR Plan)
**Audience:** Operations, compliance, architecture review board
**Sections pulled from PRD:** Non-Functional Requirements, Technical Architecture, Data Model, Risks
**Structure:**
- Recovery objectives — RTO (Recovery Time Objective) and RPO (Recovery Point Objective)
- System classification (Tier 1/2/3 criticality)
- Backup strategy — what is backed up, frequency, retention period, storage location
- Recovery procedures — step-by-step for each failure scenario
- Communication plan — who to notify, escalation chain
- Testing schedule — when DR procedures are tested

### 4. Incident Response Plan (IRP)
**Audience:** On-call engineers, operations, management
**Sections pulled from PRD:** Non-Functional Requirements, Technical Architecture, Risks
**Structure:**
- Severity levels (SEV1-SEV4) with definitions and examples
- Detection — monitoring, alerting, and escalation triggers
- Response procedures by severity level
- Communication templates (internal, external, executive)
- Post-incident review process
- Runbooks for known failure modes

### 5. Release Notes
**Audience:** End users, customer success, support teams
**Sections pulled from PRD:** User Stories, Functional Requirements, Timeline
**Structure:**
- Version number and release date
- New features — described in user-facing language (not technical jargon)
- Improvements — enhancements to existing features
- Bug fixes — resolved issues
- Known issues — acknowledged limitations
- Migration notes — if users need to take action

**Tips:**
- Write from the user's perspective: "You can now..." not "We implemented..."
- Group by feature area, not by sprint or ticket number
- Include screenshots or short descriptions for visual changes

### 6. Launch Email
**Audience:** Internal stakeholders, external users, or both
**Sections pulled from PRD:** Overview, Problem Statement, Goals, User Stories, Timeline
**Structure:**
- Subject line — clear, action-oriented
- Opening — the problem this solves (one sentence)
- What is new — 3-5 bullet points of key capabilities
- Who benefits — which teams or user groups
- How to get started — link, instructions, or next steps
- Timeline — when it is available
- Contact — who to reach for questions

### 7. Governance Documentation
**Audience:** Compliance, legal, audit, architecture review board
**Sections pulled from PRD:** Goals, Non-Functional Requirements, Data Model, Risks
**Structure:**
- Data classification and handling requirements
- Access control model (who can access what)
- Audit trail requirements
- Compliance mapping (which regulations apply and how they are met)
- Review and approval workflow

---

## Maintaining Consistency Across Deliverables

1. **Single source of truth.** The PRD is the canonical document. If a detail conflicts between the PRD and a deliverable, the PRD wins and the deliverable is regenerated.

2. **Regenerate, do not patch.** When the PRD changes, regenerate affected deliverables rather than manually editing them. Manual patches create drift.

3. **Version alignment.** All deliverables generated from the same PRD version should share a version identifier (e.g., "Generated from PRD v2.1, 2026-03-01").

4. **Cross-reference explicitly.** Each deliverable should reference the PRD section it draws from. This makes traceability auditable: "See PRD Section 8: Technical Architecture for full component details."

5. **Review the PRD first.** Before generating deliverables, validate the PRD using the validation checklist in `prd-generation.md`. Garbage in, garbage out — a weak PRD produces weak deliverables.

---

## Generation Order

For best results, generate deliverables in this order:

1. **Technical Architecture doc** — validates that the PRD's technical sections are coherent
2. **DR Plan and IRP** — forces you to think through failure modes early
3. **Presentation deck** — synthesizes the narrative for stakeholders
4. **Release notes** — translates technical features into user language
5. **Launch email** — distills everything into the shortest possible format
6. **Governance docs** — captures compliance and audit requirements

This order moves from most detailed to most summarized. Issues found in early deliverables (e.g., a missing component in the architecture doc) feed back into the PRD before less detailed deliverables are generated.
