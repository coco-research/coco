#!/usr/bin/env bash
# `coco-gate githook install` and `remove`: the wrapper lands in the repo's hooks
# dir, a pre-commit hook that is already there is kept by chaining it, nothing
# that is not ours is overwritten, and `remove` puts the kept hook back. The
# hooks dir is scoped to the repo, a hook with a second link is refused, ours
# means byte-identical to what install wrote, and --dry-run --json reports the
# same plan without writing. One case commits through git itself, so the
# hooks-dir lookup is tested and not assumed. Throwaway repos and CLAUDE_HOME;
# no network.
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

# The hooks dir git itself names for repo $1, absolute. git before 2.31 has no
# --path-format, so fall back to the plain spelling resolved from the repo.
hooks_of() {
  if ( cd "$1" && git rev-parse --path-format=absolute --git-path hooks ) 2>/dev/null; then
    return 0
  fi
  ( cd "$1" && python3 -c 'import os, subprocess
out = subprocess.run(["git", "rev-parse", "--git-path", "hooks"],
                     stdout=subprocess.PIPE, text=True).stdout
print(os.path.abspath(out.strip()))' )
}

# The mode, spelled the same on both stat flavours.
mode() { python3 -c 'import os, sys; print(oct(os.stat(sys.argv[1]).st_mode & 0o777))' "$1"; }

# A stable snapshot of a hooks dir: names, modes, bytes, and symlink targets.
snapshot() {
  python3 - "$1" <<'PY'
import hashlib, os, sys
root = sys.argv[1]
for name in sorted(os.listdir(root)):
    path = os.path.join(root, name)
    st = os.lstat(path)
    if os.path.islink(path):
        print("%s link %s" % (name, os.readlink(path)))
    elif os.path.isfile(path):
        with open(path, "rb") as fh:
            print("%s file %s %s" % (name, oct(st.st_mode & 0o777),
                                     hashlib.sha256(fh.read()).hexdigest()))
    else:
        print("%s other %s" % (name, oct(st.st_mode & 0o777)))
PY
}

# Runs `coco-gate githook ...` inside repo $1; sets RC and OUT (stdout+stderr).
run() {
  local dir="$1"
  shift
  RC=0
  OUT="$( cd "$dir" && "$GATE" githook "$@" 2>&1 )" || RC=$?
}

# Runs `coco-gate githook ... --json` inside repo $1; sets RC, OUT (stdout) and ERR.
run_json() {
  local dir="$1"
  shift
  RC=0
  OUT="$( cd "$dir" && "$GATE" githook "$@" --json 2>"$T/json.err" )" || RC=$?
  ERR="$(cat "$T/json.err")"
}

# One field of the JSON object on stdin; true/false stay true/false.
jget() {
  python3 -c 'import json, sys
obj = json.load(sys.stdin)
for key in sys.argv[1:]:
    obj = obj.get(key, "")
print("true" if obj is True else "false" if obj is False else obj)' "$@"
}

# Field $2 of the JSON object in $1.
jfield() { printf '%s' "$1" | jget "$2"; }

# One line per op of the JSON object in $1: `rename A -> B` or `op path`.
ops_of() {
  printf '%s' "$1" | python3 -c 'import json, sys
for op in json.load(sys.stdin)["ops"]:
    if op["op"] == "rename":
        print("rename %s -> %s" % (op["from"], op["to"]))
    else:
        print("%s %s" % (op["op"], op["path"]))'
}

# Asserts the JSON in $1 is a refusal with reason $2; $3 names the case.
refused_json() {
  [ "$(jfield "$1" ok)" = "false" ] || fail "$3: ok is not false: $1"
  [ "$(jfield "$1" reason)" = "$2" ] \
    || fail "$3: expected reason $2, got $(jfield "$1" reason): $1"
  [ -n "$(jfield "$1" message)" ] || fail "$3: refusal has no message: $1"
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
LINE3="$(sed -n 3p "$H/pre-commit")"
case "$LINE3" in
  "# sha256: "*) ;;
  *) fail "1 the third line is not the sha256 line: $LINE3" ;;
esac
[ "${#LINE3}" -eq 74 ] || fail "1 the third line is not a 64-hex hash: $LINE3"
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

