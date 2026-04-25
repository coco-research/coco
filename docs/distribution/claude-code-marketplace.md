# Claude Code plugin marketplace listing

Steps to publish Coco as a Claude Code plugin so it's discoverable inside Claude Code.

## Background

Anthropic maintains a curated plugin marketplace at https://github.com/anthropics/claude-plugins (or via Claude Code's built-in `/plugin` browser). Publishing means users can install Coco with `/plugin install coco` directly inside Claude Code.

## Prerequisites

- Coco repo public on GitHub ✓
- LICENSE (MIT) ✓
- README ✓
- CONTRIBUTING ✓
- CODE_OF_CONDUCT ✓
- SECURITY ✓
- Working `bash install.sh` ✓
- v0.1.0 tagged ✓

## Plugin manifest

Create `.claude-plugin.json` at repo root:

```json
{
  "name": "coco",
  "displayName": "Coco",
  "description": "An entire team. Wherever your AI lives. Open-source AI workflow framework with skills, agents, commands, and multi-agent orchestration.",
  "version": "0.1.0",
  "author": "Coco Inc",
  "license": "MIT",
  "homepage": "https://github.com/rkz91/coco",
  "repository": {
    "type": "git",
    "url": "git+https://github.com/rkz91/coco.git"
  },
  "install": {
    "command": "bash",
    "args": ["adapters/claude-code/install.sh"]
  },
  "compatibility": {
    "claude-code": ">=0.1.0"
  },
  "tags": [
    "ai",
    "agent-skills",
    "orchestration",
    "multi-agent",
    "pm-tools",
    "developer-tools"
  ],
  "categories": [
    "skills-library",
    "orchestration",
    "productivity"
  ]
}
```

## Submission

1. Fork [anthropics/claude-plugins](https://github.com/anthropics/claude-plugins) (or whichever repo Anthropic publishes for the marketplace registry)
2. Add an entry pointing to this repo + `.claude-plugin.json`
3. Open PR with description following Anthropic's template
4. Address review feedback
5. After merge, Coco appears in `/plugin install` browser

## Internal verification before submission

Run the adapter in dry-run mode and confirm clean output:

```bash
bash adapters/claude-code/install.sh --dry-run
```

Confirm the manifest validates:

```bash
python3 -c "import json; json.load(open('.claude-plugin.json'))"
```

## Marketing copy for the marketplace listing

**Tagline:** An entire team. Wherever your AI lives.

**Description:**
> Coco turns your Claude Code session into a multi-agent orchestrator. Install 59 skills, 34 commands, 10 specialized agents, and 3 opinionated system bundles in 90 seconds. Run `/team:ship` to spawn a research-to-shipped pipeline. Run `/code-verification` to catch bugs your AI just introduced. Run `/clone-website` to reverse-engineer any site pixel-perfect. Vendor-neutral, MIT-licensed, no telemetry, no SaaS.

**Screenshot ideas:**
- Terminal showing `/team:ship` running 7 stages
- Skills index browser
- `/code-verification` output

## Status

This file is the playbook for publishing. Actual submission requires:
- An OG image / promotional graphic
- A demo asciinema cast or GIF
- (Likely) maintainer commitment to handle issues from marketplace users

Defer until v0.1.x has stabilized and demo assets are ready.
