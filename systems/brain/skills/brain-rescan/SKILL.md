---
name: brain:rescan
description: "Incremental rescan of project folder. Detects new/changed files since last scan, extracts knowledge from CLAUDE.local.md, memory files, and doc inventory, and updates the brain DB. Requires an existing project_brain.db — run /brain-init first if none exists."
---

# /brain:rescan --- Incremental Knowledge Rescan

Detects what changed since the last scan and updates the brain DB with new knowledge.

## Prerequisites

- `project_brain.db` must exist in the project folder (or parent). If not found, tell the user: "No brain DB found. Run `/brain-init` first."
- At least one project must exist in the DB.

## Procedure

### Step 1: Run the scanner

```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py scan
```

Check the output:
- If `is_first_scan: true` → this folder was never scanned. Tell the user and proceed with full scan.
- If `new_files: 0` and `changed_files: 0` → "Everything up to date. No changes since last scan ({last_scan})." → done.
- Otherwise, show the delta:

```
RESCAN DELTA
============
Last scan:      {last_scan}
New files:      N
Changed files:  N
Removed files:  N
Unchanged:      N

New/changed files:
  + docs/NewDoc.html          (new)
  ~ CLAUDE.local.md           (changed)
  + emails/Latest_Thread.txt  (new)

Knowledge sources:
  CLAUDE.local.md:  found / not found (changed: yes/no)
  Memory files:     N files (N new/changed)
  Documents:        N new, N changed
  Emails:           N new, N changed
```

### Step 2: Process only new/changed files

Follow the same extraction logic as `/brain-init` Step 4, but **only for files in the delta**:

#### If CLAUDE.local.md is new or changed:
- Re-read and extract entities, decisions, events
- Use `upsert_entity` so existing entities get updated rather than duplicated
- For decisions: check existing decisions in DB, only add genuinely new ones (compare decision text)

#### If memory files are new or changed:
- Read only the new/changed memory files
- Extract project decisions, system references

#### For new/changed documents and emails:
- Register as `document` entities via `upsert_entity`
- Metadata includes path, type, size

#### For removed files:
- Do NOT auto-delete entities. Just report: "N files removed since last scan. Their brain entities are preserved — delete manually if needed."

### Step 3: Present extraction summary

```
RESCAN RESULTS
==============
Project: {name} ({slug})

New/updated entities:    N (list)
New decisions:           N (list)
New events:              N (list)
New document entities:   N (list)
Skipped (unchanged):     N files

Total proposed writes: NN
```

Ask: **"Write to brain? [Y/n/adjust]"**

### Step 4: Execute writes and update manifest

Same write order as `/brain-init` Step 6:
1. Entities (upsert)
2. Relationships
3. Decisions (dedup check)
4. Events (dedup check)
5. Document entities (upsert)

After all writes, sync to MemPalace and brain.json:
```python
from brain.memory_bridge import full_sync
full_sync("project_brain.db", project_slug)
```

Then update the manifest:
```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py scan-update
```

### Step 5: Report

```
BRAIN UPDATED (rescan)
======================
Entities:      +N, ~N updated (total: N)
Decisions:     +N (total: N)
Events:        +N (total: N)
Documents:     +N (total: N)

Manifest updated: N files tracked
Next scan will only process changes after {now}.
```

## When to use /brain-rescan vs /brain-update

| Scenario | Use |
|----------|-----|
| End of conversation session | `/brain-update` (extracts from conversation) |
| New files added to project folder | `/brain-rescan` (extracts from files) |
| Updated CLAUDE.local.md | `/brain-rescan` |
| First time in a project with existing brain | `/brain-init` (handles both init + scan) |
| Periodic refresh | `/brain-rescan` |
