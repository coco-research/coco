---
name: brain:wiki
description: "Browse, search, and generate Wikipedia-style knowledge articles from the brain. Auto-generated from brain DB entities, emails, docs, and decisions."
---

# /brain-wiki — CoCo Knowledge Articles

Browse, search, and generate Wikipedia-quality articles about people, systems, teams,
and org units across all CoCo brain DB projects.

Articles are auto-generated from the brain DB by the daily knowledge engine cron
(`~/.coco/knowledge/cron.py`). Each article synthesizes all evidence available about
an entity — decisions, events, relationships, tasks — into a structured, versioned
knowledge artifact.

---

## Commands

### `/brain-wiki [entity]` — Show article (or list all)

**With entity name:** Look up and display a knowledge article.

```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py wiki --name "{entity}"
```

Display format:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{Title}                                    [{type}]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Infobox:  Projects: {list} | Role: {role} | Team: {team}

{Summary paragraph}

## Role
{content}

## Relationships
{content}

## Timeline
{content}

## Decisions
{content}

## Open Questions
{content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated: {date}  ·  Confidence: {0-100}%  ·  Sources: N chunks
GID: {uuid}  ·  v{version}
```

If article not found → run wiki-search with the entity name as query and show top 3 candidates:
```
No article found for "{entity}". Did you mean:
  1. {title}  ({confidence}%)  — /brain-wiki {gid}
  2. {title}  ({confidence}%)
  3. {title}  ({confidence}%)
```

Warnings to show inline:
- If confidence < 30%: `⚠ Low confidence — this article needs more source data. Run /brain-update after adding more context.`
- If pending merge proposals exist for this entity: `ℹ Possible duplicate: matches "{other_name}" ({similarity}%) — run /brain-wiki review-merges to resolve`

**Without entity name:** List all available articles.

```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py wiki-search "*" --limit 50
```

Display as table:
```
KNOWLEDGE BASE  ·  N articles
═══════════════════════════════════════════════════════════
Name                    Type       Confidence   Updated
─────────────────────────────────────────────────────────
Alice Example               person     87%          2h ago
VendorPortal            system     91%          yesterday
DataPipeline            system     76%          2d ago
Platform Team           team       82%          2d ago
...
```

---

### `/brain-wiki search <query>` — Unified FTS5 + semantic search

```bash
python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py wiki-search "{query}"
```

Runs both FTS5 keyword search and MemPalace semantic search, merges via RRF.

Display format:
```
SEARCH: "{query}"  ·  N results  ·  FTS5 + semantic
══════════════════════════════════════════════════════════════
  #  Name                Type      Confidence  Projects     Updated
 ─────────────────────────────────────────────────────────────────
  1  {title}             {type}    {conf}%     {projects}   {time}
  2  ...

Run /brain-wiki {name} to read the full article.
```

If 0 results:
```
No articles found for "{query}".
Entity may not be in any brain DB yet, or articles haven't been generated.
Run: /brain-wiki generate  to generate articles for all brain entities.
```

---

### `/brain-wiki generate [project]` — Generate / refresh articles

Generates or refreshes knowledge articles from brain DB evidence.

**Procedure:**

1. If a project is specified, confirm scope:
   ```
   Generate articles for project "{project}"?
   This will use Claude API (estimated $0.XX for N entities).
   [Y/n]
   ```
   If no project specified, confirm all:
   ```
   Generate articles for ALL registered projects?
   Registered: {slug1}, {slug2}, ...  (N projects, ~N entities)
   Estimated cost: $0.XX  ·  Estimated time: N minutes
   [Y/n]
   ```

2. On confirmation, run:
   ```bash
   # Single project
   python3 ~/.coco/knowledge/cron.py --run --project {slug} --phases 2,3,5

   # All projects
   python3 ~/.coco/knowledge/cron.py --run --phases 2,3,5
   ```

3. Show phase-by-phase progress as output streams:
   ```
   Phase 2: Harvesting evidence...
     ✓ {project}: N entities, N evidence chunks

   Phase 3: Generating articles...
     ✓ Generated: Alice Example (confidence: 87%)
     ✓ Generated: VendorPortal (confidence: 91%)
     ~ Skipped:   3 entities (unchanged)

   Phase 5: Indexing...
     ✓ N articles indexed (FTS5)

   ─────────────────────────────────────────
   KNOWLEDGE ENGINE
   ================
   Articles generated:  N new, N updated
   FTS5 indexed:        N
   Estimated cost:      $0.XXX

   Articles written to: ~/.coco/knowledge/articles/
   Search with: /brain-wiki search "{project}"
   ```

4. Add `--force` flag to regenerate all articles regardless of staleness.

---

### `/brain-wiki people` — Show cross-project people graph

Show all person-type articles and cross-project relationship statistics.

**Procedure:**

1. Query knowledge.db directly (do NOT invoke cron --dry-run, per review finding m4):
   ```python
   import sys, sqlite3, json
   sys.path.insert(0, str(Path("~/.coco/knowledge").expanduser()))
   from schema import KNOWLEDGE_DB_PATH
   conn = sqlite3.connect(KNOWLEDGE_DB_PATH)

   # People articles
   people = conn.execute("""
       SELECT ge.canonical_name, ge.aliases_json, ge.merged_from_json,
              a.confidence, a.generated_at, a.version
       FROM global_entities ge
       LEFT JOIN articles a ON a.gid = ge.gid
       WHERE ge.type = 'person'
       ORDER BY a.confidence DESC NULLS LAST
   """).fetchall()

   # Pending merges
   merges = conn.execute("""
       SELECT COUNT(*) FROM cross_project_connections
       WHERE connection_type = 'proposed_merge'
   """).fetchone()[0]

   # Works-with edges
   edges = conn.execute("""
       SELECT COUNT(*) FROM cross_project_connections
       WHERE connection_type = 'works_with'
   """).fetchone()[0]
   ```

2. Display:
   ```
   PEOPLE GRAPH  ·  N people across N projects
   ════════════════════════════════════════════════════════
   Name                    Projects     Confidence   Updated
   ─────────────────────────────────────────────────────────
   Alice Example               my-project       87%          2h ago
   ...

   Works-with relationships:  N edges inferred
   Pending merge proposals:   N  — run /brain-wiki review-merges to resolve
   ```

3. If no people articles yet:
   ```
   No people articles found. Run /brain-wiki generate to build the knowledge base.
   ```

---

### `/brain-wiki review-merges` — Review and approve entity merge proposals

Interactively review merge proposals (entities that may be duplicates).

**Procedure:**

1. List pending merges:
   ```bash
   python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py wiki --list-merges
   ```

2. For each pending merge, show both entities' summaries side by side:
   ```
   MERGE PROPOSAL  (similarity: 92%)
   ══════════════════════════════════════════════════════════
   KEEP candidate A:                KEEP candidate B:
   ─────────────────────────────    ─────────────────────────
   Name: Alice Example                  Name: Alice Examplé
   GID:  {uuid-a}                   GID:  {uuid-b}
   Projects: project-a, project-b    Projects: vendor-integration

   Summary A: {2-3 sentences}       Summary B: {2-3 sentences}
   ══════════════════════════════════════════════════════════
   Action: [A=keep A | B=keep B | s=skip | q=quit]
   ```

3. On approval:
   ```bash
   python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py wiki --approve-merge {gid_keep} {gid_remove}
   ```
   This:
   - Reassigns all articles from gid_remove → gid_keep
   - Adds the removed entity's name to gid_keep's aliases
   - Deletes gid_remove from global_entities
   - FIX M6: uses delete-then-reinsert for articles_fts (not UPDATE, which fails on virtual tables):
     `DELETE FROM articles_fts WHERE gid=gid_remove` then re-INSERT with gid_keep

4. On skip: record the skip decision (do not re-propose the same pair for 30 days).

5. Show completion summary:
   ```
   MERGE REVIEW COMPLETE
   =====================
   Approved:  N merges
   Skipped:   N pairs
   Remaining: N pending
   ```

---

### `/brain-wiki install-cron` — Set up daily improvement cron

Install the daily knowledge engine job via macOS launchd.

**Procedure:**

1. Check that claude binary is resolvable first (the installer validates this):
   ```bash
   python3 ~/.coco/knowledge/cron.py --install
   ```

2. Show confirmation:
   ```
   KNOWLEDGE CRON INSTALLED
   ========================
   Schedule:       Daily at 02:00
   Claude binary:  {resolved path}
   Python binary:  {resolved path}
   Plist:          ~/Library/LaunchAgents/com.coco.knowledge-cron.plist
   Log:            ~/.coco/knowledge/cron.log

   To uninstall:  /brain-wiki uninstall-cron
   To test now:   python3 ~/.coco/knowledge/cron.py --run --dry-run
   ```

3. If claude binary not found, show the error from `_find_claude_binary()` with install instructions.

To uninstall:
```bash
python3 ~/.coco/knowledge/cron.py --uninstall
```

---

### `/brain-wiki stats` — Show knowledge engine statistics

Display current state of the knowledge engine without running any generation.

**Procedure:**

Query knowledge.db directly:
```python
import sqlite3, json
from pathlib import Path
conn = sqlite3.connect(Path("~/.coco/knowledge/knowledge.db").expanduser())

stats = {
    "entities":        conn.execute("SELECT COUNT(*) FROM global_entities").fetchone()[0],
    "articles":        conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0],
    "fts_rows":        conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0],
    "pending_merges":  conn.execute(
        "SELECT COUNT(*) FROM cross_project_connections WHERE connection_type='proposed_merge'"
    ).fetchone()[0],
    "works_with":      conn.execute(
        "SELECT COUNT(*) FROM cross_project_connections WHERE connection_type='works_with'"
    ).fetchone()[0],
    "last_gen":        conn.execute(
        "SELECT MAX(run_at) FROM generation_log WHERE phase='3_generate' AND status='ok'"
    ).fetchone()[0],
    "last_sync":       conn.execute(
        "SELECT MAX(run_at) FROM generation_log WHERE phase='6_sync' AND status='ok'"
    ).fetchone()[0],
    "by_type":         conn.execute(
        "SELECT type, COUNT(*) FROM global_entities GROUP BY type"
    ).fetchall(),
}
```

Display format:
```
KNOWLEDGE ENGINE STATS
══════════════════════════════════════════════════
Entities:          N  (person: N, system: N, team: N ...)
Articles:          N  (FTS5 indexed: N)
Relationships:     N works_with edges
Pending merges:    N proposals awaiting review

