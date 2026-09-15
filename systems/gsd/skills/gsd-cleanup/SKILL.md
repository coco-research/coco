---
name: gsd-cleanup
description: "Use when .planning/phases/ has accumulated directories from completed milestones. Shows a dry-run of what moves to .planning/milestones/v{X.Y}-phases/ and archives only after confirmation."
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
Archive phase directories from completed milestones into `.planning/milestones/v{X.Y}-phases/`.

Use when `.planning/phases/` has accumulated directories from past milestones.
</objective>

<process>
Follow the cleanup workflow.
Identify completed milestones, show a dry-run summary, and archive on confirmation.
</process>
