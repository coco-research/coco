---
name: coco-ship
description: Use when finished work needs to reach a coco-managed repository (coco-research/coco or similar) — verifies branch state, commits, pushes through the corporate DLP guard only when actually needed, opens a PR against main, waits for CI, and reports the result. Never merges, never pushes to main directly.
domain: engineering
user-invocable: true
---

# Shipping to a CoCo-managed Repo

## Overview

Formalizes the branch → commit → guard-aware push → PR → CI-wait → report flow used for shipping
work to `coco-research/coco` (or any repo carrying the same corporate git-guard pre-push hook), so it
doesn't have to be re-derived by hand each time.

**Core principle:** Verify state → commit → detect whether the guard actually applies → confirm →
push → open PR → wait for real CI → report. Never merge. Never push to `main` directly, regardless of
how it's asked.

**Announce at start:** "I'm using the coco-ship skill to ship this branch."

This is the direct formalization of Option 2 ("Push and Create PR") in
`finishing-a-development-branch`, specialized for repos that carry the corporate git-guard. It
assumes implementation is already done and reviewed — it doesn't replace planning skills like
`brainstorming`, `writing-plans`, or GSD's phase workflow, and it doesn't run tests itself (that's
`finishing-a-development-branch`'s Step 1, or the project's own CI).

## The Process

### Step 1: Preflight

```bash
git status -sb
git branch --show-current
```

**If the current branch is `main` or `master`:** stop. Do not commit or push here. Offer to create a
feature branch first:

```bash
git checkout -b <feature-branch-name>
```

**If there's nothing to commit and the branch isn't already ahead of its upstream:** stop and say so
— there's nothing to ship.

### Step 2: Commit

Use the standard git-commit protocol already in effect for this harness — this isn't a new
invention, just invoked from inside the skill:

1. In parallel: `git status`, `git diff` (staged + unstaged), `git log` (recent messages, for style).
2. Draft a commit message from the actual diff — why, not just what — matching the repo's existing
   style.
3. Stage named files explicitly. Never `git add -A` or `git add .`.
4. Commit with a `Co-Authored-By` trailer, via a heredoc so formatting survives.
5. `git status` again to confirm a clean tree.

If a pre-commit hook fails, fix the issue, re-stage, and create a **new** commit — never `--amend` a
commit that a failed hook means never actually landed.

### Step 3: Detect whether the guard bypass is actually needed

Don't assume — check:

```bash
git remote -v
gh repo view <owner>/<repo> --json visibility,owner -q '"\(.visibility) \(.owner.login)"'
git config --show-origin --get core.hooksPath
```

A `GIT_GUARD_REASON` bypass is only needed when the repo is `PUBLIC` **and** the owner isn't on the
guard's allowlist — check the actual guard config or ask the user which org(s) it allows, rather than
assuming. If `core.hooksPath` doesn't point at the guard, don't assume a bypass is relevant on this
machine at all — say so.

### Step 4: Confirm — every time, no exceptions

This is an outward-facing action (push + open a PR), so it gets the same explicit go-ahead as any
other push or PR in this session, regardless of how directly `coco-ship` was invoked. State plainly:

- Target repo and branch
- Whether a guard bypass will be used, and the **exact** reason string (not a placeholder)
- That this opens a PR against `main` — it does not push to `main` directly

Wait for a clear yes before Step 5. Invoking this skill is not itself that approval.

### Step 5: Push

```bash
git push -u origin <branch>
```

Only when Step 3 determined a bypass is needed:

```bash
GIT_GUARD_REASON="<specific, real reason>" git push -u origin <branch>
```

**Never** `--no-verify`. **Never** a plain `--force`. A `--force-with-lease` update to an
already-open PR's branch is allowed, but still gets its own confirmation, separate from Step 4's.

### Step 6: Open the PR

```bash
gh pr create --base main --head <branch> --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed and why>

## Test plan
<what was verified, or a checklist of what to verify>
EOF
)"
```

Keep the title under 70 characters. Put detail in the body, not the title.

### Step 7: Wait for CI

```bash
gh pr checks <n> --watch
```

Don't report done while checks are still pending. If a check fails, say so plainly with the failure,
don't retry blindly.

### Step 8: Report

State the PR URL, the CI result, and the mergeable/review-required status. Say plainly that merging is
the user's call — **this skill never merges and never self-approves.** If the PR author can't
self-approve (most repos), say that explicitly rather than implying the PR is ready to merge on its
own.

## Quick Reference

| Step | Action | Confirmation needed? |
|------|--------|----------------------|
| 1 | Preflight (refuse on main) | — |
| 2 | Commit | — |
| 3 | Detect guard need | — |
| 4 | State plan, ask | **Yes — always** |
| 5 | Push | (covered by Step 4) |
| 6 | Open PR | (covered by Step 4) |
| 7 | Wait for CI | — |
| 8 | Report | — |

## Common Mistakes

**Assuming the guard bypass is needed without checking**
- **Problem:** Sets `GIT_GUARD_REASON` on every push, even to private or allowlisted repos, or misses
  that the guard isn't even installed on this machine.
- **Fix:** Always run Step 3's checks; only set the env var when the repo is genuinely public and
  non-allowlisted.

**Treating skill invocation as approval**
- **Problem:** Runs Steps 5–6 immediately because the user said "ship this," without a distinct
  confirmation of the actual push/PR plan.
- **Fix:** Step 4 is a separate, explicit ask every time — state the repo, branch, guard reason (if
  any), and that a PR (not a direct push to main) will follow.

**Reporting success before CI resolves**
- **Problem:** Says "done" right after `gh pr create`, while checks are still `pending`.
- **Fix:** Step 7 watches until every check resolves, then Step 8 reports the real result.

## Red Flags

**Never:**
- Push to `main` or `master` directly, no matter how it's requested
- Use `--no-verify` or a plain `--force`
- Auto-merge or self-approve a PR
- Fabricate a `GIT_GUARD_REASON` instead of a specific, true one
- Skip Step 4's confirmation because the work "seems done"

**Always:**
- Refuse and redirect if invoked while on `main`/`master`
- Check whether the guard bypass is actually needed rather than assuming
- Get explicit confirmation before the push/PR step
- Wait for and report real CI status, not an assumed one

## Integration

**Formalizes:** Option 2 of `finishing-a-development-branch` ("Push and Create PR"), specialized for
repos carrying the corporate git-guard.

**Distinct from:** `commands/team/ship.md` (`/team:ship`, a full idea-to-product pipeline) and
`systems/gsd/skills/gsd-ship` (GSD milestone-scoped). Neither overlaps with this skill's narrower job
— shipping already-finished work through the guard and into a PR.

**Pairs with:** `using-git-worktrees` for cleanup after the PR merges (not handled by this skill).
