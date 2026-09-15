---
name: gsd-ship
description: "Use after /gsd-verify-work passes, when the work should become a PR. Pushes the branch, creates the PR with an auto-generated body, optionally triggers review, and tracks the merge, closing the plan-execute-verify-ship loop."
argument-hint: "[phase number or milestone, e.g., '4' or 'v1.0']"
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
  - Write
  - AskUserQuestion
---

<objective>
Bridge local completion → merged PR. After /gsd-verify-work passes, ship the work: push branch, create PR with auto-generated body, optionally trigger review, and track the merge.

Closes the plan → execute → verify → ship loop.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/ship.md
</execution_context>

Execute the ship workflow from @$HOME/.claude/get-shit-done/workflows/ship.md end-to-end.
