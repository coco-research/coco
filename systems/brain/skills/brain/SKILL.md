---
name: brain
description: "SQLite-based project knowledge tracker. Manages entities, relationships, tasks, threads, decisions, and events per project folder. Use /brain to query or update project_brain.db. Triggers on: 'brain', 'project knowledge', 'what do we know about', 'open tasks', 'recent decisions'."
---

# /brain --- Project Knowledge Tracker

A structured SQLite database (`project_brain.db`) that lives in each project folder, replacing flat markdown memory files with queryable, relational knowledge.

## Quick Reference

```bash
BRAIN="python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py"

# Initialize in current project folder
$BRAIN init

# Create a project
$BRAIN add-project "My Project" --slug my-project --desc "Example project description"

# Add entities (upsert --- safe to run repeatedly)
$BRAIN add-entity my-project person "Alice Example" --external-id 2882
$BRAIN add-entity my-project team "Engineering" --external-id 33
$BRAIN add-entity my-project module "PlatformHub"

# Add relationships
$BRAIN add-rel 1 2 member_of
$BRAIN add-rel 1 3 administers

# Tasks
$BRAIN add-task my-project "Configure external reviewer access" --priority 1
$BRAIN update-task 1 --status in_progress
$BRAIN tasks my-project --status open

# Threads (group related work)
$BRAIN add-thread my-project "External User Access" --category request
$BRAIN link-thread 1 task 1
$BRAIN link-thread 1 decision 1

# Decisions
$BRAIN add-decision my-project 2026-04-08 "Use Stakeholder role for external users" \
  --context "No license consumed, view-only" --decided-by You

# Events
$BRAIN add-event my-project 2026-04-08 call "Charlie Customer Call" \
  --summary "Priorities deck shared" --participants "Alice,Bob,Charlie,You"

# CoCo context (session start)
$BRAIN context my-project

# Search across everything
$BRAIN context my-project --search "Morgan"

# Entity graph (show all connections)
$BRAIN graph 1

# Thread detail (show all linked items)
$BRAIN thread-detail 1
```

## /brain:update --- End-of-Session Flush

**This is the most important command.** When the user runs `/brain:update`, Claude MUST do a thorough review of the entire conversation and write everything learned to the brain DB. This is a forcing function --- do not skip anything.

### Procedure

1. **Scan the full conversation** from top to bottom. For each project in the brain DB, extract:

   **New entities** --- any person, team, role, system, or module mentioned for the first time
   **New relationships** --- any connection between entities discovered (X owns Y, A reports to B, etc.)
   **New decisions** --- anything that was decided, agreed, confirmed, or resolved
   **New events** --- meetings, calls, emails read, milestones hit
   **New tasks** --- action items, to-dos, next steps, follow-ups
   **Task updates** --- tasks that changed status (done, blocked, in_progress)
   **Entity updates** --- new info about existing entities (role change, new metadata)

2. **Present a summary table** to the user showing what will be written:
   ```
   BRAIN UPDATE SUMMARY
   ====================
   New entities:      3 (Alice Chen, Bob Kumar, ...)
   New decisions:     2 (Use Stakeholder role, Sandbox all-or-nothing)
   New events:        1 (Charlie CSM call Apr 8)
   New tasks:         4 (Get reviewer details, Get sandbox access, ...)
   Task updates:      2 (task #3 -> blocked, task #5 -> blocked)
   New relationships: 1 (Alice administers Platform)
   Entity updates:    1 (Charlie Sohn: added CSM role metadata)
   ```

3. **Wait for user confirmation** ("looks good" / "y" / adjustments)

4. **Execute all writes** via Python operations and report counts.

### When to prompt the user

If the conversation has been long (>10 exchanges) and the user hasn't run `/brain:update`, gently suggest it:
> "We've covered a lot this session. Want me to run `/brain:update` to capture everything before we wrap?"

Do NOT auto-run it. Always wait for the user to invoke or confirm.

## Behavior Rules

### Auto-write (no confirmation needed)
- Entity sync from your custom MCP (roles, teams, users)
- Changelog entries when entities are updated
- Task status updates
- Event logging from emails and meetings

### Confirm-write (propose to user first)
- New decisions
- New relationships between entities
- Deleting or archiving entities

### Semi-auto (extract and confirm)
- After reading emails: propose entities, events, tasks to add
- After meeting notes: propose decisions, action items, new stakeholders

## DB Location

Each project folder gets its own `project_brain.db`:
```
MyProject/project_brain.db
E&C/project_brain.db
Optimize/project_brain.db
```

CoCo aggregates across all known DBs at session start.

## Memory Architecture

The brain DB is the **source of truth** for all project knowledge. It syncs to two other stores:

| Store | Backend | What syncs | Why |
|-------|---------|-----------|-----|
| **MemPalace** | ChromaDB (~/.mempalace/palace) | Entities, decisions, events → drawers | Semantic search across projects |
| **brain.json** | JSON (~/.coco/brain.json) | Person entities → people section | CoCo people graph, attention rules |

Sync happens automatically at end of `/brain-update`, `/brain-init`, and `/brain-rescan` via `brain.memory_bridge.full_sync()`.

**Write path:** Always write to brain DB first → sync propagates to other stores.
**Read path:** Use Memory Bus (`memory_search`) for cross-store federated queries, or brain CLI for structured queries.

## Schema (v1)

11 tables: `projects`, `entities`, `relationships`, `tasks`, `threads`, `thread_items`, `decisions`, `events`, `changelog`, `tags`, `taggables`

Entity types: person, team, role, system, module, org_unit, document
Relationship types: member_of, owns, administers, reports_to, depends_on, blocks, scoped_to, created_by
Task statuses: open, in_progress, blocked, waiting, done, cancelled
Thread categories: feature, incident, request, decision, research
Event types: meeting, email, call, milestone, deploy
