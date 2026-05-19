# Codex adapter

Generates an `AGENTS.md` file for OpenAI Codex CLI by compiling Coco's skills, commands, agents, and rules.

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

Codex follows the [AGENTS.md spec](https://agents.md/). The generated file has four sections:

1. **Skills** — skill name + description (one line each)
2. **Commands** — command names and descriptions injected into model context
3. **Agents** — specialized subagents available to the model
4. **Rules** — full rule bodies pasted inline

Codex picks this up automatically when you `cd` into the project.

Important: Codex does not necessarily render these as a visible slash-command palette. The `Commands` section is still useful because it tells the model which workflows exist and what they are called. You can invoke them literally (for example `/team:plan`) or ask for them in plain English.

To verify that Codex is loading the generated file:

```bash
codex debug prompt-input
```

Look for the generated `AGENTS.md` content in the prompt dump.
