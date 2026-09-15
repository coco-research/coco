---
name: gsd-undo
description: "Use when the user wants to roll back GSD commits: the last N, a whole phase, or one plan. Reverts through the phase manifest with dependency checks and a confirmation gate before anything is undone."
argument-hint: "--last N | --phase NN | --plan NN-MM"
allowed-tools:
  - Read
  - Bash
  - Glob
  - Grep
  - AskUserQuestion
---


<objective>
Safe git revert — roll back GSD phase or plan commits using the phase manifest, with dependency checks and a confirmation gate before execution.

Three modes:
- **--last N**: Show recent GSD commits for interactive selection
- **--phase NN**: Revert all commits for a phase (manifest + git log fallback)
- **--plan NN-MM**: Revert all commits for a specific plan
</objective>

<context>
$ARGUMENTS
</context>

<process>
Execute the undo workflow end-to-end.
</process>
