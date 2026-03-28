# CoCo Platform — Sprint Review & Next Sprint Plan

**Date:** 2026-03-28
**Sprint:** Gap Analysis + Critical Fixes
**Author:** Rijul Kalra (with AI assistance)
**Agents Used:** 12 (8 Jarvis specialists + 4 platform auditors)

---

## 1. What Was Found (Gap Analysis)

### Audit Scope
- 8 specialist agents audited Jarvis (PM, Architect, Bug Hunter, Security, Voice, 2x Wiring, Senior Dev)
- 4 audit agents swept entire platform (Backend APIs, Frontend Pages, Database Schema, Roadmap Completion)

### Headline Numbers

| Dimension | Score | Detail |
|-----------|-------|--------|
| Roadmap | 99% | 96/97 acceptance criteria met across all 12 phases |
| Backend | 99% | 150/152 endpoints working, 2 intentional stubs |
| Frontend | 85% | All 15 routes functional, some pages partial |
| Data Layer | 92% | 23 tables, 5 data flow gaps |
| Bonus Features | +15 | Org hierarchy, Jarvis, TTS, collaboration, templates, etc. |

---

## 2. What Was Fixed (This Sprint)

### Jarvis Audit Fixes (23 issues found, all critical/high fixed)

| Issue | Severity | Status | File(s) |
|-------|----------|--------|---------|
| Chat stream buffer overflow (64KB limit) | P0 | FIXED | `chat.py` — raised to 1MB |
| `python` command not found in subprocess | P0 | FIXED | `jarvis.py`, `home.py` — `uv run python` |
| Shadow `CommandResponse` type blocks cards | P0 | FIXED | `JarvisInput.tsx` — removed duplicate |
| Hardcoded claude CLI path | P0 | FIXED | `jarvis.py` — `shutil.which()` |
| Drafts table mismatch (`pm_drafts` vs `drafts`) | P0 | FIXED | `jarvis.py` — corrected + JOIN |
| Process command returns filtered-out card | P0 | FIXED | `jarvis.py` — `health_detail` card |
| `cmd_decide` shows project_id not name | P1 | FIXED | `jarvis.py` — JOIN to projects |
| Stale briefing (`staleTime: Infinity`) | P1 | FIXED | `JarvisPage.tsx` — 5 min |
| Audio doesn't stop on interaction | P1 | FIXED | `JarvisPage.tsx` — `cancelSpeak()` |
| Missing `edge-tts` dependency | P1 | FIXED | `pyproject.toml` |
| Command injection via macOS `say` | CRIT | FIXED | `tts.py` — stdin |
| Prompt injection via CLI arg | CRIT | FIXED | `jarvis.py` — stdin |
| No input validation on `CommandRequest` | HIGH | FIXED | `jarvis.py` — `max_length=5000` |
| No input validation on `TTSRequest` | HIGH | FIXED | `tts.py` — `max_length=2000` |
| URL parameter injection in search | HIGH | FIXED | `jarvis.py` — `urlencode()` |
| Open redirect via navigate | MED | FIXED | `JarvisInput.tsx` — `startsWith('/')` |
| Duplicate AudioContext creation | MED | FIXED | `useJarvisAudio.ts` — reuse engine |
| Missing audio cleanup on unmount | MED | FIXED | `useJarvisAudio.ts` — `destroy()` |
| Blob URL memory leaks | MED | FIXED | `useJarvisAudio.ts` — cleanup |
| Nested setTimeout not in cleanup | LOW | FIXED | `JarvisPage.tsx`, `BriefingSequence.tsx` |
| SVG missing viewBox | LOW | FIXED | `HealthRing.tsx` |
| Invalid animation syntax | LOW | FIXED | `BriefingSequence.tsx` |
| Command hints incomplete | LOW | FIXED | `JarvisInput.tsx` — all 9 commands |

### Critical Gap Fixes (5 architectural issues)

| Issue | Severity | Status | Detail |
|-------|----------|--------|--------|
| Hub.db write violations (drafts) | HIGH | FIXED | `draft_decisions` overlay table. Reads hub.db, overlays platform.db. |
| Hub.db write violations (content) | MED | FIXED | `content_classifications` overlay table. Classify/dismiss persist. |
| Goals table outside schema | HIGH | FIXED | Moved to `init_db.py` SCHEMA. Removed dynamic creation. |
| Jarvis -> Chat escalation | MED | FIXED | `suggest_chat` action + "Continue in Chat" button. |
| Blocking subprocess in `home.py` | MED | FIXED | Async with `asyncio.to_thread()`. |

