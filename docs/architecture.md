# Coco Architecture

Coco is an open-source AI workflow framework. This document explains the layout, the artifact model, and how adapters wire artifacts into specific AI coding agents.

## Mental model

```
   ┌──────────────────────────────────────────────────────┐
   │                    User invokes                      │
   │              /skill, /command, etc.                   │
   └─────────────────────┬────────────────────────────────┘
                         │
   ┌─────────────────────▼────────────────────────────────┐
   │                   IDE / Agent                         │
   │   Claude Code  │  Cursor  │  Codex  │  AGENTS.md     │
   └─────────────────────┬────────────────────────────────┘
                         │
   ┌─────────────────────▼────────────────────────────────┐
   │                    Adapter                            │
   │   adapters/<ide>/install.sh + manifest.json           │
   │   • symlinks/copies artifacts to IDE-expected paths   │
   │   • runs IDE-specific transforms (e.g., .mdc compile) │
   └─────────────────────┬────────────────────────────────┘
                         │
   ┌─────────────────────▼────────────────────────────────┐
   │           Canonical artifact libraries                │
   │  skills/  agents/  commands/  mcps/  workflows/       │
   │  templates/  rules/  systems/                         │
   └──────────────────────────────────────────────────────┘
```

Single source of truth for every artifact. Adapter is the only IDE-aware layer.

## Top-level directories

| Dir | Purpose | Format |
|-----|---------|--------|
| `skills/` | Reusable capabilities Claude/agents invoke | Folder per skill, `SKILL.md` inside |
| `agents/` | Subagent definitions (specialized roles) | One `.md` per agent |
| `commands/` | Parameterized slash prompts | One `.md` per command, namespaced subdirs (`team/`, `email/`, etc.) |
| `mcps/` | Model Context Protocol servers + connector setups | `servers/` (source), `connectors/` (per-service guides), `templates/` (run.sh templates), `catalog.md` |
| `workflows/` | Multi-step playbooks combining skills/agents | One `.md` per workflow |
| `templates/` | Reusable scaffolds (memory, PRD, project-doc) | Mixed |
| `rules/` | Cross-IDE coding/process rules | Markdown source-of-truth (cursor `.mdc` derived) |
| `systems/` | Self-contained opinionated bundles | Per-bundle subdir (`gsd/`, `team/`) |
| `adapters/` | IDE-specific install scripts + manifests | Per-IDE subdir |
| `docs/` | User-facing documentation | Markdown |
| `examples/` | Sample artifacts for new contributors | Mixed |

## Artifact frontmatter spec

Every skill, agent, command, and workflow declares its metadata via YAML frontmatter at the top of its primary markdown file.

### Required fields

```yaml
---
name: <slug>                   # unique identifier within type
description: <one-line>        # used by IDE to decide relevance
domain: <domain>               # see Domains table below
supports: [<adapter>, ...]     # which adapters can install this
version: <semver>              # X.Y.Z, defaults to 0.1.0
---
```

### Optional fields

```yaml
---
tags: [<tag>, ...]             # free-form tags for filtering
inputs: [<arg>, ...]           # named arguments the artifact expects
output: <description>          # what the artifact produces
requires: [<other-artifact>]   # dependencies on other Coco artifacts
external: [<package>]          # external dependencies (npm, pip, etc.)
deprecated: <reason>           # if set, artifact is hidden from default views
---
```

### Domains

| Slug | Meaning |
|------|---------|
| `foundational` | Cross-cutting basics (brainstorming, debugging, verification) |
| `pm` | Product management workflows (PRD, roadmap, stakeholder comms) |
| `engineering` | Engineering workflows (code review, architecture, testing) |
| `design` | Design workflows (UX, UI, design system, accessibility) |
| `ops` | Operations / risk / compliance (DR, IRP, ARB, NFR) |
| `meta` | Tooling about tooling (skill creation, artifact lint) |

Domain is used to:
- Generate `docs/by-domain/<domain>.md` indexes
- Filter listings (`coco list skills --domain=pm`)
- Apply role-based install flags (`install.sh --domains pm,foundational`)

### Adapters

Current first-class adapters (v1.0.0):

| Slug | Target | Status |
|------|--------|--------|
| `claude-code` | Anthropic Claude Code CLI | stable |
| `cursor` | Cursor IDE | stable |
| `codex` | OpenAI Codex CLI | stable |
| `generic` | Any tool reading `AGENTS.md` | stable |

`supports: [claude-code, cursor, codex, generic]` declares an artifact works everywhere. Omit an adapter to mark unsupported.

## Skill folder structure

Each skill is a folder under `skills/`:

```
skills/<name>/
  SKILL.md           # primary file with frontmatter + body
  references/        # supplementary docs the skill references
  scripts/           # optional helper scripts
  templates/         # optional skill-specific templates
```

`SKILL.md` body uses standard markdown. Reference other skill files with relative paths.

## Command folder structure

Commands are flat files in namespaced subdirs:

```
commands/
  team/
    fix.md           # /team:fix
    plan.md          # /team:plan
  email/
    read.md          # /email:read
  pm/
    sync-init.md     # /pm:sync-init
```

Adapter is responsible for mapping `team/fix.md` → IDE's expected slash command location.

## Adapter contract

Each `adapters/<ide>/install.sh` must:

1. Read `manifest.json` (declares which artifact types/domains to wire)
2. Resolve target paths for that IDE (e.g., `~/.claude/skills/`, `~/.cursor/skills/`)
3. Symlink or copy from canonical sources into target paths
4. Run any IDE-specific transforms (e.g., compile `.md` rules to Cursor `.mdc`)
5. Be idempotent (re-running = no-op if already installed)
6. Support `--dry-run` flag

Manifest schema (per adapter):

```json
{
  "name": "claude-code",
  "version": "0.1.0",
  "targets": {
    "skills": "~/.claude/skills",
    "commands": "~/.claude/commands",
    "agents": "~/.claude/agents"
  },
  "transforms": [],
  "domains": ["foundational", "pm", "engineering", "design", "ops", "meta"]
}
```

## Systems

`systems/<name>/` holds opinionated, self-contained bundles. Internal layout mirrors the framework:

```
systems/gsd/
  README.md
  skills/
  commands/
  templates/
  state-spec/
```

Systems are opt-in via `install.sh --systems gsd,team`.

## Generating indexes

`docs/INDEX.md`, `docs/by-domain/<domain>.md`, and `commands/INDEX.md` are auto-generated from artifact frontmatter. Regenerate via `scripts/build-index.sh` (added in P11).
