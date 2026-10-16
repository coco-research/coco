#!/usr/bin/env bash
# uninstall/install must not delete or update a directory that is not a
# coco-research/coco clone. Temp dirs only; no network.
set -euo pipefail

CLI="$(cd "$(dirname "$0")/.." && pwd)/bin/coco.js"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/home"

fail() { echo "FAIL: $1"; exit 1; }

# Leaves RC and stderr in $T/err. Non-zero is not a script failure.
coco() {
  RC=0
  HOME="$T/home" COCO_NO_UPDATE_CHECK=1 "$@" >"$T/out" 2>"$T/err" || RC=$?
}

# repo <dir> [origin]
repo() {
  mkdir -p "$1"
  git init -q "$1"
  printf '%s\n' '{"name":"cocosuperintelligence"}' > "$1/package.json"
  echo keep > "$1/keep.txt"
  if [ -n "${2:-}" ]; then git -C "$1" remote add origin "$2"; fi
}

# Commit and point a remote-tracking ref at HEAD so the clone has no local work.
settle() {
  git -C "$1" -c user.name=t -c user.email=t@t add -A
  if ! git -C "$1" diff --cached --quiet; then
    git -C "$1" -c user.name=t -c user.email=t@t commit -qm settled
  fi
  git -C "$1" update-ref refs/remotes/origin/main HEAD
}

# (a) plain dir named coco, with a file
mkdir -p "$T/home/.coco" "$T/a/coco"
echo '{}' > "$T/home/.coco/.update-check.json"
echo keep > "$T/a/coco/keep.txt"
coco bash -c 'cd "$1" && node "$2" uninstall' _ "$T/a" "$CLI"
[ "$RC" -eq 2 ] || fail "(a) uninstall exited $RC ($(cat "$T/err"))"
[ -f "$T/a/coco/keep.txt" ] || fail "(a) file was deleted"
grep -q "Nothing was deleted." "$T/err" || fail "(a) missing refusal ($(cat "$T/err"))"
[ -f "$T/home/.coco/.update-check.json" ] || fail "(a) update cache was deleted"

# (b) right package name, wrong origin
repo "$T/b" "https://github.com/someone/coco.git"
coco node "$CLI" uninstall "$T/b"
[ "$RC" -eq 2 ] || fail "(b) uninstall exited $RC ($(cat "$T/err"))"
[ -f "$T/b/keep.txt" ] || fail "(b) uninstall removed the dir"
repo "$T/b-install/coco" "https://github.com/someone/coco.git"
coco bash -c 'cd "$1" && node "$2" install' _ "$T/b-install" "$CLI"
[ "$RC" -eq 2 ] || fail "(b) install exited $RC ($(cat "$T/err"))"
[ -f "$T/b-install/coco/keep.txt" ] || fail "(b) install touched the dir"
[ "$(git -C "$T/b-install/coco" remote get-url origin)" = "https://github.com/someone/coco.git" ] || fail "(b) origin changed"

# (c) same, with no origin
repo "$T/c"
coco node "$CLI" uninstall "$T/c"
[ "$RC" -eq 2 ] || fail "(c) uninstall exited $RC ($(cat "$T/err"))"
[ -f "$T/c/keep.txt" ] || fail "(c) dir was removed"
# (c2) a global remote.origin.url must not stand in for the clone's own origin
printf '[remote "origin"]\n\turl = https://github.com/coco-research/coco.git\n' > "$T/home/.gitconfig"
coco node "$CLI" uninstall "$T/c"
rm -f "$T/home/.gitconfig"
[ "$RC" -eq 2 ] && [ -f "$T/c/keep.txt" ] && grep -q "origin could not be verified" "$T/err" || fail "(c2) global origin accepted (RC $RC: $(cat "$T/err"))"
repo "$T/c-install/coco"
coco bash -c 'cd "$1" && node "$2" install' _ "$T/c-install" "$CLI"
[ "$RC" -eq 2 ] || fail "(c) install exited $RC ($(cat "$T/err"))"
[ -f "$T/c-install/coco/keep.txt" ] || fail "(c) install touched the dir"

