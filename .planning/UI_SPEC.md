# CoCo Platform — UI Specification

> Paperclip-style multi-agent orchestration dashboard for a solo PM.
> Tech: React 19 + Vite + Radix UI + Tailwind CSS 4 | Dark mode primary

---

## 1. Design System

### Color Palette (Dark Mode Primary)

| Token              | Hex       | Usage                              |
|--------------------|-----------|-------------------------------------|
| `--bg-base`        | `#09090b` | App background (zinc-950)          |
| `--bg-surface`     | `#18181b` | Cards, panels (zinc-900)           |
| `--bg-elevated`    | `#27272a` | Hover states, active items (zinc-800) |
| `--border-default` | `#3f3f46` | Borders, dividers (zinc-700)       |
| `--border-subtle`  | `#27272a` | Subtle separators (zinc-800)       |
| `--text-primary`   | `#fafafa` | Headings, primary text (zinc-50)   |
| `--text-secondary` | `#a1a1aa` | Body text, labels (zinc-400)       |
| `--text-muted`     | `#71717a` | Timestamps, hints (zinc-500)       |
| `--accent`         | `#10b981` | Primary actions, active states (emerald-500) |
| `--accent-hover`   | `#059669` | Accent hover (emerald-600)         |
| `--accent-muted`   | `#065f46` | Accent backgrounds (emerald-900)   |
| `--warning`        | `#f59e0b` | Warnings, attention (amber-500)    |
| `--warning-muted`  | `#78350f` | Warning backgrounds (amber-900)    |
| `--error`          | `#ef4444` | Errors, critical (red-500)         |
| `--error-muted`    | `#7f1d1d` | Error backgrounds (red-900)        |
| `--info`           | `#3b82f6` | Informational, drafts (blue-500)   |
| `--info-muted`     | `#1e3a5f` | Info backgrounds (blue-900)        |

Light mode: invert luminance; accent colors stay. Not a launch priority.

### Typography

| Role          | Font            | Weight | Size   | Line Height | Tracking |
|---------------|-----------------|--------|--------|-------------|----------|
| Display       | Inter           | 700    | 28px   | 36px        | -0.02em  |
| Heading 1     | Inter           | 600    | 22px   | 28px        | -0.01em  |
| Heading 2     | Inter           | 600    | 18px   | 24px        | -0.01em  |
| Heading 3     | Inter           | 500    | 15px   | 20px        | 0        |
| Body          | Inter           | 400    | 14px   | 20px        | 0        |
| Body Small    | Inter           | 400    | 12px   | 16px        | 0        |
| Caption       | Inter           | 500    | 11px   | 14px        | 0.02em   |
| Data / Code   | JetBrains Mono  | 400    | 13px   | 18px        | 0        |
| Data Small    | JetBrains Mono  | 400    | 11px   | 14px        | 0        |

### Spacing Scale (4px base)

`0 (0) | 1 (4px) | 2 (8px) | 3 (12px) | 4 (16px) | 5 (20px) | 6 (24px) | 8 (32px) | 10 (40px) | 12 (48px) | 16 (64px) | 20 (80px)`

### Border Radius

| Token     | Value |
|-----------|-------|
| `--r-sm`  | 4px   |
| `--r-md`  | 8px   |
| `--r-lg`  | 12px  |
| `--r-xl`  | 16px  |
| `--r-full`| 9999px|

### Shadows (dark mode — subtle glow, not drop)

- `--shadow-sm`: `0 0 0 1px var(--border-subtle)`
- `--shadow-md`: `0 0 0 1px var(--border-default), 0 2px 8px rgba(0,0,0,0.4)`
- `--shadow-lg`: `0 0 0 1px var(--border-default), 0 8px 24px rgba(0,0,0,0.6)`

### Radix UI Primitives (used directly)

Dialog, DropdownMenu, Tooltip, Tabs, ScrollArea, Select, Switch, Checkbox, Toast, Popover, Separator, Avatar, Badge, Command (cmdk).

### Icons

Lucide React (`lucide-react`). 16px default, 20px for nav. Stroke width 1.5.

### Animation

- Default transition: `150ms ease-out`
- Slide-in (feed items): `transform: translateY(-8px) -> 0` over `200ms ease-out`
- Fade highlight (new items): `background: var(--accent-muted) -> transparent` over `1500ms ease-out`
- Skeleton loading: pulse at `1.5s ease-in-out infinite`
- Panel collapse: `width` transition `200ms ease-out`

---

## 2. Layout

### App Shell

```
+---------------------------------------------------+
| TopBar (48px, optional — shows breadcrumbs on mobile) |
+----------+------------------------+---------------+
|          |                        |               |
| Sidebar  |     Main Content       |  Chat Panel   |
| 240px    |     flex-1             |  400px        |
| (collaps.|     min-w: 480px       |  (toggle)     |
| to 64px) |                        |               |
|          |                        |               |
|          |                        |               |
+----------+------------------------+---------------+
```

### Sidebar (240px expanded / 64px collapsed)

```
+--------------------+
| [CoCo Logo] CoCo   |  <- 48px header
+--------------------+
|  Dashboard         |
|  Projects          |
|  Stations          |
|  Knowledge Hub     |
|  Decisions [3]     |  <- badge count
|  People            |
|  Todos [7]         |  <- badge count
|  Costs             |
+--------------------+
|                    |  <- flex spacer
+--------------------+
|  Settings          |
|  [Chat toggle]     |
|  ──────────────    |
|  CoCo v1 | $2.41  |  <- version + daily cost
+--------------------+
```

- Active item: `bg: var(--bg-elevated)`, left 2px `var(--accent)` border
- Hover: `bg: var(--bg-elevated)` at 50% opacity
- Collapsed: icons only, tooltips on hover
- Collapse trigger: chevron button at sidebar header, or `Cmd+B`

### Responsive Breakpoints

