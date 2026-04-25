# Agent Coordination Walkthrough — Multi-File Rename Refactor

This walkthrough demonstrates how the `dispatching-parallel-agents` skill coordinates multiple AI agents working in isolated git worktrees to execute independent tasks in parallel.

---

## Scenario

**Task:** Rename `UserService` to `AccountService` across the codebase.

Three files need changes, each independent:
1. `src/services/user-service.ts` — rename file, class, and all internal references
2. `src/api/routes/users.ts` — update import paths and handler references
3. `tests/services/user-service.test.ts` — rename file, update imports, fix test descriptions

A human doing this sequentially takes 15-20 minutes of careful find-and-replace. With parallel agents, it completes in one wave.

---

## Step 1: Brainstorming & Planning

Before dispatching, the orchestrator agent analyzes the task:

- **Dependency check:** Are any of these files importing from each other in a way that creates ordering constraints? In this case, routes imports from services and tests import from services, but the rename is consistent across all three — no ordering dependency.
- **Conflict check:** Will any two agents edit the same file? No — each agent owns exactly one file.
- **Verdict:** Safe to parallelize. Three agents, one wave.

---

## Step 2: Dispatch Table

The orchestrator creates the dispatch plan:

| Agent | Worktree Branch | Files Owned | Task |
|-------|----------------|-------------|------|
| Agent 1 | `refactor/rename-service-impl` | `src/services/user-service.ts` | Rename file to `account-service.ts`, rename class `UserService` to `AccountService`, update all method signatures and internal references |
| Agent 2 | `refactor/rename-routes` | `src/api/routes/users.ts` | Update import path from `user-service` to `account-service`, rename all `userService` variable references to `accountService` |
| Agent 3 | `refactor/rename-tests` | `tests/services/user-service.test.ts` | Rename file to `account-service.test.ts`, update imports, rename describe blocks and test descriptions |

**Wave structure:**
```
Wave 1 (parallel):  Agent 1 + Agent 2 + Agent 3
                         │         │         │
                         ▼         ▼         ▼
Consolidation:     Merge all three branches into main refactor branch
```

---

## Step 3: Parallel Execution

Each agent is dispatched with:
1. **An isolated git worktree** — created via `git worktree add` so agents never conflict on the filesystem
2. **A scoped task description** — only their files, only their changes
3. **A verification requirement** — agent must confirm the code compiles and their specific tests pass before marking complete

Agents work simultaneously. Each one:
- Creates a feature branch from `main`
- Makes changes in its worktree
- Runs `tsc --noEmit` to verify no type errors
- Runs relevant test files
- Commits with a descriptive message

**Typical timeline:**
- Sequential: 3 agents x 3 min each = 9 minutes
- Parallel: 3 agents simultaneously = 3 minutes (3x faster)

---

## Step 4: Consolidation & Merge

Once all three agents report success, the orchestrator:

1. **Verifies each branch** — checks that each agent's commit only touches the files it was assigned
2. **Merges sequentially** — merges each branch into a consolidation branch:
   ```
   git checkout -b refactor/rename-user-to-account main
   git merge refactor/rename-service-impl
   git merge refactor/rename-routes
   git merge refactor/rename-tests
   ```
3. **Runs full test suite** — ensures no cross-file breakage after combining changes
4. **Cleans up worktrees** — removes temporary worktrees and branches

If the full test suite fails after merge (e.g., a missed import), the orchestrator identifies which file needs a fix and dispatches a single corrective agent.

---

## Step 5: Result

**Before:** `UserService` referenced in 3 files across 47 lines
**After:** `AccountService` consistently renamed everywhere, all tests passing, single clean commit on the refactor branch

---

## When to Use Parallel Agents

**Good candidates:**
- Renaming/refactoring across independent files
- Adding the same pattern (logging, error handling) to multiple services
- Writing tests for multiple modules simultaneously
- Updating configuration files across environments (dev, staging, prod)
- Documentation updates across multiple pages

**Not suitable for:**
- Changes where File B depends on the exact output of File A's changes
- Database migrations that must run in order
- Changes to a single large file (cannot parallelize within one file)
- Tasks requiring back-and-forth human review between steps

**Rule of thumb:** If you can describe each agent's task without referencing another agent's output, it is safe to parallelize.

---

## Key Takeaways

1. **Worktree isolation is essential** — without it, agents would create filesystem conflicts and corrupt each other's work
2. **The dispatch table is the contract** — every agent knows exactly which files it owns and what "done" looks like
3. **Verification happens twice** — each agent verifies locally, then the orchestrator verifies the merged result
4. **Speedup scales with independence** — the more independent the tasks, the more agents you can run in parallel

---

*This walkthrough demonstrates the `dispatching-parallel-agents` and `using-git-worktrees` skills from the Superpowers tier of the how-i-pm-with-ai framework.*
