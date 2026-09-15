# Autonomous Milestone Execution Workflow

> Orchestrates end-to-end milestone execution: discuss → plan → execute for each remaining phase,
> then audit → complete → cleanup. Pauses only for user decisions on grey areas, blockers, or validation failures.

## Prerequisites

- Active milestone with `.planning/ROADMAP.md` and `.planning/STATE.md`
- At least one incomplete phase in ROADMAP.md

## Flags

| Flag | Effect |
|------|--------|
| `--from N` | Start from phase N instead of first incomplete |
| `--to N` | Stop after phase N completes (halt) |
| `--only N` | Execute only phase N (single-phase mode) |
| `--interactive` | Run discuss inline with questions; dispatch plan→execute as background agents |

## Step 0: Initialize & Discover Phases

```bash
INIT=$(node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" init milestone-op)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
```

Extract from init JSON: `milestone_version`, `state_path`, `roadmap_path`.

Analyze roadmap to find incomplete phases:
```bash
PHASES=$(node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" roadmap analyze --json)
```

Apply flag filters:
- If `--only N`: filter to single phase N
- If `--from N`: skip phases before N
- If `--to N`: stop list at phase N

If no incomplete phases remain: report "All phases complete" and jump to Step 5 (Audit).

Present phase list to user:
```
🚀 Autonomous Execution — Milestone v{version}
Phases to execute: {count}
  Phase {N}: {name} [{status}]
  Phase {N+1}: {name} [{status}]
  ...
Flags: {active flags or "none"}

Proceed? (y/n)
```

Wait for confirmation.

## Step 1: Per-Phase Loop

For each phase in the filtered list:

### 1a. Discuss Phase

Check if `{phase_num}-CONTEXT.md` already exists:
- If exists AND not stale: skip discuss, proceed to 1b
- If missing or `--research` flag: run discuss

**Interactive mode (`--interactive`):**
Run `/gsd-discuss-phase {phase_num}` inline. User answers questions directly.

**Auto mode (default):**
Run `/gsd-discuss-phase {phase_num} --auto`. Claude picks recommended defaults for grey areas.

After discuss completes, verify `{phase_num}-CONTEXT.md` was created.

### 1b. Plan Phase

Check if `{phase_num}-PLAN.md` files already exist and are valid:
- If exists AND verified: skip planning, proceed to 1c
- If missing or unverified: run planning

Run `/gsd-plan-phase {phase_num}`.

The planner creates PLAN.md files and runs verification loop internally.
Wait for planner to report success or max iterations reached.

If planning fails after max iterations:
```
⚠ Phase {N} planning failed after {max} verification attempts.
Options:
  1. Review and fix manually, then retry
  2. Skip this phase and continue
  3. Abort autonomous execution
```
Wait for user decision. If skip: mark phase as deferred in STATE.md, continue to next phase. If abort: exit.

### 1c. Execute Phase

Run `/gsd-execute-phase {phase_num}`.

Execution uses wave-based parallelization internally. Each subagent gets fresh context.

After execution completes, verify SUMMARY.md was created.

### 1d. Verify Work

Run `/gsd-verify-work {phase_num}`.

If verification passes: update STATE.md, proceed to next phase.

If verification finds issues:
```
⚠ Phase {N} verification found {count} issue(s).
Fix plans created: {fix_plan_count}

Options:
  1. Execute fix plans now (/gsd-execute-phase {phase_num} --gaps-only)
  2. Defer fixes, continue to next phase
  3. Abort autonomous execution
```

If user chooses option 1: run `/gsd-execute-phase {phase_num} --gaps-only`, then re-verify.
If user chooses option 2: log deferred gaps, continue.
If user chooses option 3: exit.

### 1e. Progress Update

After each phase completes (or is skipped/deferred):
```bash
node "$HOME/.claude/get-shit-done/bin/gsd-tools.cjs" state update-phase {phase_num} completed
```

Display progress:
```
✅ Phase {N}/{total}: {name} — Complete
   Remaining: {remaining_count} phase(s)
```

If `--to N` and current phase == N: halt loop, proceed to Step 5.

## Step 2: Check for Deferred Gaps

After all phases processed, check for any deferred gap closures:
```bash
DEFERRED=$(grep -l "deferred" .planning/phases/*/*-VERIFICATION.md 2>/dev/null | wc -l)
```

If deferred gaps exist:
```
⚠ {count} phase(s) have deferred verification gaps.
Options:
  1. Fix all deferred gaps now
  2. Accept as tech debt, proceed to audit
  3. Abort
```

## Step 3: Milestone Audit

Run `/gsd-audit-milestone`.

Audit checks:
- Requirements coverage across all phases
- Cross-phase integration wiring
- End-to-end flow completeness

If audit status is `passed`: proceed to Step 4.

If audit status is `gaps_found`:
```
⚠ Milestone audit found {count} gap(s).
Gap closure phases needed: {gap_phase_count}

Options:
  1. Create and execute gap closure phases (/gsd-plan-milestone-gaps)
  2. Accept gaps as tech debt, proceed to completion
  3. Abort
```

If option 1: run `/gsd-plan-milestone-gaps`, then execute new phases through Step 1 loop, then re-audit.

## Step 4: Complete Milestone

Run `/gsd-complete-milestone {version}`.

This archives the milestone, updates PROJECT.md, creates git tag.

## Step 5: Cleanup

Run `/gsd-cleanup`.

Archives completed phase directories into `.planning/milestones/v{version}-phases/`.

## Step 6: Final Report

```
🎉 Autonomous Execution Complete — Milestone v{version}

Phases executed: {completed_count}
Phases deferred: {deferred_count}
Gaps closed: {gaps_closed_count}
Tech debt accepted: {tech_debt_count}

Milestone archived: .planning/milestones/v{version}-*
Git tag: v{version}

Next steps:
  • /gsd-new-milestone — start next milestone
  • /gsd-ship — create PR if not yet shipped
  • Review tech debt items in PROJECT.md
```

## Error Handling

### Tool Failure
If any `/gsd-*` command fails with non-zero exit:
1. Display error output
2. Offer: retry / skip / abort
3. Never silently continue past a failure

### Context Overflow
If orchestrator context approaches limits:
1. Compress handoff documents
2. Delegate more work to subagents
3. Reduce inline output verbosity

### User Interrupt
If user sends message during autonomous execution:
1. Pause at next safe checkpoint (between phases)
2. Address user request
3. Resume or adjust plan based on input

## State Persistence

All state changes go through `gsd-tools.cjs state` commands.
STATE.md is updated after every phase transition.
If execution is interrupted, `/gsd-progress` or `/gsd-next` can resume from last checkpoint.
