#!/usr/bin/env bash
# `coco-gate githook install` and `remove`: the wrapper lands in the repo's hooks
# dir, a pre-commit hook that is already there is kept by chaining it, nothing
# that is not ours is overwritten, and `remove` puts the kept hook back. The last
# case commits through git itself, so the hooks-dir lookup is tested and not
# assumed. Throwaway repos and CLAUDE_HOME; no network.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$ROOT/bin/coco-gate"
HOOK_SRC="$ROOT/hooks/coco-workflow-pre-commit.sh"
[ -x "$GATE" ] || { echo "FAIL missing $GATE" >&2; exit 1; }
[ -f "$HOOK_SRC" ] || { echo "FAIL missing $HOOK_SRC" >&2; exit 1; }

T="$(mktemp -d)"
trap 'rc=$?; rm -rf "$T"; exit $rc' EXIT
WORK="$T/work"
mkdir -p "$WORK"

export HOME="$T/home"
export LC_ALL=C
export GIT_CONFIG_NOSYSTEM=1
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@example.test
export GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@example.test
export GIT_TERMINAL_PROMPT=0
unset GITHUB_REPOSITORY SSH_AUTH_SOCK SSH_AGENT_PID
mkdir -p "$HOME"
git config --global init.defaultBranch main
git config --global commit.gpgsign false

ok() { echo "ok   $1"; }
fail() { echo "FAIL $1" >&2; exit 1; }

# The pre-commit link a --workflow install makes, in a throwaway claude_home.
export CLAUDE_HOME="$T/claude"
mkdir -p "$CLAUDE_HOME/coco/hooks"
ln -s "$HOOK_SRC" "$CLAUDE_HOME/coco/hooks/coco-workflow-pre-commit.sh"

# A fresh repo; prints its path.
repo() {
  mkdir -p "$WORK/$1"
  git init -q "$WORK/$1"
  echo "$WORK/$1"
}

# The hooks dir git itself names for repo $1.
hooks_of() { ( cd "$1" && git rev-parse --path-format=absolute --git-path hooks ); }

# The mode, spelled the same on both stat flavours.
mode() { python3 -c 'import os, sys; print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' "$1"; }

# Runs `coco-gate githook ...` inside repo $1; sets RC and OUT (stdout+stderr).
run() {
  local dir="$1"
  shift
  RC=0
  OUT="$( cd "$dir" && "$GATE" githook "$@" 2>&1 )" || RC=$?
}

# --- 1. a repo with no pre-commit gets the wrapper --------------------------
R="$(repo one)"
H="$(hooks_of "$R")"
BEFORE="$(ls -A "$H")"
run "$R" install
[ "$RC" -eq 0 ] || fail "1 install: expected exit 0, got $RC: $OUT"
[ -f "$H/pre-commit" ] || fail "1 no pre-commit in $H"
[ -x "$H/pre-commit" ] || fail "1 pre-commit is not executable"
[ "$(sed -n 2p "$H/pre-commit")" = "# coco-workflow pre-commit wrapper" ] \
  || fail "1 the second line is not the marker: $(sed -n 2p "$H/pre-commit")"
( cd "$R" && "$H/pre-commit" ) || fail "1 the wrapper did not exit 0"
cp "$H/pre-commit" "$T/wrapper.1"
run "$R" install
[ "$RC" -eq 0 ] || fail "1 second install: expected exit 0, got $RC: $OUT"
case "$OUT" in *"already installed"*) ;; *) fail "1 second install: no already-installed line: $OUT" ;; esac
cmp -s "$H/pre-commit" "$T/wrapper.1" || fail "1 the second install changed pre-commit"
ok "1 install writes the wrapper once and says already installed after that"

# --- 2. remove takes it back out --------------------------------------------
run "$R" remove
[ "$RC" -eq 0 ] || fail "2 remove: expected exit 0, got $RC: $OUT"
[ ! -e "$H/pre-commit" ] || fail "2 remove left pre-commit behind"
[ "$(ls -A "$H")" = "$BEFORE" ] || fail "2 the hooks dir listing changed: [$BEFORE] != [$(ls -A "$H")]"
ok "2 remove deletes the wrapper and leaves the hooks dir as it was"

# --- 3. a user hook is never overwritten without --chain --------------------
R="$(repo three)"
H="$(hooks_of "$R")"
cat > "$H/pre-commit" <<EOF
#!/bin/sh
printf '%s\n' "\$*" > "$T/args"
exit 3
EOF
chmod 0755 "$H/pre-commit"
cp "$H/pre-commit" "$T/user-hook.1"
USER_MODE="$(mode "$H/pre-commit")"
run "$R" install
[ "$RC" -eq 1 ] || fail "3 install over a user hook: expected exit 1, got $RC: $OUT"
case "$OUT" in *"already exists"*) ;; *) fail "3 install over a user hook: no already-exists line: $OUT" ;; esac
cmp -s "$H/pre-commit" "$T/user-hook.1" || fail "3 install changed the user hook"
[ "$(mode "$H/pre-commit")" = "$USER_MODE" ] || fail "3 the user hook lost its mode"
[ ! -e "$H/pre-commit.coco-chained" ] || fail "3 install without --chain made a chained file"
ok "3 install without --chain refuses and leaves the user hook alone"