# --- 9. a hooks dir outside the repo is refused -----------------------------
R="$(repo nine)"
mkdir -p "$T/global-hooks"
git -C "$R" config core.hooksPath "$T/global-hooks"
BEFORE="$(ls -A "$T/global-hooks")"
run "$R" install
[ "$RC" -eq 1 ] || fail "9 a global core.hooksPath: expected exit 1, got $RC: $OUT"
run_json "$R" install
[ "$RC" -eq 1 ] || fail "9 a global core.hooksPath (json): expected exit 1, got $RC: $ERR"
refused_json "$OUT" hooks-dir-outside-repo "9 a global core.hooksPath"
[ "$(ls -A "$T/global-hooks")" = "$BEFORE" ] \
  || fail "9 install wrote into the global hooks dir: $(ls -A "$T/global-hooks")"
git -C "$R" config core.hooksPath .husky/_
run_json "$R" install
[ "$RC" -eq 1 ] || fail "9 an in-tree core.hooksPath: expected exit 1, got $RC: $ERR"
refused_json "$OUT" hooks-dir-outside-repo "9 an in-tree core.hooksPath"
[ ! -e "$R/.husky" ] || fail "9 install created .husky"
ok "9 a hooks dir outside the repo is refused, and nothing is created"

# --- 10. a hooks dir that is a symlink is refused ---------------------------
R="$(repo ten)"
H="$(hooks_of "$R")"
TARGET="$T/ten-target"
mkdir -p "$TARGET"
printf '#!/bin/sh\nexit 0\n' > "$TARGET/keep"
rm -rf "$H"
ln -s "$TARGET" "$H"
BEFORE="$(snapshot "$TARGET")"
run "$R" install
[ "$RC" -eq 1 ] || fail "10 a symlinked hooks dir: expected exit 1, got $RC: $OUT"
run_json "$R" install
[ "$RC" -eq 1 ] || fail "10 a symlinked hooks dir (json): expected exit 1, got $RC: $ERR"
refused_json "$OUT" hooks-dir-symlink "10 a symlinked hooks dir"
[ "$(snapshot "$TARGET")" = "$BEFORE" ] || fail "10 the symlink target changed"
ok "10 a hooks dir that is a symlink is refused and its target is untouched"

# --- 11. a wrapper that was edited is not ours ------------------------------
R="$(repo eleven)"
run "$R" install
[ "$RC" -eq 0 ] || fail "11 install: expected exit 0, got $RC: $OUT"
H="$(hooks_of "$R")"
printf '# a line somebody added\n' >> "$H/pre-commit"
cp "$H/pre-commit" "$T/eleven.1"
run "$R" remove
[ "$RC" -eq 1 ] || fail "11 remove an edited wrapper: expected exit 1, got $RC: $OUT"
run_json "$R" remove
[ "$RC" -eq 1 ] || fail "11 remove an edited wrapper (json): expected exit 1, got $RC: $ERR"
refused_json "$OUT" wrapper-changed "11 remove an edited wrapper"
cmp -s "$H/pre-commit" "$T/eleven.1" || fail "11 remove changed the edited wrapper"
run_json "$R" install
[ "$RC" -eq 1 ] || fail "11 install over an edited wrapper: expected exit 1, got $RC: $ERR"
refused_json "$OUT" wrapper-changed "11 install over an edited wrapper"
cmp -s "$H/pre-commit" "$T/eleven.1" || fail "11 install changed the edited wrapper"
ok "11 a wrapper with an extra line is refused by both commands and kept"

# --- 12. a hand-deleted wrapper does not leave the hook parked --------------
R="$(repo twelve)"
H="$(hooks_of "$R")"
cat > "$H/pre-commit" <<EOF
#!/bin/sh
printf '%s\n' "user" > "$T/twelve.ran"
exit 0
EOF
chmod 0755 "$H/pre-commit"
cp "$H/pre-commit" "$T/twelve.1"
MODE12="$(mode "$H/pre-commit")"
run "$R" install --chain
[ "$RC" -eq 0 ] || fail "12 install --chain: expected exit 0, got $RC: $OUT"
rm -f "$H/pre-commit"
run_json "$R" remove --dry-run
[ "$RC" -eq 0 ] || fail "12 remove after a hand-deleted wrapper: expected exit 0, got $RC: $ERR"
[ "$(jfield "$OUT" ok)" = "true" ] || fail "12 the dry run is not ok: $OUT"
[ "$(ops_of "$OUT")" = "rename $H/pre-commit.coco-chained -> $H/pre-commit" ] \
  || fail "12 the dry run plans: $(ops_of "$OUT")"
