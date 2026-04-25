---
name: pmstudio-init
description: Use when starting a new project, onboarding to an existing product, or setting up a documentation ecosystem for any initiative. Scaffolds the standard document set, folder structure, project memory, and doc-sync config. Works for software products, consulting engagements, platform implementations, and governance programs.
---

# Project Docs — Standard Document Ecosystem

## Purpose

Every project needs the same core set of interconnected documents. This skill scaffolds a complete documentation ecosystem from day one so that:

- Nothing gets lost between meetings, decisions, and deliverables
- Every document has a clear owner, purpose, and update trigger
- The doc-sync watcher can automatically detect when documents go stale
- New team members can onboard by reading the folder structure alone

## When to Use

- `/project-docs init` — Scaffold a new project from scratch
- `/project-docs init --type consulting` — Use consulting template (meetings-heavy)
- `/project-docs init --type product` — Use product template (PRD-heavy)
- `/project-docs init --type implementation` — Use implementation template (vendor + config)
- `/project-docs audit` — Check an existing project against the standard and report gaps

## The Standard Document Set

Every project should have these **16 document types** organized in **6 categories**. Not every project needs all 16 — the skill asks which ones apply and only scaffolds what's needed. Documents 11-16 are generated on demand via dedicated slash commands in the `pm-ops` skill category.

### Category 1: Source of Truth (Root Documents)

These are authoritative — all other documents derive from them.

| # | Document | File Pattern | Purpose | Update Trigger |
|---|----------|-------------|---------|----------------|
| 1 | **PRD / Requirements** | `PRD/` or `Requirements/` | What we're building and why | Decisions, research findings, stakeholder feedback |
| 2 | **Project Memory** | `CLAUDE.local.md` | AI context — architecture, decisions, recent changes | Every session (auto-maintained) |

### Category 2: Source Documents (Inputs)

Raw inputs that feed the root documents. These are append-only — never edited after creation.

| # | Document | File Pattern | Purpose | Update Trigger |
|---|----------|-------------|---------|----------------|
| 3 | **Meeting Notes** | `Meeting-Notes/YYYY-MM-DD-Name.md` | Decisions, action items, context from calls | After every meeting |
| 4 | **Research** | `Research/Topic-Name.md` | Deep dives, competitive analysis, technical research | As needed |
| 5 | **Source Documents** | `Source-Documents/` | Contracts, emails, vendor docs, screenshots | When received |

### Category 3: Derived Documents (Outputs)

Generated from root + source documents. These go stale and need syncing.

| # | Document | File Pattern | Purpose | Update Trigger |
|---|----------|-------------|---------|----------------|
| 6 | **Presentation / Deck** | `Presentations/Name-vN.html` | Stakeholder-facing summary | PRD changes, new meetings, new decisions |
| 7 | **PRD Presentation** | `PRD/PRD-Presentation.html` | Slide version of PRD for reviews | PRD changes |
| 8 | **Architecture Map** | `Architecture/` | System diagrams, data flows, integration maps | Design decisions, technical research |
| 9 | **ARB Review** | `ARB/` | Architecture Review Board presentation (Coco Inc 11-slide format) | Architecture changes, pre-go-live |

Generate with: `/arb-review` — auto-populates from PRD + architecture + project registry data.

### Category 4: Operational Documents

Living documents that track ongoing state.

| # | Document | File Pattern | Purpose | Update Trigger |
|---|----------|-------------|---------|----------------|
| 10 | **Verification / Audit** | `Verification/` | Data verification, gap analysis, compliance checks | Before milestones |
| 11 | **Stakeholder Directory** | `Data/Stakeholder-Directory.xlsx` | Contact list with roles, groups, ownership | New people mentioned in meetings |
| 12 | **Change Log** | `Change-Log.md` | Running log of product/platform changes (config, users, modules) | After every change |
| 13 | **NFR Tracker** | `.nfr-status.json` | Cross-cutting readiness dashboard — tracks status of all document types | Continuous |

Generate with: `/change-log` (init or append) and `/nfr-tracker` (audit readiness).

### Category 5: Compliance & Resilience

Required for production systems. Generated on demand as go-live approaches.

| # | Document | File Pattern | Purpose | Update Trigger |
|---|----------|-------------|---------|----------------|
| 14 | **DR Plan** | `Operations/DR-Plan.md` | Disaster Recovery — RTO/RPO targets, failover, manual fallbacks | Pre-go-live, annually |
| 15 | **IRP** | `Operations/IRP.md` | Incident Response Plan — severity matrix, escalation, SOX implications | Pre-go-live, annually |
| 16 | **Recovery Plan** | `Operations/Recovery-Plan.md` | Step-by-step restoration runbooks per failure scenario | After DR + IRP created |

Generate with: `/dr-plan` → `/irp` → `/recovery-plan` (in dependency order).

### Category 6: Communications

Templates for stakeholder announcements. Generated on demand.