| Breakpoint | Width   | Behavior                                     |
|------------|---------|----------------------------------------------|
| Desktop    | >= 1024 | Full layout, sidebar + main + optional chat  |
| Tablet     | 768-1023| Sidebar collapses to 64px, chat as overlay   |
| Mobile     | < 768   | Sidebar hidden (hamburger), chat full-screen  |

### Chat Panel (400px, right side)

- Toggle via sidebar button or `Cmd+J`
- Slides in from right with `200ms ease-out`
- Resizable handle on left edge (min 320px, max 600px)
- Header: "CoCo Chat" + minimize + pop-out buttons

---

## 3. Page Wireframes

### a) Dashboard `/`

```
+----------------------------------------------------------------+
|  Dashboard                                     [Cmd+K] [Bell]  |
+----------------------------------------------------------------+
|                                                                |
|  STATIONS (3-col grid)                                         |
|  +------------------+ +------------------+ +------------------+|
|  | PM Station    [G]| | Ingest Station[G]| | Exec Station [Y]||
|  | 14 tasks done    | | 3 emails queued  | | 1 Jira blocked  ||
|  | $0.82 today      | | $0.41 today      | | $1.18 today     ||
|  +------------------+ +------------------+ +------------------+|
|                                                                |
|  PROJECTS (2-col)                    ACTIVITY FEED             |
|  +---------------------+  +---------+  +--------------------+ |
|  | Cross Risk      [G] |  | OpsHub  |  | 9:41  Email ingested|
|  | E:12 V:3 J:8 C:5    |  | [Y]     |  | 9:38  Jira CXR-204 |
|  | Last: 4m ago        |  | E:4 V:1 |  | 9:35  Draft ready   |
|  +---------------------+  +---------+  | 9:30  Cost alert    |
|  | OpsHub          [Y] |               | 9:22  Voice memo    |
|  | ...                  |               | ...                 |
|  +---------------------+               +--------------------+ |
|                                                                |
|  DECISIONS [3 urgent]                  COST BAR                |
|  +---------------------------+  +----------------------------+ |
|  | ! Classify: 2 new emails  |  | Today: $2.41 / $10 budget | |
|  | ! Route: stakeholder msg  |  | [=========>     ] 24%     | |
|  +---------------------------+  +----------------------------+ |
+----------------------------------------------------------------+
```

Health dots: `[G]` = `var(--accent)` green, `[Y]` = `var(--warning)` amber, `[R]` = `var(--error)` red.

### b) Projects `/projects`

```
+----------------------------------------------------------------+
|  Projects                              [+ New Project] [Filter]|
+----------------------------------------------------------------+
|                                                                |
|  +---------------------+  +---------------------+             |
|  | Cross Risk Platform |  | OpsHub Migration    |             |
|  | G  Active           |  | Y  At Risk          |             |
|  | ┌──────────────────┐|  | ┌──────────────────┐|             |
|  | │ E:12  V:3  J:8   │|  | │ E:4   V:1  J:14  │|             |
|  | │ C:5   AI:2       │|  | │ C:2   AI:5       │|             |
|  | └──────────────────┘|  | └──────────────────┘|             |
|  | Last: Email 4m ago  |  | Last: Jira 22m ago  |             |
|  | Todos: 3 open       |  | Todos: 7 open       |             |
|  +---------------------+  +---------------------+             |
|                                                                |
|  +---------------------+                                      |
|  | Personal / Misc     |                                      |
|  | G  Active           |                                      |
|  | │ E:2   V:5  J:0   │|                                      |
|  | Last: Voice 1h ago  |                                      |
|  +---------------------+                                      |
+----------------------------------------------------------------+
```

Source counts use monospace (`JetBrains Mono`). Pills: `E` = email (zinc-400), `V` = voice (violet-400 `#a78bfa`), `J` = Jira (blue-400 `#60a5fa`), `C` = Confluence (blue-300 `#93c5fd`), `AI` = action items (emerald-400).

### c) Project Detail `/projects/:id`

```
+----------------------------------------------------------------+
|  < Projects / Cross Risk Platform                    [G] Active|
+----------------------------------------------------------------+
|  [Overview] [Emails] [Voice] [Jira] [Confluence] [Action Items]|
+----------------------------------------------------------------+
|                                                                |
|  OVERVIEW TAB:                                                 |
|  +---------------------------+  +----------------------------+ |
|  | Summary                   |  | Health                     | |
|  | 28 items ingested         |  | Status: Green              | |
|  | 12 emails, 3 voice,       |  | Last check: 10m ago        | |
|  | 8 Jira, 5 Confluence      |  | Risk: None flagged         | |
|  +---------------------------+  +----------------------------+ |
|                                                                |
|  Recent Activity                                               |
|  +----------------------------------------------------------+ |
|  | 9:41  [E] stakeholder-update.eml ingested                 | |
|  | 9:38  [J] CXR-204 status changed → In Review             | |
|  | 9:35  [AI] Draft: "Weekly risk summary" ready for review  | |
|  | 9:22  [V] voice-memo-0327.m4a transcribed (2m14s)        | |
|  +----------------------------------------------------------+ |
|                                                                |
|  EMAILS TAB:                                                   |
|  +----------------------------------------------------------+ |
|  | From          | Subject              | Date    | Status   | |
|  | J. Smith      | Budget review Q2     | Mar 26  | Read     | |
|  | A. Patel      | Risk escalation      | Mar 26  | Flagged  | |
|  | ...           | ...                  | ...     | ...      | |
|  +----------------------------------------------------------+ |
+----------------------------------------------------------------+
```

Tabs use Radix `Tabs` primitive. Tab indicator: 2px bottom border `var(--accent)`.

### d) Stations `/stations`

