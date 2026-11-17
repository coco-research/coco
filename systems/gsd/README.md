# GSD — Get Stuff Done

Project orchestration system. State-tracked phases, atomic commits, multi-agent execution, verification gates.

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

## Bundled runtime

Coco ships the upstream toolkit in `runtime/`, byte-identical at commit
`bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815` of
[gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done).
The MIT licence and copyright are in `runtime/LICENSE`; `runtime-pin.json`
records every upstream Git blob. No upstream runtime text is patched.

The Claude Code installer links `~/.claude/get-shit-done` to this copy when
that path is absent or is already Coco's link. It preserves an existing user
directory or foreign link and prints `kept your get-shit-done; Coco's copy not linked`.
Other adapters retain their existing behavior; for them, an upstream GSD
installation may still be needed at the path referenced by the skill files.

`bash tests/check-gsd-refs.sh` verifies all pinned bytes, all 89 literal file
references used by the shipped skills and agents, repeat installation into a
synthetic target, and preservation of a planted user directory. It uses no network.
