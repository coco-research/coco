# CoCo Platform — Build Roadmap

**Version:** 1.0
**Created:** 2026-03-25
**Author:** Rijul Kalra (with AI assistance)
**Status:** Planning

---

## 1. Project Overview

### Vision

CoCo Platform is a local-first web application that provides a visual control plane for the existing CoCo + Knowledge Hub CLI system. It replaces the current Node/Express dashboard (`~/.coco/server.js`) with a full React 19 + FastAPI application, giving a solo PM a Paperclip-grade experience: project dashboards, station (AI agent) management, decision queues, knowledge browsing, chat, cost tracking, and more — all running on localhost.

The CLI workflow (`/coco`, CoCo SKILL.md, `think.py`, MCP tools) continues to work unchanged. The web UI is additive — it reads the same databases (`hub.db`, `coco.db`), the same JSON files (`brain.json`, `queue.json`, `config.json`), and the same event stream (`events.jsonl`). No data migration required.

### Success Criteria

1. **Replaces `server.js`** — all current dashboard functionality (events SSE, chat, skills, sessions) is available in the new app.
2. **Zero disruption** — existing CLI workflow, `think.py` cron, and MCP tools continue to work throughout and after build.
3. **Independently useful phases** — each phase ships something usable; no phase is wasted if we stop early.
4. **Sub-second local UX** — all reads from SQLite/JSON resolve in <200ms; SSE events appear within 1s.
5. **Single launch command** — `./scripts/dev.sh` starts both frontend and backend.

### Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Foundation | 3 days | 3 days |
| Phase 2: Backend Core | 4 days | 7 days |
| Phase 3: Dashboard | 4 days | 11 days |
| Phase 4: Station Management | 5 days | 16 days |
| Phase 5: Knowledge Hub Browser | 4 days | 20 days |
| Phase 6: Decision Queue | 3 days | 23 days |
| Phase 7: Chat Interface | 4 days | 27 days |
| Phase 8: Task Management | 4 days | 31 days |
| Phase 9: Cost & Budget | 3 days | 34 days |
| Phase 10: People & Learning | 4 days | 38 days |
| Phase 11: Todos & Settings | 3 days | 41 days |
| Phase 12: Polish & Production | 5 days | 46 days |

**Total estimate: ~50 working days (~10 weeks)**

---

## 2. Phase Breakdown

---

### Phase 1: Foundation (3 days)

**Goal:** Monorepo scaffolding, app shell with routing, dark theme, health check — a running app that shows a static dashboard layout.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 1.1 | Initialize monorepo root: `package.json` (workspaces), `.gitignore`, `.editorconfig`, `pyproject.toml` | 0.25d | |
| 1.2 | Scaffold `frontend/` with Vite + React 19 + TypeScript + Tailwind CSS 4 | 0.25d | `npm create vite@latest` |
| 1.3 | Install + configure Radix UI primitives, Radix Colors (dark theme), Radix Icons | 0.25d | |
| 1.4 | Scaffold `backend/` with FastAPI + uvicorn, `pyproject.toml`, virtualenv | 0.25d | |
| 1.5 | Create `scripts/dev.sh` — starts backend (uvicorn) + frontend (vite dev) concurrently | 0.25d | Uses `concurrently` or `&` with trap |
| 1.6 | App shell: sidebar nav (collapsible), top bar, `<Outlet/>` content area | 0.5d | React Router v7 |
| 1.7 | Route stubs for all pages: Dashboard, Stations, Knowledge, Decisions, Chat, Tasks, Costs, People, Todos, Settings | 0.25d | Placeholder components |
| 1.8 | FastAPI health check: `GET /api/health` returns `{ status: "ok", version, uptime }` | 0.25d | |
| 1.9 | Frontend API client: `fetch` wrapper with base URL, error handling, types | 0.25d | `frontend/src/lib/api.ts` |
| 1.10 | Static dashboard layout: 2-column grid with placeholder cards | 0.25d | |
| 1.11 | Vite proxy config: `/api/*` -> `localhost:8000` | 0.1d | |
| 1.12 | `.planning/` docs: this roadmap, `CLAUDE.local.md` for project memory | 0.1d | |

#### Acceptance Criteria
- [ ] `./scripts/dev.sh` starts both servers without errors
- [ ] Browser at `localhost:5173` shows dark-themed app shell with sidebar navigation
- [ ] Clicking sidebar links routes to correct page stubs
- [ ] `curl localhost:8000/api/health` returns 200 with JSON
- [ ] Frontend successfully calls `/api/health` and displays status
- [ ] Tailwind dark theme applied globally (no white flash)

#### Key Decisions
- **Port allocation:** Frontend dev = 5173 (Vite default), Backend = 8000 (uvicorn default)
- **CSS strategy:** Tailwind CSS 4 + Radix Colors for dark theme tokens
- **Router:** React Router v7 with layout routes

---

### Phase 2: Backend Core (4 days)

**Goal:** FastAPI serves real data from `hub.db`, `coco.db`, `brain.json`, and `queue.json`. REST endpoints for stations, tasks, projects. Database schema for stations.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 2.1 | `stations.db` schema design: `stations`, `station_logs`, `station_heartbeats`, `cost_events` tables | 0.5d | New SQLite DB at `~/.coco/stations.db` |
| 2.2 | Alembic setup for `stations.db` migrations | 0.25d | |
| 2.3 | Database connection layer: read-only connections to `hub.db` and `coco.db`, read-write to `stations.db` | 0.5d | Connection pool with WAL mode |
| 2.4 | JSON file readers: `brain.json`, `queue.json`, `config.json` with file-watch caching | 0.25d | `watchfiles` or mtime check |
| 2.5 | `GET /api/projects` — list projects from `hub.db:projects` | 0.25d | |
| 2.6 | `GET /api/projects/:id` — project detail with content counts, recent activity | 0.25d | |
| 2.7 | `GET /api/content` — paginated content from `hub.db:content` with filters (source, project, status, date range) | 0.5d | |
| 2.8 | `GET /api/content/:id` — full content item (body, entities, metadata) | 0.25d | |
| 2.9 | `GET /api/stations` — list stations from `stations.db` | 0.25d | |
| 2.10 | `POST/PATCH/DELETE /api/stations` — station CRUD | 0.25d | |
| 2.11 | `GET /api/queue` — read `queue.json` (items, deferred, auto-handled) | 0.15d | |
| 2.12 | `GET /api/brain/people` — people from `brain.json` | 0.15d | |
| 2.13 | `GET /api/brain/rules` — attention rules from `brain.json` | 0.1d | |
| 2.14 | `GET /api/config` — current CoCo config | 0.1d | |
| 2.15 | `PATCH /api/config` — update config.json (atomic write) | 0.15d | |
| 2.16 | `GET /api/todos` — todos from `hub.db:todos` | 0.15d | |
| 2.17 | `GET /api/drafts` — drafts from `hub.db:drafts` | 0.15d | |
| 2.18 | `GET /api/costs` — cost aggregation from `hub.db:api_costs` | 0.25d | |
| 2.19 | Pydantic models for all request/response schemas | 0.25d | |
| 2.20 | Error handling middleware + structured error responses | 0.15d | |

