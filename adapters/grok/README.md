# Grok adapter

Wires Coco artifacts into `~/.grok/` for Grok Build / Grok CLI.

## Install

```bash
bash adapters/grok/install.sh
bash adapters/grok/install.sh --systems gsd,brain,cognee,hyperframes,superintelligence,m0
bash adapters/grok/install.sh --dry-run
```

Or from the repo root:

```bash
bash install.sh --adapter grok --systems gsd,brain,cognee,hyperframes,superintelligence,m0
```

## What it does

- `skills/<name>/` → `~/.grok/skills/<name>/` (symlink)
- `commands/<ns>/<name>.md` → `~/.grok/commands/<ns>:<name>.md` (symlink, flattened)
- `commands/<ns>/_index.md` → `~/.grok/commands/<ns>.md`
- `agents/*.md` → `~/.grok/agents/*.md` (symlink; skips INDEX.md / README.md)
- `rules/cursor-mdc/*.mdc` → `~/.grok/rules/*.md` (symlink; Grok scans `*.md`)
- `workflows/*.md` → `~/.grok/commands/workflow:<name>.md`
- `--systems` bundles → skills / agents / generated SI commands
- Super Intelligence team `SKILL.md` folders → `~/.grok/skills/si-<team>/`
- If `~/.coco/bin/coco-platform-mcp` exists, registers it in `~/.grok/config.toml`
- If `~/.coco/bin/coco-m0-hook` exists, writes `~/.grok/hooks/coco-m0.json`

Reload the Grok session (or start a new one) to pick up the new files.

## Uninstall

```bash
find ~/.grok -type l -lname "*$(pwd)*" -delete
```
