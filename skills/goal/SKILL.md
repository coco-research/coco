---
name: goal
description: Persistent project goal that survives across sessions and tools. Use when someone asks to "set a goal", "what is my goal", "goal status", "keep working on X until done", "resume the goal", or wants work to continue across sessions until an objective is achieved. File-backed (.goal.md at project root); shared by every Coco-installed tool working in that repository.
domain: meta
---

# Goal — persistent project objective

A goal is a single objective the agent keeps pursuing across turns and
sessions until it is marked done. Inspired by Prime Agent's thread goal:
state lives outside any one conversation, so any tool with this skill
installed (Claude Code, Cursor, Codex, ...) picks up where another left off.

## State file

One file per project: `.goal.md` in the repository root. Human-readable and
human-editable on purpose — pause, resume, edit, and clear are controlled by
the user editing the file directly.

```markdown
---
objective: Ship release notes for v2.3
status: active        # active | paused | done
created: 2026-08-22
---

## Progress
- 2026-08-22 14:02 — drafted changelog from git log
```

## API

- **get** — read `.goal.md`. No file means no goal is set. Report the
  objective, status, and latest progress entries when asked about goal status.
- **create(objective)** — write `.goal.md` with `status: active` and today's
  date. If an `active` goal already exists, do NOT silently replace it; show
  it and ask whether to complete, pause, or replace. Only create a goal when
  the user explicitly asks for a persistent goal; do not infer goals from
  ordinary tasks.
- **update(note)** — append one dated line to `## Progress` after each
  meaningful work session toward the goal. Keep notes short and factual.
- **complete()** — set `status: done`. Only when the objective has actually
  been achieved and no required work remains — not because the session is
  ending or momentum ran out.

## Session behavior

At the start of a session in a repo containing `.goal.md`:

- `status: active` — surface the objective to the user and continue working
  toward it before starting unrelated work. Append a progress note when you
  stop.
- `status: paused` — mention it exists; resume only if the user asks.
- `status: done` — leave it as history; offer to archive or replace.

## Rules

- One active goal per repository. The file is the source of truth — never keep
  goal state only in conversation memory.
- Never delete or rewrite past progress lines; append.
- Completion must reflect reality. An agent that marks a half-finished goal
  done defeats the entire mechanism.
