# CoCo Platform — Project Memory

## What This Is

CoCo Platform is a Paperclip-inspired web application that provides a visual control plane for the existing CoCo + Knowledge Hub CLI system. React 19 + Vite + Radix UI + Tailwind CSS 4 frontend, Python FastAPI backend, dual SQLite databases.

## Key Architecture Decisions

- **Frontend:** React 19 + Vite 6 + Radix UI + Tailwind CSS 4 + Zustand + TanStack Query
- **Backend:** Python 3.13 + FastAPI + uvicorn
- **Databases:** hub.db (read-only, KH owned) + platform.db (read-write, new)
- **Real-time:** SSE via sse-starlette (not WebSocket)
- **Stations:** Claude Code CLI processes spawned via `claude -p --output-format stream-json`
- **Chat:** Spawns `claude -p` subprocess (preserves MCP tools + CoCo skills)
- **Deployment:** launchd on macOS, single `start.sh`, port 3001
- **Auth:** Optional PIN only. No JWT. No multi-user.
- **Package manager:** uv (backend), pnpm (frontend)
- **API prefix:** `/api/` (no versioning)

## File Locations

- Planning docs: `.planning/` (ARCHITECTURE.md, FEATURES.md, ROADMAP.md, UI_SPEC.md, DATA_MODEL_AND_API.md)
- Frontend: `frontend/` (React + Vite)
- Backend: `backend/` (FastAPI)
- Scripts: `scripts/` (dev.sh, start.sh, smoke-test.sh, setup.sh)

## Existing Data Stores (DO NOT MODIFY)

- `~/.hub/hub.db` — Knowledge Hub. Open read-only (`?mode=ro`). Never write.
- `~/.coco/brain.json` — People graph, rules. Atomic writes only (tmp + rename).
- `~/.coco/queue.json` — Decision queue. Atomic writes only.
- `~/.coco/config.json` — CoCo config. Atomic writes only.
- `~/.coco/sessions/` — Session history. Read-only.
- `~/.coco/events.jsonl` — Event stream. Read-only (tail).

## New Data Store

- `~/.coco/platform.db` — Created by Alembic on first run. Stations, cost_ledger, budgets, governance_log, preferences.

## Build Phases

12 phases. See `.planning/ROADMAP.md` for full breakdown.
Phase 1-2: Foundation + Backend Core
Phase 3-4: Dashboard + Stations
Phase 5-6: Knowledge Hub + Decisions
Phase 7-8: Chat + Tasks
Phase 9-11: Costs + People + Todos
Phase 12: Polish

## Conventions

- Backend tests: `pytest` + `pytest-asyncio` + `httpx`
- Frontend tests: `vitest` + `@testing-library/react` + MSW
- Commit format: `{phase}.{task}: {description}`
- Branch per phase: `phase/{N}-{name}`
- All SQLite connections use WAL mode
- All JSON file writes use atomic tmp+rename pattern
- hub.db queries use explicit column names (never `SELECT *`)
