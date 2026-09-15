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

## External dependency: this bundle is not self-contained

This directory vendors the skill and agent definitions only: `README.md`, `agents/*.md` (24 files), `skills/*/SKILL.md` (68 files), and one workflow file, `workflows/autonomous.md`, per the scope named in the repository's `CREDITS.md` ("68 skills + 24 agents"). It does not vendor the upstream GSD framework's workflow documents, reference documents, templates, or its `gsd-tools.cjs` command-line tool.

Most skill files load the rest of their instructions, and some agent files load their reference material, from a separate GSD installation expected at `~/.claude/get-shit-done/`. That path is referenced directly in this bundle's `SKILL.md` and agent files, for example `@$HOME/.claude/get-shit-done/workflows/add-phase.md` or `node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" ...`. For those skills and agents to function, a user needs a working GSD installation at that path, providing at least its `bin/`, `references/`, `templates/`, and `workflows/` directories.

Installing that separate GSD toolkit is outside the scope of this bundle and this repository; consult the upstream project named in `CREDITS.md` for its own installation instructions. Only `workflows/autonomous.md` is vendored here directly, so `/gsd-autonomous` is the one command in this bundle that works without any external installation.
