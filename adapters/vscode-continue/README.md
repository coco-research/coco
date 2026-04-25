# VS Code adapter (via Continue) — STUB

Planned for Coco v0.2.

## What it will do

Wire Coco's skills, commands, and rules into the [Continue](https://continue.dev/) VS Code extension's config format.

## Why "via Continue"

VS Code itself doesn't have a native skills system. Continue is the most OSS-aligned extension that does. Other VS Code AI extensions (Cline, Cody, GitHub Copilot Chat) have their own incompatible formats.

If you want VS Code support today, two options work:

1. **Generic adapter** — produces AGENTS.md that Continue reads automatically:
   ```bash
   bash install.sh --adapter generic
   ```

2. **Cursor adapter** — Cursor is a VS Code fork with its own AI; Coco's Cursor adapter is stable:
   ```bash
   bash install.sh --adapter cursor
   ```

## Tracking

[Issue #4](https://github.com/rkz91/coco/issues/4) — labeled `good first issue` and `enhancement`. Open if you want to help build it.
