---
name: gsd-ui-phase
description: "Use before planning a frontend phase, or when a UI contract must be locked before implementation. Orchestrates gsd-ui-researcher and gsd-ui-checker to validate, research, and verify UI-SPEC.md for the phase."
argument-hint: "[phase]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Task
  - WebFetch
  - AskUserQuestion
  - mcp__context7__*
---

<objective>
Create a UI design contract (UI-SPEC.md) for a frontend phase.
Orchestrates gsd-ui-researcher and gsd-ui-checker.
Flow: Validate → Research UI → Verify UI-SPEC → Done
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/ui-phase.md
@$HOME/.claude/get-shit-done/references/ui-brand.md
</execution_context>

<context>
Phase number: $ARGUMENTS — optional, auto-detects next unplanned phase if omitted.
</context>

<process>
Execute @$HOME/.claude/get-shit-done/workflows/ui-phase.md end-to-end.
Preserve all workflow gates.
</process>
