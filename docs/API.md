# CoCo Platform — API Reference

Base URL: `http://localhost:8000`

## System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/edition` | Current edition and features |

## Home & Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/home` | Home dashboard data |
| GET | `/api/dashboard` | Aggregated dashboard |

## Projects & Teams

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List projects |
| GET | `/api/projects/{id}` | Project detail |
| GET | `/api/teams` | List teams |
| GET | `/api/tree` | Portfolio tree |

## Agents

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/agents` | List agents |
| POST | `/api/agents` | Spawn agent |
| GET | `/api/agents/{id}` | Agent detail |
| POST | `/api/agents/{id}/stop` | Stop agent |
| POST | `/api/agents/{id}/delegate` | Delegate to subagent |

## Tasks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create task |
| PATCH | `/api/tasks/{id}` | Update task |
| POST | `/api/tasks/{id}/transition` | State transition |

## Todos

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/todos` | List todos |
| POST | `/api/todos` | Create todo |
| PATCH | `/api/todos/{id}` | Update todo |
| POST | `/api/todos/{id}/transition` | State transition |
| POST | `/api/todos/dedup` | Deduplicate todos |

## Goals

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/goals` | List goals |
| POST | `/api/goals` | Create goal |
| PATCH | `/api/goals/{id}` | Update goal |

## Chat

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Send message (SSE stream) |
| GET | `/api/chat/sessions` | List sessions |
| GET | `/api/chat/sessions/{id}` | Session messages |

## Knowledge & Content

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/content` | List content |
| GET | `/api/content/{id}` | Content detail |
| GET | `/api/content/suggestions` | Auto-classifier suggestions |
| POST | `/api/content/{id}/accept-suggestion` | Accept suggestion |
| GET | `/api/search` | Unified search |

## Inbox & Drafts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/inbox/read-states` | Get read states |
| PATCH | `/api/inbox/read-states` | Update read states |
| GET | `/api/drafts` | List drafts |
| POST | `/api/drafts/{id}/approve` | Approve draft |
| POST | `/api/drafts/{id}/reject` | Reject draft |

## Costs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/costs` | Cost summary |
| GET | `/api/costs/ledger` | Detailed ledger |
| GET | `/api/costs/budget` | Budget status |

## Triggers

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/triggers` | List triggers |
| POST | `/api/triggers` | Create trigger |
| PATCH | `/api/triggers/{id}` | Update trigger |
| DELETE | `/api/triggers/{id}` | Delete trigger |
| POST | `/api/webhooks/{id}` | Incoming webhook |

## Events (SSE)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/events` | SSE event stream |

## Settings

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/settings` | Get settings |
| PATCH | `/api/settings` | Update settings |

---

For the full OpenAPI schema, visit `http://localhost:8000/docs` when the backend is running.
