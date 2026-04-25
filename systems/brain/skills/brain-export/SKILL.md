---
name: brain:export
description: "Auto-generate a slim CLAUDE.local.md from brain DB. Preserves manual behavior rules. Produces ~1,200 token auto-generated context section with key people, systems, decisions, and project status."
---

# /brain-export — CLAUDE.local.md Auto-Generator

Generates or refreshes the `<!-- AUTO-GENERATED: brain-export -->` section in the project's `CLAUDE.local.md` file from the brain SQLite DB. Protects all manually written content above and below the sentinels.

## Quick Reference

```bash
BRAIN="python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py"

# Basic export (writes CLAUDE.local.md next to project_brain.db)
$BRAIN export <project-slug>

# Export with explicit output path
$BRAIN export <project-slug> --output /path/to/CLAUDE.local.md

# Export with explicit DB path
$BRAIN --db /path/to/project_brain.db export <project-slug>
```

## Procedure

### Step 1 — Verify brain DB exists

```bash
BRAIN="python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py"
$BRAIN info
```

If the DB is missing, tell the user to run `/brain-init` first.

### Step 2 — Run the export

```bash
$BRAIN export <project-slug>
```

The exporter will:
1. Read any existing `CLAUDE.local.md` at the output path
2. Preserve everything above `<!-- AUTO-GENERATED: brain-export -->`
3. Preserve everything below `<!-- END AUTO-GENERATED -->`
4. If no sentinels found, append the auto section at the bottom (safe first run)
5. Regenerate the auto section from brain DB
6. Write atomically (tmp file + rename)

### Step 3 — Show the user what was generated

Parse the JSON output and display:

```
brain:export complete
─────────────────────────────────────────
Output:         /path/to/CLAUDE.local.md
Project slug:   <slug>
Auto section:   ~NNN tokens (within 1,200 token budget: YES/NO)
Total file:     ~NNN tokens
─────────────────────────────────────────
Sections generated:
  - Project Identity  (if ~/.mempalace/identity.txt exists)
  - Last Session      (most recent event + decision)
  - Key People        (up to 8 person entities)
  - Key Systems       (up to 8 system/module entities)
  - Recent Decisions  (last 4 decisions)
  - Project Status    (entity/decision/event counts + last sync date)
```

### Step 4 — First-run: offer to migrate feedback memories

If this is the first export AND the project memory directory contains files with `type: feedback` frontmatter, offer to migrate them into behavior rules:

```
Found N feedback memory files that could become behavior rules in CLAUDE.local.md:
  - feedback_html_docs_with_tailwind.md → "Documents as Tailwind HTML not Markdown"

Add these as a ## Behavior Rules section below the auto-generated block? [y/N]
```

To migrate programmatically:

```python
from brain.exporter import migrate_feedback_memories
from pathlib import Path

memory_dir = Path("~/.claude/projects/<project-slug-hash>/memory").expanduser()
rules = migrate_feedback_memories(memory_dir)
for rule in rules:
    print(rule)
```

Then append the rules as a `## Behavior Rules` section below `<!-- END AUTO-GENERATED -->` in `CLAUDE.local.md`.

## Auto-Section Format

```markdown
<!-- AUTO-GENERATED: brain-export -->
<!-- Generated: 2026-04-09T12:00:00Z | Brain DB: 42 entities | MemPalace: 7 drawers -->

## Project Identity
<contents of ~/.mempalace/identity.txt if it exists>

## Last Session
- Most recent event title (YYYY-MM-DD)
- Most recent decision text (YYYY-MM-DD)

## Key People
| Name | Role | Email |
|------|------|-------|
| Alice Smith | Product Manager | alice@example.com |

## Key Systems
- **SystemA** — Description from metadata
- **ModuleB**

## Recent Decisions
- [2026-04-08] Decision text (truncated to 120 chars)

## Project Status
- Entities: 42 | Decisions: 12 | Events: 8
- Last brain sync: 2026-04-09
- Query: `/coco brain` or `/brain context {slug}` for full context

<!-- END AUTO-GENERATED -->
```

## Sentinel Contract

| Sentinel | Position | Meaning |
|----------|----------|---------|
| `<!-- AUTO-GENERATED: brain-export -->` | Start of auto block | Everything below is managed by exporter |
| `<!-- END AUTO-GENERATED -->` | End of auto block | Everything below is protected manual content |

**Never manually edit between the sentinels** — changes will be overwritten on next export.
**Safe to edit** anything above START or below END at any time.

## Token Budget

The auto section is capped at **1,200 tokens (~4,800 characters)**. If the generated content exceeds this, the body is truncated. The header comment and sentinels are always preserved intact.

## When to Run

- After every `/brain-update` session flush (brain DB has new data)
- After `/brain-init` (first time setup)
- After `/brain-rescan` (bulk entity import)
- When starting work on a project for the first time in a new session (ensure context is fresh)

## Trigger Phrases

- "export brain to CLAUDE.local.md"
- "refresh project context file"
- "generate CLAUDE.local"
- "update auto-generated section"
- "brain export <slug>"
