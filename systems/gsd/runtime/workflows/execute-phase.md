<purpose>
Execute all plans in a phase using wave-based parallel execution. Orchestrator stays lean — delegates plan execution to subagents.
</purpose>

<core_principle>
Orchestrator coordinates, not executes. Each subagent loads the full execute-plan context. Orchestrator: discover plans → analyze deps → group waves → spawn agents → handle checkpoints → collect results.
</core_principle>

<runtime_compatibility>
**Subagent spawning is runtime-specific:**
- **Claude Code:** Uses `Agent(subagent_type="gsd-executor", ...)` — blocks until complete, returns result
- **Copilot:** Subagent spawning does not reliably return completion signals. **Default to
  sequential inline execution**: read and follow execute-plan.md directly for each plan
  instead of spawning parallel agents. Only attempt parallel spawning if the user
  explicitly requests it — and in that case, rely on the spot-check fallback in step 3
  to detect completion.
- **Other runtimes:** If `Agent`/`agent` tool is unavailable, use sequential inline execution as the
  fallback. Check for tool availability at runtime rather than assuming based on runtime name.

**Fallback rule:** If a spawned agent completes its work (commits visible, SUMMARY.md exists) but
the orchestrator never receives the completion signal, treat it as successful based on spot-checks
and continue to the next wave/plan. Never block indefinitely waiting for a signal — always verify
via filesystem and git state.
</runtime_compatibility>

<required_reading>
Read STATE.md before any operation to load project context.
@~/.claude/get-shit-done/references/agent-contracts.md
@~/.claude/get-shit-done/references/context-budget.md
@~/.claude/get-shit-done/references/gates.md
</required_reading>

<available_agent_types>
These are the valid GSD subagent types registered in .claude/agents/ (or equivalent for your runtime).
Always use the exact name from this list — do not fall back to 'general-purpose' or other built-in types:

- gsd-executor — Executes plan tasks, commits, creates SUMMARY.md
- gsd-verifier — Verifies phase completion, checks quality gates
- gsd-planner — Creates detailed plans from phase scope
- gsd-phase-researcher — Researches technical approaches for a phase
- gsd-plan-checker — Reviews plan quality before execution
- gsd-debugger — Diagnoses and fixes issues
- gsd-codebase-mapper — Maps project structure and dependencies
- gsd-integration-checker — Checks cross-phase integration
- gsd-nyquist-auditor — Validates verification coverage
- gsd-ui-researcher — Researches UI/UX approaches
- gsd-ui-checker — Reviews UI implementation quality
- gsd-ui-auditor — Audits UI against design requirements
</available_agent_types>

<process>

<step name="parse_args" priority="first">
Parse `$ARGUMENTS` before loading any context:

- First positional token → `PHASE_ARG`
- Optional `--wave N` → `WAVE_FILTER`
- Optional `--gaps-only` keeps its current meaning
- Optional `--cross-ai` → `CROSS_AI_FORCE=true` (force all plans through cross-AI execution)
- Optional `--no-cross-ai` → `CROSS_AI_DISABLED=true` (disable cross-AI for this run, overrides config and frontmatter)

If `--wave` is absent, preserve the current behavior of executing all incomplete waves in the phase.
</step>

<step name="initialize" priority="first">
Load all context in one call:

```bash
INIT=$(gsd-sdk query init.execute-phase "${PHASE_ARG}")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS=$(gsd-sdk query agent-skills gsd-executor)
```

Parse JSON for: `executor_model`, `verifier_model`, `commit_docs`, `parallelization`, `branching_strategy`, `branch_name`, `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `plans`, `incomplete_plans`, `plan_count`, `incomplete_count`, `state_exists`, `roadmap_exists`, `phase_req_ids`, `response_language`.

**Model resolution:** If `executor_model` is `"inherit"`, omit the `model=` parameter from all `Agent()` calls — do NOT pass `model="inherit"` to Agent. Omitting the `model=` parameter causes Claude Code to inherit the current orchestrator model automatically. Only set `model=` when `executor_model` is an explicit model name (e.g., `"claude-sonnet-4-6"`, `"claude-opus-4-7"`).

**If `response_language` is set:** Include `response_language: {value}` in all spawned subagent prompts so any user-facing output stays in the configured language.

Read runtime/worktree config and fail closed before any executor dispatch:

```bash
RUNTIME=$(gsd-sdk query config-get runtime --default claude 2>/dev/null || echo "claude")
USE_WORKTREES=$(gsd-sdk query config-get workflow.use_worktrees 2>/dev/null || echo "true")
EXECUTOR_STALL_INTERVAL_MINUTES=$(gsd-sdk query config-get executor.stall_detect_interval_minutes 2>/dev/null || echo "5")
EXECUTOR_STALL_THRESHOLD_MINUTES=$(gsd-sdk query config-get executor.stall_threshold_minutes 2>/dev/null || echo "10")

