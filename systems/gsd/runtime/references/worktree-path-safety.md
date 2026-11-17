# Worktree Path Safety

Guards for executor agents running inside Claude Code worktrees. Three checks
must run before any staging, Edit, or Write operation in worktree mode.

---

## Worktree branch check (run once at spawn-time)

FIRST ACTION: HEAD assertion MUST run before any reset/checkout. Worktrees
spawned by Claude Code's `isolation="worktree"` use the `worktree-agent-<id>`
namespace. If HEAD is on a protected ref (main/master/develop/trunk/release/*)
or detached, HALT — do NOT self-recover by force-rewinding via `git update-ref`,
that destroys concurrent commits in multi-active scenarios (#2924). Only after
this passes is `git reset --hard` safe (#2015 — affects all platforms).

```bash
HEAD_REF=$(git symbolic-ref --quiet HEAD || echo "DETACHED")
ACTUAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$HEAD_REF" = "DETACHED" ] || echo "$ACTUAL_BRANCH" | grep -Eq '^(main|master|develop|trunk|release/.*)$'; then
  echo "FATAL: worktree HEAD on '$ACTUAL_BRANCH' (expected worktree-agent-*); refusing to self-recover via 'git update-ref' (#2924)." >&2