```
+----------------------------------------------------------------+
|  Stations                                            [+ New]   |
+----------------------------------------------------------------+
|                                                                |
|  +---------------------+  +---------------------+             |
|  | PM Station          |  | Ingest Station      |             |
|  | Role: Orchestrator  |  | Role: Data Intake   |             |
|  | Model: opus-4       |  | Model: haiku-3      |             |
|  | [G] Running         |  | [G] Running         |             |
|  | ───────────────     |  | ───────────────     |             |
|  | Task: Weekly brief  |  | Task: Email scan    |             |
|  | Last: 2m ago        |  | Last: 30s ago       |             |
|  | Cost: $0.82 today   |  | Cost: $0.41 today   |             |
|  | ───────────────     |  | ───────────────     |             |
|  | [Pause] [Logs]      |  | [Pause] [Logs]      |             |
|  +---------------------+  +---------------------+             |
|                                                                |
|  +---------------------+  +---------------------+             |
|  | Exec Station        |  | Review Station      |             |
|  | Role: Task Runner   |  | Role: QA Gate       |             |
|  | Model: sonnet-4     |  | Model: sonnet-4     |             |
|  | [Y] Blocked         |  | [_] Idle            |             |
|  | ───────────────     |  | ───────────────     |             |
|  | Task: CXR-204 impl  |  | Task: —             |             |
|  | Last: 5m ago        |  | Last: 1h ago        |             |
|  | Cost: $1.18 today   |  | Cost: $0.00 today   |             |
|  | ───────────────     |  | ───────────────     |             |
|  | [Resume] [Kill] [L] |  | [Wake] [Logs]       |             |
|  +---------------------+  +---------------------+             |
+----------------------------------------------------------------+
```

Status indicators: `[G]` green dot (running), `[Y]` amber dot (blocked/warning), `[R]` red dot (error), `[_]` gray dot (idle/paused).

### e) Station Detail `/stations/:id`

```
+----------------------------------------------------------------+
|  < Stations / PM Station                   [G] Running  [$0.82]|
+----------------------------------------------------------------+
|  [Logs] [Tasks] [Cost] [Trust Matrix] [Config]                 |
+----------------------------------------------------------------+
|                                                                |
|  LOGS TAB (live stream):                                       |
|  +----------------------------------------------------------+ |
|  | 09:41:02.341  INFO   Ingested email from J. Smith         | |
|  | 09:41:02.105  DEBUG  Embedding generated (384 dims)       | |
|  | 09:40:58.887  INFO   Classified → Cross Risk / Email      | |
|  | 09:40:55.201  DEBUG  Token usage: 1,247 in / 342 out      | |
|  | 09:40:52.003  INFO   Processing stakeholder-update.eml    | |
|  | ...                                                       | |
|  | [Auto-scroll ON]              [Filter: ALL v] [Search]    | |
|  +----------------------------------------------------------+ |
|                                                                |
|  COST TAB:                                                     |
|  +----------------------------------------------------------+ |
|  |  $                                                        | |
|  |  0.80 |          ____                                     | |
|  |  0.60 |     ____/                                         | |
|  |  0.40 |    /                                              | |
|  |  0.20 |___/                                               | |
|  |  0.00 +-----|-----|-----|-----|---->                       | |
|  |        6am   8am  10am  12pm  2pm                         | |
|  +----------------------------------------------------------+ |
|                                                                |
|  TRUST MATRIX TAB:                                             |
|  +----------------------------------------------------------+ |
|  |           PM    Ingest  Exec  Review                      | |
|  | PM        --    0.95    0.88  0.91                        | |
|  | Ingest   0.95    --     0.72  0.85                        | |
|  | Exec     0.88   0.72    --    0.93                        | |
|  | Review   0.91   0.85   0.93   --                          | |
|  |                                                           | |
|  | Color scale: 0.5 [red] → 0.75 [amber] → 1.0 [green]     | |
|  +----------------------------------------------------------+ |
+----------------------------------------------------------------+
```

Log stream: monospace (`JetBrains Mono 13px`), color-coded severity — `DEBUG` zinc-500, `INFO` zinc-300, `WARN` amber-400, `ERROR` red-400. Auto-scroll toggle bottom-left.

### f) Knowledge Hub `/knowledge`

```
+----------------------------------------------------------------+
|  Knowledge Hub                                    [+ Ingest]   |
+----------------------------------------------------------------+
|  [Search________________________] [Source v] [Project v] [Date]|
|  Source pills: [All] [Email] [Voice] [Jira] [Confluence] [AI] |
+----------------------------------------------------------------+
|                                                                |
|  +----------------------------------------------------------+ |
|  | [E] Budget review Q2                                      | |
|  | Cross Risk | J. Smith | Mar 26 | Classified              | |
|  | "The Q2 budget allocation for risk tooling needs to..."   | |
|  +----------------------------------------------------------+ |
|  | [V] Voice memo — standup notes                            | |
|  | Cross Risk | Rijul | Mar 26 | Transcribed                | |
|  | "Talked to Anika about the deployment timeline, she..."   | |
|  +----------------------------------------------------------+ |
|  | [J] CXR-204: Implement risk scoring API                   | |
|  | Cross Risk | Assignee: Rijul | Mar 25 | Synced            | |
|  | "Acceptance criteria: 1) Score calculation matches..."    | |
|  +----------------------------------------------------------+ |
|  | [C] Architecture Decision Record — Cache Layer             | |
|  | OpsHub | Mar 24 | Synced                                  | |
|  | "We decided to use Redis for the session cache..."        | |
|  +----------------------------------------------------------+ |
|                                                                |
|  Showing 1-20 of 134               [< Prev] [1] [2] ... [Next>]|
+----------------------------------------------------------------+
```

Preview text: 1 line, truncated with ellipsis. Source pill colors match project card convention. Click opens detail drawer (slide-in from right, 600px).

### g) Decisions `/decisions`