#### Acceptance Criteria
- [ ] `GET /api/projects` returns real projects from `hub.db`
- [ ] `GET /api/content?source=email&project=audit-board&limit=20` returns filtered content
- [ ] `GET /api/queue` returns current queue state
- [ ] `GET /api/brain/people` returns people graph from `brain.json`
- [ ] Station CRUD works: create station, list, update, delete
- [ ] `stations.db` created via Alembic migration on first run
- [ ] All endpoints return proper error codes (404 for missing, 422 for bad input)
- [ ] `hub.db` is opened read-only (no risk of corruption)

#### Key Decisions
- **Separate DB:** `stations.db` is a new file — we don't modify `hub.db` or `coco.db`
- **Read-only safety:** `hub.db` and `coco.db` opened with `?mode=ro` URI parameter
- **Caching:** `brain.json` and `queue.json` re-read on mtime change, cached in memory otherwise

---

### Phase 3: Dashboard (4 days)

**Goal:** The dashboard page shows live project cards, station status, activity feed, cost summary, and pending decisions badge — all using real data from Phase 2 endpoints.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 3.1 | `useQuery` / `useSWR` data fetching setup (or TanStack Query) | 0.25d | Centralized caching, revalidation |
| 3.2 | Project cards component: name, content count by source, last activity timestamp, health indicator | 0.5d | Grid layout, click to expand |
| 3.3 | Station status cards: name, state (idle/running/paused/dead), current task, uptime, last heartbeat | 0.5d | Color-coded status dot |
| 3.4 | SSE backend: `GET /api/events/stream` — tail `events.jsonl`, emit new events | 0.5d | Port from `server.js` to FastAPI |
| 3.5 | SSE client hook: `useEventSource` React hook | 0.25d | Auto-reconnect, parse JSON |
| 3.6 | Activity feed component: scrollable list of recent events, auto-updating via SSE | 0.5d | Event type icons, relative timestamps |
| 3.7 | Cost summary widget: total spend today / this week / this month, mini bar chart | 0.5d | Reads from `/api/costs` |
| 3.8 | Decisions pending badge: count from `/api/queue`, shown in sidebar + dashboard | 0.25d | Red badge if > 0 |
| 3.9 | Dashboard layout: responsive grid — projects row, stations row, activity + cost side by side | 0.25d | |
| 3.10 | Loading skeletons for all dashboard widgets | 0.25d | Radix Skeleton or custom shimmer |
| 3.11 | Auto-refresh: dashboard data polls every 30s, SSE for real-time events | 0.15d | |
| 3.12 | Empty states for all widgets (no projects, no stations, no events) | 0.1d | |

#### Acceptance Criteria
- [ ] Dashboard loads and displays real project data from Knowledge Hub
- [ ] Station cards show current state with color-coded indicators
- [ ] Activity feed updates in real-time via SSE (test by appending to `events.jsonl`)
- [ ] Cost widget shows aggregated costs with correct totals
- [ ] Pending decisions badge shows correct count from `queue.json`
- [ ] All widgets show loading skeletons while data loads
- [ ] Page is usable at 1280px and 1920px widths

#### Key Decisions
- **Data fetching:** TanStack Query for caching + background refetch
- **SSE implementation:** FastAPI `StreamingResponse` with `asyncio.Queue` per client
- **Chart library:** Defer to Phase 9; use simple HTML/CSS bar for cost summary here

---

### Phase 4: Station Management (5 days)

**Goal:** Full station lifecycle — create, configure, spawn (start a Claude Code background process), pause, kill, view logs. This is the core "Paperclip" feature.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 4.1 | Station list page: table/cards with status, task, uptime, actions | 0.5d | |
| 4.2 | Create station dialog: name, project assignment, system prompt template, model selection | 0.5d | Radix Dialog |
| 4.3 | Station detail page: config, current task, log viewer, cost, controls | 0.5d | |
| 4.4 | Process manager module (backend): spawn `claude` CLI as subprocess | 0.75d | `asyncio.create_subprocess_exec` |
| 4.5 | Process manager: capture stdout/stderr, write to `station_logs` table | 0.5d | Streaming capture |
| 4.6 | Process manager: pause (SIGSTOP) / resume (SIGCONT) / kill (SIGTERM) | 0.25d | |
| 4.7 | Heartbeat system: stations write heartbeat to `station_heartbeats` every 30s | 0.25d | Detect stale = no heartbeat for 2 min |
| 4.8 | Log viewer component: scrollable, auto-scroll, ANSI color rendering | 0.5d | `ansi-to-html` or similar |
| 4.9 | Spawn/pause/kill API endpoints with validation | 0.25d | |
| 4.10 | Station status SSE: emit station state changes on `/api/events/stream` | 0.25d | |
| 4.11 | Guard rails: max concurrent stations config, confirm before kill | 0.25d | |
| 4.12 | Station templates: pre-configured station types (researcher, coder, reviewer) | 0.25d | Stored in config |
| 4.13 | Edit station config (system prompt, model, working directory) | 0.25d | |

#### Acceptance Criteria
- [ ] Can create a new station with name, project, and system prompt
- [ ] "Spawn" button starts a real Claude Code process; stdout appears in log viewer
- [ ] "Pause" sends SIGSTOP; "Resume" sends SIGCONT; "Kill" sends SIGTERM
- [ ] Station status updates automatically (running -> idle -> dead)
- [ ] Heartbeat detects crashed stations (marks as "dead" after 2 min silence)
- [ ] Log viewer shows real-time output with ANSI colors rendered
- [ ] Cannot spawn more stations than `max_concurrent_stations` config value
- [ ] Station list reflects current state without manual refresh

#### Key Decisions
- **Process model:** Each station is a `claude --dangerously-skip-permissions -p "prompt"` subprocess managed by FastAPI
- **Log storage:** SQLite `station_logs` table (station_id, timestamp, level, message) — not files
- **Heartbeat:** Backend polls process status; no agent-side heartbeat needed initially

---

### Phase 5: Knowledge Hub Browser (4 days)

