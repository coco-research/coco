# Contributing to CoCo Platform

Thank you for considering contributing to CoCo! This document explains how to get started.

## Development Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/rijulkalra2000/Project-Coco.git
   cd Project-Coco
   ./setup.sh
   ```

2. **Start development servers**
   ```bash
   ./scripts/dev.sh
   ```

3. **Run tests**
   ```bash
   cd backend && uv run pytest
   cd frontend && pnpm test
   ```

## Project Structure

```
coco-platform/
├── backend/               # Python FastAPI backend
│   ├── app/
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── models/        # Pydantic models
│   │   ├── db/            # Database (SQLAlchemy Core)
│   │   └── middleware/     # Auth, rate limiting
│   └── tests/
├── frontend/              # React 19 + Vite frontend
│   ├── src/
│   │   ├── pages/         # Route pages
│   │   ├── components/    # UI components
│   │   ├── hooks/         # Custom hooks
│   │   ├── lib/           # Utilities
│   │   └── types/         # TypeScript types
│   └── tests/
├── scripts/               # Dev and deployment scripts
├── docs/                  # Documentation
└── .planning/             # Sprint plans and architecture docs
```

## Code Style

### Backend (Python)
- Python 3.13+
- Type hints everywhere
- `structlog` for logging (not `print()` or `logging`)
- SQLAlchemy Core (not ORM) for database queries
- Pydantic models for request/response validation
- `uv` for package management

### Frontend (TypeScript)
- React 19 with functional components
- TanStack Query for server state
- Zustand for client state (sparingly)
- Tailwind CSS 4 for styling (no CSS modules)
- Radix UI for accessible primitives
- `pnpm` for package management

## Commit Format

```
{sprint}.{task}: {description}
```

Examples:
- `8.1: Add feature gate infrastructure`
- `8.2: Frontend edition gating`
- `fix: Correct SSE reconnection backoff`

## Pull Request Process

1. Create a branch from `main`
2. Make your changes
3. Run tests: `cd backend && uv run pytest && cd ../frontend && pnpm test`
4. Push and open a PR
5. Fill in the PR template
6. Wait for review

## Architecture Decisions

Key decisions are documented in `.planning/`. Before making significant architectural changes, please open an issue to discuss.

## Core vs Studio

- **Core** features are MIT-licensed and free forever
- **Studio** features are BSL 1.1 (converts to MIT in 2029)
- New features should target Core unless they involve voice, AI generation, or premium analytics
- If unsure, open an issue and ask

## Reporting Issues

Use [GitHub Issues](https://github.com/rijulkalra2000/Project-Coco/issues) with the provided templates:
- **Bug Report** — for bugs and errors
- **Feature Request** — for new feature ideas
- **Question** — for questions about the codebase
