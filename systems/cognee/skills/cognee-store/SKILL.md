---
name: cognee:store
description: "Push project knowledge into the Cognee knowledge graph. Stores entities, decisions, events, relationships, and session context. End-of-session flush that extracts everything from the conversation and writes to the graph. Triggers on: 'cognee store', 'push to cognee', 'save to graph', 'remember this', 'log this decision'."
---

# /cognee-store — Push Knowledge to the Graph

Stores structured knowledge into Cognee's knowledge graph. Functions as the write path for Coco's memory layer — maps entities, decisions, events, and relationships to graph nodes and edges with embeddings for later semantic retrieval.

## Quick Reference

```bash
COGNEE="${COGNEE_BASE_URL:-http://localhost:8000}"
DATASET="my-project"

# Store a text fact (auto-cognifies)
curl -s -X POST "$COGNEE/api/v1/remember" \
  -F "datasetName=$DATASET" \
  -F 'data={"entity": {"type": "decision", "text": "Use JWT for API auth", "date": "2026-06-30", "decided_by": "Rijul", "context": "Stateless, works with existing infra"}}' \
  -F "run_in_background=false" | jq .

# Store file-based knowledge
curl -s -X POST "$COGNEE/api/v1/remember" \
  -F "datasetName=$DATASET" \
  -F "data=@/path/to/decision-log.md" \
  -F "run_in_background=false" | jq .

# Cognify existing data (process + build graph)
curl -s -X POST "$COGNEE/api/v1/cognify" \
  -H "Content-Type: application/json" \
  -d '{"datasets": ["my-project"]}' | jq .
```

## Data Format

All knowledge is stored as text, structured for Cognee's graph extraction. Use these formats:

### Entities
```
ENTITY: {name} | TYPE: {person|team|system|module|org_unit|document}
DESCRIPTION: {one-line description}
METADATA: {key: value, ...}
```

### Decisions
```
DECISION: {text} | DATE: {YYYY-MM-DD}
DECIDED_BY: {name}
CONTEXT: {why this was decided, alternatives considered}
IMPACT: {what changes as a result}
```

### Events
```
EVENT: {title} | DATE: {YYYY-MM-DD} | TYPE: {meeting|call|email|milestone|deploy}
SUMMARY: {what happened}
PARTICIPANTS: {comma-separated names}
OUTCOMES: {decisions made, action items}
```

### Relationships
```
RELATIONSHIP: {entity_a} -> {entity_b} | TYPE: {member_of|owns|depends_on|reports_to|blocks|administers|scoped_to}
CONTEXT: {why this relationship exists}
```

### Tasks
```
TASK: {description} | STATUS: {open|in_progress|blocked|waiting|done|cancelled}
PRIORITY: {1 (highest) - 5 (lowest)}
ASSIGNED_TO: {name}
BLOCKED_BY: {task or entity reference}
```

## /cognee-store:update — End-of-Session Flush

**This is the most important command.** When invoked, the agent MUST thoroughly review the entire conversation and write everything learned to Cognee. This is a forcing function — do not skip anything.

### Procedure

### Step 1: Check Cognee availability

```bash
COGNEE="${COGNEE_BASE_URL:-http://localhost:8000}"
curl -s -o /dev/null -w "%{http_code}" "$COGNEE/health"
```

If not 200: "Cognee is not running. Start with `cognee server start`." → offer to use `/brain-update` instead.

### Step 2: Verify dataset exists

```bash
curl -s "$COGNEE/api/v1/datasets" | jq -r '.[].name'
```

If the project dataset doesn't exist: "No dataset found for this project. Run `/cognee init` first."

### Step 3: Scan the full conversation

Go through every message from top to bottom. Extract:

| Category | What to look for |
|----------|-----------------|
| **New entities** | Any person, team, role, system, module mentioned for the first time |
| **New relationships** | Connections discovered: X owns Y, A reports to B |
| **New decisions** | Anything decided, agreed, confirmed, resolved, or ruled out |
| **New events** | Meetings, calls, emails read, milestones, deployments |
| **New tasks** | Action items, to-dos, next steps, follow-ups |
| **Task updates** | Existing tasks that changed status |
| **Entity updates** | New info about existing entities |

### Step 4: Present summary

```
COGNEE STORE SUMMARY
====================
Dataset:        my-project

New entities:      3 (Alice Chen [person], PlatformHub [module], Auth Service [system])
New decisions:     2 (Use JWT for API auth, Rate-limit at gateway level)
New events:        1 (Architecture review call Jun 30)
New tasks:         4 (Set up JWT middleware, Configure rate limiter, ...)
Task updates:      2 (task #3 → blocked, task #5 → in_progress)
New relationships: 1 (Auth Service depends_on PlatformHub)
Entity updates:    1 (Alice Chen: added backend lead role)

Total items to store: 13
```

