# Sprint 8 Plan: "Open-Source Prep"

**Date:** 2026-03-28
**Duration:** 8 days
**Prerequisites:** Sprint 7

---

## Workstream A: Core/Studio Split (Days 1-4)

### Architecture Decision

Runtime feature flags via `COCO_EDITION` env var — **not** build-time separation. Single codebase, single binary, single install. Studio features are gated at both API and UI layers.

| Edition | License | Features |
|---------|---------|----------|
| **Core** | MIT | Home, Projects, Agents, Knowledge Hub, Todos/Goals/Tasks, Basic Costs, Chat, Inbox, Settings, Search, Comments, Templates, Triggers |
| **Studio** | BSL 1.1 | Jarvis voice, TTS/STT, Agent Replay, Morning Podcast, Self-Improvement, Folder Analysis, CocoOrb voice |

### Day 1: Feature Gate Infrastructure
- `feature_gate.py` — `is_studio()`, `require_studio()` decorator, `GET /api/edition` endpoint
- `useEdition.ts` hook — fetches edition on mount, caches in Zustand
- Conditional router mounting — Studio routers only registered when `COCO_EDITION=studio`

### Day 2: Frontend Gating
- Conditional route registration (Studio routes return 404 in Core)
- Hidden nav items — sidebar hides Studio pages in Core edition
- "Requires Studio" upgrade prompts — tasteful inline cards, not modals

### Day 3: License Files + SPDX Headers
- `LICENSE` (MIT) for Core
- `LICENSE-STUDIO` (BSL 1.1, converts to MIT after 3 years) for Studio
- SPDX headers added to ~15 Studio-specific files

### Day 4: Install Script + Scrub
- `setup.sh` — single install script (detect OS, install deps, create DBs, set edition)
- Private data scrub: `CLAUDE.local.md` added to `.gitignore`, McKinsey references removed
- Clean-clone test: fresh `git clone` → `./setup.sh` → working app in <2 minutes

### Files

| New | Modified |
|-----|----------|
| `backend/app/services/feature_gate.py` | `backend/app/main.py` |
| `frontend/src/hooks/useEdition.ts` | `frontend/src/components/layout/Sidebar.tsx` |
| `LICENSE` | `frontend/src/App.tsx` |
| `LICENSE-STUDIO` | ~15 Studio files (SPDX headers) |
| `setup.sh` | `.gitignore` |
| `CLAUDE.local.md.template` | |
| `.env.example` | |

---

## Workstream B: Documentation (Days 5-6)

### Day 5: README.md
- Hero image/banner
- 30-second GIF (Home → Agents → Chat → Costs loop)
- What is CoCo / Why it exists
- Core vs Studio feature table
- Quick start (3 commands)
- Feature highlights with screenshots
- Architecture overview (one diagram)
- License section (dual license explanation)

### Day 6: Contributing + API Docs
- `CONTRIBUTING.md` — setup, code style, PR process, testing, commit format
- `docs/API.md` — full endpoint reference (auto-generated from OpenAPI where possible)
- GitHub issue templates: `bug_report.yml`, `feature_request.yml`, `question.yml`
- PR template with checklist

### Files

| New |
|-----|
| `README.md` |
| `CONTRIBUTING.md` |
| `docs/ARCHITECTURE.md` |
| `docs/SETUP.md` |
| `docs/STUDIO.md` |
| `docs/API.md` |
| `.github/ISSUE_TEMPLATE/bug_report.yml` |
| `.github/ISSUE_TEMPLATE/feature_request.yml` |
| `.github/ISSUE_TEMPLATE/question.yml` |
| `.github/ISSUE_TEMPLATE/config.yml` |
| `.github/PULL_REQUEST_TEMPLATE.md` |

---

## Workstream C: Security Hardening (Days 7-8)

### Day 7: Authentication + API Key Safety
- Bearer token auth middleware (optional — only active when `COCO_AUTH_TOKEN` env var is set)
- Fix STT raw API key exposure — scoped temporary keys with short TTL
- CORS configuration via `COCO_CORS_ORIGINS` env var (default: localhost only)

### Day 8: Rate Limiting + Audit
- Rate limiting via `slowapi` (sensible defaults, configurable)
- Dependency audit: `pip-audit` (backend), `npm audit` (frontend)
- Additional security headers: CSP, Referrer-Policy, X-Content-Type-Options
- Pin dependency upper bounds in `pyproject.toml` and `package.json`

### Files

| New | Modified |
|-----|----------|
| `backend/app/middleware/auth.py` | `backend/app/main.py` |
| `backend/app/middleware/rate_limit.py` | `backend/pyproject.toml` |
| `.env.example` (updated) | `frontend/package.json` |

---

## Summary

| Metric | Count |
|--------|-------|
| New files | 17 |
| Modified files | 12 |
| New DB tables | 0 |

## Risk Register

| Risk | Mitigation |
|------|------------|
| Feature gate misses a Studio dependency in Core mode | Full UI walkthrough test in Core edition before release |
| BSL license scares potential contributors | README clearly explains BSL → MIT conversion timeline |
| Missed secret in commit history | Run `trufflehog` scan on full history before public push |

---

## Sprint 5.5 Compatibility Note

> Sprint 5.5 introduces SQLAlchemy Core + hub mirror tables. All new code in Sprint 8+ MUST use SA Core, not raw sqlite3.

Sprint 8 splits Core vs Studio editions. The `DATABASE_URL` env var from Sprint 5.5 fits naturally:
- **Core edition:** `DATABASE_URL=sqlite:///~/.coco/platform.db` (default, zero-config)
- **Studio/Cloud edition:** `DATABASE_URL=postgresql://...` (docker-compose provides this)

The `docker-compose.yml` from Sprint 5.5 should be referenced in Sprint 8's setup docs.