**Goal:** Browse all Knowledge Hub content — emails, voice memos, Jira tickets, Confluence pages — with filtering, search, and unsorted item classification.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 5.1 | Content list page: table with source icon, title, project, date, status columns | 0.5d | Sortable columns |
| 5.2 | Filter bar: source dropdown (email, voice, jira, confluence), project, date range, status (classified/unsorted/archived) | 0.5d | URL-synced filters |
| 5.3 | Search input: powered by FTS5 via `GET /api/content?q=search+term` | 0.25d | |
| 5.4 | Backend: FTS5 search endpoint using `hub.db:content_fts` | 0.25d | Highlight snippets with `snippet()` |
| 5.5 | Content detail view: full body rendering by source type | 0.5d | Email HTML, voice transcript, Jira fields, Confluence body |
| 5.6 | Email detail: from, to, date, subject, HTML body (sanitized), attachments list | 0.25d | `DOMPurify` for HTML |
| 5.7 | Voice memo detail: transcript text, duration, source file path, extracted action items | 0.25d | |
| 5.8 | Jira/Confluence detail: key fields, status, formatted body | 0.25d | |
| 5.9 | Entity sidebar: entities extracted from content (people, projects, action items) | 0.25d | From `content_entities` table |
| 5.10 | Unsorted items view: filter to `status=unsorted`, classify button per item | 0.25d | |
| 5.11 | Classify action: `POST /api/content/:id/classify` — assign project + status | 0.25d | |
| 5.12 | Pagination: cursor-based, 50 items per page | 0.25d | |
| 5.13 | Keyboard navigation: j/k to move through list, Enter to open detail | 0.25d | |

#### Acceptance Criteria
- [ ] Content list shows all items from `hub.db:content` with correct source icons
- [ ] Filtering by source, project, and date range works and updates URL
- [ ] FTS5 search returns relevant results with highlighted snippets
- [ ] Content detail renders email HTML safely (no XSS)
- [ ] Voice memo detail shows full transcript
- [ ] Unsorted items can be classified (assigned to project)
- [ ] Pagination works smoothly with 50-item pages
- [ ] j/k keyboard navigation works in list view

#### Key Decisions
- **Search:** Leverage existing `content_fts` FTS5 table in `hub.db` (read-only)
- **HTML sanitization:** `DOMPurify` on frontend for email bodies
- **Classification:** Calls backend which uses same logic as KH `reclassify` MCP tool

---

### Phase 5.5: Database Abstraction & Hub Sync (4 days)

**Goal:** Introduce SQLAlchemy Core as the database abstraction layer so the platform can target both SQLite (local/dev) and PostgreSQL (cloud/production). Mirror hub.db tables into platform's database so all reads come from one source. KH itself stays untouched — it continues writing to hub.db (SQLite) as before.

**Deployment note:** This phase is tested locally on SQLite for at least 2 weeks before any cloud/PostgreSQL deployment. The abstraction is in place but PostgreSQL is not required until cloud launch.

#### Architecture

```
LOCAL MODE (default, open-source):
  KH CLI -> hub.db (SQLite, unchanged)
  Sync daemon reads hub.db -> writes hub_* mirror tables into platform DB
  CoCo Platform reads from platform DB only (SQLite or PostgreSQL)

CLOUD MODE (future):
  KH CLI -> hub.db (local Mac)
  Sync daemon pushes hub.db deltas -> cloud PostgreSQL
  CoCo Platform reads from PostgreSQL only
```

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 5.5.1 | Add SQLAlchemy Core dependency + engine factory: `create_engine()` from `DATABASE_URL` env var (default: `sqlite:///~/.coco/platform.db`) | 0.25d | No ORM — Core only |
| 5.5.2 | Define SA Core `Table` metadata for all 37 existing platform.db tables | 0.5d | Mirror existing schema in `backend/app/db/tables.py` |
| 5.5.3 | Create connection manager: replaces `connections.py` with SA engine. `get_db()` returns SA connection. WAL + foreign keys via engine events | 0.25d | Backward compat: existing `get_platform_db()` delegates to new engine |
| 5.5.4 | Hub mirror tables: create `hub_content`, `hub_projects`, `hub_todos`, `hub_action_items`, `hub_drafts` in platform DB schema | 0.25d | Subset of hub.db schema — only tables platform reads |
| 5.5.5 | Hub sync service: `backend/app/services/hub_sync.py` — reads hub.db (read-only), diffs against `hub_sync_state` watermark table, upserts changed rows into `hub_*` tables | 0.5d | Runs on startup + every 60s via background task |
| 5.5.6 | Migrate Phase 2 routers (projects, health, dashboard) from raw sqlite3 to SA Core queries | 0.5d | Start with highest-traffic endpoints |
| 5.5.7 | Migrate hub.db reads: replace all `get_hub_db()` calls with reads from `hub_*` mirror tables | 0.5d | Remove direct hub.db dependency from routers |
| 5.5.8 | Update Alembic config: auto-generate migrations from SA Core metadata, support both SQLite and PostgreSQL | 0.25d | `alembic.ini` reads `DATABASE_URL` |
| 5.5.9 | Add `docker-compose.yml` with PostgreSQL service (for future use, not required locally) | 0.25d | `DATABASE_URL=postgresql://coco:coco@localhost/coco` |
| 5.5.10 | Integration tests: run full test suite against both SQLite and PostgreSQL (CI matrix) | 0.5d | `pytest --db=sqlite` and `pytest --db=postgres` |
| 5.5.11 | Update `init_db.py`: use SA Core `metadata.create_all()` instead of raw DDL. Keep backward compat migration logic | 0.25d | Idempotent — safe to run on existing DBs |

#### Acceptance Criteria
- [ ] `DATABASE_URL=sqlite:///...` works identically to current behavior (no regressions)
- [ ] `DATABASE_URL=postgresql://...` connects and all tables are created via Alembic
- [ ] Hub sync service mirrors hub.db content into `hub_*` tables within 60 seconds of changes
- [ ] No router imports `sqlite3` directly — all go through SA Core engine
- [ ] No router calls `get_hub_db()` — all hub reads come from `hub_*` mirror tables
- [ ] Test suite passes against both SQLite and PostgreSQL
- [ ] KH CLI is completely unmodified — hub.db schema and write patterns unchanged
- [ ] Existing `~/.coco/platform.db` data survives the migration (no data loss)

#### Key Decisions
- **SQLAlchemy Core, not ORM:** Dialect-agnostic SQL without mapped classes or identity maps. Core gives us `table.select().where(...)` that compiles to correct SQL for both dialects.
- **Hub sync, not direct read:** Decouples KH from Platform's database engine. KH stays on SQLite forever. Platform reads from one source (its own DB) regardless of engine.
- **Sync watermark:** `hub_sync_state` table tracks last-synced rowid/timestamp per hub table. Delta sync, not full copy.
- **Local-first testing:** Phase runs entirely on SQLite locally for at least 2 weeks. PostgreSQL validated in CI but not required for development. Cloud deployment is a separate future step.
- **60-second sync interval:** Acceptable lag for a dashboard. KH data is already minutes old (email/Jira polling).