Last generation:   {time ago}
Last MemPalace sync: {time ago}

Articles directory: ~/.coco/knowledge/articles/  (N files)
DB size:            {KB/MB}
══════════════════════════════════════════════════
Commands: /brain-wiki generate · /brain-wiki search · /brain-wiki review-merges
```

If knowledge.db does not exist:
```
Knowledge engine not initialized.
Run /brain-wiki generate to bootstrap, or /brain-wiki install-cron for daily automation.
```

---

## Implementation Notes

- **FTS5 scoring:** BM25 rank in SQLite FTS5 is negative (more negative = better match).
  Score normalization: `score = 1.0 / (1.0 + abs(rank))` — higher score = more relevant.
  (FIX M5 from review findings.)

- **body_json → FTS5 text:** FTS5 indexes plain text, not raw JSON. The engine extracts
  `section["content"]` from each section in `body_json` before inserting into `articles_fts`.
  (FIX C3 from review findings.)

- **articles_fts updates:** Virtual tables cannot be bulk-UPDATEd. Always use
  DELETE WHERE gid=? then re-INSERT for any gid change (e.g., merge approvals).
  (FIX M6 from review findings.)

- **Project registration:** Before the cron can harvest a project, it must be registered:
  ```bash
  python3 ~/.claude/skills/brain/scripts/brain/brain_cli.py wiki-register \
    --slug {slug} --db {path/to/project_brain.db}
  ```
  brain-init Step 8 calls this automatically. (FIX M1 from review findings.)

- **Kill switch:** If `~/.coco/disabled` exists, all brain-wiki commands should exit silently
  (consistent with CoCo kill switch convention).
