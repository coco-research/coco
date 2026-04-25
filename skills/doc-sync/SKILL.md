---
name: pmstudio-sync
description: Use when a project has linked documentation artifacts (PRDs, presentations, meeting notes, architecture maps) that must stay synchronized. Detects which source files changed, identifies downstream documents needing updates, reads new content, and proposes specific edits with diffs before applying. Also use when a .sync-report.md exists in the project or user says "process sync report".
---

# Doc Sync — Cascading Document Updater

## What This Skill Does

Maintains consistency across a documentation ecosystem where one source change (e.g., a new meeting note) should cascade updates to multiple downstream documents (PRD, presentation, project memory).

**This is NOT a background watcher.** This skill is the Claude-side processor that:
1. Reads a sync report or detects changes directly
2. Extracts actionable content from new/modified source files
3. Proposes specific edits to each downstream target
4. Applies changes only after user approval

## Prerequisites

### Infrastructure (one-time setup)

The persistent detection layer runs outside Claude Code via `/project-sync init`:

| Component | Path | Purpose |
|-----------|------|---------|
| Orchestrator | `~/.claude/scripts/project-sync-orchestrator.sh` | Email search + file detection + report generation |
| launchd agent | `~/Library/LaunchAgents/com.claude.project-sync.<name>.plist` | Background scheduler (every 2 hours) |
| State dir | `~/.claude/state/<project-name>/` | Logs, timestamps, cached config (outside OneDrive) |

### Per-Project Config

Each project needs `.sync-watch.json` in its root:

```json
{
  "project_name": "My Project",
  "watch_dirs": ["docs/meeting-notes", "docs/research"],
  "target_docs": {
    "tier1": [
      {
        "path": "docs/PRD.html",
        "name": "Product Requirements",
        "update_from": ["meeting-notes", "research"],
        "what": "Requirements, user stories, decisions"
      }
    ],
    "tier2": [
      {
        "path": "docs/presentation.html",
        "name": "Stakeholder Deck",
        "update_from": ["meeting-notes"],
        "what": "Stakeholder updates, timeline changes"
      }
    ]
  },
  "ignore_patterns": [".*", "*.tmp", "~$*"],
  "file_types": [".md", ".html", ".docx", ".xlsx", ".pdf"]
}
```

## Invocation

### Automatic (via session hook)
When you start a Claude Code session in a watched project with pending changes:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 SYNC WATCHER ► 3 new/modified file(s) detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Say "process sync report" to review and apply updates.
```

### Manual
- `/doc-sync` — check for changes now and process
- `/doc-sync path/to/new-file.md` — process a specific source file
- `process sync report` — process a pending `.sync-report.md`

## Process

### Step 1: Detect Changes

**If `.sync-report.md` exists:** Read it — it lists all changed files with timestamps.

**If no report (manual invocation):**
```bash
!`bash ~/.claude/scripts/project-sync-orchestrator.sh "$(pwd)"`
```
Then read the generated `.sync-report.md` (written to project root or `~/.claude/state/<project-name>/sync-report.md`).

**If a specific file was passed as `$ARGUMENTS`:** Use that file as the sole source.

**If no changes detected:** Report "All documents are in sync." and stop.

### Step 2: Read Source Files

For each new/modified file detected:

1. **Skip binaries** (`.docx`, `.xlsx`, `.pptx`, `.pdf`) — note them but don't read. Tell user: "Binary file detected — paste key content or convert to text."
2. **Read text files** (`.md`, `.html`) in full
3. **Extract structured data** from each:

```
For each source file, extract:
- NEW STAKEHOLDERS: Name, Role, Email, Group
- NEW DECISIONS: What was decided, by whom, date, impact
- NEW REQUIREMENTS: Functional/non-functional, priority, acceptance criteria
- NEW ACTION ITEMS: Owner, deadline, status
- NEW ARCHITECTURE: Design changes, module updates, integration changes
- NEW RISKS: Description, impact, mitigation
- VERSION CHANGES: What changed from previous version
```

### Step 3: Read Config & Map Dependencies

Read `.sync-watch.json` to determine which target docs need which types of updates.

For each target doc in `tier1` and `tier2`:
- Check if any source file matches its `update_from` patterns
- If yes → read the target doc to understand current state
- Identify exactly WHERE in the target doc the new content should go

### Step 4: Propose Updates

Present a structured proposal — DO NOT edit anything yet:

```markdown
## Sync Proposal