### Step 5: Wait for confirmation

Ask: **"Write all to Cognee? [Y/n/adjust]"**

### Step 6: Execute writes

On confirmation, format each item according to the data formats above and send as a single batch:

```bash
COGNEE="${COGNEE_BASE_URL:-http://localhost:8000}"

# Build the payload as a multiline text document
cat > /tmp/cognee-store-batch.txt << 'STORE_EOF'
ENTITY: Alice Chen | TYPE: person
DESCRIPTION: Backend lead on PlatformHub
METADATA: {role: "backend lead", team: "Engineering"}

ENTITY: PlatformHub | TYPE: module
DESCRIPTION: Central platform for managing external access

ENTITY: Auth Service | TYPE: system
DESCRIPTION: Authentication and authorization service

DECISION: Use JWT for API auth | DATE: 2026-06-30
DECIDED_BY: Rijul
CONTEXT: Stateless, works with existing infrastructure. Considered session tokens but JWT more scalable.
IMPACT: All API endpoints will validate JWT tokens

DECISION: Rate-limit at gateway level | DATE: 2026-06-30
DECIDED_BY: Rijul
CONTEXT: Prefer gateway-level rate limiting over per-service to avoid duplication
IMPACT: API gateway configuration needs updating

EVENT: Architecture review call | DATE: 2026-06-30 | TYPE: call
SUMMARY: Reviewed authentication and rate-limiting architecture
PARTICIPANTS: Rijul, Alice Chen
OUTCOMES: JWT chosen for auth, rate-limiting at gateway

RELATIONSHIP: Auth Service -> PlatformHub | TYPE: depends_on
CONTEXT: Auth service validates tokens before requests reach PlatformHub

TASK: Set up JWT middleware | STATUS: open
PRIORITY: 1
ASSIGNED_TO: Alice Chen

TASK: Configure rate limiter at gateway | STATUS: open
PRIORITY: 2
ASSIGNED_TO: Alice Chen

TASK: Update API docs with auth headers | STATUS: open
PRIORITY: 3

TASK: Add monitoring for rate-limit hits | STATUS: open
PRIORITY: 4
STORE_EOF

# Send batch
curl -s -X POST "$COGNEE/api/v1/remember" \
  -F "datasetName=$DATASET" \
  -F "data=@/tmp/cognee-store-batch.txt" \
  -F "run_in_background=false" | jq .

rm /tmp/cognee-store-batch.txt
```

### Step 7: Report

```
COGNEE STORE COMPLETE
=====================
Dataset:    my-project
Stored:     13 items (3 entities, 2 decisions, 1 event, 4 tasks, 2 updates, 1 relationship)
Cognified:  yes
Graph:      updated with new nodes and edges

Recall with: /cognee-recall "what did we decide about authentication"
```

## Behavior Rules

### Auto-write (no confirmation needed)
- Entity sync from external sources (MCP, APIs)
- Task status updates
- Event logging from emails and meetings
- Changelog entries

### Confirm-write (propose to user first)
- New decisions
- New relationships between entities
- Bulk end-of-session flush (`/cognee-store:update`)

### Inline store (single items during conversation)
When a decision is made or important info surfaces mid-conversation, offer a lightweight store:

```
> "Should I store this decision in Cognee? [store / skip]"
```

If "store": format as single item and send via `/remember`.

### Dedup
Before storing, check if similar content already exists by doing a quick search:

```bash
curl -s -X POST "$COGNEE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$SEARCH_TEXT\", \"datasets\": [\"$DATASET\"], \"search_type\": \"FEELING_LUCKY\", \"top_k\": 5}" | jq .
```

If high-confidence match found (>80% similarity), note it and skip: "Similar content already exists in graph. Skipping duplicate."

### Batch efficiency
Group all items into a single `/remember` call rather than sending individual requests. Cognee processes the batch and builds graph connections between items automatically.

## Cognee vs Brain: When to use which for storing

| Scenario | Use |
|----------|-----|
| Quick local decision log | Brain (SQLite, instant) |
| Cross-project entity linking | Cognee (graph edges span datasets) |
| Semantic search needed later | Cognee (embeddings enable fuzzy recall) |
| Offline / no Cognee running | Brain (zero dependencies) |
| Session context for auto-recall | Cognee (session-aware search) |
| Both (belt and suspenders) | Store to both |
