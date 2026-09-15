---
name: gsd-remove-workspace
description: "Use when a finished GSD workspace and its worktrees should be deleted. Confirms first, runs git worktree remove for each member repo, and refuses if any repo has uncommitted changes."
argument-hint: "<workspace-name>"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

<context>
**Arguments:**
- `<workspace-name>` (required) — Name of the workspace to remove
</context>

<objective>
Remove a workspace directory after confirmation. For worktree strategy, runs `git worktree remove` for each member repo first. Refuses if any repo has uncommitted changes.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/remove-workspace.md
@$HOME/.claude/get-shit-done/references/ui-brand.md
</execution_context>

<process>
Execute the remove-workspace workflow from @$HOME/.claude/get-shit-done/workflows/remove-workspace.md end-to-end.
</process>