if [ "$RUNTIME" = "codex" ] && [ "$USE_WORKTREES" != "false" ]; then
  echo "FATAL: Codex execute-phase worktree isolation is unsupported. Set workflow.use_worktrees=false or use a runtime with Agent isolation=\"worktree\" support." >&2
  exit 1
fi
# Sweep orphaned locked worktrees from prior crashed sessions before spawning executors (#3707).
[ "$USE_WORKTREES" != "false" ] && gsd-sdk query worktree.reap-orphans 2>/dev/null || true
```
Codex maps subagents to `spawn_agent`, which has no direct Codex mapping for Claude Code's `isolation="worktree"` parameter. Failing closed prevents main-checkout edits while the workflow believes agents are isolated.

If the project uses git submodules, worktree isolation is unsafe **only when a plan touches a submodule path** — the executor commit protocol cannot correctly handle submodule commits inside isolated worktrees. The previous behavior unconditionally disabled worktree isolation whenever `.gitmodules` existed, which penalised every plan in a submodule project even when the plan was nowhere near a submodule. Compute submodule paths once and intersect them per-plan with the plan's declared `files_modified` frontmatter.

```bash
# Parse submodule paths from .gitmodules once (empty if no .gitmodules).
# SUBMODULE_PATHS is a newline-separated list of repo-relative paths.
if [ -f .gitmodules ]; then
  SUBMODULE_PATHS=$(git config --file .gitmodules --get-regexp '^submodule\..*\.path$' 2>/dev/null | awk '{print $2}')
else
  SUBMODULE_PATHS=""
fi
```

`SUBMODULE_PATHS` is exported to the `execute_waves` step, where the per-plan decision actually happens (see "Per-plan worktree decision" sub-step inside `execute_waves`). The decision is per-plan because different plans in the same wave can touch different files — only plans whose paths intersect a submodule must drop worktree isolation; plans nowhere near a submodule keep parallel isolation.

When `USE_WORKTREES` (project-level) is `false`, all executor agents run without `isolation="worktree"` — they execute sequentially on the main working tree instead of in parallel worktrees. The per-plan decision below has no effect when worktrees are project-disabled.

Read context window size for adaptive prompt enrichment:

```bash
CONTEXT_WINDOW=$(gsd-sdk query config-get context_window 2>/dev/null || echo "200000")
```

When `CONTEXT_WINDOW >= 500000` (1M-class models), subagent prompts include richer context:
- Executor agents receive prior wave SUMMARY.md files and the phase CONTEXT.md/RESEARCH.md
- Verifier agents receive all PLAN.md, SUMMARY.md, CONTEXT.md files plus REQUIREMENTS.md
- This enables cross-phase awareness and history-aware verification

When `CONTEXT_WINDOW < 200000` (sub-200K models), subagent prompts are thinned to reduce static overhead:
- Executor agents omit extended deviation rule examples and checkpoint examples from inline prompt — load on-demand via @~/.claude/get-shit-done/references/executor-examples.md
- Planner agents omit extended anti-pattern lists and specificity examples from inline prompt — load on-demand via @~/.claude/get-shit-done/references/planner-antipatterns.md
- Core rules and decision logic remain inline; only verbose examples and edge-case lists are extracted
- This reduces executor static overhead by ~40% while preserving behavioral correctness

**If `phase_found` is false:** Error — phase directory not found.
**If `plan_count` is 0:** Error — no plans found in phase.
**If `state_exists` is false but `.planning/` exists:** Offer reconstruct or continue.

When `parallelization` is false, plans within a wave execute sequentially.

**Runtime detection for Copilot:**
Check if the current runtime is Copilot by testing for the `@gsd-executor` agent pattern
or absence of the `Agent()` subagent API. If running under Copilot, force sequential inline
execution regardless of the `parallelization` setting — Copilot's subagent completion
signals are unreliable (see `<runtime_compatibility>`). Set `COPILOT_SEQUENTIAL=true`
internally and skip the `execute_waves` step in favor of `check_interactive_mode`'s
inline path for each plan.

**REQUIRED — Sync chain flag with intent.** If user invoked manually (no `--auto`), clear the ephemeral chain flag from any previous interrupted `--auto` chain. This prevents stale `_auto_chain_active: true` from causing unwanted auto-advance. This does NOT touch `workflow.auto_advance` (the user's persistent settings preference). You MUST execute this bash block before any config reads:
```bash
# REQUIRED: prevents stale auto-chain from previous --auto runs
if [[ ! "$ARGUMENTS" =~ --auto ]]; then
  gsd-sdk query config-set workflow._auto_chain_active false || true
