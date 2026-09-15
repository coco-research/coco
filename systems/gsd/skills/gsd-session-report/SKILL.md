---
name: gsd-session-report
description: "Use when a session ends and the user wants a summary of what was done and what it cost. Writes a shareable SESSION_REPORT.md with outcomes, work performed and estimated resource usage."
allowed-tools:
  - Read
  - Bash
  - Write
---

<objective>
Generate a structured SESSION_REPORT.md document capturing session outcomes, work performed, and estimated resource usage. Provides a shareable artifact for post-session review.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/session-report.md
</execution_context>

<process>
Execute the session-report workflow from @$HOME/.claude/get-shit-done/workflows/session-report.md end-to-end.
</process>
