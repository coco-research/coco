# Sprint 3 Plan: FEATURES -- "Build What Competitors Can't"

**Date:** 2026-03-28
**Duration:** 10-12 working days (2.5 weeks)
**Prerequisites:** Sprint 2 (FOUNDATION) must deliver Alembic migrations, Pydantic standardization, and the hub.db overlay migration for todos.

---

## Dependency Graph

```
INDEPENDENT (can start Day 1, parallel agents):
  [F1] Human-readable IDs
  [F5] Todo dependencies
  [F6] Desktop notifications
  [F8] Kokoro TTS replacement
  [F9] Floating mic button

DEPENDS ON F1:
  [F2] Unified search (needs human IDs to display in results)

DEPENDS ON Sprint 2 (Alembic + overlay pattern):
  [F3] Webhook/trigger automation
  [F4] Inter-agent delegation

DEPENDS ON F9:
  [F7] Deepgram streaming STT
  [F10] Voice-driven decision queue (needs mic + STT)
```

---

## Feature 1: Human-Readable IDs (`CXR-47`)

**Effort:** 1.5 days | **Risk:** Low | **Independent:** Yes

### Schema (platform.db)
```sql
ALTER TABLE nodes ADD COLUMN prefix TEXT;

CREATE TABLE IF NOT EXISTS id_sequences (
    node_id TEXT PRIMARY KEY REFERENCES nodes(id),
    next_seq INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS todo_identifiers (
    hub_todo_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    sequence_num INTEGER NOT NULL,
    display_id TEXT NOT NULL,
    UNIQUE(node_id, sequence_num)
);
CREATE INDEX idx_todo_ident_display ON todo_identifiers(display_id);
```

### Backend
| File | Change |
|------|--------|
| `backend/app/db/init_db.py` | Add new tables |
| `backend/app/routers/tree.py` | PATCH support for `prefix` field |
| `backend/app/routers/todos.py` | On POST, insert into `todo_identifiers` with atomic sequence increment. On GET, LEFT JOIN to return `display_id` |
| `backend/app/services/id_generator.py` | **New.** `generate_display_id(node_id) -> str` |

### Frontend
| File | Change |
|------|--------|
| `frontend/src/pages/TodosPage.tsx` | Display `display_id` badge before todo title |
| `frontend/src/types/` | Add `display_id?: string` to Todo type |

### New endpoint
- `GET /api/todos/by-id/{display_id}` -- resolve `CXR-47` to full todo

---

## Feature 2: Unified Search in Cmd+K

**Effort:** 2 days | **Risk:** Low | **Depends on:** F1

### Backend
| File | Change |
|------|--------|
| `backend/app/routers/search.py` | **New.** `GET /api/search?q={query}&types=todos,agents,content,goals,drafts&limit=10`. Queries across 5 entity types. Returns `{ type, id, title, subtitle, url, display_id? }` |
| `backend/app/main.py` | Register search router |

### Frontend
| File | Change |
|------|--------|
| `frontend/src/components/shared/CommandPalette.tsx` | Add "Search Results" section when query >= 2 chars. Debounce 300ms. Show results grouped by type with icons. |

---

## Feature 3: Webhook/Trigger-Based Automation

**Effort:** 5-6 days | **Risk:** Medium-High | **Depends on:** Sprint 2

### Schema
```sql
CREATE TABLE IF NOT EXISTS triggers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('cron', 'webhook', 'file_watch')),
    enabled INTEGER NOT NULL DEFAULT 1,
    config TEXT NOT NULL DEFAULT '{}',
    action_type TEXT NOT NULL CHECK(action_type IN ('spawn_agent', 'run_command', 'create_todo', 'notify')),
    action_config TEXT NOT NULL DEFAULT '{}',
    last_fired_at TEXT,
    fire_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trigger_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_id TEXT NOT NULL REFERENCES triggers(id),
    fired_at TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'skipped')),
    result TEXT,
    error TEXT
);
```

### Backend
| File | Change |
|------|--------|
| `backend/app/routers/triggers.py` | **New.** CRUD + `POST /api/webhooks/{trigger_id}` |
| `backend/app/services/trigger_engine.py` | **New.** Cron scheduler, file watcher, webhook handler |
| `backend/app/main.py` | Register + start trigger engine on startup |

