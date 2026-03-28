# CoCo Platform — Comprehensive Feature Specification

> **Version:** 1.0-draft
> **Date:** 2026-03-25
> **Author:** Rijul Kalra
> **Status:** Product Bible — living document

---

## Table of Contents

1. [Feature Matrix](#1-feature-matrix)
2. [Page-by-Page Specification](#2-page-by-page-specification)
3. [New Features (CoCo-Only)](#3-new-features-coco-only)
4. [Feature Phases](#4-feature-phases)
5. [Non-Goals](#5-non-goals)

---

## 1. Feature Matrix

Complete mapping of every Paperclip feature to its CoCo Platform equivalent.

### 1.1 Dashboard and Navigation

| Feature | Paperclip | CoCo Platform | Priority | Notes |
|---|---|---|---|---|
| Multi-entity switcher | Company switcher with logos | **Project switcher** — dropdown with 9 active projects (AuditBoard, AB Tax, TCRE, Optimize, etc.). No multi-company; single user, multi-project. | P0 | Replace "company" concept with "project focus" throughout |
| Main dashboard | Agent cards with status, last action, cost | **Command center** — unified dashboard showing decision queue count, source health (email/voice/jira/conf), project activity sparklines, cost ticker, recent session log | P0 | Mirrors `/coco` activation dashboard in web form |
| Activity feed | Real-time SSE updates of agent actions | **Activity stream** — real-time feed of ingested content, auto-classifications, draft generations, todo completions. SSE from KH server | P0 | Sources: content table inserts, drafts table changes, todos table changes |
| Cost summary | Charts per agent, per project, per model | **Cost dashboard** — charts per feature (triage/classify/synthesize/embed), per project, per model (Haiku/Sonnet/Opus), per time period | P1 | Data from `api_costs` table. Replace "per agent" with "per feature" |
| Navigation sidebar | Company list, dashboard, agents, issues, settings | **Sidebar:** Home, Projects, Inbox (unsorted), Decision Queue, Drafts, Todos, People, Knowledge Search, Cost, Settings | P0 | Sidebar items map 1:1 to CoCo commands |
| Settings page | Company settings, API keys | **Settings:** Autonomy mode, config.json editor, adapter health, scheduler controls, brain.json viewer | P1 | Wraps `~/.coco/config.json` and `~/.coco/brain.json` |

### 1.2 Agent Management

| Feature | Paperclip | CoCo Platform | Priority | Notes |
|---|---|---|---|---|
| Create/edit agents | Name, role, title, model preference | **Not applicable.** CoCo is a single-agent system (CoCo itself). Replace with **People Graph management** — add/edit people CoCo tracks (name, role, projects, priority, email patterns, transcription aliases) | P0 | People are stakeholders CoCo monitors, not autonomous agents |
| Org chart visualization | Tree hierarchy of agents | **People graph visualization** — network graph showing people, their projects, priority levels, and communication patterns | P1 | Uses `brain.json` people data + content_entities relationships |
| Agent status | Active, paused, terminated | **Adapter health status** — each source (email, voice, jira, confluence) has green/yellow/red status. Plus **CoCo scheduler status** (running/stopped/errored) | P0 | Maps to `sync_state` table |
| Agent API keys | Long-lived + run JWTs | **API authentication** — single user auth (JWT for web app sessions). No multi-agent key management needed | P1 | Simple auth; no agent-level keys |
| Heartbeat protocol | 9-step identity/checkout/work/delegate | **Think pass** — background 15-min cycle: scan new content, classify, queue decisions, update todos. Viewable in scheduler status page | P0 | Maps to `think.py` + launchd scheduler |
| Agent routines | Scheduled heartbeats (cron-like) | **Scheduler management** — install/uninstall/status of launchd think pass. Configure interval. View recent logs | P1 | Wraps `/coco scheduler` commands |
| Invoke agent manually | Trigger heartbeat on demand | **Manual process** — "Run Now" button that triggers ingest + process pipeline on demand | P0 | Maps to `/coco process` |

### 1.3 Task and Issue Management

| Feature | Paperclip | CoCo Platform | Priority | Notes |
|---|---|---|---|---|
| Create issues | Title, description, priority, labels | **Todos** — create with title, description, priority (high/medium/low), project, owner, due date, tags, source type | P0 | Maps to `todos` table |
| Assign to agents | Agent assignment pool | **Assign to people** — owner field on todos. People come from brain.json graph | P0 | Single user system; "owner" is for tracking delegation |
| Atomic checkout | 409 Conflict if already assigned | **Not applicable.** Single user, no concurrent agents | -- | Skip entirely |
| Issue documents | Versioned text artifacts | **Drafts** — versioned text artifacts attached to source content. Template + section targeting for Confluence | P0 | Maps to `drafts` table (pending/approved/rejected/applied) |
| Issue comments | Threaded comments | **Not in v1.** Could add notes to todos later | P2 | Low value for solo PM |
| File attachments | Multipart upload/download | **Content attachments** — voice memos (source_path), email attachments, ingested files. View/download from content detail page | P1 | Maps to `content.source_path` and metadata JSON |
| Issue status workflow | open -> in_progress -> review -> done | **Todo status workflow:** open -> done / jira-created / dismissed. **Draft status workflow:** pending -> approved / rejected -> applied. **Content status workflow:** ingested -> preprocessed -> triaged -> classified -> synthesized -> complete / failed | P0 | Three separate workflows, all richer than Paperclip's single flow |

### 1.4 Cost and Budget

| Feature | Paperclip | CoCo Platform | Priority | Notes |
|---|---|---|---|---|
| Per-agent cost events | Tokens, model, provider | **Per-feature cost events** — tokens (input/output/cache_read/cache_write), model, feature name, linked content_id | P0 | Maps to `api_costs` table. More granular than Paperclip (cache tokens tracked) |
| Monthly budgets | Per-company in cents | **Monthly budget** — single budget threshold in config.json. Alert at 80%, pause at 100% | P1 | Add `budget_monthly_usd` to config.json |
| 80% soft alert | Notification | **Dashboard warning banner** — yellow at 80% of monthly budget | P1 | Visual indicator on cost page and dashboard |
| 100% hard stop | Auto-pause agent | **Processing pause** — auto-pause triage/synthesis (expensive operations) but keep ingestion running | P1 | Graceful degradation, not full stop |
| Cost breakdown | By agent, project, model, time | **Cost breakdown** — by feature, project (via content_id join), model, time period. Daily/weekly/monthly/custom views | P0 | Richer than Paperclip: feature-level and cache token visibility |
| Cost charts | Trends over time | **Cost charts** — line chart (daily spend), stacked bar (by model), pie (by feature), table (by project). Sparklines on dashboard | P1 | Chart.js or Recharts |

### 1.5 Governance

| Feature | Paperclip | CoCo Platform | Priority | Notes |
|---|---|---|---|---|
| Board approval gates | Before agent hires, strategy changes | **Autonomy mode gates** — CAREFUL mode requires approval for every action; NORMAL auto-handles above 0.85 confidence; YOLO auto-handles most actions. Visual trust matrix shows what each mode permits | P0 | Maps to CoCo's 3-mode autonomy system. More nuanced than Paperclip's binary gate |
| Activity audit trail | Log of all actions | **Session history** — full log of every command, MCP tool call, decision made, item deferred. Stored in `~/.coco/sessions/*.json` | P0 | Already implemented in CoCo session logging |
| Config revisions with rollback | Version history of config | **Config versioning** — track changes to config.json and brain.json with timestamps. Diff view. Rollback button | P2 | Nice to have; git-like versioning of JSON files |

### 1.6 Projects and Goals

| Feature | Paperclip | CoCo Platform | Priority | Notes |
|---|---|---|---|---|
| Goal hierarchy | Company goal -> sub-goals -> tasks | **Project hierarchy** — project -> action items -> todos -> Jira tickets. No formal "goal" object; projects ARE the goals | P1 | Simpler model than Paperclip; PM knows goals implicitly |
| Project grouping | Group projects | **Project list with metadata** — name, Jira key, Confluence space, item count, active/inactive, health indicators | P0 | Maps to `projects` table |
| Company import/export | JSON export | **Full backup/restore** — export hub.db + brain.json + config.json + queue.json as single archive. Import to new machine | P2 | Migration support for moving between machines |

---

## 2. Page-by-Page Specification

### 2.1 Home / Command Center

**Route:** `/`

**What it shows:**
- CoCo logo and current date/time
- "Since last session" delta: time elapsed, new items per source
- Source health indicators (4 colored dots: email, voice, Jira, Confluence)
- Decision queue badge with count of pending items
- Attention items: unsorted count, pending drafts count, overdue action items count, health issues count
- Project activity summary: top 6 projects with bar chart of item counts, sparklines of recent activity
- Cost ticker: current month spend vs budget
- Quick action buttons: Process Now, Open Decision Queue, View Briefing
- Recent activity stream (last 20 events)

**User interactions:**
- Click any project to navigate to project detail page
- Click source health indicator to navigate to health page
- Click decision queue badge to navigate to decision queue
- "Process Now" button triggers full ingest + process pipeline
- Activity stream auto-scrolls; click any item to see detail
- Project switcher dropdown to set focus (applies globally to all pages)

**Data sources:**
- `GET /api/dashboard` — aggregates from content, projects, project_content, sync_state, drafts, todos tables
- `GET /api/health` — from sync_state table
- `GET /api/cost/summary?days=30` — from api_costs table
- `GET /api/sessions/latest` — from `~/.coco/sessions/` directory
- `SSE /api/events` — real-time stream of content inserts, classification events, draft status changes

**Real-time updates:**
- SSE connection for activity stream (new content ingested, classifications, draft approvals)
- Polling every 60s for health status and queue count badge
- Cost ticker updates on every SSE event that includes cost data

---

### 2.2 Projects List

**Route:** `/projects`

**What it shows:**
- Grid or list view of all projects (toggle)
- Each project card shows: name, Jira key, Confluence space, total items, items by source (email/voice/jira/conf), active/inactive badge, last activity timestamp
- Inactive projects collapsed at bottom
- "Add Project" button
- Sort controls: by name, by item count, by last activity

**User interactions:**
- Click project card to navigate to project detail
- Toggle active/inactive on each project
- Add new project: modal with name, Jira key (optional), Confluence space (optional), folder path (optional)
- Deactivate project: confirmation modal, marks as inactive but preserves data
- Drag-and-drop reorder (saved to display preferences)

**Data sources:**
- `GET /api/projects` — from projects table with aggregated counts from project_content, content
- `POST /api/projects` — insert into projects table
- `PATCH /api/projects/:id` — update projects table (name, jira_key, confluence_space, active flag)

**Real-time updates:**
- SSE for item count badges (increment when new content classified to project)

---

### 2.3 Project Detail

**Route:** `/projects/:projectId`

**What it shows:**
- Project header: name, Jira key (linked), Confluence space (linked), active status
- Tabs: Overview | Content | Action Items | Drafts | Todos | Classification Rules
- **Overview tab:**
  - Item counts by source (4 cards with counts and mini trends)
  - Recent activity timeline (last 30 events for this project)
  - Overdue action items (highlighted)
  - Active Jira tickets summary
  - Recent Confluence page updates
- **Content tab:**
  - Filterable, sortable table of all content items classified to this project
  - Columns: title, source, status, relevance score, date, actions
  - Source filter (email/voice/jira/confluence)
  - Status filter (ingested through complete)
  - Full-text search within project
  - Click row to expand and see full content
- **Action Items tab:**
  - List grouped by: OVERDUE, THIS WEEK, LATER
  - Each item: description, owner, due date, source content link
  - Inline actions: mark done, defer, create Jira ticket
- **Drafts tab:**
  - List of drafts targeting this project's Confluence templates
  - Each draft: template, section, status, created date, source content link
  - Actions: approve, reject, view full content, diff against current Confluence content
- **Todos tab:**
  - Kanban or list of todos for this project
  - Drag between columns: Open | Done | Jira Created | Dismissed
  - Inline edit: title, priority, due date, owner
  - "Create from action item" button
  - "Push to Jira" button (preview then create)
- **Classification Rules tab:**
  - Learned rules from `learned_rules` table for this project
  - Attention rules from `brain.json` targeting this project
  - Hit count for each rule
  - Add/edit/delete rules
  - Test a rule against recent unsorted content

**Data sources:**
- `GET /api/projects/:id` — project metadata from projects table
- `GET /api/projects/:id/content?source=&status=&q=&page=&limit=` — from content + project_content join
- `GET /api/projects/:id/action-items` — from content where metadata contains action items, filtered by project
- `GET /api/projects/:id/drafts` — from drafts table filtered by project_id
- `GET /api/projects/:id/todos` — from todos table filtered by project_id
- `GET /api/projects/:id/rules` — from learned_rules + brain.json attention_rules
- `PATCH /api/todos/:id` — update todo status, priority, etc.
- `POST /api/todos/:id/jira` — create Jira ticket from todo
- `POST /api/drafts/:id/approve` — approve draft
- `POST /api/drafts/:id/reject` — reject draft

**Real-time updates:**
- SSE filtered to project scope: new content, draft status changes, todo updates

---

### 2.4 Inbox (Unsorted Content)

**Route:** `/inbox`

**What it shows:**
- List of all content items not yet classified to a project (status in 'ingested', 'preprocessed', 'triaged' without project_content entry, or with low confidence)
- Each item shows: title, source icon, date, snippet of raw_text (first 200 chars), suggested project (if triage produced one), confidence score
- Bulk action toolbar at top
- Count badge synced with sidebar

**User interactions:**
- Click item to expand full content in a side panel
- Classify: dropdown to assign to a project (creates project_content entry)
- Dismiss: mark as noise/irrelevant (sets status to 'complete' with relevance_score = 0)
- Bulk select (checkboxes) + bulk classify or dismiss
- Auto-suggest: if CoCo's attention rules match, show suggested project with "Accept" button
- "Process All" button to run triage on untriaged items
- Sort by: date, source, suggested project
- Filter by: source type

**Data sources:**
- `GET /api/inbox?source=&sort=&page=&limit=` — content LEFT JOIN project_content WHERE project_content IS NULL or confidence < threshold
- `POST /api/content/:id/classify` — insert/update project_content, update content status
- `POST /api/content/:id/dismiss` — update content status and relevance_score
- `POST /api/inbox/bulk-classify` — batch operation
- `POST /api/inbox/process` — trigger triage on unprocessed items

**Real-time updates:**
- SSE for new unsorted items arriving (from ingestion)
- Badge count updates on classify/dismiss

---

### 2.5 Decision Queue

**Route:** `/decide`

**What it shows:**
- Prioritized queue matching CoCo's `/coco decide` output, rendered as interactive cards
- Sections (shown only if non-empty):
  1. **URGENT** — items from high-priority people (red left border)
  2. **DRAFTS** — pending draft approvals (blue left border)
  3. **CLASSIFY** — unsorted items needing project assignment (yellow left border)
  4. **HEALTH** — adapter issues (orange left border)
  5. **OVERDUE** — past-due action items (red left border)
- Each card shows: summary, project context, source, time since creation, available actions
- Progress bar at top: "N items remaining"
- Session stats: "Processed X items this session (Y approved, Z classified, W dismissed)"

**User interactions:**
- **Draft cards:** Approve / Reject / Show Full Content buttons. "Show" opens side panel with full draft text and diff against current Confluence content
- **Classify cards:** Project dropdown (pre-populated with suggestions based on attention rules). "Accept Suggestion" if auto-classified
- **Health cards:** "Fix" (triggers re-sync for that adapter) / "Skip" buttons
- **Overdue cards:** "Act Now" (opens detail) / "Defer" / "Dismiss" buttons
- **Batch mode:** "Approve All Drafts" / "Accept All Suggestions" buttons at section level
- **Defer:** Moves item to deferred queue with aging rules (resurface next session / 24h / flag as stale)
- Keyboard shortcuts: `a` = approve, `r` = reject, `d` = defer, `s` = skip, `j/k` = navigate cards

**Data sources:**
- `GET /api/queue` — assembled from drafts (status=pending), content (unsorted), sync_state (red), action items (overdue). Cross-referenced with brain.json for priority classification
- `POST /api/queue/:id/action` — body: `{ action: "approve|reject|classify|defer|dismiss|fix", project?: string }`
- `GET /api/queue/deferred` — from queue.json deferred array
- `GET /api/drafts/:id` — full draft content for "Show" action

**Real-time updates:**
- SSE for queue item count changes
- Optimistic UI: card animates out on action, count decrements immediately

---

### 2.6 Drafts

**Route:** `/drafts`

**What it shows:**
- Filterable list of all drafts across projects
- Tabs or filters: Pending | Approved | Rejected | Applied | All
- Each draft row: ID, project name, source content title, target template, target section, format, status, created date, reviewed date
- Pending count badge on "Pending" tab

**User interactions:**
- Click draft to open detail view (side panel or full page)
- Detail view shows: full generated content, source content it was derived from, target template/section, diff view against current Confluence content (if available)
- Approve / Reject buttons with optional note
- "Approve All Pending" bulk action
- "Push to Confluence" for approved drafts (creates/updates Confluence page)
- Filter by project, template, date range
- Search within draft content

**Data sources:**
- `GET /api/drafts?status=&project=&template=&q=&page=&limit=` — from drafts table with project join
- `GET /api/drafts/:id` — single draft with full content
- `POST /api/drafts/:id/approve` — update status to 'approved', set reviewed_at
- `POST /api/drafts/:id/reject` — update status to 'rejected', set reviewed_at
- `POST /api/drafts/:id/push` — call Confluence API to update page, set status to 'applied'

**Real-time updates:**
- SSE for new drafts generated by processing pipeline
- Badge count on pending tab

---

### 2.7 Todos

**Route:** `/todos`

**What it shows:**
- Kanban board with 4 columns: Open | Done | Jira Created | Dismissed
- OR list view (toggle) with sortable/filterable table
- Each todo card: title, project badge, priority indicator (color), owner, due date, source type icon, tags
- Overdue items highlighted in red
- Filters: by project, priority, owner, source type, due date range
- "Sync from Action Items" button (pulls new action items from KH, deduplicates)

**User interactions:**
- Drag cards between columns (updates status)
- Click card to open edit modal: title, description, project, owner, priority, due date, tags
- "Add Todo" button: manual creation form
- "Push to Jira" on individual cards: preview modal showing Jira ticket fields, then create
- "Bulk Push to Jira" for all high-priority open todos
- Inline priority toggle (click to cycle high/medium/low)
- Search across all todos

**Data sources:**
- `GET /api/todos?status=&project=&priority=&owner=&sort=&page=&limit=` — from todos table
- `POST /api/todos` — insert new todo
- `PATCH /api/todos/:id` — update fields (status, priority, title, etc.)
- `DELETE /api/todos/:id` — soft delete (set status to dismissed)
- `POST /api/todos/:id/jira` — preview Jira ticket, then create via Jira API, update jira_key field
- `POST /api/todos/sync` — pull action items from content, deduplicate, insert new todos
- `POST /api/todos/bulk-jira` — batch Jira creation for filtered set

**Real-time updates:**
- SSE for todo status changes (from CLI or background processing)
- Due date countdowns update in real-time

---

### 2.8 People Graph

**Route:** `/people`

**What it shows:**
- Interactive network visualization (D3 force-directed or similar)
  - Center node: Rijul (self)
  - Connected nodes: all people in brain.json
  - Node size: proportional to number of content items associated
  - Node color: by priority (red=high, yellow=medium, gray=low)
  - Edge thickness: proportional to communication frequency
  - Edge labels: projects in common
- Side panel (on node click): person detail card
- Table view toggle: sortable list of all people with role, priority, projects, email patterns, transcription aliases, last seen

**User interactions:**
- Click node to select person and show detail in side panel
- Detail panel shows:
  - Name, role, priority, projects
  - Email patterns (for auto-classification)
  - Transcription aliases (for voice memo matching)
  - Recent content involving this person (last 10 items)
  - Communication frequency chart (emails/week over time)
- "Add Person" button: form with name, role, priority, projects, email patterns
- "Edit" on selected person: modify all fields
- "Delete" on selected person: remove from brain.json (with confirmation)
- "Teach" freeform: text input that parses natural language rules (mirrors `/coco teach`)
- Graph layout controls: zoom, pan, reset, toggle labels
- Filter graph by project

**Data sources:**
- `GET /api/people` — from brain.json people object
- `GET /api/people/:id` — single person with associated content from content_entities
- `POST /api/people` — add to brain.json
- `PATCH /api/people/:id` — update in brain.json
- `DELETE /api/people/:id` — remove from brain.json
- `GET /api/people/:id/content?limit=` — content items linked via entities table
- `POST /api/people/teach` — natural language rule parsing (mirrors CoCo teach)

**Real-time updates:**
- None needed (people graph changes infrequently)

---

### 2.9 Knowledge Search

**Route:** `/search`

**What it shows:**
- Full-page search interface
- Large search bar at top with filters below: source type, project, date range, content status
- Results list: title, source icon, project badge, date, relevance score, snippet with highlighted search terms
- Result count and pagination
- "No results" state with suggestions

**User interactions:**
- Type query to search (debounced, 300ms)
- Click result to expand inline or navigate to content detail
- Filter toggles update results in real-time
- "Search within project" shortcut when project focus is set
- Export results (CSV/JSON)
- Semantic search toggle (uses content_vec embeddings) vs keyword search (uses content_fts)

**Data sources:**
- `GET /api/search?q=&source=&project=&from=&to=&status=&mode=keyword|semantic&page=&limit=` — keyword mode queries content_fts; semantic mode queries content_vec
- `GET /api/content/:id` — full content detail on click

**Real-time updates:**
- None (search is on-demand)

---

### 2.10 Content Detail

**Route:** `/content/:contentId`

**What it shows:**
- Full content view for any content item
- Header: title, source icon and label, ingested date, status badge, relevance score
- Body: raw_text (collapsible) and processed_text (primary view)
- Metadata panel: all fields from metadata JSON (sender, recipients, attachments, duration for voice, etc.)
- Project classification: which project(s) this belongs to, confidence score, classification method
- Related items:
  - Entities extracted (people, topics, projects linked via content_entities)
  - Drafts generated from this content
  - Todos created from this content
  - Other content items with shared entities
- Processing timeline: status progression with timestamps (ingested_at -> processed_at)
- For voice content: audio player (if source_path points to audio file), transcript viewer with speaker labels

**User interactions:**
- Reclassify: change project assignment
- Reprocess: re-run triage/classification/synthesis
- Create todo from content
- Create Jira ticket from content
- Generate draft from content
- Mark as noise (set relevance_score to 0)
- Edit processed_text (manual corrections)
- Copy content to clipboard

**Data sources:**
- `GET /api/content/:id` — from content table with all fields
- `GET /api/content/:id/classification` — from project_content join
- `GET /api/content/:id/entities` — from content_entities + entities join
- `GET /api/content/:id/drafts` — from drafts where source_content_id = id
- `GET /api/content/:id/todos` — from todos where source_content_id = id
- `POST /api/content/:id/reclassify` — update project_content
- `POST /api/content/:id/reprocess` — trigger pipeline re-run
- `GET /api/content/:id/audio` — serve audio file for voice content

**Real-time updates:**
- SSE for status changes during reprocessing

---

### 2.11 Cost Dashboard

**Route:** `/cost`

**What it shows:**
- Summary cards at top: total spend this month, daily average, projected monthly, budget remaining (% and $)
- Budget progress bar with yellow (80%) and red (100%) markers
- Charts section:
  - **Daily spend** — line chart, last 30 days
  - **By model** — stacked bar chart (Haiku / Sonnet / Opus) per day
  - **By feature** — pie chart (triage / classify / synthesize / embed / search)
  - **By project** — horizontal bar chart (spend per project via content_id join)
  - **Token efficiency** — cache hit ratio over time (cache_read_tokens / total_input_tokens)
- Detailed table: every cost event, sortable by date, model, feature, tokens, cost
- Date range selector: 7d / 30d / 90d / custom

**User interactions:**
- Click chart segments to filter table to that dimension
- Export table as CSV
- Set monthly budget (input field, saves to config.json)
- Toggle between USD and token views
- Hover on chart points for detailed tooltips

**Data sources:**
- `GET /api/cost?days=&groupBy=feature|model|project|day` — aggregated from api_costs table
- `GET /api/cost/events?from=&to=&model=&feature=&page=&limit=` — raw events from api_costs
- `GET /api/cost/summary` — current month total, daily average, projection
- `GET /api/cost/budget` — from config.json budget_monthly_usd field
- `PATCH /api/cost/budget` — update config.json budget_monthly_usd

**Real-time updates:**
- SSE for new cost events (updates summary cards and chart data points)

---

### 2.12 Health and Adapters

**Route:** `/health`

**What it shows:**
- Adapter status cards (one per source: email, voice, Jira, Confluence):
  - Status indicator (green/yellow/red/off circle)
  - Last successful sync timestamp
  - Last failure timestamp and error message (if any)
  - Items synced count (lifetime)
  - Unsorted items count for this source
  - "Sync Now" button
- Scheduler status:
  - Running/stopped indicator
  - Last think pass timestamp and duration
  - Next scheduled run
  - Recent log output (last 20 lines of think.log)
- System info:
  - hub.db size and path
  - brain.json last modified
  - config.json last modified
  - Session count

**User interactions:**
- "Sync Now" per adapter (triggers ingest for that source)
- "Sync All" button (triggers full ingest)
- Start/stop scheduler toggle
- View full think.log (scrollable, auto-tail)
- Reset adapter state (clear error, reset last_failure)
- Configure adapter (modal with source-specific settings)

**Data sources:**
- `GET /api/health` — from sync_state table
- `GET /api/health/scheduler` — reads launchd status and `~/.coco/logs/think.log`
- `POST /api/health/:adapter/sync` — trigger ingest for specific source
- `POST /api/health/sync-all` — trigger full ingest
- `POST /api/health/scheduler/start` — install launchd plist
- `POST /api/health/scheduler/stop` — uninstall launchd plist
- `GET /api/health/logs?lines=` — tail of think.log

**Real-time updates:**
- SSE for sync completion events (status changes in sync_state)
- Auto-tail of think.log when scheduler page is open

---

### 2.13 Settings

**Route:** `/settings`

**What it shows:**
- Tabbed settings page: General | Autonomy | Display | Auto-Handle | YOLO Guardrails | Brain | Advanced

- **General tab:**
  - Morning cutoff hour (slider, 1-12)
  - Quick reopen threshold (minutes, slider)
  - Briefing lookback default (dropdown: since_last_session / 24h / 48h / 7d)
  - Monthly budget (USD input)

- **Autonomy tab:**
  - Current mode indicator (CAREFUL / NORMAL / YOLO) with large toggle
  - Visual trust matrix (table showing action types vs. what each mode allows):
    ```
    Action Type       | CAREFUL | NORMAL | YOLO
    ─────────────────┼─────────┼────────┼──────
    Read/search       | Auto    | Auto   | Auto
    Classify content  | Ask     | Auto>85%| Auto
    Approve drafts    | Ask     | Auto>85%| Auto
    Create Jira       | Ask     | Ask    | Auto
    External comms    | Ask     | Ask    | Ask
    Git push          | Ask     | Ask    | Ask
    Delete            | Ask     | Ask    | Ask
    ```
  - Per-action confidence thresholds (editable sliders)

- **Display tab:**
  - Max projects shown on dashboard (number input)
  - Collapse quiet projects toggle
  - Show cost on dashboard toggle
  - Emoji toggle (on/off)
  - Theme (light/dark/system)

- **Auto-Handle tab:**
  - Classify above confidence threshold (slider, 0.0-1.0)
  - Dismiss noise from unknown senders toggle
  - File FYI silently toggle
  - Draft generation toggle

- **YOLO Guardrails tab:**
  - Auto-approve threshold (slider)
  - Skip-and-queue threshold (slider)
  - Always-ask actions (checklist: external_comms, git_push, delete)
  - Max Jira tickets per session (number)
  - Max draft approvals per session (number)

- **Brain tab (read-only in v1):**
  - Raw JSON viewer for brain.json (syntax highlighted)
  - People count, rules count, preferences count
  - Last modified timestamp
  - "Edit in CLI" instruction

- **Advanced tab:**
  - hub.db path (read-only)
  - Export all data (button: downloads zip of hub.db + ~/.coco/)
  - Import data (file upload)
  - Reset all settings to defaults (with confirmation)
  - Clear session history (with confirmation)

**User interactions:**
- All settings are live-editable with auto-save (debounced 1s)
- Change indicators show unsaved changes
- "Reset to defaults" per section
- Export/import for migration

**Data sources:**
- `GET /api/settings` — reads config.json
- `PATCH /api/settings` — writes config.json (atomic write)
- `GET /api/settings/brain` — reads brain.json
- `POST /api/settings/export` — generates zip archive
- `POST /api/settings/import` — processes uploaded archive

**Real-time updates:**
- None (settings are user-initiated)

---

### 2.14 Session History

**Route:** `/sessions`

**What it shows:**
- Chronological list of all CoCo sessions from `~/.coco/sessions/`
- Each session card: start time, end time, duration, launch type, focus project, commands used count, decisions made count, items deferred count
- Expandable detail: full list of commands, MCP tools called, decisions with outcomes, skills invoked
- Aggregate stats at top: total sessions, avg session length, most active project, most used commands

**User interactions:**
- Click session to expand details
- Filter by: date range, launch type, project focus
- Search within session logs
- "Export" session data as JSON

**Data sources:**
- `GET /api/sessions?from=&to=&type=&project=&page=&limit=` — reads and parses all JSON files in `~/.coco/sessions/`
- `GET /api/sessions/:timestamp` — single session detail
- `GET /api/sessions/stats` — aggregate computations

**Real-time updates:**
- Current session updates live (commands_used grows)

---

### 2.15 Briefing

**Route:** `/briefing`

**What it shows:**
- Full briefing view matching CoCo's briefing format
- Grouped by project: each project section shows email/voice/jira/confluence counts, key items, action items due
- Totals bar at bottom: total items by source, overdue count, upcoming count, pending drafts
- Time selector: "Since last session" / "Last 24h" / "Last 48h" / "Last 7d" / Custom

**User interactions:**
- Expand/collapse project sections
- Click any item to navigate to content detail
- Click action item to navigate to todo or create one
- "Mark as reviewed" per project section (collapse and dim)
- Print-friendly view (button)
- Drill-down: click source count to see filtered list

**Data sources:**
- `GET /api/briefing?since=` — aggregated from content, project_content, drafts, action items. `since` defaults to last session timestamp
- Uses same data as `mcp__knowledge-hub__briefing` MCP tool

**Real-time updates:**
- None (briefing is a point-in-time snapshot)

---

## 3. New Features (CoCo-Only)

Features that Paperclip does not have but CoCo Platform includes, leveraging the existing Knowledge Hub and CoCo capabilities.

---

### 3.1 Knowledge Hub Integration

**What:** Full visibility into the Knowledge Hub's multi-source ingestion and processing pipeline, presented as native web UI rather than CLI output.

#### 3.1.1 Email Viewer

**Route:** `/knowledge/email`

**What it shows:**
- Timeline of all ingested emails, grouped by thread or flat list
- Each email: sender, recipients, subject, date, snippet, project classification, relevance score
- Attachment indicators
- Source health status for email adapter

**User interactions:**
- Click to read full email content (processed_text view)
- Reclassify to different project
- Create action item / todo from email
- Reply draft (opens draft composer)
- Filter by: project, sender, date range, has-attachment

**Data sources:**
- `GET /api/content?source=email&...` — from content table where source='email'

#### 3.1.2 Voice Memo Viewer

**Route:** `/knowledge/voice`

**What it shows:**
- List of all ingested voice memos with duration, date, project, status
- Transcript viewer with speaker labels (parsed from processed_text)
- Audio player (if source_path points to accessible audio file)
- Speaker identification with alias resolution (e.g., "Vishal" -> Rijul, using brain.json transcription_aliases)

**User interactions:**
- Play/pause/seek audio with synchronized transcript highlighting
- Click on transcript segment to jump to that point in audio
- Edit transcript (correct misheard names/terms)
- Extract action items from transcript
- Reclassify to different project
- Filter by: project, date, duration, speaker

**Data sources:**
- `GET /api/content?source=voice&...` — from content table where source='voice'
- `GET /api/content/:id/audio` — serves audio file from source_path
- `GET /api/people/aliases` — from brain.json transcription_aliases for speaker mapping

#### 3.1.3 Jira Integration View

**Route:** `/knowledge/jira`

**What it shows:**
- List of all Jira ticket updates ingested by KH
- Grouped by project (using project.jira_key)
- Each item: Jira key (linked to Jira), summary, status, assignee, last update, change description
- Sync status and last sync timestamp

**User interactions:**
- Click Jira key to open in Jira (external link)
- View change history for a ticket
- Create new Jira ticket from any content item
- Filter by: project, status, assignee, date range

**Data sources:**
- `GET /api/content?source=jira&...` — from content table where source='jira'

#### 3.1.4 Confluence Integration View

**Route:** `/knowledge/confluence`

**What it shows:**
- List of all Confluence page updates ingested by KH
- Grouped by space (using project.confluence_space)
- Each item: page title (linked), space, last editor, update date, change summary
- Draft status: pages that have pending CoCo-generated drafts

**User interactions:**
- Click page title to open in Confluence (external link)
- View drafts targeting this page
- Trigger stale document detection
- Filter by: space, editor, date range

**Data sources:**
- `GET /api/content?source=confluence&...` — from content table where source='confluence'

---

### 3.2 People Graph Visualization

**Route:** `/people` (described in Section 2.8)

**What Paperclip lacks:** Paperclip has agents (bots) in a hierarchy. CoCo has a **people graph** — real humans with roles, communication patterns, and learned routing rules. This is a fundamental differentiator: CoCo understands the human context of a PM's work.

**Unique capabilities:**
- **Transcription alias mapping** — voice memo speakers misheard as "Vishal", "Rizzul", etc. are auto-mapped to the correct person
- **Communication frequency analysis** — derived from content_entities, shows who you interact with most and through what channels
- **Attention rule management** — visual rule builder: "When [source] mentions [topic], classify as [project]"
- **Priority heatmap** — who requires the most attention based on incoming content volume and urgency

---

### 3.3 Decision Queue in the UI

**Route:** `/decide` (described in Section 2.5)

**What Paperclip lacks:** Paperclip has a simple issue list. CoCo's decision queue is a **prioritized triage interface** that combines multiple data sources (drafts, unsorted content, health issues, overdue items) into a single actionable stream, ranked by urgency and filtered through learned rules.

**Unique capabilities:**
- **Multi-type queue** — not just issues; combines drafts, classifications, health alerts, and overdue items
- **Confidence-based suggestions** — auto-classification suggestions with visible confidence scores
- **Deferral with aging** — items can be deferred with progressive escalation (next session -> 24h -> flagged as stale)
- **Observed learning** — every classification action updates the learning model for future auto-handling
- **Batch processing** — process an entire queue in one sitting with keyboard shortcuts

---

### 3.4 Learning and Teaching Interface

**Route:** `/learn`

**What it shows:**
- Three sections: Taught Rules | Observed Rules | Teach CoCo
- **Taught Rules:** rules explicitly taught via `/coco teach` or the web UI. Each rule shows: description, target project, source, creation date, hit count
- **Observed Rules:** rules CoCo learned by observing user classification patterns. Each shows: pattern, confidence, observation count, last triggered
- **Teach CoCo:** freeform text input that accepts natural language rules

**User interactions:**
- Type natural language rules: "Chris always emails about AuditBoard" -> creates attention rule mapping Chris's emails to AuditBoard project
- Edit existing rules (modify target, adjust thresholds)
- Delete rules (with confirmation)
- View rule hit history (when did this rule last trigger, what content did it match)
- Test a rule: paste content, see which rules would match
- "Observation mode" toggle: when on, all manual classifications are tracked for pattern extraction
- Export rules as JSON

**Data sources:**
- `GET /api/learn/rules` — from brain.json attention_rules + learned_rules table
- `POST /api/learn/teach` — parse natural language, update brain.json and/or learned_rules
- `DELETE /api/learn/rules/:id` — remove from brain.json or learned_rules
- `GET /api/learn/rules/:id/history` — hits from content that matched this rule
- `POST /api/learn/test` — evaluate content against all rules, return matches

**Real-time updates:**
- None (learning is user-initiated)

**What Paperclip lacks:** Paperclip has no learning system. CoCo builds an increasingly accurate model of your work by combining explicit teaching with observed patterns, reducing the manual triage burden over time.

---

### 3.5 Autonomy Mode Controls with Visual Trust Matrix

**Route:** `/settings` (Autonomy tab, described in Section 2.13)

**Additionally, a persistent indicator in the app header:**
- Small badge showing current mode: "CAREFUL" (red) / "NORMAL" (blue) / "YOLO" (green)
- Click to change mode
- YOLO shows timer if time-limited (e.g., "YOLO 22m remaining")

**What it shows beyond settings:**
- **Trust matrix visualization** — color-coded grid showing what CoCo is allowed to do automatically in the current mode
- **Action log** — real-time view of what CoCo has auto-handled vs. what it asked about
- **Confidence distribution chart** — histogram of recent classification confidences, with threshold lines showing where auto-handle kicks in

**What Paperclip lacks:** Paperclip has binary approval gates. CoCo has a **3-tier autonomy system with per-action confidence thresholds**, allowing graduated trust. The PM can go full-auto (YOLO) for a time-boxed sprint, then pull back to CAREFUL when reviewing sensitive content.

---

### 3.6 Todo List Management

**Route:** `/todos` (described in Section 2.7)

**What Paperclip lacks:** Paperclip issues are for agent work. CoCo todos are **PM action items** derived from voice memos, emails, and meetings, with a direct pipeline to Jira.

**Unique capabilities:**
- **Source tracing** — every todo links back to the content item it came from (voice memo timestamp, email thread, etc.)
- **Action item sync** — automatic extraction of action items from meeting notes and voice memos
- **Jira pipeline** — preview and push todos to Jira with full field mapping (project, labels, priority, description)
- **Smart deduplication** — when syncing from Knowledge Hub, detects near-duplicate todos and merges
- **Owner from people graph** — assign owners from known people, auto-suggesting based on content context

---

### 3.7 Voice Memo Player and Transcript Viewer

**Route:** `/knowledge/voice` (described in Section 3.1.2)

**Standalone component also embedded in content detail view.**

**What it shows:**
- Waveform visualization of audio file
- Transcript with speaker labels and timestamps
- Speaker color coding
- Confidence indicators for uncertain transcription segments
- Extracted entities highlighted in transcript (people names, project references, action items)

**User interactions:**
- Play/pause, seek, playback speed control (0.5x / 1x / 1.5x / 2x)
- Click transcript line to seek audio to that timestamp
- Select transcript text to: create todo, create draft, add to search
- Edit transcript inline (correct names, fix misheard words)
- "Correct speaker" — reassign speaker labels using people graph
- "Extract action items" — re-run action item extraction on this memo
- Download transcript as text/markdown

**What Paperclip lacks entirely.** Paperclip has no voice/audio capabilities. This is a core CoCo differentiator for the PM workflow (25+ hrs/week of meetings captured as voice memos).

---

### 3.8 Stale Document Detection

**Route:** `/stale` (also accessible from project detail)

**What it shows:**
- List of Confluence pages that may be outdated based on:
  - Last edit date vs. related Jira ticket activity (tickets moved but docs not updated)
  - Content drift: voice memos or emails discuss changes not reflected in docs
  - Explicit age thresholds per template type
- Each item: page title, last edited, staleness score, evidence (what changed that makes it stale)

**User interactions:**
- Click to view page content vs. recent changes side by side
- "Generate Update Draft" — creates a draft updating the page with recent context
- "Mark as Current" — explicitly mark as not stale (resets timer)
- "Ignore" — exclude from stale detection
- Sort by: staleness score, last edit date, project

**Data sources:**
- `GET /api/stale?project=` — analysis of content (source=confluence) vs recent content from other sources
- `POST /api/stale/:id/generate-draft` — create draft targeting this Confluence page
- `POST /api/stale/:id/mark-current` — update metadata

**What Paperclip lacks entirely.** No document freshness tracking.

---

### 3.9 Briefing / Daily Digest

**Route:** `/briefing` (described in Section 2.15)

**What Paperclip lacks:** Paperclip has an activity feed but no synthesized, PM-oriented briefing. CoCo's briefing aggregates across email, voice, Jira, and Confluence to give a holistic "what happened while I was away" view, grouped by project and prioritized by urgency.

---

## 4. Feature Phases

### 4.0 Phase 0 — Foundation (pre-v1.0)

Infrastructure and scaffolding. Not user-visible.

| Item | Description |
|---|---|
| Project setup | Next.js 14+ (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| API layer | Express or Next.js API routes wrapping hub.db (SQLite via better-sqlite3) |
| Auth | Simple local auth (single user). JWT session. No SSO in v1 |
| SSE server | Server-sent events endpoint for real-time updates |
| DB access | Read-only access to hub.db + read-write access to ~/.coco/ JSON files |
| CI | Lint + type-check + test on push |

---

### 4.1 Phase 1 — v1.0 "Mirror" (Core CoCo in a browser)

**Goal:** Replicate every `/coco` command as a web page. A PM should be able to do everything they currently do in the CLI, in the browser.

| Feature | Page | Priority |
|---|---|---|
| Command center dashboard | `/` | P0 |
| Project list | `/projects` | P0 |
| Project detail (all tabs) | `/projects/:id` | P0 |
| Inbox (unsorted content) | `/inbox` | P0 |
| Decision queue | `/decide` | P0 |
| Drafts list and detail | `/drafts` | P0 |
| Todo list (kanban + list) | `/todos` | P0 |
| Knowledge search | `/search` | P0 |
| Content detail | `/content/:id` | P0 |
| Health and adapters | `/health` | P0 |
| Cost dashboard | `/cost` | P0 |
| Settings (all tabs) | `/settings` | P0 |
| Session history | `/sessions` | P1 |
| SSE activity stream | All pages | P0 |
| Manual process trigger | Dashboard | P0 |

**v1.0 ships when:** All P0 items above are functional. User can process their entire daily CoCo workflow through the browser without touching the CLI.

---

### 4.2 Phase 2 — v1.1 "Intelligence" (New capabilities beyond CLI)

**Goal:** Add features that are better in a GUI than a CLI — visualizations, drag-and-drop, audio playback.

| Feature | Page | Priority |
|---|---|---|
| People graph visualization (D3) | `/people` | P1 |
| Voice memo player + transcript viewer | `/knowledge/voice` | P1 |
| Autonomy mode controls + trust matrix | `/settings` + header | P1 |
| Learning / teaching interface | `/learn` | P1 |
| Stale document detection | `/stale` | P1 |
| Cost charts (line, bar, pie) | `/cost` | P1 |
| Keyboard shortcuts (j/k nav, a/r/d actions) | Decision queue | P1 |
| Briefing page | `/briefing` | P1 |
| Email viewer | `/knowledge/email` | P1 |
| Jira integration view | `/knowledge/jira` | P1 |
| Confluence integration view | `/knowledge/confluence` | P1 |
| Budget alerts (80%/100% thresholds) | Dashboard + cost | P1 |

**v1.1 ships when:** All visualization and intelligence features are functional. The web app offers capabilities that are meaningfully better than the CLI experience.

---

### 4.3 Phase 3 — v1.2 "Polish and Power" (Refinement and advanced features)

**Goal:** Smooth edges, add power-user features, and prepare for potential multi-user expansion.

| Feature | Page | Priority |
|---|---|---|
| Config versioning with diff and rollback | `/settings` | P2 |
| Full backup/restore (export/import) | `/settings` | P2 |
| Todo comments/notes | `/todos` | P2 |
| Content attachment viewer (inline PDF, images) | `/content/:id` | P2 |
| Drag-and-drop file ingestion (drop email/file onto browser) | Global | P2 |
| Print-friendly briefing view | `/briefing` | P2 |
| Notification system (browser notifications for urgent items) | Global | P2 |
| Dark mode / theme system | Global | P2 |
| Mobile-responsive layout | Global | P2 |
| Performance: virtual scrolling for large lists | All list views | P2 |
| Performance: incremental SSE (delta updates, not full refresh) | All pages | P2 |
| Offline support (service worker, cached reads) | Global | P2 |
| API rate limiting and error recovery | API layer | P2 |

**v1.2 ships when:** The app feels polished and production-ready for daily use. All rough edges from v1.0 and v1.1 are smoothed.

---

## 5. Non-Goals

What we explicitly will **not** build, and why.

| Non-Goal | Rationale |
|---|---|
| **Multi-user / multi-tenant** | CoCo Platform is a personal PM tool for a single user (Rijul). No login page, no user management, no RBAC. If expanded later, it would be a major refactor, not a feature add. |
| **Autonomous agent execution** | Paperclip agents execute code and make API calls independently. CoCo's "agent" is Claude in a CLI session. The web app is a dashboard and control surface, not an agent runtime. Background processing is limited to the existing think.py launchd job. |
| **Agent-to-agent delegation** | Paperclip supports agents delegating tasks to other agents. CoCo is a single-brain system. All delegation is to humans (via todos, Jira tickets, nudges). |
| **Custom agent creation** | Paperclip lets you create agents with roles and model preferences. CoCo has one agent (itself). No need for an agent builder. |
| **Slack integration** | Blocked by McKinsey IT policy. Explicitly out of scope. May revisit if IT unblocks. |
| **Real-time collaboration** | No multi-cursor, no shared editing, no presence indicators. Single user. |
| **Embedded LLM inference** | The web app does not run Claude API calls directly. All LLM work happens through the Knowledge Hub MCP server or the CoCo CLI skill. The web app reads results from hub.db. |
| **Custom dashboards / widgets** | No drag-and-drop dashboard builder. The layout is fixed and opinionated based on the PM workflow. |
| **Confluence/Jira WYSIWYG editor** | Drafts are viewed and approved/rejected, but editing happens in the native Confluence/Jira UIs. We show links, not embedded editors. |
| **Calendar integration** | Interesting but complex (requires Outlook Graph API or calendar file parsing). Defer to v2+. |
| **Notification channels (email, SMS, push)** | Browser notifications only (and only for urgent decision queue items). No email/SMS alerting. |
| **Git integration / code review** | CoCo has `/coco build`, `/coco fix`, `/coco review` but these are CLI-native experiences that require terminal access. The web app shows session logs of these activities but does not replicate the interactive coding experience. |
| **Custom report builder** | No drag-and-drop report creation. The cost dashboard and briefing page cover the reporting needs. |
| **Data retention / archival policies** | hub.db grows indefinitely. Manual cleanup via SQLite. Archival policies deferred to v2+. |
| **API for external consumers** | The API exists to serve the web frontend. No public API documentation, no API keys for external integrations, no webhooks. |

---

## Appendix A: Data Model Reference

### hub.db Tables (Knowledge Hub — read-write via API)

| Table | Purpose | Key Fields |
|---|---|---|
| `content` | All ingested content items | id, source, source_id, title, raw_text, processed_text, status, relevance_score, metadata (JSON), timestamps |
| `projects` | Project registry | id, name, jira_key, confluence_space, active |
| `project_content` | Content-to-project classification | project_id, content_id, confidence, method |
| `entities` | Extracted entities (people, topics) | id, name, entity_type |
| `content_entities` | Content-to-entity links | content_id, entity_id |
| `drafts` | Generated document drafts | id, project_id, source_content_id, target_template, target_section, content, status |
| `todos` | Action items and tasks | id, title, project_id, owner, due_date, priority, status, source_type, jira_key |
| `sync_state` | Adapter health per source | source_name, last_success, last_failure, items_synced, status |
| `api_costs` | LLM API cost tracking | id, timestamp, model, feature, input_tokens, output_tokens, cache tokens, cost_usd |
| `learned_rules` | Auto-classification rules | id, project_id, rule_type, rule_value, hit_count |
| `corrections` | Manual reclassification history | id, content_id, old_project_id, new_project_id |
| `content_fts` | Full-text search (FTS5) | title, raw_text, processed_text |
| `content_vec` | Semantic search (vec0) | content_id, embedding (float[512]) |

### ~/.coco/ Files (CoCo Brain — read-write via API)

| File | Purpose | Key Fields |
|---|---|---|
| `brain.json` | People graph, attention rules, preferences | version, people{}, attention_rules[], preferences{}, classification_hints{}, owner_matching{}, stats{} |
| `config.json` | CoCo behavior configuration | launch_ui, thresholds, auto_handle{}, display{}, yolo{} |
| `queue.json` | Decision queue state | items[], deferred[], auto_handled_since_last_session[] |
| `sessions/*.json` | Session history | started_at, ended_at, launch_type, commands_used[], decisions_made[] |
| `think.py` | Background processor | Python script, reads hub.db, writes queue.json |
| `logs/think.log` | Background processing logs | Timestamped log lines |

---

## Appendix B: API Endpoint Summary

All endpoints are prefixed with `/api/v1`. Authentication is JWT-based (single user).

### Dashboard and Core
| Method | Path | Description |
|---|---|---|
| GET | `/dashboard` | Aggregated dashboard data |
| GET | `/briefing?since=` | Synthesized briefing |
| GET | `/events` | SSE stream for real-time updates |

### Projects
| Method | Path | Description |
|---|---|---|
| GET | `/projects` | List all projects with counts |
| POST | `/projects` | Create project |
| GET | `/projects/:id` | Project detail |
| PATCH | `/projects/:id` | Update project |
| GET | `/projects/:id/content` | Content for project |
| GET | `/projects/:id/action-items` | Action items for project |
| GET | `/projects/:id/drafts` | Drafts for project |
| GET | `/projects/:id/todos` | Todos for project |
| GET | `/projects/:id/rules` | Classification rules for project |

### Content
| Method | Path | Description |
|---|---|---|
| GET | `/content` | List/filter content |
| GET | `/content/:id` | Content detail |
| POST | `/content/:id/classify` | Classify to project |
| POST | `/content/:id/dismiss` | Dismiss as noise |
| POST | `/content/:id/reprocess` | Re-run pipeline |
| GET | `/content/:id/audio` | Serve audio file |
| GET | `/content/:id/entities` | Linked entities |
| GET | `/content/:id/drafts` | Drafts from this content |
| GET | `/content/:id/todos` | Todos from this content |

### Inbox
| Method | Path | Description |
|---|---|---|
| GET | `/inbox` | Unsorted content |
| POST | `/inbox/bulk-classify` | Batch classify |
| POST | `/inbox/process` | Trigger triage |

### Decision Queue
| Method | Path | Description |
|---|---|---|
| GET | `/queue` | Assembled decision queue |
| POST | `/queue/:id/action` | Execute action on queue item |
| GET | `/queue/deferred` | Deferred items |

### Drafts
| Method | Path | Description |
|---|---|---|
| GET | `/drafts` | List/filter drafts |
| GET | `/drafts/:id` | Draft detail |
| POST | `/drafts/:id/approve` | Approve draft |
| POST | `/drafts/:id/reject` | Reject draft |
| POST | `/drafts/:id/push` | Push to Confluence |

### Todos
| Method | Path | Description |
|---|---|---|
| GET | `/todos` | List/filter todos |
| POST | `/todos` | Create todo |
| PATCH | `/todos/:id` | Update todo |
| DELETE | `/todos/:id` | Dismiss todo |
| POST | `/todos/:id/jira` | Create Jira ticket |
| POST | `/todos/sync` | Sync from action items |
| POST | `/todos/bulk-jira` | Batch Jira creation |

### People
| Method | Path | Description |
|---|---|---|
| GET | `/people` | List all people |
| GET | `/people/:id` | Person detail |
| POST | `/people` | Add person |
| PATCH | `/people/:id` | Update person |
| DELETE | `/people/:id` | Remove person |
| GET | `/people/:id/content` | Content involving person |
| POST | `/people/teach` | Natural language rule |
| GET | `/people/aliases` | Transcription alias map |

### Search
| Method | Path | Description |
|---|---|---|
| GET | `/search` | Full-text or semantic search |

### Cost
| Method | Path | Description |
|---|---|---|
| GET | `/cost` | Aggregated cost data |
| GET | `/cost/events` | Raw cost events |
| GET | `/cost/summary` | Monthly summary and projection |
| GET | `/cost/budget` | Current budget setting |
| PATCH | `/cost/budget` | Update budget |

### Health
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Adapter statuses |
| POST | `/health/:adapter/sync` | Trigger sync for adapter |
| POST | `/health/sync-all` | Trigger full sync |
| GET | `/health/scheduler` | Scheduler status |
| POST | `/health/scheduler/start` | Install scheduler |
| POST | `/health/scheduler/stop` | Stop scheduler |
| GET | `/health/logs` | Think pass logs |

### Learning
| Method | Path | Description |
|---|---|---|
| GET | `/learn/rules` | All rules (taught + observed) |
| POST | `/learn/teach` | Teach natural language rule |
| DELETE | `/learn/rules/:id` | Delete rule |
| GET | `/learn/rules/:id/history` | Rule hit history |
| POST | `/learn/test` | Test content against rules |

### Settings
| Method | Path | Description |
|---|---|---|
| GET | `/settings` | Current config |
| PATCH | `/settings` | Update config |
| GET | `/settings/brain` | Brain.json contents |
| POST | `/settings/export` | Export all data |
| POST | `/settings/import` | Import data archive |

### Sessions
| Method | Path | Description |
|---|---|---|
| GET | `/sessions` | List sessions |
| GET | `/sessions/:timestamp` | Session detail |
| GET | `/sessions/stats` | Aggregate stats |