fi
```

Resolve `MVP_MODE` once via the centralized `phase.mvp-mode` query verb (precedence chain: CLI flag → ROADMAP `**Mode:** mvp` → `workflow.mvp_mode` config → false):
```bash
MVP_FLAG_ARG=""
if [[ "$ARGUMENTS" =~ (^|[[:space:]])--mvp([[:space:]]|$) ]]; then MVP_FLAG_ARG="--cli-flag"; fi
MVP_MODE=$(gsd-sdk query phase.mvp-mode "${PHASE_NUMBER}" $MVP_FLAG_ARG --pick active)
TDD_MODE=$(gsd-sdk query config-get workflow.tdd_mode 2>/dev/null || echo "false")
```

<step name="safe_resume_gate">
Before trusting `STATE.md` or dispatching any executor, derive `CURRENT_PLAN_ID`
from the active incomplete plan in `INIT`, then search recent history:
```bash
CURRENT_PLAN_ID="{phase_number}-{plan_padded}"
SUMMARY_PATH="{phase_dir}/{plan_padded}-SUMMARY.md"
PLAN_COMMITS=$(git log --oneline --grep="${CURRENT_PLAN_ID}" -30)
```
If production commits exist and `SUMMARY.md is missing`, stop before spawning a
new executor; continuing risks duplicate work and stale `STATE.md`/ROADMAP progress.
Offer these recovery options:
- `close out manually` — inspect commits, write SUMMARY.md, then update STATE/ROADMAP.
- `re-execute from scratch` — revert or supersede partial commits before dispatch.
- `mark-and-skip` — record the anomaly and move on only with explicit confirmation.
</step>

**MVP+TDD gate.** Task-scoped enforcement runs inside plan execution (immediately before each implementation step), where `TASK_FILE`, `PLAN_ID`, and `TASK_ID` are defined. Keep the same predicate and RED-commit contract:
```bash
if [ "$MVP_MODE" = "true" ] && [ "$TDD_MODE" = "true" ]; then
  IS_BEHAVIOR_ADDING=$(gsd-sdk query task.is-behavior-adding "$TASK_FILE" --pick is_behavior_adding)
  if [ "$IS_BEHAVIOR_ADDING" = "true" ]; then
    RED_COMMIT=$(git log --oneline --grep="^test(${PHASE_NUMBER}-${PLAN_ID}):" -- "**/*.test.*" "**/*.spec.*" "tests/" | head -1)
    if [ -z "$RED_COMMIT" ]; then
      gsd-sdk query state.update last_gate_trip "${PLAN_ID}/${TASK_ID}" || true
      echo "MVP+TDD GATE TRIPPED: missing RED commit for ${PLAN_ID}/${TASK_ID}"
      exit 1
    fi
  fi
