# Team — Cross-Functional Multi-Agent Pipeline

Opinionated orchestration system for multi-agent workflows: research, plan, build, review, verify, ship.

## Install

```bash
bash adapters/<your-ide>/install.sh --systems team
```

Wires the team commands (`/team:*`) and supporting roles into your IDE.

## What it does

Pipeline shape (4 layers):
- **L1 — Analysts** — gather context, surface requirements
- **L2 — Specialists** — domain-specific work (engineers, PMs, designers)
- **L3 — Reviewers** — audit L2's output for accuracy and standards
- **L4 — Principal** — synthesize, render verdict, recommend next action

## Commands

Already in `commands/team/`:
- `/team plan`, `/team research`, `/team think`
- `/team develop`, `/team fix`, `/team test`
- `/team review`, `/team verify`, `/team document`
- `/team communicate`, `/team present`, `/team ship`
- `/team toolkit`, `/team feedback`, `/team roles`

Each command spawns the appropriate role mix for that pipeline.

## Specs

Design decisions and architecture live in `specs/`.

## Why a separate system

Team conventions (4-layer role bias, parallel agent dispatch) don't apply outside team workflows. Keeping it bundled under `systems/` lets users opt in cleanly.
