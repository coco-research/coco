---
name: pmstudio
description: PM Studio command center. Use for a quick overview of available commands and document inventory. Use when someone says "pmstudio", "show commands", "what can I generate", or "project status". Do NOT use for detailed completeness audits — use /pmstudio-nfr instead. Shows document coverage dashboard and recommends which /pmstudio-* command to run next.
---

# PM Studio — Command Center

## Purpose

Single entry point for all PM document generation. Shows what exists, what's missing, and what to run next.

## Process

### Step 1: Read Project Context

Read these files (skip any that don't exist):
- `CLAUDE.local.md` — project overview, folder structure, recent changes
- `.sync-watch.json` — watched directories and target documents

### Step 2: Scan for Existing Documents

Use glob patterns to detect which document types exist in the current project:

| Document Type | Glob Pattern | Category |
|---------------|-------------|----------|
| PRD | `**/*PRD*.html`, `**/*PRD*.md`, `**/PRD/**` | CREATE |
| Presentation | `**/Presentations/*-v[0-9]*.html`, `**/*Presentation*.html` | CREATE |
| PRD Presentation | `**/*PRD*Presentation*.html`, `**/*PRD*-Presentation*.html` | CREATE |
| Architecture Map | `**/*Architecture*.html`, `**/*Map*.html` | CREATE |
| Verification | `**/Verification/**`, `**/*Verification*.md` | CREATE |
| Stakeholder Comms | `**/Comms/**`, `**/*Comms*.html` | CREATE |
| ARB Review | `**/ARB/**`, `**/*ARB*.html` | GOVERN |
| DR Plan | `**/Operations/*DR*`, `**/*DR-Plan*`, `**/*Disaster*` | GOVERN |
| IRP | `**/Operations/*IRP*`, `**/*Incident*Response*` | GOVERN |
| Recovery Plan | `**/Operations/*Recovery*`, `**/*Recovery-Plan*` | GOVERN |
| Change Log | `**/*Change-Log*`, `**/*Changelog*` | GOVERN |
| NFR Status | `.nfr-status.json` | GOVERN |
| Meeting Notes | `**/Meeting-Notes/**` | SOURCE |
| Research | `**/Research/**` | SOURCE |
| Source Documents | `**/Source-Documents/**` | SOURCE |
| Stakeholder Directory | `**/Data/*Stakeholder*` | SOURCE |
| Project Memory | `CLAUDE.local.md` | SOURCE |
| Sync Config | `.sync-watch.json` | ORCHESTRATION |

For each match, note the file path and last-modified date.

### Step 3: Discover Installed Commands

List available `/pmstudio-*` commands by checking which skills are loaded. Present only commands that are actually installed.

### Step 4: Present Dashboard

Output this format (adapt to actual project data):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 PM STUDIO ► {Project Name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Coverage: {found}/{total scanned} document types

─── CREATE ────────────────────────────────────────────
  /pmstudio-prd          PRD / Requirements          {✓ path (version, date) | ✗ Missing}
  /pmstudio-deck         Stakeholder Presentation    {✓ | ✗ | ○ Not installed}
  /pmstudio-prd-deck     PRD Presentation            {✓ | ✗ | ○ Not installed}
  /pmstudio-arch-map     Architecture Map            {✓ | ✗ | ○ Not installed}
  /pmstudio-verify       Verification / Audit        {✓ | ✗ | ○ Not installed}
  /pmstudio-comms        Stakeholder Comms           {✓ | ✗}

─── GOVERN ────────────────────────────────────────────
  /pmstudio-arb          ARB Review                  {✓ | ✗}
  /pmstudio-dr           Disaster Recovery Plan      {✓ | ✗}
  /pmstudio-irp          Incident Response Plan      {✓ | ✗}
  /pmstudio-recovery     Recovery Runbooks           {✓ | ✗}
  /pmstudio-changelog    Change Log                  {✓ | ✗}
  /pmstudio-nfr          Readiness Audit             → Run for full report

─── ORCHESTRATION ─────────────────────────────────────
  /pmstudio-sync         Cascade document updates    {✓ Config found | ✗ No .sync-watch.json}
  /pmstudio-init         Scaffold project            {✓ Initialized | ✗ Not initialized}

─── SOURCE (manual) ───────────────────────────────────
  Meeting Notes          {N files, latest: date}
  Research               {N files, latest: date}
  Source Documents       {N files}
  Stakeholder Directory  {✓ Found | ✗ Missing}
  Project Memory         {✓ CLAUDE.local.md | ✗ Missing}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommendations:
1. [{priority}] {what to do} → /pmstudio-{command}
2. [{priority}] {what to do} → /pmstudio-{command}
3. [{priority}] {what to do} → /pmstudio-{command}

Type a command to run it.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 5: Generate Recommendations

Priority rules:
- **CRITICAL**: Production system + no DR/IRP = critical
- **HIGH**: PRD exists but no ARB review; >30 days since last doc update; change log missing with many changes in CLAUDE.local.md
- **MEDIUM**: Missing stakeholder comms before a kickoff; no architecture map for implementation project
- **LOW**: Missing optional docs (recovery plan, verification)

Show top 3 recommendations only. Each must include the exact `/pmstudio-*` command to run.

## Arguments

- `/pmstudio` — full dashboard (default)
- `/pmstudio --deep` — delegates to `/pmstudio-nfr` for detailed readiness audit

## Critical Rules

1. **Read-only.** This command NEVER generates or modifies documents. It only reports status and recommends commands.
2. **Adapt to project.** Don't show hardcoded paths. Glob the actual project and show what's really there.
3. **Mark uninstalled commands.** If a `/pmstudio-*` subcommand isn't installed, show it as `○ Not installed` (not ✗ Missing).
4. **Show real dates.** For found documents, show the actual last-modified date, not just ✓.
5. **Be concise.** The dashboard should fit in one screen. No lengthy explanations.