# (d) otherwise a real clone, but PATH has no git
repo "$T/d" "https://github.com/coco-research/coco.git"
mkdir -p "$T/path"
ln -s "$(command -v node)" "$T/path/node"
coco env PATH="$T/path" "$T/path/node" "$CLI" uninstall "$T/d"
[ "$RC" -eq 2 ] || fail "(d) uninstall exited $RC ($(cat "$T/err"))"
[ -f "$T/d/keep.txt" ] || fail "(d) dir was removed"
grep -q "Nothing was deleted." "$T/err" || fail "(d) missing refusal ($(cat "$T/err"))"

# (e) right name and origin, no local work: uninstall removes it
repo "$T/e" "https://github.com/coco-research/coco.git"
settle "$T/e"
coco node "$CLI" uninstall "$T/e"
[ "$RC" -eq 0 ] || fail "(e) uninstall exited $RC ($(cat "$T/err"))"
[ ! -e "$T/e" ] || fail "(e) clone was not removed"

# (f) other accepted spellings: scp form, port + credentials + mixed case, trailing slash
for o in "git@github.com:coco-research/coco.git" "ssh://git@GitHub.com:22/Coco-Research/coco" "https://u:t@github.com/coco-research/coco/"; do
  rm -rf "$T/f"; repo "$T/f" "$o"
  settle "$T/f"
  coco node "$CLI" uninstall "$T/f"
  [ "$RC" -eq 0 ] && [ ! -e "$T/f" ] || fail "(f) $o refused or not removed (RC $RC: $(cat "$T/err"))"
done

# (g) a regular file as the target: refuse with exit 2, never crash, file kept
echo keep > "$T/g"
coco node "$CLI" uninstall "$T/g"
[ "$RC" -eq 2 ] && [ -f "$T/g" ] || fail "(g) file target: RC $RC ($(cat "$T/err"))"

# (h) update on a wrong-origin clone: exit 2, origin untouched
repo "$T/h" "https://github.com/someone/coco.git"
coco node "$CLI" update "$T/h"
[ "$RC" -eq 2 ] || fail "(h) update exited $RC ($(cat "$T/err"))"
[ "$(git -C "$T/h" remote get-url origin)" = "https://github.com/someone/coco.git" ] || fail "(h) origin changed"

# (i) a linked worktree (.git is a file) of a real clone is accepted
repo "$T/i" "https://github.com/coco-research/coco.git"
settle "$T/i"
git -C "$T/i" worktree add -q "$T/iw" 2>/dev/null
[ -f "$T/iw/.git" ] || fail "(i) worktree .git is not a file"
coco node "$CLI" uninstall "$T/iw"
[ "$RC" -eq 0 ] && [ ! -e "$T/iw" ] || fail "(i) worktree clone refused or kept (RC $RC: $(cat "$T/err"))"

# (j) GIT_DIR pointing at a real coco clone must not uninstall a fork or a repo with no origin
repo "$T/j-real" "https://github.com/coco-research/coco.git"
settle "$T/j-real"
repo "$T/j-fork" "https://github.com/someone/coco.git"
coco env GIT_DIR="$T/j-real/.git" node "$CLI" uninstall "$T/j-fork"
[ "$RC" -eq 2 ] || fail "(j) fork with GIT_DIR exited $RC ($(cat "$T/err"))"
[ -f "$T/j-fork/keep.txt" ] || fail "(j) fork was removed"
repo "$T/j-none"
coco env GIT_DIR="$T/j-real/.git" node "$CLI" uninstall "$T/j-none"
[ "$RC" -eq 2 ] || fail "(j) no-origin with GIT_DIR exited $RC ($(cat "$T/err"))"
[ -f "$T/j-none/keep.txt" ] || fail "(j) no-origin was removed"

# (k) uncommitted file: refuse unless --force
repo "$T/k" "https://github.com/coco-research/coco.git"
settle "$T/k"
echo dirty > "$T/k/dirty.txt"
coco node "$CLI" uninstall "$T/k"
[ "$RC" -eq 2 ] || fail "(k) dirty exited $RC ($(cat "$T/err"))"
[ -f "$T/k/dirty.txt" ] || fail "(k) dirty was removed"
grep -q "uncommitted" "$T/err" || fail "(k) message ($(cat "$T/err"))"
grep -q -- "--force" "$T/err" || fail "(k) message missing --force ($(cat "$T/err"))"
coco node "$CLI" uninstall --force "$T/k"
[ "$RC" -eq 0 ] && [ ! -e "$T/k" ] || fail "(k) --force did not remove (RC $RC: $(cat "$T/err"))"

