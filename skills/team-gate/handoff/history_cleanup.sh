#!/usr/bin/env bash
# Pre-PR history cleanup for feat/team-gate-retrofit. Run only when no agent is
# working in the worktree. It squashes the five commits that the round-1
# arch_gate fixture generator made by accident (196fe89..5dcce01, parented on
# 3e181ff) into one honestly named commit and re-parents every later commit on
# top of it with git commit-tree, so every tree is byte-identical to the
# original and no replay or conflict resolution happens. The old head is kept
# under refs/backup/ until the pull request merges.
set -u -o pipefail
WT=~/projects/coco/.claude/worktrees/team-gate-retrofit
cd "$WT" || exit 2
BASE=3e181ff
JUNK_TIP=5dcce01
OLD_HEAD=$(git rev-parse HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
[ "$BRANCH" = feat/team-gate-retrofit ] || { echo "not on feat/team-gate-retrofit"; exit 2; }
git diff --quiet && git diff --cached --quiet || { echo "tracked changes present; refusing"; exit 2; }
git update-ref refs/backup/team-gate-retrofit-before-cleanup "$OLD_HEAD"

# One commit carrying the junk range's tree, honestly described.
SQUASH=$(GIT_AUTHOR_DATE="$(git log -1 --format=%aI "$JUNK_TIP")" GIT_COMMITTER_DATE="$(git log -1 --format=%cI "$JUNK_TIP")" \
  git commit-tree "$JUNK_TIP^{tree}" -p "$BASE" <<'MSG'
chore(team-gate): round-one arch_gate draft, superseded by a5298a1

Five commits from the first arch_gate fixture generator landed in the
main worktree by mistake with fixture-shaped messages. They are squashed
here into one commit so the history reads honestly; the draft script and
its static fixtures were rewritten in a5298a1 and later removed, and the
tree at the head of this branch is unchanged by the squash.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
)
NEW_PARENT=$SQUASH
for c in $(git rev-list --reverse "$JUNK_TIP..$OLD_HEAD"); do
  msg=$(git log -1 --format=%B "$c")
  NEW_PARENT=$(GIT_AUTHOR_NAME="$(git log -1 --format=%an "$c")" GIT_AUTHOR_EMAIL="$(git log -1 --format=%ae "$c")" \
    GIT_AUTHOR_DATE="$(git log -1 --format=%aI "$c")" GIT_COMMITTER_DATE="$(git log -1 --format=%cI "$c")" \
    git commit-tree "$c^{tree}" -p "$NEW_PARENT" -m "$msg")
done
git update-ref refs/heads/feat/team-gate-retrofit "$NEW_PARENT" "$OLD_HEAD"
git reset -q --soft "$NEW_PARENT"   # index and working tree untouched; trees are identical
echo "old head $OLD_HEAD"
echo "new head $NEW_PARENT"
echo "tree diff (must be empty):"; git diff --stat "$OLD_HEAD" "$NEW_PARENT"
echo "commits after base: $(git rev-list --count "$BASE..HEAD") (expect $(( $(git rev-list --count "$JUNK_TIP..$OLD_HEAD") + 1 )))"
git log --oneline "$BASE..HEAD" | tail -3