```
+----------------------------------------------------------------+
|  Decisions                                  [3 pending] [Hist] |
+----------------------------------------------------------------+
|                                                                |
|  URGENT (red left-border)                                      |
|  +----------------------------------------------------------+ |
|  | ! Classify: 2 new emails need routing                     | |
|  | From: J. Smith, A. Patel | Received: 4m ago               | |
|  | [View] [Auto-Classify] [Assign to Project v]              | |
|  +----------------------------------------------------------+ |
|                                                                |
|  DRAFTS (blue left-border)                                     |
|  +----------------------------------------------------------+ |
|  | Draft ready: "Weekly risk summary for Cross Risk"         | |
|  | Generated by PM Station | 12m ago                         | |
|  | [Preview] [Approve & Send] [Edit] [Reject]                | |
|  +----------------------------------------------------------+ |
|                                                                |
|  CLASSIFY (amber left-border)                                  |
|  +----------------------------------------------------------+ |
|  | Unsorted: voice-memo-0327.m4a transcription                | |
|  | Mentions: Cross Risk, budget, Q2 | 22m ago                | |
|  | [View] [Assign: Cross Risk v] [Dismiss]                   | |
|  +----------------------------------------------------------+ |
|                                                                |
|  HEALTH (orange left-border, orange = #f97316)                 |
|  +----------------------------------------------------------+ |
|  | OpsHub: No Jira updates in 48h                            | |
|  | Last sync: Mar 25 14:30 | Threshold: 24h                  | |
|  | [Acknowledge] [Snooze 24h] [Investigate]                  | |
|  +----------------------------------------------------------+ |
|                                                                |
|  OVERDUE (gray left-border)                                    |
|  +----------------------------------------------------------+ |
|  | Todo overdue: "Review Anika's PR" — due Mar 25            | |
|  | Cross Risk | Priority: High | 2 days overdue              | |
|  | [Mark Done] [Reschedule] [Dismiss]                        | |
|  +----------------------------------------------------------+ |
+----------------------------------------------------------------+
```

Decision groups are collapsible (`Radix Collapsible`). Badge counts in group headers. Empty groups hidden.

### h) People `/people`

```
+----------------------------------------------------------------+
|  People                                            [+ Person]  |
+----------------------------------------------------------------+
|                                                                |
|  +---------------------+  +---------------------+             |
|  | Rijul Kalra         |  | Anika Patel         |             |
|  | [PM] Owner          |  | [ENG] Developer     |             |
|  | Priority: --        |  | Priority: High      |             |
|  | Projects:           |  | Projects:           |             |
|  |  [Cross Risk]       |  |  [Cross Risk]       |             |
|  |  [OpsHub]           |  |  [OpsHub]           |             |
|  | Routes: 4 rules     |  | Routes: 2 rules     |             |
|  | [Edit] [Routes]     |  | [Edit] [Routes]     |             |
|  +---------------------+  +---------------------+             |
|                                                                |
|  +---------------------+  +---------------------+             |
|  | James Smith         |  | Sarah Chen          |             |
|  | [STAKEHOLDER] VP    |  | [STAKEHOLDER] Dir   |             |
|  | Priority: Critical  |  | Priority: Medium    |             |
|  | Projects:           |  | Projects:           |             |
|  |  [Cross Risk]       |  |  [OpsHub]           |             |
|  | Routes: 1 rule      |  | Routes: 1 rule      |             |
|  | [Edit] [Routes]     |  | [Edit] [Routes]     |             |
|  +---------------------+  +---------------------+             |
+----------------------------------------------------------------+
```

Role badges: `PM` emerald, `ENG` blue-400, `STAKEHOLDER` amber-400, `DESIGN` violet-400, `OPS` zinc-400. Priority: `Critical` red text, `High` amber, `Medium` zinc-300, `Low` zinc-500.

### i) Todos `/todos`

```
+----------------------------------------------------------------+
|  Todos                          [Sort: Priority v] [+ Todo]    |
+----------------------------------------------------------------+
|                                                                |
|  Cross Risk (3 open)                                           |
|  +----------------------------------------------------------+ |
|  | [ ] Review Anika's PR on risk scoring       High  Mar 25 | |
|  |     [Done] [Dismiss] [->Jira]                   OVERDUE  | |
|  | [ ] Update stakeholder deck for Q2 review   Med   Mar 28 | |
|  |     [Done] [Dismiss] [->Jira]                             | |
|  | [ ] Respond to J. Smith budget email         High  Mar 27 | |
|  |     [Done] [Dismiss] [->Jira]                   TODAY    | |
|  +----------------------------------------------------------+ |
|                                                                |
|  OpsHub (4 open)                                               |
|  +----------------------------------------------------------+ |
|  | [ ] Triage blocked Jira tickets              High  Mar 27 | |
|  |     [Done] [Dismiss] [->Jira]                   TODAY    | |
|  | [ ] Review cache layer ADR                   Med   Mar 29 | |
|  | [ ] Schedule migration dry-run               Low   Mar 31 | |
|  | [ ] Update OpsHub Confluence space           Low   Apr 02 | |
|  +----------------------------------------------------------+ |
|                                                                |
|  Completed today: 5                        [Show completed v]  |
+----------------------------------------------------------------+
```

`OVERDUE` badge: red-500 text. `TODAY` badge: amber-500 text. Checkboxes use Radix `Checkbox`. `->Jira` button creates a Jira ticket via Knowledge Hub MCP. Bulk select: shift+click range, then bulk action bar slides up from bottom.

### j) Chat `/chat`