# (l) stash: refuse unless --force
repo "$T/l" "https://github.com/coco-research/coco.git"
settle "$T/l"
echo stashed >> "$T/l/keep.txt"
git -C "$T/l" -c user.name=t -c user.email=t@t stash push -q -m l
coco node "$CLI" uninstall "$T/l"
[ "$RC" -eq 2 ] && [ -f "$T/l/keep.txt" ] || fail "(l) stash exited $RC ($(cat "$T/err"))"
grep -q "stash" "$T/err" || fail "(l) message ($(cat "$T/err"))"
grep -q -- "--force" "$T/err" || fail "(l) message missing --force ($(cat "$T/err"))"
coco node "$CLI" uninstall "$T/l" --force
[ "$RC" -eq 0 ] && [ ! -e "$T/l" ] || fail "(l) --force did not remove (RC $RC: $(cat "$T/err"))"

# (m) unpushed commit: push to a bare repo, then point origin at coco-research, then commit again
git init -q --bare "$T/m.git"
repo "$T/m" "$T/m.git"
git -C "$T/m" -c user.name=t -c user.email=t@t add -A
git -C "$T/m" -c user.name=t -c user.email=t@t commit -qm base
git -C "$T/m" push -q -u origin HEAD
git -C "$T/m" config remote.origin.url "https://github.com/coco-research/coco.git"
echo local >> "$T/m/keep.txt"
git -C "$T/m" -c user.name=t -c user.email=t@t add -A
git -C "$T/m" -c user.name=t -c user.email=t@t commit -qm local
coco node "$CLI" uninstall "$T/m"
[ "$RC" -eq 2 ] && [ -f "$T/m/keep.txt" ] || fail "(m) unpushed exited $RC ($(cat "$T/err"))"
grep -q "unpushed" "$T/err" || fail "(m) message ($(cat "$T/err"))"
grep -q -- "--force" "$T/err" || fail "(m) message missing --force ($(cat "$T/err"))"
coco node "$CLI" uninstall --force "$T/m"
[ "$RC" -eq 0 ] && [ ! -e "$T/m" ] || fail "(m) --force did not remove (RC $RC: $(cat "$T/err"))"

# (n) a .git file that points at another repo's gitdir is refused
repo "$T/n-real" "https://github.com/coco-research/coco.git"
settle "$T/n-real"
mkdir -p "$T/n"
printf '%s\n' '{"name":"cocosuperintelligence"}' > "$T/n/package.json"
echo data > "$T/n/data.txt"
printf 'gitdir: %s\n' "$T/n-real/.git" > "$T/n/.git"
coco node "$CLI" uninstall "$T/n"
[ "$RC" -eq 2 ] || fail "(n) redirect exited $RC ($(cat "$T/err"))"
grep -q "toplevel is not this directory" "$T/err" || fail "(n) message ($(cat "$T/err"))"
[ -f "$T/n/data.txt" ] || fail "(n) redirect was removed"
[ -d "$T/n-real/.git" ] || fail "(n) real gitdir was removed"

# (o) install/update into an empty ./coco clones; it does not use uninstall wording
mkdir -p "$T/o/coco" "$T/obin"
cat > "$T/obin/git" << EOF
#!/bin/bash
printf '%s\n' "\$*" >> "$T/o/git.log"
exit 0
EOF
chmod +x "$T/obin/git"
coco env PATH="$T/obin:$PATH" bash -c 'cd "$1" && node "$2" install' _ "$T/o" "$CLI"
grep -q "Nothing was deleted" "$T/err" && fail "(o) install used uninstall wording ($(cat "$T/err"))" || true
grep -q '^clone ' "$T/o/git.log" || fail "(o) install did not clone ($(cat "$T/err"))"
: > "$T/o/git.log"
coco env PATH="$T/obin:$PATH" node "$CLI" update "$T/o/coco"
grep -q "Nothing was deleted" "$T/err" && fail "(o) update used uninstall wording ($(cat "$T/err"))" || true
grep -q '^clone ' "$T/o/git.log" || fail "(o) update did not clone ($(cat "$T/err"))"

