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
| `codex` | file generation | `./AGENTS.md` (cwd) | overwrites | Codex CLI |
| `generic` | file generation | `./AGENTS.md` (cwd) | overwrites | Aider, Continue, Windsurf, Cline |
| `vscode-continue` | symlink + copy | `~/.continue/{skills,agents,rules}` | yes | VS Code with the Continue extension |

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

## VS Code with Continue

```bash
bash install.sh --adapter vscode-continue
bash adapters/vscode-continue/install.sh --dry-run    # preview, writes nothing
```

Writes into `~/.continue/` (override the root with `CONTINUE_HOME`). Skills and agents are symlinked into the clone; the markdown files directly under `rules/` are copied. Skills come with the default bundles (176 skills and 34 agents on a plain run; `--core-only` installs the core set alone, `--systems gsd,brain` an explicit subset).

| Coco source | Destination |
|-------------|-------------|
| `skills/<name>/` | `~/.continue/skills/<name>` (symlink) |
| `agents/*.md` | `~/.continue/agents/<name>.md` (symlink) |
| `rules/*.md` | `~/.continue/rules/` (copy) |

Two things to know. The only markdown file directly under `rules/` is `rules/README.md`, so that is the only rule file copied; the Cursor `.mdc` rules are not. And the adapter does not generate slash commands, so the `/SI-*` commands are not part of this install. An existing real file or folder at a skill or agent path is skipped, not overwritten. This adapter only places the files; check that your Continue version loads these folders.

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

File-generation adapters (`codex`, `generic`):

```bash
rm path/to/project/AGENTS.md
```

VS Code with Continue (links from the clone root, plus the copied rules file):

```bash
CLONE="$(pwd)"
find ~/.continue -type l -lname "${CLONE}/*" -delete
for f in rules/*.md; do cmp -s "$f" ~/.continue/rules/"$(basename "$f")" && rm ~/.continue/rules/"$(basename "$f")"; done
```

The `cmp` guard removes a copied rule only if it is still identical to the one in the clone, and the `find` touches only links that point into the clone. Use `$CONTINUE_HOME` in place of `~/.continue` if you set it. Empty `skills/`, `agents/` and `rules/` folders are left behind; remove them if you like.

---

## Conflicts

Existing target files are handled like this:

- Symlink adapters — non-symlink files are skipped (won't overwrite)
- File-generation adapters — existing `AGENTS.md` is overwritten

Use `--dry-run` to preview before any destructive action.