```
+----------------------------------------------------------------+
|  CoCo Chat                                    [History] [Pop]  |
+----------------------------------------------------------------+
|                                                                |
|  History Sidebar (240px, toggle):                              |
|  +------------+                                               |
|  | Today      |  +------------------------------------------+ |
|  |  Budget Q  |  |                                          | |
|  |  Standup   |  |  [CoCo]  Good morning. 3 decisions       | |
|  | Yesterday  |  |          pending, 2 urgent emails.       | |
|  |  Risk rev  |  |          Cross Risk is green, OpsHub     | |
|  |  Deploy    |  |          amber — no Jira updates 48h.    | |
|  +------------+  |                                          | |
|                   |  [You]   Show me the OpsHub health       | |
|                   |          details.                        | |
|                   |                                          | |
|                   |  [CoCo]  OpsHub health breakdown:        | |
|                   |          - Last Jira sync: Mar 25 14:30  | |
|                   |          - 3 tickets stale (>48h)        | |
|                   |          - Confluence: OK (synced 2h)    | |
|                   |          **Recommendation:** Run Jira    | |
|                   |          sync now. [Run Sync]            | |
|                   |                                          | |
|                   +------------------------------------------+ |
|                                                                |
|  +----------------------------------------------------------+ |
|  | Type a message...                    [Attach] [Send ->]   | |
|  +----------------------------------------------------------+ |
+----------------------------------------------------------------+
```

Messages support markdown rendering (code blocks, bold, lists, links). CoCo avatar: small ASCII logo or emerald dot. Inline action buttons in messages (`[Run Sync]`) rendered as small ghost buttons. Input supports `Shift+Enter` for newline, `Enter` to send.

### k) Costs `/costs`

```
+----------------------------------------------------------------+
|  Costs                              [Today] [7d] [30d] [All]  |
+----------------------------------------------------------------+
|                                                                |
|  SPEND OVER TIME (area chart)                                  |
|  +----------------------------------------------------------+ |
|  | $12 |                                                     | |
|  | $10 |                         ___________                 | |
|  |  $8 |               _________/                            | |
|  |  $6 |          ____/                                      | |
|  |  $4 |     ____/                                           | |
|  |  $2 |____/                                                | |
|  |  $0 +-----|-----|-----|-----|-----|-----|----->            | |
|  |     Mon   Tue   Wed   Thu   Fri   Sat   Sun               | |
|  +----------------------------------------------------------+ |
|                                                                |
|  BY STATION (bar)             BY PROJECT (bar)                 |
|  +-------------------------+  +------------------------------+ |
|  | PM       [========] $4.20| | Cross Risk [=========] $6.10| |
|  | Ingest   [====]     $2.10| | OpsHub     [=====]    $3.50| |
|  | Exec     [======]   $3.50| | Personal   [=]        $0.80| |
|  | Review   [==]       $0.60| |                             | |
|  +-------------------------+  +------------------------------+ |
|                                                                |
|  BUDGET                                                        |
|  +----------------------------------------------------------+ |
|  | Daily:  $2.41 / $10.00  [========================>   ] 24%| |
|  | Weekly: $10.40 / $70.00 [===============>            ] 15%| |
|  | Monthly:$48.20 / $300   [=================>          ] 16%| |
|  +----------------------------------------------------------+ |
|                                                                |
|  RECENT EVENTS                                                 |
|  +----------------------------------------------------------+ |
|  | Time     | Station  | Tokens     | Cost   | Task          | |
|  | 09:41:02 | PM       | 1,589      | $0.023 | Classify email| |
|  | 09:40:55 | Ingest   | 847        | $0.004 | Embed doc     | |
|  | 09:38:10 | Exec     | 3,241      | $0.048 | Jira update   | |
|  | ...      | ...      | ...        | ...    | ...           | |
|  +----------------------------------------------------------+ |
+----------------------------------------------------------------+
```

Charts: use Recharts or visx. Area chart fill: `var(--accent)` at 20% opacity. Budget bars: green < 50%, amber 50-80%, red > 80%. All cost numbers in `JetBrains Mono`.

### l) Settings `/settings`

```
+----------------------------------------------------------------+
|  Settings                                                      |
+----------------------------------------------------------------+
|  [General] [Stations] [Autonomy] [Knowledge Hub] [About]      |
+----------------------------------------------------------------+
|                                                                |
|  GENERAL TAB:                                                  |
|  +----------------------------------------------------------+ |
|  | Theme              [Dark v]                               | |
|  | Sidebar default    [Expanded v]                           | |
|  | Chat position      [Right panel v]                        | |
|  | Daily budget limit  [$___10.00___]                        | |
|  | Notifications       [X] Desktop  [X] Sound  [ ] Email    | |
|  +----------------------------------------------------------+ |
|                                                                |
|  STATIONS TAB:                                                 |
|  +----------------------------------------------------------+ |
|  | Station          | Model        | Max $/day | Status      | |
|  | PM Station       | [opus-4 v]   | [$5.00]   | [Enabled]   | |
|  | Ingest Station   | [haiku-3 v]  | [$2.00]   | [Enabled]   | |
|  | Exec Station     | [sonnet-4 v] | [$3.00]   | [Enabled]   | |
|  | Review Station   | [sonnet-4 v] | [$2.00]   | [Disabled]  | |
|  | [+ Add Station]                                           | |
|  +----------------------------------------------------------+ |
|                                                                |
|  AUTONOMY TAB:                                                 |
|  +----------------------------------------------------------+ |
|  | Auto-classify emails       [X]                            | |
|  | Auto-create Jira tickets   [ ]  (requires approval)      | |
|  | Auto-send drafts           [ ]  (requires approval)      | |
|  | Auto-sync Confluence       [X]                            | |
|  | Trust threshold             [0.75____]                    | |
|  | Escalation: email to       [rijul_kalra@mckinsey.com]     | |
|  +----------------------------------------------------------+ |
|                                                                |
|  KNOWLEDGE HUB TAB:                                            |
|  +----------------------------------------------------------+ |
|  | SQLite DB path     [/path/to/knowledge.db]                | |
|  | Embedding model    [text-embedding-3-small v]             | |
|  | Chunk size         [512] tokens                           | |
|  | Overlap            [64] tokens                            | |
|  | Re-index           [Re-index Now]                         | |
|  +----------------------------------------------------------+ |
|                                                                |
|  ABOUT TAB:                                                    |
|  +----------------------------------------------------------+ |
|  |                                                           | |
|  |     ██████╗ ██████╗  ██████╗ ██████╗                     | |
|  |    ██╔════╝██╔═══██╗██╔════╝██╔═══██╗                    | |
|  |    ██║     ██║   ██║██║     ██║   ██║                     | |
|  |    ██║     ██║   ██║██║     ██║   ██║                     | |
|  |    ╚██████╗╚██████╔╝╚██████╗╚██████╔╝                    | |
|  |     ╚═════╝ ╚═════╝  ╚═════╝ ╚═════╝                    | |
|  |                                                           | |
|  |    CoCo Platform v1.0.0                                   | |
|  |    Multi-agent PM orchestration                           | |
|  |    Built by Rijul Kalra                                   | |
|  |                                                           | |
|  +----------------------------------------------------------+ |
+----------------------------------------------------------------+
```

