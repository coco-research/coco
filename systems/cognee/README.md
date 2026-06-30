# Cognee — Knowledge Graph Memory Backend

Graph-based, embedding-powered persistent memory for Coco agents. Upgrades project memory from a flat SQLite file (Brain) to a true knowledge graph with semantic search, cross-project entity linking, and multi-turn session awareness.

## What it is

Cognee is an open-source AI memory platform ([coco-research/cognee](https://github.com/coco-research/cognee)) that gives agents persistent long-term memory. This bundle wires Cognee into Coco as an optional memory backend, coexisting with the default Brain bundle.

## What it gives you over Brain alone

| Feature | Brain (SQLite) | Cognee |
|---------|---------------|--------|
| Storage | Flat relational DB | Knowledge graph + embeddings |
| Search | Keyword + relational queries | Semantic + graph traversal + lexical |
| Cross-project | Manual aggregation | Native cross-dataset graph queries |
| Sessions | Stateless | Multi-turn session tracking |
| Auto-recall | Manual context query | Automatic memory injection before agent runs |
| Entity linking | Within one project | Across all projects and datasets |

## Install

### Prerequisites

Cognee must be running locally (or accessible via URL):

```bash
pip install cognee
cognee server start   # starts at http://localhost:8000
```

### Wire into Coco

```bash
bash install.sh --adapter claude-code --systems cognee
```

Or with other bundles:

```bash
bash install.sh --adapter claude-code --systems brain,cognee,gsd
```

## Skills

| Skill | What it does |
|-------|-------------|
| `/cognee` | Status, init, dataset management, backend switching |
| `/cognee-store` | Push decisions, entities, events, context into the graph |
| `/cognee-recall` | Semantic + graph search, inject results as agent context |

## When to use Cognee vs Brain

- **Brain** → You want zero-dependency, per-project knowledge that just works. Good for: tracking decisions and entities within a single project.
- **Cognee** → You want semantic search across projects, graph-based entity relationships, and automatic context injection. Good for: multi-project work, complex entity webs, long-running agent memory.
- **Both** → They coexist. Use Brain for quick per-project lookup, Cognee for cross-project graph queries and recall.

## Data model

Cognee maps Coco's concepts to its graph:

| Coco Concept | Cognee Representation |
|-------------|---------------------|
| Entity (person, team, system, module) | Graph node with type label |
| Relationship (member_of, owns, depends_on) | Graph edge |
| Decision | Graph node with metadata (date, decided_by, context) |
| Event | Graph node with temporal data |
| Task | Graph node with status tracking |
| Session context | Session-scoped nodes linked to agent runs |

## API reference

All skills use Cognee's HTTP API. Default base URL: `http://localhost:8000` (overridable via `COGNEE_BASE_URL`).

Key endpoints used by this bundle:

- `GET /health` — server status
- `POST /api/v1/add` — ingest data
- `POST /api/v1/cognify` — process and build graph
- `POST /api/v1/search` — query with graph/semantic search
- `POST /api/v1/recall` — semantic search with context injection
- `POST /api/v1/remember` — add + cognify convenience
- `GET /api/v1/datasets` — list datasets
- `POST /api/v1/datasets` — create dataset
