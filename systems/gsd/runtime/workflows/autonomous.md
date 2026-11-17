<purpose>

Drive milestone phases autonomously — all remaining phases, a range via `--from N`/`--to N`, or a single phase via `--only N`. For each incomplete phase: discuss → plan → execute using Skill() flat invocations. Pauses only for explicit user decisions (grey area acceptance, blockers, validation requests). Re-reads ROADMAP.md after each phase to catch dynamically inserted phases.

</purpose>

<required_reading>

Read all files referenced by the invoking prompt's execution_context before starting.

</required_reading>

<process>

<step name="initialize" priority="first">

## 1. Initialize

Parse `$ARGUMENTS` for `--from N`, `--to N`, `--only N`, and `--interactive` flags:

```bash
FROM_PHASE=""
if echo "$ARGUMENTS" | grep -qE '\-\-from\s+[0-9]'; then
  FROM_PHASE=$(echo "$ARGUMENTS" | grep -oE '\-\-from\s+[0-9]+\.?[0-9]*' | awk '{print $2}')
fi

TO_PHASE=""
if echo "$ARGUMENTS" | grep -qE '\-\-to\s+[0-9]'; then
  TO_PHASE=$(echo "$ARGUMENTS" | grep -oE '\-\-to\s+[0-9]+\.?[0-9]*' | awk '{print $2}')
fi

ONLY_PHASE=""
if echo "$ARGUMENTS" | grep -qE '\-\-only\s+[0-9]'; then
  ONLY_PHASE=$(echo "$ARGUMENTS" | grep -oE '\-\-only\s+[0-9]+\.?[0-9]*' | awk '{print $2}')
  FROM_PHASE="$ONLY_PHASE"
fi

INTERACTIVE=""
if echo "$ARGUMENTS" | grep -q '\-\-interactive'; then
  INTERACTIVE="true"
fi
```

When `--only` is set, also set `FROM_PHASE` to the same value so existing filter logic applies.

When `--interactive` is set, discuss runs inline with questions (not auto-answered), while plan and execute are dispatched as background agents. This keeps the main context lean — only discuss conversations accumulate — while preserving user input on all design decisions.

Bootstrap via milestone-level init:

```bash
INIT=$(gsd-sdk query init.milestone-op)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Parse JSON for: `milestone_version`, `milestone_name`, `phase_count`, `completed_phases`, `roadmap_exists`, `state_exists`, `commit_docs`.

**If `roadmap_exists` is false:** Error — "No ROADMAP.md found. Run `/gsd:new-milestone` first."
**If `state_exists` is false:** Error — "No STATE.md found. Run `/gsd:new-milestone` first."

Display startup banner:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► AUTONOMOUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Milestone: {milestone_version} — {milestone_name}
 Phases: {phase_count} total, {completed_phases} complete
```

If `ONLY_PHASE` is set, display: `Single phase mode: Phase ${ONLY_PHASE}`
Else if `FROM_PHASE` is set, display: `Starting from phase ${FROM_PHASE}`
If `TO_PHASE` is set, display: `Stopping after phase ${TO_PHASE}`
If `INTERACTIVE` is set, display: `Mode: Interactive (discuss inline, plan+execute in background)`

</step>

<step name="discover_phases">

## 2. Discover Phases

Run phase discovery:

```bash
ROADMAP=$(gsd-sdk query roadmap.analyze)
```

Parse the JSON `phases` array.

**Filter to incomplete phases:** Keep only phases where `disk_status !== "complete"` OR `roadmap_complete === false`.

**Apply `--from N` filter:** If `FROM_PHASE` was provided, additionally filter out phases where `number < FROM_PHASE` (use numeric comparison — handles decimal phases like "5.1").

**Apply `--to N` filter:** If `TO_PHASE` was provided, additionally filter out phases where `number > TO_PHASE` (use numeric comparison). This limits execution to phases up through the target phase.