---

## 3. Comparison: Found vs Fixed vs Remaining

### Critical/High Issues

| Issue | Found By | Fixed? | Notes |
|-------|----------|--------|-------|
| Chat stream 64KB buffer | Bug Hunter | YES | `limit=1024*1024` in subprocess |
| `python` not on PATH | Architect | YES | `uv run python` everywhere |
| Shadow CommandResponse type | Architect + Wiring FE | YES | Deleted local interface |
| Hub.db draft writes | Data Auditor | YES | Overlay pattern in platform.db |
| Hub.db todo writes | Data Auditor | **YES** | Sprint 2: `todo_overrides` overlay table. `_get_hub_rw()` removed entirely from todos.py |
| Goals table fragile | Data Auditor | YES | In init_db.py now |
| Content stubs (no-op) | Backend Auditor | YES | Persists to platform.db |
| Prompt injection | Security | YES | Text via stdin |
| Command injection (say) | Security | YES | Text via stdin |
| Missing edge-tts | Voice Specialist | YES | Added to pyproject.toml |
| XSS in MessageBubble | Security | **YES** | Sprint 1: DOMPurify.sanitize() added to MessageBubble.tsx |

### Medium Issues

| Issue | Found By | Fixed? | Notes |
|-------|----------|--------|-------|
| Stale briefing | PM | YES | 5-min staleTime |
| Audio not cancelling | PM + Voice | YES | cancelSpeak on interact |
| Blocking subprocess (home) | Architect | YES | async |
| Duplicate AudioContext | Voice | YES | Reuse engine ctx |
| Blob URL leaks | Bug Hunter + Voice | YES | destroy() cleanup |
| Input validation missing | Security | YES | max_length on Pydantic |
| URL injection in search | Security | YES | urlencode() |
| Open redirect | Security | YES | Path validation |
| Jarvis -> Chat handoff | PM + Wiring FE | YES | suggest_chat action |
| CORS too permissive | Security | **NO** | Low risk for localhost |
| TTS cache collisions | Voice | PARTIAL | Fixed for `say`, not Piper/Edge |
| ProjectDetail tabs incomplete | Frontend Auditor | **NO** | Next sprint |
| No Jarvis session memory | PM | **NO** | Strategic — v1.1 |

### Low Issues

| Issue | Found By | Fixed? | Notes |
|-------|----------|--------|-------|
| SVG viewBox | Senior Dev | YES | Added |
| Animation syntax | Senior Dev | YES | Inline style |
| Timer cleanup | Bug Hunter | YES | All timers tracked |
| Command hints | PM | YES | All 9 listed |
| FTS5 silent fallback | Data Auditor | **NO** | Trivial, next sprint |
| No code copy button | Frontend Auditor | **NO** | Next sprint |
| Goal status UI | Frontend Auditor | **NO** | Next sprint |
| Overflow-hidden clips | Senior Dev | YES | `overflow-y-auto` |
| Responsive padding | Senior Dev | YES | `px-4 sm:px-6 md:px-8` |
| No Alembic | Data Auditor | **YES** | Sprint 2: Alembic set up with baseline migration covering all 24 tables + 13 indexes |

---

## 4. Scorecard

| Metric | Value |
|--------|-------|
| Total issues found | 35+ |
| Issues fixed (prior sprint) | 28 |
| Issues fixed (Sprint 1 + 2) | 31 more (see below) |
| Issues remaining | 22 (mostly LOW UX polish) |
| Critical/High remaining | 0 |
| Medium remaining | 3 |
| Low remaining | 19 |
| New tables created | 8 (goals, draft_decisions, content_classifications, project_overrides, todo_overrides, comments, templates, analysis_jobs) |
| New infra | Alembic migrations, EventBus, SSE rewrite, Pydantic models module (18 files) |
| Files modified | 80+ |
| Compilation | Clean (TS + Python) |

---

## 5. Next Sprint Plan

### Sprint Goal: "Ship-Ready v1.0"
**Duration:** 3 days | **Total items:** 30 | **Total effort:** ~19.5h

---

#### Day 1: Data Integrity + Security (~5h)

