# Coco Documentation Index

| Doc | Read when |
|-----|-----------|
| [Getting started](getting-started.md) | First-time install + first skill call |
| [Install matrix](install.md) | Picking an adapter, troubleshooting installs |
| [Architecture](architecture.md) | Understanding the layout + frontmatter spec |
| [Recommended plugins](recommended-plugins.md) | Adding third-party plugins to complement Coco |
| [Troubleshooting](TROUBLESHOOTING.md) | Common issues and fixes |
| [Contributing](../CONTRIBUTING.md) | Adding skills, commands, agents, adapters |
| [Changelog](../CHANGELOG.md) | What changed in each release |

## By artifact type

- [Skills](../skills/) — flat library of 68 core skills (179 including bundles)
- [Agents](../agents/) — 11 subagent definitions
- [Commands](../commands/) — 37 slash commands grouped by namespace
- [Workflows](../workflows/) — multi-step playbooks
- [Templates](../templates/) — memory templates
- [Rules](../rules/) — cross-IDE rules

## By system bundle

Installable with `install.sh --systems <name>`:

- [GSD](../systems/gsd/) — project orchestration (68 skills, 24 agents)
- [HyperFrames](../systems/hyperframes/) — video and motion suite (20 skills)
- [Superintelligence](../systems/superintelligence/) — 389-persona expert board (9 team skills; generates 242 commands at install)
- [Brain](../systems/brain/) — local knowledge tracker (6 skills)
- [M0](../systems/m0/) — cross-tool agent memory (4 skills)
- [Cognee](../systems/cognee/) — knowledge-graph memory (3 skills)

See [systems/INDEX.md](../systems/INDEX.md) for the generated bundle table with live counts.

`/team` is **not** a bundle — it is core, and its commands are installed by a plain
`bash install.sh`. See [systems/team/](../systems/team/) for the design notes.

## By IDE adapter

- [Claude Code](../adapters/claude-code/)
- [Cursor](../adapters/cursor/)
- [Codex](../adapters/codex/)
- [Generic AGENTS.md](../adapters/generic/)
