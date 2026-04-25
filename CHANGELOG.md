# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [0.1.0] — 2026-04-25

Initial public release.

### Added

- **59 skills** across foundational, PM, engineering, design, ops, meta domains
- **34 namespaced slash commands** — team, email, design, eng, pm, util
- **10 specialized subagents** at top level — code-reviewer, pm-advisor, mcp-specialist, refactoring-specialist, test-guardian, typescript-pro, ui-ux-designer, ai-engineer, data-specialist, database-architect
- **3 system bundles** — `gsd` (68 orchestration skills + 24 specialized GSD subagents), `brain` (6 knowledge skills), `team` (multi-agent pipelines)
- **claude-code adapter** wires `systems/<bundle>/agents/` and `systems/<bundle>/commands/` in addition to skills, when installed via `--systems`
- **4 IDE adapters** — `claude-code`, `cursor`, `codex`, `generic` (AGENTS.md)
- **Single-entry installer** — `bash install.sh` auto-detects target IDE
- **Frontmatter spec** — vendor-neutral artifact format ([`docs/architecture.md`](docs/architecture.md))
- **Full docs** — getting-started, install matrix, architecture, recommended-plugins
- **MIT license** — copyright Coco Inc

### Compatibility

- Stable: Claude Code, Cursor, Codex CLI, generic AGENTS.md
- Planned for v0.2: VS Code (via Continue), Antigravity (Google)

---

## Roadmap

### v0.2 (next)

- VS Code adapter (Continue integration)
- Antigravity adapter (experimental, format pending)
- CI: frontmatter linter
- Skill INDEX auto-generator
- Star history badge embed

### Backlog

- Asciinema demo casts
- Per-domain INDEX views (`docs/by-domain/<domain>.md`)
- Plugin distribution channel
- Web demo / playground
