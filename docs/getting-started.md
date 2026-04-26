# Getting started

Five minutes. From zero to your first multi-agent run.

---

## Install

```bash
git clone https://github.com/rkz91/coco.git
cd coco
bash install.sh
```

Coco auto-detects your AI tool. Override if needed:

| Your tool | Command |
|-----------|---------|
| Claude Code | `bash install.sh --adapter claude-code` |
| Cursor | `bash install.sh --adapter cursor` |
| Codex CLI | `bash install.sh --adapter codex` |
| Aider, Continue, Windsurf, Cline | `bash install.sh --adapter generic` |

That's it. Your AI now has 59 skills, 34 commands, 11 agents.

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

## Add an orchestration system

```bash
bash install.sh --systems gsd
```

Adds 68 skills for project orchestration: state-tracked phases, parallel agent waves, atomic commits, verification gates.

```text
/gsd-new-project
/gsd-plan-phase
/gsd-execute-phase
```

State persists in `.planning/` — survives context resets.

---

## Where things live

- **Skills** → [`skills/`](../skills/) (59 entries, each `<name>/SKILL.md`)
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