### Source: Meeting-Notes-2026-03-17.md
**New content extracted:**
- 2 new stakeholders (Jane Doe, John Smith)
- 1 decision (moved go-live to Q4)
- 3 action items

### Updates Needed:

**1. PRD.html** (Tier 1)
- Section 05 Stakeholders: Add Jane Doe (Tax Director), John Smith (IT Lead)
- Section 12 Timeline: Update go-live from Q3 → Q4
- Change log: Add v1.1 entry
- [Show exact diff preview for each change]

**2. Presentation.html** (Tier 1)
- Slide 7 (Team): Add 2 stakeholder cards
- Slide 12 (Timeline): Update milestone date
- [Show exact diff preview]

**3. CLAUDE.local.md** (Tier 1)
- Recent Changes: Add dated entry
- [Show exact content to append]

**4. Stakeholder-Directory.xlsx** (Tier 2)
- SKIP — binary file, manual update needed
```

### Step 5: Get Approval

Ask user:
- "Apply all updates?" → proceed with all
- "Apply selectively?" → let user pick which targets
- "Skip for now?" → clean up report, do nothing
- User may also request modifications to the proposal

### Step 6: Apply Updates

For each approved target:
1. **Read the target file** (always re-read before editing — it may have changed)
2. **Apply edits** using the Edit tool (not Write — preserve unchanged content)
3. **Verify** the edit was applied correctly
4. **Log** what was changed

### Step 7: Clean Up & Update Memory

After all edits applied:
1. **Delete `.sync-report.md`** (consumed)
2. **Update `_temp/.last-sync-check`** timestamp
3. **Update `CLAUDE.local.md`** Recent Changes section with a dated entry summarizing what was synced
4. **Report** summary to user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DOC SYNC ► COMPLETE ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Source files processed: 3
Documents updated: 4
  ✓ PRD.html — 3 edits (stakeholders, timeline, changelog)
  ✓ Presentation.html — 2 edits (team slide, timeline)
  ✓ CLAUDE.local.md — 1 edit (recent changes)
  ⚠ Stakeholder-Directory.xlsx — skipped (binary)

Manual follow-up needed:
  - Update Stakeholder-Directory.xlsx with 2 new contacts
```

## Critical Rules

1. **NEVER edit without approval.** Always show the proposal first. The user must explicitly approve.
2. **NEVER fabricate content.** Only extract what's actually written in source files. If a meeting note doesn't mention a stakeholder's email, don't guess it.
3. **NEVER overwrite — always append/insert.** Use Edit tool with precise `old_string` matching. Never rewrite entire files.
4. **ALWAYS read target docs before editing.** They may have been modified since the report was generated.
5. **ALWAYS preserve existing formatting.** Match the target doc's style (HTML structure, CSS classes, indentation patterns).
6. **Binary files are report-only.** Flag them for manual update, don't attempt to modify.
7. **Version bumps:** If the target doc has a version badge/number, increment it and add a changelog entry.

## Adding This to a New Project

1. Create `.sync-watch.json` in the project root (use template above)
2. Run `/project-sync init` to set up the launchd cron job
3. Done — the background orchestrator runs every 2 hours and generates `.sync-report.md` when changes are detected

## Dependency Graph Pattern

For complex projects, document the update cascade in `.sync-watch.json`:

```
Meeting Notes ──→ PRD ──→ PRD Presentation
       │                         │
       ├──→ Main Presentation ←──┘
       │
       └──→ CLAUDE.local.md ←── (all changes)
```

This ensures that when a meeting note creates a PRD change, and that PRD change should also update the presentation, the full cascade is handled in one sync pass.