# (u) the CLI's own .update-check.json inside a clean clone is not "local work"
repo "$T/j" "https://github.com/coco-research/coco.git"
git -C "$T/j" -c user.name=t -c user.email=t@t add -A && git -C "$T/j" -c user.name=t -c user.email=t@t commit -qm j
git -C "$T/j" update-ref refs/remotes/origin/main HEAD
echo '{}' > "$T/j/.update-check.json"
coco node "$CLI" uninstall "$T/j"
[ "$RC" -eq 0 ] && [ ! -e "$T/j" ] || fail "(u) cache-only clone refused (RC $RC: $(cat "$T/err"))"

# (p) git status exiting 128 is a check that could not run: keep unless --force
repo "$T/p" "https://github.com/coco-research/coco.git"
settle "$T/p"
REALGIT=$(command -v git)
mkdir -p "$T/pbin"
cat > "$T/pbin/git" << EOF
#!/bin/bash
for a in "\$@"; do
  [ "\$a" = status ] && exit 128
done
exec "$REALGIT" "\$@"
EOF
chmod +x "$T/pbin/git"
coco env PATH="$T/pbin:$PATH" node "$CLI" uninstall "$T/p"
[ "$RC" -eq 2 ] || fail "(p) status 128 exited $RC ($(cat "$T/err"))"
[ -d "$T/p" ] || fail "(p) clone was removed"
grep -q "could not run" "$T/err" || fail "(p) message ($(cat "$T/err"))"
coco env PATH="$T/pbin:$PATH" node "$CLI" uninstall --force "$T/p"
[ "$RC" -eq 0 ] && [ ! -e "$T/p" ] || fail "(p) --force did not remove (RC $RC: $(cat "$T/err"))"

# (q) run('git') keeps GIT_SSH_COMMAND and drops repo/config redirects
mkdir -p "$T/q/coco" "$T/qbin"
cat > "$T/qbin/git" << EOF
#!/bin/bash
{
  printf '%s\n' "GIT_SSH_COMMAND=\${GIT_SSH_COMMAND-}"
  printf '%s\n' "GIT_DIR=\${GIT_DIR-unset}"
  printf '%s\n' "GIT_CONFIG_KEY_0=\${GIT_CONFIG_KEY_0-unset}"
  printf '%s\n' "GIT_CONFIG_VALUE_0=\${GIT_CONFIG_VALUE_0-unset}"
} > "$T/q/env"
exit 0
EOF
chmod +x "$T/qbin/git"
coco env PATH="$T/qbin:$PATH" \
  GIT_SSH_COMMAND="ssh -o BatchMode=yes" \
  GIT_DIR="/tmp/not-this-repo" \
  GIT_CONFIG_KEY_0="core.sshCommand" \
  GIT_CONFIG_VALUE_0="evil" \
  bash -c 'cd "$1" && node "$2" install' _ "$T/q" "$CLI"
grep -qx 'GIT_SSH_COMMAND=ssh -o BatchMode=yes' "$T/q/env" || fail "(q) GIT_SSH_COMMAND dropped ($(cat "$T/q/env" 2>/dev/null))"
grep -qx 'GIT_DIR=unset' "$T/q/env" || fail "(q) GIT_DIR survived ($(cat "$T/q/env"))"
grep -qx 'GIT_CONFIG_KEY_0=unset' "$T/q/env" || fail "(q) GIT_CONFIG_KEY_0 survived ($(cat "$T/q/env"))"
grep -qx 'GIT_CONFIG_VALUE_0=unset' "$T/q/env" || fail "(q) GIT_CONFIG_VALUE_0 survived ($(cat "$T/q/env"))"

# (r) untracked si-commands/ in a clean clone is not local work
repo "$T/r" "https://github.com/coco-research/coco.git"
settle "$T/r"
mkdir -p "$T/r/si-commands"
echo '# SI' > "$T/r/si-commands/SI-Decide.md"
coco node "$CLI" uninstall "$T/r"
[ "$RC" -eq 0 ] && [ ! -e "$T/r" ] || fail "(r) si-commands clone refused (RC $RC: $(cat "$T/err"))"

