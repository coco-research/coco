# Architecture Index — coco

**Pinned at:** 992abf3 (2026-09-04) · **Validator:** exit 0, 10 paths verified
**Source:** crawl · **Altitude:** C4-Container

Structural index only. Component paths describe where code lives; they are not
work-assignment boundaries, and a single component may legitimately own thousands of
files. Drift detection covers structural change only — a component whose datastore was
swapped inside its own already-claimed directory produces no drift. See
`team:architecture.md` for the protocol and its stated limits.

| Component | Purpose | Primary paths |
|---|---|---|
| Agent Skill Library | Delivers reusable agent capabilities as self-contained skill directories with SKILL.md manifests, reference documents, scripts, and templates that agents load on demand. | `skills/` |
| Slash Command Surface | Delivers namespaced slash commands as markdown files, including the team orchestration router that selects roles and sequences agent handoffs. | `commands/` |
| Bundled Orchestration Systems | Delivers multi-phase project orchestration, knowledge tracking, persona councils, and video generation as optional bundles under systems/, each shipping its own nested skills, agents, personas, and validation scripts. | `systems/` |
| Subagent Role Definitions | Delivers named subagent roles and behavioural rules that commands dispatch work to, defined once and reused across every pipeline. | `agents/`, `rules/` |
| Multi-Editor Install Adapters | Delivers installation across Claude Code, Cursor, VS Code, Codex, and generic editors by mapping assets into each tool's configuration directory, with a Homebrew formula and bootstrap script. | `adapters/`, `bin/`, `Formula/`, `install.sh` |

## Diagram

```mermaid
C4Container
  title Architecture Index — coco
  Container(skill_library, "Agent Skill Library", "Markdown + Python + Shell")
  Container(command_surface, "Slash Command Surface", "Markdown")
  Container(system_bundles, "Bundled Orchestration Systems", "Python + Markdown + JSON")
  Container(agent_roster, "Subagent Role Definitions", "Markdown")
  Container(install_adapters, "Multi-Editor Install Adapters", "Shell + Ruby + JSON")
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