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

**Update STATE.md for phase start:**
```bash
gsd-sdk query state.begin-phase --phase "${PHASE_NUMBER}" --name "${PHASE_NAME}" --plans "${PLAN_COUNT}"
```
This updates Status, Last Activity, Current focus, Current Position, and plan counts in STATE.md so frontmatter and body text reflect the active phase immediately.
</step>

<step name="discover_and_group_plans">
Load plan inventory with wave grouping in one call:

```bash
PLAN_INDEX=$(gsd-sdk query phase-plan-index "${PHASE_NUMBER}")
```

Parse JSON for: `phase`, `plans[]` (each with `id`, `wave`, `autonomous`, `objective`, `files_modified`, `task_count`, `has_summary`), `waves` (map of wave number → plan IDs), `incomplete`, `has_checkpoints`.

**Filtering:** Skip plans where `has_summary: true`. If `--gaps-only`: also skip non-gap_closure plans. If `WAVE_FILTER` is set: also skip plans whose `wave` does not equal `WAVE_FILTER`.

**Wave safety check:** If `WAVE_FILTER` is set and there are still incomplete plans in any lower wave that match the current execution mode, STOP and tell the user to finish earlier waves first. Do not let Wave 2+ execute while prerequisite earlier-wave plans remain incomplete.

If all filtered: "No matching incomplete plans" → exit.

Report:
```
## Execution Plan

**Phase {X}: {Name}** — {total_plans} matching plans across {wave_count} wave(s)

{If WAVE_FILTER is set: `Wave filter active: executing only Wave {WAVE_FILTER}`.}

| Wave | Plans | What it builds |
|------|-------|----------------|
| 1 | 01-01, 01-02 | {from plan objectives, 3-8 words} |
| 2 | 01-03 | ... |
```
</step>

<step name="cross_ai_delegation">
**Optional step 2.5 — Delegate plans to an external AI runtime.**

This step runs after plan discovery and before normal wave execution. It identifies plans
that should be delegated to an external AI command and executes them via stdin-based prompt
delivery. Plans handled here are removed from the execute_waves plan list so the normal
executor skips them.

**Activation logic:**

1. If `CROSS_AI_DISABLED` is true (`--no-cross-ai` flag): skip this step entirely.
2. If `CROSS_AI_FORCE` is true (`--cross-ai` flag): mark ALL incomplete plans for cross-AI execution.
3. Otherwise: check each plan's frontmatter for `cross_ai: true` AND verify config
   `workflow.cross_ai_execution` is `true`. Plans matching both conditions are marked for cross-AI.

```bash
CROSS_AI_ENABLED=$(gsd-sdk query config-get workflow.cross_ai_execution 2>/dev/null || echo "false")
CROSS_AI_CMD=$(gsd-sdk query config-get workflow.cross_ai_command 2>/dev/null || echo "")
CROSS_AI_TIMEOUT=$(gsd-sdk query config-get workflow.cross_ai_timeout 2>/dev/null || echo "300")
```

**If no plans are marked for cross-AI:** Skip to execute_waves.

**If plans are marked but `cross_ai_command` is empty:** Error — tell user to set
`workflow.cross_ai_command` via `gsd-sdk query config-set workflow.cross_ai_command "<command>"`.

**For each cross-AI plan (sequentially):**

1. **Construct the task prompt** from the plan file:
   - Extract `<objective>` and `<tasks>` sections from the PLAN.md
   - Append PROJECT.md context (project name, description, tech stack)
   - Format as a self-contained execution prompt

2. **Check for dirty working tree before execution:**
   ```bash
   if ! git diff --quiet HEAD 2>/dev/null; then
     echo "WARNING: dirty working tree detected — the external AI command may produce uncommitted changes that conflict with existing modifications"
   fi
   ```

3. **Run the external command** from the project root, writing the prompt to stdin.
   Never shell-interpolate the prompt — always pipe via stdin to prevent injection:
   ```bash
   echo "$TASK_PROMPT" | timeout "${CROSS_AI_TIMEOUT}s" ${CROSS_AI_CMD} > "$CANDIDATE_SUMMARY" 2>"$ERROR_LOG"
   EXIT_CODE=$?
   ```

4. **Evaluate the result:**

   **Success (exit 0 + valid summary):**
   - Read `$CANDIDATE_SUMMARY` and validate it contains meaningful content
     (not empty, has at least a heading and description — a valid SUMMARY.md structure)
   - Write it as the plan's SUMMARY.md file
   - Update STATE.md plan status to complete
   - Update ROADMAP.md progress
   - Mark plan as handled — skip it in execute_waves

   **Failure (non-zero exit or invalid summary):**
   - Display the error output and exit code
   - Warn: "The external command may have left uncommitted changes or partial edits
     in the working tree. Review `git status` and `git diff` before proceeding."
   - Offer three choices:
     - **retry** — run the same plan through cross-AI again
     - **skip** — fall back to normal executor for this plan (re-add to execute_waves list)
     - **abort** — stop execution entirely, preserve state for resume

5. **After all cross-AI plans processed:** Remove successfully handled plans from the
   incomplete plan list so execute_waves skips them. Any skipped-to-fallback plans remain
   in the list for normal executor processing.
</step>