# --- 4. --chain parks the user hook and runs it after the warning -----------
run "$R" install --chain
[ "$RC" -eq 0 ] || fail "4 install --chain: expected exit 0, got $RC: $OUT"
[ -f "$H/pre-commit.coco-chained" ] || fail "4 no pre-commit.coco-chained"
cmp -s "$H/pre-commit.coco-chained" "$T/user-hook.1" || fail "4 the chained copy differs from the user hook"
[ "$(mode "$H/pre-commit.coco-chained")" = "$USER_MODE" ] || fail "4 the chained copy lost the mode"
rm -f "$T/args"
RC=0
( cd "$R" && "$H/pre-commit" a b ) || RC=$?
[ "$RC" -eq 3 ] || fail "4 running the wrapper: expected exit 3, got $RC"
[ "$(cat "$T/args" 2>/dev/null)" = "a b" ] || fail "4 the user hook saw '$(cat "$T/args" 2>/dev/null)'"
ok "4 install --chain keeps the user hook, and its exit code decides"

# --- 5. with coco uninstalled the chained hook still runs -------------------
R2="$(repo five)"
H2="$(hooks_of "$R2")"
run "$R2" install
[ "$RC" -eq 0 ] || fail "5 install in a second repo: expected exit 0, got $RC: $OUT"
rm -f "$CLAUDE_HOME/coco/hooks/coco-workflow-pre-commit.sh"
rm -f "$T/args"
RC=0
( cd "$R" && "$H/pre-commit" a b ) || RC=$?
[ "$RC" -eq 3 ] || fail "5 with coco gone the chained hook must still decide: expected 3, got $RC"
[ "$(cat "$T/args" 2>/dev/null)" = "a b" ] || fail "5 the chained hook did not run with coco gone"
RC=0
( cd "$R2" && "$H2/pre-commit" ) || RC=$?
[ "$RC" -eq 0 ] || fail "5 an unchained wrapper with coco gone: expected exit 0, got $RC"
ok "5 with coco uninstalled: chained runs and decides, unchained exits 0"

# --- 6. remove puts the user hook back where it was -------------------------
run "$R" remove
[ "$RC" -eq 0 ] || fail "6 remove: expected exit 0, got $RC: $OUT"
[ -f "$H/pre-commit" ] || fail "6 nothing at pre-commit after remove"
[ ! -e "$H/pre-commit.coco-chained" ] || fail "6 pre-commit.coco-chained is still there"
cmp -s "$H/pre-commit" "$T/user-hook.1" || fail "6 the restored hook differs from the user hook"
[ "$(mode "$H/pre-commit")" = "$USER_MODE" ] || fail "6 the restored hook lost the mode"
ok "6 remove puts the user hook back and drops the chained copy"

# --- 7. refusals change nothing ---------------------------------------------
export CLAUDE_HOME="$T/claude-bare"
mkdir -p "$CLAUDE_HOME/coco/hooks"
R="$(repo seven)"
H="$(hooks_of "$R")"
BEFORE="$(ls -A "$H")"
run "$R" install
[ "$RC" -eq 1 ] || fail "7 without the coco hook: expected exit 1, got $RC: $OUT"
case "$OUT" in *"--workflow"*) ;; *) fail "7 without the coco hook: no hint about the installer: $OUT" ;; esac
[ "$(ls -A "$H")" = "$BEFORE" ] || fail "7 install wrote something without the coco hook"
export CLAUDE_HOME="$T/claude"
ln -sfn "$HOOK_SRC" "$CLAUDE_HOME/coco/hooks/coco-workflow-pre-commit.sh"
R="$(repo seven-b)"
H="$(hooks_of "$R")"
printf '#!/bin/sh\nexit 0\n' > "$H/pre-commit"
printf '#!/bin/sh\nexit 0\n' > "$H/pre-commit.coco-chained"
chmod 0755 "$H/pre-commit" "$H/pre-commit.coco-chained"
cp "$H/pre-commit" "$T/seven-pre.1"
cp "$H/pre-commit.coco-chained" "$T/seven-chain.1"
run "$R" install --chain
[ "$RC" -eq 1 ] || fail "7 with pre-commit.coco-chained present: expected exit 1, got $RC: $OUT"
cmp -s "$H/pre-commit" "$T/seven-pre.1" || fail "7 the refusal changed pre-commit"
cmp -s "$H/pre-commit.coco-chained" "$T/seven-chain.1" \
  || fail "7 the refusal changed pre-commit.coco-chained"
ok "7 a missing coco hook and a taken chained name are both refused with no change"

# --- 8. a real commit goes through the wrapper ------------------------------
R="$(repo eight)"
H="$(hooks_of "$R")"
printf '#!/bin/sh\nexit 3\n' > "$H/pre-commit"
chmod 0755 "$H/pre-commit"
run "$R" install --chain
[ "$RC" -eq 0 ] || fail "8 install --chain: expected exit 0, got $RC: $OUT"
RC=0
git -C "$R" -c user.name=t -c user.email=t@example.test commit --allow-empty -qm t || RC=$?
[ "$RC" -ne 0 ] || fail "8 a chained hook exiting 3 did not stop the commit"
run "$R" remove
[ "$RC" -eq 0 ] || fail "8 remove: expected exit 0, got $RC: $OUT"
printf '#!/bin/sh\nexit 0\n' > "$H/pre-commit"
chmod 0755 "$H/pre-commit"
git -C "$R" -c user.name=t -c user.email=t@example.test commit --allow-empty -qm t \
  || fail "8 the commit failed with a user hook exiting 0"
ok "8 a real commit runs the wrapper git found, and remove puts the hook back"

echo "ok   coco-gate githook installs, chains, removes, and overwrites nothing"
