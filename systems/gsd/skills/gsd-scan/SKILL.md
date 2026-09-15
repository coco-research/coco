---
name: gsd-scan
description: "Use when you need a quick read on one subsystem instead of a full /gsd-map-codebase run, or the user asks to scan tech, arch, quality, or concerns. Spawns one mapper agent and writes targeted docs into .planning/codebase/."
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
  - Agent
  - AskUserQuestion
---

<objective>
Run a focused codebase scan for a single area, producing targeted documents in `.planning/codebase/`.
Accepts an optional `--focus` flag: `tech`, `arch`, `quality`, `concerns`, or `tech+arch` (default).

Lightweight alternative to `/gsd-map-codebase` — spawns one mapper agent instead of four parallel ones.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/scan.md
</execution_context>

<process>
Execute the scan workflow from @$HOME/.claude/get-shit-done/workflows/scan.md end-to-end.
</process>
