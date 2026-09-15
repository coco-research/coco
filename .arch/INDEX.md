# Architecture Index — coco

**Pinned at:** 6a22fe8 (2026-09-15) · **Validator:** exit 0, 10 paths verified
**Source:** repository crawl (`scripts/repo_tree.py`, depth 4, 819 files, not truncated) · **Altitude:** C4-Container

Structural index only. Component paths describe where code lives; they are not
work-assignment boundaries, and a single component may legitimately own more than a
thousand files — `systems/` and `skills/` each do. Drift detection covers structural
change only: a component reworked entirely inside its own already-claimed directory
produces no drift. See `team:architecture.md` for the protocol and its stated limits.

| Component | Purpose | Primary paths |
|---|---|---|
| Agent Skill Library | Delivers reusable agent capabilities as self-contained skill directories with SKILL.md manifests, reference documents, scripts, and templates that agents load on demand to perform specialized tasks. | `skills` |
| Slash Command Surface | Delivers namespaced slash commands as markdown files under commands/<namespace>/, including the team orchestration router that selects roles and sequences agent handoffs across the four-layer protocol. | `commands` |
| Bundled Orchestration Systems | Delivers multi-phase project orchestration, knowledge tracking, persona councils spanning a growing set of professional domains, and video generation as optional bundles under systems/, each shipping its own nested skills, agents, personas, and validation scripts that install independently of the core asset set. | `systems` |
| Subagent Role Definitions | Delivers named subagent roles and behavioural rules that commands dispatch work to, so each role's system prompt is defined once in agents/ and rules/ and reused across every pipeline that spawns it. | `agents`, `rules` |
| Multi-Editor Install Adapters | Delivers installation across every editor and CLI adapter under adapters/, including Claude Code, Cursor, VS Code and the Copilot CLI, Codex, Grok, Amazon Q, and other AGENTS.md consumers, by mapping skills, commands, and agents into each tool's configuration directory under a per-adapter namespace convention, with a Homebrew formula and bootstrap script for first-time setup. | `adapters`, `bin`, `Formula`, `install.sh` |

`skills/` additionally shares `templates/` with the command surface.

## Deliberately unclaimed

Under the runtime-only rule in `skills/arch-index/references/component-rules.md`, these
are not components and belong to none: `scripts/` and `docs/` (build tooling and the
catalogs it generates), `.github/` (continuous integration), `tests/`, `examples/`,
`assets/` and `coco/` (site media), `mcps/` (reference documentation cataloguing MCP
connectors, not runtime code), and `.arch/` (this artifact). They are real and they
matter; they are not part of the runtime an agent consumes.

## What this index does not say

It records where code lives, not what an install delivers, and here those diverge
sharply: the largest single piece of the command surface is generated at install time
rather than committed. That question is answered empirically, by installing every
adapter and counting, in [`adapters/INDEX.md`](../adapters/INDEX.md).

## Diagram

```mermaid
C4Container
  title Architecture Index — coco
  Container(skill_library, "Agent Skill Library", "markdown + scripts")
  Container(command_surface, "Slash Command Surface", "markdown + generated")
  Container(system_bundles, "Bundled Orchestration Systems", "markdown + registries")
  Container(agent_roster, "Subagent Role Definitions", "markdown")
  Container(install_adapters, "Multi-Editor Install Adapters", "shell + ruby")
  Rel(skill_library, command_surface, "Capability invocation")
  Rel(skill_library, install_adapters, "Skill registration")
  Rel(skill_library, system_bundles, "Nested skill hosting")
  Rel(command_surface, system_bundles, "Bundled command registration")
  Rel(command_surface, agent_roster, "Role dispatch")
  Rel(command_surface, install_adapters, "Command registration")
  Rel(system_bundles, install_adapters, "Bundle registration")
  Rel(agent_roster, install_adapters, "Agent registration")
```

Render with `design:mermaid` (beautiful-mermaid), never the standard Mermaid CDN.

## Regenerating

This file is derived from `.arch/index.json` and is rewritten on every build. Edit the
JSON, never this file; if the two disagree, the JSON wins.

```bash
python3 skills/arch-index/scripts/validate_index.py .arch/index.json --repo-root .
python3 skills/arch-index/scripts/arch_drift.py --repo-root .
```