Form controls: Radix `Select`, `Switch`, `Checkbox`. Input fields: `bg: var(--bg-base)`, `border: var(--border-default)`, focus ring `var(--accent)` 2px.

---

## 4. Key Components

### StationCard

```
Props: { name, role, model, status, currentTask, lastAction, costToday, onPause, onKill, onViewLogs }

Dimensions: min-w 280px, p-16px
Structure:
  - Header row: name (H3 Inter 15px 500) + status dot (8px circle, right-aligned)
  - Role: Body Small, text-secondary
  - Model: Caption, monospace, text-muted
  - Divider: 1px var(--border-subtle), my-12px
  - Task: Body, text-primary, truncate 1 line
  - Last action: Caption, text-muted, relative time
  - Cost: Data Small, monospace, text-secondary, "$X.XX today"
  - Divider
  - Actions: ghost button row — [Pause/Resume] [Kill] [Logs]

Status dot colors:
  - running: var(--accent) + subtle pulse animation
  - blocked: var(--warning)
  - error: var(--error) + pulse
  - idle: var(--text-muted)

Border: 1px var(--border-default), radius var(--r-lg)
Hover: border-color var(--border-default) -> var(--accent) at 50% opacity
```

### ProjectCard

```
Props: { name, status, itemCounts: { email, voice, jira, confluence, actionItems }, lastActivity, todoCount, onClick }

Dimensions: min-w 280px, p-16px
Structure:
  - Header row: name (H3) + health dot
  - Status text: Caption, colored by health
  - Source counts grid (2x3): each cell = pill icon + count in monospace
  - Last activity: Caption, text-muted, relative time + source type
  - Todo count: Caption, text-muted

Source count pills:
  - E (email):      bg zinc-800, text zinc-300
  - V (voice):      bg violet-900, text violet-300
  - J (Jira):       bg blue-900, text blue-300
  - C (Confluence): bg blue-900/50, text blue-200
  - AI (actions):   bg emerald-900, text emerald-300
```

### DecisionCard

```
Props: { type, title, description, timestamp, actions: Action[], metadata }

Type styles (left border 3px):
  - URGENT:   border var(--error),   bg var(--error-muted) at 20%
  - DRAFTS:   border var(--info),    bg var(--info-muted) at 20%
  - CLASSIFY: border var(--warning), bg var(--warning-muted) at 20%
  - HEALTH:   border #f97316,        bg rgba(249,115,22,0.1)
  - OVERDUE:  border var(--text-muted), bg transparent

Structure:
  - Title: H3 + type icon (Lucide: AlertTriangle, FileEdit, Tag, HeartPulse, Clock)
  - Description: Body, text-secondary, max 2 lines
  - Metadata: Caption, text-muted
  - Actions: row of small buttons (primary for main action, ghost for others)

Dimensions: full-width, p-16px, radius var(--r-md)
```

### ActivityFeedItem

```
Props: { timestamp, type, message, source, isNew }

Structure:
  - Timestamp: monospace Data Small, text-muted, fixed-width 56px
  - Source icon: 16px Lucide icon (Mail, Mic, GitBranch, FileText, Zap)
  - Message: Body, text-primary, flex-1, truncate 1 line

isNew animation:
  - slide in: translateY(-8px) -> 0 over 200ms
  - bg highlight: var(--accent-muted) -> transparent over 1500ms

Height: 36px. Hover: bg var(--bg-elevated).
```

### CostChart

```
Props: { data: TimeseriesPoint[], period, budget }

Renders:
  - Area chart (Recharts / visx)
  - Fill: var(--accent) at 15% opacity
  - Stroke: var(--accent) 2px
  - Grid lines: var(--border-subtle)
  - Axis labels: Data Small, text-muted
  - Tooltip: shadow-lg card with timestamp + cost, monospace numbers
  - Budget line: dashed var(--warning) horizontal line
```

### TrustMatrixGrid

```
Props: { stations: string[], matrix: number[][] }

Renders: n x n grid table
  - Headers: station names, Caption, text-secondary
  - Cells: trust score 0.00-1.00, Data Small monospace
  - Cell bg color interpolated:
    - < 0.5:  red-900 -> red-700
    - 0.5-0.75: amber-900 -> amber-700
    - 0.75-1.0: emerald-900 -> emerald-700
  - Diagonal: dashed, text-muted "--"
  - Cell size: 64x40px
  - Border: 1px var(--border-subtle) between cells
```

### ChatMessage

```
Props: { role: 'user' | 'coco', content: string (markdown), timestamp, actions?: InlineAction[] }

User message:
  - Align right, bg var(--bg-elevated), radius var(--r-lg), max-w 80%
  - Text: Body, text-primary

CoCo message:
  - Align left, bg var(--bg-surface), radius var(--r-lg), max-w 80%
  - Avatar: 24px emerald dot or CoCo mini-logo
  - Content: rendered markdown (react-markdown + remark-gfm)
  - Code blocks: bg var(--bg-base), radius var(--r-sm), JetBrains Mono
  - Inline actions: small ghost buttons below message body

Timestamp: Caption, text-muted, below bubble
```

