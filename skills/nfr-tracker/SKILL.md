---
name: pmstudio-nfr
description: Detailed completeness audit of all project documents. Use when someone asks "are we ready for production", "audit our docs", "readiness check", "nfr tracker", or "what's missing". Do NOT use for a quick command listing — use /pmstudio instead. Scans every document for section-level completeness, reports staleness, and gives prioritized gap-closure recommendations.
---

# NFR Tracker — Operational Readiness Auditor

## Purpose

Meta-command that discovers all project documents, checks existence and freshness, and produces a readiness dashboard with prioritized recommendations for what to create or update next.

## Process

### Step 1: Detect Project Context

Read these files to understand the project:

1. **`CLAUDE.local.md`** — project name, type, architecture, folder structure
2. **`.sync-watch.json`** — registered documents and watch directories
3. Run `ls -R` on the project root to discover all files

Determine the **product lifecycle stage** from context:
- **Ideate/Build** — pre-production (DR/IRP not yet required)
- **Production** — live product (DR/IRP required)
- **Mixed** — some components live, some building (e.g., ProductA production + ProductB ideate)

### Step 2: Scan Document Registry

Check for each document type. For each, record: exists (Y/N), path, last modified date, stale (Y/N based on threshold).

**Document registry:**

| Document Type | Source Skill | File Pattern | Required When | Staleness |
|---------------|-------------|-------------|---------------|-----------|
| PRD | `/prd-generator` | `PRD/*.html`, `PRD/*.md` | Always | 30 days |
| Project Memory | (auto) | `CLAUDE.local.md` | Always | 7 days |
| Presentation | `/project-docs` | `Presentations/*.html` | Recommended | 30 days |
| Architecture Map | `/project-docs` | `Architecture/*.html`, `*Architecture*.html` | If PRD has architecture section | 60 days |
| Stakeholder Directory | `/project-docs` | `Data/Stakeholder*.xlsx`, `Data/Stakeholder*.md` | If >5 stakeholders | 30 days |
| Change Log | `/change-log` | `Data/Change-Log*.md` | Recommended | 14 days |
| ARB Presentation | `/arb-review` | `Presentations/ARB-*.html` | Before architecture review | 90 days |
| DR Plan | `/dr-plan` | `Operational/DR-Plan*.html` | Production | 180 days |
| Incident Response Plan | `/irp` | `Operational/IRP-*.html` | Production | 180 days |
| Recovery Procedures | `/recovery-plan` | `Operational/Recovery-*.html` | If DR Plan exists | 180 days |
| Verification Report | `/project-docs` | `Verification/*.md` | Before milestones | 60 days |

**Staleness calculation:** Compare file modification date to today. If `(today - last_modified) > threshold`, mark as STALE.

**Search strategy:** Use glob patterns first. If the project uses non-standard paths (from CLAUDE.local.md folder structure), adapt the search. Example: Some projects store PRDs in non-default paths like `ProductB-Control-Framework/PRD/` not `PRD/`.

### Step 3: Assess Completeness (Optional Deep Check)

If `--deep` flag or user requests "thorough check":

For each FOUND document, open it and check for key sections:

- **PRD**: Has executive summary, requirements, timeline, risks? Missing sections = partial.
- **DR Plan**: Has RTO/RPO targets, scenarios, procedures? Missing = partial.
- **IRP**: Has severity matrix, escalation contacts, playbooks? Missing = partial.

Without `--deep`, existence + freshness is sufficient.

### Step 4: Generate Recommendations

Prioritize missing/stale documents:

**Priority logic:**
1. **CRITICAL** — Production product missing DR or IRP
2. **HIGH** — Any required document missing or stale >2x threshold
3. **MEDIUM** — Recommended document missing or stale >1x threshold
4. **LOW** — Optional document missing

Each recommendation includes:
- What to create/update
- Why it matters
- The slash command to run

### Step 5: Output Report

**Console output (default):**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 NFR TRACKER ► READINESS REPORT — {Project Name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Lifecycle: {Production / Ideate / Mixed}
Scanned: {timestamp}

| Document              | Status  | Path              | Updated    | Stale? |
|-----------------------|---------|-------------------|------------|--------|
| ...                   | FOUND   | ...               | YYYY-MM-DD | No     |
| ...                   | MISSING | —                 | —          | —      |
| ...                   | FOUND   | ...               | YYYY-MM-DD | STALE  |

Coverage: N/M ({pct}%)    Stale: N    Missing: N

Recommendations:
1. [{priority}] {description}
   → Run: /{command}
...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Markdown file output (with `--format md`):**

Write to `Operational/Readiness-Report-{YYYY-MM-DD}.md` with the same content plus a header with project metadata.

## Modes

- `/nfr-tracker` — Full audit, console output
- `/nfr-tracker --format md` — Write report to file
- `/nfr-tracker --deep` — Check document completeness, not just existence
- `/nfr-tracker --scope {name}` — Filter to a specific product/instance within the project

## Critical Rules

1. **Read-only.** This skill never creates or modifies documents. It only reports.
2. **Adapt paths.** Don't assume standard folder structure. Read CLAUDE.local.md for actual paths.
3. **No false positives.** Only mark FOUND if the file has real content (>100 bytes). Empty scaffolds don't count.
4. **Date accuracy.** Use file system modification date, not content parsing, for freshness checks.
