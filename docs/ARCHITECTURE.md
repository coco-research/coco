# CoCo Platform — Architecture

## Overview

CoCo Platform follows a monolith-first architecture: a single FastAPI backend serving a React SPA, backed by dual SQLite databases.

## Data Model

### Dual Database Strategy

| Database | Path | Access | Owner |
|----------|------|--------|-------|
| `hub.db` | `~/.hub/hub.db` | Read-only | Knowledge Hub |
| `platform.db` | `~/.coco/platform.db` | Read-write | CoCo Platform |

hub.db is the Knowledge Hub's database — emails, voice memos, Jira tickets, Confluence pages. CoCo opens it read-only and never writes to it.

platform.db is CoCo's own database — agents, cost ledger, todo overlays, governance log, triggers.

### Overlay Pattern

When CoCo needs to "modify" KH data (e.g., mark a todo as done), it writes to an overlay table in platform.db rather than touching hub.db. The API layer merges both sources.

## Real-Time

Server-Sent Events (SSE) via `sse-starlette`. Each event type is a named SSE event. The EventBus persists events to a database table for replay on reconnection.

## Agent Spawning

Agents are Claude Code CLI processes spawned via `subprocess.Popen` (legacy) or the Anthropic Python SDK (when `USE_AGENT_SDK=true`). The ProcessManager tracks lifecycle, enforces concurrency limits, and records costs.

## Feature Gating

Runtime `COCO_EDITION` env var gates Studio features. No build-time separation — single codebase, single binary.
