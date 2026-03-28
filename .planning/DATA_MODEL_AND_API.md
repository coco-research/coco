# CoCo Platform — Data Model & API Specification

**Version:** 1.0
**Date:** 2026-03-27
**Author:** Rijul Kalra / Claude Opus 4.6
**Status:** Draft — awaiting review

---

## Table of Contents

1. [Database Strategy](#1-database-strategy)
2. [platform.db Schema](#2-platformdb-schema)
3. [REST API](#3-rest-api)
4. [SSE Event Types](#4-sse-event-types)
5. [Integration Notes](#5-integration-notes)

---

## 1. Database Strategy

### Two SQLite Databases

```
~/.hub/hub.db         — Knowledge Hub (EXISTING, read-only from platform)
~/.coco/platform.db   — CoCo Platform (NEW, read-write)
```

| Property | hub.db | platform.db |
|----------|--------|-------------|
| Owner | Knowledge Hub MCP server | CoCo Platform FastAPI |
| Access from Platform | Read-only (`?mode=ro`) | Read-write |
| Tables | content, projects, project_content, drafts, todos, api_costs, learned_rules, entities, content_entities, sync_state, content_fts (FTS5), content_vec (vec0) | stations, tasks, task_documents, task_comments, cost_events, resource_locks, trust_matrix, activity_log, budgets, station_routines, chat_messages |
| Migration tool | Manual `schema_version` table | Alembic |
| FTS | content_fts (FTS5, porter+unicode61) | None (relies on hub.db FTS) |

### Connection Configuration

```python
import sqlite3

# hub.db — read-only, WAL mode (set by KH)
hub_conn = sqlite3.connect(
    "file:~/.hub/hub.db?mode=ro",
    uri=True,
    check_same_thread=False,
)
hub_conn.execute("PRAGMA journal_mode")  # WAL (already set by KH)
hub_conn.execute("PRAGMA busy_timeout = 5000")
hub_conn.row_factory = sqlite3.Row

# platform.db — read-write, WAL mode (we set it)
platform_conn = sqlite3.connect(
    "~/.coco/platform.db",
    check_same_thread=False,
)
platform_conn.execute("PRAGMA journal_mode = WAL")
platform_conn.execute("PRAGMA busy_timeout = 5000")
platform_conn.execute("PRAGMA foreign_keys = ON")
platform_conn.row_factory = sqlite3.Row
```

### Alembic Setup for platform.db

```
backend/
  alembic/
    versions/
      001_initial_schema.py
    env.py
  alembic.ini
```

`alembic.ini` points at `sqlite:///~/.coco/platform.db`. Each migration is auto-generated from SQLAlchemy models in `backend/models/platform.py`. Run with:

```bash
alembic upgrade head      # apply all pending
alembic revision --autogenerate -m "add station_routines"
```

### Cross-DB References

`platform.db` columns like `tasks.project_id` or `cost_events.task_id` reference `hub.db` rows by convention (TEXT foreign key to `projects.id` or `content.id`). These are **not enforced** via SQL foreign keys since they cross database boundaries. The application layer validates existence on write.

---

## 2. platform.db Schema

### Full CREATE TABLE SQL

```sql
-- ============================================================
-- platform.db — CoCo Platform schema
-- Applied via Alembic migration 001_initial_schema
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------
-- Stations: Claude Code background agent processes
-- ---------------------------------------------------------
CREATE TABLE stations (
    id          TEXT PRIMARY KEY,                -- ULID, e.g. "01HX3K..."
    name        TEXT NOT NULL,                   -- human label, e.g. "audit-board-drafter"
    role        TEXT,                            -- freeform, e.g. "Draft Confluence pages for AuditBoard"
    model       TEXT NOT NULL DEFAULT 'sonnet',  -- 'haiku', 'sonnet', 'opus'
    status      TEXT NOT NULL DEFAULT 'idle'
                CHECK(status IN ('idle','running','paused','failed','killed')),
    config      TEXT DEFAULT '{}',               -- JSON blob: system_prompt, allowed_tools, etc.
    pid         INTEGER,                         -- OS process ID when running, NULL otherwise
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX idx_stations_status ON stations(status);

-- ---------------------------------------------------------
-- Tasks: work items assigned to stations
-- ---------------------------------------------------------
CREATE TABLE tasks (
    id              TEXT PRIMARY KEY,            -- ULID
    title           TEXT NOT NULL,
    description     TEXT,
    station_id      TEXT REFERENCES stations(id) ON DELETE SET NULL,
    status          TEXT NOT NULL DEFAULT 'open'
                    CHECK(status IN ('open','checked_out','in_progress','review','done','cancelled')),
    checked_out_by  TEXT REFERENCES stations(id),  -- station that holds the lock
    checked_out_at  TEXT,
    priority        INTEGER NOT NULL DEFAULT 3,    -- 1=critical, 2=high, 3=medium, 4=low
    project_id      TEXT,                          -- cross-DB ref to hub.db projects.id
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    completed_at    TEXT
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_station ON tasks(station_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);

-- ---------------------------------------------------------
-- Task Documents: versioned text artifacts per task
-- ---------------------------------------------------------
CREATE TABLE task_documents (
    id          TEXT PRIMARY KEY,                -- ULID
    task_id     TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    key         TEXT NOT NULL,                   -- e.g. "plan", "draft", "review-notes"
    body        TEXT NOT NULL,
    revision    INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    UNIQUE(task_id, key)
);

-- ---------------------------------------------------------
-- Task Comments: threaded discussion on tasks
-- ---------------------------------------------------------
CREATE TABLE task_comments (
    id          TEXT PRIMARY KEY,                -- ULID
    task_id     TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    author      TEXT NOT NULL,                   -- "user", station_id, or "coco"
    body        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX idx_task_comments_task ON task_comments(task_id);

-- ---------------------------------------------------------
-- Cost Events: per-call token usage and dollar cost
-- ---------------------------------------------------------
CREATE TABLE cost_events (
    id              TEXT PRIMARY KEY,            -- ULID
    station_id      TEXT REFERENCES stations(id),
    task_id         TEXT REFERENCES tasks(id),
    model           TEXT NOT NULL,               -- e.g. "claude-sonnet-4-20250514"
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    cost_usd        REAL NOT NULL DEFAULT 0.0,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX idx_cost_events_station ON cost_events(station_id);
CREATE INDEX idx_cost_events_created ON cost_events(created_at);

-- ---------------------------------------------------------
-- Resource Locks: prevent concurrent access to shared resources
-- ---------------------------------------------------------
CREATE TABLE resource_locks (
    id              TEXT PRIMARY KEY,            -- ULID
    resource_type   TEXT NOT NULL,               -- e.g. "file", "confluence_page", "jira_ticket"
    resource_id     TEXT NOT NULL,               -- e.g. file path or Jira key
    station_id      TEXT NOT NULL REFERENCES stations(id),
    claimed_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    expires_at      TEXT NOT NULL,               -- auto-release after TTL
    UNIQUE(resource_type, resource_id)
);

-- ---------------------------------------------------------
-- Trust Matrix: per-station permission escalation
-- ---------------------------------------------------------
CREATE TABLE trust_matrix (
    station_id              TEXT NOT NULL REFERENCES stations(id),
    action_type             TEXT NOT NULL,       -- e.g. "git_push", "jira_create", "confluence_update", "file_write"
    permission              TEXT NOT NULL DEFAULT 'confirm'
                            CHECK(permission IN ('auto','confirm','blocked')),
    consecutive_approvals   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (station_id, action_type)
);

-- ---------------------------------------------------------
-- Activity Log: audit trail of all platform events
-- ---------------------------------------------------------
CREATE TABLE activity_log (
    id          TEXT PRIMARY KEY,                -- ULID
    station_id  TEXT REFERENCES stations(id),
    task_id     TEXT REFERENCES tasks(id),
    action      TEXT NOT NULL,                   -- e.g. "station.spawned", "task.checked_out", "decision.approved"
    detail      TEXT DEFAULT '{}',               -- JSON blob with action-specific data
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX idx_activity_log_station ON activity_log(station_id);
CREATE INDEX idx_activity_log_action ON activity_log(action);
CREATE INDEX idx_activity_log_created ON activity_log(created_at);

-- ---------------------------------------------------------
-- Budgets: monthly spend caps per project
-- ---------------------------------------------------------
CREATE TABLE budgets (
    project_id          TEXT PRIMARY KEY,        -- cross-DB ref to hub.db projects.id
    monthly_limit_usd   REAL NOT NULL,
    alert_threshold     REAL NOT NULL DEFAULT 0.8  -- fraction, fires at 80% by default
);

-- ---------------------------------------------------------
-- Station Routines: cron-scheduled recurring tasks
-- ---------------------------------------------------------
CREATE TABLE station_routines (
    id          TEXT PRIMARY KEY,                -- ULID
    station_id  TEXT NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
    cron_expr   TEXT NOT NULL,                   -- e.g. "*/15 * * * *"
    enabled     INTEGER NOT NULL DEFAULT 1,      -- 0=disabled, 1=enabled (SQLite bool)
    last_run_at TEXT,
    next_run_at TEXT
);

CREATE INDEX idx_station_routines_next ON station_routines(next_run_at);

-- ---------------------------------------------------------
-- Chat Messages: conversation history with CoCo web chat
-- ---------------------------------------------------------
CREATE TABLE chat_messages (
    id          TEXT PRIMARY KEY,                -- ULID
    role        TEXT NOT NULL                    -- "user", "assistant", "system"
                CHECK(role IN ('user','assistant','system')),
    content     TEXT NOT NULL,
    metadata    TEXT DEFAULT '{}',               -- JSON: model, tokens, cost, tool_calls, etc.
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX idx_chat_messages_created ON chat_messages(created_at);
```

### Example Rows

**stations:**

```json
{
  "id": "01JQXK7M3NFVB0YPTG2E5A",
  "name": "audit-board-drafter",
  "role": "Draft Confluence updates from voice memo transcripts for AuditBoard project",
  "model": "sonnet",
  "status": "running",
  "config": "{\"system_prompt\": \"You are a Confluence page drafter...\", \"allowed_tools\": [\"Read\", \"Write\", \"Bash\"], \"max_turns\": 50}",
  "pid": 48721,
  "created_at": "2026-03-27T09:15:00.000Z",
  "updated_at": "2026-03-27T09:15:02.341Z"
}
```

**tasks:**

```json
{
  "id": "01JQXK8P4QGW71ZRH3F6B2",
  "title": "Draft Q1 QBR slides from voice memos",
  "description": "Synthesize 3 voice memos from March into QBR talking points",
  "station_id": "01JQXK7M3NFVB0YPTG2E5A",
  "status": "in_progress",
  "checked_out_by": "01JQXK7M3NFVB0YPTG2E5A",
  "checked_out_at": "2026-03-27T09:16:00.000Z",
  "priority": 2,
  "project_id": "audit-board",
  "created_at": "2026-03-27T09:10:00.000Z",
  "completed_at": null
}
```

**trust_matrix:**

```json
[
  { "station_id": "01JQXK7M3N...", "action_type": "file_write",        "permission": "auto",    "consecutive_approvals": 12 },
  { "station_id": "01JQXK7M3N...", "action_type": "git_push",          "permission": "confirm", "consecutive_approvals": 3  },
  { "station_id": "01JQXK7M3N...", "action_type": "confluence_update",  "permission": "blocked", "consecutive_approvals": 0  }
]
```

**resource_locks:**

```json
{
  "id": "01JQXL2R9T...",
  "resource_type": "confluence_page",
  "resource_id": "ACC/3PI-Architecture",
  "station_id": "01JQXK7M3N...",
  "claimed_at": "2026-03-27T09:20:00.000Z",
  "expires_at": "2026-03-27T09:50:00.000Z"
}
```

---

## 3. REST API

Base URL: `http://localhost:3001`

All responses use `Content-Type: application/json`. Timestamps are ISO 8601 UTC. IDs are ULIDs. Pagination uses `?offset=0&limit=50`. Error responses follow `{ "error": "message", "detail": "..." }`.

---

### 3.1 Dashboard

#### GET /api/dashboard

Aggregated stats from both databases.

**Response:**

```json
{
  "projects": {
    "total": 9,
    "active": 6
  },
  "content": {
    "total": 1423,
    "by_source": { "voice": 312, "email": 890, "jira": 156, "confluence": 65 },
    "ingested_today": 7
  },
  "decisions": {
    "pending": 4,
    "deferred": 2,
    "auto_handled_today": 11
  },
  "stations": {
    "running": 2,
    "idle": 1,
    "failed": 0
  },
  "cost": {
    "today_usd": 1.23,
    "month_usd": 34.56,
    "budget_pct": 0.42
  },
  "todos": {
    "open": 8,
    "overdue": 2
  },
  "drafts": {
    "pending": 5,
    "approved_today": 3
  },
  "unsorted": 12,
  "recent_activity": [
    {
      "id": "01JQXL...",
      "action": "content.classified",
      "detail": { "content_id": "c-123", "project": "audit-board", "confidence": 0.92 },
      "created_at": "2026-03-27T09:15:00.000Z"
    }
  ]
}
```

**Sources:** hub.db (content, projects, project_content, drafts, todos, sync_state), platform.db (stations, activity_log, cost_events), queue.json (decisions).

**SSE:** None (poll or compose from individual SSE events client-side).

---

### 3.2 Projects

#### GET /api/projects

List all projects from hub.db.

**Query params:** `?active=true` (filter by active flag)

**Response:**

```json
[
  {
    "id": "audit-board",
    "name": "AuditBoard",
    "jira_key": "AB",
    "confluence_space": "AB",
    "active": true,
    "content_count": 342,
    "todo_count": 3,
    "draft_count": 2,
    "created_at": "2026-01-15T00:00:00.000Z"
  }
]
```

**SSE:** None.

---

#### GET /api/projects/:id

Project detail with content counts by source and status.

**Response:**

```json
{
  "id": "audit-board",
  "name": "AuditBoard",
  "jira_key": "AB",
  "confluence_space": "AB",
  "folder_path": "/Users/Rijul_Kalra/projects/audit-board",
  "active": true,
  "content_counts": {
    "by_source": { "voice": 45, "email": 210, "jira": 67, "confluence": 20 },
    "by_status": { "complete": 300, "classified": 20, "triaged": 12, "ingested": 10 }
  },
  "open_todos": 3,
  "pending_drafts": 2,
  "cost_month_usd": 4.12,
  "created_at": "2026-01-15T00:00:00.000Z"
}
```

**SSE:** None.

---

#### GET /api/projects/:id/content

Paginated content items from hub.db for this project.

**Query params:** `?offset=0&limit=50&source=voice&status=complete&q=search+term`

**Response:**

```json
{
  "items": [
    {
      "id": "c-abc123",
      "source": "voice",
      "title": "Voice memo — staffing update",
      "status": "complete",
      "relevance_score": 0.87,
      "created_at": "2026-03-25T14:30:00.000Z",
      "confidence": 0.92,
      "method": "learned_rule"
    }
  ],
  "total": 342,
  "offset": 0,
  "limit": 50
}
```

**SSE:** `content.classified` when new items are added to this project.

---

#### GET /api/projects/:id/action-items

Action items (todos) from hub.db for this project.

**Query params:** `?status=open`

**Response:**

```json
[
  {
    "id": "todo-001",
    "title": "Follow up with EY on TCF timeline",
    "priority": "high",
    "status": "open",
    "owner": "rijul",
    "due_date": "2026-03-30",
    "source_type": "voice",
    "created_at": "2026-03-25T14:30:00.000Z"
  }
]
```

**SSE:** None.

---

#### GET /api/projects/:id/cost

Cost breakdown for a project, combining cost_events (platform.db) and api_costs (hub.db).

**Query params:** `?days=30`

**Response:**

```json
{
  "project_id": "audit-board",
  "period_days": 30,
  "total_usd": 4.12,
  "by_model": {
    "claude-haiku-3.5": 0.45,
    "claude-sonnet-4": 3.22,
    "claude-opus-4": 0.45
  },
  "by_day": [
    { "date": "2026-03-27", "cost_usd": 0.34 }
  ],
  "budget": {
    "monthly_limit_usd": 20.0,
    "alert_threshold": 0.8,
    "pct_used": 0.206
  }
}
```

**SSE:** `cost.alert` when budget threshold is crossed.

---

### 3.3 Stations

#### GET /api/stations

List all stations.

**Query params:** `?status=running`

**Response:**

```json
[
  {
    "id": "01JQXK7M3N...",
    "name": "audit-board-drafter",
    "role": "Draft Confluence updates",
    "model": "sonnet",
    "status": "running",
    "pid": 48721,
    "current_task": {
      "id": "01JQXK8P4Q...",
      "title": "Draft Q1 QBR slides",
      "status": "in_progress"
    },
    "created_at": "2026-03-27T09:15:00.000Z",
    "updated_at": "2026-03-27T09:15:02.341Z"
  }
]
```

**SSE:** `station.status` on any status change.

---

#### POST /api/stations

Create a new station definition (does not start the process).

**Request:**

```json
{
  "name": "optimize-researcher",
  "role": "Research 3PI vendor pricing from ingested emails",
  "model": "sonnet",
  "config": {
    "system_prompt": "You are a procurement research assistant...",
    "allowed_tools": ["Read", "Grep", "Glob", "WebSearch"],
    "max_turns": 30,
    "working_directory": "/Users/Rijul_Kalra/projects/optimize"
  }
}
```

**Response:** `201 Created` with the full station object.

**SSE:** `activity.new` with action `station.created`.

---

#### GET /api/stations/:id

Station detail including current task and recent activity.

**Response:**

```json
{
  "id": "01JQXK7M3N...",
  "name": "audit-board-drafter",
  "role": "Draft Confluence updates",
  "model": "sonnet",
  "status": "running",
  "pid": 48721,
  "config": { "...": "..." },
  "current_task": { "id": "...", "title": "...", "status": "in_progress" },
  "trust": [
    { "action_type": "file_write", "permission": "auto", "consecutive_approvals": 12 },
    { "action_type": "git_push", "permission": "confirm", "consecutive_approvals": 3 }
  ],
  "recent_activity": [
    { "id": "...", "action": "task.checked_out", "created_at": "..." }
  ],
  "cost_session_usd": 0.87,
  "created_at": "2026-03-27T09:15:00.000Z",
  "updated_at": "2026-03-27T09:15:02.341Z"
}
```

**SSE:** None (use `/api/stations/:id/logs` for live output).

---

#### PATCH /api/stations/:id

Update station config or status.

**Request:**

```json
{
  "name": "audit-board-drafter-v2",
  "model": "opus",
  "config": { "max_turns": 100 }
}
```

**Response:** `200 OK` with updated station object.

**SSE:** `station.status` if status changed; `activity.new` with action `station.updated`.

---

#### POST /api/stations/:id/spawn

Start the Claude Code CLI process for this station.

**Request:**

```json
{
  "task_id": "01JQXK8P4Q...",
  "resume_session": false
}
```

**Response:**

```json
{
  "station_id": "01JQXK7M3N...",
  "pid": 48721,
  "status": "running",
  "spawned_at": "2026-03-27T09:15:02.341Z"
}
```

**SSE:** `station.status` (idle -> running), `activity.new` with action `station.spawned`.

---

#### POST /api/stations/:id/pause

Send SIGSTOP to the station process.

**Response:**

```json
{ "station_id": "01JQXK7M3N...", "status": "paused", "pid": 48721 }
```

**SSE:** `station.status` (running -> paused).

---

#### POST /api/stations/:id/resume

Send SIGCONT to the station process.

**Response:**

```json
{ "station_id": "01JQXK7M3N...", "status": "running", "pid": 48721 }
```

**SSE:** `station.status` (paused -> running).

---

#### POST /api/stations/:id/kill

Send SIGTERM to the station process. If still alive after 5s, SIGKILL.

**Response:**

```json
{ "station_id": "01JQXK7M3N...", "status": "killed", "pid": null }
```

**SSE:** `station.status` (running -> killed), `activity.new` with action `station.killed`.

---

#### GET /api/stations/:id/logs

**SSE stream** of station stdout/stderr output. This is a long-lived connection.

**Response:** `Content-Type: text/event-stream`

```
event: stdout
data: {"line": "Reading file /Users/Rijul_Kalra/projects/audit-board/notes.md...", "ts": "2026-03-27T09:16:01.123Z"}

event: stderr
data: {"line": "Warning: file is large (2.3MB), reading first 2000 lines", "ts": "2026-03-27T09:16:01.456Z"}

event: status
data: {"status": "running", "pid": 48721}
```

---

#### POST /api/stations/:id/invoke

Trigger a manual heartbeat/think pass for this station.

**Response:**

```json
{ "station_id": "01JQXK7M3N...", "invoked_at": "2026-03-27T09:30:00.000Z" }
```

**SSE:** `activity.new` with action `station.invoked`.

---

### 3.4 Tasks

#### GET /api/tasks

List tasks, filterable.

**Query params:** `?station_id=...&status=open,in_progress&project_id=audit-board&offset=0&limit=50`

**Response:**

```json
{
  "items": [
    {
      "id": "01JQXK8P4Q...",
      "title": "Draft Q1 QBR slides",
      "status": "in_progress",
      "priority": 2,
      "station_id": "01JQXK7M3N...",
      "station_name": "audit-board-drafter",
      "project_id": "audit-board",
      "checked_out_by": "01JQXK7M3N...",
      "checked_out_at": "2026-03-27T09:16:00.000Z",
      "created_at": "2026-03-27T09:10:00.000Z",
      "completed_at": null
    }
  ],
  "total": 23,
  "offset": 0,
  "limit": 50
}
```

**SSE:** `task.update` on any status change.

---

#### POST /api/tasks

Create a new task.

**Request:**

```json
{
  "title": "Review and approve March voice memo drafts",
  "description": "5 drafts are pending for audit-board. Review each, approve or reject.",
  "priority": 2,
  "project_id": "audit-board",
  "station_id": null
}
```

**Response:** `201 Created` with the full task object.

**SSE:** `task.update` with action `task.created`.

---

#### GET /api/tasks/:id

Task detail with documents and comments.

**Response:**

```json
{
  "id": "01JQXK8P4Q...",
  "title": "Draft Q1 QBR slides",
  "description": "Synthesize 3 voice memos from March into QBR talking points",
  "status": "in_progress",
  "priority": 2,
  "station_id": "01JQXK7M3N...",
  "station_name": "audit-board-drafter",
  "project_id": "audit-board",
  "checked_out_by": "01JQXK7M3N...",
  "checked_out_at": "2026-03-27T09:16:00.000Z",
  "documents": [
    { "id": "...", "key": "plan", "revision": 2, "updated_at": "..." },
    { "id": "...", "key": "draft", "revision": 1, "updated_at": "..." }
  ],
  "comments": [
    { "id": "...", "author": "user", "body": "Focus on Q1 staffing wins", "created_at": "..." }
  ],
  "created_at": "2026-03-27T09:10:00.000Z",
  "completed_at": null
}
```

---

#### PATCH /api/tasks/:id

Update task fields.

**Request:**

```json
{
  "status": "review",
  "priority": 1
}
```

**Response:** `200 OK` with updated task object.

**SSE:** `task.update`.

---

#### POST /api/tasks/:id/checkout

Atomic checkout — assigns the task to a station. Returns `409 Conflict` if already checked out by a different station.

**Request:**

```json
{
  "station_id": "01JQXK7M3N..."
}
```

**Response (success, 200):**

```json
{
  "task_id": "01JQXK8P4Q...",
  "checked_out_by": "01JQXK7M3N...",
  "checked_out_at": "2026-03-27T09:16:00.000Z",
  "status": "checked_out"
}
```

**Response (conflict, 409):**

```json
{
  "error": "already_checked_out",
  "detail": "Task is checked out by station 01JQXL9R2T... since 2026-03-27T09:10:00Z"
}
```

**Implementation:**

```sql
-- Atomic checkout using UPDATE ... WHERE
UPDATE tasks
SET checked_out_by = :station_id,
    checked_out_at = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
    status = 'checked_out'
WHERE id = :task_id
  AND (checked_out_by IS NULL OR checked_out_by = :station_id);
-- Check rows_affected == 1; if 0, return 409
```

**SSE:** `task.update` with action `task.checked_out`.

---

#### POST /api/tasks/:id/release

Release the checkout lock, returning the task to `open`.

**Request:**

```json
{
  "station_id": "01JQXK7M3N..."
}
```

**Response:**

```json
{
  "task_id": "01JQXK8P4Q...",
  "checked_out_by": null,
  "status": "open"
}
```

**SSE:** `task.update` with action `task.released`.

---

#### GET /api/tasks/:id/documents

List all documents for a task.

**Response:**

```json
[
  {
    "id": "01JQXM...",
    "task_id": "01JQXK8P4Q...",
    "key": "plan",
    "body": "## Plan\n1. Read voice memos c-111, c-222, c-333\n2. Extract key themes...",
    "revision": 2,
    "created_at": "2026-03-27T09:16:00.000Z",
    "updated_at": "2026-03-27T09:22:00.000Z"
  }
]
```

---

#### POST /api/tasks/:id/documents

Create or update a document (upsert on `task_id + key`). Increments revision on update.

**Request:**

```json
{
  "key": "draft",
  "body": "## Q1 QBR Talking Points\n\n### Staffing Wins\n- Onboarded 2 new analysts..."
}
```

**Response:** `201 Created` (new) or `200 OK` (updated) with the document object.

**SSE:** `task.update` with action `task.document_updated`.

---

#### GET /api/tasks/:id/comments

List comments on a task, ordered by created_at ascending.

**Response:**

```json
[
  {
    "id": "01JQXN...",
    "task_id": "01JQXK8P4Q...",
    "author": "user",
    "body": "Focus on Q1 staffing wins and cost savings",
    "created_at": "2026-03-27T09:12:00.000Z"
  }
]
```

---

#### POST /api/tasks/:id/comments

Add a comment.

**Request:**

```json
{
  "author": "user",
  "body": "Looks good, but add the budget numbers from the email thread"
}
```

**Response:** `201 Created` with the comment object.

**SSE:** `task.update` with action `task.comment_added`.

---

### 3.5 Decisions

Decisions are composed from multiple sources: `queue.json` items, hub.db drafts (status=pending), hub.db unsorted content, hub.db action items needing triage, and system health alerts from `sync_state`.

#### GET /api/decisions

List all pending decisions.

**Query params:** `?type=draft,unsorted,action_item,health`

**Response:**

```json
{
  "items": [
    {
      "id": "draft-abc123",
      "type": "draft",
      "title": "Approve Confluence draft: AuditBoard Q1 status update",
      "summary": "3 bullet points synthesized from voice memo on 2026-03-25",
      "project_id": "audit-board",
      "urgency": "medium",
      "source": {
        "table": "drafts",
        "id": "abc123",
        "target_template": "project-status",
        "target_section": "Q1 Update"
      },
      "created_at": "2026-03-26T10:00:00.000Z"
    },
    {
      "id": "unsorted-def456",
      "type": "unsorted",
      "title": "Classify: Voice memo — mentions Aravo and 3PI",
      "summary": "5-minute voice memo discussing vendor pricing changes",
      "project_id": null,
      "urgency": "low",
      "source": {
        "table": "content",
        "id": "def456"
      },
      "created_at": "2026-03-27T08:30:00.000Z"
    },
    {
      "id": "queue-ghi789",
      "type": "queue",
      "title": "Approve Jira ticket creation: Follow up with EY",
      "summary": "Auto-generated from action item todo-001",
      "project_id": "audit-board-tax",
      "urgency": "high",
      "source": {
        "file": "queue.json",
        "index": 0
      },
      "created_at": "2026-03-27T07:00:00.000Z"
    }
  ],
  "total": 4,
  "deferred": 2,
  "auto_handled_today": 11
}
```

**SSE:** `decision.new` when a new decision is queued.

---

#### POST /api/decisions/:id/approve

Approve a pending decision. Action depends on type:
- `draft` -> calls KH `approve_draft` (sets status to `approved`)
- `unsorted` -> triggers classification pipeline
- `queue` -> executes the queued action (e.g., create Jira ticket)

**Request:**

```json
{
  "notes": "Approved with minor edits"
}
```

**Response:**

```json
{
  "id": "draft-abc123",
  "status": "approved",
  "action_taken": "Draft approved and marked for Confluence push",
  "approved_at": "2026-03-27T09:30:00.000Z"
}
```

**SSE:** `decision.resolved`, `activity.new`.

---

#### POST /api/decisions/:id/reject

Reject a decision.

**Request:**

```json
{
  "reason": "Draft is missing budget numbers, regenerate with cost data included"
}
```

**Response:**

```json
{
  "id": "draft-abc123",
  "status": "rejected",
  "reason": "Draft is missing budget numbers...",
  "rejected_at": "2026-03-27T09:30:00.000Z"
}
```

**SSE:** `decision.resolved`, `activity.new`.

---

#### POST /api/decisions/:id/defer

Defer a decision to resurface later (per config.json `deferred_resurface` rules: next_session -> 24h -> flag_as_stale).

**Request:**

```json
{
  "resurface": "next_session"
}
```

**Response:**

```json
{
  "id": "draft-abc123",
  "status": "deferred",
  "resurface_at": "next_session"
}
```

**SSE:** `activity.new` with action `decision.deferred`.

---

#### POST /api/decisions/:id/classify

Assign an unsorted content item to a project.

**Request:**

```json
{
  "project_id": "optimize",
  "confidence_override": 1.0,
  "learn_rule": true
}
```

**Response:**

```json
{
  "id": "unsorted-def456",
  "status": "classified",
  "project_id": "optimize",
  "rule_learned": {
    "id": "lr-new-001",
    "rule_type": "keyword",
    "rule_value": "aravo",
    "project_id": "optimize"
  }
}
```

**SSE:** `decision.resolved`, `content.classified`.

---

### 3.6 Knowledge

Read-only access to hub.db content with FTS5 search.

#### GET /api/knowledge/search

Full-text search across all content.

**Query params:** `?q=aravo+vendor+pricing&project_id=optimize&source=email&limit=20`

**Response:**

```json
{
  "items": [
    {
      "id": "c-xyz789",
      "source": "email",
      "title": "RE: Aravo Pricing Update Q1",
      "snippet": "...the <b>Aravo</b> <b>vendor</b> <b>pricing</b> has been updated to reflect...",
      "relevance_score": 0.94,
      "project_id": "optimize",
      "created_at": "2026-03-20T11:00:00.000Z"
    }
  ],
  "total": 7,
  "query": "aravo vendor pricing"
}
```

**Implementation:**

```sql
SELECT c.id, c.source, c.title,
       snippet(content_fts, 2, '<b>', '</b>', '...', 32) AS snippet,
       c.relevance_score, pc.project_id, c.created_at
FROM content_fts
JOIN content c ON c.rowid = content_fts.rowid
LEFT JOIN project_content pc ON pc.content_id = c.id
WHERE content_fts MATCH :query
ORDER BY rank
LIMIT :limit OFFSET :offset;
```

**SSE:** None.

---

#### GET /api/knowledge/content/:id

Single content item with full text, metadata, entities, and project classification.

**Response:**

```json
{
  "id": "c-xyz789",
  "source": "email",
  "source_id": "msg-abc",
  "source_path": null,
  "content_type": "email",
  "title": "RE: Aravo Pricing Update Q1",
  "raw_text": "Hi Rijul, the Aravo vendor pricing has been...",
  "processed_text": "Summary: Aravo pricing updated for Q1...",
  "metadata": { "from": "john_doe@mckinsey.com", "to": "rijul_kalra@mckinsey.com", "date": "2026-03-20" },
  "status": "complete",
  "relevance_score": 0.94,
  "project": { "id": "optimize", "name": "Optimize", "confidence": 0.92 },
  "entities": [
    { "id": "e-001", "name": "Aravo", "entity_type": "topic" },
    { "id": "e-002", "name": "John Doe", "entity_type": "person" }
  ],
  "created_at": "2026-03-20T11:00:00.000Z"
}
```

---

#### GET /api/knowledge/unsorted

Content items that have not been classified to a project.

**Query params:** `?offset=0&limit=50`

**Response:**

```json
{
  "items": [
    {
      "id": "c-unclass01",
      "source": "voice",
      "title": "Voice memo — unclear topic",
      "snippet": "Quick note about the thing we discussed...",
      "created_at": "2026-03-27T08:30:00.000Z"
    }
  ],
  "total": 12
}
```

**Implementation:**

```sql
SELECT c.* FROM content c
LEFT JOIN project_content pc ON pc.content_id = c.id
WHERE pc.content_id IS NULL
  AND c.status NOT IN ('failed')
ORDER BY c.created_at DESC
LIMIT :limit OFFSET :offset;
```

---

### 3.7 People

CRUD on `~/.coco/brain.json` people graph.

#### GET /api/people

List all people from brain.json.

**Response:**

```json
[
  {
    "key": "rijul",
    "full_name": "Rijul Kalra",
    "role": "self",
    "priority": "high",
    "projects": ["audit-board", "audit-board-tax", "acc", "reg-coe", "optimize", "tcre"],
    "patterns": {
      "email_from": ["rijul_kalra@mckinsey.com"],
      "frequency": "daily",
      "transcription_aliases": ["Vishal", "Rizzul", "Rizul", "Reduel", "Regal"]
    },
    "learned_at": "2026-03-23",
    "source": "taught"
  }
]
```

---

#### POST /api/people

Add a person to brain.json.

**Request:**

```json
{
  "key": "sarah_j",
  "full_name": "Sarah Johnson",
  "role": "AP on AuditBoard",
  "priority": "high",
  "projects": ["audit-board"],
  "patterns": {
    "email_from": ["sarah_johnson@mckinsey.com"],
    "frequency": "weekly",
    "transcription_aliases": ["Sarah", "Sara"]
  }
}
```

**Response:** `201 Created` with the person object.

**SSE:** `activity.new` with action `people.added`.

---

#### PATCH /api/people/:key

Update a person's fields. Merges with existing data.

**Request:**

```json
{
  "projects": ["audit-board", "audit-board-tax"],
  "priority": "medium"
}
```

**Response:** `200 OK` with updated person object.

---

#### DELETE /api/people/:key

Remove a person and cascade-remove any attention_rules that reference them.

**Response:** `204 No Content`.

**SSE:** `activity.new` with action `people.removed`.

---

#### GET /api/people/:key/activity

Search hub.db for content items related to this person (by entity match or email pattern).

**Query params:** `?days=30&limit=20`

**Response:**

```json
{
  "person": "sarah_j",
  "items": [
    {
      "id": "c-mail001",
      "source": "email",
      "title": "RE: AuditBoard go-live timeline",
      "project_id": "audit-board",
      "created_at": "2026-03-25T10:00:00.000Z"
    }
  ],
  "total": 8
}
```

---

### 3.8 Costs

#### GET /api/costs/summary

Aggregated cost data from both cost_events (platform.db) and api_costs (hub.db).

**Query params:** `?days=30`

**Response:**

```json
{
  "period_days": 30,
  "total_usd": 34.56,
  "by_source": {
    "kh_pipeline": 22.10,
    "station": 8.90,
    "chat": 3.56
  },
  "by_model": {
    "claude-haiku-3.5": 3.20,
    "claude-sonnet-4": 28.10,
    "claude-opus-4": 3.26
  },
  "by_day": [
    { "date": "2026-03-27", "cost_usd": 1.23 },
    { "date": "2026-03-26", "cost_usd": 2.45 }
  ],
  "budget": {
    "total_monthly_limit_usd": 100.0,
    "pct_used": 0.346
  }
}
```

**SSE:** `cost.alert` when thresholds are crossed.

---

#### GET /api/costs/by-station

Cost grouped by station.

**Query params:** `?days=30`

**Response:**

```json
[
  {
    "station_id": "01JQXK7M3N...",
    "station_name": "audit-board-drafter",
    "total_usd": 5.67,
    "input_tokens": 245000,
    "output_tokens": 32000,
    "event_count": 47
  }
]
```

---

#### GET /api/costs/by-project

Cost grouped by project (joins cost_events by station's project + api_costs by content's project).

**Query params:** `?days=30`

**Response:**

```json
[
  {
    "project_id": "audit-board",
    "project_name": "AuditBoard",
    "total_usd": 8.90,
    "station_cost_usd": 5.67,
    "pipeline_cost_usd": 3.23
  }
]
```

---

#### GET /api/costs/events

Raw cost events, paginated.

**Query params:** `?station_id=...&offset=0&limit=100`

**Response:**

```json
{
  "items": [
    {
      "id": "01JQXP...",
      "station_id": "01JQXK7M3N...",
      "task_id": "01JQXK8P4Q...",
      "model": "claude-sonnet-4-20250514",
      "input_tokens": 12500,
      "output_tokens": 1800,
      "cost_usd": 0.087,
      "created_at": "2026-03-27T09:20:00.000Z"
    }
  ],
  "total": 234,
  "offset": 0,
  "limit": 100
}
```

---

#### GET /api/budgets/:project_id

Get budget for a project.

**Response:**

```json
{
  "project_id": "audit-board",
  "monthly_limit_usd": 20.0,
  "alert_threshold": 0.8,
  "current_month_usd": 8.90,
  "pct_used": 0.445
}
```

---

#### PUT /api/budgets/:project_id

Set or update budget.

**Request:**

```json
{
  "monthly_limit_usd": 25.0,
  "alert_threshold": 0.75
}
```

**Response:** `200 OK` with the budget object (includes `current_month_usd` and `pct_used`).

**SSE:** `activity.new` with action `budget.updated`.

---

### 3.9 Todos

#### GET /api/todos

List todos from hub.db.

**Query params:** `?status=open&project_id=audit-board&priority=high&offset=0&limit=50`

**Response:**

```json
{
  "items": [
    {
      "id": "todo-001",
      "title": "Follow up with EY on TCF timeline",
      "description": "Discussed in March 25 voice memo. EY expects response by EOW.",
      "project_id": "audit-board-tax",
      "owner": "rijul",
      "due_date": "2026-03-30",
      "priority": "high",
      "status": "open",
      "source_type": "voice",
      "source_content_id": "c-voice-025",
      "jira_key": null,
      "created_at": "2026-03-25T14:30:00.000Z",
      "tags": "ey,tcf,follow-up"
    }
  ],
  "total": 8,
  "offset": 0,
  "limit": 50
}
```

---

#### POST /api/todos

Create a new todo (writes to hub.db via KH adapter).

**Request:**

```json
{
  "title": "Prepare Optimize vendor comparison doc",
  "description": "Compare Aravo vs ODaaS pricing for Q2 review",
  "project_id": "optimize",
  "priority": "medium",
  "due_date": "2026-04-05",
  "tags": "aravo,odaas,vendor"
}
```

**Response:** `201 Created` with the full todo object.

**SSE:** `activity.new` with action `todo.created`.

---

#### PATCH /api/todos/:id

Update a todo (mark done, dismiss, edit fields).

**Request:**

```json
{
  "status": "done",
  "completed_at": "2026-03-27T10:00:00.000Z"
}
```

**Response:** `200 OK` with updated todo object.

**SSE:** `activity.new` with action `todo.updated`.

---

#### POST /api/todos/:id/jira

Promote a todo to a Jira ticket via KH's `create_jira_ticket` tool.

**Request:**

```json
{
  "jira_project": "AB",
  "issue_type": "Task",
  "additional_labels": ["q1-follow-up"]
}
```

**Response:**

```json
{
  "todo_id": "todo-001",
  "jira_key": "AB-1234",
  "jira_url": "https://mckinsey.atlassian.net/browse/AB-1234",
  "status": "jira-created"
}
```

**SSE:** `activity.new` with action `todo.promoted_to_jira`.

---

#### POST /api/todos/sync

Trigger KH action item sync (extracts action items from recent content).

**Response:**

```json
{
  "synced": true,
  "new_items": 3,
  "updated_items": 1
}
```

---

### 3.10 Chat

#### POST /api/chat

Send a message to CoCo web chat. Returns an SSE stream of the Claude response.

**Request:**

```json
{
  "message": "What happened on the AuditBoard project this week?",
  "context": {
    "focused_project": "audit-board"
  }
}
```

**Response:** `Content-Type: text/event-stream`

```
event: chat.token
data: {"token": "This", "index": 0}

event: chat.token
data: {"token": " week", "index": 1}

event: chat.token
data: {"token": " on", "index": 2}

...

event: chat.done
data: {"message_id": "01JQXR...", "model": "claude-sonnet-4-20250514", "input_tokens": 4200, "output_tokens": 890, "cost_usd": 0.042}
```

Both the user message and assistant response are persisted to `chat_messages`.

**SSE (global):** `chat.response` with the completed message.

---

#### GET /api/chat/history

Paginated chat history.

**Query params:** `?offset=0&limit=50`

**Response:**

```json
{
  "items": [
    {
      "id": "01JQXR01...",
      "role": "user",
      "content": "What happened on the AuditBoard project this week?",
      "metadata": {},
      "created_at": "2026-03-27T09:30:00.000Z"
    },
    {
      "id": "01JQXR02...",
      "role": "assistant",
      "content": "This week on AuditBoard, 3 new voice memos were processed...",
      "metadata": {
        "model": "claude-sonnet-4-20250514",
        "input_tokens": 4200,
        "output_tokens": 890,
        "cost_usd": 0.042
      },
      "created_at": "2026-03-27T09:30:05.000Z"
    }
  ],
  "total": 128,
  "offset": 0,
  "limit": 50
}
```

---

### 3.11 Activity

#### GET /api/activity

Filterable activity log from platform.db.

**Query params:** `?station_id=...&project_id=...&action=station.spawned,task.checked_out&since=2026-03-26T00:00:00Z&until=2026-03-27T23:59:59Z&offset=0&limit=100`

**Response:**

```json
{
  "items": [
    {
      "id": "01JQXL...",
      "station_id": "01JQXK7M3N...",
      "station_name": "audit-board-drafter",
      "task_id": "01JQXK8P4Q...",
      "action": "task.checked_out",
      "detail": {
        "task_title": "Draft Q1 QBR slides",
        "previous_status": "open"
      },
      "created_at": "2026-03-27T09:16:00.000Z"
    }
  ],
  "total": 456,
  "offset": 0,
  "limit": 100
}
```

**SSE:** Every activity_log insert also emits `activity.new`.

---

### 3.12 Settings

#### GET /api/settings

Combined settings from config.json and platform preferences.

**Response:**

```json
{
  "autonomy": {
    "launch_ui": "adaptive",
    "morning_cutoff_hour": 10,
    "quick_reopen_minutes": 30,
    "auto_handle": {
      "classify_above_confidence": 0.85,
      "dismiss_noise_from_unknown": true,
      "file_fyi_silently": true,
      "draft_generation": true
    },
    "never_auto_handle": ["external_comms", "jira_ticket_creation", "confluence_updates", "replies"],
    "yolo": {
      "auto_approve_above": 0.85,
      "skip_and_queue_below": 0.70,
      "always_ask": ["external_comms", "git_push", "delete"],
      "max_jira_tickets_per_session": 10,
      "max_draft_approvals_per_session": 20
    }
  },
  "display": {
    "max_projects_shown": 6,
    "collapse_quiet_projects": true,
    "show_cost": true,
    "emoji": true
  },
  "deferred_resurface": {
    "first": "next_session",
    "second": "24h",
    "third": "flag_as_stale"
  },
  "classification_hints": {
    "voice_memo_rules": [
      "Staffing, capacity, team allocation, OKR, QBR -> tcre",
      "Tax governance, TCF, AB2, Optro, EY contract -> audit-board-tax",
      "3PI, TPI, Aravo, ODaaS, TP inventory -> optimize"
    ]
  }
}
```

---

#### PUT /api/settings

Update settings. Writes atomically to config.json (see Integration Notes).

**Request:**

```json
{
  "autonomy": {
    "auto_handle": {
      "classify_above_confidence": 0.90
    }
  },
  "display": {
    "emoji": false
  }
}
```

**Response:** `200 OK` with the full merged settings object.

**SSE:** `activity.new` with action `settings.updated`.

---

### 3.13 Health

#### GET /api/health

System health check.

**Response:**

```json
{
  "status": "healthy",
  "checks": {
    "hub_db": {
      "status": "ok",
      "path": "~/.hub/hub.db",
      "size_mb": 42.3,
      "content_count": 1423,
      "journal_mode": "wal"
    },
    "platform_db": {
      "status": "ok",
      "path": "~/.coco/platform.db",
      "size_mb": 1.2,
      "journal_mode": "wal"
    },
    "brain_json": {
      "status": "ok",
      "path": "~/.coco/brain.json",
      "people_count": 1,
      "rules_count": 3
    },
    "queue_json": {
      "status": "ok",
      "path": "~/.coco/queue.json",
      "pending_count": 0,
      "deferred_count": 0
    },
    "adapters": {
      "email": { "status": "ok", "last_sync": "2026-03-27T08:00:00Z", "items_synced": 890 },
      "voice": { "status": "ok", "last_sync": "2026-03-27T07:30:00Z", "items_synced": 312 },
      "jira":  { "status": "warning", "last_sync": "2026-03-26T18:00:00Z", "error": "Rate limited" },
      "confluence": { "status": "ok", "last_sync": "2026-03-27T06:00:00Z", "items_synced": 65 }
    },
    "stations": {
      "running": 2,
      "pids_alive": [48721, 48790],
      "pids_stale": []
    },
    "think_pass": {
      "last_run": "2026-03-27T09:00:00Z",
      "next_run": "2026-03-27T09:15:00Z",
      "launchd_loaded": true
    }
  },
  "uptime_seconds": 3621,
  "version": "0.1.0"
}
```

---

### 3.14 SSE

#### GET /api/events

Global SSE stream. The client opens a single `EventSource` connection here and receives all event types.

**Query params:** `?types=station.status,task.update,cost.alert` (optional filter; default: all types)

**Response:** `Content-Type: text/event-stream`

See Section 4 for event schemas.

---

## 4. SSE Event Types

All events follow this envelope:

```
event: <event_type>
data: {"ts": "2026-03-27T09:16:00.000Z", "payload": { ... }}
id: <monotonic_counter>
```

The `id` field enables `Last-Event-ID` reconnection.

| Event Name | Payload | When It Fires |
|---|---|---|
| `station.status` | `{ "station_id": "...", "name": "...", "old_status": "idle", "new_status": "running", "pid": 48721 }` | Station status changes (spawn, pause, resume, kill, fail) |
| `task.update` | `{ "task_id": "...", "title": "...", "action": "task.created\|task.checked_out\|task.released\|task.status_changed\|task.document_updated\|task.comment_added", "status": "in_progress", "station_id": "..." }` | Any task mutation |
| `decision.new` | `{ "decision_id": "...", "type": "draft\|unsorted\|queue\|health", "title": "...", "urgency": "high", "project_id": "..." }` | New item enters the decision queue (draft generated, content unsorted, queue.json updated, health alert) |
| `decision.resolved` | `{ "decision_id": "...", "resolution": "approved\|rejected\|deferred\|classified", "resolved_by": "user\|auto" }` | Decision approved, rejected, deferred, or auto-handled |
| `cost.alert` | `{ "project_id": "...", "project_name": "...", "monthly_limit_usd": 20.0, "current_usd": 16.50, "pct_used": 0.825, "threshold": 0.8 }` | Project spend crosses the budget alert_threshold |
| `activity.new` | `{ "id": "...", "station_id": "...", "task_id": "...", "action": "...", "detail": { ... } }` | Any row inserted into activity_log |
| `chat.response` | `{ "message_id": "...", "content": "...", "model": "...", "cost_usd": 0.042 }` | Chat response completed (full message, not streaming tokens) |
| `content.classified` | `{ "content_id": "...", "project_id": "...", "confidence": 0.92, "method": "learned_rule" }` | Content classified to a project (from KH pipeline or manual classification) |

### SSE Server Implementation

```python
from sse_starlette.sse import EventSourceResponse
import asyncio

# Global broadcast queue — each SSE client gets a clone
class EventBus:
    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=256)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.remove(q)

    async def publish(self, event_type: str, payload: dict):
        for q in self._subscribers:
            try:
                q.put_nowait({"event": event_type, "data": payload})
            except asyncio.QueueFull:
                pass  # slow client, drop oldest

event_bus = EventBus()

@app.get("/api/events")
async def sse_events(request: Request, types: str | None = None):
    type_filter = set(types.split(",")) if types else None
    q = event_bus.subscribe()

    async def generator():
        try:
            while True:
                msg = await q.get()
                if type_filter and msg["event"] not in type_filter:
                    continue
                yield msg
        except asyncio.CancelledError:
            event_bus.unsubscribe(q)

    return EventSourceResponse(generator())
```

---

## 5. Integration Notes

### 5.1 Reading hub.db Safely

hub.db is owned by the Knowledge Hub MCP server and its adapters. The platform opens it read-only to avoid write contention.

**Connection:**

```python
hub_conn = sqlite3.connect(
    "file:/Users/Rijul_Kalra/.hub/hub.db?mode=ro",
    uri=True,
    check_same_thread=False,
)
hub_conn.execute("PRAGMA busy_timeout = 5000")
```

**Handling SQLITE_BUSY:** Even read-only connections can encounter BUSY when the writer is checkpointing WAL. The `busy_timeout = 5000` pragma makes SQLite retry for up to 5 seconds before raising. In the application layer, wrap queries:

```python
import sqlite3
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.1, max=2),
    retry=lambda e: isinstance(e, sqlite3.OperationalError) and "locked" in str(e),
)
def query_hub(sql: str, params: tuple = ()):
    with hub_conn:
        return hub_conn.execute(sql, params).fetchall()
```

**FTS5 queries:** Use `content_fts MATCH` syntax. Always `JOIN content` to get full row data. The FTS index is maintained by triggers on the content table (already set up by KH).

**Cross-DB references:** To join hub.db and platform.db data (e.g., station cost + project name), query each DB separately and join in Python. Do not use `ATTACH DATABASE` as it would require write access on hub.db's WAL.

---

### 5.2 Writing brain.json and queue.json Atomically

These JSON files are shared between the CLI (CoCo), think.py (launchd), and the platform server. All writes must use the atomic tmp+rename pattern to prevent corruption from concurrent access.

```python
import json
import os
import tempfile
from pathlib import Path

def atomic_json_write(path: Path, data: dict) -> None:
    """Write JSON atomically using tmp file + os.replace().

    os.replace() is atomic on POSIX (same filesystem).
    The tempfile is created in the same directory to guarantee same-fs.
    """
    dir_ = path.parent
    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=dir_,
        suffix=".tmp",
        delete=False,
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name

    os.replace(tmp_path, path)


def atomic_json_read(path: Path) -> dict:
    """Read JSON file. Returns empty dict if missing or corrupt."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
```

**brain.json update pattern** (read-modify-write):

```python
BRAIN_PATH = Path.home() / ".coco" / "brain.json"

def add_person(key: str, person: dict) -> dict:
    brain = atomic_json_read(BRAIN_PATH)
    brain.setdefault("people", {})[key] = person
    atomic_json_write(BRAIN_PATH, brain)
    return person

def remove_person(key: str) -> None:
    brain = atomic_json_read(BRAIN_PATH)
    brain.get("people", {}).pop(key, None)
    # Cascade: remove attention_rules referencing this person
    rules = brain.get("attention_rules", [])
    brain["attention_rules"] = [
        r for r in rules
        if not _rule_references_person(r, key)
    ]
    atomic_json_write(BRAIN_PATH, brain)
```

**queue.json decision handling:**

```python
QUEUE_PATH = Path.home() / ".coco" / "queue.json"

def approve_queue_item(index: int) -> dict:
    queue = atomic_json_read(QUEUE_PATH)
    items = queue.get("items", [])
    if index >= len(items):
        raise IndexError("Queue item not found")
    item = items.pop(index)
    queue["auto_handled_since_last_session"].append({
        **item,
        "resolution": "approved",
        "resolved_at": datetime.utcnow().isoformat() + "Z",
    })
    atomic_json_write(QUEUE_PATH, queue)
    return item
```

---

### 5.3 Calling Claude API for Chat

The `/api/chat` endpoint calls the Anthropic Messages API with a CoCo-specific system prompt, then streams tokens back as SSE.

```python
import anthropic
from sse_starlette.sse import EventSourceResponse

client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

COCO_SYSTEM_PROMPT = """You are CoCo, Rijul's PM autopilot assistant.
You have access to his Knowledge Hub data, project context, and people graph.
Answer questions about projects, summarize recent activity, help draft content,
and suggest next actions. Be concise and structured."""

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Persist user message
    user_msg_id = ulid.new().str
    platform_db.execute(
        "INSERT INTO chat_messages (id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_msg_id, "user", request.message, "{}", now_iso()),
    )

    # Build context from KH
    context = await build_chat_context(request.context)

    async def generate():
        full_response = []
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=COCO_SYSTEM_PROMPT + "\n\n" + context,
            messages=[
                # Load last N messages from chat_messages for conversation continuity
                *load_recent_messages(limit=20),
                {"role": "user", "content": request.message},
            ],
        ) as stream:
            for text in stream.text_stream:
                full_response.append(text)
                yield {
                    "event": "chat.token",
                    "data": json.dumps({"token": text}),
                }

            # Finalize
            message = stream.get_final_message()
            usage = message.usage
            cost = calculate_cost(message.model, usage.input_tokens, usage.output_tokens)

            # Persist assistant message
            asst_msg_id = ulid.new().str
            metadata = {
                "model": message.model,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cost_usd": cost,
            }
            platform_db.execute(
                "INSERT INTO chat_messages (id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                (asst_msg_id, "assistant", "".join(full_response), json.dumps(metadata), now_iso()),
            )

            # Log cost event
            platform_db.execute(
                "INSERT INTO cost_events (id, model, input_tokens, output_tokens, cost_usd, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (ulid.new().str, message.model, usage.input_tokens, usage.output_tokens, cost, now_iso()),
            )

            yield {
                "event": "chat.done",
                "data": json.dumps({
                    "message_id": asst_msg_id,
                    "model": message.model,
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cost_usd": cost,
                }),
            }

            # Broadcast to global SSE
            await event_bus.publish("chat.response", {
                "message_id": asst_msg_id,
                "content": "".join(full_response),
                "model": message.model,
                "cost_usd": cost,
            })

    return EventSourceResponse(generate())
```

---

### 5.4 Spawning Claude Code CLI Processes

Stations are background `claude` CLI processes managed via `subprocess.Popen` and monitored with `psutil`.

```python
import subprocess
import psutil
import signal
from pathlib import Path

CLAUDE_BIN = "/usr/local/bin/claude"  # or detect via `which claude`

def spawn_station(station: dict, task: dict | None = None) -> int:
    """Spawn a Claude Code CLI process for a station.

    Returns the OS PID.
    """
    config = json.loads(station["config"] or "{}")
    working_dir = config.get("working_directory", str(Path.home()))

    # Build the prompt from station role + task description
    prompt_parts = [f"You are station '{station['name']}'. Role: {station['role']}."]
    if task:
        prompt_parts.append(f"Current task: {task['title']}")
        if task.get("description"):
            prompt_parts.append(task["description"])

    prompt = "\n".join(prompt_parts)

    # Spawn claude CLI in print mode (non-interactive)
    proc = subprocess.Popen(
        [
            CLAUDE_BIN,
            "--print",              # non-interactive, output only
            "--model", station["model"],
            "--max-turns", str(config.get("max_turns", 25)),
            "--prompt", prompt,
        ],
        cwd=working_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # Detach from parent process group so signals don't cascade
        preexec_fn=os.setpgrp,
    )

    return proc.pid


def pause_station(pid: int) -> None:
    """Send SIGSTOP to pause a station process."""
    os.kill(pid, signal.SIGSTOP)


def resume_station(pid: int) -> None:
    """Send SIGCONT to resume a paused station."""
    os.kill(pid, signal.SIGCONT)


def kill_station(pid: int, timeout: int = 5) -> None:
    """Send SIGTERM, wait, then SIGKILL if needed."""
    try:
        proc = psutil.Process(pid)
        proc.terminate()  # SIGTERM
        proc.wait(timeout=timeout)
    except psutil.TimeoutExpired:
        proc.kill()  # SIGKILL
    except psutil.NoSuchProcess:
        pass  # already dead


def get_station_health(pid: int) -> dict | None:
    """Get CPU, memory, and status for a station process."""
    try:
        proc = psutil.Process(pid)
        return {
            "pid": pid,
            "status": proc.status(),          # running, sleeping, stopped, zombie
            "cpu_percent": proc.cpu_percent(),
            "memory_mb": proc.memory_info().rss / (1024 * 1024),
            "create_time": proc.create_time(),
        }
    except psutil.NoSuchProcess:
        return None
```

**Station output streaming:** A background asyncio task reads stdout/stderr from the subprocess pipe and both persists chunks to the `station_output` table (if needed for replay) and broadcasts them to SSE subscribers on `/api/stations/:id/logs`.

```python
async def stream_station_output(station_id: str, proc: subprocess.Popen):
    """Background task that reads station output and broadcasts via SSE."""
    loop = asyncio.get_event_loop()

    async def read_stream(stream, stream_name):
        while True:
            line = await loop.run_in_executor(None, stream.readline)
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip()
            await event_bus.publish(f"station.output.{station_id}", {
                "station_id": station_id,
                "stream": stream_name,
                "line": text,
                "ts": now_iso(),
            })

    await asyncio.gather(
        read_stream(proc.stdout, "stdout"),
        read_stream(proc.stderr, "stderr"),
    )

    # Process exited — update station status
    exit_code = proc.wait()
    new_status = "failed" if exit_code != 0 else "idle"
    platform_db.execute(
        "UPDATE stations SET status = ?, pid = NULL, updated_at = ? WHERE id = ?",
        (new_status, now_iso(), station_id),
    )
    await event_bus.publish("station.status", {
        "station_id": station_id,
        "old_status": "running",
        "new_status": new_status,
        "exit_code": exit_code,
    })
```

### 5.5 ULID Generation

All primary keys in platform.db use ULIDs (Universally Unique Lexicographically Sortable Identifiers). They are time-ordered, so `ORDER BY id` is equivalent to `ORDER BY created_at` and index scans are efficient.

```python
import ulid

def new_id() -> str:
    return ulid.new().str  # e.g. "01JQXK7M3NFVB0YPTG2E5A"
```

### 5.6 Alembic Migration Example

```python
# alembic/versions/001_initial_schema.py
"""Initial platform.db schema."""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None

def upgrade():
    op.execute("PRAGMA journal_mode = WAL")
    op.execute("PRAGMA foreign_keys = ON")

    op.create_table(
        "stations",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("role", sa.Text),
        sa.Column("model", sa.Text, nullable=False, server_default="sonnet"),
        sa.Column("status", sa.Text, nullable=False, server_default="idle"),
        sa.Column("config", sa.Text, server_default="{}"),
        sa.Column("pid", sa.Integer),
        sa.Column("created_at", sa.Text, nullable=False),
        sa.Column("updated_at", sa.Text, nullable=False),
        sa.CheckConstraint("status IN ('idle','running','paused','failed','killed')"),
    )
    # ... remaining tables follow the same pattern from Section 2

def downgrade():
    op.drop_table("chat_messages")
    op.drop_table("station_routines")
    op.drop_table("budgets")
    op.drop_table("activity_log")
    op.drop_table("trust_matrix")
    op.drop_table("resource_locks")
    op.drop_table("cost_events")
    op.drop_table("task_comments")
    op.drop_table("task_documents")
    op.drop_table("tasks")
    op.drop_table("stations")
```
