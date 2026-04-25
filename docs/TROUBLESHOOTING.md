# Troubleshooting

Quick fixes for common issues.

---

## Install

### `install.sh` fails or hangs

```bash
bash install.sh --dry-run        # preview without writing
bash -x install.sh                # trace every command
```

If a specific adapter fails, run it directly:

```bash
bash adapters/claude-code/install.sh --dry-run
```

### Symlinks didn't resolve

Re-run `bash install.sh`. Verify:

```bash
ls -la ~/.claude/skills/<name>     # should be symlink → repo path
```

If you see a regular file at the target, remove it and re-run install:

```bash
rm ~/.claude/skills/<name>
bash install.sh
```

### Existing files block install

Symlink adapters skip targets that already exist as non-symlinks. Either remove the existing files or back them up:

```bash
mv ~/.claude/skills/<name> ~/.claude/skills/<name>.bak
bash install.sh
```

---

## Runtime

### AI doesn't invoke a skill

Check the skill's frontmatter has a `description:` field. AIs use the description for relevance scoring.

```bash
head -10 skills/<name>/SKILL.md
```

If `description:` is missing, add it. Re-run install.

### Slash command not recognized

Coco's commands install as `<namespace>:<name>` (Claude Code) or in `commands/<ns>/<name>.md` (Codex via AGENTS.md). Verify:

```bash
ls ~/.claude/commands/ | grep <name>
```

If absent, re-run install.

### AGENTS.md missing

Codex / generic adapters write to current working directory. `cd` into your project first:

```bash
cd path/to/your/project
bash /path/to/coco/adapters/codex/install.sh
```

---

## System bundles

### GSD `.planning/` directory not created

`/gsd-new-project` creates `.planning/`. If you've manually deleted it, re-run:

```bash
/gsd-new-project
```

### Brain DB not found

`/brain-init` creates `project_brain.db` in the current directory:

```bash
/brain-init
```

DB is gitignored by default. Add to `.gitignore` if you fork.

---

## Adapter-specific

### Cursor doesn't see skills

Cursor versions before 0.42 don't support skills. Use rules instead — copied automatically by the cursor adapter from `rules/cursor-mdc/` to `~/.cursor/rules/`.

### Codex `AGENTS.md` not picked up

Confirm `AGENTS.md` is at your project root (not nested). Codex reads the closest ancestor `AGENTS.md`. Re-run:

```bash
cd path/to/project
bash adapters/codex/install.sh
```

---

## Uninstall

Symlink adapters:

```bash
find ~/.claude ~/.cursor -type l -lname "*$(pwd)*" -delete
```

File-generation adapters:

```bash
rm path/to/your/project/AGENTS.md
```

---

## Still stuck?

[Open an issue](https://github.com/rkz91/coco/issues) with:
- Which adapter you used
- IDE version
- OS
- Output of `bash install.sh --dry-run`