run "$R" remove
[ "$RC" -eq 0 ] || fail "12 remove with the wrapper gone: expected exit 0, got $RC: $OUT"
cmp -s "$H/pre-commit" "$T/twelve.1" || fail "12 the parked hook did not come back byte for byte"
[ "$(mode "$H/pre-commit")" = "$MODE12" ] || fail "12 the restored hook lost its mode"
[ ! -e "$H/pre-commit.coco-chained" ] || fail "12 pre-commit.coco-chained is still there"
run_json "$R" remove
[ "$RC" -eq 1 ] || fail "12 a second remove over a user hook: expected exit 1, got $RC: $ERR"
refused_json "$OUT" not-coco-wrapper "12 a second remove over a user hook"
ok "12 a hand-deleted wrapper: remove puts the parked hook back"

# --- 13. a hard-linked hook is refused -------------------------------------
R="$(repo thirteen)"
H="$(hooks_of "$R")"
printf '#!/bin/sh\nexit 0\n' > "$H/pre-commit"
chmod 0755 "$H/pre-commit"
ln "$H/pre-commit" "$T/thirteen-hard"
BEFORE="$(snapshot "$H")"
run "$R" install --chain
[ "$RC" -eq 1 ] || fail "13 a hard-linked hook: expected exit 1, got $RC: $OUT"
run_json "$R" install --chain
[ "$RC" -eq 1 ] || fail "13 a hard-linked hook (json): expected exit 1, got $RC: $ERR"
refused_json "$OUT" hardlinked-hook "13 a hard-linked hook"
[ "$(snapshot "$H")" = "$BEFORE" ] || fail "13 the hard-linked hook changed"
ok "13 a hook with a second hard link is refused and nothing changes"

# --- 14. --dry-run --json plans and writes nothing -------------------------
R="$(repo fourteen)"
H="$(hooks_of "$R")"
printf '#!/bin/sh\nexit 0\n' > "$H/pre-commit"
chmod 0755 "$H/pre-commit"
BEFORE="$(snapshot "$H")"
run_json "$R" install --dry-run
[ "$RC" -eq 1 ] || fail "14 install --dry-run over a user hook: expected exit 1, got $RC: $ERR"
refused_json "$OUT" existing-hook "14 install --dry-run over a user hook"
[ "$(jfield "$OUT" existing)" = "file" ] || fail "14 existing is not file: $OUT"
[ "$(jfield "$OUT" dry_run)" = "true" ] || fail "14 dry_run is not true: $OUT"
[ "$(snapshot "$H")" = "$BEFORE" ] || fail "14 the first dry run changed the hooks dir"
run_json "$R" install --chain --dry-run
[ "$RC" -eq 0 ] || fail "14 install --chain --dry-run: expected exit 0, got $RC: $ERR"
[ "$(jfield "$OUT" ok)" = "true" ] || fail "14 install --chain --dry-run: ok is not true: $OUT"
[ "$(jfield "$OUT" hooks_dir)" = "$H" ] || fail "14 hooks_dir is not $H: $OUT"
EXPECT="rename $H/pre-commit -> $H/pre-commit.coco-chained
write $H/pre-commit"
[ "$(ops_of "$OUT")" = "$EXPECT" ] \
  || fail "14 install --chain --dry-run plans: $(ops_of "$OUT")"
[ "$(snapshot "$H")" = "$BEFORE" ] || fail "14 the chain dry run changed the hooks dir"
run "$R" install --chain
[ "$RC" -eq 0 ] || fail "14 install --chain: expected exit 0, got $RC: $OUT"
AFTER="$(snapshot "$H")"
run_json "$R" remove --dry-run
[ "$RC" -eq 0 ] || fail "14 remove --dry-run: expected exit 0, got $RC: $ERR"
EXPECT="delete $H/pre-commit
rename $H/pre-commit.coco-chained -> $H/pre-commit"
[ "$(ops_of "$OUT")" = "$EXPECT" ] \
  || fail "14 remove --dry-run plans: $(ops_of "$OUT")"
[ "$(jfield "$OUT" existing)" = "coco-wrapper" ] \
  || fail "14 remove existing is not coco-wrapper: $OUT"
