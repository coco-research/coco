---
name: pmstudio-changelog
description: Create or update a structured change log for a product or platform. Use when someone asks to "create a change log", "log this change", "what changed", "update the change log", "release notes", or "changelog". Reads project memory (CLAUDE.local.md Recent Changes) and meeting notes to build chronological change records. Supports init (backfill from memory), update (append new entries), and release (summarize for a version).
---

# Change Log — Running Product Change Record

## Purpose

Maintains a chronological, append-only record of all meaningful changes to a product. Unlike CLAUDE.local.md (which is AI context), the change log is a **stakeholder-facing** document suitable for sharing with leadership, auditors, and team members.

## Process

### Step 1: Determine Mode

- **`/change-log init`** — Create new change log, backfill from CLAUDE.local.md
- **`/change-log update`** — Find changes since last entry, propose new entries
- **`/change-log release {version}`** — Create release summary from accumulated entries
- **`/change-log`** (no args) — Same as `update`

### Step 2: Read Context

**Always read:**
- `CLAUDE.local.md` — Recent Changes section (primary source of truth for what changed)
- Existing change log file (if `update` or `release` mode)

**For `init` mode, also read:**
- `Meeting-Notes/` directory listing — to identify decision-bearing meetings
- `PRD/` — version history sections
- `.sync-watch.json` — project name

**For `update` mode:**
- Find the date of the last change log entry
- Read any `Meeting-Notes/` files dated after that
- Read `CLAUDE.local.md` Recent Changes entries dated after that

### Step 3: Extract Changes

For each source, extract structured change data:

```
- Date: YYYY-MM-DD
- Summary: one-line description
- Type: Feature | Enhancement | Bug Fix | Configuration | Process | Security | Documentation
- Impact: High | Medium | Low
- Components: which modules/layers/documents were affected
- Author: who made or requested the change
- Approved By: who approved (if known from meeting notes)
- Details: bullet list of specific changes
- Rationale: why the change was made
- Downstream: what else was updated as a result
```

**Impact classification:**
- **High** — Changes product behavior, affects users, or modifies architecture
- **Medium** — Updates documentation, adds stakeholders, changes processes
- **Low** — Minor fixes, formatting, internal-only changes

### Step 4: Propose Entries (update/init)

Present proposed entries to user before writing:

```markdown
## Proposed Change Log Entries

### [2026-03-17] PRD v0.9 — User Journey Sections
**Type:** Enhancement | **Impact:** High
**Components:** ProductB PRD, ProductB PRD Presentation
- Added Current User Journey (6-step timeline)
- Added Future User Journey (3-layer cascading)
- Renumbered all sections (19 total)

Accept? [Y/n] or modify?
```

### Step 5: Write

**File location:** `Data/Change-Log-{ProjectName}.md`

**File structure:**

```markdown
# Change Log — {Product Name}

> Running record of all changes. Newest entries first.
> Generated and maintained via `/change-log` skill.

Last updated: {date}
Total entries: {count}

---

## [YYYY-MM-DD] v{X.Y} — {Summary}

**Type:** {type} | **Impact:** {impact}
**Components:** {affected components}
**Author:** {name} | **Approved By:** {name or "—"}

### Changes
- {specific change 1}
- {specific change 2}

### Rationale
- {why this change was made}

### Downstream Effects
- {what else was updated}

---

## [YYYY-MM-DD] ...
```

**For `release` mode:**

Collect all entries since the last release entry (or all entries if first release). Produce a summary:

```markdown
## Release: v{version} — {date}

### Summary
{2-3 sentence overview of what this release includes}

### Changes Included
| Date | Type | Summary | Impact |
|------|------|---------|--------|
| ... | ... | ... | ... |

### Highlights
- {Most important change}
- {Second most important}

### Known Issues
- {Any caveats}
```

## Critical Rules

1. **Append-only.** Never modify existing entries. Only add new ones at the top.
2. **Propose before writing.** Always show the user what entries will be added.
3. **Don't duplicate.** Check existing entries before proposing. If a change is already logged, skip it.
4. **Real content only.** Don't log trivial changes (typo fixes, formatting) unless the user specifically asks.
5. **Dates from sources.** Use the date from CLAUDE.local.md or meeting notes, not today's date, for the change date. Today's date is for entries about changes made today.
