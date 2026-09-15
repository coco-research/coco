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

<process>
Execute the health workflow end-to-end.
Parse --repair flag from arguments and pass to workflow.
</process>