| # | Task | Found By | Effort | Priority | Status |
|---|------|----------|--------|----------|--------|
| 1.1 | Todo overlay table in platform.db (same pattern as drafts) | Data Auditor | 2h | HIGH | DONE ✓ (Sprint 2) |
| 1.2 | DOMPurify in MessageBubble (replace regex HTML) | Security | 1h | HIGH | DONE ✓ (Sprint 1) |
| 1.3 | Subprocess concurrency limiter (`asyncio.Semaphore(5)`) | Security | 30m | MEDIUM | TODO |
| 1.4 | `_build_briefing()` null check in `cmd_briefing` | Bug Hunter | 10m | MEDIUM | TODO |
| 1.5 | CORS tightening (explicit methods/headers in main.py) | Security | 15m | LOW | TODO |
| 1.6 | FTS5 fallback logging when `content_fts` missing | Data Auditor | 15m | LOW | TODO |
| 1.7 | `cmd_costs` stale data — cache-bust `get_home()` call | PM | 15m | LOW | TODO |
| 1.8 | Move 3 inline `get_home` imports to module-level in jarvis.py | Architect | 10m | LOW | TODO |

**Already fixed in this area (current sprint):**
- ~~Hub.db draft writes~~ → `draft_decisions` overlay ✓
- ~~Hub.db content stubs (no-op)~~ → `content_classifications` overlay ✓
- ~~Goals table outside schema~~ → moved to `init_db.py` ✓
- ~~Blocking subprocess in home.py~~ → `asyncio.to_thread()` ✓
- ~~Command injection via `say`~~ → stdin ✓
- ~~Prompt injection via CLI arg~~ → stdin ✓
- ~~No input validation (CommandRequest)~~ → `max_length=5000` ✓
- ~~No input validation (TTSRequest)~~ → `max_length=2000` ✓
- ~~URL injection in search~~ → `urlencode()` ✓
- ~~`python` not on PATH~~ → `uv run python` ✓
- ~~Hardcoded claude path~~ → `shutil.which()` ✓

---

#### Day 2: UX Polish (~7.5h)

| # | Task | Found By | Effort | Priority | Status |
|---|------|----------|--------|----------|--------|
| 2.1 | ProjectDetailPage — complete People tab | Frontend Auditor | 2h | MEDIUM | TODO |
| 2.2 | ProjectDetailPage — agent management within project | Frontend Auditor | 2h | MEDIUM | TODO |
| 2.3 | `jarvis-waveform` uses `height` (reflow) → `transform: scaleY()` | Senior Dev | 15m | MEDIUM | TODO |
| 2.4 | Goal status transitions (visual workflow) | Frontend Auditor | 2h | LOW | DONE ✓ (Issue lifecycle state machine — TransitionButtons, StatusBar, BoardView, color-coded states) |
| 2.5 | Code block copy button in MessageBubble | Frontend Auditor | 30m | LOW | TODO |
| 2.6 | NavigateHintCard auto-nav — add "Cancel" button | PM | 20m | LOW | TODO |
| 2.7 | Grid gap not responsive → `gap-3 sm:gap-4 md:gap-6` | Senior Dev | 10m | LOW | TODO |
| 2.8 | `HomeProject.active` type `number` → `boolean` in types/home.ts | Bug Hunter | 5m | LOW | TODO |
| 2.9 | Remove unused `jira_preview` from CardType union | Architect | 5m | LOW | TODO |
| 2.10 | Array index as React key in MetricScene → content-based keys | Bug Hunter | 10m | LOW | TODO |
| 2.11 | Dismiss command canvas flicker — delay clear to match animation | PM | 15m | LOW | TODO |

**Already fixed in this area (current sprint):**
- ~~SVG missing viewBox~~ → added to HealthRing ✓
- ~~Invalid animation syntax~~ → inline style in BriefingSequence ✓
- ~~Overflow-hidden clips content~~ → `overflow-y-auto` ✓
- ~~Responsive padding~~ → `px-4 sm:px-6 md:px-8` ✓
- ~~Command hints incomplete~~ → all 9 commands listed ✓
- ~~Shadow CommandResponse type~~ → deleted duplicate ✓
- ~~Open redirect~~ → validates `startsWith('/')` ✓
- ~~Jarvis → Chat handoff~~ → "Continue in Chat" button ✓
- ~~AlertScene empty string fallback~~ → fixed sources array ✓

---

#### Day 3: Jarvis + Voice + Validation (~7h)

| # | Task | Found By | Effort | Priority | Status |
|---|------|----------|--------|----------|--------|
| 3.1 | Jarvis session memory (last 5 commands per activation) | PM | 3h | MEDIUM | TODO |
| 3.2 | Jarvis inline actions (create todo, approve draft from command) | PM | 3h | MEDIUM | TODO |
| 3.3 | Smoke test validation (run suite, fix failures) | Roadmap Auditor | 2h | HIGH | TODO |
| 3.4 | Force-stop oscillator nodes on destroy (bypass 2.2s fade) | Voice | 15m | LOW | TODO |
| 3.5 | TTS prefetch failure logging | Voice | 10m | LOW | TODO |
| 3.6 | Friendly mic permission error messages in useVoiceInput.ts | Voice | 15m | LOW | TODO |
| 3.7 | `drop-shadow` on HealthRing SVG → `box-shadow` or CSS var | Senior Dev | 20m | LOW | TODO |
| 3.8 | TTS cache unique filenames for Piper/Edge (race condition) | Security + Voice | 15m | LOW | TODO |

