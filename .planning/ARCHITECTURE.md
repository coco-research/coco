# CoCo Platform — Architecture Document

**Version:** 1.0
**Date:** 2026-03-25
**Author:** Rijul Kalra / Claude Opus 4.6
**Status:** Draft — awaiting review

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Tech Stack Decision](#2-tech-stack-decision)
3. [Component Architecture](#3-component-architecture)
4. [Integration Architecture](#4-integration-architecture)
5. [Data Flow](#5-data-flow)
6. [Station Management](#6-station-management)
7. [Security Model](#7-security-model)
8. [Deployment Model](#8-deployment-model)
9. [Key Technical Risks](#9-key-technical-risks)

---

## 1. System Overview

### What CoCo Platform Is

CoCo Platform is a local-first web application that provides a visual control plane for CoCo (conversational CLI PM autopilot) and Knowledge Hub (content ingestion pipeline). It gives a single PM — Rijul — a browser-based dashboard to manage multiple McKinsey projects, spawn and monitor background Claude Code agents ("stations"), review queued decisions, track costs, and chat with CoCo — all without replacing the CLI workflow that already works.

Think of it as "mission control" layered on top of the existing `~/.coco/` and `~/.hub/` data stores.

### Design Principles

1. **Additive, not replacement.** The CLI remains the primary interface. The web app reads the same files and databases. Nothing breaks if the web app is down.
2. **Single-user, local-only.** No multi-tenancy. No cloud deployment. No auth beyond optional PIN. Runs on `localhost`.
3. **SQLite as source of truth.** No new database engine. The existing `hub.db` stays authoritative for content; new platform state goes into a sibling `platform.db`.
4. **File-system as IPC.** Stations communicate via `events.jsonl`, session files, and JSON state files — the same mechanism CoCo already uses. No message broker.
5. **Stateless backend, stateful files.** The API server holds no in-memory state beyond caches. All durable state is in SQLite or JSON files on disk.
6. **Progressive enhancement.** Phase 1 is read-only dashboard over existing data. Station management and chat come in later phases.

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BROWSER (localhost:5173)                     │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Dashboard │ │ Projects │ │ Stations │ │   Chat   │ │ Settings │ │
│  │  (home)  │ │  Detail  │ │  Panel   │ │(CoCo Web)│ │  & Cost  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       └─────────────┴────────────┴─────────────┴────────────┘       │
│                              │ React 19 + Vite 6                    │
│                              │ Radix UI + Tailwind CSS 4            │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ HTTP + SSE
┌──────────────────────────────┼──────────────────────────────────────┐
│                     API SERVER (localhost:3001)                      │
│                        Python 3.13 / FastAPI                        │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ Project  │ │ Station  │ │  Queue   │ │   Chat   │              │
│  │ Service  │ │ Manager  │ │ Service  │ │ Service  │              │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘              │
│       │             │            │             │                     │
│  ┌────┴─────────────┴────────────┴─────────────┴──────────────────┐ │
│  │                     Data Access Layer                          │ │
│  │   hub.db (RO)  │  platform.db (RW)  │  JSON files (RW)       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ File I/O + subprocess
┌──────────────────────────────┼──────────────────────────────────────┐
│                        LOCAL FILE SYSTEM                             │
│                                                                     │
│  ~/.hub/hub.db          ~/.coco/brain.json     ~/.coco/events.jsonl │
│  ~/.hub/projects.toml   ~/.coco/queue.json     ~/.coco/sessions/    │
│                          ~/.coco/config.json    ~/.coco/platform.db  │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │  Station 1  │  │  Station 2  │  │  Station N  │                │
│  │ claude -p   │  │ claude -p   │  │ claude -p   │                │
│  │  (PID 4521) │  │  (PID 4588) │  │  (PID ...)  │                │
│  └─────────────┘  └─────────────┘  └─────────────┘                │
│                                                                     │
│  ┌─────────────┐                                                    │
│  │  think.py   │  (launchd, every 15min)                           │
│  │  cron job   │                                                    │
│  └─────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tech Stack Decision

### Frontend: React 19 + Vite 6 + Radix UI + Tailwind CSS 4

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | React 19 | Server Components not needed (local app), but React 19's `use()` hook and improved Suspense simplify data fetching from the FastAPI backend. |
| Bundler | Vite 6 | Sub-second HMR. No webpack complexity. Dev server proxies API calls to FastAPI. |
| Component library | Radix UI (primitives) | Unstyled, accessible, composable. No design-system lock-in. Pairs with Tailwind for styling. |
| Styling | Tailwind CSS 4 | Utility-first, zero runtime, v4's CSS-first config eliminates `tailwind.config.js`. |
| State management | Zustand | Minimal API, no boilerplate, works well with SSE streams. One store per domain (projects, stations, queue, chat). |
| Data fetching | TanStack Query v5 | Cache invalidation, background refetch, SSE integration via `queryClient.setQueryData`. |
| Routing | React Router v7 | File-based routing optional; explicit routes preferred for this app's small surface area. |
| Charts | Recharts | Lightweight, composable, React-native. Used for cost charts and activity timelines. |

### Backend: Python 3.13 + FastAPI

**Decision: FastAPI (Python), not Express (Node).**

Rationale:

1. **Knowledge Hub is Python.** The existing hub.db interactions, content pipeline, and think.py are all Python. Sharing the data access layer avoids rewriting SQLite queries and TOML parsing in JavaScript.
2. **sqlite3 in Python is superior.** Python's `sqlite3` module with `row_factory`, context managers, and read-only URI mode (`?mode=ro`) is more ergonomic than `better-sqlite3` in Node. We already have battle-tested query patterns from think.py.
3. **subprocess management.** Python's `subprocess.Popen` with `psutil` for process monitoring is more reliable than Node's `child_process.spawn` for long-lived station management. We need PID tracking, CPU/memory monitoring, and signal handling — `psutil` is purpose-built for this.
4. **FastAPI's async model.** SSE via `StreamingResponse` + `asyncio.Queue` is cleaner than Express's manual `res.write()` pattern. Pydantic models enforce API contracts.
5. **Existing server.js is minimal.** The current Express server is 345 lines. Its functionality (events SSE, chat spawn, skill catalog, session listing) will be absorbed into FastAPI with less code.

The existing `server.js` dashboard continues to run during migration on port 3000. The new FastAPI server runs on port 3001. Once feature parity is reached, `server.js` is retired.

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | FastAPI 0.115+ | Async, typed, auto-OpenAPI docs, Pydantic validation |
| Python | 3.13 | Already installed (used by think.py). Free-threaded mode available if needed. |
| Process mgmt | psutil | Cross-platform process monitoring (CPU, memory, status) |
| TOML parsing | tomllib (stdlib) | Parse projects.toml without dependencies |
| SSE | sse-starlette | `EventSourceResponse` over `asyncio.Queue` |
| Task scheduling | None (launchd) | think.py already runs via launchd. No need for Celery/APScheduler. |

### Database Strategy: Two SQLite Files

```
~/.hub/hub.db        — Knowledge Hub (EXISTING, read-only from platform)
~/.coco/platform.db  — CoCo Platform (NEW, read-write)
```

**Why two databases, not one:**

- `hub.db` is owned by Knowledge Hub's MCP server. CoCo Platform opens it `?mode=ro` to avoid write contention. Knowledge Hub's adapters, pipeline stages, and MCP tools all write to it. Platform never writes to it.
- `platform.db` stores station state, cost aggregations, governance audit log, and UI preferences. This is owned exclusively by the FastAPI server.

**platform.db schema (new):**

```sql
-- Station lifecycle tracking
CREATE TABLE stations (
    id TEXT PRIMARY KEY,           -- uuid
    name TEXT NOT NULL,
    project_id TEXT,               -- FK to hub.db projects (loose, not enforced cross-db)
    pid INTEGER,                   -- OS process ID
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending','running','paused','completed','failed','killed')),
    task_description TEXT,
    working_directory TEXT,
    started_at TEXT,
    stopped_at TEXT,
    last_heartbeat TEXT,
    exit_code INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Station output log (stdout/stderr chunks)
CREATE TABLE station_output (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT NOT NULL REFERENCES stations(id),
    stream TEXT NOT NULL CHECK(stream IN ('stdout','stderr')),
    chunk TEXT NOT NULL,
    timestamp TEXT NOT NULL
);
CREATE INDEX idx_station_output_station ON station_output(station_id);

-- Cost tracking (aggregated from hub.db api_costs + station-level tracking)
CREATE TABLE cost_ledger (
    id TEXT PRIMARY KEY,
    station_id TEXT REFERENCES stations(id),
    project_id TEXT,
    timestamp TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    source TEXT NOT NULL CHECK(source IN ('station','chat','think','kh_pipeline'))
);
CREATE INDEX idx_cost_ledger_project ON cost_ledger(project_id);
CREATE INDEX idx_cost_ledger_timestamp ON cost_ledger(timestamp);

-- Budget caps per project
CREATE TABLE budgets (
    project_id TEXT PRIMARY KEY,
    daily_cap_usd REAL,
    weekly_cap_usd REAL,
    monthly_cap_usd REAL,
    alert_threshold_pct REAL DEFAULT 0.8
);

-- Governance audit log
CREATE TABLE governance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,          -- 'approved', 'rejected', 'auto_handled', 'escalated'
    item_type TEXT NOT NULL,       -- 'draft', 'jira_ticket', 'external_comm', 'station_spawn'
    item_id TEXT,
    autonomy_mode TEXT,            -- 'CAREFUL', 'NORMAL', 'YOLO'
    confidence REAL,
    decision_by TEXT DEFAULT 'user', -- 'user', 'auto', 'coco'
    notes TEXT
);
CREATE INDEX idx_governance_timestamp ON governance_log(timestamp);

-- UI preferences (single row)
CREATE TABLE preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### Real-Time: SSE (Server-Sent Events)

**Decision: SSE, not WebSocket.**

Rationale:

1. **Unidirectional is sufficient.** The server pushes events to the browser (station output, activity feed, cost updates). The browser sends commands via REST POST. There is no bidirectional streaming requirement.
2. **Existing pattern.** The current `server.js` already uses SSE for `events.jsonl` tailing. This is a proven pattern in this codebase.
3. **Simpler infrastructure.** SSE works over standard HTTP. No upgrade handshake, no ping/pong frames, no reconnection protocol to implement (browsers auto-reconnect SSE via `EventSource`).
4. **Multiple channels.** FastAPI serves multiple SSE endpoints: `/api/events/activity` (activity feed), `/api/events/stations/{id}` (station output), `/api/events/costs` (cost updates). Each is an independent `EventSourceResponse`.

The chat interface uses a hybrid: POST to `/api/chat` returns an SSE stream of the Claude response (same pattern as current `server.js`).

---

## 3. Component Architecture

### Frontend Component Tree

```
App
├── Layout
│   ├── Sidebar
│   │   ├── NavItem (Dashboard)
│   │   ├── NavItem (Projects)
│   │   ├── NavItem (Stations)
│   │   ├── NavItem (Queue)
│   │   ├── NavItem (Chat)
│   │   ├── NavItem (Costs)
│   │   ├── NavItem (Settings)
│   │   └── AutonomyModeBadge        — shows CAREFUL/NORMAL/YOLO
│   └── TopBar
│       ├── SearchCommand (Cmd+K)
│       ├── NotificationBell
│       └── ThinkPassIndicator       — pulses when think.py last ran
│
├── DashboardPage
│   ├── ProjectCardGrid
│   │   └── ProjectCard              — name, item counts, health dot, cost sparkline
│   ├── StationStatusBar             — running/paused/idle counts
│   ├── ActivityFeed                  — real-time SSE event stream
│   │   └── ActivityItem             — icon + description + timestamp
│   ├── QueueSummary                 — pending items count, top-3 preview
│   └── CostSummaryChart             — daily spend bar chart (last 7 days)
│
├── ProjectsPage
│   ├── ProjectList
│   │   └── ProjectRow               — name, Jira key, Confluence space, health
│   └── ProjectDetailPanel (slide-over)
│       ├── ProjectHeader            — name, links to Jira/Confluence
│       ├── ContentTimeline          — items from hub.db for this project
│       ├── DraftsList               — pending drafts needing approval
│       ├── StationsList             — stations assigned to this project
│       ├── TodoList                 — open todos for this project
│       └── BudgetGauge              — spend vs cap
│
├── StationsPage
│   ├── StationGrid
│   │   └── StationCard              — name, PID, status, uptime, CPU/MEM
│   ├── SpawnStationDialog           — project picker, task description, autonomy
│   └── StationDetailPanel
│       ├── OutputTerminal           — live stdout/stderr via SSE
│       ├── StationControls          — pause, resume, kill buttons
│       └── StationCostChart
│
├── QueuePage
│   ├── QueueFilters                 — by type, priority, project
│   ├── QueueItemList
│   │   └── QueueItem                — priority badge, summary, action buttons
│   │       ├── ApproveButton
│   │       ├── DeferButton
│   │       └── DismissButton
│   └── AutoHandledLog               — what CoCo handled automatically
│
├── ChatPage
│   ├── MessageList
│   │   └── ChatMessage              — user or assistant, markdown rendered
│   ├── ChatInput                    — textarea + send, supports / commands
│   └── SkillPalette                 — searchable list of /commands
│
├── CostsPage
│   ├── CostOverviewChart            — line chart, daily/weekly/monthly toggle
│   ├── CostByProjectTable           — project breakdown
│   ├── CostByModelTable             — model breakdown (sonnet vs opus vs haiku)
│   ├── CostByFeatureTable           — pipeline stage breakdown
│   └── BudgetAlertsList
│
└── SettingsPage
    ├── AutonomyModeSelector         — CAREFUL / NORMAL / YOLO with thresholds
    ├── AutoHandleRules              — edit config.json auto_handle section
    ├── BudgetEditor                 — per-project caps
    ├── BrainViewer                  — read-only brain.json visualization
    │   └── PeopleGraph              — org chart / network from brain.json
    └── ImportExportPanel            — backup/restore brain.json, queue.json, platform.db
```

### Backend Service Layers

```
FastAPI Application (main.py)
│
├── Routers (HTTP layer)
│   ├── projects.py        — GET /api/projects, GET /api/projects/{id}
│   ├── stations.py        — CRUD + POST /api/stations/{id}/spawn, /pause, /kill
│   ├── queue.py           — GET /api/queue, POST /api/queue/{id}/approve|defer|dismiss
│   ├── chat.py            — POST /api/chat (SSE response)
│   ├── costs.py           — GET /api/costs, GET /api/costs/by-project, /by-model
│   ├── events.py          — GET /api/events/activity, /stations/{id}
│   ├── brain.py           — GET /api/brain (read-only), GET /api/brain/people
│   ├── settings.py        — GET/PUT /api/settings
│   └── health.py          — GET /api/health
│
├── Services (business logic)
│   ├── project_service.py     — reads hub.db projects + projects.toml, joins with content counts
│   ├── station_manager.py     — spawn/monitor/kill Claude Code processes (see Section 6)
│   ├── queue_service.py       — reads/writes queue.json, applies governance rules
│   ├── chat_service.py        — spawns claude -p, streams output
│   ├── cost_service.py        — aggregates from hub.db api_costs + platform.db cost_ledger
│   ├── brain_service.py       — reads brain.json, provides people graph
│   ├── event_bus.py           — in-process pub/sub for SSE fan-out
│   └── governance.py          — autonomy mode enforcement, approval gates
│
├── Data Access (persistence)
│   ├── hub_db.py              — read-only connection to ~/.hub/hub.db
│   ├── platform_db.py         — read-write connection to ~/.coco/platform.db
│   ├── json_store.py          — atomic read/write for brain.json, queue.json, config.json
│   └── events_log.py          — append to events.jsonl, tail for SSE
│
└── Core
    ├── config.py              — loads config.json + env vars
    ├── models.py              — Pydantic models for all API request/response types
    └── dependencies.py        — FastAPI dependency injection (DB connections, services)
```

### How They Connect

```
Browser (React)
    │
    │  fetch / EventSource
    │
    ▼
FastAPI Router
    │
    │  dependency injection
    │
    ▼
Service Layer
    │
    ├──► hub_db.py ──► ~/.hub/hub.db (SELECT only)
    ├──► platform_db.py ──► ~/.coco/platform.db (full CRUD)
    ├──► json_store.py ──► brain.json, queue.json, config.json
    ├──► events_log.py ──► events.jsonl (append + tail)
    └──► subprocess ──► claude -p (station processes)
```

---

## 4. Integration Architecture

### 4.1 Knowledge Hub (hub.db)

```
CoCo Platform ──(sqlite3, ?mode=ro)──► ~/.hub/hub.db
```

**Connection strategy:**
- Open a single read-only connection at startup: `sqlite3.connect("file:~/.hub/hub.db?mode=ro", uri=True)`
- Use WAL mode (hub.db already uses WAL) so reads never block the Knowledge Hub's writes
- Connection is shared across async requests via a thread pool (`run_in_executor`) since sqlite3 is not async-native
- All queries are parameterized, read-only

**Tables read:**

| Table | Used For |
|-------|----------|
| `projects` | Project list, names, Jira/Confluence links |
| `content` | Content items per project, status counts, timeline |
| `content_fts` | Full-text search from the dashboard search bar |
| `drafts` | Pending drafts shown in Queue and Project Detail |
| `sync_state` | Health indicators (green/yellow/red per adapter) |
| `api_costs` | Cost aggregation by project, model, feature |
| `todos` | Todo list per project |
| `entities` | People/org mentions for brain enrichment |

**Supplemental file:**
- `~/.hub/projects.toml` is parsed at startup for sender rules, subject patterns, and folder paths that are not stored in hub.db.

### 4.2 CoCo Brain Files

```
CoCo Platform ──(json_store.py)──► ~/.coco/brain.json   (read-write)
                                    ~/.coco/queue.json   (read-write)
                                    ~/.coco/config.json  (read-write)
```

**Concurrency with think.py:**

Both CoCo Platform and `think.py` (launchd cron) read and write `queue.json` and `brain.json`. Conflict resolution:

1. **Atomic writes.** Both use the write-to-tmp-then-rename pattern (already implemented in think.py's `atomic_write_json`). Platform's `json_store.py` uses the same pattern.
2. **Last-write-wins.** For queue.json, think.py adds items and Platform removes them (approve/dismiss). These are non-overlapping mutations — think.py appends to `items[]`, Platform removes from `items[]` or moves to `deferred[]`. Rare race condition: think.py overwrites a just-approved item. Mitigation: Platform writes a `.queue.lock` advisory file. think.py checks it and retries after 1 second.
3. **brain.json is mostly read.** Platform only writes to it when the user edits attention rules from Settings. think.py only increments `stats.items_auto_handled`. These touch different keys.
4. **config.json is read-only from think.py.** Only Platform writes to it (Settings page).

### 4.3 Claude API (Chat)

```
Browser ──POST /api/chat──► FastAPI ──subprocess──► claude -p ──► Claude API
                              │
                              └──SSE stream──► Browser
```

The chat service does NOT call the Claude API directly. It spawns `claude -p --output-format text <message>` as a subprocess (same as current server.js). This preserves:
- Claude Code's MCP tool access (Knowledge Hub tools, Confluence, Jira)
- CoCo SKILL.md activation (the spawned Claude Code loads ~/.claude/skills/)
- Existing session journaling (events.jsonl)

**Why not direct API calls:**
Using `anthropic` Python SDK directly would bypass MCP tools, CoCo skills, and session tracking. The whole point of CoCo Platform chat is that it IS CoCo, just rendered in a browser instead of a terminal.

**Chat session management:**
- Each chat spawns a new `claude -p` process
- The process runs in `$HOME` directory (same as current server.js)
- 5-minute timeout with SIGKILL on disconnect
- Output streamed as SSE events: `{type: "text", text: "..."}`, `{type: "done", code: 0}`

### 4.4 Claude Code CLI (Station Spawning)

```
FastAPI StationManager
    │
    ├── spawn(task, project, cwd)
    │   └── subprocess.Popen(["claude", "-p", "--output-format", "stream-json", task], ...)
    │
    ├── monitor(pid)
    │   └── psutil.Process(pid).status(), .cpu_percent(), .memory_info()
    │
    ├── pause(pid)
    │   └── os.kill(pid, signal.SIGSTOP)
    │
    ├── resume(pid)
    │   └── os.kill(pid, signal.SIGCONT)
    │
    └── kill(pid)
        └── os.kill(pid, signal.SIGTERM) → wait 5s → SIGKILL
```

Stations use `--output-format stream-json` (not `text`) to get structured output with tool use events, token counts, and cost data. This enables:
- Real-time activity tracking per station
- Accurate cost attribution
- Tool use visibility in the station detail panel

See Section 6 for full station lifecycle.

---

## 5. Data Flow

### 5.1 Primary Data Flow: Content Ingestion to Dashboard

```
Email/Voice/Jira/Confluence
         │
         ▼
   Knowledge Hub Adapters
         │
         ▼
   hub.db (content table)
   status: INGESTED → PREPROCESSED → TRIAGED → CLASSIFIED → SYNTHESIZED → COMPLETE
         │
         ▼
   think.py (every 15min)
   reads hub.db, writes queue.json
         │
         ▼
   CoCo Platform FastAPI
   reads hub.db (project cards, content counts)
   reads queue.json (pending items)
         │
         ▼
   Browser (React)
   Dashboard: project cards, activity feed, queue summary
```

### 5.2 User Action: Approve a Draft

```
User clicks "Approve" on QueuePage
         │
         ▼
POST /api/queue/{id}/approve
         │
         ▼
queue_service.py:
  1. Read queue.json
  2. Remove item from items[]
  3. Call MCP tool: mcp__knowledge-hub__approve_draft(draft_id)
     (via subprocess: claude -p "approve draft {id}")
  4. Log to governance_log table in platform.db
  5. Write queue.json (atomic)
  6. Publish event to event_bus
         │
         ▼
event_bus.py → SSE /api/events/activity
         │
         ▼
Browser: ActivityFeed updates, QueueSummary count decrements
```

### 5.3 User Action: Spawn a Station

```
User fills SpawnStationDialog: project="audit-board", task="Review Q3 draft"
         │
         ▼
POST /api/stations
  body: { project_id, task_description, autonomy_mode }
         │
         ▼
station_manager.py:
  1. Check governance: is user allowed to spawn? (budget check, max stations)
  2. INSERT INTO stations (status='pending')
  3. Popen(["claude", "-p", "--output-format", "stream-json", task], cwd=project_folder)
  4. UPDATE stations SET pid=..., status='running', started_at=now()
  5. Start background reader thread for stdout/stderr
  6. Publish 'station_started' event
         │
         ▼
Background reader thread:
  - Reads stdout line-by-line (stream-json produces one JSON object per line)
  - Parses each line for: text output, tool_use, cost data
  - INSERT INTO station_output (chunks for terminal display)
  - INSERT INTO cost_ledger (per-message cost tracking)
  - UPDATE stations SET last_heartbeat=now()
  - Publish chunks to SSE /api/events/stations/{id}
         │
         ▼
Browser: StationCard goes green, OutputTerminal shows live output
```

### 5.4 Background: think.py Cycle

```
launchd fires think.py (every 15 min)
         │
         ▼
think.py:
  1. Read brain.json, queue.json, config.json
  2. Connect hub.db (read-only)
  3. Query new content since last_updated
  4. Apply attention rules → calculate priority
  5. Apply auto_handle rules → dismiss noise, file FYI
  6. Age deferred items → resurface if due
  7. Write queue.json (atomic)
  8. Write brain.json stats (atomic)
         │
         ▼
Platform (if running):
  - json_store.py detects queue.json mtime change (inotify/kqueue via watchdog)
  - Publishes 'queue_updated' event to event_bus
  - SSE pushes update to browser
  - QueueSummary and NotificationBell update
```

---

## 6. Station Management

### Process Model

A "station" is a long-running `claude -p` process that executes a task autonomously. Stations are the CoCo Platform equivalent of Paperclip's "agents."

```
┌─────────────────────────────────────────────┐
│              Station Lifecycle               │
│                                             │
│  PENDING ──► RUNNING ──► COMPLETED          │
│                │                             │
│                ├──► PAUSED ──► RUNNING       │
│                │                             │
│                ├──► FAILED                   │
│                │                             │
│                └──► KILLED                   │
└─────────────────────────────────────────────┘
```

| State | Trigger | PID | Notes |
|-------|---------|-----|-------|
| PENDING | POST /api/stations | None | Pre-governance check |
| RUNNING | Popen succeeds | Active | Stdout being read |
| PAUSED | SIGSTOP sent | Active (stopped) | macOS supports SIGSTOP for Claude processes |
| COMPLETED | Process exits code 0 | Dead | Output preserved |
| FAILED | Process exits code != 0 | Dead | Stderr captured |
| KILLED | User clicks Kill, or budget exceeded | Dead | SIGTERM → 5s → SIGKILL |

### Spawn Protocol

```python
async def spawn_station(task: str, project_id: str, autonomy: str) -> Station:
    # 1. Governance gate
    if autonomy == "CAREFUL":
        # Queue for approval, don't spawn yet
        return create_pending_station(task, project_id)

    # 2. Budget check
    budget = get_budget(project_id)
    if budget and get_daily_spend(project_id) >= budget.daily_cap_usd:
        raise BudgetExceeded(project_id)

    # 3. Max concurrent station check (default: 3)
    running = count_running_stations()
    if running >= MAX_CONCURRENT_STATIONS:
        raise TooManyStations(running)

    # 4. Resolve working directory
    project = get_project(project_id)
    cwd = project.folder_path or os.environ["HOME"]

    # 5. Build the prompt with project context
    system_prompt = f"You are working on project: {project.name}. Autonomy mode: {autonomy}."
    full_prompt = f"{system_prompt}\n\nTask: {task}"

    # 6. Spawn
    env = sanitized_env()  # strip CLAUDECODE vars
    proc = subprocess.Popen(
        ["claude", "-p", "--output-format", "stream-json", full_prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=env,
    )

    # 7. Record in platform.db
    station = insert_station(pid=proc.pid, project_id=project_id, task=task, status="running")

    # 8. Start output reader in background thread
    threading.Thread(target=read_station_output, args=(station.id, proc), daemon=True).start()

    # 9. Emit event
    event_bus.publish("station_started", station)

    return station
```

### IPC Mechanism

Stations communicate with the platform via two channels:

1. **stdout (stream-json).** The `--output-format stream-json` flag causes Claude Code to emit one JSON object per line. Each object contains:
   - `type`: "text", "tool_use", "tool_result", "error", "usage"
   - Token counts and cost per message
   - Tool calls (which Knowledge Hub MCP tools were invoked)

2. **events.jsonl (shared).** If the station's Claude Code session writes to `~/.coco/events.jsonl` (via CoCo skill), the platform's event tailer picks it up and attributes it to the station by matching the session ID.

There is no stdin communication. Stations are fire-and-forget with monitoring. If you need to change a station's behavior, you kill it and spawn a new one with updated instructions.

### Heartbeat Protocol

```
Every 30 seconds, the output reader thread:
  1. UPDATE stations SET last_heartbeat = now() WHERE id = ?
  2. Check psutil.Process(pid).status()
     - If zombie/dead → mark FAILED, capture exit code
     - If stopped → verify status is PAUSED (external SIGSTOP detection)
  3. Read CPU% and RSS memory → store in station_output for charting

If no heartbeat for 2 minutes and process is gone:
  → Mark station as FAILED with note "process disappeared"
```

### Concurrent Station Limits

Default maximum: **3 concurrent running stations.** Configurable in config.json.

Rationale: Each `claude -p` process consumes ~200MB RAM and makes API calls that cost money. Three stations is enough for parallel work across projects without resource exhaustion on a MacBook.

---

## 7. Security Model

### Threat Model

This is a local-only, single-user application. The threat model is narrow:

| Threat | Risk | Mitigation |
|--------|------|------------|
| API key exposure | HIGH | Keys stored in macOS Keychain or `~/.claude/` config (managed by Claude Code). Never in platform.db or browser localStorage. |
| Non-localhost access | MEDIUM | FastAPI binds to `127.0.0.1` only. Origin check middleware rejects non-localhost `Origin` headers. |
| Runaway cost | HIGH | Budget caps in platform.db. Station auto-kill when budget exceeded. Cost alerts via SSE. |
| Rogue station | MEDIUM | 5-minute timeout on chat. Configurable timeout on stations (default 30 min). SIGKILL as last resort. |
| File permission | LOW | hub.db opened read-only. brain.json backed up before writes (think.py pattern). Atomic writes prevent corruption. |
| XSS in station output | LOW | React's JSX escaping handles this. Station output rendered in a `<pre>` block, not `dangerouslySetInnerHTML`. |

### API Key Management

```
Claude API key:
  └── Managed by Claude Code CLI (~/.claude/ config)
  └── Inherited by spawned claude -p processes via environment
  └── Never read, stored, or proxied by CoCo Platform

Confluence/Jira API tokens:
  └── Stored in ~/.cursor/confluence-mcp/run.sh (existing)
  └── Used by Knowledge Hub MCP server, not by Platform directly
  └── Platform accesses Jira/Confluence data only through hub.db
```

### Optional PIN Lock

For physical security (shared office, screen visibility):
- PIN stored as bcrypt hash in platform.db `preferences` table
- Checked once per browser session via a cookie (HttpOnly, SameSite=Strict, 8-hour expiry)
- No PIN by default — opt-in from Settings

---

## 8. Deployment Model

### How It Runs

CoCo Platform runs as **two processes** on macOS, managed by launchd:

```
com.coco.platform-api    — Python FastAPI server (port 3001)
com.coco.platform-ui     — Vite dev server (port 5173) OR static build served by FastAPI
```

In development:
```bash
# Terminal 1: API server
cd ~/projects/coco-platform/backend
uv run uvicorn main:app --host 127.0.0.1 --port 3001 --reload

# Terminal 2: Frontend dev server
cd ~/projects/coco-platform/frontend
npm run dev   # Vite on port 5173, proxies /api to 3001
```

In production (daily use):
```bash
# Single command starts everything
cd ~/projects/coco-platform
./start.sh
# 1. Builds frontend: npm run build → backend/static/
# 2. Starts FastAPI with static file serving: uvicorn main:app --host 127.0.0.1 --port 3001
# 3. Opens browser to http://localhost:3001
```

### launchd Integration

```xml
<!-- ~/Library/LaunchAgents/com.coco.platform.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.coco.platform</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/Rijul_Kalra/.local/bin/uv</string>
        <string>run</string>
        <string>uvicorn</string>
        <string>main:app</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>3001</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/Rijul_Kalra/projects/coco-platform/backend</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/Rijul_Kalra/.coco/logs/platform-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/Rijul_Kalra/.coco/logs/platform-error.log</string>
</dict>
</plist>
```

### Why Not Docker

- Single user, single machine — Docker adds latency and complexity for no benefit
- Need direct access to `~/.coco/` and `~/.hub/` files — volume mounts add friction
- Need to spawn `claude` CLI — Docker would need Claude Code installed inside the container
- `psutil` process monitoring needs host PID namespace access
- macOS Docker Desktop has known performance issues with file watching

### Coexistence with Existing Services

| Service | Port | Manager | Status |
|---------|------|---------|--------|
| CoCo Dashboard (server.js) | 3000 | Manual `node server.js` | **Deprecated after migration** |
| CoCo Platform API (FastAPI) | 3001 | launchd | **New** |
| CoCo Platform UI (Vite dev) | 5173 | Manual `npm run dev` | Dev only |
| Knowledge Hub MCP | stdio | Claude Code | Unchanged |
| think.py | N/A | launchd (every 15min) | Unchanged |

### Directory Structure

```
~/projects/coco-platform/
├── .planning/
│   ├── ARCHITECTURE.md          ← this document
│   ├── FEATURES.md
│   └── ROADMAP.md
├── backend/
│   ├── main.py                  — FastAPI app entry point
│   ├── routers/
│   │   ├── projects.py
│   │   ├── stations.py
│   │   ├── queue.py
│   │   ├── chat.py
│   │   ├── costs.py
│   │   ├── events.py
│   │   ├── brain.py
│   │   ├── settings.py
│   │   └── health.py
│   ├── services/
│   │   ├── project_service.py
│   │   ├── station_manager.py
│   │   ├── queue_service.py
│   │   ├── chat_service.py
│   │   ├── cost_service.py
│   │   ├── brain_service.py
│   │   ├── event_bus.py
│   │   └── governance.py
│   ├── data/
│   │   ├── hub_db.py
│   │   ├── platform_db.py
│   │   ├── json_store.py
│   │   └── events_log.py
│   ├── core/
│   │   ├── config.py
│   │   ├── models.py
│   │   └── dependencies.py
│   ├── static/                  — Vite build output (gitignored)
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.css
│   ├── tsconfig.json
│   ├── package.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── routes/
│       │   ├── dashboard.tsx
│       │   ├── projects.tsx
│       │   ├── stations.tsx
│       │   ├── queue.tsx
│       │   ├── chat.tsx
│       │   ├── costs.tsx
│       │   └── settings.tsx
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.tsx
│       │   │   ├── TopBar.tsx
│       │   │   └── Layout.tsx
│       │   ├── dashboard/
│       │   │   ├── ProjectCard.tsx
│       │   │   ├── ActivityFeed.tsx
│       │   │   ├── StationStatusBar.tsx
│       │   │   └── CostSummaryChart.tsx
│       │   ├── stations/
│       │   │   ├── StationCard.tsx
│       │   │   ├── OutputTerminal.tsx
│       │   │   ├── SpawnDialog.tsx
│       │   │   └── StationControls.tsx
│       │   ├── queue/
│       │   │   ├── QueueItem.tsx
│       │   │   └── QueueFilters.tsx
│       │   ├── chat/
│       │   │   ├── MessageList.tsx
│       │   │   ├── ChatInput.tsx
│       │   │   └── SkillPalette.tsx
│       │   └── shared/
│       │       ├── HealthDot.tsx
│       │       ├── PriorityBadge.tsx
│       │       └── CostSparkline.tsx
│       ├── stores/
│       │   ├── projectStore.ts
│       │   ├── stationStore.ts
│       │   ├── queueStore.ts
│       │   └── costStore.ts
│       ├── hooks/
│       │   ├── useSSE.ts
│       │   └── useProjects.ts
│       ├── lib/
│       │   └── api.ts            — fetch wrapper, SSE helpers
│       └── types/
│           └── index.ts          — TypeScript types matching Pydantic models
├── start.sh
├── CLAUDE.local.md
└── .gitignore
```

---

## 9. Key Technical Risks

### Risk 1: SQLite Write Contention on queue.json

**Problem:** Both think.py (every 15min) and the FastAPI server write to `queue.json`. If think.py runs during a user's rapid approve/dismiss sequence, one write could clobber the other.

**Severity:** Medium. Data loss is limited to a single think-pass cycle (15 minutes of queue items).

**Mitigation:**
1. Advisory lock file (`.queue.lock`) with PID. Writer checks lock, backs off 1 second.
2. Merge-on-write: before writing, re-read the file and merge changes rather than overwrite. think.py only adds items; Platform only removes/modifies items. A 3-way merge is possible.
3. Long-term migration: move queue to `platform.db` SQLite table. think.py writes to the table directly. SQLite handles concurrency via WAL mode.

### Risk 2: Claude Code CLI as Black Box

**Problem:** Stations depend on `claude -p` subprocess behavior. If Anthropic changes the CLI's `--output-format stream-json` schema, stations break silently.

**Severity:** High. This is an external dependency we do not control.

**Mitigation:**
1. Pin the Claude Code version in the project (track in CLAUDE.local.md).
2. Parse station output defensively — unknown fields ignored, missing fields defaulted.
3. Integration test that spawns `claude -p --output-format stream-json "say hello"` and validates the JSON structure. Run weekly.
4. Keep the existing `--output-format text` path as a fallback for chat (simpler, more stable).

### Risk 3: Runaway Station Costs

**Problem:** A station given a broad task ("review all Q3 content") could make hundreds of API calls, costing tens of dollars before anyone notices.

**Severity:** High. Real money at stake.

**Mitigation:**
1. **Per-station token budget.** Configurable max tokens per station (default: 200k input + 50k output, roughly $5 for Sonnet). Station manager reads stream-json usage events and kills the process when budget is exceeded.
2. **Per-project daily cap.** Checked before spawn and during execution.
3. **Real-time cost SSE.** CostSummaryChart shows live spend. Budget alerts push notifications to the browser.
4. **Governance gate.** In CAREFUL mode, station spawn requires explicit approval. In NORMAL mode, auto-approved up to budget. In YOLO mode, no gates but alerts still fire.

### Risk 4: Process Zombies

**Problem:** If FastAPI crashes while stations are running, those `claude -p` processes become orphans. On restart, Platform has stale PID records that may point to wrong processes.

**Severity:** Medium. Orphan processes waste resources and money.

**Mitigation:**
1. **Startup reconciliation.** On FastAPI startup, scan `stations` table for `status='running'`. For each, check if PID is alive via `psutil.pid_exists()`. If dead, mark as FAILED. If alive, verify it is actually a `claude` process (check `psutil.Process(pid).name()`).
2. **Process group.** Spawn stations in their own process group (`os.setpgrp`). On Platform shutdown, send SIGTERM to all station process groups.
3. **Heartbeat timeout.** If `last_heartbeat` is older than 2 minutes, assume dead and clean up.

### Risk 5: hub.db Schema Changes

**Problem:** Knowledge Hub may add or alter tables in hub.db. Platform queries could break.

**Severity:** Low-Medium. Both systems are maintained by the same developer.

**Mitigation:**
1. `hub_db.py` queries use explicit column lists, not `SELECT *`.
2. On startup, run a schema check: verify expected tables and columns exist. Log warnings for missing elements, degrade gracefully.
3. Document the hub.db schema contract in this architecture doc (done — see Section 4.1).

### Risk 6: Vite Dev Server CORS / Proxy Issues

**Problem:** During development, the Vite dev server on port 5173 needs to proxy API calls to FastAPI on port 3001. CORS misconfigurations or proxy failures cause confusing errors.

**Severity:** Low. Development-only issue.

**Mitigation:**
1. `vite.config.ts` configures proxy: `server.proxy["/api"] = "http://127.0.0.1:3001"`.
2. FastAPI adds CORS middleware allowing `http://localhost:5173` in development.
3. In production, FastAPI serves the built static files directly — no CORS needed.

### Risk 7: events.jsonl Unbounded Growth

**Problem:** `events.jsonl` grows indefinitely. It is already 1.7MB after a few days. At high station activity, it could reach hundreds of MB.

**Severity:** Medium. Degrades SSE performance (full replay on connect) and disk usage.

**Mitigation:**
1. **Log rotation.** Platform rotates `events.jsonl` daily. Archive files: `events.2026-03-24.jsonl.gz`. Keep 7 days of archives.
2. **SSE replay limit.** Only replay the last 500 events on connect (not the entire file). Use byte offset tracking.
3. **Archival to platform.db.** Periodically copy events into a `events` table in platform.db for queryable history. The JSONL file becomes a hot buffer, not a permanent store.

---

## Appendix A: API Surface Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Server health, DB connectivity, think.py last run |
| GET | /api/projects | All projects with content counts, health |
| GET | /api/projects/{id} | Project detail with content, drafts, todos |
| GET | /api/stations | All stations with status |
| POST | /api/stations | Spawn a new station |
| GET | /api/stations/{id} | Station detail |
| POST | /api/stations/{id}/pause | SIGSTOP the station |
| POST | /api/stations/{id}/resume | SIGCONT the station |
| POST | /api/stations/{id}/kill | SIGTERM/SIGKILL the station |
| GET | /api/queue | Pending queue items |
| POST | /api/queue/{id}/approve | Approve a queue item |
| POST | /api/queue/{id}/defer | Defer a queue item |
| POST | /api/queue/{id}/dismiss | Dismiss a queue item |
| POST | /api/chat | Send message, receive SSE stream |
| GET | /api/costs | Cost summary (daily/weekly/monthly) |
| GET | /api/costs/by-project | Cost breakdown by project |
| GET | /api/costs/by-model | Cost breakdown by model |
| GET | /api/brain | Brain state (people, attention rules, stats) |
| GET | /api/brain/people | People graph for visualization |
| GET | /api/settings | Current config.json |
| PUT | /api/settings | Update config.json |
| GET | /api/events/activity | SSE: activity feed |
| GET | /api/events/stations/{id} | SSE: station output stream |

## Appendix B: Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| COCO_DIR | ~/.coco | CoCo data directory |
| HUB_DIR | ~/.hub | Knowledge Hub data directory |
| PLATFORM_PORT | 3001 | FastAPI server port |
| MAX_CONCURRENT_STATIONS | 3 | Max running stations |
| STATION_TIMEOUT_MINUTES | 30 | Default station timeout |
| CHAT_TIMEOUT_MINUTES | 5 | Chat process timeout |
| LOG_LEVEL | INFO | Python logging level |

## Appendix C: Decision Log

| # | Decision | Alternatives Considered | Rationale |
|---|----------|------------------------|-----------|
| D1 | FastAPI over Express | Express (existing), Flask | Python alignment with KH, subprocess management, typed APIs |
| D2 | SSE over WebSocket | WebSocket, polling | Unidirectional sufficient, simpler, existing pattern |
| D3 | Two SQLite DBs | Single DB, PostgreSQL | Ownership boundaries, read-only access to hub.db |
| D4 | Zustand over Redux | Redux Toolkit, Jotai, Context | Minimal API, good SSE integration, no boilerplate |
| D5 | launchd over Docker | Docker, systemd, PM2 | Native macOS, no virtualization overhead, existing pattern |
| D6 | claude -p over direct API | anthropic SDK, litellm | Preserves MCP tools, CoCo skills, session tracking |
| D7 | stream-json over text | text, json | Structured output enables cost tracking and tool visibility |
| D8 | uv over pip/poetry | pip, poetry, conda | Fast, lockfile support, inline scripts, already common in ecosystem |

---

## Appendix D: Data Migration Plan

### Existing Data — Zero Migration Required

CoCo Platform reads existing data stores in place. No data migration is needed.

| Data Store | Action | Notes |
|---|---|---|
| `~/.hub/hub.db` | Read as-is (`?mode=ro`) | Platform queries existing tables. No schema changes. |
| `~/.coco/brain.json` | Read/write as-is | Same atomic write pattern as think.py. No format changes. |
| `~/.coco/queue.json` | Read/write as-is | Same format. Platform adds/removes items like CoCo CLI does. |
| `~/.coco/config.json` | Read/write as-is | Platform may add new keys; existing keys unchanged. |
| `~/.coco/sessions/*.json` | Read as-is | Platform reads for session history page. Never writes. |
| `~/.coco/events.jsonl` | Read (tail) as-is | Platform tails for SSE. Never writes (stations write their own events). |

### New Data — Created on First Run

| Data Store | Created By | Trigger |
|---|---|---|
| `~/.coco/platform.db` | Alembic migration | First `uvicorn` startup runs `alembic upgrade head` |
| `~/.coco/platform.db` tables | Alembic | stations, station_output, cost_ledger, budgets, governance_log, preferences |

### Rollback

If CoCo Platform is uninstalled:
- Delete `~/.coco/platform.db` — removes all platform-specific state
- All existing files (hub.db, brain.json, queue.json, config.json) remain untouched
- CLI workflow continues as if Platform never existed

### hub.db Schema Versioning

On startup, Platform checks `PRAGMA user_version` on hub.db and logs a warning if it doesn't match the expected version. Queries use explicit column names (not `SELECT *`) to tolerate added columns. If a required table is missing, that feature degrades gracefully with an error message in the UI.

---

## Appendix E: Performance Budgets

| Metric | Target | Measurement |
|---|---|---|
| **API response (simple read)** | < 50ms | SQLite single-table query (projects, stations, config) |
| **API response (aggregation)** | < 200ms | Dashboard, cost summary, queue assembly |
| **API response (FTS5 search)** | < 100ms | Full-text search with snippet generation |
| **SSE event delivery** | < 500ms | Time from event write to browser render |
| **Frontend initial load** | < 2s | First contentful paint on localhost (Vite prod build) |
| **Frontend route transition** | < 100ms | React Router navigation between pages |
| **SQLite write (atomic JSON)** | < 20ms | brain.json/queue.json write-to-tmp + rename |
| **Station spawn** | < 3s | Time from click "Spawn" to process running + first output |
| **Chat first token** | < 2s | Time from send to first streaming token in browser |
| **Memory (FastAPI server)** | < 150MB | Baseline with no stations running |
| **Memory (per station)** | < 250MB | Each `claude -p` subprocess |
| **Disk (platform.db)** | < 50MB | After 6 months of typical use |

### How to Enforce

- Backend: Add `X-Response-Time` header middleware. Log slow queries (>200ms) to `~/.coco/logs/platform-slow.log`.
- Frontend: Lighthouse audit in Phase 12. Target score > 90 for Performance.
- SQLite: `PRAGMA journal_mode=WAL` on all DBs. `PRAGMA busy_timeout=5000` for contention.

---

## Appendix F: Platform Monitoring & Logging

### Log Files

| File | Content | Rotation |
|---|---|---|
| `~/.coco/logs/platform-stdout.log` | uvicorn access logs | launchd managed, manual rotation |
| `~/.coco/logs/platform-error.log` | Python exceptions, stack traces | launchd managed |
| `~/.coco/logs/platform-slow.log` | API responses > 200ms | Append-only, rotate weekly |
| `~/.coco/logs/station-{id}.log` | Per-station stdout/stderr | Created per spawn, archived on completion |

### Structured Logging

Backend uses Python `structlog` with JSON output:

```json
{"timestamp": "2026-03-25T13:22:00Z", "level": "info", "event": "station_spawned", "station_id": "abc123", "project": "audit-board", "pid": 4521}
{"timestamp": "2026-03-25T13:22:05Z", "level": "warning", "event": "slow_query", "path": "/api/dashboard", "duration_ms": 312}
{"timestamp": "2026-03-25T13:22:10Z", "level": "error", "event": "station_crash", "station_id": "abc123", "exit_code": 1, "stderr": "..."}
```

### Health Endpoint

`GET /api/health` returns:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "databases": {
    "hub_db": {"connected": true, "size_mb": 45.2, "wal_mode": true},
    "platform_db": {"connected": true, "size_mb": 1.3, "wal_mode": true}
  },
  "stations": {"running": 2, "paused": 0, "failed": 0},
  "think_py": {"last_run": "2026-03-25T13:15:00Z", "status": "ok"},
  "memory_mb": 128,
  "slow_queries_last_hour": 0
}
```

### Alerting

No external alerting in v1.0. The dashboard health widget surfaces:
- Database connection failures (red banner)
- think.py stale (>30min since last run)
- Station crashes (notification toast)
- Budget threshold breaches (warning banner)
- Slow query spikes (>5 per hour → yellow health indicator)