<step name="execute_waves">
Execute each selected wave in sequence. Within a wave: parallel if `PARALLELIZATION=true`, sequential if `false`.

**Stream-idle-timeout prevention — checkpoint heartbeats (#2410):**

Multi-plan phases can accumulate enough subagent context that the Claude API
SSE layer terminates with `Stream idle timeout - partial response received`
between a large tool_result and the next assistant turn (seen on Claude Code
+ Opus 4.7 at ~200K+ cache_read). To keep the stream warm, emit short
assistant-text heartbeats — **no tool call, just a literal line** — at every
wave and plan boundary. Each heartbeat MUST start with `[checkpoint]` so
tooling and `/gsd:manager`'s background-completion handler can grep partial
transcripts. `{P}/{Q}` is the phase-wide completed/total plans counter and
increases monotonically across waves. `{status}` is `complete` (success),
`failed` (executor error), or `checkpoint` (human-gate returned).

```
[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} starting, {wave_plan_count} plan(s), {P}/{Q} plans done
[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} starting ({P}/{Q} plans done)
[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} {status} ({P}/{Q} plans done)
[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} complete, {P}/{Q} plans done ({wave_success}/{wave_plan_count} ok)
```

**For each wave:**

1. **Intra-wave files_modified overlap check (BEFORE spawning):**

   Before spawning any agents for this wave, inspect the `files_modified` list of all plans
   in the wave. Check every pair of plans in the wave — if any two plans share even one file
   in their `files_modified` lists, those plans have an implicit dependency and MUST NOT run
   in parallel.

   **Detection algorithm (pseudocode):**
   ```
   seen_files = {}
   overlapping_plans = []
   for each plan in wave_plans:
     for each file in plan.files_modified:
       if file in seen_files:
         overlapping_plans.add(plan, seen_files[file])  # both plans overlap on this file
       else:
         seen_files[file] = plan
   ```

   **If overlap is detected:**
   - Warn the user:
     ```
     ⚠ Intra-wave files_modified overlap detected in Wave {N}:
       Plan {A} and Plan {B} both modify {file}
       Running these plans sequentially to avoid parallel worktree conflicts.
     ```
   - Override `PARALLELIZATION` to `false` for this wave only — run all plans in the wave
     sequentially regardless of the global parallelization setting.
   - This is a safety net for plans that were incorrectly assigned to the same wave.
     The planner should have caught this; flag it as a planning defect so the user can
     replan the phase if desired.

   **If no overlap:** proceed normally (parallel if `PARALLELIZATION=true`).

2. **Describe what's being built (BEFORE spawning):**

   **First, emit the wave-start checkpoint heartbeat as a literal assistant-text
   line — no tool call (#2410). Do NOT skip this even for single-plan waves; it
   is required before any further reasoning or spawning:**

   ```
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} starting, {wave_plan_count} plan(s), {P}/{Q} plans done
   ```

   Then read each plan's `<objective>`. Extract what's being built and why.

   ```
   ---
   ## Wave {N}

   **{Plan ID}: {Plan Name}**
   {2-3 sentences: what this builds, technical approach, why it matters}

   Spawning {count} agent(s)...
   ---
   ```

   - Bad: "Executing terrain generation plan"
   - Good: "Procedural terrain generator using Perlin noise — creates height maps, biome zones, and collision meshes. Required before vehicle physics can interact with ground."

2.5. **Per-plan worktree decision (run for each plan in this wave BEFORE its dispatch):**

   Read and execute `get-shit-done/workflows/execute-phase/steps/per-plan-worktree-gate.md` for each plan. It extracts `PLAN_FILES` from the plan's JSON, intersects against `SUBMODULE_PATHS` (with normalization, bidirectional matching, and glob-prefix handling), and sets `USE_WORKTREES_FOR_PLAN` to `false` when the plan touches a submodule path. Append `plan_id` to a `WAVE_WORKTREE_PLANS` accumulator when `USE_WORKTREES_FOR_PLAN != false`.

   The dispatch branches in step 3 below MUST gate on `USE_WORKTREES_FOR_PLAN` for the current plan, not on the project-level `USE_WORKTREES`.

3. **Spawn executor agents:**

   **Emit a plan-start heartbeat (literal line, no tool call) immediately before
   each `Agent()` dispatch (#2410):**

   `[checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} starting ({P}/{Q} plans done)`

   Pass paths only — executors read files themselves with their fresh context window.
   For 200k models, this keeps orchestrator context lean (~10-15%).
   For 1M+ models (Opus 4.6, Sonnet 4.6), richer context can be passed directly.

   **Worktree mode** (`USE_WORKTREES_FOR_PLAN` is not `false` — evaluated per-plan in step 2.5):

   Before spawning, capture the current HEAD:
   ```bash
   EXPECTED_BASE=$(git rev-parse HEAD)
   DISPATCH_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
   EXPECTED_BRANCH=$(git rev-parse --abbrev-ref HEAD)
   if [ "${USE_WORKTREES_FOR_PLAN:-true}" != "false" ] && [ -z "${WAVE_WORKTREE_MANIFEST:-}" ]; then
     WAVE_WORKTREE_MANIFEST=$(mktemp "${TMPDIR:-/tmp}/gsd-worktree-wave-XXXXXX.json")
     printf '{"worktrees":[]}\n' > "$WAVE_WORKTREE_MANIFEST"
     export WAVE_WORKTREE_MANIFEST
   fi
   ```

   **Sequential dispatch for parallel execution (waves with 2+ agents):**
   Dispatch each `Agent()` call **one at a time with `run_in_background: true`**. Do NOT
   send all Agent calls in a single message: simultaneous `git worktree add` calls race
   on `.git/config.lock`. Agents still run in parallel once their worktrees are created.

   ```text
   # CORRECT: one Agent() per message with run_in_background: true
   # WRONG: multiple Agent() calls in one message -> .git/config.lock contention
   ```

   ```text
   Agent(
     subagent_type="gsd-executor",
     description="Execute plan {plan_number} of phase {phase_number}",
     # Only include model= when executor_model is an explicit model name.
     # When executor_model is "inherit", omit this parameter entirely so
     # Claude Code inherits the orchestrator model automatically.
     model="{executor_model}",  # omit this line when executor_model == "inherit"
     isolation="worktree",
     prompt="
       <objective>
       Execute plan {plan_number} of phase {phase_number}-{phase_name}.
       Commit each task atomically. Create SUMMARY.md.
       Do NOT update STATE.md or ROADMAP.md — the orchestrator owns those writes after all worktree agents in the wave complete.
       </objective>

       <worktree_branch_check>
       FIRST ACTION: HEAD assertion MUST run before any reset/checkout. Worktrees
       spawned by Claude Code's `isolation="worktree"` use the `worktree-agent-<id>`
       namespace. If HEAD is on a protected ref (main/master/develop/trunk/release/*)
       or detached, HALT — do NOT self-recover by force-rewinding via `git update-ref`,
       that destroys concurrent commits in multi-active scenarios (#2924). Only after
       Step 1 passes is `git reset --hard` safe (#2015 — affects all platforms).
       ```bash
       HEAD_REF=$(git symbolic-ref --quiet HEAD || echo "DETACHED")
       ACTUAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
       if [ "$HEAD_REF" = "DETACHED" ] || echo "$ACTUAL_BRANCH" | grep -Eq '^(main|master|develop|trunk|release/.*)$'; then
         echo "FATAL: worktree HEAD on '$ACTUAL_BRANCH' (expected worktree-agent-*); refusing to self-recover via 'git update-ref' (#2924)." >&2
         exit 1
       fi
       if ! echo "$ACTUAL_BRANCH" | grep -Eq '^worktree-agent-[A-Za-z0-9._/-]+$'; then
         echo "FATAL: worktree HEAD '$ACTUAL_BRANCH' is not in the worktree-agent-* namespace; refusing to commit (#2924)." >&2
         exit 1
       fi
       ACTUAL_BASE=$(git merge-base HEAD {EXPECTED_BASE})
       if [ "$ACTUAL_BASE" != "{EXPECTED_BASE}" ]; then
         git reset --hard {EXPECTED_BASE}
         [ "$(git rev-parse HEAD)" != "{EXPECTED_BASE}" ] && { echo "ERROR: could not correct worktree base"; exit 1; }
       fi
       ```
       Per-commit HEAD/cwd-drift/path-guard: `agents/gsd-executor.md` steps 0/0a/0b + `references/worktree-path-safety.md` (in <execution_context>).
       </worktree_branch_check>

       <parallel_execution>
       You are running as a PARALLEL executor agent in a git worktree. Worktree path safety (cwd-drift, absolute-path guards) is in `worktree-path-safety.md` (loaded below).
       Run `git commit` normally — hooks run by default. Do NOT pass `--no-verify`
       unless the orchestrator surfaces `workflow.worktree_skip_hooks=true` in this
       prompt; silent bypass violates project CLAUDE.md guidance (#2924).

       IMPORTANT: Do NOT modify STATE.md or ROADMAP.md. execute-plan.md
       auto-detects worktree mode (`.git` is a file, not a directory) and skips
       shared file updates automatically. The orchestrator updates them centrally
       after merge.

       REQUIRED: SUMMARY.md MUST be committed before you return. In worktree mode the
       git_commit_metadata step in execute-plan.md commits SUMMARY.md and REQUIREMENTS.md
       only (STATE.md and ROADMAP.md are excluded automatically). Do NOT skip or defer
       this commit — the orchestrator force-removes the worktree after you return, and
       any uncommitted SUMMARY.md will be permanently lost (#2070).
       REQUIRED ORDER: Write SUMMARY.md → commit → only then any narration. No text between Write and commit (truncation risk; #2070 rescue is not primary defense).
       </parallel_execution>

       <execution_context>
       @~/.claude/get-shit-done/workflows/execute-plan.md
       @~/.claude/get-shit-done/templates/summary.md
       @~/.claude/get-shit-done/references/checkpoints.md
       @~/.claude/get-shit-done/references/tdd.md
       @~/.claude/get-shit-done/references/worktree-path-safety.md
       ${CONTEXT_WINDOW < 200000 ? '' : '@~/.claude/get-shit-done/references/executor-examples.md'}
       </execution_context>

       <files_to_read>
       Read these files at execution start using the Read tool:
       - {phase_dir}/{plan_file} (Plan)
       - .planning/PROJECT.md (Project context — core value, requirements, evolution rules)
       - .planning/STATE.md (State)
       - .planning/config.json (Config, if exists)
       ${CONTEXT_WINDOW >= 500000 ? `
       - ${phase_dir}/*-CONTEXT.md (User decisions from discuss-phase — honors locked choices)
       - ${phase_dir}/*-RESEARCH.md (Technical research — pitfalls and patterns to follow)
       - ${prior_wave_summaries} (SUMMARY.md files from earlier waves in this phase — what was already built)
       ` : ''}
       - ./CLAUDE.md (Project instructions, if exists — follow project-specific guidelines and coding conventions)
       - .claude/skills/ or .agents/skills/ (Project skills, if either exists — list skills, read SKILL.md for each, follow relevant rules during implementation)
       </files_to_read>

       ${AGENT_SKILLS}

       <mcp_tools>
       If CLAUDE.md or project instructions reference MCP tools (e.g. jCodeMunch, context7,
       or other MCP servers), prefer those tools over Grep/Glob for code navigation when available.
       MCP tools often save significant tokens by providing structured code indexes.
       Check tool availability first — if MCP tools are not accessible, fall back to Grep/Glob.
       </mcp_tools>

       <success_criteria>
       - [ ] All tasks executed
       - [ ] Each task committed individually
       - [ ] SUMMARY.md created in plan directory
       - [ ] No modifications to shared orchestrator artifacts (the orchestrator handles all post-wave shared-file writes)
       </success_criteria>
     "
   )
   ```

   Immediately after each worktree `Agent()` spawn returns metadata, atomically append `{agent_id, worktree_path, branch, expected_base}` to `WAVE_WORKTREE_MANIFEST`. If any field is missing, stop and ask for recovery instead of scanning all agent worktrees.

   > **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above to spawn executor agent(s), stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

   **Sequential mode** (`USE_WORKTREES_FOR_PLAN` is `false` — either project-level `USE_WORKTREES=false`, or per-plan submodule intersection forced it false in step 2.5):

   Omit `isolation="worktree"` from the Agent call. Replace the `<parallel_execution>` block with:

   ```
       <sequential_execution>
       You are running as a SEQUENTIAL executor agent on the main working tree.
       Use normal git commits (with hooks). Do NOT use --no-verify.
       REQUIRED ORDER: Write SUMMARY.md → commit → only then any narration. No text between Write and commit (truncation risk; #2070 rescue is not primary defense).
       </sequential_execution>
   ```

   The sequential mode Agent prompt uses the same structure as worktree mode but with these differences in success_criteria — since there is only one agent writing at a time, there are no shared-file conflicts:

   ```
       <success_criteria>
       - [ ] All tasks executed
       - [ ] Each task committed individually
       - [ ] SUMMARY.md created in plan directory
       - [ ] STATE.md updated with position and decisions
       - [ ] ROADMAP.md updated with plan progress (via `roadmap update-plan-progress`)
       </success_criteria>
   ```

   When worktrees are disabled for a plan (per-plan or project-level), that plan's executor runs on the main working tree. If **any** plan in the current wave dropped to sequential mode, execute the affected plan(s) **one at a time** to avoid concurrent writes to the main working tree — plans in the same wave that retained worktree isolation can still run in parallel alongside the sequential ones, but two non-worktree plans in the same wave must serialize. When the project-level `USE_WORKTREES=false`, all plans in the wave serialize regardless of the `PARALLELIZATION` setting.

4. **Wait for all agents in wave to complete.**

   **Plan-complete heartbeat (#2410):** as each executor returns (or is verified
   via spot-check below), emit one line — `complete` advances `{P}`, `failed`
   and `checkpoint` do not but still warm the stream:

   ```
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} complete ({P}/{Q} plans done)
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} failed ({P}/{Q} plans done)
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} plan {plan_id} checkpoint ({P}/{Q} plans done)
   ```

   **Completion signal fallback (Copilot and runtimes where Agent() may not return):**

   If a spawned agent does not return a completion signal but appears to have finished
   its work, do NOT block indefinitely. Instead, verify completion via spot-checks:

   ```bash
   # For each plan in this wave, check if the executor finished:
   SUMMARY_EXISTS=$(test -f "{phase_dir}/{plan_number}-{plan_padded}-SUMMARY.md" && echo "true" || echo "false")
   COMMITS_FOUND=$(git log --oneline --all --grep="{phase_number}-{plan_padded}" --since="1 hour ago" | head -1)
   COMMITS_SINCE_DISPATCH=$(git log "${EXPECTED_BRANCH}" --since="${DISPATCH_TS}" --oneline | head -1)
   ```

   **If SUMMARY.md exists AND commits are found:** The agent completed successfully —
   treat as done and proceed to step 5. Log: `"✓ {Plan ID} completed (verified via spot-check — completion signal not received)"`

   **If SUMMARY.md does NOT exist after a reasonable wait:** The agent may still be
   running or may have failed silently. Check `git log --oneline -5` for recent
   activity. If commits are still appearing, wait longer. If no activity, report
   the plan as failed and route to the failure handler in step 6.

   **Configurable stall surveillance (#3212):** Every `${EXECUTOR_STALL_INTERVAL_MINUTES}`
   minutes while waiting, inspect `git log "${EXPECTED_BRANCH}" --since="${DISPATCH_TS}"`
   for activity. If no completion signal, no SUMMARY.md, and no expected-branch
   commits appear for `${EXECUTOR_STALL_THRESHOLD_MINUTES}` minutes, pause and
   ask for one recovery path: `continue waiting`, `kill and retry`, or
   `kill and switch to inline execution`.

   **This fallback applies automatically to all runtimes.** Claude Code's Agent() normally
   returns synchronously, but the fallback ensures resilience if it doesn't.

5. **Post-wave hook validation (parallel mode only):** Hooks run on every executor commit by default (#2924); this post-wave run only fires when `workflow.worktree_skip_hooks=true` opted out of per-commit hooks:
   ```bash
   SKIP_HOOKS=$(gsd-sdk query config-get workflow.worktree_skip_hooks 2>/dev/null || echo "false")
   if [ "$SKIP_HOOKS" = "true" ]; then
     # Stash uncommitted changes under a named ref so we always pop (bare `git stash` strands them on hook/script failure). #3542: `refs/stash` is shared across worktrees, so this helper runs ONLY in the orchestrator's main checkout after all wave worktrees have been merged + removed; executors are forbidden from running any `git stash` subcommand (see `<destructive_git_prohibition>` in `agents/gsd-executor.md`).
     STASHED=false
     if (! git diff --quiet || ! git diff --cached --quiet) && git stash push -u -m "gsd-post-wave-hook-$$" >/dev/null 2>&1; then STASHED=true; fi
     git hook run pre-commit 2>&1 || echo "⚠ Pre-commit hooks failed — review before continuing"
     [ "$STASHED" = "true" ] && (git stash pop >/dev/null 2>&1 || echo "⚠ Could not pop gsd-post-wave-hook stash — recover manually")
   fi
   ```
   If hooks fail: report the failure and ask "Fix hook issues now?" or "Continue to next wave?"

5.5. **Worktree cleanup (when `isolation="worktree"` was used):**

   **Standard wave contract:** Each wave's worktrees merge to main via the templated path below before the next wave's worktrees fork. The cleanup loop runs once per wave at the end of the wave lifecycle. Worktrees created in wave N must be fully removed before wave N+1 forks new ones.

   **Cross-wave dependency deviation (supported execution mode):** When the orchestrator legitimately deviates from the standard wave model — for example, a phase with cross-wave plan dependencies that requires custom inter-worktree base-update merges (e.g., `merge: bring 09-01 + 09-02 into 09-03 base`) — the cleanup loop below is NOT automatically re-entered for those custom merges. The deviation path produces correct final history but bypasses this loop, leaving `worktree-agent-*` directories in place. Use the **cleanup-tail snippet** below to remove any residual worktrees after such a deviation.

   When executor agents ran in worktree isolation, their commits land on temporary branches in separate working trees. After the wave completes, merge these changes back and clean up:

   **Manifest source of truth (#3384):** Cleanup consumes the `WAVE_WORKTREE_MANIFEST` created and populated during executor dispatch in step 3. Do not recreate or truncate it here.

   Prefer the bounded helper, which validates branch identity, expected base, deletion
   diffs, merge result, and worktree removal before deleting the temporary branch.
   If the helper reports a blocked cleanup, resolve the reported manifest entry and
   rerun the same command. Do not fall back to broad worktree discovery.

   ```bash
   [ -n "${WAVE_WORKTREE_MANIFEST:-}" ] && [ -f "$WAVE_WORKTREE_MANIFEST" ] || {
     echo "BLOCKED: missing WAVE_WORKTREE_MANIFEST; refusing broad worktree cleanup (#3384)." >&2
     exit 1
   }

   # Guard: pin cleanup back to the primary worktree and fail on branch drift (#3174).
   PRIMARY_WT=$(git worktree list --porcelain | awk '/^worktree /{print substr($0,10); exit}')
   if [ -z "$PRIMARY_WT" ]; then
     echo "FATAL: could not resolve primary worktree before cleanup" >&2
     exit 1
   fi
   if [ -n "$PRIMARY_WT" ] && [ "$(pwd -P 2>/dev/null)" != "$(cd "$PRIMARY_WT" 2>/dev/null && pwd -P)" ]; then echo "⚠ Orchestrator CWD drifted to $(pwd) — pinning to $PRIMARY_WT before worktree cleanup (#3174)"; cd "$PRIMARY_WT" || { echo "FATAL: cannot cd to primary worktree $PRIMARY_WT" >&2; exit 1; }; fi
   ORCH_BRANCH=$(git rev-parse --abbrev-ref HEAD)
   [ -z "${EXPECTED_BRANCH:-}" ] || [ "$ORCH_BRANCH" = "$EXPECTED_BRANCH" ] || { echo "FATAL: orchestrator on '$ORCH_BRANCH' but expected '$EXPECTED_BRANCH' before worktree cleanup — refusing to merge (#3174-class drift)" >&2; exit 1; }

   if command -v gsd-sdk >/dev/null 2>&1; then
     gsd-sdk query worktree.cleanup-wave --manifest "$WAVE_WORKTREE_MANIFEST" || exit 1
   else
     echo "WARN: gsd-sdk unavailable; using manifest-scoped shell fallback (#3384)." >&2
   WT_PATHS_FILE=$(mktemp "${TMPDIR:-/tmp}/gsd-worktree-paths-XXXXXX")
   node -e 'const fs=require("fs");const p=process.env.WAVE_WORKTREE_MANIFEST;try{if(!p)throw new Error("WAVE_WORKTREE_MANIFEST is unset");if(!fs.existsSync(p))throw new Error("manifest does not exist");const s=fs.readFileSync(p,"utf8");if(!s.trim())throw new Error("manifest is empty");const j=JSON.parse(s);for(const w of j.worktrees||[])if(w.worktree_path)console.log(w.worktree_path)}catch(e){console.error(`ERROR: cannot read worktree manifest ${p||"(unset)"}: ${e.message}`);process.exit(1)}' > "$WT_PATHS_FILE" || { echo "BLOCKED: cannot read WAVE_WORKTREE_MANIFEST; refusing cleanup (#3384)." >&2; exit 1; }
   while IFS= read -r WT; do
     [ -z "$WT" ] && continue
     WT_BRANCH=$(git -C "$WT" rev-parse --abbrev-ref HEAD 2>/dev/null)
     if [ -n "$WT_BRANCH" ] && [ "$WT_BRANCH" != "HEAD" ]; then
       CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
       STATE_BACKUP=$(mktemp)
       ROADMAP_BACKUP=$(mktemp)
       [ -f .planning/STATE.md ] && cp .planning/STATE.md "$STATE_BACKUP" || true
       [ -f .planning/ROADMAP.md ] && cp .planning/ROADMAP.md "$ROADMAP_BACKUP" || true
       DELETIONS=$(git diff --diff-filter=D --name-only HEAD..."$WT_BRANCH" 2>/dev/null || true)
       if [ -n "$DELETIONS" ]; then
         echo "BLOCKED: Worktree branch $WT_BRANCH contains file deletions: $DELETIONS"
         echo "Review these deletions before merging. If intentional, remove this guard and re-run."
         rm -f "$STATE_BACKUP" "$ROADMAP_BACKUP"
         continue
       fi
       git merge "$WT_BRANCH" --no-ff --no-edit -m "chore: merge executor worktree ($WT_BRANCH)" 2>&1 || {
         echo "⚠ Merge conflict from worktree $WT_BRANCH — resolve manually"
         echo "  STATE.md backup:   $STATE_BACKUP"
         echo "  ROADMAP.md backup: $ROADMAP_BACKUP"
         echo "  Restore with: cp \$STATE_BACKUP .planning/STATE.md && cp \$ROADMAP_BACKUP .planning/ROADMAP.md"
         break
       }
       MERGE_DEL_COUNT=$(git diff --diff-filter=D --name-only HEAD~1 HEAD 2>/dev/null | grep -vc '^\.planning/' || true)
       if [ "$MERGE_DEL_COUNT" -gt 5 ] && [ "${ALLOW_BULK_DELETE:-0}" != "1" ]; then
         MERGE_DELETIONS=$(git diff --diff-filter=D --name-only HEAD~1 HEAD 2>/dev/null | grep -v '^\.planning/' || true)
         echo "⚠ BLOCKED: Merge of $WT_BRANCH deleted $MERGE_DEL_COUNT files outside .planning/ — reverting to protect repository integrity (#2384)"
         echo "$MERGE_DELETIONS"
         echo "  If these deletions are intentional, re-run with ALLOW_BULK_DELETE=1"
         git reset --hard HEAD~1 2>/dev/null || true
         rm -f "$STATE_BACKUP" "$ROADMAP_BACKUP"
         continue
       fi
       if [ -s "$STATE_BACKUP" ]; then
         cp "$STATE_BACKUP" .planning/STATE.md
       fi
       if [ -s "$ROADMAP_BACKUP" ]; then
         cp "$ROADMAP_BACKUP" .planning/ROADMAP.md
       fi
       rm -f "$STATE_BACKUP" "$ROADMAP_BACKUP"
       # Detect files deleted on main but re-added by worktree merge (#2501).
       DELETED_FILES=$(git diff --diff-filter=A --name-only HEAD~1 -- .planning/ 2>/dev/null || true)
       for RESURRECTED in $DELETED_FILES; do
         WAS_DELETED=$(git log --follow --diff-filter=D --name-only --format="" HEAD~1 -- "$RESURRECTED" 2>/dev/null | grep -c . || true)
         if [ "${WAS_DELETED:-0}" -gt 0 ]; then
           git rm -f "$RESURRECTED" 2>/dev/null || true
         fi
       done
       if ! git diff --quiet .planning/STATE.md .planning/ROADMAP.md 2>/dev/null || \
          [ -n "$DELETED_FILES" ]; then
         COMMIT_DOCS=$(gsd-sdk query config-get commit_docs 2>/dev/null || echo "true")
         if [ "$COMMIT_DOCS" != "false" ]; then
           git add .planning/STATE.md .planning/ROADMAP.md 2>/dev/null || true
           git commit --amend --no-edit 2>/dev/null || true
         fi
       fi
       # Safety net: rescue uncommitted SUMMARY.md before worktree removal (#2070, #2838).
       while IFS= read -r SUMMARY; do
         [ -z "$SUMMARY" ] && continue
         REL_PATH="${SUMMARY#$WT/}"
         if [ ! -f "$REL_PATH" ] || ! cmp -s "$SUMMARY" "$REL_PATH"; then
           mkdir -p "$(dirname "$REL_PATH")"
           cp "$SUMMARY" "$REL_PATH"
           echo "⚠ Rescued $REL_PATH from worktree before removal"
         fi
       done < <(find "$WT/.planning" -name "*SUMMARY.md" 2>/dev/null)
       REMOVE_OK=false
       if git worktree remove "$WT" --force; then
         REMOVE_OK=true
       else
         WT_NAME=$(basename "$WT")
         if [ -f ".git/worktrees/${WT_NAME}/locked" ]; then
           echo "⚠ Worktree $WT is locked — attempting to unlock and retry"
           git worktree unlock "$WT" 2>/dev/null || true
           if git worktree remove "$WT" --force; then
             REMOVE_OK=true
           else
             echo "⚠ Residual worktree at $WT — manual cleanup required after session exits:"
             echo "    git worktree unlock \"$WT\" && git worktree remove \"$WT\" --force && git branch -D \"$WT_BRANCH\""
           fi
         else
           echo "⚠ Residual worktree at $WT (remove failed) — investigate manually"
         fi
       fi
       if [ "$REMOVE_OK" = "true" ]; then
         git branch -D "$WT_BRANCH" 2>/dev/null || true
       else
         echo "⚠ Keeping branch $WT_BRANCH because worktree removal failed (#3384)"
       fi
     fi
   done < "$WT_PATHS_FILE"
   fi
   ```

   **Cleanup-tail snippet (use after any wave whose merges did not flow through the templated path above):**

   If the orchestrator deviated from the standard wave merge path (e.g., custom inter-worktree base-update merges with `merge: bring …` style messages), run this snippet after the custom merges are complete. It reads only `WAVE_WORKTREE_MANIFEST`; do not discover unrelated `worktree-agent-*` worktrees.

   ```bash
   # Cleanup-tail: pin orchestrator CWD to primary worktree before cleanup-tail (#3174).
   PRIMARY_WT=$(git worktree list --porcelain | awk '/^worktree /{print substr($0,10); exit}')
   if [ -n "$PRIMARY_WT" ] && [ "$(pwd -P 2>/dev/null)" != "$(cd "$PRIMARY_WT" 2>/dev/null && pwd -P)" ]; then echo "⚠ Orchestrator CWD drifted to $(pwd) — pinning to $PRIMARY_WT before cleanup-tail (#3174)"; cd "$PRIMARY_WT" || { echo "FATAL: cannot cd to primary worktree $PRIMARY_WT" >&2; exit 1; }; fi
   # Cleanup-tail: remove residual agent worktrees after a cross-wave-dependency deviation.
   # Uses only the current wave manifest to avoid touching unrelated active agents (#3384).
   WT_PATHS_FILE=$(mktemp "${TMPDIR:-/tmp}/gsd-worktree-paths-XXXXXX")
   node -e 'const fs=require("fs");const p=process.env.WAVE_WORKTREE_MANIFEST;try{if(!p)throw new Error("WAVE_WORKTREE_MANIFEST is unset");if(!fs.existsSync(p))throw new Error("manifest does not exist");const s=fs.readFileSync(p,"utf8");if(!s.trim())throw new Error("manifest is empty");const j=JSON.parse(s);for(const w of j.worktrees||[])if(w.worktree_path)console.log(w.worktree_path)}catch(e){console.error(`ERROR: cannot read worktree manifest ${p||"(unset)"}: ${e.message}`);process.exit(1)}' > "$WT_PATHS_FILE" || { echo "BLOCKED: cannot read WAVE_WORKTREE_MANIFEST; refusing cleanup (#3384)." >&2; exit 1; }
   while IFS= read -r WT; do
     [ -z "$WT" ] && continue
     WT_BRANCH=$(git -C "$WT" rev-parse --abbrev-ref HEAD 2>/dev/null)
     [ -z "$WT_BRANCH" ] || [ "$WT_BRANCH" = "HEAD" ] && continue
     echo "Cleaning up residual worktree: $WT (branch: $WT_BRANCH)"
     git worktree unlock "$WT" 2>/dev/null || true
     if ! git worktree remove "$WT" --force; then
       WT_NAME=$(basename "$WT")
       if [ -f ".git/worktrees/${WT_NAME}/locked" ]; then
         echo "⚠ Worktree $WT is locked — unlock failed; manual cleanup required:"
         echo "    git worktree unlock \"$WT\" && git worktree remove \"$WT\" --force && git branch -D \"$WT_BRANCH\""
       else
         echo "⚠ Residual worktree at $WT — remove failed; manual cleanup required"
       fi
     else
       git branch -D "$WT_BRANCH" 2>/dev/null || true
     fi
   done < "$WT_PATHS_FILE"
   git worktree prune
   ```

   **When to skip step 5.5:**

   **If no plan in this wave used worktree isolation** (project-level `USE_WORKTREES=false` OR every plan in the wave had `USE_WORKTREES_FOR_PLAN=false` — i.e. `WAVE_WORKTREE_PLANS` from step 2.5 is empty): all agents ran on the main working tree — skip this step entirely.

   **If the orchestrator merged via custom messages (cross-wave-dependency deviation):** the templated cleanup loop above was not triggered for those merges. Run the cleanup-tail snippet above instead. After the snippet completes, proceed to step 5.6.

   **If at least one plan used worktrees but others did not:** still run this cleanup — it iterates over actual `git worktree list` output and only merges back the worktrees that were created, leaving sequential plans' commits on the main tree untouched.

   **If no worktrees found at runtime:** Skip silently — agents may have been spawned without worktree isolation, or the orchestrator already cleaned them up.

5.6. **Post-merge build & test gate:**

   After merging all worktrees in a wave (parallel mode), or after the last plan completes
   (serial mode), run a build and then the project's test suite to catch cross-plan
   integration issues that individual worktree self-checks cannot detect (e.g., conflicting
   type definitions, removed exports, import changes, link errors).

   This addresses the Generator self-evaluation blind spot identified in Anthropic's
   harness engineering research: agents reliably report Self-Check: PASSED even when
   merging their work creates failures.

   Read and execute `get-shit-done/workflows/execute-phase/steps/post-merge-gate.md`.

5.7. **Post-wave shared artifact update (when at least one plan used worktrees, skip if tests failed):**

   When **any** executor agent in this wave ran with `isolation="worktree"`, that agent skipped STATE.md and ROADMAP.md updates to avoid last-merge-wins overwrites. The orchestrator is the single writer for these files. After worktrees are merged back, update shared artifacts once for every completed plan in the wave (worktree-mode plans **and** sequential plans that ran on the main tree but deferred to the orchestrator for tracking writes).

   **Only update tracking when tests passed (TEST_EXIT=0).**
   If tests failed or timed out, skip the tracking update — plans should
   not be marked as complete when integration tests are failing or inconclusive.

   ```bash
   # Guard: only update tracking if post-merge tests passed
   # Timeout (124) is treated as inconclusive — do NOT mark plans complete
   if [ "${TEST_EXIT}" -eq 0 ]; then
     # Update ROADMAP plan progress for each completed plan in this wave
     for plan_id in {completed_plan_ids}; do
       gsd-sdk query roadmap.update-plan-progress "${PHASE_NUMBER}" "${plan_id}" "complete"
     done

     # Only commit tracking files if they actually changed
     if ! git diff --quiet .planning/ROADMAP.md .planning/STATE.md 2>/dev/null; then
       gsd-sdk query commit "docs(phase-${PHASE_NUMBER}): update tracking after wave ${N}" --files .planning/ROADMAP.md .planning/STATE.md
     fi
   elif [ "${TEST_EXIT}" -eq 124 ]; then
     echo "⚠ Skipping tracking update — test suite timed out. Plans remain in-progress. Run tests manually to confirm."
   else
     echo "⚠ Skipping tracking update — post-merge tests failed (exit ${TEST_EXIT}). Plans remain in-progress until tests pass."
   fi
   ```

   Where `WAVE_PLAN_IDS` is the space-separated list of plan IDs that completed in this wave.

   **If no plan in this wave used worktrees** (project-level `USE_WORKTREES=false` OR `WAVE_WORKTREE_PLANS` is empty): sequential agents already updated STATE.md and ROADMAP.md themselves — skip this step.

5.8. **Handle test gate failures (when `WAVE_FAILURE_COUNT > 0`):**

   ```
   ## ⚠ Post-Merge Test Failure (cumulative failures: ${WAVE_FAILURE_COUNT})

   Wave {N} worktrees merged successfully, but {M} tests fail after merge.
   This typically indicates conflicting changes across parallel plans
   (e.g., type definitions, shared imports, API contracts).

   Failed tests:
   {first 10 lines of failure output}

   Options:
   1. Fix now (recommended) — resolve conflicts before next wave
   2. Continue — failures may compound in subsequent waves
   ```

   Note: If `WAVE_FAILURE_COUNT > 1`, strongly recommend "Fix now" — compounding
   failures across multiple waves become exponentially harder to diagnose.

   If "Fix now": diagnose failures (typically import conflicts, missing types,
   or changed function signatures from parallel plans modifying the same module).
   Fix, commit as `fix: resolve post-merge conflicts from wave {N}`, re-run tests.

   **Why this matters:** Worktree isolation means each agent's Self-Check passes
   in isolation. But when merged, add/add conflicts in shared files (models, registries,
   CLI entry points) can silently drop code. The post-merge gate catches this before
   the next wave builds on a broken foundation.

6. **Report completion — spot-check claims first:**

   **Wave-close heartbeat (#2410):** after spot-checks finish (pass or fail),
   before the `## Wave {N} Complete` summary, emit as a literal line:

   ```
   [checkpoint] phase {PHASE_NUMBER} wave {N}/{M} complete, {P}/{Q} plans done ({wave_success}/{wave_plan_count} ok)
   ```



   For each SUMMARY.md:
   - Verify first 2 files from `key-files.created` exist on disk
   - Check `git log --oneline --all --grep="{phase}-{plan}"` returns ≥1 commit
   - Check for `## Self-Check: FAILED` marker

   If ANY spot-check fails: report which plan failed, route to failure handler — ask "Retry plan?" or "Continue with remaining waves?"

   If pass:
   ```
   ---
   ## Wave {N} Complete

   **{Plan ID}: {Plan Name}**
   {What was built — from SUMMARY.md}
   {Notable deviations, if any}

