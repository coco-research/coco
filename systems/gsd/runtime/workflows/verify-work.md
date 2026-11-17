<purpose>
Validate built features through conversational testing with persistent state. Creates UAT.md that tracks test progress, survives /clear, and feeds gaps into /gsd:plan-phase --gaps.

User tests, Claude records. One test at a time. Plain text responses.
</purpose>

<available_agent_types>
Valid GSD subagent types (use exact names — do not fall back to 'general-purpose'):
- gsd-planner — Creates detailed plans from phase scope
- gsd-plan-checker — Reviews plan quality before execution
</available_agent_types>

<philosophy>
**Show expected, ask if reality matches.**

Claude presents what SHOULD happen. User confirms or describes what's different.
- "yes" / "y" / "next" / empty → pass
- Anything else → logged as issue, severity inferred

No Pass/Fail buttons. No severity questions. Just: "Here's what should happen. Does it?"
</philosophy>

<template>
@~/.claude/get-shit-done/templates/UAT.md
</template>

<process>

<step name="initialize" priority="first">
If $ARGUMENTS contains a phase number, load context:

```bash
GSD_WS=""
echo "$ARGUMENTS" | grep -qE -- '--ws[[:space:]]+[^[:space:]]+' && GSD_WS=$(echo "$ARGUMENTS" | grep -oE -- '--ws[[:space:]]+[^[:space:]]+')
PHASE_ARG=$(echo "$ARGUMENTS" | sed -E 's/--ws[[:space:]]+[^[:space:]]+//g' | xargs)

INIT=$(gsd-sdk query init.verify-work "${PHASE_ARG}" ${GSD_WS})
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_PLANNER=$(gsd-sdk query agent-skills gsd-planner)
AGENT_SKILLS_CHECKER=$(gsd-sdk query agent-skills gsd-plan-checker)
```

Parse JSON for: `planner_model`, `checker_model`, `commit_docs`, `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `has_verification`, `uat_path`.

```bash
# MVP mode detection via the centralized phase.mvp-mode resolver.
# verify-work has no --mvp CLI flag (mode is inherited from the planned phase),
# so we omit --cli-flag — the verb falls through roadmap → config → false.
MVP_MODE=$(gsd-sdk query phase.mvp-mode "${phase_number}" ${GSD_WS} --pick active)
```
</step>

<step name="check_active_session">
**First: Check for active UAT sessions**

```bash
(find .planning/phases -name "*-UAT.md" -type f 2>/dev/null || true)
```

**If active sessions exist AND no $ARGUMENTS provided:**

Read each file's frontmatter (status, phase) and Current Test section.

Display inline:

```
## Active UAT Sessions
