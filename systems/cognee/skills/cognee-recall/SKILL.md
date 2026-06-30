---
name: cognee:recall
description: "Semantic and graph search across Cognee knowledge graph. Queries project memory, finds related entities and decisions, injects results as agent context. Triggers on: 'cognee recall', 'search memory', 'what do we know about', 'find related', 'graph search', 'memory search', 'recall context'."
---

# /cognee-recall — Search & Recall from Knowledge Graph

Semantic, graph-traversal, and lexical search across Cognee's knowledge graph. Finds entities, decisions, events, and their relationships — then injects relevant results as agent context for informed decision-making.

## Quick Reference

```bash
COGNEE="${COGNEE_BASE_URL:-http://localhost:8000}"
DATASET="my-project"

# Semantic search (auto-selects best strategy)
curl -s -X POST "$COGNEE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication decisions", "datasets": ["my-project"], "search_type": "FEELING_LUCKY", "top_k": 10}' | jq .

# Graph completion search (relationship-aware)
curl -s -X POST "$COGNEE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "who reports to Alice", "datasets": ["my-project"], "search_type": "GRAPH_COMPLETION", "top_k": 10}' | jq .

# Recall with context injection (adds system prompt)
curl -s -X POST "$COGNEE/api/v1/recall" \
  -H "Content-Type: application/json" \
  -d '{"query": "rate limiting", "datasets": ["my-project"], "top_k": 10, "only_context": true}' | jq .

# Cross-project search
curl -s -X POST "$COGNEE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "auth decisions", "datasets": ["project-a", "project-b", "project-c"], "search_type": "FEELING_LUCKY"}' | jq .
```

## Search Types

Cognee supports multiple search strategies. Use `FEELING_LUCKY` for auto-selection (recommended), or specify one:

| Type | Best for |
|------|---------|
| `FEELING_LUCKY` | Auto-selects best strategy (default, recommended) |
| `GRAPH_COMPLETION` | Relationship-heavy queries ("who owns X", "what depends on Y") |
| `GRAPH_COMPLETION_COT` | Complex reasoning with chain-of-thought |
| `GRAPH_COMPLETION_CONTEXT_EXTENSION` | Expanding context around a node |
| `GRAPH_SUMMARY_COMPLETION` | Summarization of graph neighborhood |
| `RAG_COMPLETION` | Retrieval-augmented generation |
| `TRIPLET_COMPLETION` | Entity-relationship-entity patterns |
| `CHUNKS` | Raw chunk retrieval |
| `CHUNKS_LEXICAL` | Keyword/lexical matching |
| `SUMMARIES` | Pre-computed summaries |
| `NATURAL_LANGUAGE` | Free-form natural language queries |
| `TEMPORAL` | Time-based queries |
| `CODING_RULES` | Code-specific patterns |

## Sub-commands

### /cognee-recall search — Run a semantic/graph search

**Procedure:**

1. Ask the user what they're looking for (or use the provided query).
2. Determine the best search type based on the query:
   - Queries about relationships → `GRAPH_COMPLETION`
   - General "what do we know" → `FEELING_LUCKY`
   - Time-based ("last week", "in Q2") → `TEMPORAL` if available
   - Code-related → `CODING_RULES`
3. Detect which datasets to search:
   - Default: current project dataset
   - If user mentions another project: include its dataset
   - Use `/cognee status` to list available datasets
4. Execute search:

```bash
COGNEE="${COGNEE_BASE_URL:-http://localhost:8000}"

curl -s -X POST "$COGNEE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"$QUERY\",
    \"datasets\": $DATASETS_JSON,
    \"search_type\": \"$SEARCH_TYPE\",
    \"top_k\": $TOP_K
  }" | jq .
```

5. Present results:

```
COGNEE RECALL — "$QUERY"
==================================================
Found N results across M datasets

[1] DECISION: Use JWT for API auth (2026-06-30)
    Context: Stateless, works with existing infra
    Dataset: my-project | Score: 0.94

[2] ENTITY: Auth Service — depends_on → PlatformHub
    Description: Authentication and authorization service
    Dataset: my-project | Score: 0.87

[3] TASK: Set up JWT middleware (open, priority 1)
    Assigned to: Alice Chen
    Dataset: my-project | Score: 0.82

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### /cognee-recall context — Inject results as agent context

Same as search, but formats results for direct injection into the agent's context window. Use this before making architectural decisions or when context from past sessions is needed.

**Procedure:**

1. Run search as above.
2. Format results as a compact context block:

```
[COGNEE CONTEXT INJECTION — {timestamp}]
Query: "{original_query}"
Dataset(s): {dataset_names}