#### Migration Strategy

Routers are migrated incrementally. During this phase, both patterns coexist:

```python
# OLD (removed by end of phase)
with get_hub_db() as db:
    row = db.execute("SELECT ... FROM todos WHERE id = ?", (tid,)).fetchone()

# NEW (SA Core — works on SQLite AND PostgreSQL)
with get_db() as conn:
    row = conn.execute(hub_todos.select().where(hub_todos.c.id == tid)).fetchone()
```

`get_hub_db()` is deprecated but not removed until all callers are migrated.

#### What stays unchanged
- `~/.hub/hub.db` — KH still owns this, still writes to it, schema unchanged
- `~/.coco/brain.json`, `queue.json`, `config.json` — JSON files stay as-is
- KH MCP tools — continue reading/writing hub.db directly
- `think.py` — continues reading hub.db directly

---

### Phase 6: Decision Queue (3 days)

**Goal:** Visual queue for items needing human decision — approve drafts, classify unsorted items, handle overdue todos, review health warnings.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 6.1 | Queue page layout: grouped by priority tier (urgent, drafts, classify, health, overdue) | 0.5d | Collapsible sections |
| 6.2 | Decision card component: item summary, context snippet, action buttons | 0.5d | |
| 6.3 | Draft decision cards: show draft title, project, preview; Approve / Reject / Edit buttons | 0.5d | |
| 6.4 | Classify decision cards: unsorted content with suggested project; Accept / Override / Skip | 0.25d | |
| 6.5 | Backend: `POST /api/queue/decide` — process decision (approve, reject, classify, defer) | 0.25d | Delegates to KH MCP tools or direct DB |
| 6.6 | Defer action: snooze item with resurface time (next session, 24h, 1 week) | 0.25d | Moves to `deferred` array in queue.json |
| 6.7 | Batch actions: select multiple items, bulk approve/reject/defer | 0.25d | |
| 6.8 | Queue badge: real-time count in sidebar nav | 0.1d | SSE-driven |
| 6.9 | Empty state: "All clear" celebration when queue is empty | 0.1d | |
| 6.10 | Auto-handled log: expandable section showing what `think.py` auto-handled since last session | 0.25d | From `queue.json:auto_handled_since_last_session` |
| 6.11 | Keyboard shortcuts: 1-4 for action buttons, n/p for next/prev card | 0.15d | |

#### Acceptance Criteria
- [ ] Queue page shows items grouped by priority tier
- [ ] Draft cards show preview; Approve writes to `hub.db:drafts`
- [ ] Classify cards allow project assignment
- [ ] Defer moves items to deferred list with resurface time
- [ ] Batch select + action works for 2+ items
- [ ] Queue badge in sidebar shows real-time count
- [ ] Auto-handled section shows what think.py processed
- [ ] Keyboard shortcuts (1-4, n/p) work on queue page

#### Key Decisions
- **Queue source:** Read from `queue.json` (populated by `think.py` every 15 min)
- **Decision execution:** Backend writes decisions back to `queue.json` and calls appropriate KH operations (approve_draft, reclassify, etc.)

---

### Phase 7: Chat Interface (4 days)

**Goal:** CoCo in the browser — a chat panel that talks to Claude API with full CoCo context (brain, projects, config) injected as system prompt.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 7.1 | Chat page layout: message list + input area, full-page or collapsible sidebar mode | 0.5d | Toggle between modes |
| 7.2 | Message components: user bubble, assistant bubble, system message | 0.25d | |
| 7.3 | Markdown rendering: tables, code blocks (syntax highlighted), lists, links | 0.5d | `react-markdown` + `rehype-highlight` |
| 7.4 | Backend: `POST /api/chat` — stream response via SSE | 0.5d | Uses `anthropic` Python SDK |
| 7.5 | System prompt construction: inject brain.json summary, active projects, config, queue summary | 0.5d | Same context as SKILL.md provides in CLI |
| 7.6 | Streaming display: tokens appear as they arrive | 0.25d | SSE chunks assembled client-side |
| 7.7 | Chat history: store in `coco.db` or new `chat_history` table in `stations.db` | 0.5d | Session-based grouping |
| 7.8 | Chat history sidebar: list of past conversations, click to load | 0.25d | |
| 7.9 | Context attachment: "Attach" button to include a content item, project, or draft as context | 0.5d | Adds to user message as structured block |
| 7.10 | Input: multi-line, Cmd+Enter to send, Shift+Enter for newline | 0.15d | |
| 7.11 | Copy code block button | 0.1d | |

#### Acceptance Criteria
- [ ] Chat sends message to Claude API and streams response in real-time
- [ ] System prompt includes brain.json people, active projects, config
- [ ] Markdown renders correctly: tables, code with syntax highlighting, lists
- [ ] Chat history persists and can be loaded from sidebar
- [ ] "Attach" button lets user include a KH content item as context
- [ ] Streaming tokens appear character-by-character (not waiting for full response)
- [ ] Cmd+Enter sends; Shift+Enter adds newline

#### Key Decisions
- **API key:** Read from environment variable `ANTHROPIC_API_KEY` (backend only; never sent to frontend)
- **Model:** Default `claude-sonnet-4-20250514`, configurable in settings
- **Context budget:** System prompt capped at ~4000 tokens; summarize brain.json if needed

---

### Phase 8: Task Management (4 days)

**Goal:** Task/issue CRUD with atomic checkout, versioned task documents, station assignment, and status workflow.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 8.1 | Tasks schema in `stations.db`: `tasks` table (id, title, description, status, assigned_station, project, priority, created_at, updated_at) | 0.25d | |
| 8.2 | Task documents table: `task_docs` (task_id, version, content, created_at) | 0.15d | |
| 8.3 | Task CRUD endpoints: `GET/POST/PATCH/DELETE /api/tasks` | 0.25d | |
| 8.4 | Atomic checkout: `POST /api/tasks/:id/checkout` — locks task to a station, prevents double-assignment | 0.25d | Optimistic locking with version field |
| 8.5 | Task list page: table with status, priority, assignee, project columns | 0.5d | Filterable, sortable |
| 8.6 | Task detail page: description (markdown), documents tab, activity log, assignment controls | 0.5d | |
| 8.7 | Task creation dialog: title, description (markdown editor), project, priority | 0.25d | |
| 8.8 | Status workflow: visual kanban-style columns (open, in_progress, review, done) or list with status chips | 0.5d | Drag-and-drop optional |
| 8.9 | Assign to station: dropdown of active stations, triggers checkout | 0.25d | |
| 8.10 | Task documents: view version history, diff between versions | 0.5d | |
| 8.11 | Link task to KH content: associate task with emails, voice memos that spawned it | 0.25d | |
| 8.12 | Bulk status update | 0.15d | |
| 8.13 | Task search | 0.15d | |