| Document | File Pattern | Purpose | Generate With |
|----------|-------------|---------|---------------|
| **Stakeholder Comms** | `Comms/Stakeholder-Comms.html` | Pre-filled templates: go-live, status, onboarding, incident, SteerCo | `/stakeholder-comms` |

## The Dependency Graph

```
Meeting Notes ──┬──→ PRD ──────────→ PRD Presentation
                │     │
Research ───────┤     ├──→ Main Presentation
                │     │
Source Docs ────┘     ├──→ Architecture Map
                      │
                      ├──→ /arb-review (ARB presentation)
                      │
                      ├──→ /dr-plan ────→ /recovery-plan
                      │
                      ├──→ /irp ────────→ /recovery-plan
                      │
                      ├──→ /change-log (append mode)
                      │
                      └──→ /stakeholder-comms

/nfr-tracker ──────→ Reads ALL of the above, reports readiness

All changes ──────────→ CLAUDE.local.md
                ──────→ Stakeholder Directory (if new people)
```

**Key rule:** Source documents (meetings, research) flow INTO root documents (PRD). Root documents flow INTO derived documents (presentations, architecture, ops docs). Never the reverse. The NFR tracker is read-only — it audits but never modifies.

## Staged Generation

Not all documents are needed on day one. The standard cadence:

| When | Generate | Command |
|------|----------|---------|
| **Day 1** (project start) | Folder structure, CLAUDE.local.md, .sync-watch.json | `/project-docs init` |
| **Week 1** (after first meetings) | PRD, Meeting Notes, Research | `/prd-generator` |
| **Ongoing** | Change Log, Meeting Notes | `/change-log`, manual |
| **Pre-kickoff** | ARB Review, Stakeholder Comms | `/arb-review`, `/stakeholder-comms` |
| **Pre-go-live** | DR Plan → IRP → Recovery Plan | `/dr-plan` → `/irp` → `/recovery-plan` |
| **Anytime** | Readiness check | `/nfr-tracker` |

## Process

### Step 1: Gather Project Context

