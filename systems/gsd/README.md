# GSD — Get Stuff Done

Self-contained project orchestration system. State-tracked phases, atomic commits, multi-agent execution, verification gates.

## Install

```bash
bash adapters/<your-ide>/install.sh --systems gsd
```

This wires the 68 GSD skills (`gsd-*`) into your IDE's skill location.

## What it does

- **Phase planning** — break work into phases, each with research, plan, execute, verify gates
- **Multi-agent execution** — parallel waves of specialized agents
- **Atomic commits** — each step commits independently, fully reversible
- **State tracking** — `.planning/` directory holds project state across sessions

## Top-level commands

| Command | Purpose |
|---------|---------|
| `/gsd-new-project` | Initialize a new GSD project |
| `/gsd-new-milestone` | Start a new milestone cycle |
| `/gsd-plan-phase` | Create detailed phase plan with verification loop |
| `/gsd-execute-phase` | Execute all plans in a phase with wave-based parallelization |
| `/gsd-verify-work` | Validate built features through conversational UAT |
| `/gsd-ship` | Create PR, run review, prepare for merge |
| `/gsd-progress` | Check project progress, route to next action |
| `/gsd-help` | Full command index |

See `skills/` for the complete inventory of 68 skills.

## State directory

GSD creates `.planning/` in the project root:

```
.planning/
├─ PROJECT.md
├─ REQUIREMENTS.md
├─ ROADMAP.md
├─ STATE.md
├─ config.json
└─ phases/
   └─ <NN-phase-slug>/
      ├─ <NN>-CONTEXT.md
      ├─ <NN>-RESEARCH.md
      ├─ <NN>-PLAN.md
      └─ <NN>-VERIFICATION.md
```

The repo's own `.planning/` is included as a dogfood example.

## Why a separate system

GSD has its own conventions, state spec, and agent pipelines that don't apply to plain skill use. Bundling under `systems/` keeps the core framework lightweight while letting GSD users opt in.
