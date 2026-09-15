---
name: gsd-ui-review
description: "Use when the user asks for a visual or UI quality review of frontend code that already shipped, or passes a phase number. Produces {phase_num}-UI-REVIEW.md with a graded 1-4 assessment across six pillars."
argument-hint: "[phase]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
---

<objective>
Conduct a retroactive 6-pillar visual audit. Produces UI-REVIEW.md with
graded assessment (1-4 per pillar). Works on any project.
Output: {phase_num}-UI-REVIEW.md
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/ui-review.md
@$HOME/.claude/get-shit-done/references/ui-brand.md
</execution_context>

<context>
Phase: $ARGUMENTS — optional, defaults to last completed phase.
</context>

<process>
Execute @$HOME/.claude/get-shit-done/workflows/ui-review.md end-to-end.
Preserve all workflow gates.
</process>
