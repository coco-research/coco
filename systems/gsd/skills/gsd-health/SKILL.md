---
name: gsd-health
description: "Use when .planning/ looks inconsistent, files are missing, or state seems wrong. Validates .planning/ integrity, reports missing files, bad config, and orphaned plans, and --repair fixes what it finds."
argument-hint: "[--repair]"
allowed-tools:
  - Read
  - Bash
  - Write
  - AskUserQuestion
---

<objective>
Validate `.planning/` directory integrity and report actionable issues. Checks for missing files, invalid configurations, inconsistent state, and orphaned plans.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/health.md
</execution_context>

<process>
Execute the health workflow from @$HOME/.claude/get-shit-done/workflows/health.md end-to-end.
Parse --repair flag from arguments and pass to workflow.
</process>
