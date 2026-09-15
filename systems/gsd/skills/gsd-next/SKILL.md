---
name: gsd-next
description: "Use to keep moving without inspecting progress, or when the user asks what is next in the GSD workflow. Reads STATE.md, ROADMAP.md and phase dirs to invoke the next step; --force skips safety and verification gates."
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
  - SlashCommand
---

<objective>
Detect the current project state and automatically invoke the next logical GSD workflow step.
No arguments needed — reads STATE.md, ROADMAP.md, and phase directories to determine what comes next.

Designed for rapid multi-project workflows where remembering which phase/step you're on is overhead.

Supports `--force` flag to bypass safety gates (checkpoint, error state, verification failures).
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/next.md
</execution_context>

<process>
Execute the next workflow from @$HOME/.claude/get-shit-done/workflows/next.md end-to-end.
</process>