**Already fixed in this area (current sprint):**
- ~~Stale briefing (`staleTime: Infinity`)~~ → 5 min ✓
- ~~Audio doesn't stop on interaction~~ → `cancelSpeak()` ✓
- ~~Missing `edge-tts` dependency~~ → added to pyproject.toml ✓
- ~~Duplicate AudioContext creation~~ → reuse engine ctx ✓
- ~~Missing audio cleanup on unmount~~ → `destroy()` method ✓
- ~~Blob URL memory leaks~~ → cleanup in destroy ✓
- ~~Nested setTimeout not in cleanup~~ → all timers tracked ✓
- ~~Chat stream buffer overflow~~ → 1MB limit ✓
- ~~`cmd_decide` shows project_id not name~~ → JOIN ✓
- ~~Drafts table mismatch~~ → corrected query ✓
- ~~Process command returns filtered card~~ → `health_detail` ✓
- ~~TTS `say` injection~~ → stdin + unique filename ✓

---

### Summary by Day

| Day | Focus | Tasks | Effort | HIGH | MED | LOW |
|-----|-------|-------|--------|------|-----|-----|
| 1 | Data + Security | 8 | ~5h | 2 | 2 | 4 |
| 2 | UX + Rendering | 11 | ~7.5h | 0 | 3 | 8 |
| 3 | Jarvis + Voice + QA | 8 | ~7h | 1 | 2 | 5 |
| **Total** | | **27** | **~19.5h** | **3** | **7** | **17** |

### Already Fixed (Current Sprint): 28 issues across 15+ files

---

### Deferred to v1.1

| Task | Reason |
|------|--------|
| Streaming Jarvis chat | Requires Jarvis rearchitecture |
| Jarvis as primary interface | Strategic design decision needed |
| ~~Alembic migration framework~~ | ~~Schema stable for v1.0~~ → **DONE in Sprint 2** |
| Chat context attachment (Phase 7.9) | Nice-to-have |
| E2E Playwright tests | Infrastructure setup |
| Agent-to-agent communication | Beyond v1.0 scope |
| Rate limiting middleware | Low risk for single-user localhost |
| No auth on jarvis/command endpoint | Localhost-only, optional PIN exists |
| No Jarvis session memory across page loads | Needs backend session store |

---

## 6. Overlay Pattern (Architecture Note)

Hub.db remains strictly read-only. Platform decisions stored in overlay tables:

```
hub.db (KH-owned, read-only)     platform.db (CoCo-owned, read-write)
+-----------+                     +---------------------------+
| drafts    |  <-- read --------> | draft_decisions           |
| content   |  <-- read --------> | content_classifications   |
| todos     |  <-- read --------> | todo_overrides ✓          |
| projects  |  <-- read --------> | project_overrides         |
+-----------+                     +---------------------------+
```

**Pattern:** Read from hub.db, overlay platform.db decisions, return merged result. All writes go to platform.db only.

---

## 7. Sprint 1 + 2 Additions (beyond original plan)

These fixes were identified by the 8-agent deep analysis and executed across Sprint 1 (STABILIZE) and Sprint 2 (FOUNDATION):

### Sprint 1: STABILIZE (31 fixes)

**P0 Crashes Fixed:**
- `section_name` vs `section` column mismatch in collaboration_context.py → fixed
- AgentDetail uses POST instead of PATCH → fixed to apiPatch
- Analysis job always "completed" even on failure → dead conditional fixed
- write_json caches mutable data without deepcopy → deepcopy added
- json_store._cache not thread-safe → threading.Lock added

**P1 Wiring Fixed:**
- PATCH `/api/projects/{id}` missing → added with project_overrides table
- PATCH `/api/brain/people/{slug}` missing → added with atomic brain.json writes
- ActivityPage `timestamp` vs `created_at` field mismatch → fixed
- Dashboard queue total double-counting → fixed
- apiDelete throws on 204 No Content → handled
- `?status=unsorted` filter broken → implemented correctly
- `?project_ids=X,Y` multi-value not supported → added to goals + drafts
- content/classify and content/dismiss no-ops → now persist to platform.db

