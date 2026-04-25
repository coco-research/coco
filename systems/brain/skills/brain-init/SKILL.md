---
name: brain:init
description: "Initialize a project_brain.db in the current project folder. Creates the database, project record, then scans existing files (CLAUDE.local.md, memory files, docs, emails) to bootstrap the brain with knowledge. Smart enough to handle re-runs — skips what already exists and only processes new/changed files."
---

# /brain:init --- Initialize Project Brain

Sets up a new `project_brain.db` in the current working directory and bootstraps it from existing project knowledge.

## Procedure

### Step 1: Check existing state

Run:
```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py info
```

- If **no DB exists** → proceed to Step 2 (full init)
- If **DB exists with project(s)** → skip to Step 3 (scan only). Tell user: "Brain already initialized. Running scan for new/changed files..."

### Step 2: Create the database and project record

Run:
```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py init
```

Ask the user:
- **Project name** (e.g., "My Project A", "My Project B")
- **Slug** (short URL-safe identifier, e.g., "my-project-a", "my-project-b")
- **Description** (one-liner)

Then run:
```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py add-project "{name}" --slug {slug} --desc "{description}"
```

If the project has sub-scopes (like ProjectA-Phase1 and ProjectA-Phase2 under one umbrella), ask if the user wants multiple project records.

### Step 3: Scan the project folder

Run the scanner to discover what's available:
```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py scan
```

This returns a JSON report with:
- **manifest_diff**: new/changed/unchanged file counts, whether this is the first scan
- **files_to_process**: paths of new or changed files
- **knowledge_sources**: which CLAUDE.local.md, memory files, docs, and emails were found

Show the user a summary:
```
FOLDER SCAN
===========
First scan:     yes/no
Files found:    NN total (NN new, NN changed, NN unchanged)

Knowledge sources detected:
  CLAUDE.local.md:  found / not found
  CLAUDE.md:        found / not found
  Memory files:     N files (list names)
  Documents:        N files in docs/
  Emails:           N files in emails/
  Reference docs:   N files
```

If nothing to process (all unchanged): "Everything up to date. No new knowledge to extract." → done.

### Step 4: Extract knowledge from sources (Claude-driven)

Process sources in **priority order**. For each source, read the file, extract structured knowledge, and collect proposed writes. Do NOT write to the brain yet — collect everything first.

#### Priority 1: CLAUDE.local.md
If found, read the full file. Extract:
- **Sections like "Key Decisions"** → `decisions` (with date, decision text, decided_by if mentioned)
- **People mentioned by name** → `person` entities (with metadata like role, email, team if mentioned)
- **Systems/tools mentioned** → `system` entities (e.g., Snowflake, Postgres, Datadog)
- **Teams mentioned** → `team` entities
- **Folder structure sections** → `document` entities for key docs
- **Recent Changes entries** → `events` (with date, type, title)

#### Priority 2: Memory files (~/.claude/projects/.../memory/*.md)
Each memory file has frontmatter (name, description, type) and content. Read each file:
- **project type memories** → `decisions` or context to enrich existing entities
- **feedback type memories** → skip (these are Claude behavior guidance, not project knowledge)
- **reference type memories** → `system` or `document` entities with metadata

#### Priority 3: Document inventory
For each file in docs/, emails/, and Reference Doc/:
- Create a `document` entity with metadata: `{"path": "relative/path", "type": "doc|email|reference", "size": N}`
- Use the filename (cleaned) as the entity name
- Do NOT read the full content of every file — just register them in the inventory

#### Priority 4: CLAUDE.md (project-level, if exists)
Same extraction as CLAUDE.local.md but lower priority (may overlap).

### Step 5: Present extraction summary

Show proposed writes:
```
BRAIN BOOTSTRAP SUMMARY
========================
Project: {name} ({slug})

From CLAUDE.local.md:
  Entities:    N (list: name [type])
  Decisions:   N (list: short text)
  Events:      N (list: title)

From memory files:
  Decisions:   N (list: short text)
  Entities:    N (list: name [type])

Document inventory:
  Documents:   N (list: filename [doc|email|reference])

Total proposed writes: NN
```

Ask: **"Write all to brain? [Y/n/adjust]"**

### Step 6: Execute writes

On confirmation, write in this order using Python:
```python
import sys
sys.path.insert(0, '$HOME/.claude/skills/brain/scripts')
from brain.schema import get_db
from brain.operations import *
```

1. **Entities** — use `upsert_entity` (idempotent, safe to re-run)
2. **Relationships** — use `create_relationship` (also idempotent)
3. **Decisions** — use `create_decision` (check for duplicates by matching decision text before inserting)
4. **Events** — use `create_event` (check for duplicates by matching title + date)
5. **Document entities** — use `upsert_entity` with type="document"

After all writes, sync to MemPalace and brain.json:
```python
from brain.memory_bridge import full_sync
full_sync("project_brain.db", project_slug)
```

After writes complete, update the manifest:
```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py scan-update
```

### Step 7: Report

```
BRAIN INITIALIZED
=================
DB:            {path}/project_brain.db
Project:       {name} ({slug})
Schema:        v1 (11 tables)

Bootstrapped from existing knowledge:
  Entities:      +N (total: N)
  Decisions:     +N (total: N)
  Events:        +N (total: N)
  Documents:     +N (total: N)
  Relationships: +N (total: N)

Manifest updated: N files tracked

Next: Run /brain-update at end of session, or /brain-rescan when files change.
```

### Step 8: Generate knowledge articles

After completing brain writes (Step 6) and confirming the manifest is updated (Step 6
scan-update), initialize the knowledge engine for this project.

**First, register the project with the knowledge engine:**

```python
import sys, os
sys.path.insert(0, os.path.expanduser("~/.coco/knowledge"))
from engine import KnowledgeEngine

engine = KnowledgeEngine()
engine.register_project("{slug}", os.path.abspath("project_brain.db"))
```

This is required before the cron can harvest the project. (FIX M1: register_project
must be called before running any cron phases.)

**Then, bootstrap article generation:**

```python
engine.full_refresh("{slug}")
```

Or equivalently via CLI:

```bash
python3 ~/.coco/knowledge/cron.py --run --project {slug} --phases 2,3,5
```

This runs:
- Phase 2 (harvest evidence from the brain DB you just populated + infer relationships)
- Phase 3 (generate articles for all entities — first run will generate all)
- Phase 5 (FTS5 index the new articles)

Show the user:
```
KNOWLEDGE ENGINE
================
Articles generated:  N
FTS5 indexed:        N
Estimated cost:      $0.XXX

Articles written to: ~/.coco/knowledge/articles/
Search with: /brain-wiki search "{project_name}"
```

**Skip this step silently if:**
- `~/.coco/knowledge/` does not exist (knowledge engine not installed)
- The `cron.py` call fails for any reason (non-blocking — brain init still succeeds)

---

## Important Rules

- **Dedup before writing.** Always check what exists in the DB before proposing new writes. Use `upsert_entity` which handles this automatically for entities.
- **Don't read every file.** For doc inventory, just register the file — don't parse 130KB HTML files to extract content. That's what `/brain-update` is for (conversation-driven).
- **Date everything.** Decisions and events need dates. Parse from the source if available, fall back to file modification date, then today.
- **Memory files are structured.** They have frontmatter — use the `type` field to decide what to extract.
- **Manifest tracks scan state.** Always run `scan-update` after writes so the next scan is incremental.
