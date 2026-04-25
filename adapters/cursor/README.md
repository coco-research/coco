# Cursor adapter

Wires Coco artifacts into `~/.cursor/` for the Cursor IDE.

## Install

```bash
bash adapters/cursor/install.sh
```

## What it does

- `skills/<name>/` → `~/.cursor/skills/<name>/` (symlink)
- `rules/cursor-mdc/*.mdc` → `~/.cursor/rules/*.mdc` (copy)
- `adapters/cursor/skills/<name>/` → `~/.cursor/skills/<name>/` (Cursor-specific helpers)
