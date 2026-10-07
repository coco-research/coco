# Zed adapter

Places Coco's agents and rules under `~/.config/zed/`. **Zed does not read either folder today, so this install has no effect inside Zed yet** (see Limitations).

## Install

```bash
bash install.sh --adapter zed
# or run the adapter directly
bash adapters/zed/install.sh

# preview without writing
bash adapters/zed/install.sh --dry-run
```

Flags: `--dry-run`, `--systems <list>`, `--core-only`. Run directly, the adapter installs the core set only. Run through `install.sh`, the default bundles are passed in; only bundles that ship agents contribute anything (`gsd`, 24 agents).

## What it does

Target root: `~/.config/zed/` (override with `ZED_HOME`).

- `rules/*.md` → `~/.config/zed/rules/` (copied). The only markdown file directly under `rules/` is `README.md`, so that is all that is copied. The Cursor rules in `rules/cursor-mdc/*.mdc` are not.
- `agents/*.md` → `~/.config/zed/agents/` (symlinks into the clone). This includes the `README.md`, `INDEX.md` and `PROMPT-DEFENSE.md` files that sit beside the agents: 13 links from a direct run, 37 through `install.sh`.
- `--systems <list>` adds each listed bundle's `agents/*.md` the same way. It links no skills or commands.

An existing real file at an agent path is skipped, not overwritten. Re-runs replace the symlinks.

## Limitations

- **Zed is not known to read `~/.config/zed/rules/` or `~/.config/zed/agents/`.** Zed's documented place for personal instructions is `~/.config/zed/AGENTS.md`, and for skills `~/.agents/skills/`. This adapter writes neither, so the installer reports `Done.` while Zed has nothing new to load. Tracked in issue #227.
- No skills, no slash commands (so no `/SI-*` commands) and no Cursor rules are delivered.
- Until that is fixed, the files are only useful if you point something at them yourself, for example by copying content into `~/.config/zed/AGENTS.md`.

## Uninstall

```bash
# Run from the clone root. Match the clone path plus a trailing slash so a
# directory named `coco` cannot also delete links into `coco-research`.
CLONE="$(pwd)"
find ~/.config/zed -type l -lname "${CLONE}/*" -delete
for f in rules/*.md; do cmp -s "$f" ~/.config/zed/rules/"$(basename "$f")" && rm ~/.config/zed/rules/"$(basename "$f")"; done
```

The `cmp` guard removes a copied rule only if it is still identical to the one in the clone. Use `$ZED_HOME` in place of `~/.config/zed` if you set it. Empty `rules/` and `agents/` folders are left behind.
