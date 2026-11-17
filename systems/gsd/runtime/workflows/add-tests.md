<purpose>
Generate unit and E2E tests for a completed phase based on its SUMMARY.md, CONTEXT.md, and implementation. Classifies each changed file into TDD (unit), E2E (browser), or Skip categories, presents a test plan for user approval, then generates tests following RED-GREEN conventions.

Users currently hand-craft `/gsd:quick` prompts for test generation after each phase. This workflow standardizes the process with proper classification, quality gates, and gap reporting.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="parse_arguments">
Parse `$ARGUMENTS` for:
- Phase number (integer, decimal, or letter-suffix) → store as `$PHASE_ARG`
- Remaining text after phase number → store as `$EXTRA_INSTRUCTIONS` (optional)

Example: `/gsd:add-tests 12 focus on edge cases` → `$PHASE_ARG=12`, `$EXTRA_INSTRUCTIONS="focus on edge cases"`

If no phase argument provided:

```
ERROR: Phase number required
Usage: /gsd:add-tests <phase> [additional instructions]
Example: /gsd:add-tests 12
Example: /gsd:add-tests 12 focus on edge cases in the pricing module
```

Exit.
</step>