#### Acceptance Criteria
- [ ] Can create, edit, and delete tasks
- [ ] Atomic checkout prevents two stations from working the same task
- [ ] Status workflow: open -> in_progress -> review -> done transitions work
- [ ] Task documents store versions; can view version history
- [ ] Assign task to station triggers checkout automatically
- [ ] Task list is filterable by status, project, assignee
- [ ] Task detail shows linked KH content items

#### Key Decisions
- **Atomic checkout:** Row-level lock in SQLite using `locked_by` + `lock_version` fields; checkout increments version
- **Kanban vs. list:** Default is list view; kanban is a stretch goal within this phase

---

### Phase 9: Cost & Budget (3 days)

**Goal:** Track API costs per station and task, visualize spending over time, configure budget caps with threshold alerts.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 9.1 | Cost events schema: extend `stations.db` with `cost_events` (station_id, task_id, model, input_tokens, output_tokens, cost_usd, timestamp) | 0.25d | |
| 9.2 | Cost ingestion: parse station logs for API usage, insert cost events | 0.5d | Regex patterns for Claude output |
| 9.3 | Cost aggregation endpoints: by station, by task, by project, by time period | 0.25d | |
| 9.4 | Also read existing `hub.db:api_costs` for historical KH costs | 0.15d | |
| 9.5 | Cost dashboard page: total spend chart (line/area), breakdown by station (stacked bar), breakdown by project (donut) | 0.75d | Recharts |
| 9.6 | Budget config: `POST /api/config/budgets` — per-project daily/weekly/monthly caps | 0.25d | Stored in `config.json` or `stations.db` |
| 9.7 | Threshold alerts: when spend reaches 80% of budget, show warning in dashboard + decision queue | 0.25d | |
| 9.8 | Hard stop: when spend reaches 100%, auto-pause stations on that project | 0.25d | |
| 9.9 | Cost detail: click-through from chart to individual cost events | 0.25d | |
| 9.10 | Export: CSV download of cost events | 0.1d | |

#### Acceptance Criteria
- [ ] Cost events are recorded for every station API call
- [ ] Cost dashboard shows line chart of spend over time
- [ ] Breakdown by station and project renders as stacked bar / donut charts
- [ ] Budget caps can be set per project
- [ ] 80% warning appears in dashboard when threshold reached
- [ ] 100% hard stop pauses relevant stations
- [ ] Existing `api_costs` from hub.db appear in historical view
- [ ] CSV export works

#### Key Decisions
- **Chart library:** Recharts (React-native, composable, lightweight)
- **Cost parsing:** Extract from Claude CLI output format; may need adjustment as Claude CLI evolves
- **Budget storage:** In `stations.db:budgets` table (not config.json, as it needs structured queries)

---

### Phase 10: People & Learning (4 days)

**Goal:** Visualize the people graph from `brain.json`, teach/forget interface, trust matrix editor, attention rules viewer.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 10.1 | People list page: cards for each person (name, role, priority, projects, email patterns) | 0.5d | From `brain.json:people` |
| 10.2 | Person detail: full profile, communication patterns, frequency, typical topics | 0.25d | |
| 10.3 | Teach dialog: add new person (name, role, email pattern, projects, priority) | 0.5d | `PATCH /api/brain/people` |
| 10.4 | Forget action: remove person with confirmation | 0.15d | |
| 10.5 | Edit person: update role, projects, patterns | 0.25d | |
| 10.6 | Attention rules viewer: list all rules from `brain.json:attention_rules` | 0.5d | Show match conditions, actions, priority |
| 10.7 | Attention rule editor: create/edit/delete rules | 0.5d | Form with condition builder |
| 10.8 | Trust matrix: station x action grid (which stations can do what autonomously) | 0.75d | Grid component with toggles |
| 10.9 | Backend: `PATCH /api/brain` — atomic update of brain.json sections | 0.25d | Atomic write like think.py |
| 10.10 | People graph visualization: force-directed graph or relationship cards showing project connections | 0.5d | Optional: D3 force layout |

#### Acceptance Criteria
- [ ] People list shows all people from brain.json with key details
- [ ] Can teach (add) a new person; brain.json updates correctly
- [ ] Can forget (remove) a person with confirmation
- [ ] Attention rules display with readable condition descriptions
- [ ] Can create new attention rule via form
- [ ] Trust matrix grid renders; changes persist to config
- [ ] brain.json is written atomically (no corruption risk)

#### Key Decisions
- **Graph visualization:** Start with relationship cards (simpler); D3 force graph is a stretch goal
- **brain.json writes:** Use same `atomic_write_json` pattern as `think.py` (write to `.tmp`, rename)

---

### Phase 11: Todos & Settings (3 days)

**Goal:** Todo management with grouping and Jira promotion, settings page with config editor and autonomy mode controls.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 11.1 | Todo list page: grouped by project, filterable by status (pending, done, missed, dismissed) | 0.5d | From `hub.db:todos` |
| 11.2 | Quick actions: complete, dismiss, snooze, edit | 0.25d | |
| 11.3 | Add todo: title, project, due date, priority | 0.25d | Backend calls KH `todo_add` logic |
| 11.4 | Jira promotion: button to create Jira ticket from todo | 0.25d | Shows preview first (like KH `preview_jira_ticket`) |
| 11.5 | Jira promotion confirmation dialog with editable fields | 0.25d | |
| 11.6 | Backend: `POST /api/todos/:id/promote` — create Jira ticket | 0.25d | Uses Jira REST API |
| 11.7 | Settings page: display current `config.json` as editable form | 0.5d | Grouped sections |
| 11.8 | Autonomy mode toggle: CAREFUL / NORMAL / YOLO with description of what each mode allows | 0.25d | Updates `config.json:yolo` section |
| 11.9 | Display settings: max projects shown, collapse quiet projects, show cost, emoji toggle | 0.15d | |
| 11.10 | Auto-handle settings: confidence thresholds, noise dismissal, draft generation toggles | 0.25d | |
| 11.11 | Deferred resurface config: first/second/third timing | 0.1d | |

#### Acceptance Criteria
- [ ] Todo list shows all todos grouped by project
- [ ] Can complete, dismiss, snooze, and add todos
- [ ] Jira promotion shows preview, then creates ticket on confirm
- [ ] Settings page displays all config.json fields as editable form
- [ ] Autonomy mode toggle works and persists to config.json
- [ ] Auto-handle thresholds are configurable
- [ ] Changes to settings are reflected immediately (no restart needed)

#### Key Decisions
- **Jira integration:** Backend calls Jira REST API directly (same auth pattern as KH)
- **Config form:** Auto-generated from config.json schema where possible; manual for complex fields