Relevant knowledge:
• DECISION ({date}): {text} — {context} [relevance: {score}]
• ENTITY: {name} ({type}) — {description} [relevance: {score}]
• TASK: {text} ({status}) — assigned to {assignee} [relevance: {score}]
• EVENT: {title} ({date}, {type}) — {summary} [relevance: {score}]

Use this context to inform your response. Cite specific decisions and entities where relevant.
```

3. The agent then uses this context transparently in its reasoning.

### /cognee-recall graph — Explore entity neighborhood

Explore the graph around a specific entity to understand its relationships.

```bash
COGNEE="${COGNEE_BASE_URL:-http://localhost:8000}"

# First, get the dataset ID
DATASET_ID=$(curl -s "$COGNEE/api/v1/datasets" | jq -r '.[] | select(.name=="my-project") | .id')

# Get the full graph
curl -s "$COGNEE/api/v1/datasets/$DATASET_ID/graph" | jq .
```

Present as a relationship map:

```
ENTITY GRAPH — "Auth Service" (my-project)
==================================================
                      ┌──────────────────┐
                      │   Auth Service   │
                      │   (system)       │
                      └───┬──────────┬───┘
                          │          │
              depends_on  │          │ owns
                          │          │
                   ┌──────▼──┐  ┌───▼──────────┐
                   │Platform │  │ JWT Middleware│
                   │Hub      │  │ (module)      │
                   │(module) │  └───────────────┘
                   └─────────┘

Related decisions:
  • Use JWT for API auth (2026-06-30) — relates to Auth Service

Related tasks:
  • Set up JWT middleware (open) — assigned to Alice Chen
  • Update API docs (open) — assigned to unassigned
```

### /cognee-recall cross-project — Search across multiple projects

Search for related knowledge across all available datasets.

```bash
COGNEE="${COGNEE_BASE_URL:-http://localhost:8000}"

# Get all dataset names
DATASETS=$(curl -s "$COGNEE/api/v1/datasets" | jq -r '[.[].name] | join(",")')

# Cross-project search
curl -s -X POST "$COGNEE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"$QUERY\",
    \"datasets\": [$DATASETS_JSON],
    \"search_type\": \"FEELING_LUCKY\",
    \"top_k\": 15
  }" | jq .
```

Present results grouped by dataset:

```
CROSS-PROJECT RECALL — "$QUERY"
==================================================
Found N results across M datasets

my-project (5 results):
  [1] DECISION: Use JWT for API auth — 0.94
  [2] ENTITY: Auth Service — 0.87
  ...

e-and-c (3 results):
  [1] DECISION: Stakeholder role for external users — 0.91
  [2] ENTITY: External Review System — 0.84
  ...

optimize (2 results):
  [1] DECISION: Migration to pgvector — 0.78
  ...
```

## Behavior Rules

### Proactive recall triggers
Automatically run `/cognee-recall search` when:
- User asks "what do we know about X" or "what did we decide about Y"
- User starts a new task that references past work ("continue working on auth")
- User makes a decision that might conflict with past decisions
- Before architectural or design discussions that would benefit from context

### Relevance threshold
Only show results with relevance score > 0.5 by default. If fewer than 3 results exceed threshold, tell the user: "Only {N} low-relevance results found. Try a broader query."

### Context injection discipline
- Inject context **before** reasoning about a decision, not after.
- Cite specific decisions/entities from the graph in responses: "Based on the June 30 decision to use JWT for API auth [Cognee]..."
- Never fabricate — if the graph has no relevant data, say so.

### Session-aware recall
If Cognee supports sessions, tag recalls with a session ID for better multi-turn context:

```bash
SESSION_ID="coco-$(date +%s)"

curl -s -X POST "$COGNEE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"$QUERY\",
    \"datasets\": [\"$DATASET\"],
    \"search_type\": \"FEELING_LUCKY\",
    \"top_k\": 10
  }" | jq .
```

## Fallback Behavior

If Cognee is unreachable:
1. Check if Brain is available: look for `project_brain.db` in current or parent directories
2. If available: "Cognee is not running. Using Brain for this query instead." Run equivalent `/brain context --search "query"`
3. If neither available: "No memory backend available. Start Cognee with `cognee server start` or initialize Brain with `/brain init`."

## Prerequisites

Cognee must be running and the project dataset must exist (created via `/cognee init`).

```bash
# Verify
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/datasets | jq '.[].name'
```