Ask the user these questions (skip any they've already answered):

1. **Project name?** (used for folder name and CLAUDE.local.md header)
2. **What type of project?**
   - `product` — Building software (PRD-centric, Jira/Confluence integration)
   - `consulting` — Advisory/implementation engagement (meeting-notes-centric, stakeholder-heavy)
   - `implementation` — Deploying a vendor product (config-centric, vendor docs, phased rollout)
   - `governance` — Risk, compliance, controls (framework-centric, regulatory docs)
3. **One-line description?** (goes in CLAUDE.local.md overview)
4. **Who are the key stakeholders?** (seeds the stakeholder directory)
5. **What's the primary deliverable?** (determines which Tier 1 doc to scaffold first)
6. **Is this a git repo?** (affects .gitignore recommendations)

### Step 2: Scaffold Folder Structure

Create the folder structure based on project type. Use the template from `templates/folder-structures.md`.

**All types get:**
```
Project-Name/
├── CLAUDE.local.md
├── .sync-watch.json
├── .nfr-status.json          # NFR tracker state (created by /nfr-tracker)
├── Meeting-Notes/
├── Research/
├── Source-Documents/
├── Data/
├── Operations/               # DR Plan, IRP, Recovery Plan (created by slash commands)
├── Comms/                    # Stakeholder communication templates
└── _temp/
```

**Product type adds:**
```
├── PRD/
│   ├── PRD-Name.html (or .md)
│   └── PRD-Presentation.html
├── Architecture/
└── Verification/
```

**Consulting type adds:**
```
├── Presentations/
│   ├── Name-v1.html
│   └── _archive/
├── PRD/ (optional)
└── Verification/
```

**Implementation type adds:**
```
├── PRD/
│   ├── PRD-Name.html
│   └── PRD-Presentation.html
├── Presentations/
│   ├── Name-v1.html
│   └── _archive/
├── ARB/                      # Created by /arb-review
├── Architecture/
├── Verification/
├── Change-Log.md             # Created by /change-log
└── Source-Documents/
    ├── Contracts/
    ├── Emails/
    └── Screenshots/
```

**Governance type adds:**
```
├── Framework/
│   ├── Controls/
│   ├── Risks/
│   └── Policies/
├── Presentations/
├── Architecture/
└── Verification/
```

### Step 3: Create CLAUDE.local.md

Use the template from `templates/project-memory.md`. Pre-fill:
- Project name and description from Step 1
- Folder structure section (document what was created)
- Routing guide table (map "I need X" → "Go to Y")
- Empty sections for: Key Decisions, Recent Changes, Open Questions, Commands

### Step 4: Create .sync-watch.json

Generate based on project type and folder structure. Map:
- `watch_dirs` → all source document directories (Meeting-Notes, Research, etc.)
- `target_docs.tier1` → root + primary derived documents
- `target_docs.tier2` → secondary derived documents

Register the project in `~/.claude/sync-watch-projects.txt`.

### Step 5: Create Starter Files

For each document type the user selected, create a minimal starter:
- **Meeting Notes:** Create `Meeting-Notes/` with a `_template.md` file
- **PRD:** Trigger `/prd-generator` or create empty PRD scaffold
- **Presentation:** Create empty `Presentations/Name-v1.html`
- **Stakeholder Directory:** Create `Data/Stakeholder-Directory.xlsx` or `.md` with initial contacts

### Step 6: Report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PROJECT DOCS ► SCAFFOLDED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Project: [Name]
Type: [product/consulting/implementation/governance]
Documents: [N] types configured
Sync watcher: Registered

Folder structure:
[tree output]

Next steps:
1. Start capturing meeting notes in Meeting-Notes/
2. Begin your PRD: /prd-generator
3. The doc-sync watcher will alert you when documents need updating
```

## Audit Mode

When invoked with `/project-docs audit`:

1. Read `.sync-watch.json` (if exists) or scan folder structure
2. Check against the standard document set
3. Report:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PROJECT DOCS ► AUDIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Document Type | Status | Path | Last Updated |
|---------------|--------|------|--------------|
| PRD | ✓ | PRD/ProductB-PRD.html | 2026-03-17 |
| Project Memory | ✓ | CLAUDE.local.md | 2026-03-17 |
| Meeting Notes | ✓ | Meeting-Notes/ (3 files) | 2026-03-13 |
| Research | ✓ | Research/ (4 files) | 2026-03-17 |
| Presentation | ✓ | Presentations/v5.html | 2026-03-12 |
| Architecture | ✓ | ProductB-Architecture-Map.html | 2026-03-13 |
| Verification | ✓ | Verification/ (2 files) | 2026-03-12 |
| Stakeholder Dir | ✗ MISSING | — | — |
| Source Documents | ✓ | Source-Documents/ | 2026-03-12 |
| Sync Config | ✓ | .sync-watch.json | 2026-03-17 |

Coverage: 9/10 (90%)
Missing: Stakeholder Directory
```

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Meeting notes | `YYYY-MM-DD-Attendee-or-Topic.md` | `2026-03-17-{Stakeholder}-Kickoff.md` |
| Research | `Topic-Name.md` (no date suffix) | `Access-Management-Research.md` |
| PRD | `ProjectName-PRD.html` or `PRD-Name.html` | `ProductB-PRD-Control-Framework.html` |
| Presentation | `Name-vN.html` | `AppName-v5.html` |
| Source docs | Original filename | `20251215-TGT-POC-Writeup.docx` |
| Architecture | `Architecture-Map.html` or descriptive | `ProductB-Architecture-Map.html` |

## Integration with Other Skills

### pm-core (Document Creation & Sync)

| Skill | How project-docs connects |
|-------|--------------------------|
| `/prd-generator` | Called in Step 5 if user wants PRD scaffolded |
| `/doc-sync` | `.sync-watch.json` created in Step 4 enables automatic sync detection |
| `/prd-mastery` | PRD folder structure follows prd-mastery's `prds/` convention |
| `CLAUDE.local.md` | Template from `core/memory/project-memory-template.md` |

### pm-ops (Operational Documents — Generated On Demand)

| Skill | What it generates | When to run |
|-------|-------------------|-------------|
| `/nfr-tracker` | Readiness dashboard across all 16 doc types | Anytime — audits what exists vs what's missing |
| `/change-log` | Running log of product/platform changes | After project init, then ongoing |
| `/stakeholder-comms` | Pre-filled communication templates (6 types) | Before kickoffs, go-lives, status cycles |
| `/arb-review` | Coco Inc ARB presentation (11 slides) | Pre-go-live or when architecture review required |
| `/dr-plan` | Disaster Recovery plan with RTO/RPO | Pre-go-live |
| `/irp` | Incident Response Plan with escalation matrix | Pre-go-live (after DR plan) |
| `/recovery-plan` | Step-by-step restoration runbooks | Pre-go-live (after DR + IRP) |

**Dependency chain:** `/dr-plan` → `/irp` → `/recovery-plan` (each builds on the previous).
**Meta-command:** `/nfr-tracker` checks which of the above exist and reports gaps.

## Critical Rules

1. **Don't over-scaffold.** Only create directories the user confirmed they need. Empty folders are noise.
2. **Don't create placeholder content.** An empty `PRD.html` with boilerplate headers is worse than no file. Either use `/prd-generator` to make a real one, or leave it for later.
3. **Date everything.** CLAUDE.local.md entries use `[YYYY-MM-DD]` format. Meeting notes use date-first filenames.
4. **Archive, don't delete.** When presentations get major updates, move old version to `_archive/` before creating new one.
5. **Source docs are immutable.** Meeting notes and research files are never edited after creation. New information goes in a new file.
