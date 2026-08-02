# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [Unreleased]

### Fixed

- **`/team ship` no longer reconciles the architecture index mid-pipeline.** Stage 1 previously ran `/team arch build` or `/team arch drift` whenever the index was absent or behind HEAD, which meant every ship following a few commits silently paid for a full index reconciliation, with agents, before any product work began. Stage 1 now only records the pin alongside HEAD and continues, which costs nothing. Refreshing the index is a separate explicit act, and a stale baseline degrades the conformance gate to `UNVERIFIED`, which is the honest outcome.
- **Replaced an unimplementable escape hatch with a real flag.** The architecture gate previously said it could be skipped "on a repository where an index is not wanted", without defining how a pipeline was supposed to know that. `--no-arch` is now a documented flag with its own handling section, reported as `DISABLED (--no-arch)` and distinct from both a pass and `NOT APPLICABLE`. The router explicitly forbids inferring the intent from context, because a condition an agent has to guess at is not a condition.
- **Corrected how the conformance gate reads the pin after a build.** Stage 6 commits, so by the time the gate runs the pin is expected to be behind HEAD; that is precisely what makes `git diff <pin>..HEAD` the set of changes the ship made and any drift attributable to it. Currency is therefore judged once at Stage 1 rather than re-derived at gate time, and `team:architecture.md` documents this baseline convention so the two files cannot contradict each other.
- **The Cursor adapter installed no commands at all.** Its manifest covered only skills and rules, so `~/.cursor/commands/` was never touched and six symlinks left over from an earlier repository location dangled indefinitely. The adapter now installs commands, flattened to `<namespace>:<command>.md` because Cursor discovers user commands with the pattern `~/.cursor/commands/*.md` and does not recurse into subdirectories — a directory symlink resolves correctly while sitting one level too deep to be found. It also prunes command links that point outside the repository or at a directory.
- **Both installers now report skipped targets loudly.** `link_dir` leaves a real file in place rather than overwriting possible user work, which is correct, but it announced this with a quiet `Skip` line and no summary. The consequence observed in practice was an installed command set that went two months out of date while every re-install appeared to succeed. Skips are now prefixed `STALE:`, counted, and summarised with instructions at the end of the run.

- **Removed five phantom artifacts from the `/team ship` handoff table.** The table named `RESEARCH-BRIEF.md`, `ARCHITECTURE-DECISION.md`, `REVIEW-FINDINGS.md`, and `VERIFICATION-REPORT.md`, and no stage was ever instructed to write any of them. `ARCHITECTURE-DECISION.md` was the most consequential, because the single user-facing approval gate promised to present an architecture decision drawn from a file that had no producer anywhere in the repository. Every artifact in the table is now written to `.team-ship/` by the stage that owns it, and each stage body names the artifact it writes. The table also referred to a Verify stage that does not exist in the pipeline; verification is what Stages 7 through 13 are, and `EVIDENCE.md` is its artifact. Stage 14 now writes a real `SHIP-REPORT.md` on both the green and the blocked path.
- **Fixed a dangling tool pointer in the team toolkit registry.** The PRD Generation entry named `/pmstudio-prd`, which no skill declares; the skill identifies itself as `prd-generator`. An agent handed an unresolvable tool name silently falls back to the entry's `Alternative` line, which defeats the purpose of routing through the registry at all. The nine other `pmstudio-*` pointers in the registry were audited and do resolve, because those skills declare `pmstudio-*` names even though their directory names differ.
- **Stopped routing architecture documents to an infrastructure specialist.** The `/team document` type-detection branch for "architecture" and "design doc" sent the work to `senior-cloud-architect` or `senior-backend-eng` and reviewed the result only through `doc-quality`, `grammar-editor`, and `standards-reviewer` — a roster that checks structure, tone, and template conformance, and cannot assess whether the architecture described is sound. The branch now pairs `technical-writer` with the engineering role that owns the system, adds `domain-accuracy` to the review roster, and points at `/util:create-architecture-documentation` for formal published documents.
- **Corrected the asset counts in `.claude-plugin.json`,** which advertised 59 skills, 34 commands and 10 agents against a measured 179 skills, 37 in-repo commands and 34 agents, and understated the installable system bundles as three rather than 5.

