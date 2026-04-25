---
name: gsd-list-workspaces
description: "List active GSD workspaces and their status"
allowed-tools:
  - Bash
  - Read
---

<objective>
Scan `~/gsd-workspaces/` for workspace directories containing `WORKSPACE.md` manifests. Display a summary table with name, path, repo count, strategy, and GSD project status.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/list-workspaces.md
@$HOME/.claude/get-shit-done/references/ui-brand.md
</execution_context>

<process>
Execute the list-workspaces workflow from @$HOME/.claude/get-shit-done/workflows/list-workspaces.md end-to-end.
</process>
