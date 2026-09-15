---
name: gsd-help
description: "Use when the user asks what GSD commands exist or how to use GSD. Outputs the complete GSD command reference verbatim, with no project analysis, status, or next-step suggestions."
allowed-tools:
  - Read
---

<objective>
Display the complete GSD command reference.

Output ONLY the reference content below. Do NOT add:
- Project-specific analysis
- Git status or file context
- Next-step suggestions
- Any commentary beyond the reference
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/help.md
</execution_context>

<process>
Output the complete GSD command reference from @$HOME/.claude/get-shit-done/workflows/help.md.
Display the reference content directly — no additions or modifications.
</process>