---

### Phase 12: Polish & Production (5 days)

**Goal:** Keyboard shortcuts, command palette, responsive design, performance optimization, error handling, and a one-command launch script.

#### Tasks

| # | Task | Effort | Notes |
|---|------|--------|-------|
| 12.1 | Command palette: Cmd+K opens search across all entities (projects, content, tasks, people, pages) | 0.75d | Radix Command or cmdk |
| 12.2 | Global keyboard shortcuts: navigation (g+d = dashboard, g+s = stations, etc.), actions (n = new, e = edit) | 0.5d | Help overlay with `?` key |
| 12.3 | Responsive design: tablet (768px-1024px), mobile (< 768px) breakpoints | 0.5d | Collapsible sidebar, stacked layouts |
| 12.4 | Performance: lazy-load routes, virtualize long lists (react-window), optimize re-renders | 0.5d | |
| 12.5 | Error boundaries: graceful error handling per widget/page, retry buttons | 0.25d | |
| 12.6 | Offline/error states: "Backend unreachable" banner, auto-reconnect SSE | 0.25d | |
| 12.7 | Toast notifications: success/error/info for all actions | 0.25d | Radix Toast |
| 12.8 | Loading states audit: ensure all pages have proper loading/skeleton states | 0.25d | |
| 12.9 | Production build: Vite build, FastAPI static file serving, single-port mode | 0.5d | Backend serves frontend in prod |
| 12.10 | Launch script: `./scripts/start.sh` — creates venv if needed, installs deps, builds frontend, starts uvicorn | 0.5d | |
| 12.11 | launchd plist: optional auto-start on login (like `com.coco.think.plist`) | 0.25d | |
| 12.12 | Smoke test script: hits all API endpoints, verifies 200s | 0.25d | |
| 12.13 | Update README with setup instructions | 0.25d | |

#### Acceptance Criteria
- [ ] Cmd+K opens command palette; can search and navigate to any entity
- [ ] `?` shows keyboard shortcut overlay
- [ ] App is usable on iPad (1024px) and iPhone (375px) widths
- [ ] Long lists (1000+ items) render smoothly with virtualization
- [ ] Error boundary catches component crashes without killing the whole app
- [ ] "Backend unreachable" banner appears when FastAPI is down, disappears on reconnect
- [ ] `./scripts/start.sh` starts the full app from a clean checkout
- [ ] All 200 smoke tests pass

---

## 3. Dependency Graph

```
Phase 1: Foundation
    |
    v
Phase 2: Backend Core
    |
    +------------------+------------------+------------------+
    |                  |                  |                  |
    v                  v                  v                  v
Phase 3:           Phase 5:          Phase 7:           Phase 8:
Dashboard          KH Browser        Chat               Tasks
    |                  |                                    |
    v                  v                                    |
Phase 4:           Phase 5.5:                              |
Stations           DB Abstraction                          |
    |              & Hub Sync                               |
    |                  |                                    |
    |                  v                                    |
    |              Phase 6:                                 |
    |              Decision Queue                           |
    |                  |                                    |
    +------------------+------------------------------------+
    |
    v
Phase 9: Cost & Budget
    |
    v
Phase 10: People & Learning
    |
    v
Phase 11: Todos & Settings
    |
    v
Phase 12: Polish & Production
```

**Parallel opportunities:**
- Phases 3, 5, 7, and 8 can be built in parallel after Phase 2 (they share no dependencies)
- Phase 4 depends on Phase 3 (station cards on dashboard)
- Phase 5.5 depends on Phase 5 (needs hub.db read patterns to exist before abstracting them)
- Phase 6 depends on Phase 5.5 (classify actions use new SA Core queries and hub mirror tables)
- Phase 9 depends on Phases 4 + 8 (cost tracking needs stations + tasks)
- Phases 10 and 11 depend only on Phase 2 but are sequenced late because they are lower priority
- Phase 12 depends on all prior phases (polish pass)
- All phases after 5.5 benefit from SA Core — new queries are written DB-agnostic from the start

**Critical path:** 1 -> 2 -> 5 -> 5.5 -> 6 -> 9 -> 12 (30 days)

---

## 4. Risk Register

| Phase | Risk | Likelihood | Impact | Mitigation |
|-------|------|-----------|--------|------------|
| 1 | Tailwind CSS 4 breaking changes (still relatively new) | Medium | Low | Pin exact version; fall back to v3 if needed |
| 2 | `hub.db` schema changes from KH updates breaking queries | Medium | High | Version-check `schema_version` table on startup; abstract queries behind a DAO layer |
| 2 | SQLite concurrent access issues (think.py writes while backend reads) | Medium | High | WAL mode on all databases; read-only connections for hub.db and coco.db |
| 3 | SSE connection drops/memory leaks with long-running connections | Medium | Medium | Auto-reconnect client-side; server-side timeout + cleanup after 5 min idle |
| 4 | Claude CLI subprocess management unreliable on macOS | High | High | Start with simple spawn/kill; add watchdog process; log all process events for debugging |
| 4 | Claude CLI output format changes break log parsing | Medium | Medium | Loose regex patterns; fallback to raw text display |
| 5 | FTS5 search performance with large content sets | Low | Medium | Already indexed in hub.db; add LIMIT and pagination |
| 7 | Anthropic API key management / cost exposure | Medium | High | Key stored server-side only; never sent to frontend; rate limiting on chat endpoint |
| 7 | Chat context window overflow with large brain.json | Low | Medium | Summarize brain.json to ~2000 tokens; only include active projects |
| 8 | Atomic checkout race conditions in SQLite | Low | Medium | Use `BEGIN IMMEDIATE` transactions for checkout operations |
| 9 | Cost parsing from Claude CLI output unreliable | High | Medium | Start with manual cost entry; add auto-parse as enhancement; fall back to hub.db api_costs |
| 12 | Single-port production mode (FastAPI serving React) may need CORS/path config | Low | Low | Well-documented pattern; use `StaticFiles` mount |
| ALL | Scope creep on individual phases | High | High | Each phase has fixed acceptance criteria; defer "nice to haves" to Phase 12 or backlog |
| ALL | Existing CLI workflow breaks during development | Medium | Critical | Never modify hub.db/coco.db schemas; web app uses separate stations.db; all existing files read-only |

---

## 5. Success Metrics

### Per-Phase Completion Criteria