### NotificationToast

```
Props: { type: 'info' | 'success' | 'warning' | 'error', title, description?, duration: 5000 }

Uses Radix Toast. Position: bottom-right, 16px from edges.
Width: 360px. Stack max 3, newest on top.

Structure:
  - Left icon: 20px, colored by type
  - Title: Body 500
  - Description: Body Small, text-secondary (optional)
  - Close X: top-right, 16px, text-muted

Slide in from right 200ms. Auto-dismiss with progress bar at bottom (2px, colored by type).
```

### CommandPalette (Cmd+K)

```
Uses cmdk library (palanikanat/cmdk).

Trigger: Cmd+K globally
Overlay: bg black at 50% opacity
Dialog: 560px wide, max-h 400px, top 20% of viewport

Structure:
  - Search input: 48px tall, no border, large text, auto-focus
  - Divider
  - Results list (ScrollArea, max 8 visible):
    - Group headers: Caption, text-muted, uppercase
    - Items: 40px rows, icon (20px) + label + shortcut hint (right)
    - Active: bg var(--bg-elevated)

Groups:
  - Navigation: Dashboard, Projects, Stations, Knowledge Hub, etc.
  - Actions: New Project, New Todo, Ingest File, Run Sync
  - Stations: Pause All, Resume All, View PM Station, etc.
  - Recent: last 5 visited pages

Keyboard: arrow keys to navigate, Enter to select, Escape to close.
```

---

## 5. Interaction Patterns

### Keyboard Shortcuts

| Shortcut      | Action                         |
|---------------|--------------------------------|
| `Cmd+K`       | Open command palette           |
| `Cmd+B`       | Toggle sidebar                 |
| `Cmd+J`       | Toggle chat panel              |
| `Cmd+D`       | Go to Dashboard                |
| `Cmd+1`       | Sidebar item 1 (Dashboard)     |
| `Cmd+2`       | Sidebar item 2 (Projects)      |
| `Cmd+3`       | Sidebar item 3 (Stations)      |
| `Cmd+4`       | Sidebar item 4 (Knowledge Hub) |
| `Cmd+5`       | Sidebar item 5 (Decisions)     |
| `Cmd+6`       | Sidebar item 6 (People)        |
| `Cmd+7`       | Sidebar item 7 (Todos)         |
| `Cmd+8`       | Sidebar item 8 (Costs)         |
| `Cmd+9`       | Sidebar item 9 (Settings)      |
| `Escape`      | Close panel / dialog / palette |
| `Cmd+Enter`   | Send chat message              |
| `Cmd+Shift+D` | Toggle dark/light mode         |

Shortcuts displayed in command palette and in tooltip hints. Register via `useHotkeys` hook or equivalent.

### Bulk Selection

- Available on: Todos, Knowledge Hub list, Decisions
- Activate: click checkbox on any item, or `Cmd+A` to select all visible
- Shift+click: range select
- Bulk action bar: slides up from bottom (56px), shows count + action buttons
  - Todos: [Mark Done] [Dismiss] [->Jira]
  - Knowledge Hub: [Re-classify] [Delete] [Assign Project]
  - Decisions: [Approve All] [Dismiss All]
- Escape to deselect all

### Real-Time Updates

- New feed items: slide in from top with `translateY(-8px)` animation (200ms)
- Background highlight: `var(--accent-muted)` fades to transparent over 1500ms
- Station status changes: dot color transitions over 300ms
- Cost counters: number ticks up with `tabular-nums` font feature
- Toast notification for high-priority events (urgent decisions, budget alerts, station errors)
- WebSocket connection indicator: small dot in sidebar footer (green = connected, red = disconnected)

### Loading States

- Initial page load: skeleton screens matching card/list layouts, pulse animation
- Data refresh: subtle spinner (16px) in section headers, content stays visible
- Empty states: centered illustration + message + primary action button
- Error states: red-tinted card with retry button

### Navigation

- All navigation via React Router v7
- Breadcrumbs on detail pages: `< Section / Item Name`
- Back navigation: breadcrumb click or browser back
- Deep links: every page, tab, and filter state is URL-encoded

---

## 6. The CoCo Feel

### Dark Cockpit Aesthetic

The interface should feel like a **mission control dashboard** — information-dense but not cluttered. Every pixel earns its place. The dark background (`#09090b`) lets colored status indicators and accent elements pop without competing for attention.

### Terminal-Inspired Data Displays

- All numerical data (costs, token counts, timestamps, IDs) rendered in `JetBrains Mono`
- Log streams styled like terminal output: monospace, color-coded severity, auto-scroll
- Cost values always show 2 decimal places: `$2.41`, not `$2.4`
- Timestamps in logs use `HH:mm:ss.SSS` format (monospace, fixed-width)
- Trust matrix values always `0.00` format
- Token counts use locale formatting: `1,247` not `1247`

### Glanceability (2-Second Rule)

A PM should understand system health within 2 seconds of looking at any page:

1. **Dashboard**: Three station dots (green/amber/red) + cost bar = instant health check
2. **Stations**: Status dots + current task = what is each agent doing right now
3. **Decisions**: Red count badge in sidebar = how many things need my attention
4. **Costs**: Budget progress bar color = am I on track

### CoCo Logo (Sidebar SVG)

The ASCII art logo from the About page, rendered as an SVG path for crisp display at any size. In the sidebar header, displayed at 32px height, `var(--accent)` color. On hover, subtle glow effect (`drop-shadow: 0 0 8px var(--accent) at 40%`).

Collapsed sidebar: logo only (no text), centered in 64px width.

### Personality Touches

