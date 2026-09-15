---
name: gsd-audit-uat
description: "Use when the user asks what UAT or verification items are still outstanding across phases, or wants a prioritized manual test plan. Scans every phase for pending, skipped, blocked and human_needed items and flags stale docs."
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

<objective>
Scan all phases for pending, skipped, blocked, and human_needed UAT items. Cross-reference against codebase to detect stale documentation. Produce prioritized human test plan.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/audit-uat.md
</execution_context>

<context>
Core planning files are loaded in-workflow via CLI.

**Scope:**
Glob: .planning/phases/*/*-UAT.md
Glob: .planning/phases/*/*-VERIFICATION.md
</context>

<process>
Execute the audit-uat workflow from @$HOME/.claude/get-shit-done/workflows/audit-uat.md end-to-end.
</process>