**Apply `--only N` filter:** If `ONLY_PHASE` was provided, additionally filter OUT phases where `number != ONLY_PHASE`. This means the phase list will contain exactly one phase (or zero if already complete).

**If `TO_PHASE` is set and no phases remain** (all phases up to N are already completed):

```
All phases through ${TO_PHASE} are already completed. Nothing to do.
```

Exit cleanly.

**If `ONLY_PHASE` is set and no phases remain** (phase already complete):

```
Phase ${ONLY_PHASE} is already complete. Nothing to do.
```

Exit cleanly.

**Sort by `number`** in numeric ascending order.

**If no incomplete phases remain:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► AUTONOMOUS ▸ COMPLETE 🎉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 All phases complete! Nothing left to do.
```

Exit cleanly.

**Display phase plan:**

```
## Phase Plan

| # | Phase | Status |
|---|-------|--------|
| 5 | Skill Scaffolding & Phase Discovery | In Progress |
| 6 | Smart Discuss | Not Started |
| 7 | Auto-Chain Refinements | Not Started |
| 8 | Lifecycle Orchestration | Not Started |
```

**Fetch details for each phase:**

```bash
DETAIL=$(gsd-sdk query roadmap.get-phase ${PHASE_NUM})
```

Extract `phase_name`, `goal`, `success_criteria` from each. Store for use in execute_phase and transition messages.

</step>

<step name="execute_phase">

## 3. Execute Phase

For the current phase, display the progress banner:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► AUTONOMOUS ▸ Phase {N}/{T}: {Name} [████░░░░] {P}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Where N = current phase number (from the ROADMAP, e.g., 63), T = total milestone phases (from `phase_count` parsed in initialize step, e.g., 67). **Important:** T must be `phase_count` (the total number of phases in this milestone), NOT the count of remaining/incomplete phases. When phases are numbered 61-67, T=7 and the banner should read `Phase 63/7` (phase 63, 7 total in milestone), not `Phase 63/3` (which would confuse 3 remaining with 3 total). P = percentage of all milestone phases completed so far. Calculate P as: (number of phases with `disk_status` "complete" from the latest `roadmap analyze` / T × 100). Use █ for filled and ░ for empty segments in the progress bar (8 characters wide).

**Alternative display when phase numbers exceed total** (e.g., multi-milestone projects where phases are numbered globally): If N > T (phase number exceeds milestone phase count), use the format `Phase {N} ({position}/{T})` where `position` is the 1-based index of this phase among incomplete phases being processed. This prevents confusing displays like "Phase 63/5".

**3a. Smart Discuss**

Check if CONTEXT.md already exists for this phase:

```bash
PHASE_STATE=$(gsd-sdk query init.phase-op ${PHASE_NUM})
```

Parse `has_context` from JSON.

**If has_context is true:** Skip discuss — context already gathered. Display:

```
Phase ${PHASE_NUM}: Context exists — skipping discuss.
```

Proceed to 3b.

**If has_context is false:** Check if discuss is disabled via settings:

```bash
SKIP_DISCUSS=$(gsd-sdk query config-get workflow.skip_discuss 2>/dev/null || echo "false")
```

**If SKIP_DISCUSS is `true`:** Skip discuss entirely — the ROADMAP phase description is the spec. Display:

```
Phase ${PHASE_NUM}: Discuss skipped (workflow.skip_discuss=true) — using ROADMAP phase goal as spec.
```

Write a minimal CONTEXT.md so downstream plan-phase has valid input. Get phase details:

```bash
DETAIL=$(gsd-sdk query roadmap.get-phase ${PHASE_NUM})
```

Extract `goal` and `requirements` from JSON. Write `${phase_dir}/${padded_phase}-CONTEXT.md` with:

```markdown
# Phase {PHASE_NUM}: {Phase Name} - Context

**Gathered:** {date}
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

{goal from ROADMAP phase description}

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