| Phase | "Done" means... |
|-------|-----------------|
| 1 | App shell renders at `localhost:5173`, routes work, health check passes, `dev.sh` starts both servers |
| 2 | All `/api/*` endpoints return real data from existing databases; station CRUD works; Pydantic validation catches bad input |
| 3 | Dashboard shows live project cards, station status, real-time activity feed, cost summary — all from real data |
| 4 | Can spawn a Claude Code process from the UI, see its output in real-time, pause it, and kill it |
| 5 | Can browse all KH content, filter by source/project, search with FTS5, view full content detail |
| 6 | Can process all queue items (approve drafts, classify content, defer items); queue empties correctly |
| 7 | Can chat with Claude in the browser with CoCo context; responses stream in real-time; history persists |
| 8 | Can create tasks, assign to stations with atomic checkout, track through status workflow |
| 9 | Cost chart shows real spend data; budget caps trigger warnings and auto-pause |
| 10 | Can view/edit people graph and attention rules; changes persist to brain.json |
| 11 | Can manage todos, promote to Jira, configure all settings from the UI |
| 12 | Cmd+K works, app is responsive, single launch command, all smoke tests pass |

### Overall Project Success

- **Usable replacement:** Rijul uses the web dashboard daily instead of (or alongside) the CLI
- **No regressions:** CLI workflow, think.py, MCP tools all continue working unchanged
- **Performance:** All pages load in <500ms; SSE events appear within 1s
- **Reliability:** App runs for 8+ hours without crashes or memory leaks

---

## 6. File/Folder Structure

```
coco-platform/
├── .planning/
│   ├── ROADMAP.md                  # This file
│   └── CLAUDE.local.md             # Project-level memory
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.tsx                # Entry point
│       ├── App.tsx                 # Root component with router
│       ├── index.css               # Tailwind imports + global styles
│       ├── lib/
│       │   ├── api.ts              # Fetch wrapper, base URL, error handling
│       │   ├── sse.ts              # useEventSource hook
│       │   └── utils.ts            # Formatting, date helpers
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.tsx
│       │   │   ├── TopBar.tsx
│       │   │   └── AppShell.tsx
│       │   ├── ui/                 # Shared primitives (Badge, Card, Button, etc.)
│       │   ├── dashboard/
│       │   │   ├── ProjectCard.tsx
│       │   │   ├── StationStatusCard.tsx
│       │   │   ├── ActivityFeed.tsx
│       │   │   └── CostSummary.tsx
│       │   ├── stations/
│       │   │   ├── StationList.tsx
│       │   │   ├── StationDetail.tsx
│       │   │   ├── LogViewer.tsx
│       │   │   └── CreateStationDialog.tsx
│       │   ├── knowledge/
│       │   │   ├── ContentList.tsx
│       │   │   ├── ContentDetail.tsx
│       │   │   ├── FilterBar.tsx
│       │   │   └── SearchInput.tsx
│       │   ├── decisions/
│       │   │   ├── QueuePage.tsx
│       │   │   ├── DecisionCard.tsx
│       │   │   └── DraftPreview.tsx
│       │   ├── chat/
│       │   │   ├── ChatPage.tsx
│       │   │   ├── MessageBubble.tsx
│       │   │   ├── ChatInput.tsx
│       │   │   └── ChatHistory.tsx
│       │   ├── tasks/
│       │   │   ├── TaskList.tsx
│       │   │   ├── TaskDetail.tsx
│       │   │   └── TaskDocuments.tsx
│       │   ├── costs/
│       │   │   ├── CostDashboard.tsx
│       │   │   ├── SpendChart.tsx
│       │   │   └── BudgetConfig.tsx
│       │   ├── people/
│       │   │   ├── PeopleList.tsx
│       │   │   ├── PersonDetail.tsx
│       │   │   ├── AttentionRules.tsx
│       │   │   └── TrustMatrix.tsx
│       │   ├── todos/
│       │   │   ├── TodoList.tsx
│       │   │   └── JiraPromoteDialog.tsx
│       │   └── settings/
│       │       ├── SettingsPage.tsx
│       │       └── AutonomyToggle.tsx
│       ├── pages/                  # Route-level components (thin wrappers)
│       │   ├── DashboardPage.tsx
│       │   ├── StationsPage.tsx
│       │   ├── KnowledgePage.tsx
│       │   ├── DecisionsPage.tsx
│       │   ├── ChatPage.tsx
│       │   ├── TasksPage.tsx
│       │   ├── CostsPage.tsx
│       │   ├── PeoplePage.tsx
│       │   ├── TodosPage.tsx
│       │   └── SettingsPage.tsx
│       └── types/
│           ├── api.ts              # Response types matching Pydantic models
│           ├── station.ts
│           ├── content.ts
│           ├── task.ts
│           └── brain.ts
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/              # Migration scripts
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app, middleware, lifespan
│       ├── config.py               # Settings, paths, env vars
│       ├── db/
│       │   ├── __init__.py
│       │   ├── connections.py      # SQLite connection pool (hub, coco, stations)
│       │   ├── models.py           # SQLAlchemy / raw schema definitions
│       │   └── migrations.py       # Alembic helpers
│       ├── services/
│       │   ├── __init__.py
│       │   ├── projects.py         # Project queries (hub.db)
│       │   ├── content.py          # Content queries + FTS5 search (hub.db)
│       │   ├── stations.py         # Station CRUD + process management
│       │   ├── process_manager.py  # Subprocess spawn/pause/kill
│       │   ├── queue.py            # Queue JSON reader + decision handler
│       │   ├── brain.py            # brain.json reader + writer
│       │   ├── chat.py             # Claude API chat with context injection
│       │   ├── tasks.py            # Task CRUD + atomic checkout
│       │   ├── costs.py            # Cost aggregation + budget checks
│       │   ├── todos.py            # Todo queries (hub.db)
│       │   └── config.py           # config.json reader + writer
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── health.py           # GET /api/health
│       │   ├── projects.py         # /api/projects
│       │   ├── content.py          # /api/content
│       │   ├── stations.py         # /api/stations
│       │   ├── queue.py            # /api/queue
│       │   ├── brain.py            # /api/brain
│       │   ├── chat.py             # /api/chat
│       │   ├── tasks.py            # /api/tasks
│       │   ├── costs.py            # /api/costs
│       │   ├── todos.py            # /api/todos
│       │   ├── config.py           # /api/config
│       │   └── events.py           # /api/events/stream (SSE)
│       └── schemas/
│           ├── __init__.py
│           ├── project.py          # Pydantic models for projects
│           ├── content.py          # Pydantic models for content
│           ├── station.py          # Pydantic models for stations
│           ├── task.py             # Pydantic models for tasks
│           ├── queue.py            # Pydantic models for queue
│           ├── brain.py            # Pydantic models for brain
│           ├── cost.py             # Pydantic models for costs
│           └── config.py           # Pydantic models for config
│
├── shared/
│   └── constants.py                # Shared constants (status enums, paths)
│
├── scripts/
│   ├── dev.sh                      # Start frontend + backend for development
│   ├── start.sh                    # Production start (build + serve)
│   ├── smoke-test.sh               # Hit all endpoints, verify 200s
│   └── setup.sh                    # First-time setup (venv, deps, migrations)
│
├── .gitignore
├── .env.example                    # ANTHROPIC_API_KEY, HUB_DB_PATH, etc.
├── README.md
└── package.json                    # Root workspace config
```

