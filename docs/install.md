# Install

Canonical path from a clone:

```bash
bash install.sh
bash install.sh --adapter cursor
bash install.sh --adapter claude-code
bash install.sh --systems gsd,brain
bash install.sh --systems superintelligence
```

`install.sh` auto-detects the active tool. `--adapter` forces one; `--systems` replaces the default bundle set. Per-adapter wiring is below. For the 30-second version, see [`README.md`](../README.md).

---

## At a glance

| Adapter | Mechanism | Target | Re-runs idempotent | Best for |
|---------|-----------|--------|---------------------|----------|
| `claude-code` | symlink | `~/.claude/{skills,commands,agents}` | yes | Anthropic CLI |
| `cursor` | symlink + copy | `~/.cursor/{skills,rules}` | yes | Cursor IDE |
| `grok` | symlink | `~/.grok/{skills,commands,agents,rules,hooks}` | yes | Grok Build / Grok CLI |
| `vscode` | symlink + file generation | `~/.copilot/{skills,agents,instructions}` + VS Code `prompts/` | yes | VS Code chat, Copilot CLI |
| `pi-desktop` | marker-tagged copy | `~/.pi/agent/prompts` + `~/.agents/{skills,subagents}` | yes | PI-Desktop |
| `hermes` | symlink + generated files | `~/.hermes/profiles/<profile>/{skills,home/.claude}` | yes | Hermes Agent |
| `zed` | symlink + copy | `~/.config/zed/{agents,rules}` | yes | Zed |
| `codex` | file generation | `./AGENTS.md` (cwd) | overwrites | Codex CLI |
| `generic` | file generation | `./AGENTS.md` (cwd) | overwrites | Aider, Continue, Windsurf, Cline |

---

## Common flags

| Flag | Effect |
|------|--------|
| `--adapter <name>` | Force an adapter (`cursor`, `claude-code`, …) instead of auto-detect. Root `install.sh` only; equivalent to `bash adapters/<name>/install.sh`. |
| `--dry-run` | Print what would happen, don't write |
| `--help` | Show usage |
| `--systems gsd,brain` | Install one or more system bundles. Accepted by every adapter, including cursor (`~/.cursor/commands` for generated SI-* files) |

---

## Claude Code

```bash
bash adapters/claude-code/install.sh
```

Wires:
- `skills/<name>/` → `~/.claude/skills/<name>/`
- `commands/<ns>/<name>.md` → `~/.claude/commands/<ns>:<name>.md`
- `commands/<ns>/_index.md` → `~/.claude/commands/<ns>.md`
- `agents/*.md` → `~/.claude/agents/*.md`

Verify:

```bash
ls ~/.claude/skills/ | head
ls ~/.claude/commands/ | head
```

You should see symlinks pointing back into the cloned repo.

---

## Cursor

```bash
bash adapters/cursor/install.sh
bash adapters/cursor/install.sh --systems superintelligence
# equivalent flagship path:
# bash install.sh --adapter cursor --systems superintelligence
```

Wires:
- `skills/<name>/` → `~/.cursor/skills/<name>/`
- `rules/cursor-mdc/*.mdc` → `~/.cursor/rules/*.mdc`
- `adapters/cursor/skills/*` → `~/.cursor/skills/*` (Cursor-specific helpers)
- `commands/<ns>/<name>.md` → `~/.cursor/commands/<ns>:<name>.md`
- `--systems superintelligence` generates SI-* command files (including `SI-Decide.md`) into `~/.cursor/commands` via `COCO_SI_COMMANDS_DIR`. Same generators as claude-code; Cursor is not a claude-code install in disguise.

Verify: `ls ~/.cursor/commands/SI-Decide.md`

---

## Grok Build / Grok CLI

```bash
bash adapters/grok/install.sh
bash adapters/grok/install.sh --systems gsd,brain,cognee,hyperframes,superintelligence,m0
```

