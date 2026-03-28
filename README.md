<div align="center">

# CoCo Platform

**Your AI agents, managed like a product team.**

CoCo is a local-first control plane for AI coding agents. It turns Claude Code sessions into a managed product team — with knowledge from your emails, voice memos, Jira, and Confluence feeding directly into agent context.

[Quick Start](#quick-start) · [Features](#features) · [Architecture](#architecture) · [Contributing](CONTRIBUTING.md) · [License](#license)

</div>

---

## Why CoCo?

AI coding agents are powerful but chaotic. You spawn them, lose track of what they're doing, and have no idea what they cost. CoCo fixes that:

- **One dashboard** for all your agents, tasks, and costs
- **Knowledge Hub** — emails, voice memos, Jira, Confluence all searchable in one place
- **Smart inbox** — auto-classified items, draft approvals, decision queue
- **Real cost tracking** — per-agent, per-task token usage and spend
- **Trigger engine** — cron jobs, file watchers, webhooks that spawn agents

## Quick Start

```bash
git clone https://github.com/rijulkalra2000/Project-Coco.git
cd Project-Coco
./setup.sh
./scripts/dev.sh
```

Open [http://localhost:5173](http://localhost:5173). That's it.

## Features

### Core Edition (MIT — free forever)

| Feature | Description |
|---------|-------------|
| **Home Dashboard** | Project health, recent activity, quick actions |
| **Agent Management** | Spawn, monitor, and coordinate Claude Code agents |
| **Knowledge Hub** | Unified search across email, voice, Jira, Confluence |
| **Smart Inbox** | Auto-classified items, draft approvals, batch actions |
| **Todos & Goals** | Full lifecycle: backlog → in progress → done |
| **Chat** | Claude conversations with injected project context |
| **Cost Tracking** | Per-agent token usage, budgets, cost ledger |
| **Triggers** | Cron, file watch, webhook automation |
| **Portfolio Tree** | Hierarchical team → project → agent organization |
| **Templates** | Export/import project configurations |
| **Comments** | Threaded discussions on any entity |
| **Search** | Unified search across todos, agents, tasks, content |

### Studio Edition (BSL 1.1)

| Feature | Description |
|---------|-------------|
| **Jarvis Voice** | Cinematic voice assistant overlay with briefings |
| **TTS/STT** | Text-to-speech (Kokoro) and speech-to-text (Deepgram) |
| **Agent Replay** | Shareable HTML time-lapse of agent sessions |
| **Morning Podcast** | Auto-generated audio briefing of overnight activity |
| **Self-Improvement** | Agents that analyze and improve the platform itself |
| **Folder Analysis** | Deep document analysis pipeline |

> Studio features convert to MIT license on March 28, 2029.

## Architecture

```
┌─────────────────────────────────────┐
│           React 19 + Vite           │  ← Frontend (port 5173)
│  Radix UI · Tailwind CSS 4 · Zustand│
└──────────────┬──────────────────────┘
               │ REST + SSE
┌──────────────┴──────────────────────┐
│         FastAPI + uvicorn           │  ← Backend (port 8000)
│  SQLAlchemy Core · structlog        │
└──────┬───────────────┬──────────────┘
       │               │
┌──────┴──────┐ ┌──────┴──────┐
│  hub.db     │ │ platform.db │
│  (read-only)│ │ (read-write)│
│  KH owned   │ │ CoCo owned  │
└─────────────┘ └─────────────┘
```

- **hub.db** — Knowledge Hub's database. Opened read-only. Never written to by CoCo.
- **platform.db** — CoCo's own database. Agents, costs, todos overlay, governance log.
- **SSE** — Server-Sent Events for real-time updates (not WebSocket).
- **SQLite WAL mode** — concurrent reads, single writer.

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
COCO_EDITION=core          # or "studio"
PLATFORM_PORT=8000
MAX_CONCURRENT_AGENTS=3
USE_AGENT_SDK=false        # true = use Anthropic API directly
```

See [docs/SETUP.md](docs/SETUP.md) for full configuration reference.

## Development

```bash
# Backend
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && pnpm dev

# Tests
cd backend && uv run pytest
cd frontend && pnpm test
```

## License

CoCo Platform uses a dual license model:

- **Core** — [MIT License](LICENSE)
- **Studio** — [Business Source License 1.1](LICENSE-STUDIO), converting to MIT on March 28, 2029

You can use Core features freely in any project. Studio features require the BSL license until the change date.
