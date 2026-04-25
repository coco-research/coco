# Install

Per-adapter detail. For the 30-second version, see [`README.md`](../README.md).

---

## At a glance

| Adapter | Mechanism | Target | Re-runs idempotent | Best for |
|---------|-----------|--------|---------------------|----------|
| `claude-code` | symlink | `~/.claude/{skills,commands,agents}` | yes | Anthropic CLI |
| `cursor` | symlink + copy | `~/.cursor/{skills,rules}` | yes | Cursor IDE |
| `codex` | file generation | `./AGENTS.md` (cwd) | overwrites | Codex CLI |
| `generic` | file generation | `./AGENTS.md` (cwd) | overwrites | Aider, Continue, Windsurf, Cline |

---

## Common flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Print what would happen, don't write |
| `--help` | Show usage |
| `--systems gsd,brain,team` | Install one or more system bundles (claude-code, cursor only) |

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
```

Wires:
- `skills/<name>/` → `~/.cursor/skills/<name>/`
- `rules/cursor-mdc/*.mdc` → `~/.cursor/rules/*.mdc`
- `adapters/cursor/skills/*` → `~/.cursor/skills/*` (Cursor-specific helpers)

Verify in Cursor: open command palette, search for skill names.

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
| `team` | Multi-agent pipeline conventions | `--systems team` |

Combine freely:

```bash
bash install.sh --systems gsd,brain
```

---

## Uninstall

Symlink-based adapters (`claude-code`, `cursor`):

```bash
find ~/.claude ~/.cursor -type l -lname "*$(pwd)*" -delete
```

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
