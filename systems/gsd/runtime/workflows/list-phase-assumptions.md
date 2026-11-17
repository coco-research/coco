<purpose>
Surface Claude's assumptions about a phase before planning, enabling users to correct misconceptions early.

Key difference from discuss-phase: This is ANALYSIS of what Claude thinks, not INTAKE of what user knows. No file output - purely conversational to prompt discussion.
</purpose>

<process>

<step name="validate_phase" priority="first">
Phase number: $ARGUMENTS (required)

**If argument missing:**

```
Error: Phase number required.

Usage: /gsd-list-phase-assumptions [phase-number]
