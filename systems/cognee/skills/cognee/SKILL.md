---
name: cognee
description: "Knowledge graph memory backend powered by Cognee. Query, status check, dataset management, and backend switching between Brain and Cognee. Triggers on: 'cognee', 'knowledge graph', 'graph memory', 'switch memory', 'memory backend'."
---

# /cognee — Knowledge Graph Memory Backend

A persistent knowledge graph memory system powered by [Cognee](https://github.com/coco-research/cognee). Stores entities, decisions, events, and relationships as graph nodes with embeddings, enabling semantic search across projects and sessions.

## Quick Reference

```bash
COGNEE="http://localhost:8000"   # default; override with COGNEE_BASE_URL

# Status check
curl -s "$COGNEE/health" | jq .

# List datasets
curl -s "$COGNEE/api/v1/datasets" | jq .

# Create a dataset for this project
curl -s -X POST "$COGNEE/api/v1/datasets" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-project"}' | jq .

# Quick semantic search
curl -s -X POST "$COGNEE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "what did we decide about authentication", "search_type": "FEELING_LUCKY", "top_k": 10}' | jq .
```

## Sub-commands

### /cognee status — Health check and dataset overview

Check if Cognee is reachable and show available datasets.

```bash
COGNEE="${COGNEE_BASE_URL:-http://localhost:8000}"

echo "=== Cognee Status ==="
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$COGNEE/health" 2>/dev/null)
if [ "$HEALTH" = "200" ]; then
    echo "Server:  RUNNING at $COGNEE"
    echo ""
    echo "Datasets:"
    curl -s "$COGNEE/api/v1/datasets" | jq -r '.[] | "  • \(.name) (\(.id))"'
else
    echo "Server:  NOT REACHABLE"
    echo ""
    echo "Start Cognee:"
    echo "  pip install cognee && cognee server start"
fi
```

### /cognee init — Initialize a project dataset

Create a Cognee dataset for the current project.

**Procedure:**

1. Ask the user for the **dataset name** (default: current directory name, slugified).
2. Check if a dataset with that name already exists:

```bash
curl -s "$COGNEE/api/v1/datasets" | jq -r '.[].name'
```

3. If it exists: "Dataset 'X' already exists. Using it." → skip creation.
4. If not: create it:

```bash
curl -s -X POST "$COGNEE/api/v1/datasets" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"$DATASET_NAME\"}" | jq .
```

5. Confirm:
```
COGNEE INITIALIZED
==================
Dataset:  {name} ({id})
Endpoint: $COGNEE

Next: Use /cognee-store to push knowledge, /cognee-recall to search.
```

### /cognee switch — Toggle between Brain and Cognee

Switch which memory backend is primary for this project.

**Options:**
- `brain` → Use SQLite-based Brain (zero-dependency, per-project)
- `cognee` → Use Cognee knowledge graph (semantic search, cross-project)
- `both` → Use both (Brain for quick per-project lookup, Cognee for graph queries)

**Behavior:**
This sets a preference. Skills that support both backends will check this preference and route accordingly. Default behavior without explicit switch: Brain for local queries, Cognee for cross-project and semantic search.

### /cognee graph — View entity relationships

Show the knowledge graph for a specific entity or the current dataset.

```bash
# Get dataset ID first
DATASET_ID=$(curl -s "$COGNEE/api/v1/datasets" | jq -r '.[] | select(.name=="my-project") | .id')

# View graph
curl -s "$COGNEE/api/v1/datasets/$DATASET_ID/graph" | jq .
```

## Architecture

Cognee and Brain coexist. They are not mutually exclusive:

```
┌─────────────────────────────────────┐
│           Coco Agent                │
├─────────────────────────────────────┤
│  /cognee-recall  │  /brain          │
│  /cognee-store   │  /brain-update   │
├─────────────────────────────────────┤
│  Cognee (graph)  │  Brain (SQLite)   │
│  localhost:8000  │  project_brain.db │
└─────────────────────────────────────┘
```

- **Write path**: `/cognee-store` pushes to Cognee; `/brain-update` pushes to SQLite. You can write to both.
- **Read path**: `/cognee-recall` for semantic/graph queries; `/brain` for structured relational queries.
- **No sync between them** — they are independent stores. If you need consistency, pick one as primary and use the other as supplementary.

## Behavior Rules

### Detect Cognee availability
Before any Cognee operation, check the health endpoint. If unreachable:
- Tell the user: "Cognee is not running. Start it with `cognee server start` or install with `pip install cognee`."
- Fall back gracefully: offer to use Brain instead for the same operation.

### Dataset naming convention
Default dataset name = project directory slug. For example:
- `/home/user/MyProject` → `myproject`
- `/home/user/E&C` → `e-and-c`

User can override. Ask once, remember the mapping.

### Multi-project awareness
Unlike Brain (one DB per project folder), Cognee datasets are namespaced. An agent working across multiple projects can query multiple datasets in a single search:

```bash
curl -s -X POST "$COGNEE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication decisions", "datasets": ["project-a", "project-b"], "search_type": "FEELING_LUCKY"}' | jq .
```

## Prerequisites

Cognee must be installed and running:

```bash
pip install cognee
cognee server start
```

Verify: `curl http://localhost:8000/health`
