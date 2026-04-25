# Cursor extension listing

Steps to publish Coco for Cursor users.

## Cursor's distribution model

Cursor doesn't have a traditional extension marketplace like VS Code. Cursor distributes:

- **Rules** — copied from `~/.cursor/rules/*.mdc`
- **Skills** — copied from `~/.cursor/skills/<name>/SKILL.md`
- **MCP servers** — registered in `~/.cursor/mcp.json`

Coco's cursor adapter handles all three. Distribution = telling Cursor users how to install.

## Recommended distribution channels

| Channel | Status |
|---------|--------|
| Cursor's official "rules library" page | https://cursor.com/rules — submit a link |
| Cursor's Discord | Share in `#community-rules` channel |
| Awesome Cursor lists | https://github.com/PontusHultkrantz/awesome-cursor (or similar) |
| Reddit r/cursor | Post with screenshot + install instructions |
| Direct install instructions in Coco's README | Already done ✓ |

## Marketing copy for Cursor users

**Tagline:** Cursor + Coco = a curated team of skills.

**Description:**
> Coco gives Cursor 59 skills, 34 namespaced commands, 10 agents, and 15 cross-IDE rules. Install in 90 seconds, then invoke `/clone-website`, `/code-verification`, `/team:ship`, `/dr-plan`, `/c4-architecture`, and dozens more from inside Cursor. The same skills also work in Claude Code, Codex, and any AGENTS.md tool — switch IDEs anytime, your skills follow.

**Install instructions:**

```bash
git clone https://github.com/rkz91/coco.git
cd coco
bash install.sh --adapter cursor
```

Adds to `~/.cursor/`:
- `skills/` — 59 skill folders
- `rules/` — 15 cross-IDE rules in `.mdc` format

## Submission checklist

- [x] Working cursor adapter (`adapters/cursor/install.sh`)
- [x] Cursor-specific `.mdc` rules in `rules/cursor-mdc/`
- [x] Cursor-specific helper skills in `adapters/cursor/skills/`
- [x] LICENSE, README, CONTRIBUTING
- [ ] Demo screenshot or asciinema cast
- [ ] Submission to Cursor official rules library (link below)
- [ ] Discord post in `#community-rules`
- [ ] Reddit post with install walkthrough

## Submission links

- Cursor official rules submission: https://cursor.com/rules (or via PR to Cursor docs repo when public)
- Cursor Discord: invite link in Cursor app
- Awesome Cursor lists: https://github.com/PontusHultkrantz/awesome-cursor

## Status

This file is the playbook for outreach. Actual submission can happen anytime — the technical artifacts are already ready and stable.
