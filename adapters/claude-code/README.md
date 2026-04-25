# Claude Code adapter

Symlinks Coco artifacts into `~/.claude/` so they're discovered by the Claude Code CLI.

## Install

```bash
bash adapters/claude-code/install.sh
```

Add a system bundle:

```bash
bash adapters/claude-code/install.sh --systems gsd,brain
```

Preview without writing:

```bash
bash adapters/claude-code/install.sh --dry-run
```

## What it does

- `skills/<name>/` → `~/.claude/skills/<name>/` (symlink)
- `commands/<ns>/<name>.md` → `~/.claude/commands/<ns>:<name>.md` (symlink, colon namespace reconstructed)
- `commands/<ns>/_index.md` → `~/.claude/commands/<ns>.md` (base command for namespace)
- `agents/*.md` → `~/.claude/agents/*.md` (symlink)
- `systems/<bundle>/skills/*` → `~/.claude/skills/*` (when --systems flag passed)

## Uninstall

```bash
# remove symlinks coming from this repo
find ~/.claude -type l -lname "*$(pwd)*" -delete
```