[ "$(snapshot "$H")" = "$AFTER" ] || fail "14 remove --dry-run changed the hooks dir"
ok "14 --dry-run plans the same ops as the real run and writes nothing"

# --- 15. install --chain then remove is a round trip -----------------------
R="$(repo fifteen)"
H="$(hooks_of "$R")"
printf '#!/bin/sh\nexit 7\n' > "$H/pre-commit"
chmod 0750 "$H/pre-commit"
BEFORE="$(snapshot "$H")"
run "$R" install --chain
[ "$RC" -eq 0 ] || fail "15 install --chain: expected exit 0, got $RC: $OUT"
RC=0
( cd "$R" && "$H/pre-commit" ) || RC=$?
[ "$RC" -eq 7 ] || fail "15 running the wrapper: expected the user hook's exit 7, got $RC"
run_json "$R" remove
[ "$RC" -eq 0 ] || fail "15 remove: expected exit 0, got $RC: $ERR"
[ "$(jfield "$OUT" ok)" = "true" ] || fail "15 the remove is not ok: $OUT"
EXPECT="delete $H/pre-commit
rename $H/pre-commit.coco-chained -> $H/pre-commit"
[ "$(ops_of "$OUT")" = "$EXPECT" ] || fail "15 remove plans: $(ops_of "$OUT")"
[ "$(snapshot "$H")" = "$BEFORE" ] || fail "15 the hooks dir is not back to its snapshot"
ok "15 a round trip leaves the hooks dir identical"

# --- 16. a parked hook with no pre-commit is one refusal, not a plain write --
R="$(repo sixteen)"
H="$(hooks_of "$R")"
cat > "$H/pre-commit" <<EOF
#!/bin/sh
printf '%s\n' "sixteen" > "$T/sixteen.ran"
exit 0
EOF
chmod 0755 "$H/pre-commit"
cp "$H/pre-commit" "$T/sixteen.1"
MODE16="$(mode "$H/pre-commit")"
run "$R" install --chain
[ "$RC" -eq 0 ] || fail "16 install --chain: expected exit 0, got $RC: $OUT"
rm -f "$H/pre-commit"
run_json "$R" install
[ "$RC" -eq 1 ] || fail "16 install after a hand-deleted wrapper: expected exit 1, got $RC: $ERR"
refused_json "$OUT" chained-name-taken "16 install after a hand-deleted wrapper"
[ ! -e "$H/pre-commit" ] || fail "16 the refusal wrote a pre-commit"
cmp -s "$H/pre-commit.coco-chained" "$T/sixteen.1" \
  || fail "16 the refusal changed the parked hook"
run "$R" remove
[ "$RC" -eq 0 ] || fail "16 remove: expected exit 0, got $RC: $OUT"
cmp -s "$H/pre-commit" "$T/sixteen.1" || fail "16 the parked hook did not come back byte for byte"
[ "$(mode "$H/pre-commit")" = "$MODE16" ] || fail "16 the restored hook lost its mode"
[ ! -e "$H/pre-commit.coco-chained" ] || fail "16 pre-commit.coco-chained is still there"
ok "16 a deleted wrapper over a parked hook is refused, and remove puts it back"

# --- 17. the installer leaves the repo's git hooks alone -------------------
R="$(repo seventeen)"
H="$(hooks_of "$R")"
BEFORE="$(snapshot "$H")"
H17="$T/home-seventeen"
mkdir -p "$H17" "$T/seventeen-managed"
for flags in "--core-only" "--core-only --workflow"; do
  RC=0
  ( cd "$R" && HOME="$H17" CLAUDE_HOME="$H17/.claude" \
      COCO_MANAGED_ROOT="$T/seventeen-managed" \
      bash "$ROOT/adapters/claude-code/install.sh" $flags ) \
    >"$T/seventeen.out" 2>&1 || RC=$?
  [ "$RC" -eq 0 ] || fail "17 install.sh $flags: expected exit 0, got $RC: $(tail -3 "$T/seventeen.out")"
done
[ "$(snapshot "$H")" = "$BEFORE" ] \
  || fail "17 the installer changed the repo's hooks dir: [$(snapshot "$H")] != [$BEFORE]"
[ ! -e "$H/pre-commit" ] || fail "17 the installer wrote a hook the repo never had"
ok "17 the installer writes no git hook into the repo it runs in"

echo "ok   coco-gate githook installs, chains, removes, and overwrites nothing"
