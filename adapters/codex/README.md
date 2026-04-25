# Codex adapter

Generates an `AGENTS.md` file for OpenAI Codex CLI by compiling Coco's skills, commands, and rules.

## Install

```bash
cd path/to/your/project
bash /path/to/coco/adapters/codex/install.sh
```

This writes `./AGENTS.md` in the current directory.

Custom output path:

```bash
bash adapters/codex/install.sh -o ~/projects/my-app/AGENTS.md
```

Preview:

```bash
bash adapters/codex/install.sh --dry-run
```

## Format

Codex follows the [AGENTS.md spec](https://agents.md/). The generated file has three sections:

1. **Skills** — skill name + description (one line each)
2. **Commands** — slash commands available, fully namespaced
3. **Rules** — full rule bodies pasted inline

Codex picks this up automatically when you `cd` into the project.
