# CoCo Platform — Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- pnpm (`npm install -g pnpm`)
- uv (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Quick Setup

```bash
git clone https://github.com/rijulkalra2000/Project-Coco.git
cd Project-Coco
./setup.sh
./scripts/dev.sh
```

## Manual Setup

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

## Configuration

All configuration is via environment variables. Copy `.env.example` to `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `COCO_EDITION` | `core` | `core` or `studio` |
| `COCO_DIR` | `~/.coco` | Data directory |
| `HUB_DIR` | `~/.hub` | Knowledge Hub directory |
| `DATABASE_URL` | `sqlite:///~/.coco/platform.db` | Database connection |
| `PLATFORM_PORT` | `8000` | Backend port |
| `MAX_CONCURRENT_AGENTS` | `3` | Max parallel agents |
| `AGENT_TIMEOUT_MINUTES` | `30` | Agent timeout |
| `USE_AGENT_SDK` | `false` | Use Anthropic SDK instead of CLI |
| `DEEPGRAM_API_KEY` | _(none)_ | Deepgram STT key (Studio) |
| `ANTHROPIC_API_KEY` | _(none)_ | Anthropic API key |
| `COCO_AUTH_TOKEN` | _(none)_ | Optional bearer token auth |
| `COCO_CORS_ORIGINS` | `localhost:5173` | Allowed CORS origins |

## Database

CoCo uses SQLite by default (zero config). For production or multi-user setups, PostgreSQL is supported:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/coco
```