fi
```
Pure doc-only / config-only / test-only tasks return `is_behavior_adding=false` and are exempt. See `execute-mvp-tdd.md` for the halt report format.
</step>

<step name="check_blocking_antipatterns" priority="first">
**MANDATORY — Check for blocking anti-patterns before any other work.**

Look for a `.continue-here.md` in the current phase directory:

```bash
ls ${phase_dir}/.continue-here.md 2>/dev/null || true
```

If `.continue-here.md` exists, parse its "Critical Anti-Patterns" table for rows with `severity` = `blocking`.

**If one or more `blocking` anti-patterns are found:**

This step cannot be skipped. Before proceeding to `check_interactive_mode` or any other step, the agent must demonstrate understanding of each blocking anti-pattern by answering all three questions for each one:

1. **What is this anti-pattern?** — Describe it in your own words, not by quoting the handoff.
2. **How did it manifest?** — Explain the specific failure that caused it to be recorded.
3. **What structural mechanism (not acknowledgment) prevents it?** — Name the concrete step, checklist item, or enforcement mechanism that stops recurrence.

Write these answers inline before continuing. If a blocking anti-pattern cannot be answered from the context in `.continue-here.md`, stop and ask the user for clarification.

**If no `.continue-here.md` exists, or no `blocking` rows are found:** Proceed directly to `check_interactive_mode`.
</step>

<step name="check_interactive_mode">
**Parse `--interactive` flag from $ARGUMENTS.**

**If `--interactive` flag present:** Switch to interactive execution mode.

Interactive mode executes plans sequentially **inline** (no subagent spawning) with user
checkpoints between tasks. The user can review, modify, or redirect work at any point.

**Interactive execution flow:**

1. Load plan inventory as normal (discover_and_group_plans)
2. For each plan (sequentially, ignoring wave grouping):

   a. **Present the plan to the user:**
      ```
      ## Plan {plan_id}: {plan_name}

      Objective: {from plan file}
      Tasks: {task_count}

      Options:
      - Execute (proceed with all tasks)
      - Review first (show task breakdown before starting)
      - Skip (move to next plan)
      - Stop (end execution, save progress)
      ```

   b. **If "Review first":** Read and display the full plan file. Ask again: Execute, Modify, Skip.

   c. **If "Execute":** Read and follow `~/.claude/get-shit-done/workflows/execute-plan.md` **inline**
      (do NOT spawn a subagent). Execute tasks one at a time.

   d. **After each task:** Pause briefly. If the user intervenes (types anything), stop and address
      their feedback before continuing. Otherwise proceed to next task.

   e. **After plan complete:** Show results, commit, create SUMMARY.md, then present next plan.

3. After all plans: proceed to verification (same as normal mode).

**Benefits of interactive mode:**
- No subagent overhead — dramatically lower token usage
- User catches mistakes early — saves costly verification cycles
- Maintains GSD's planning/tracking structure
- Best for: small phases, bug fixes, verification gaps, learning GSD

**Skip to handle_branching step** (interactive plans execute inline after grouping).
</step>

<step name="handle_branching">
Check `branching_strategy` from init:

**"none":** Skip, continue on current branch.

**"phase" or "milestone":** Use pre-computed `branch_name` from init.

Fork the new phase branch off `origin/HEAD` (the project's default branch), not the current HEAD — otherwise consecutive phases compound and stay unpushed (#2916). If `$BRANCH_NAME` already exists locally, reuse it as-is.

```bash
DEFAULT_BRANCH=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}

if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  git switch "$BRANCH_NAME" || { echo "ERROR: Could not switch to existing branch '$BRANCH_NAME'." >&2; exit 1; }
else
  if ! git fetch --quiet origin "$DEFAULT_BRANCH"; then  # #2916
    git show-ref --verify --quiet "refs/remotes/origin/$DEFAULT_BRANCH" \
      || { echo "ERROR: fetch origin/$DEFAULT_BRANCH failed and no local copy exists. Refusing to create '$BRANCH_NAME' off current HEAD (#2916)." >&2; exit 1; }
    echo "WARNING: fetch origin/$DEFAULT_BRANCH failed; using local copy as base." >&2
  fi
  if [ -n "$(git status --porcelain)" ]; then
    echo "WARNING: Uncommitted changes will be carried onto '$BRANCH_NAME' (branched off origin/$DEFAULT_BRANCH, not previous HEAD)."
  else
    git switch --quiet "$DEFAULT_BRANCH" 2>/dev/null && git merge --ff-only --quiet "origin/$DEFAULT_BRANCH" 2>/dev/null || true
  fi
  # Pinned base + fail-fast: on success HEAD is exactly at origin/$DEFAULT_BRANCH,
  # so a post-creation merge-base or "ahead-of" guard would be unreachable. The
  # explicit base argument here is the single source of correctness for #2916.
  git checkout -b "$BRANCH_NAME" "origin/$DEFAULT_BRANCH" \
    || { echo "ERROR: Could not create '$BRANCH_NAME' from origin/$DEFAULT_BRANCH (#2916)." >&2; exit 1; }
fi
```

All subsequent commits go to this branch. User handles merging.
</step>

<step name="validate_phase">
From init JSON: `phase_dir`, `plan_count`, `incomplete_count`.

Report: "Found {plan_count} plans in {phase_dir} ({incomplete_count} incomplete)"