# (s) detached HEAD at a tagged commit, no remote-tracking ref: the pin is not local work
repo "$T/s" "https://github.com/coco-research/coco.git"
git -C "$T/s" -c user.name=t -c user.email=t@t add -A
git -C "$T/s" -c user.name=t -c user.email=t@t commit -qm tagged
git -C "$T/s" tag v9.9.9
git -C "$T/s" checkout -q --detach v9.9.9
git -C "$T/s" for-each-ref --format='%(refname:short)' refs/heads | xargs git -C "$T/s" branch -qD  # a tag clone has no local branch
coco node "$CLI" uninstall "$T/s"
[ "$RC" -eq 0 ] && [ ! -e "$T/s" ] || fail "(s) tagged detached refused (RC $RC: $(cat "$T/err"))"

# (s2) a commit on the pin that the user tagged locally (not a release tag) is still local work
repo "$T/s2" "https://github.com/coco-research/coco.git"
git -C "$T/s2" -c user.name=t -c user.email=t@t add -A && git -C "$T/s2" -c user.name=t -c user.email=t@t commit -qm tagged
git -C "$T/s2" tag v9.9.9 && git -C "$T/s2" checkout -q --detach v9.9.9
git -C "$T/s2" for-each-ref --format='%(refname:short)' refs/heads | xargs git -C "$T/s2" branch -qD
echo mine >> "$T/s2/keep.txt" && git -C "$T/s2" -c user.name=t -c user.email=t@t commit -qam mine && git -C "$T/s2" tag wip
coco node "$CLI" uninstall "$T/s2"
[ "$RC" -eq 2 ] && [ -f "$T/s2/keep.txt" ] || fail "(s2) locally tagged commit deleted (RC $RC: $(cat "$T/err"))"

# (v) update on a detached pin with a local commit: refuse before the forced checkout, nothing changed
repo "$T/v" "https://github.com/coco-research/coco.git"
git -C "$T/v" -c user.name=t -c user.email=t@t add -A && git -C "$T/v" -c user.name=t -c user.email=t@t commit -qm tagged
git -C "$T/v" tag pinned && git -C "$T/v" checkout -q --detach pinned
echo extra >> "$T/v/keep.txt" && git -C "$T/v" -c user.name=t -c user.email=t@t commit -qam extra
before=$(git -C "$T/v" rev-parse HEAD)
coco node "$CLI" update "$T/v"
[ "$RC" -eq 2 ] && [ "$(git -C "$T/v" rev-parse HEAD)" = "$before" ] && grep -q "Nothing was changed" "$T/err" || fail "(v) update with local commit: RC $RC ($(cat "$T/err"))"

# (w) status.showUntrackedFiles=no must not hide untracked local work
repo "$T/w" "https://github.com/coco-research/coco.git"
settle "$T/w"
git -C "$T/w" config status.showUntrackedFiles no
echo mine > "$T/w/notes.txt"
coco node "$CLI" uninstall "$T/w"
[ "$RC" -eq 2 ] && [ -f "$T/w/notes.txt" ] || fail "(w) hidden untracked file: RC $RC ($(cat "$T/err"))"

# (j2) the guard's own git calls never see an inherited GIT_DIR (shim records it)
mkdir -p "$T/shim"
printf '#!/bin/sh\necho "GIT_DIR=${GIT_DIR:-}" >> "%s"\nexec "%s" "$@"\n' "$T/shim.log" "$(command -v git)" > "$T/shim/git"
chmod +x "$T/shim/git"
repo "$T/j2" "https://github.com/coco-research/coco.git"
settle "$T/j2"
coco env PATH="$T/shim:$PATH" GIT_DIR="$T/j-real/.git" node "$CLI" uninstall "$T/j2"
[ -s "$T/shim.log" ] || fail "(j2) shim never ran"
! grep -q "GIT_DIR=." "$T/shim.log" || fail "(j2) GIT_DIR leaked into a guard git call"

