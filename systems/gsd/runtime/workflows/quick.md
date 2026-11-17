<purpose>
Execute small, ad-hoc tasks with GSD guarantees (atomic commits, STATE.md tracking). Quick mode spawns gsd-planner (quick mode) + gsd-executor(s), tracks tasks in `.planning/quick/`, and updates STATE.md's "Quick Tasks Completed" table.

With `--full` flag: enables the complete quality pipeline — discussion + research + plan-checking + verification. One flag for everything.

With `--validate` flag: enables plan-checking (max 2 iterations) and post-execution verification only. Use when you want quality guarantees without discussion or research.

With `--discuss` flag: lightweight discussion phase before planning. Surfaces assumptions, clarifies gray areas, captures decisions in CONTEXT.md so the planner treats them as locked.

With `--research` flag: spawns a focused research agent before planning. Investigates implementation approaches, library options, and pitfalls. Use when you're unsure how to approach a task.

Granular flags are composable: `--discuss --research --validate` gives the same result as `--full`.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<available_agent_types>
Valid GSD subagent types (use exact names — do not fall back to 'general-purpose'):
- gsd-phase-researcher — Researches technical approaches for a phase
- gsd-planner — Creates detailed plans from phase scope
- gsd-plan-checker — Reviews plan quality before execution
- gsd-executor — Executes plan tasks, commits, creates SUMMARY.md
- gsd-verifier — Verifies phase completion, checks quality gates
- gsd-code-reviewer — Reviews source files for bugs, security issues, and code quality
</available_agent_types>

<process>
**Step 1: Parse arguments and get task description**

Parse `$ARGUMENTS` for:
- `--full` flag → store `$FULL_MODE=true`, `$DISCUSS_MODE=true`, `$RESEARCH_MODE=true`, `$VALIDATE_MODE=true`
- `--validate` flag → store `$VALIDATE_MODE=true`
- `--discuss` flag → store `$DISCUSS_MODE=true`
- `--research` flag → store `$RESEARCH_MODE=true`
- Remaining text → use as `$DESCRIPTION` if non-empty

After parsing, normalize: if `$DISCUSS_MODE` and `$RESEARCH_MODE` and `$VALIDATE_MODE` are all true, set `$FULL_MODE=true`. This ensures `--discuss --research --validate` is treated identically to `--full`.

If `$DESCRIPTION` is empty after parsing, prompt user interactively:


**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.

```
AskUserQuestion(
  header: "Quick Task",
  question: "What do you want to do?",
  followUp: null
)
```

Store response as `$DESCRIPTION`.

If still empty, re-prompt: "Please provide a task description."

Display banner based on active flags:

If `$FULL_MODE` (all phases enabled — `--full` or all granular flags):
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► QUICK TASK (FULL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Discussion + research + plan checking + verification enabled
```

If `$DISCUSS_MODE` and `$VALIDATE_MODE` (no research):
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► QUICK TASK (DISCUSS + VALIDATE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Discussion + plan checking + verification enabled
```

If `$DISCUSS_MODE` and `$RESEARCH_MODE` (no validate):
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► QUICK TASK (DISCUSS + RESEARCH)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Discussion + research enabled
```

If `$RESEARCH_MODE` and `$VALIDATE_MODE` (no discuss):
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► QUICK TASK (RESEARCH + VALIDATE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Research + plan checking + verification enabled
```

If `$DISCUSS_MODE` only:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► QUICK TASK (DISCUSS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Discussion phase enabled — surfacing gray areas before planning
```

If `$RESEARCH_MODE` only:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► QUICK TASK (RESEARCH)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Research phase enabled — investigating approaches before planning
```

If `$VALIDATE_MODE` only:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► QUICK TASK (VALIDATE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Plan checking + verification enabled
```

---

**Step 2: Initialize**

```bash
if ! command -v gsd-sdk &>/dev/null; then
  echo "⚠ gsd-sdk not found in PATH — /gsd:quick requires it."
  echo ""
  echo "Install the query-capable GSD SDK CLI:"
  echo "  npm install -g get-shit-done-cc"
  echo ""
  echo "Or update GSD to get the latest packages:"
  echo "  /gsd:update"
  exit 1
fi
```

```bash
INIT=$(gsd-sdk query init.quick "$DESCRIPTION")
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_PLANNER=$(gsd-sdk query agent-skills gsd-planner)
AGENT_SKILLS_EXECUTOR=$(gsd-sdk query agent-skills gsd-executor)
AGENT_SKILLS_CHECKER=$(gsd-sdk query agent-skills gsd-plan-checker)
AGENT_SKILLS_VERIFIER=$(gsd-sdk query agent-skills gsd-verifier)
```

Parse JSON for: `planner_model`, `executor_model`, `checker_model`, `verifier_model`, `commit_docs`, `branch_name`, `quick_id`, `slug`, `date`, `timestamp`, `quick_dir`, `task_dir`, `roadmap_exists`, `planning_exists`.

```bash
USE_WORKTREES=$(gsd-sdk query config-get workflow.use_worktrees 2>/dev/null || echo "true")
```

If `USE_WORKTREES` is not `"false"`, run a startup orphan sweep before spawning any executors. This reaps locked worktrees whose lock-owner process is dead, whose branch is merged into the default branch, and whose lock file mtime is older than 5 minutes. Running it at startup prevents accumulation of orphaned worktrees from prior sessions that exited without cleanup (#3707).

```bash
if [ "$USE_WORKTREES" != "false" ]; then
  gsd-sdk query worktree.reap-orphans 2>/dev/null || true
fi
```

If the project uses git submodules, worktree isolation is unsafe **only when the quick task touches a submodule path**. The previous behavior unconditionally disabled worktree isolation whenever `.gitmodules` existed, which penalised every quick task in a submodule project even when the task was nowhere near a submodule. Parse submodule paths from `.gitmodules` so the executor can act on actual submodule paths rather than the mere file's existence:

```bash
# Parse submodule paths from .gitmodules once (empty if no .gitmodules).
# SUBMODULE_PATHS is a newline-separated list of repo-relative paths used as
# a fail-loud commit-time guard inside the quick-task executor — if the
# executor stages any path that falls inside SUBMODULE_PATHS, it must abort
# the commit and surface the conflict rather than silently corrupting the
# submodule state.
if [ -f .gitmodules ]; then
  SUBMODULE_PATHS=$(git config --file .gitmodules --get-regexp '^submodule\..*\.path$' 2>/dev/null | awk '{print $2}')
else
  SUBMODULE_PATHS=""
fi
```

Quick mode does not have a pre-declared `files_modified` list (the task is freeform), so use a fail-loud guard at commit time: when the executor stages files for the quick-task commit, if any staged path falls inside a `SUBMODULE_PATHS` entry, abort with a clear error explaining that worktree-isolated commits cannot safely span submodule boundaries — the user can re-run with `workflow.use_worktrees=false` to fall back to sequential execution on the main tree. If `SUBMODULE_PATHS` is empty (no `.gitmodules` in the repo), worktree isolation proceeds normally.

**If `roadmap_exists` is false:** Error — Quick mode requires an active project with ROADMAP.md. Run `/gsd:new-project` first.

Quick tasks can run mid-phase - validation only checks ROADMAP.md exists, not phase status.

---

**Step 2.5: Handle quick-task branching**

**If `branch_name` is empty/null:** Skip and continue on the current branch.

**If `branch_name` is set:** Check out the quick-task branch before any planning commits.

The new branch must fork off the project's default branch (`origin/HEAD`), not
off whatever HEAD happens to be checked out — otherwise consecutive quick tasks
compound on top of each other and stay unpushed (#2916). If `$branch_name`
already exists locally, reuse it as-is so resumed work is not rebased.

```bash
DEFAULT_BRANCH=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}

if git show-ref --verify --quiet "refs/heads/$branch_name"; then
  git switch "$branch_name" \
    || { echo "ERROR: Could not switch to existing quick-task branch '$branch_name'." >&2; exit 1; }
else
  # Fetch the default branch so origin/$DEFAULT_BRANCH is current. If the fetch
  # fails (offline, no remote, auth failure) AND we have no local copy of
  # origin/$DEFAULT_BRANCH to fall back on, abort — creating the branch off
  # arbitrary HEAD is exactly the bug #2916 fixed.
  if ! git fetch --quiet origin "$DEFAULT_BRANCH"; then
    if ! git show-ref --verify --quiet "refs/remotes/origin/$DEFAULT_BRANCH"; then
      echo "ERROR: Could not fetch origin/$DEFAULT_BRANCH and no local copy exists. Refusing to create '$branch_name' off the current HEAD (#2916). Resolve the remote/network issue and retry." >&2
      exit 1
    fi
    echo "WARNING: git fetch origin $DEFAULT_BRANCH failed; using the local copy of origin/$DEFAULT_BRANCH as base." >&2
  fi

  if [ -n "$(git status --porcelain)" ]; then
    echo "WARNING: Uncommitted changes present. Carrying them onto the new quick-task branch — they will be branched off origin/$DEFAULT_BRANCH (not the previous-task HEAD)."
  else
    # Best-effort: fast-forward the local default branch so subsequent local
    # work sees the latest tip. Failure here is non-fatal because we always
    # create the new branch directly from origin/$DEFAULT_BRANCH below.
    git switch --quiet "$DEFAULT_BRANCH" 2>/dev/null \
      && git merge --ff-only --quiet "origin/$DEFAULT_BRANCH" 2>/dev/null \
      || true
  fi

  # Pin the new branch to origin/$DEFAULT_BRANCH so the start point is
  # deterministic regardless of which branch we are currently on (#2916).
  # On success HEAD is exactly at origin/$DEFAULT_BRANCH, so a post-creation
  # merge-base / "ahead-of" guard would be unreachable — the explicit base
  # argument here is the single source of correctness for #2916.
  git checkout -b "$branch_name" "origin/$DEFAULT_BRANCH" \
    || { echo "ERROR: Could not create '$branch_name' from origin/$DEFAULT_BRANCH (#2916)." >&2; exit 1; }
fi
```

All quick-task commits for this run stay on that branch. User handles merge/rebase afterward.

---

**Step 3: Create task directory**

```bash
mkdir -p "${task_dir}"
```

---

**Step 4: Create quick task directory**

Create the directory for this quick task:

```bash
QUICK_DIR=".planning/quick/${quick_id}-${slug}"
mkdir -p "$QUICK_DIR"
```

Report to user:
```
Creating quick task ${quick_id}: ${DESCRIPTION}
Directory: ${QUICK_DIR}
```

Store `$QUICK_DIR` for use in orchestration.

---

**Step 4.5: Discussion phase (only when `$DISCUSS_MODE`)**

Skip this step entirely if NOT `$DISCUSS_MODE`.

Display banner:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GSD ► DISCUSSING QUICK TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

◆ Surfacing gray areas for: ${DESCRIPTION}
```

**4.5a. Identify gray areas**

Analyze `$DESCRIPTION` to identify 2-4 gray areas — implementation decisions that would change the outcome and that the user should weigh in on.

Use the domain-aware heuristic to generate phase-specific (not generic) gray areas:
- Something users **SEE** → layout, density, interactions, states
- Something users **CALL** → responses, errors, auth, versioning
- Something users **RUN** → output format, flags, modes, error handling
- Something users **READ** → structure, tone, depth, flow
- Something being **ORGANIZED** → criteria, grouping, naming, exceptions

Each gray area should be a concrete decision point, not a vague category. Example: "Loading behavior" not "UX".

**4.5b. Present gray areas**

```
AskUserQuestion(
  header: "Gray Areas",
  question: "Which areas need clarification before planning?",
  options: [
    { label: "${area_1}", description: "${why_it_matters_1}" },
    { label: "${area_2}", description: "${why_it_matters_2}" },
    { label: "${area_3}", description: "${why_it_matters_3}" },
    { label: "All clear", description: "Skip discussion — I know what I want" }
  ],