---

## Appendix A: Existing Data Sources

| Source | Path | Access Mode | Used By |
|--------|------|-------------|---------|
| Knowledge Hub DB | `~/.hub/hub.db` | Read-only | Phases 2, 3, 5, 6, 9, 11 |
| CoCo DB | `~/.coco/coco.db` | Read-only | Phase 2, 7 |
| Stations DB | `~/.coco/stations.db` | Read-write | Phases 2, 4, 8, 9 (NEW) |
| brain.json | `~/.coco/brain.json` | Read-write | Phases 2, 3, 7, 10 |
| queue.json | `~/.coco/queue.json` | Read-write | Phases 2, 3, 6 |
| config.json | `~/.coco/config.json` | Read-write | Phases 2, 7, 9, 11 |
| events.jsonl | `~/.coco/events.jsonl` | Read-only (tail) | Phases 3, 4 |
| Session files | `~/.coco/sessions/` | Read-only | Phase 7 |

## Appendix B: Key Database Tables

### hub.db (Knowledge Hub — read-only)
- `projects` — project definitions
- `content` — all ingested content (emails, voice, jira, confluence)
- `content_fts` — FTS5 index on content
- `entities` — extracted people, orgs, topics
- `content_entities` — content-entity join
- `drafts` — generated draft communications
- `todos` — todo items
- `api_costs` — historical API cost records
- `sync_state` — adapter sync timestamps

### coco.db (CoCo — read-only)
- `sessions` — CoCo CLI sessions
- `events` — session events
- `context` — session context snapshots
- `task_queue` — CLI task queue
- `skill_usage` — skill invocation history
- `intent_log` — user intent classification
- `session_summaries` — session summaries

### stations.db (NEW — read-write)
- `stations` — station definitions (id, name, project, system_prompt, model, status, pid, created_at)
- `station_logs` — stdout/stderr log lines (station_id, timestamp, level, message)
- `station_heartbeats` — heartbeat timestamps (station_id, timestamp, metadata)
- `tasks` — task/issue records (id, title, description, status, priority, project, assigned_station_id, locked_by, lock_version)
- `task_docs` — versioned task documents (task_id, version, content, created_at)
- `cost_events` — per-call cost records (station_id, task_id, model, input_tokens, output_tokens, cost_usd, timestamp)
- `budgets` — budget caps (project, period, cap_usd, current_usd)
- `chat_history` — chat messages (session_id, role, content, model, tokens, timestamp)

---

## Appendix C: Testing Strategy

Each phase includes test expectations. Tests run via `pytest` (backend) and `vitest` (frontend).

### Per-Phase Test Requirements

| Phase | Backend Tests | Frontend Tests |
|-------|--------------|----------------|
| 1 | Health endpoint returns 200. Vite proxy works. | App shell renders. Sidebar navigation routes correctly. |
| 2 | All GET endpoints return correct shape from real hub.db. Station CRUD round-trips. JSON file readers handle missing/corrupt files. hub.db opened read-only (write attempt raises). | N/A (no UI yet for these endpoints) |
| 3 | Dashboard aggregation returns correct counts. SSE stream emits events. | Project cards render with mock data. Activity feed appends new items. Loading skeletons appear. |
| 4 | Spawn creates real subprocess (use `echo` stub, not `claude`). Pause/resume sends correct signals. Heartbeat detects dead process. Max concurrent limit enforced. | Station card status updates. Log viewer renders ANSI. Spawn/kill buttons call correct endpoints. |
| 5 | FTS5 search returns ranked results. Pagination cursor works. Content filters compose correctly. | Filter bar updates URL params. Content list renders all source types. HTML sanitized in email view. |
| 6 | Queue assembly merges drafts + unsorted + health + overdue. Approve/reject/defer mutates queue.json correctly. | Decision cards render per tier. Batch select works. Keyboard shortcuts (a/r/d) fire correct actions. |
| 7 | Chat endpoint streams SSE chunks. System prompt includes brain summary. Chat history persists to DB. | Markdown renders tables and code blocks. Streaming tokens appear incrementally. Cmd+Enter sends. |
| 8 | Atomic checkout returns 409 on double-checkout. Task status transitions validate. Document versioning increments. | Task list filters work. Status workflow buttons transition correctly. |
| 9 | Cost aggregation sums correctly across stations/projects. Budget threshold triggers alert event. 100% cap pauses station. | Charts render with mock data. Budget bar shows correct percentage. CSV export downloads. |
| 10 | brain.json atomic write survives concurrent read. People CRUD round-trips. Rule cascade delete works. | People cards render. Teach input parses and confirms. Trust matrix grid toggles persist. |
| 11 | Todo CRUD round-trips. Jira promotion creates ticket (mock Jira API). Config write is atomic. | Todo list groups by project. Kanban drag updates status. Settings form auto-saves. |
| 12 | Smoke test script hits all endpoints. | Cmd+K palette opens and searches. Responsive layout at 768px and 375px. Error boundary catches thrown component. |

### Test Infrastructure

- **Backend:** `pytest` + `pytest-asyncio` + `httpx` (async test client for FastAPI). Fixtures create temp SQLite DBs with seed data.
- **Frontend:** `vitest` + `@testing-library/react`. MSW (Mock Service Worker) for API mocking.
- **Integration:** `scripts/smoke-test.sh` — curl-based script hitting every endpoint, verifying 200s and response shapes.
- **No E2E (Playwright) in v1.0.** Defer to v1.1 polish phase. Manual testing covers UI flows.

---

## Appendix D: Git Strategy

### Repository

Single git repo at `~/projects/coco-platform/`. Initialized in Phase 1.

### Branching

- `main` — stable, always runnable. Each phase merges here when acceptance criteria pass.
- `phase/{N}-{name}` — feature branches per phase (e.g., `phase/3-dashboard`, `phase/4-stations`).
- No PRs (solo developer). Direct merge to main after self-review.

### Commit Convention

```
{phase}.{task}: {description}

Examples:
1.6: app shell with sidebar nav and routing
2.5: GET /api/projects endpoint with hub.db read-only
4.4: process manager spawn with subprocess.Popen
```

### .gitignore

```
node_modules/
__pycache__/
*.pyc
.venv/
backend/static/
*.db
.env
```

### CI

No CI pipeline in v1.0 (local-only project). `scripts/smoke-test.sh` serves as the gate before merging to main. Lint on save via editor config.
