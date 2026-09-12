---
name: gsd-secure-phase
description: "Use to re-verify the threat mitigations of a phase that already shipped, or when the user asks to audit SECURITY.md. Audits an existing SECURITY.md, runs from a PLAN.md threat model, or exits if the phase never ran."
argument-hint: "[phase number]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
---

<objective>
Verify threat mitigations for a completed phase. Three states:
- (A) SECURITY.md exists — audit and verify mitigations
- (B) No SECURITY.md, PLAN.md with threat model exists — run from artifacts
- (C) Phase not executed — exit with guidance

Output: updated SECURITY.md.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/secure-phase.md
</execution_context>

<context>
Phase: $ARGUMENTS — optional, defaults to last completed phase.
</context>

<process>
Execute @$HOME/.claude/get-shit-done/workflows/secure-phase.md.
Preserve all workflow gates.
</process>
