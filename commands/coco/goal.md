---
allowed-tools: Read, Write, Edit, Glob
argument-hint: "<objective> | status | done"
description: Set, check, or complete the persistent project goal stored in .goal.md. Trigger as /coco-goal or /coco:goal.
---

# Coco Goal

Manage the persistent project goal in `.goal.md` at the repository root. Full
conventions: the \`goal\` skill. Arguments: **$ARGUMENTS**

## Routing

- Empty arguments or `status` — read `.goal.md` and report the objective,
  status, and latest progress entries. No file means no goal is set.
- Any other text — treat it as a new objective. If an `active` goal already
  exists, show it and ask whether to complete, pause, or replace it; never
  silently replace. Otherwise write `.goal.md` with `status: active` and
  today's date.
- `done` — set `status: done` only if the objective has actually been
  achieved; verify before writing.

## Rules

- One active goal per repository. The file is the source of truth.
- Append progress notes after each work session; never rewrite past entries.
- Only create a goal when explicitly asked; ordinary tasks are not goals.
