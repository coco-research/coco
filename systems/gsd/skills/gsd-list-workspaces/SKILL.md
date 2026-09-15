---
name: gsd-list-workspaces
description: "Use when the user asks which GSD workspaces exist, or where their isolated work lives. Scans the workspaces root for WORKSPACE.md manifests and prints name, path, repo count, strategy and project status."
allowed-tools:
  - Bash
  - Read
---

<objective>
Scan `~/gsd-workspaces/` for workspace directories containing `WORKSPACE.md` manifests. Display a summary table with name, path, repo count, strategy, and GSD project status.
</objective>

<process>
Execute the list-workspaces workflow end-to-end.
</process>
