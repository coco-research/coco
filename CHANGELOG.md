# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

---

## [1.2.0] — 2026-07-31

### Added

- **`coco-loop` skill.** Turns a plain-language goal into a readable charter that the person confirms, then arms and runs a bounded autonomous loop in propose-only mode. It never commits on its own. Requires the [coco-loops](https://github.com/coco-research/coco-loops) framework, which the skill now links with install instructions.
- **`scroll-world` skill.** Builds an immersive scroll-scrubbed landing page in which a pre-rendered camera flies from outside each scene into its interior and then on to the next with no cuts. Contributed upstream by cyw under the MIT license, with the original license retained at `skills/scroll-world/LICENSE`.

### Security

- **Corrected the funding pointer.** `.github/FUNDING.yml` still referenced `rkz91`, the account name used before the 2026-07-18 rename to `coco-research`. An unrelated third party had since registered the vacated username, so the repository's Sponsor configuration pointed at a stranger. No funds could have been misdirected, because that account has no Sponsors listing, but the window is now closed.
- **Removed the remaining stale account references from the installer.** The documented `curl`-pipe-to-`bash` command and the commit-verification link in `bin/coco-bootstrap.sh` both pointed at the reclaimed `rkz91` username, which would have resolved to third-party content had that account created a repository named `coco`.
- **Added a commit-verification gate to `bin/coco-bootstrap.sh`.** The installer now clones first, prints the commit hash, date, and message, and waits for explicit confirmation before running `install.sh`. The default is fail-closed. Only `COCO_BOOTSTRAP_YES=1` or `--yes` skips it; a previous form of this check treated any non-empty value, including `0`, as consent.
- **Pinned GitHub Actions to commit SHAs** and scoped the workflows to `permissions: contents: read`. Pins target `actions/setup-node` v7 and `actions/setup-python` v5, each verified to exist upstream and to match the commit its tag currently points to.
- **Fixed a DOM cross-site-scripting vector** in `skills/brainstorming/scripts/helper.js`, which built its selection indicator by concatenating a label into `innerHTML`. It now assigns `textContent`.
- **Hardened the Cursor adapter installer.** `link_dir()` could silently overwrite a real file, and an `A && B || C` pattern could execute a real command when the dry-run echo failed.
- **Added a Content-Security-Policy** to the generated diagram artifacts, and raised the floor versions of `@modelcontextprotocol/sdk`, `hono`, `vite`, and `wrangler` in the `openai-apps-mcp` template.
- **Added prompt-injection guidance** to `find-skills`, requiring the resolved package name to be surfaced and confirmed before an agent installs a skill on someone's behalf.

Security contributions in this release are by [@imachiever](https://github.com/imachiever) (Rajat Bhatia).

### Fixed

- **Corrected asset counts** for the two new skills. Skills 147 to **149** (core 64 to **66**), total addressable assets 865 to **867**, core install 124 to **126** active assets.

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