**P2 Security Fixed:**
- XSS in MessageBubble → DOMPurify.sanitize() added
- Agent subprocess gets full env → whitelist of needed vars only
- Security headers missing → middleware for CSP, X-Frame-Options, X-Content-Type-Options
- Health endpoint exposes file paths → returns existence only
- Agent timeout never enforced → watchdog timer in ProcessManager

**P3 SSE Overhaul (complete rewrite):**
- SSE named events never received by onmessage → addEventListener per event type
- SSE reconnection leaks + no recursive retry → exponential backoff + proper cleanup
- Backend never writes to events.jsonl → EventBus created, all mutations emit events
- AgentDetail 2s polling → wired to SSE `/api/events/agents/{id}`
- Chat stream no reconnection → retry logic + subprocess kill on disconnect
- No offline indicator → "Connection lost" banner in AppShell

**P4 Error Handling Fixed:**
- 80+ bare `except Exception: return []` → logging added to key routers
- delete_node leaves orphaned records → cascading deletes for 7+ tables
- Chat `message` variable shadowing → renamed to `assistant_message`
- _read_output opens DB per line → batched with single connection
- update_goal can't set progress_pct to 0 → exclude_unset=True

### Sprint 2: FOUNDATION (4 workstreams)

**Todo Overlay (hub.db write elimination):**
- `todo_overrides` table created in platform.db
- All 7 `_get_hub_rw()` call sites rewritten to overlay pattern
- `_get_hub_rw()` function removed entirely — hub.db is now 100% read-only

**Pydantic Models Extraction:**
- 18 model files created in `backend/app/models/`
- All 9 `body: dict` endpoints replaced with typed Pydantic models
- 14 router files updated to import from models module

**Code Quality:**
- `datetime.utcnow()` replaced in 3 files (deprecated Python 3.12+)
- `SELECT *` replaced with explicit columns in 6 routers (39 queries)
- OpenAPI tags added to all 25 routers with descriptions
- Dev dependencies added (pytest, httpx, alembic)

**DB Foundation:**
- PRAGMA foreign_keys = ON enabled in connections.py
- 13 missing indexes added to init_db.py (runtime migration for existing DBs)
- Alembic framework set up with baseline migration (24 tables)

### Features Built (Tier 2 gap closures)

| Feature | Status |
|---------|--------|
| Unread 3-state machine (visible→seen→dismissed) | DONE |
| Comment threads with @mentions | DONE |
| Export/import project templates | DONE |
| Issue lifecycle state machine (backlog→todo→in_progress→in_review→done→archived) | DONE |
| Agent org chart with reporting lines | DONE |
| Todo deduplication (fuzzy matching + merge UI) | DONE |
| Folder analysis pipeline (scan + multi-agent analysis) | DONE |

---

## 8. Remaining Items (not yet done)

### From this plan (Day 1-3 tasks still TODO):
| # | Task | Priority |
|---|------|----------|
| 1.3 | Subprocess concurrency limiter (asyncio.Semaphore) | MEDIUM |
| 1.4 | _build_briefing() null check | MEDIUM |
| 1.5 | CORS tightening | LOW |
| 1.6 | FTS5 fallback logging | LOW |
| 1.7 | cmd_costs stale data | LOW |
| 1.8 | Move inline imports in jarvis.py | LOW |
| 2.1 | ProjectDetailPage People tab | MEDIUM |
| 2.2 | ProjectDetailPage agent management | MEDIUM |
| 2.3 | jarvis-waveform transform | MEDIUM |
| 2.5 | Code block copy button | LOW |
| 2.6 | NavigateHintCard cancel button | LOW |
| 2.7 | Grid gap responsive | LOW |
| 2.8 | HomeProject.active type fix | LOW |
| 2.9 | Remove unused jira_preview | LOW |
| 2.10 | Array index as React key | LOW |
| 2.11 | Dismiss canvas flicker | LOW |
| 3.1 | Jarvis session memory | MEDIUM |
| 3.2 | Jarvis inline actions | MEDIUM |
| 3.3 | Smoke test validation | HIGH |
| 3.4 | Force-stop oscillator nodes | LOW |
| 3.5 | TTS prefetch failure logging | LOW |
| 3.6 | Friendly mic permission errors | LOW |
| 3.7 | drop-shadow on HealthRing | LOW |
| 3.8 | TTS cache unique filenames | LOW |

**Summary: 0 Critical, 0 High (except smoke tests), 6 Medium, 18 Low remaining.**
