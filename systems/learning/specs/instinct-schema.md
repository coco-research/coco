# Coco Learning System — Instinct Schema

## Overview

Instincts are atomic learned behaviors extracted from session observations.
Each instinct captures a reusable pattern with confidence scoring and lifecycle management.

## Storage Layout

```
~/.coco/learning/
├── global/
│   └── instincts/
│       ├── <instinct-id>.yaml
│       └── ...
└── projects/
    └── <project-hash>/
        ├── observations.jsonl
        └── instincts/
            ├── <instinct-id>.yaml
            └── ...
```

## Instinct YAML Format

```yaml
id: "inst-20260905-a1b2c3"
pattern: "Always run tests after modifying database schema"
domain: "testing"
confidence: 0.7
evidence_count: 5
created_at: "2026-09-05T10:00:00Z"
updated_at: "2026-09-05T14:30:00Z"
source_project: "69b36043d669"
promoted: false
superseded_by: null
tags: ["database", "testing", "safety"]
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique identifier (inst-YYYYMMDD-xxxxxx) |
| pattern | string | Natural language description of the learned behavior |
| domain | string | Category: testing, security, architecture, workflow, debugging, performance |
| confidence | float | 0.3–0.9 range, computed from evidence |
| evidence_count | int | Number of supporting observations |
| created_at | ISO8601 | First observation timestamp |
| updated_at | ISO8601 | Last reinforcement timestamp |
| source_project | string | Project hash where first observed |
| promoted | bool | True if promoted to global |
| superseded_by | string\|null | ID of newer instinct that replaces this one |
| tags | list[str] | Searchable labels |

## Confidence Algorithm

```
confidence = min(0.9, 0.3 + (evidence_count * 0.05))
```

- Starts at 0.3 (minimum viable confidence)
- Gains 0.05 per supporting observation
- Caps at 0.9 (never fully certain)
- Decays 0.02 per day without reinforcement (floor 0.3)

## Lifecycle States

| State | Condition |
|-------|-----------|
| candidate | confidence < 0.5 |
| active | 0.5 <= confidence < 0.7 |
| strong | confidence >= 0.7 |
| dormant | no reinforcement for 30 days |
| superseded | replaced by newer instinct |

## Promotion Rules

An instinct is eligible for global promotion when:
1. confidence >= 0.7
2. evidence_count >= 10
3. Observed in >= 2 distinct projects
4. Not domain-specific to a single project's tooling

## Observation JSONL Format

Each line in `observations.jsonl`:

```json
{"timestamp":"2026-09-05T22:28:01Z","event":"PostToolUse","session":"abc123","tool":"Bash","input_summary":"npm test","output_summary":"12 passed","project_id":"69b36043d669","project_name":"coco"}
```
