# Merge Losses — reconciling main into merge/wave-3

Date: 2026-05-27

Reconciled `main` (22 commits, phases 1-11) into `merge/wave-3` (98 commits).
Common ancestor: `f5fad47`. This file documents features that were dropped
or superseded during conflict resolution.

## Features dropped

### 1. `frontend/src/pages/InboxPage.tsx` — wave-3 dismiss-flicker fix obsolete

- **Wave-3 commit**: `c168fc7 fix(inbox): eliminate dismiss flicker via optimistic cache`
- **Reason dropped**: Main's phase-6 v3 redesign (commit `6d11e65`) moved
  the implementation from `frontend/src/pages/InboxPage.tsx` to
  `frontend/src/pages/inbox/InboxPage.tsx` (3-zone deck). The new design
  already uses a Zustand `optimistic` store for immediate UI updates and
  SSE-confirmed reconciliation — a fundamentally different pattern that
  the wave-3 TanStack-cache fix does not port onto.
- **Risk**: low — the new design solves the same flicker problem by
  different means (Zustand optimistic state + SSE `queue.side_effect_confirmed`).
- **Followup if needed**: if flicker re-emerges in the new design,
  port the 8-second optimistic-clear safety net pattern (already present
  in new InboxPage at lines 284-295).

### 2. `frontend/src/pages/InboxPage.tsx` — wave-3 ErrorState wrapping

- **Wave-3 commit**: `d8f13ef feat(inbox): empty/loading/error states`
- **Reason dropped**: Same as above — the legacy file became a thin
  re-export of the new 3-zone implementation. The shared
  `EmptyState/LoadingSkeleton/ErrorState` trio (`frontend/src/components/shared/`)
  is still present and used by other pages, but the InboxPage redesign
  pre-dates the trio.
- **Risk**: low/medium — error handling exists in the new InboxPage
  via TanStack Query's error states, just not wrapped in the shared
  component. Visual consistency only.
- **Followup**: wrap the new InboxPage's error branches with the shared
  `ErrorState` component in a small follow-up.

### 3. `backend/app/db/init_db.py` — `SCHEMA` constant removed

- **Wave-3 commit**: `b4cb9e9 phase-1: rewire init_db.py to SA Core metadata.create_all`
  (originally from main) was largely accepted, then wave-3's tests
  referenced `from app.db.init_db import SCHEMA` (in `backend/tests/conftest.py`).
- **Reason dropped**: After Sprint 6A both branches agreed `tables.py`
  metadata is the single source of truth. The ~640-line raw `SCHEMA` string
  is removed entirely. `conftest.py` was rewritten to call
  `metadata.create_all(engine, checkfirst=True)` instead.
- **Risk**: low — schema content is preserved; test fixture path changed.

## Alembic migration chain reconciliation

Both branches added migrations off `001`, creating duplicate revision IDs
and parallel heads. The chain has been linearised:

```
001 -> 002 (triggers) -> 003 (todo_deps) -> 004 (agent_tasks) -> 005 (human_ids)
    -> 006_dead_letter_queue -> 140054f726ca (brain_b0)
    -> 007_brain_merge_log -> 008_audit_log
```

Main's migrations were renumbered (002->006, 003->007, 004->008) to chain
**after** wave-3's 005. The brain_b0 migration keeps its hash-style
revision ID but its `down_revision` is now `006_dead_letter_queue`.
Filenames on disk match the new IDs.

No DDL was lost — only revision metadata was rewritten.