- Empty states use CoCo voice: "Nothing here yet. Want me to go find something?" with a suggested action button
- Chat responses feel conversational, not robotic — the UI supports this with softer bubble shapes and the emerald avatar
- Station cards feel alive when running: the green dot pulses gently (1.5s ease-in-out)
- Subtle sound effects (optional, off by default): soft chime for new decisions, click for completed todos

### Information Density Principles

- Cards use 16px padding, 12px gap between sections
- No unnecessary whitespace — but breathing room between logical groups (24px between card groups)
- Tables use 40px row height with 12px horizontal padding
- Sidebar items: 36px height, 12px left padding
- Prefer inline data over drill-down when possible: show counts, costs, and status directly on cards

---

## 7. Error & Empty State Specifications

Every page and component must handle three states beyond "loaded with data": loading, empty, and error.

### Loading States

- **Skeleton screens** (not spinners) for all card grids and lists. Use `animate-pulse` on gray rectangles matching the shape of the content.
- **Inline loading** for actions: button text changes to "Approving..." with a subtle spinner icon. Button disabled during request.
- **SSE reconnecting**: thin yellow bar at top of activity feed: "Reconnecting..." Auto-dismiss on reconnect.

### Empty States

Each page has a specific empty state with a CoCo-voice message and a call to action:

| Page | Empty Message | CTA |
|---|---|---|
| Dashboard (no projects) | "No projects yet. Let's set one up." | "Add Project" button |
| Dashboard (all healthy, no items) | "All clear. Nothing needs your attention." | "Run Process" or "Open Chat" |
| Stations (none created) | "No stations running. Spawn one to get started." | "Create Station" button |
| Stations (all idle) | "All stations idle. Assign a task to wake one up." | "Create Task" button |
| Knowledge Hub (no content) | "Knowledge Hub is empty. Run an ingestion first." | "Process Now" button |
| Decisions (queue empty) | "Queue is clear. Nice work." | Confetti animation (subtle, 1s) |
| Todos (none open) | "Nothing on your plate. Enjoy the calm." | "Add Todo" or "Sync from KH" |
| People (none taught) | "No people tracked yet. Teach me who matters." | "Add Person" button |
| Search (no results) | "No matches for '{query}'. Try different keywords." | Suggested queries based on recent content |
| Costs (no data) | "No cost data yet. Costs appear after stations run." | Link to Stations page |
| Chat (no history) | "Start a conversation. I'm CoCo." | Pre-filled suggestions: "What's new?", "Catch me up", "Process my emails" |

### Error States

| Scenario | Display | Recovery |
|---|---|---|
| API endpoint returns 500 | Red banner at top of affected widget: "Failed to load {resource}. [Retry]" | Retry button re-fetches. Auto-retry after 30s. |
| API endpoint returns 404 | "Not found" page with back button | Navigate back |
| API unreachable (server down) | Full-page overlay: "CoCo Platform is offline. Checking..." with pulsing dot | Auto-reconnect every 5s. Dismiss when back. |
| SSE disconnected | Yellow bar: "Live updates paused. Reconnecting..." | EventSource auto-reconnects. Bar dismisses on reconnect. |
| hub.db read fails | Per-widget degradation: "Knowledge Hub data unavailable" with gray placeholder | "Check Health" link to /health page |
| brain.json corrupt | Toast: "brain.json was corrupt — backed up and reset to defaults" | Automatic recovery (same as think.py pattern) |
| Station crash | Toast: "Station '{name}' crashed (exit code {N})" + red status on card | "View Logs" button, "Restart" button |
| Budget exceeded | Dashboard banner: "Budget limit reached for {project}. Stations paused." | "Adjust Budget" link to settings |

### Error Boundaries

React error boundaries at three levels:
1. **Page-level**: catches crashes in any page component. Shows "Something went wrong on this page. [Reload Page]"
2. **Widget-level**: catches crashes in individual dashboard widgets. Other widgets continue working.
3. **App-level**: last resort. Shows "CoCo Platform encountered an error. [Reload App]" with a link to copy error details.

---

## 8. Accessibility

### Keyboard Navigation

- All interactive elements reachable via Tab
- Focus ring: 2px `var(--accent)` outline with 2px offset (visible on dark background)
- Skip-to-content link (hidden until focused): jumps past sidebar to main content
- Escape closes all dialogs, popovers, and slide-overs
- Arrow keys navigate within lists, grids, and menus
- Enter/Space activates buttons and toggles

### ARIA

- Sidebar navigation: `<nav aria-label="Main navigation">`
- Station status dots: `aria-label="Station triage is running"` (not just color)
- Health indicators: `aria-label="Email adapter status: warning"` (not just emoji)
- Decision queue tiers: `role="region" aria-label="Urgent items"`
- Activity feed: `role="log" aria-live="polite"` for real-time updates
- Chat messages: `role="log" aria-live="polite"`
- Loading skeletons: `aria-busy="true" aria-label="Loading..."`
- Toast notifications: `role="alert"`

### Color

- Never use color alone to convey meaning. All status indicators pair color with:
  - Icon shape (checkmark, warning triangle, X circle)
  - Text label ("Running", "Warning", "Failed")
- Contrast ratio: minimum 4.5:1 for body text, 3:1 for large text (WCAG AA)
- Focus ring visible in both dark and light themes

### Screen Reader

- Page titles update on route change: `<title>Dashboard — CoCo Platform</title>`
- Dynamic content updates announced via `aria-live` regions
- Charts include `aria-label` with text summary: `aria-label="Daily spend chart: $4.20 today, trending up 15% this week"`
- Tables use proper `<th scope="col">` headers

### Motion

- `prefers-reduced-motion` media query disables:
  - Skeleton pulse animations
  - Station status dot pulse
  - Activity feed slide-in transitions
  - Confetti on empty queue
- Replaced with instant state changes (no animation)