### Frontend
| File | Change |
|------|--------|
| `frontend/src/pages/SettingsPage.tsx` | Add "Automations" tab |
| `frontend/src/components/triggers/TriggerForm.tsx` | **New.** Create/edit form |
| `frontend/src/components/triggers/TriggerList.tsx` | **New.** List with enable/disable |

---

## Feature 4: Inter-Agent Delegation

**Effort:** 5-6 days | **Risk:** High | **Depends on:** Sprint 2

### Schema additions
```sql
ALTER TABLE tasks ADD COLUMN delegated_by TEXT;
ALTER TABLE tasks ADD COLUMN delegated_to TEXT;
ALTER TABLE tasks ADD COLUMN parent_task_id TEXT;
ALTER TABLE tasks ADD COLUMN context_json TEXT DEFAULT '{}';

CREATE TABLE IF NOT EXISTS task_board (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT 'Shared Board',
    agent_ids TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Backend
| File | Change |
|------|--------|
| `backend/app/routers/tasks.py` | `POST /api/tasks/{id}/delegate`, `GET /api/agents/{id}/task-queue` |
| `backend/app/routers/collaboration.py` | Auto-delegate on workflow advance |
| `backend/app/services/delegation.py` | **New.** DelegationService |

### Frontend
| File | Change |
|------|--------|
| `frontend/src/components/agents/DelegationPanel.tsx` | **New.** Delegation chain view |
| `frontend/src/components/agents/SharedTaskBoard.tsx` | **New.** Kanban per node |

---

## Feature 5: Todo Dependencies

**Effort:** 1.5 days | **Risk:** Low | **Independent:** Yes

### Schema
```sql
CREATE TABLE IF NOT EXISTS todo_dependencies (
    id TEXT PRIMARY KEY,
    todo_id TEXT NOT NULL,
    depends_on TEXT NOT NULL,
    dep_type TEXT NOT NULL DEFAULT 'blocked_by',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(todo_id, depends_on)
);
```

### Backend
| File | Change |
|------|--------|
| `backend/app/routers/todos.py` | `POST/DELETE/GET /api/todos/{id}/dependencies`. Add `blocked_by_count` to list response. |

### Frontend
| File | Change |
|------|--------|
| `frontend/src/pages/TodosPage.tsx` | Blocked/blocking badges |
| `frontend/src/components/todos/DependencyGraph.tsx` | **New.** Simple DAG view |

---

## Feature 6: Desktop Notifications

**Effort:** 1 day | **Risk:** Low | **Independent:** Yes

### Frontend only
| File | Change |
|------|--------|
| `frontend/src/lib/desktop-notifications.ts` | **New.** Web Notification API wrapper |
| `frontend/src/components/shared/NotificationProvider.tsx` | Call desktop notification for urgent events |
| `frontend/src/pages/SettingsPage.tsx` | Toggle + permission request |

---

## Feature 7: Deepgram Streaming STT

**Effort:** 3 days | **Risk:** Medium | **Depends on:** F9

### Backend
| File | Change |
|------|--------|
| `backend/app/routers/stt.py` | **New.** `POST /api/stt/token` for Deepgram session key |
| `backend/app/config.py` | Add `DEEPGRAM_API_KEY` env var |

### Frontend
| File | Change |
|------|--------|
| `frontend/src/hooks/useVoiceInput.ts` | Rewrite to use Deepgram WebSocket streaming |
| `frontend/src/lib/deepgram.ts` | **New.** Deepgram WebSocket client |

---

## Feature 8: Kokoro TTS Replacement

**Effort:** 2 days | **Risk:** Medium | **Independent:** Yes

### Backend
| File | Change |
|------|--------|
| `backend/app/routers/tts.py` | Add Kokoro as priority 0 engine |
| `backend/app/services/kokoro_engine.py` | **New.** Lazy-loading Kokoro wrapper |
| `backend/pyproject.toml` | Add `kokoro` dependency |

**TTS cascade:** Kokoro > Piper > Edge TTS > OpenAI TTS > macOS `say`

---

## Feature 9: Floating Mic Button

**Effort:** 1 day | **Risk:** Low | **Independent:** Yes

### Frontend only
| File | Change |
|------|--------|
| `frontend/src/components/shared/FloatingMic.tsx` | **New.** Fixed bottom-right, pulsing, transcript bubble |
| `frontend/src/components/layout/AppShell.tsx` | Render FloatingMic (hidden on /jarvis) |
| `frontend/src/App.tsx` | Global voice command routing |

---

## Feature 10: Voice-Driven Decision Queue

**Effort:** 2 days | **Risk:** Medium | **Depends on:** F7, F9

### Backend
| File | Change |
|------|--------|
| `backend/app/routers/jarvis.py` | Add approve/reject/next voice commands |

### Frontend
| File | Change |
|------|--------|
| `frontend/src/pages/InboxPage.tsx` | "Voice Mode" toggle, flashcard display |
| `frontend/src/components/inbox/VoiceDecisionCard.tsx` | **New.** Large-format decision card with TTS |

---

## Schedule (4 parallel agents, 8 days)

| Day | Agent A | Agent B | Agent C | Agent D |
|-----|---------|---------|---------|---------|
| 1 | F1: Human IDs (backend) | F5: Todo deps (backend) | F6: Desktop notifications | F8: Kokoro TTS |
| 1 | **+BF batch** (see below) | | | |
| 2 | F1: Human IDs (frontend) | F5: Todo deps (frontend) | F9: Floating mic | F8: Kokoro (polish) |
| 2 | **+BF batch** (see below) | | | |
| 3 | F2: Unified search (backend) | F3: Triggers (schema+CRUD) | F9: Voice routing | F7: Deepgram (backend) |
| 4 | F2: Search (frontend) | F3: Triggers (cron engine) | F7: Deepgram (WebSocket) | F4: Delegation (schema) |
| 5 | F2: Search (polish) | F3: Triggers (file watch) | F7: Deepgram (hook rewrite) | F4: Delegation (endpoints) |
| 6 | F10: Voice queue (backend) | F3: Triggers (frontend) | F7: Deepgram (fallback) | F4: Delegation (auto-spawn) |
| 7 | F10: Voice queue (frontend) | F3: Triggers (polish) | Integration testing | F4: Delegation (frontend) |
| 8 | F10: Voice queue (polish) | **+BF batch** (see below) | Integration testing | F4: Delegation (board) |

---

## New Files Summary

| File | Feature |
|------|---------|
| `backend/app/services/id_generator.py` | F1 |
| `backend/app/routers/search.py` | F2 |
| `backend/app/routers/triggers.py` | F3 |
| `backend/app/services/trigger_engine.py` | F3 |
| `backend/app/services/delegation.py` | F4 |
| `backend/app/routers/stt.py` | F7 |
| `backend/app/services/kokoro_engine.py` | F8 |
| `frontend/src/lib/desktop-notifications.ts` | F6 |
| `frontend/src/lib/deepgram.ts` | F7 |
| `frontend/src/components/shared/FloatingMic.tsx` | F9 |
| `frontend/src/components/todos/DependencyGraph.tsx` | F5 |
| `frontend/src/components/agents/DelegationPanel.tsx` | F4 |
| `frontend/src/components/agents/SharedTaskBoard.tsx` | F4 |
| `frontend/src/components/inbox/VoiceDecisionCard.tsx` | F10 |
| `frontend/src/components/triggers/TriggerForm.tsx` | F3 |
| `frontend/src/components/triggers/TriggerList.tsx` | F3 |

---

## Bug Fixes & Audit Items (from 12-Agent Deep Analysis, 2026-03-28)

These 27 items were captured by a 12-agent audit (PM, Architect, Bug Hunter, Security Engineer, Voice Specialist, 2x Wiring Engineers, Senior Dev, Backend Auditor, Frontend Auditor, Data Auditor, Roadmap Auditor). They are slotted into Sprint 3 days alongside feature work.

### Already Fixed (Sprint 2 / current session) — 28 items ✓

| # | Issue | Fix Applied |
|---|-------|-------------|
| 1 | Chat stream 64KB buffer overflow | `limit=1024*1024` in `chat.py` subprocess |
| 2 | `python` command not found | Changed to `uv run python` in `jarvis.py`, `home.py` |
| 3 | Shadow `CommandResponse` type blocks Jarvis cards | Removed duplicate interface in `JarvisInput.tsx` |
| 4 | Hardcoded claude CLI path | `shutil.which()` fallback in `jarvis.py` |
| 5 | Drafts table name mismatch (`pm_drafts`) | Corrected to `drafts` + JOIN in `jarvis.py` |
| 6 | Process command returns filtered-out card type | Returns `health_detail` card now |
| 7 | `cmd_decide` shows project_id not name | Added JOIN to projects table |
| 8 | Stale briefing (`staleTime: Infinity`) | Changed to 5-minute staleTime |
| 9 | Audio doesn't stop on interaction | `cancelSpeak()` called on interact |
| 10 | Missing `edge-tts` dependency | Added to `pyproject.toml` |
| 11 | Command injection via macOS `say` | Text passed via stdin |
| 12 | Prompt injection via CLI arg | Text passed via stdin |
| 13 | No input validation on `CommandRequest` | `max_length=5000` |
| 14 | No input validation on `TTSRequest` | `max_length=2000` |
| 15 | URL parameter injection in search | `urlencode()` |
| 16 | Open redirect via navigate | Validates `startsWith('/')` |
| 17 | Duplicate AudioContext creation | Reuses engine context |
| 18 | Missing audio cleanup on unmount | Added `destroy()` method |
| 19 | Blob URL memory leaks | Cleanup in destroy |
| 20 | Nested setTimeout not in cleanup array | All timers tracked |
| 21 | SVG missing viewBox | Added to HealthRing |
| 22 | Invalid animation syntax | Inline style in BriefingSequence |
| 23 | Command hints incomplete | All 9 commands listed |
| 24 | Hub.db draft writes | `draft_decisions` overlay in platform.db |
| 25 | Hub.db content classify/dismiss no-ops | `content_classifications` overlay in platform.db |
| 26 | Goals table outside schema | Moved to `init_db.py` SCHEMA |
| 27 | Jarvis → Chat escalation missing | `suggest_chat` action + "Continue in Chat" button |
| 28 | Blocking subprocess in `home.py` | `asyncio.to_thread()` |

### BF Batch Day 1: Data Integrity + Security (~5h, alongside F1/F5/F6/F8)

These items are small, independent, and fit naturally as warm-up or end-of-day work for any agent.

| # | Task | Found By | Effort | Priority | File(s) |
|---|------|----------|--------|----------|---------|
| BF-1 | Todo overlay table in platform.db (same overlay pattern as drafts) | Data Auditor | 2h | HIGH | `init_db.py`, `todos.py` |
| BF-2 | DOMPurify in MessageBubble (replace regex HTML sanitization) | Security | 1h | HIGH | `MessageBubble.tsx`, `package.json` |
| BF-3 | Subprocess concurrency limiter (`asyncio.Semaphore(5)`) | Security | 30m | MEDIUM | `jarvis.py`, `home.py`, `tts.py` |
| BF-4 | `_build_briefing()` null check in `cmd_briefing` | Bug Hunter | 10m | MEDIUM | `jarvis.py` |
| BF-5 | CORS tightening (explicit methods/headers) | Security | 15m | LOW | `main.py` |
| BF-6 | FTS5 fallback logging when `content_fts` missing | Data Auditor | 15m | LOW | `content.py` |
| BF-7 | `cmd_costs` stale data — cache-bust `get_home()` | PM | 15m | LOW | `jarvis.py` |
| BF-8 | Move 3 inline `get_home` imports to module-level | Architect | 10m | LOW | `jarvis.py` |

### BF Batch Day 2: UX Polish (~2.5h, alongside F1-frontend/F5-frontend/F9)

Quick rendering and type fixes that any frontend agent can batch in 1 hour.

| # | Task | Found By | Effort | Priority | File(s) |
|---|------|----------|--------|----------|---------|
| BF-9 | `jarvis-waveform` uses `height` (reflow) → `transform: scaleY()` | Senior Dev | 15m | MEDIUM | `index.css`, `BriefingSequence.tsx` |
| BF-10 | Code block copy button in MessageBubble | Frontend Auditor | 30m | LOW | `MessageBubble.tsx` |
| BF-11 | NavigateHintCard auto-nav — add "Cancel" button | PM | 20m | LOW | `NavigateHintCard.tsx` |
| BF-12 | Grid gap not responsive → `gap-3 sm:gap-4 md:gap-6` | Senior Dev | 10m | LOW | `JarvisPage.tsx` |
| BF-13 | `HomeProject.active` type `number` → `boolean` | Bug Hunter | 5m | LOW | `types/home.ts` |
| BF-14 | Remove unused `jira_preview` from CardType union | Architect | 5m | LOW | `types/cards.ts` |
| BF-15 | Array index as React key in MetricScene → content-based | Bug Hunter | 10m | LOW | `BriefingSequence.tsx` |
| BF-16 | Dismiss command canvas flicker | PM | 15m | LOW | `JarvisPage.tsx` |

### BF Batch Day 2 cont: Project Detail (~4h, fills remaining time)

| # | Task | Found By | Effort | Priority | File(s) |
|---|------|----------|--------|----------|---------|
| BF-17 | ProjectDetailPage — complete People tab | Frontend Auditor | 2h | MEDIUM | `ProjectDetailPage.tsx` |
| BF-18 | ProjectDetailPage — agent management within project | Frontend Auditor | 2h | MEDIUM | `ProjectDetailPage.tsx` |

### BF Batch Day 8: Voice/Jarvis Polish (~1.5h, alongside integration testing)

Slot alongside integration testing day — quick voice fixes before final validation.

| # | Task | Found By | Effort | Priority | File(s) |
|---|------|----------|--------|----------|---------|
| BF-19 | Force-stop oscillator nodes on destroy (bypass 2.2s fade) | Voice | 15m | LOW | `useJarvisAudio.ts` |
| BF-20 | TTS prefetch failure logging | Voice | 10m | LOW | `useJarvisAudio.ts` |
| BF-21 | Friendly mic permission error messages | Voice | 15m | LOW | `useVoiceInput.ts` |
| BF-22 | `drop-shadow` on HealthRing SVG → `box-shadow` or CSS var | Senior Dev | 20m | LOW | `HealthRing.tsx` |
| BF-23 | TTS cache unique filenames for Piper/Edge (race condition) | Security + Voice | 15m | LOW | `tts.py` |

### BF Stretch: If Time Permits

| # | Task | Found By | Effort | Priority | File(s) |
|---|------|----------|--------|----------|---------|
| BF-24 | Goal status transitions (visual workflow) | Frontend Auditor | 2h | LOW | `GoalsPage.tsx` |
| BF-25 | Jarvis session memory (last 5 commands) | PM | 3h | MEDIUM | `JarvisInput.tsx`, `jarvis.py` |
| BF-26 | Jarvis inline actions (create todo, approve draft) | PM | 3h | MEDIUM | `jarvis.py`, `JarvisInput.tsx` |
| BF-27 | Smoke test validation (run full suite, fix failures) | Roadmap Auditor | 2h | HIGH | `scripts/smoke-test.sh` |

### BF Summary

| Batch | Day | Items | Effort | HIGH | MED | LOW |
|-------|-----|-------|--------|------|-----|-----|
| Day 1 | 1 | 8 | ~5h | 2 | 2 | 4 |
| Day 2 | 2 | 10 | ~6.5h | 0 | 3 | 7 |
| Day 8 | 8 | 5 | ~1.5h | 0 | 0 | 5 |
| Stretch | any | 4 | ~10h | 1 | 2 | 1 |
| **Total** | | **27** | **~23h** | **3** | **7** | **17** |

**Strategy:** BF-1 and BF-2 (HIGH) must be done Day 1. BF-27 (smoke tests) should be Day 8 with integration testing. Everything else is slotted by theme affinity — data items on Day 1, UX on Day 2, voice on Day 8.

---

## UX Elevation Features (from Gap Analysis Top 10 — not in original Sprint 3)

These 3 features were ranked #1, #2, #3 in the comprehensive gap analysis (vs Paperclip, Linear, Notion) but weren't in the Sprint 3 feature list. They transform CoCo from "dashboard" to "control plane."

### UX-1: Live Agent Status via SSE (Gap Analysis #1)

**Impact:** Critical | **Effort:** 1.5 days | **Independent:** Yes (can start Day 1)
**Why:** The single biggest signal that makes an agent tool feel "alive." Paperclip has pulsing blue dots. Cursor shows live agent activity. CoCo polls every 3s — no visual heartbeat.

**Backend:**
| File | Change |
|------|--------|
| `backend/app/routers/events.py` | Emit `agent_status` events on spawn/pause/kill/heartbeat via existing SSE stream |
| `backend/app/services/process_manager.py` | Push status changes to an `asyncio.Queue` consumed by SSE |

**Frontend:**
| File | Change |
|------|--------|
| `frontend/src/hooks/useAgentSSE.ts` | **New.** Hook that subscribes to `/api/events/stream` and filters `agent_status` events |
| `frontend/src/components/agents/AgentCard.tsx` | Add pulsing dot (CSS `animate-pulse` with status color). Wire to SSE hook. |
| `frontend/src/components/dashboard/AgentStatusBar.tsx` | Live count updates without polling |
| `frontend/src/components/agents/LogViewer.tsx` | Stream logs via SSE instead of polling |

**Schedule fit:** Agent C or D, Day 1-2 (independent, can parallel with F1/F5/F6/F8)

---

### UX-2: Pervasive Inline Editing (Gap Analysis #2)

**Impact:** High | **Effort:** 2 days | **Independent:** Yes
**Why:** `InlineEditor` component already exists and works on GoalsPage. But todo titles, agent names, project names, task descriptions — all read-only. Linear lets you click any field to edit. This is the #1 UX signal separating "viewer" from "tool."

**Frontend:**
| File | Change |
|------|--------|
| `frontend/src/components/todos/TodoList.tsx` | Wrap todo titles in `<InlineEditor>` with PATCH callback |
| `frontend/src/components/agents/AgentCard.tsx` | Inline edit agent name + task description |
| `frontend/src/components/tasks/TaskList.tsx` | Inline edit task titles |
| `frontend/src/pages/GoalsPage.tsx` | Already done ✓ (reference implementation) |
| `frontend/src/pages/ProjectDetailPage.tsx` | Inline edit project name in header |
| `frontend/src/components/shared/InlineEditor.tsx` | Add `onBlur` auto-save, `Escape` to cancel (if not already) |

**No backend changes** — all entities already have PATCH endpoints.

**Schedule fit:** Any agent, Day 3-4 (after Day 1-2 features land, apply InlineEditor broadly)

---

### UX-3: Properties Panel (Slide-Out Detail) (Gap Analysis #3)

**Impact:** High | **Effort:** 2.5 days | **Independent:** Yes
**Why:** Paperclip's `PropertiesPanel` is the primary interaction model — click a row, see details on the right without losing list context. CoCo uses modals or full-page navigations. A slide-out panel keeps the user in flow.

**Frontend:**
| File | Change |
|------|--------|
| `frontend/src/components/shared/PropertiesPanel.tsx` | Exists but needs generalization. Add: slide-in animation (translate-x), backdrop click to close, keyboard Escape, resizable width. |
| `frontend/src/pages/TodosPage.tsx` | Click todo row → open PropertiesPanel with todo detail instead of modal |
| `frontend/src/pages/AgentsPage.tsx` | Click agent card → slide-out with full config, logs, cost |
| `frontend/src/pages/GoalsPage.tsx` | Click goal → slide-out with description, linked todos, progress |
| `frontend/src/pages/KnowledgePage.tsx` | Already uses a slide-out pattern for ContentDetail ✓ (reference) |

**Schedule fit:** Any agent, Day 4-5 (after InlineEditor pass, layer on slide-out)

---

### Parallelized Schedule (8 agents, 5 days)

Key insight: split every feature into backend + frontend agents. Independent features all start Day 1. Bug fixes get their own dedicated agent.

**Agent Roles:**
| Agent | Specialty | Focus |
|-------|-----------|-------|
| BE-1 | Backend | Schema, APIs, services |
| BE-2 | Backend | Schema, APIs, services |
| BE-3 | Backend | Voice/TTS engines |
| FE-1 | Frontend | Pages, components |
| FE-2 | Frontend | Pages, components |
| FE-3 | Frontend | UX (inline editing, properties panel) |
| FE-4 | Frontend | Voice UI, mic, Jarvis |
| QA | Full-stack | Bug fixes, polish, smoke tests |

---

#### Day 1: All Independent Features Launch (8 agents)

| Agent | Morning | Afternoon |
|-------|---------|-----------|
| **BE-1** | F1: Human IDs — schema + `id_generator.py` + todos endpoint | F5: Todo deps — schema + endpoints |
| **BE-2** | UX-1: Agent SSE — `process_manager.py` push + `events.py` emit | F6: Desktop notifications — no backend needed (idle → help BE-1) |
| **FE-1** | F1: Human IDs — display_id badges in TodosPage | F5: Todo deps — blocked/blocking badges + DependencyGraph |
| **FE-2** | F6: Desktop notifications — `desktop-notifications.ts` + settings toggle | UX-1: Agent SSE — `useAgentSSE.ts` hook + pulsing dots on AgentCard |
| **FE-3** | UX-2: Inline editing — TodoList, AgentCard, TaskList (no deps) | UX-2: Inline editing — ProjectDetailPage header, polish InlineEditor |
| **FE-4** | F9: Floating mic — `FloatingMic.tsx` + AppShell integration | F9: Voice command routing in App.tsx |
| **BE-3** | F8: Kokoro TTS — `kokoro_engine.py` + integrate in tts.py cascade | F8: Kokoro polish + fallback testing |
| **QA** | BF-1: Todo overlay table (HIGH, 2h) | BF-2: DOMPurify in MessageBubble (HIGH, 1h) |
| **QA** | BF-3: Subprocess semaphore (30m) | BF-4/5/6/7/8: Quick fixes batch (1h) |

**Day 1 output:** F1, F5, F6, F8, F9, UX-1, UX-2 all **backend-complete** or **fully done**. BF-1 through BF-8 done.

---

#### Day 2: Dependent Features Start + UX Polish (8 agents)

| Agent | Morning | Afternoon |
|-------|---------|-----------|
| **BE-1** | F2: Unified search — `search.py` router (can start, uses existing IDs) | F2: Search polish + edge cases |
| **BE-2** | F3: Triggers — schema + CRUD endpoints in `triggers.py` | F3: Trigger engine — cron scheduler |
| **FE-1** | F2: Search — wire into CommandPalette, grouped results | F2: Search debounce, result categories |
| **FE-2** | UX-1: SSE — AgentStatusBar live counts + LogViewer streaming | UX-3: Properties panel — generalize component (slide-in, escape, resize) |
| **FE-3** | UX-3: Properties panel — wire to TodosPage + AgentsPage | UX-3: Properties panel — wire to GoalsPage |
| **FE-4** | BF-17: ProjectDetailPage People tab (2h) | BF-18: ProjectDetailPage agent management (2h) |
| **BE-3** | F7: Deepgram — `stt.py` token endpoint + config | F7: Deepgram — WebSocket proxy if needed |
| **QA** | BF-9 through BF-16: UX polish batch (2.5h) | BF-25: Jarvis session memory (3h) |

**Day 2 output:** F2, F3-CRUD, F7-backend, UX-3 all done. ProjectDetail tabs complete. UX polish batch done.

---

#### Day 3: Heavy Features (Triggers Engine, Delegation, Deepgram) (8 agents)

| Agent | Morning | Afternoon |
|-------|---------|-----------|
| **BE-1** | F4: Delegation — schema + `delegation.py` service | F4: Delegation — `POST /tasks/{id}/delegate` + agent task queue |
| **BE-2** | F3: Triggers — file watcher engine | F3: Triggers — webhook handler |
| **FE-1** | F3: Triggers — `TriggerForm.tsx` + `TriggerList.tsx` | F3: Triggers — Settings "Automations" tab |
| **FE-2** | F4: Delegation — `DelegationPanel.tsx` | F4: Delegation — `SharedTaskBoard.tsx` |
| **FE-3** | BF-24: Goal status transitions (2h) | BF-26: Jarvis inline actions (3h — create todo, approve draft) |
| **FE-4** | F7: Deepgram — rewrite `useVoiceInput.ts` with WebSocket streaming | F7: Deepgram — fallback to Web Speech API on failure |
| **BE-3** | F4: Delegation — auto-delegate on workflow advance | F10: Voice queue — backend commands in jarvis.py |
| **QA** | Integration testing — F1+F2 end-to-end (search by human ID) | Integration testing — F5 (dependency blocking) + F6 (notifications) |

**Day 3 output:** F3, F4, F7 all feature-complete. Jarvis inline actions done.

---

#### Day 4: Voice Features + Integration (8 agents)

| Agent | Morning | Afternoon |
|-------|---------|-----------|
| **BE-1** | F10: Voice queue — approve/reject/next voice commands | F10: Polish + edge cases |
| **FE-1** | F10: Voice queue — `VoiceDecisionCard.tsx` + InboxPage voice mode | F10: Voice queue — TTS narration of decisions |
| **FE-2** | F3: Triggers polish — enable/disable toggle, error states | F4: Delegation polish — delegation chain visualization |
| **FE-3** | F7: Deepgram — FloatingMic integration with streaming STT | F7: Deepgram — live transcript in FloatingMic bubble |
| **FE-4** | UX-2: Inline editing — second pass (any pages missed) | UX-3: Properties panel — second pass + keyboard nav |
| **BE-2** | F3: Triggers — integration testing (cron fires, webhook receives) | Idle / help QA |
| **BE-3** | BF-19/20/21/22/23: Voice polish batch (1.5h) | Idle / help QA |
| **QA** | Integration testing — F3 (trigger fires → agent spawns) | Integration testing — F4 (delegation chain end-to-end) |

**Day 4 output:** F10 done. All features code-complete. Voice polish done.

---

#### Day 5: Integration Testing + Final Polish (8 agents)

| Agent | Morning | Afternoon |
|-------|---------|-----------|
| **BE-1** | Integration testing — all backend endpoints regression | Fix any failures |
| **BE-2** | Integration testing — SSE streaming end-to-end | Fix any failures |
| **BE-3** | Integration testing — TTS cascade (Kokoro → Edge → macOS) | Fix any failures |
| **FE-1** | Integration testing — all 15 pages load without errors | Fix any failures |
| **FE-2** | Integration testing — voice flow (mic → STT → command → TTS) | Fix any failures |
| **FE-3** | BF-24: Goal status transitions (if not done Day 3) | Polish pass — responsive, dark theme consistency |
| **FE-4** | BF-27: Smoke test validation (run full suite) | Fix smoke test failures |
| **QA** | End-to-end: morning check-in flow (Jarvis → briefing → act → chat) | End-to-end: delegate-to-agent flow (task → agent → review) |

**Day 5 output:** All 40 items verified. Sprint 3 complete.

---

### Comparison: 4 agents × 8 days vs 8 agents × 5 days

| Metric | Old (4×8) | New (8×5) | Improvement |
|--------|-----------|-----------|-------------|
| Calendar days | 8 | 5 | **37% faster** |
| Agent-days | 32 | 40 | +25% agent capacity |
| Idle time | ~8 agent-days | ~2 agent-days | **75% less waste** |
| Features done by Day 1 | 0 | 6 (F1,F5,F6,F8,F9,UX-1) | **Day 1 visible progress** |
| All BF items done by | Day 8 | Day 4 | **50% sooner** |
| Integration testing days | 1 | 2 (Day 4 partial + Day 5 full) | More thorough |

### Critical Path

```
Day 1: F1 (Human IDs) ─────→ Day 2: F2 (Search needs IDs)
Day 1: F9 (Floating mic) ──→ Day 3: F7 (Deepgram needs mic) ──→ Day 4: F10 (Voice queue needs STT)
Day 2: F3-CRUD ────────────→ Day 3: F3-engine ──→ Day 4: F3-polish
Day 3: F4-schema ──────────→ Day 3: F4-endpoints ──→ Day 4: F4-polish
```

Longest path: F9 → F7 → F10 (3 days). Sprint cannot be shorter than 5 days due to this chain.

### New Files (complete list)

| File | Feature |
|------|---------|
| `backend/app/services/id_generator.py` | F1 |
| `backend/app/routers/search.py` | F2 |
| `backend/app/routers/triggers.py` | F3 |
| `backend/app/services/trigger_engine.py` | F3 |
| `backend/app/services/delegation.py` | F4 |
| `backend/app/routers/stt.py` | F7 |
| `backend/app/services/kokoro_engine.py` | F8 |
| `frontend/src/hooks/useAgentSSE.ts` | UX-1 |
| `frontend/src/lib/desktop-notifications.ts` | F6 |
| `frontend/src/lib/deepgram.ts` | F7 |
| `frontend/src/components/shared/FloatingMic.tsx` | F9 |
| `frontend/src/components/todos/DependencyGraph.tsx` | F5 |
| `frontend/src/components/agents/DelegationPanel.tsx` | F4 |
| `frontend/src/components/agents/SharedTaskBoard.tsx` | F4 |
| `frontend/src/components/inbox/VoiceDecisionCard.tsx` | F10 |
| `frontend/src/components/triggers/TriggerForm.tsx` | F3 |
| `frontend/src/components/triggers/TriggerList.tsx` | F3 |
