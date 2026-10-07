# Getting started

Five minutes. From zero to your first multi-agent run.

---

## Install

```bash
git clone https://github.com/coco-research/coco.git
cd coco
bash install.sh
```

Coco auto-detects your AI tool. Override if needed:

| Your tool | Command |
|-----------|---------|
| Claude Code | `bash install.sh --adapter claude-code` |
| Cursor | `bash install.sh --adapter cursor` |
| Codex CLI | `bash install.sh --adapter codex` |
| Aider | `bash install.sh --adapter aider` |
| Windsurf, Cline | `bash install.sh --adapter generic` |
| Continue (VS Code) | `bash install.sh --adapter vscode-continue` |

That's it. On Claude Code your AI now has 189 skills, 386 commands and 34 agents (measured in [`docs/delivered-counts.json`](delivered-counts.json)).

---

## Try a skill

Open a fresh project. Ask your AI:

> "Use the prd-generator skill to write a PRD for a habit-tracking app."

You get a 13-section PRD in seconds. The AI invoked [`skills/prd-generator/SKILL.md`](../skills/prd-generator/) automatically.

---

## Try a command

```
/team:plan Build a CLI for AWS cost monitoring
```

In Claude Code and Cursor, this appears as a first-class slash command. In Codex, it may not show up in a visible command palette, but the generated `AGENTS.md` still tells the model that `/team:plan` exists. Routes to [`commands/team/plan.md`](../commands/team/plan.md).

---

## Orchestration is already installed

A plain `bash install.sh` installs all 6 default bundles: GSD, Brain, Cognee, HyperFrames, Super Intelligence and M0. GSD's project orchestration (state-tracked phases, parallel agent waves, atomic commits, verification gates) is therefore available right away:

```text
/gsd-new-project
/gsd-plan-phase
/gsd-execute-phase
```

State persists in `.planning/` — survives context resets.

### Narrow your install

`--systems <list>` replaces the default bundle set, it does not add to it. `--core-only` installs no bundles at all.

```bash
bash install.sh --systems gsd      # GSD only; the other 5 bundles are not installed
bash install.sh --core-only        # core skills and commands only
```

The install receipt counts only that run, so after `--systems gsd` it reports a much smaller install. A narrower run does not remove what an earlier run already linked: those files stay until you uninstall (see [`install.md`](install.md)). `reverse-skill` is not a default bundle; opt in with `--systems reverse-skill`.

---

## Optional: semantic routing

Super Intelligence routes a prompt to teams with a local embedding model (`text-embedding-nomic-embed-text-v1.5` at `http://127.0.0.1:1234/v1/embeddings`, LM Studio's default port). It is optional: without it, routing falls back to keyword matching and says so (`keyword fallback active`). Setup and how to verify: [`install.md`](install.md#optional-semantic-routing-for-super-intelligence).

---

## Where things live

- **Skills** → [`skills/`](../skills/) (75 entries, each `<name>/SKILL.md`)
- **Commands** → [`commands/<namespace>/`](../commands/) (`team/`, `email/`, `design/`, `eng/`, `pm/`, `util/`)
- **Agents** → [`agents/`](../agents/)
- **Systems** → [`systems/`](../systems/) (gsd, brain, team)
- **Architecture** → [`architecture.md`](architecture.md)
- **Install matrix** → [`install.md`](install.md)
- **Recommended plugins** → [`recommended-plugins.md`](recommended-plugins.md)

---

## Add your own skill

```bash
mkdir -p skills/my-skill
cat > skills/my-skill/SKILL.md <<'YAML'
---
name: my-skill
description: What it does (one line, used for relevance)
domain: pm
supports: [claude-code, cursor, codex, generic]
version: 0.1.0
---

# My Skill

Markdown body.
YAML

bash install.sh   # rewires
```

Conventions: [`CONTRIBUTING.md`](../CONTRIBUTING.md).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `install.sh` skips files | Pass `--dry-run` to see what would happen |
| Symlinks didn't resolve | Re-run `bash install.sh`; check `~/.claude/skills/<name>` |
| AGENTS.md missing | `cd` to your project first; Codex/generic adapters write to cwd |
| Codex shows no slash-command menu | Expected; verify `AGENTS.md` is loaded with `codex debug prompt-input` |
| AI doesn't invoke skill | Verify SKILL.md has `description:` frontmatter (used for routing) |

Open an issue for anything not listed.
