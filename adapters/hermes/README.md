# Hermes adapter

Symlinks Coco artifacts into a [Hermes Agent](https://github.com/NousResearch/hermes-agent) profile, so every Hermes bot gets the full Coco library.

## Install

```bash
# current profile (HERMES_PROFILE env or 'dev' default)
bash adapters/hermes/install.sh

# explicit profile
bash adapters/hermes/install.sh --profile tester

# every profile on the machine
bash adapters/hermes/install.sh --all-profiles

# add system bundles
bash adapters/hermes/install.sh --all-profiles --systems gsd,brain,team,superintelligence,cognee,hyperframes,m0
```

Preview without writing:

```bash
bash adapters/hermes/install.sh --dry-run
```

## What it does

Hermes profiles live at `~/.hermes/profiles/<profile>/`. The adapter wires:

- `skills/<name>/` → `<profile>/skills/<name>/` (symlink — Hermes discovers skills here)
- `systems/<bundle>/skills/*` → `<profile>/skills/*` (when `--systems` passed)
- `agents/*.md` → `<profile>/home/.claude/agents/*.md` (symlink)
- `commands/*.md` → `<profile>/home/.claude/commands/*.md`
- rules → appended as an idempotent marker-wrapped block to `<profile>/home/.claude/CLAUDE.md`
- Super Intelligence `/SI-*` commands generated into `<profile>/home/.claude/commands`

## Environment overrides

- `HERMES_PROFILES` — profiles root (default `~/.hermes/profiles`)
- `HERMES_PROFILE` — default profile name when `--profile` is not given

## Uninstall

```bash
find ~/.hermes/profiles -type l -lname "*<path-to-coco-repo>*" -delete
```

The rules block is removed automatically on the next install run without the repo; otherwise strip everything between `<!-- coco:rules-start -->` and `<!-- coco:rules-end -->`.
