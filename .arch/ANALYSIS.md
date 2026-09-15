# Repository analysis — coco

Produced by the `crawl` path of `skills/arch-index/SKILL.md`, from
`scripts/repo_tree.py` (depth 4, 706 files, not truncated). Consumed by the
synthesis stage that writes `.arch/index.json`; not an index itself.

## 1. Executive summary

CoCo is a framework that installs instructions, not code that runs as a service. Its
runtime is a set of markdown assets an agent reads on demand — skills, slash commands,
subagent role definitions and behavioural rules — plus the installers that place those
assets where each editor or CLI looks for them. The architecture is therefore shaped by
two questions: how capabilities are authored, and how they reach a tool.

The distinguishing structural fact is that one large surface does not exist as files at
all. The 242-command Super Intelligence family is generated at install time from the
JSON registries under `systems/superintelligence/`, so the installed command surface is
roughly eight times the size of the `commands/` directory.

## 2. Tech stack

| Concern | Technology | Purpose |
|---|---|---|
| Authored assets | Markdown + YAML frontmatter | The product. Every capability is a document with a frontmatter contract. |
| Install logic | POSIX shell (`bash`) | Per-editor installers; the only code that runs on a user's machine. |
| Catalog generation | Python 3 (stdlib + PyYAML) | Builds `*/INDEX.md`, `docs/by-domain/*`, and the SI command family. |
| Package/bootstrap | Node (`bin/coco.js`), Ruby (`Formula/coco.rb`) | npm wrapper and Homebrew formula over the same installers. |
| CI | GitHub Actions | Frontmatter lint, adapter smoke tests, bundle gate, index-freshness gates. |

No application runtime, no database, no server. Persistence, where a bundle provides it
(`brain`, `cognee`, `m0`), is delegated to each bundle's own external store.

## 3. Architecture overview

Four authored asset trees sit at the root — `skills/`, `commands/`, `agents/`,
`rules/` — and one bundle tree, `systems/`, holds optional systems that ship their own
nested copies of the same four shapes. That duplication is deliberate: a bundle must
install independently, so it cannot depend on the core asset set.

`adapters/` holds one directory per install target. Every adapter reads the same asset
trees and writes into a different tool's configuration directory. Two of the five also
run the Super Intelligence generators as part of install.

Data flows one way. Authoring happens in the repo; the adapters project it outward into
editor configurations; generated catalogs (`INDEX.md`, `docs/by-domain/`) are derived
from frontmatter and committed so drift is reviewable.

## 4. Core components

**Agent Skill Library** (`skills/`) — self-contained capability directories, each with
a `SKILL.md` manifest plus optional references, scripts and templates. Feeds the command
surface and the adapters.

**Slash Command Surface** (`commands/`) — namespaced commands as flat markdown, six
namespaces including `team`, the four-layer orchestration router. 38 committed here;
242 more are generated at install.

**Bundled Orchestration Systems** (`systems/`) — opt-in bundles shipping nested skills,
agents and registries: GSD (68 skills, 24 agents), HyperFrames (20), Super Intelligence
(9 skills over 389 personas), brain, cognee, m0. The SI registries are the source the
generators read.

**Subagent Role Definitions** (`agents/`, `rules/`) — the named roles commands dispatch
to, plus the Cursor `.mdc` behavioural rules loaded alongside them.

**Multi-Editor Install Adapters** (`adapters/`, `bin/`, `Formula/`, `install.sh`) — five
targets (Claude Code, Cursor, VS Code/Copilot CLI, Codex, generic AGENTS.md) plus the
npm wrapper and Homebrew formula. Each adapter carries a `manifest.json` declaring the
surfaces and bundles it supports.

## 5. Data flow

Inward: a user invokes a slash command or the agent loads a skill by description; both
resolve to markdown read from the installed target directory, which usually symlinks
back into the checkout.

Persistence: none at the framework level. Bundles that need state own their own store
outside the repo.

Outward: `build-index.py` reads frontmatter to emit catalogs; `build_commands.py` and
`build_meta_commands.py` read the SI registries to emit commands; the adapters write
into `~/.claude`, `~/.cursor`, `~/.copilot`, `~/.codex` and equivalent.

## 6. External integrations

`install.sh` clone-and-run is the entry point; an npm wrapper and a Homebrew formula sit
over it. There is no telemetry, no remote fetch at install time, and no network
dependency in the generated command family — the generators read local registries. Media
skills reference third-party tooling (HyperFrames, Remotion, ffmpeg) at use time rather
than install time.

## 7. Key architectural decisions

**The command surface is generated, not committed.** 242 commands derive from nine
registries so a roster change propagates without hand-editing. The cost is that the
delivered surface is invisible to a file listing, and an adapter that omits the
generator step under-delivers silently — which is why `adapters/INDEX.md` is generated
by *running* the installers rather than by reading the tree.

**Bundles are opt-in.** Keeps the default install small; makes the advertised totals
reachable only with an explicit `--systems` flag.

**Two generations of adapters.** The first wrote AGENTS.md for `codex` and `generic`;
the later ones link real files into editor-specific directories.

**Everything is committed, including generated catalogs.** Regeneration is gated in CI,
so a stale index fails the build rather than drifting unnoticed.

**The doc trees are not components.** `scripts/`, `docs/`, `tests/`, `.github/`,
`assets/` and `coco/` are excluded under the runtime-only rule — real, and not part of
the runtime an agent consumes.