# (t) one commit on top of that detached tag: refuse unless --force
repo "$T/t" "https://github.com/coco-research/coco.git"
git -C "$T/t" -c user.name=t -c user.email=t@t add -A
git -C "$T/t" -c user.name=t -c user.email=t@t commit -qm tagged
git -C "$T/t" tag pinned
git -C "$T/t" checkout -q --detach pinned
echo extra >> "$T/t/keep.txt"
git -C "$T/t" -c user.name=t -c user.email=t@t add -A
git -C "$T/t" -c user.name=t -c user.email=t@t commit -qm extra
coco node "$CLI" uninstall "$T/t"
[ "$RC" -eq 2 ] && [ -f "$T/t/keep.txt" ] || fail "(t) detached commit exited $RC ($(cat "$T/err"))"
grep -q "unpushed" "$T/err" || fail "(t) message ($(cat "$T/err"))"
grep -q -- "--force" "$T/err" || fail "(t) message missing --force ($(cat "$T/err"))"
coco node "$CLI" uninstall --force "$T/t"
[ "$RC" -eq 0 ] && [ ! -e "$T/t" ] || fail "(t) --force did not remove (RC $RC: $(cat "$T/err"))"

# (x) update keeps untracked Coco state on a clean detached pin
# const PINNED_TAG = 'v' + PKG_VERSION; PKG_VERSION is package.json's version.
PINNED_TAG="$(sed -n "s/^const PINNED_TAG = '\\([^']*\\)'.*/\\1/p" "$CLI")$(sed -n 's/^[[:space:]]*"version": "\([^"]*\)".*/\1/p' "$(dirname "$CLI")/../package.json" | head -1)"
[ -n "$PINNED_TAG" ] || fail "(x) could not read PINNED_TAG"
repo "$T/x" "https://github.com/coco-research/coco.git"
git -C "$T/x" -c user.name=t -c user.email=t@t add -A
git -C "$T/x" -c user.name=t -c user.email=t@t commit -qm tagged
git -C "$T/x" tag "$PINNED_TAG"
git -C "$T/x" checkout -q --detach "$PINNED_TAG"
git -C "$T/x" for-each-ref --format='%(refname:short)' refs/heads | xargs git -C "$T/x" branch -qD  # a tag clone has no local branch
mkdir -p "$T/x/knowledge"
echo note > "$T/x/knowledge/note.md"
echo token > "$T/x/m0-token"
REALGIT=$(command -v git)
mkdir -p "$T/xbin"
cat > "$T/xbin/git" << EOF
#!/bin/bash
for a in "\$@"; do
  [ "\$a" = fetch ] && exit 0
done
exec "$REALGIT" "\$@"
EOF
chmod +x "$T/xbin/git"
coco env PATH="$T/xbin:$PATH" node "$CLI" update "$T/x"
[ "$RC" -eq 0 ] || fail "(x) update exited $RC ($(cat "$T/err"))"
[ -f "$T/x/knowledge/note.md" ] && [ -f "$T/x/m0-token" ] || fail "(x) untracked state removed"
[ "$(git -C "$T/x" rev-parse HEAD)" = "$(git -C "$T/x" rev-parse "$PINNED_TAG^{commit}")" ] || fail "(x) HEAD is not the tag commit"
coco node "$CLI" uninstall "$T/x"
[ "$RC" -eq 2 ] && [ -f "$T/x/knowledge/note.md" ] || fail "(x) uninstall exited $RC ($(cat "$T/err"))"

# (y) a global url.<official>.insteadOf alias must not make a foreign origin look official
repo "$T/y" "https://github.com/someone/coco.git"
settle "$T/y"
printf '[url "https://github.com/coco-research/coco.git"]\n\tinsteadOf = https://github.com/someone/coco.git\n' > "$T/home/.gitconfig"
coco node "$CLI" uninstall "$T/y"
rm -f "$T/home/.gitconfig"
[ "$RC" -eq 2 ] && [ -f "$T/y/keep.txt" ] || fail "(y) insteadOf origin accepted (RC $RC: $(cat "$T/err"))"

# (z) --force never bypasses the clone check
coco node "$CLI" uninstall --force "$T/b"
[ "$RC" -eq 2 ] && [ -f "$T/b/keep.txt" ] || fail "(z) --force removed wrong origin (RC $RC: $(cat "$T/err"))"
coco node "$CLI" uninstall --force "$T/c"
[ "$RC" -eq 2 ] && [ -f "$T/c/keep.txt" ] || fail "(z) --force removed no-origin (RC $RC: $(cat "$T/err"))"

echo "PASS: clone guard refuses non-clones and removes a real one"
