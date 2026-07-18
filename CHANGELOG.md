# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

---

## [1.1.0] — 2026-07-18

### Changed

- **Rebranded to CoCo Super Intelligence.** The README now leads with the 389-persona advisory board as the hero capability, with the orchestration framework (skills, persistent state, portability) as the supporting layer. Added new brand lockups (`assets/logo-si.svg` / `logo-si-light.svg`) and a refreshed social card (`assets/og-image.svg`); the original `coco` mark (`logo.svg` / `logo-light.svg`) is preserved unchanged.
- **Repository migrated to the `coco-research` GitHub org.** All URLs, the npm scope (`@coco-research/coco-cli`), the Homebrew tap reference, and the publish workflows now point to `coco-research` instead of `rkz91`.
- **Relicensed to open-core.** The CoCo core stays MIT, but the Super Intelligence System (`systems/superintelligence/`) is now proprietary — source-available for reference, all rights reserved (see `systems/superintelligence/LICENSE`). The root `LICENSE` carves it out; `package.json`/`.claude-plugin.json` now declare `SEE LICENSE IN LICENSE`, the Homebrew formula uses `:cannot_represent`, and the README badge/labels read "Open-core." Bumped **Spec Version 1.0.0 → 1.1.0**. Note: MIT grants already made on prior releases of the Super Intelligence System remain valid for those snapshots; the change is forward-only.

### Fixed

- **Corrected asset counts.** Skills 146 → **147** (core 63 → 64 — `coco-ads` landed after the previous count fix), total addressable assets 864 → **865**, core install 123 → **124**. Replaced the stale `package.json` description ("59+ skills, 34+ commands") with accurate figures.
- **Expanded attribution.** Added CREDITS.md entries for Vercel and vercel-labs (web guidelines), plus reference sources for Apple (Liquid Glass), OpenAI, and Microsoft (Agent Lightning).

---

## [1.0.0] — 2026-06-07

First stable release. Establishes the Superintelligence board, the update notifier, and accurate docs.

### Added

- **Update notifier** — `npx @coco-research/coco-cli version` and `bash scripts/check-update.sh` report when a newer Coco is available. Checks the GitHub repo at most once per day, prints a one-line banner, sends no telemetry; opt out with `COCO_NO_UPDATE_CHECK=1`. The installer now prints the installed version and how to check for updates.
- **Superintelligence board expanded to 389 personas across 9 teams** (added Finance, Trading, Risk & Compliance, Strategy, Data & Analytics, GTM) plus the cross-team meta-orchestrator.

### Fixed

- **Full SI command family now generated on install.** The claude-code adapter now runs both `build_commands.py` (225 per-team) and `build_meta_commands.py` (17 cross-team), delivering all 242 SI commands instead of 225. The generators are now path-portable (derive the repo root from their own location; honor `COCO_SI_COMMANDS_DIR` / `COCO_SI_REPO`) instead of a hardcoded absolute path.
- **README accuracy** — clarified `/schedule` and `/loop` rely on the host CLI (not shipped by Coco), corrected the `vscode-continue` adapter status to experimental stub, and added Staying Current and Contributing sections.

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