### Added

- **A declare-then-verify architecture stage in `/team ship`.** Stage 3 now writes `.team-ship/ARCH-PLAN.json`, declaring the components this ship intends to build, the paths each will occupy, and the paths it must not touch. The declaration is shape-checked immediately and shown at the approval gate, so the intended architecture is something you can disagree with before any code is written. After Stage 6, a new built-as-declared gate checks that every declared path now exists and that nothing landed out of scope. A component declared and then silently dropped is a BLOCK, which no test gate can detect, because tests fail when behaviour breaks rather than when work is quietly abandoned. Implemented by `skills/arch-index/scripts/verify_arch_plan.py` with contract and rationale in `skills/arch-index/references/arch-plan.md`. Earlier analysis rejected forward architecture specifications on the grounds that path checking must be disabled for a system that does not exist yet; that holds only if the check runs at declaration time. Deferring it to after the build moves the check rather than weakening it, which is what makes the declaration enforceable.
- **`arch-index` skill and the `/team arch` action.** Together they produce and maintain `.arch/index.json`, a committed, commit-pinned map from each architectural component of the repository to the real directories and files that implement it. `scripts/validate_index.py` enforces twelve checks with a process exit code, the most important being that every claimed path resolves on disk. `scripts/arch_drift.py` performs a deterministic structural drift scan with no model calls at all, applying a deletion-first rule that removes a component when none of its primary paths survive. `scripts/repo_tree.py` emits a filtered tree whose depth is chosen by measuring the file count against a budget rather than by a fixed cap. The design is adapted from devildev by lak7 (Apache-2.0); the significant addition is that upstream stated its path-matching rule in prose, with a validation checklist of unchecked boxes, and never verified a single path in roughly thirteen hundred lines of code.
- **`team:architecture.md`, the Architecture Conformance Protocol.** Modelled on the Test Evidence Protocol, with the guiding principle "Paths or it does not exist." It carries an explicit list of the rules it does *not* mechanically enforce — currency, semantic drift, decomposition quality, and the exploration read budget — because a gate that overstates its reach is worse than one that does not exist.
- **Failure mode (e), architecture abandoned, in `/team verify`.** This is the reason the rest of the work exists. The four pre-existing failure modes are all test-evidence traps, so a build could satisfy every requirement and every test gate while having silently relocated, merged, or deleted the components it was built against. Tests do not fail when a component moves; they fail when behaviour changes. Failure mode (e) closes that gap with a shell script and no model call, and the Layer 4 verdict rule now spans (a) through (e).
- **Three roles: `solution-architect`, `architecture-reviewer`, and `repo-cartographer`.** All three carry the `all` domain tag, so no new tag was introduced — the tag vocabulary is duplicated in the router and `--roles` validates identifiers only, which means a role carrying an unlisted tag would be silently unselectable with no error. `architecture-reviewer` is the only Layer 3 role that evaluates decomposition; the existing six check structure, tone, template conformance, and factual accuracy, so an unsound architecture previously passed the review layer cleanly.
- **An architecture-conformance hard gate in `/team ship`,** alongside the existing seven. Because `.arch/` is committed rather than gitignored, this gate also runs inside the Stage 11 clean checkout; an untracked index would have made it silently unrunnable in the one path the pipeline designates as authoritative.
- **Registered six architecture-relevant assets in the team toolkit registry,** each of which existed in the repository but was invisible to every `/team` run because Layer 2 agents receive only registry excerpts and never browse the filesystem: `gsd-map-codebase` for codebase mapping, the gitnexus MCP for code-graph queries, `c4-architecture` for diagrams, `api-design-principles` for interface contracts, `/util:architecture-review` for audits, and `/util:create-architecture-documentation` for the formal document suite. Also clarified that the existing Architecture Review Decks entry is a presentation generator rather than an architecture tool.
- **Credited devildev by lak7 (Apache-2.0)** in `CREDITS.md` for the reverse-architecture design that the forthcoming `arch-index` skill builds on.

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

### Changed

- **Bumped Spec Version 1.1.0 to 1.2.0** so that it tracks the release version.

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
