---
name: brain:update
description: "End-of-session brain flush. Scans the full conversation, extracts all new entities, decisions, tasks, events, relationships, and updates, presents a summary, and writes to project_brain.db after confirmation. Use at end of every session or when you want to capture everything discussed."
---

# /brain:update --- End-of-Session Brain Flush

**This is a forcing function.** When invoked, Claude MUST thoroughly review the entire conversation and write everything learned to the brain DB. No shortcuts, no skipping.

## Procedure

### Step 1: Detect brain DB

Look for `project_brain.db` in the current working directory or parent dirs. If not found, error: "No brain DB found. Run `/brain init` first."

### Step 2: Read current DB state (cross-session awareness)

**CRITICAL --- the user runs multiple terminal sessions in parallel.** Another session may have already written to the brain since this conversation started. Before extracting, read the current DB state:

```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py context {slug}
```

For each project, note:
- **Existing entities** (names and types) --- so you don't propose adding what's already there
- **Existing decisions** (decision text) --- so you don't duplicate
- **Existing events** (title + date) --- so you don't duplicate
- **Current task statuses** --- so you don't regress a task that another session already advanced (e.g., don't set to "open" if another session set it to "done")

**Conflict rules:**
- **Entity already exists with newer metadata** --- skip your update. The other session's data is fresher.
- **Decision already recorded** --- skip. Match on first 40 chars of decision text.
- **Event already recorded** --- skip. Match on title + date.
- **Task status conflict** --- the MORE ADVANCED status wins. Status order: open < in_progress < blocked < waiting < done < cancelled. Never regress.
- **Task notes** --- if brain has notes that your session doesn't know about, MERGE (append), don't overwrite.
- **New data from this session not in DB** --- these are the writes to propose.

Show any conflicts detected:
```
CROSS-SESSION CONFLICTS
=======================
  Task "Get sandbox access" --- brain says "done" (updated by another session), 
  this session would set "open". KEEPING "done".
  
  Decision "Use Stakeholder role..." --- already in brain. SKIPPING.
```

### Step 3: Scan the full conversation

Go through every message from top to bottom. For EACH project in the brain DB, extract:

| Category | What to look for |
|----------|-----------------|
| **New entities** | Any person, team, role, system, module, or org mentioned for the first time |
| **New relationships** | Connections discovered: X owns Y, A reports to B, team scoped to module |
| **New decisions** | Anything decided, agreed, confirmed, resolved, or ruled out |
| **New events** | Meetings, calls, emails read, milestones, deployments |
| **New tasks** | Action items, to-dos, next steps, follow-ups, blockers identified |
| **Task updates** | Existing tasks that changed status (started, completed, blocked, cancelled) |
| **Entity updates** | New info about existing entities (role change, new metadata, correction) |
| **Thread updates** | New items to link to existing threads, or new threads to create |

### Step 3: Execute writes immediately

**The user invoked `/brain-update` --- that IS the confirmation. Do NOT ask "Write all to brain?" or wait for approval. Just do it.**

Use Python to write all items via the brain operations module:

```python
import sys
sys.path.insert(0, '$HOME/.claude/skills/brain/scripts')
from brain.schema import get_db
from brain.operations import *
```

Write in this order:
1. Entities (upsert --- safe to run repeatedly)
2. Relationships
3. Tasks (new + updates)
4. Threads + thread_items
5. Decisions
6. Events

### Step 6: Report

```
BRAIN UPDATED
=============
Entities:      +3 (total: 47)
Relationships: +1 (total: 37)
Tasks:         +2, ~3 updated (total: 8)
Decisions:     +1 (total: 4)
Events:        +1 (total: 3)
Threads:       1 updated (total: 1)
Synced to:     MemPalace (N drawers), brain.json (N people)
```

### Step 6b: Sync to MemPalace and brain.json

After all brain DB writes complete, run the memory bridge to sync new knowledge to the other memory stores:

```python
from brain.memory_bridge import full_sync
full_sync(db_path, project_slug)
```

This:
1. Copies new entities, decisions, and events to MemPalace as searchable drawers (wing = project slug, room = entity type)
2. Rebuilds brain.json people section from all brain DB person entities across all projects
3. Is best-effort — if MemPalace or brain.json sync fails, brain DB data is still safe

The sync is automatic. No user confirmation needed for this step.

### Step 7: Update knowledge articles

After brain DB writes complete and `full_sync` runs (Step 6b), incrementally update
knowledge articles for entities whose evidence has changed in this session.

**Collect changed entity IDs** from the writes performed in Step 3 (entities upserted,
decisions/events written). Pass these to the knowledge engine for targeted refresh:

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.coco/knowledge"))
from engine import KnowledgeEngine

engine = KnowledgeEngine()
# changed_entity_ids = list of brain DB entity IDs written in this session
engine.incremental_update(project_slug, changed_entity_ids)
```

Or equivalently via CLI (re-harvests all entities but only regenerates stale ones):

```bash
python3 ~/.coco/knowledge/cron.py --run --project {slug} --phases 2,3,5
```

Only articles whose `source_hash` changed are regenerated. Expected: 1–5 article
regenerations per typical session. Estimated cost: ~$0.01.

Show result **inline in the existing brain-update summary block**:
```
BRAIN UPDATED
=============
Entities:      +3 (total: 47)
Relationships: +1 (total: 37)
Tasks:         +2, ~3 updated (total: 8)
Decisions:     +1 (total: 4)
Events:        +1 (total: 3)
Threads:       1 updated (total: 1)
Synced to:     MemPalace (N drawers), brain.json (N people)
Knowledge:     N articles refreshed  (N new entities, N updated)
```

**Skip silently if:**
- `~/.coco/knowledge/` does not exist (knowledge engine not installed)
- `cron.py` is unavailable or returns a non-zero exit code
- The knowledge engine step takes more than 60 seconds (non-blocking)

---

## Important Rules

- **Be thorough.** Scan EVERY message. If someone was mentioned by name, they should be an entity. If something was decided, it should be a decision. If there's a next step, it should be a task.
- **Deduplicate.** Check what already exists in the DB before proposing new writes. Use `upsert_entity` which matches on (project_id, type, name) or (project_id, type, external_id).
- **Date everything.** Decisions and events need dates. Use today's date if the exact date isn't clear.
- **Attribute decisions.** Record who decided, not just what was decided.
- **Link to threads.** If a task, decision, or event belongs to an existing thread, link it.
