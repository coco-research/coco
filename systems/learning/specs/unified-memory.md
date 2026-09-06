# Coco Unified Memory — Cross-Agent Context Vault Specification

## Overview

Unified Memory provides a shared context vault that all agents (Team roles, Brain, GSD) can read from and write to. It bridges the Learning System's instincts with the Brain DB's knowledge graph and makes both available as structured context during agent execution.

## Architecture

```
┌─────────────────────────────────────────────┐
│           Unified Memory Vault              │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Instincts│  │ Decisions│  │ Entities │  │
│  │(Learning)│  │ (Brain)  │  │ (Brain)  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │         │
│       └─────────────┼─────────────┘         │
│                     ▼                       │
│            Context Resolver                 │
│         (relevance + recency)               │
│                     ▼                       │
│          Agent Prompt Injection             │
└─────────────────────────────────────────────┘
```

## Storage Layout

```
~/.coco/memory/
├── vault.db              # SQLite unified index
├── cache/                # Rendered context snapshots
│   └── <session-id>.json
└── config.yaml           # Vault configuration
```

## Vault DB Schema

### context_entries

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| source | TEXT | 'instinct', 'decision', 'entity', 'observation' |
| source_id | TEXT | ID in source system |
| domain | TEXT | Category for filtering |
| content | TEXT | Rendered text content |
| relevance_score | REAL | 0.0–1.0 computed score |
| project_id | TEXT | Project scope hash |
| created_at | TEXT | ISO8601 timestamp |
| updated_at | TEXT | Last refresh timestamp |
| tags | TEXT | JSON array of tags |

### access_log

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| session_id | TEXT | Agent session identifier |
| agent_role | TEXT | Role that accessed context |
| entry_ids | TEXT | JSON array of accessed entry IDs |
| accessed_at | TEXT | ISO8601 timestamp |

## Context Resolution Algorithm

When an agent requests context for a task:

1. **Filter** by project_id and domain relevance
2. **Score** each entry:
   - Base score from source confidence/status
   - Recency boost: `max(0, 1.0 - days_since_update * 0.01)`
   - Tag overlap bonus: `0.1 * matching_tags / total_query_tags`
3. **Rank** by composite score descending
4. **Select** top-N entries (default: 10, configurable)
5. **Render** into prompt-friendly format

## Agent Integration Points

### Pre-Execution Context Injection

Before any Team role executes, the orchestrator calls:
```python
context = resolve_context(project_id, role, task_description, limit=10)
```

The returned context is prepended to the agent's system prompt under a `<unified_memory>` block.

### Post-Execution Feedback Capture

After agent completion, relevant outputs are fed back:
- Code reviewer findings → team_bridge.ingest_team_feedback()
- Test guardian results → observation append
- Refactoring decisions → brain_sync.sync_instincts_to_brain()

## Configuration (config.yaml)

```yaml
vault:
  max_context_entries: 10000
  context_limit_per_agent: 10
  stale_threshold_days: 90
  
scoring:
  recency_weight: 0.3
  confidence_weight: 0.5
  tag_overlap_weight: 0.2
  
sources:
  instincts:
    enabled: true
    min_confidence: 0.4
  decisions:
    enabled: true
    min_status: "proposed"
  entities:
    enabled: true
    types: ["architecture", "pattern", "convention"]
```

## Security Considerations

- Vault DB is local-only; no network access
- Project-scoped entries never leak across projects
- Sensitive patterns (secrets, credentials) are excluded by detector rules
- Access logging enables audit trail for compliance
