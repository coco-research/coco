# Phase 2: Org Hierarchy — API Contract

## New Table: `nodes` (in platform.db)

```sql
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    parent_id TEXT REFERENCES nodes(id),
    hub_project_id TEXT,
    label TEXT NOT NULL,
    node_type TEXT NOT NULL DEFAULT 'group',
    sort_order INTEGER NOT NULL DEFAULT 0,
    path TEXT NOT NULL DEFAULT '',
    depth INTEGER NOT NULL DEFAULT 0,
    icon TEXT,
    color TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_nodes_path ON nodes(path);
CREATE INDEX IF NOT EXISTS idx_nodes_hub ON nodes(hub_project_id);
```

## New Endpoints

### Tree CRUD
- `GET /api/tree` — returns full tree as nested JSON
- `GET /api/tree/:id` — single node + immediate children
- `GET /api/tree/:id/subtree` — full subtree rooted at :id
- `POST /api/tree` — create node `{ parent_id, label, node_type, hub_project_id?, sort_order? }`
- `PATCH /api/tree/:id` — update node `{ label?, node_type?, icon?, color?, metadata?, sort_order? }`
- `DELETE /api/tree/:id` — delete leaf/empty node only
- `POST /api/tree/:id/move` — `{ new_parent_id, sort_order? }` — recalculates path+depth atomically
- `POST /api/tree/reorder` — `[{ id, sort_order }, ...]` — batch sibling reorder
- `GET /api/tree/unplaced` — hub.db projects with no corresponding node

### Existing Endpoints — Add `node_id` + `subtree` params
- `GET /api/agents?node_id=X&subtree=true`
- `GET /api/goals?node_id=X&subtree=true`
- `GET /api/tasks?node_id=X&subtree=true`
- `GET /api/costs/summary?node_id=X&subtree=true`
- `GET /api/activity?node_id=X&subtree=true`
- `GET /api/todos?node_id=X` (hub.db, team-level only)

### Subtree Query Pattern
When `subtree=true`, resolve node_id to its path, then:
```sql
SELECT n.id FROM nodes n WHERE n.path LIKE ? || '%'
-- Then filter entities: WHERE node_id IN (...)
```

## Renamed Endpoints
- `GET /api/teams` — alias for `GET /api/projects` (hub.db), returns as "teams"
- `GET /api/teams/:id` — alias for `GET /api/projects/:id`

## Schema Migration
1. Add `node_id TEXT` column to: agents, goals, tasks, cost_ledger, budgets
2. Auto-seed: create root node "My Portfolio", one leaf per hub.db project
3. Backfill: UPDATE agents SET node_id = (SELECT id FROM nodes WHERE hub_project_id = agents.project_id)
4. Keep project_id columns as deprecated (remove in future phase)

## Frontend Routes
- `/tree` — tree builder/editor page
- `/tree/:nodeId` — tree focused on specific node
- Existing `/projects/:id` routes remain (hub_project_id based)

## ScopeContext (replaces ProjectContext)
- `selectedNodeId: string | null`
- `selectedNode: Node | null`
- `scopeProjectIds: string[]` — all hub_project_ids under the selected subtree
- Persisted to localStorage as `coco.selectedNodeId`