Wires:
- `skills/<name>/` → `~/.grok/skills/<name>/`
- `commands/<ns>/<name>.md` → `~/.grok/commands/<ns>:<name>.md`
- `commands/<ns>/_index.md` → `~/.grok/commands/<ns>.md`
- `agents/*.md` → `~/.grok/agents/*.md` (skips INDEX.md / README.md)
- `rules/cursor-mdc/*.mdc` → `~/.grok/rules/*.md` (Grok scans `*.md`, not `*.mdc`)
- `workflows/*.md` → `~/.grok/commands/workflow:<name>.md`
- Super Intelligence team `SKILL.md` folders → `~/.grok/skills/si-<team>/`
- If `~/.coco/bin/coco-platform-mcp` exists, registers it in `~/.grok/config.toml` (native Grok config wins over Cursor's relative `./backend` MCP entry)
- If `~/.coco/bin/coco-m0-hook` exists, writes `~/.grok/hooks/coco-m0.json`

Verify:

```bash
ls ~/.grok/skills | head
ls ~/.grok/commands | head
```

Start a new Grok session (or reload) so MCP and hooks pick up `config.toml`.

---

## VS Code (and Copilot CLI)

```bash
bash adapters/vscode/install.sh
```

Wires:
- `skills/<name>/` → `~/.copilot/skills/<name>/`
- `agents/*.md` → `~/.copilot/agents/*.md`
- `commands/<ns>/<name>.md` → `<VS Code User>/prompts/<ns>-<name>.prompt.md`
- `commands/<ns>/_index.md` → `<VS Code User>/prompts/<ns>.prompt.md`
- `rules/cursor-mdc/*.mdc` → `~/.copilot/instructions/*.instructions.md` (generated, with `applyTo` globs)

`~/.copilot/{skills,agents,instructions}` are VS Code's own default discovery locations and
are also read by the Copilot CLI agent runtime, so one install serves the editor and the
terminal. Prompt files have no user-level default outside the VS Code profile, so commands
are linked into `<User>/prompts` and every `<User>/profiles/*/prompts` found — for VS Code,
VS Code Insiders and VSCodium alike.

Commands are named `<ns>-<name>` rather than Claude's `<ns>:<name>`, because VS Code takes
the slash-command name from the filename and a colon is not portable.

Adapter-specific flags:

| Flag | Effect |
|------|--------|
| `--source /path/to/coco` | Link artifacts from another checkout — useful when running from a git worktree that may later be removed |
| `--user-dir "<dir>"` | Add a VS Code `User` folder the detector missed |

Verify:

```bash
ls ~/.copilot/skills | head
ls "$HOME/Library/Application Support/Code/User/prompts" | head   # macOS
```

Then reload VS Code (**Developer: Reload Window**); type `/` in chat to see the commands,
and open **Chat: Configure Agent Skills** to see the skills.

---

## Codex / Generic (AGENTS.md)

```bash
cd path/to/your/project
bash /path/to/coco/adapters/codex/install.sh
```

Generates `./AGENTS.md` in the project root. Codex picks it up automatically.

The `generic` adapter is the same script under a different name — for users of Aider, Continue, Windsurf, Cline, etc.

---

## PI-Desktop

```bash
bash install.sh --adapter pi-desktop
bash adapters/pi-desktop/install.sh --dry-run    # preview, writes nothing
```

Auto-detected when `~/.pi/agent` or `~/.agents` exists and Claude Code is not. It copies, rather than links, so PI-Desktop reads real files:

| Coco source | Destination |
|-------------|-------------|
| `commands/<ns>/<name>.md` | `~/.pi/agent/prompts/<ns>-<name>.md` |
| `skills/<name>/` | `~/.agents/skills/<name>/` |
| `agents/*.md` | `~/.agents/subagents/coco-<name>.md` |
| Super Intelligence `/SI-*` commands (generated) | `~/.pi/agent/prompts/` |

Every file the adapter writes carries a `Coco PI-Desktop adapter` marker; it only replaces or deletes marked files and reports anything else as untouched (`--force` replaces those). Skill descriptions are clipped to PI-Desktop's 240-character cap. `PI_AGENT_HOME` and `AGENTS_HOME` override the two roots. Restart PI-Desktop or open a new session afterwards. More: [`adapters/pi-desktop/README.md`](../adapters/pi-desktop/README.md).

---

## Hermes

```bash
bash install.sh --adapter hermes                         # profile from HERMES_PROFILE, default "dev"
bash adapters/hermes/install.sh --profile tester         # explicit profile
bash adapters/hermes/install.sh --all-profiles           # every profile under ~/.hermes/profiles
```

Writes into `~/.hermes/profiles/<profile>/` (override the root with `HERMES_PROFILES`); a missing profile is created. Skills are symlinked into `<profile>/skills/`. Agents, commands and rules go into the Claude-compatible home `<profile>/home/.claude/`: agents and commands are symlinked, the rules go into an idempotent block between `<!-- coco:rules-start -->` and `<!-- coco:rules-end -->` in `CLAUDE.md`, and the Super Intelligence `/SI-*` commands are generated there as real files. A real file already at a target is not overwritten; it is reported as `STALE` and left for you to remove. Restart any running Hermes gateway afterwards. More: [`adapters/hermes/README.md`](../adapters/hermes/README.md).

---

## Zed

```bash
bash install.sh --adapter zed
bash adapters/zed/install.sh --dry-run
```

Writes into `~/.config/zed/` (override with `ZED_HOME`): the markdown files in `rules/` are copied to `~/.config/zed/rules/`, and each `agents/*.md` is symlinked into `~/.config/zed/agents/`. System bundles contribute only the agents they ship; this adapter links no skills or commands. An existing real file at an agent target is skipped, not overwritten.

---

## System bundles

| Bundle | What | Install |
|--------|------|---------|
| `gsd` | 68-skill project orchestration | `--systems gsd` |
| `brain` | 6-skill local knowledge tracker | `--systems brain` |
| `cognee` | 3-skill knowledge-graph memory | `--systems cognee` |
| `hyperframes` | 20-skill video and motion suite | `--systems hyperframes` |
| `superintelligence` | 495-persona expert board, generates 342 commands at install | `--systems superintelligence` |
| `m0` | 4-skill cross-tool agent memory | `--systems m0` |

Combine freely:

```bash
bash install.sh --systems gsd,brain
```

---

## Optional: semantic routing for Super Intelligence

Super Intelligence picks which teams to seat with `systems/superintelligence/scripts/meta_select.py`. It embeds your prompt against each team's profile by calling an OpenAI-compatible embeddings endpoint on this machine:

- URL: `http://127.0.0.1:1234/v1/embeddings` (LM Studio's default port)
- Model name sent: `text-embedding-nomic-embed-text-v1.5`

Both values are hard-coded in the script, so the server must answer on that port and accept that model name.

Without the endpoint nothing breaks. The script falls back to keyword overlap, prints `meta_select WARN: keyword fallback active` on stderr, marks its output `"method": "keyword"` and `"degraded": true`, and never auto-delegates to a single team. Routing still works, but team selection is coarser.

To use embeddings: load the nomic-embed-text-v1.5 model in LM Studio, start its local server, then check:

```bash
curl -s -m 3 http://127.0.0.1:1234/v1/models   # any JSON reply means the endpoint is up
python3 systems/superintelligence/scripts/meta_select.py "should we ship an AI compliance product?"   # "method": "embed" when it is used
```

---

## Uninstall

Symlink-based adapters (`claude-code`, `cursor`, `grok`, `vscode`):

```bash
# Run from the clone root. Match the clone path plus a trailing slash so a
# directory named `coco` cannot also delete links into `coco-research`.
CLONE="$(pwd)"
find ~/.claude ~/.cursor ~/.grok ~/.copilot -type l -lname "${CLONE}/*" -delete
find "$HOME/Library/Application Support/Code/User" -type l -lname "${CLONE}/*" -delete   # macOS prompts
grep -rl "Generated by the Coco VS Code adapter" ~/.copilot/instructions | xargs rm -f  # generated rules only
rm -rf ~/.copilot/coco-generated
```

`~/.copilot/instructions` is a VS Code default folder that may also hold your own
instruction files, so match on the generated-by marker rather than deleting the folder.

PI-Desktop:

```bash
bash adapters/pi-desktop/install.sh --uninstall
rm -f ~/.pi/agent/prompts/SI*.md   # generated /SI-* commands are not marker-tagged, so --uninstall leaves them
```

`--uninstall` removes only files carrying the adapter's marker; skills you wrote yourself stay. Check that no `SI*.md` in that folder is your own before the `rm`.

Hermes (links from the clone root; generated files and the rules block by hand):

```bash
CLONE="$(pwd)"
find ~/.hermes/profiles -type l -lname "${CLONE}/*" -delete
rm -f ~/.hermes/profiles/<profile>/home/.claude/commands/SI*.md
```

Then delete the block between `<!-- coco:rules-start -->` and `<!-- coco:rules-end -->` in `~/.hermes/profiles/<profile>/home/.claude/CLAUDE.md` (the installer also leaves a `CLAUDE.md.coco-bak` copy beside it).

Zed (agent links, plus the copied rules file):

```bash
CLONE="$(pwd)"
find ~/.config/zed -type l -lname "${CLONE}/*" -delete
for f in rules/*.md; do cmp -s "$f" ~/.config/zed/rules/"$(basename "$f")" && rm ~/.config/zed/rules/"$(basename "$f")"; done
```

The `cmp` guard removes a copied rule only if it is still identical to the one in the clone.

File-generation adapters (`codex`, `generic`):

```bash
rm path/to/project/AGENTS.md
```

---

## Conflicts

Existing target files are handled like this:

- Symlink adapters — non-symlink files are skipped (won't overwrite)
- File-generation adapters — existing `AGENTS.md` is overwritten

Use `--dry-run` to preview before any destructive action.
