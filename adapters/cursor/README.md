# Cursor adapter

Wires Coco artifacts into `~/.cursor/` for the Cursor IDE.

## Install

```bash
bash adapters/cursor/install.sh
```

## What it does

- `skills/<name>/` → `~/.cursor/skills/<name>/` (symlink)
- `rules/cursor-mdc/*.mdc` → `~/.cursor/rules/*.mdc` (symlink)
- `adapters/cursor/skills/<name>/` → `~/.cursor/skills/<name>/` (Cursor-specific helpers)
- `commands/<ns>/<name>.md` → `~/.cursor/commands/<ns>:<name>.md` (symlink, flattened)

## Why commands are flattened

Cursor discovers user-level commands with the pattern `~/.cursor/commands/*.md` and does
not recurse into subdirectories. A directory symlink such as
`~/.cursor/commands/team -> <repo>/commands/team` therefore places every command one level
too deep to be found, even though the link itself resolves correctly. Namespacing is
preserved in the filename instead, matching the Claude Code adapter: `team:ship.md`
becomes `/team:ship`.

## Two failure modes this adapter now handles

**Real files are never silently skipped.** If a target is a regular file rather than a
symlink, the adapter leaves it alone, because it may be your own work. It also prints
`STALE:` for each one and a summary count at the end. Silently skipping is how an
installed copy can go months out of date while every re-install appears to succeed.

**Links pointing outside the repo are pruned.** Moving or renaming the repository leaves
dangling symlinks in `~/.cursor/commands`. Nothing else revisits them, so the adapter
removes any command link whose target is not inside the current repository root before
relinking.
