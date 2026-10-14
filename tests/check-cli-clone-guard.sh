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

# (e) right name and origin: uninstall removes it
repo "$T/e" "https://github.com/coco-research/coco.git"
coco node "$CLI" uninstall "$T/e"
[ "$RC" -eq 0 ] || fail "(e) uninstall exited $RC ($(cat "$T/err"))"
[ ! -e "$T/e" ] || fail "(e) clone was not removed"

# (f) other accepted spellings: scp form, port + credentials + mixed case, trailing slash
for o in "git@github.com:coco-research/coco.git" "ssh://git@GitHub.com:22/Coco-Research/coco" "https://u:t@github.com/coco-research/coco/"; do
  rm -rf "$T/f"; repo "$T/f" "$o"
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
git -C "$T/i" -c user.name=t -c user.email=t@t add -A && git -C "$T/i" -c user.name=t -c user.email=t@t commit -qm i
git -C "$T/i" worktree add -q "$T/iw" 2>/dev/null
[ -f "$T/iw/.git" ] || fail "(i) worktree .git is not a file"
coco node "$CLI" uninstall "$T/iw"
[ "$RC" -eq 0 ] && [ ! -e "$T/iw" ] || fail "(i) worktree clone refused or kept (RC $RC: $(cat "$T/err"))"

echo "PASS: clone guard refuses non-clones and removes a real one"
