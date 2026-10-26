#!/usr/bin/env bash
# The coco-workflow in-session hooks: while the branch's gate is size=feature
# and its plan sign-off does not verify with the work tree's rules, the
# PreToolUse hook refuses Edit/Write/MultiEdit/NotebookEdit on code paths with
# one line naming the pending stage, and the UserPromptSubmit hook says the
# stage and the next artifact. The CI check is the lock; these only nudge, so
# every case here is either a refusal that must name the stage or a touch that
# must stay silent. Agent-only signing, no network, no real repo.
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
GATE_SRC="$HERE/scripts/coco_gate.py"
[ -f "$GATE_SRC" ] || { echo "FAIL missing $GATE_SRC" >&2; exit 1; }

T="$(mktemp -d)"
AGENT_PID=""
AGENT_DIR="$(mktemp -d /tmp/cwh.XXXXXX)"  # short and 0700: a long socket path fails on macOS
AGENT_SOCK="$AGENT_DIR/s"
trap 'rc=$?; rm -rf "$T"; rm -rf "$AGENT_DIR"; [ -z "$AGENT_PID" ] || kill "$AGENT_PID" 2>/dev/null; exit $rc' EXIT
WORK="$T/work"
REPO="cocoresearch/coco"

export HOME="$T/home"
export GIT_CONFIG_NOSYSTEM=1
export GIT_AUTHOR_NAME=gate
export GIT_AUTHOR_EMAIL=gate@example.test
export GIT_COMMITTER_NAME=gate
export GIT_COMMITTER_EMAIL=gate@example.test
export GIT_TERMINAL_PROMPT=0
export COCO_GATE_REPO="$REPO"
unset GITHUB_REPOSITORY GITHUB_HEAD_REF GITHUB_BASE_REF
# A stray agent would sign for keys these cases mean to refuse (T7, lab-0514).
unset SSH_AUTH_SOCK SSH_AGENT_PID
mkdir -p "$HOME" "$T/keys"

ok() { echo "ok   $1"; }
fail() { echo "FAIL $1" >&2; exit 1; }

# --- throwaway keys; every signature goes through ssh-agent -----------------
for k in brain steve design outsider; do
  ssh-keygen -t ed25519 -N '' -q -C "$k" -f "$T/keys/$k"
done
AGENT_ENV="$(ssh-agent -a "$AGENT_SOCK" -s 2>&1)" || fail "cannot start ssh-agent: $AGENT_ENV"
# The agent output is parsed, never eval'd: only the two values we expect.
SSH_AUTH_SOCK="$(printf '%s\n' "$AGENT_ENV" | sed -n 's/^SSH_AUTH_SOCK=\([^;]*\);.*/\1/p')"
SSH_AGENT_PID="$(printf '%s\n' "$AGENT_ENV" | sed -n 's/^SSH_AGENT_PID=\([^;]*\);.*/\1/p')"
[ -n "$SSH_AUTH_SOCK" ] && [ -n "$SSH_AGENT_PID" ] \
  || fail "cannot parse ssh-agent output: $AGENT_ENV"
export SSH_AUTH_SOCK SSH_AGENT_PID
AGENT_PID="$SSH_AGENT_PID"
for k in brain steve design outsider; do
  ssh-add "$T/keys/$k" </dev/null >/dev/null 2>&1 || fail "ssh-add $k failed"
done

# --- a temp repo that owns the signers and both hooks ------------------------
git config --global init.defaultBranch main
git config --global commit.gpgsign false
git init -q "$WORK"
mkdir -p "$WORK/.coco/gates" "$WORK/scripts" "$WORK/hooks" "$WORK/docs/specs/h" "$WORK/src"
cp "$GATE_SRC" "$WORK/scripts/coco_gate.py"
cp "$HERE/hooks/coco-workflow-pretooluse.sh" "$WORK/hooks/"
cp "$HERE/hooks/coco-workflow-context.sh" "$WORK/hooks/"
chmod +x "$WORK/hooks/"*.sh
{
  for k in brain steve design; do
    printf '%s namespaces="coco-gate" %s coco-role=%s\n' \
      "$k" "$(cat "$T/keys/$k.pub")" "$k"
  done
} > "$WORK/.coco/allowed_signers"
printf '# base\n' > "$WORK/README.md"
printf '# prd\n' > "$WORK/docs/specs/h/prd.md"
printf '# arch\n' > "$WORK/docs/specs/h/arch.md"
printf '# plan\n' > "$WORK/docs/specs/h/plan.md"
git -C "$WORK" add -A
git -C "$WORK" commit -qm base
git -C "$WORK" checkout -q -b feat/hook

HOOK="$WORK/hooks/coco-workflow-pretooluse.sh"
CTX="$WORK/hooks/coco-workflow-context.sh"
gate() { ( cd "$WORK" && python3 scripts/coco_gate.py "$@" ); }
sign() { gate sign --stage "$1" --signer "$2" --key "$T/keys/$3.pub"; }

# Runs hook $1 with JSON $2 on stdin, from inside the work tree; sets RC, OUT.
hook() {
  RC=0
  OUT="$( cd "$WORK" && printf '%s' "$2" | "$1" 2>&1 )" || RC=$?
}

edit_json() { printf '{"tool_name":"%s","tool_input":{"file_path":"%s"}}' "$1" "$2"; }

want_silent() {
  [ "$RC" -eq 0 ] || fail "$1: expected exit 0, got $RC: $OUT"
  [ -z "$OUT" ] || fail "$1: expected no output, got: $OUT"
  ok "$1"
}

want_deny() {
  [ "$RC" -eq 0 ] || fail "$1: expected exit 0, got $RC: $OUT"
  case "$OUT" in
    *'"permissionDecision": "deny"'*"$2"*) ;;
    *) fail "$1: no deny naming '$2': $OUT" ;;
  esac
  ok "$1"
}

# --- 1/9b. no gate: the hooks stay silent ------------------------------------
hook "$HOOK" "$(edit_json Write "$WORK/src/a.py")"
want_silent "1 no gate: Write src/a.py passes"
hook "$CTX" ''
want_silent "9b no gate: the context hook says nothing"

# --- 2. a feature gate with only the PRD signed ------------------------------
gate init --branch feat/hook --size feature --builder si-brain \
  --prd docs/specs/h/prd.md --arch docs/specs/h/arch.md --plan docs/specs/h/plan.md
sign prd brain brain
hook "$HOOK" "$(edit_json Write "$WORK/src/a.py")"
want_deny "2a only the PRD signed: Write src/a.py" \
  "arch is not signed yet; next: docs/specs/h/arch.md"
hook "$HOOK" "$(edit_json Edit "$WORK/docs/specs/h/arch.md")"
want_silent "2b a specs path is always editable"
hook "$HOOK" "$(edit_json Write "$WORK/README.md")"
want_silent "2c a root-level .md is always editable"
hook "$HOOK" "$(edit_json Write "$WORK/sub/README.md")"
want_deny "2d a nested README.md is a code path" "arch is not signed yet"
for tool in Bash Read; do
  hook "$HOOK" "$(edit_json "$tool" "$WORK/src/a.py")"
  want_silent "6 $tool passes untouched while arch is pending"
done
hook "$CTX" ''
[ "$RC" -eq 0 ] || fail "9 the context hook must exit 0, got $RC: $OUT"
case "$OUT" in
  *'"additionalContext": "Coco workflow: stage arch; next: docs/specs/h/arch.md"'*) ;;
  *) fail "9 the context hook line is wrong: $OUT" ;;
esac
ok "9 the context hook names the stage and the next artifact"

# --- 4. a forged plan is still refused ---------------------------------------
sign arch steve steve
gate sign --stage plan --signer steve --key "$T/keys/outsider.pub"
hook "$HOOK" "$(edit_json Write "$WORK/src/a.py")"
want_deny "4 an outsider key signing as steve" \
  "plan is not signed yet; next: docs/specs/h/plan.md"

# --- 3. the plan signed: code edits pass -------------------------------------
sign plan steve steve
hook "$HOOK" "$(edit_json Write "$WORK/src/a.py")"
want_silent "3 plan signed: Write src/a.py passes"

# --- 5. the plan edited after signing ----------------------------------------
printf 'late edit\n' >> "$WORK/docs/specs/h/plan.md"
hook "$HOOK" "$(edit_json Write "$WORK/src/a.py")"
want_deny "5 the plan file edited after signing" "plan is not signed yet"
for tool in Bash Read; do
  hook "$HOOK" "$(edit_json "$tool" "$WORK/src/a.py")"
  want_silent "6b $tool passes untouched while plan is pending"
done

# --- 7. a malformed gate: one deny line, no traceback ------------------------
printf 'not json at all\n' > "$WORK/.coco/gates/feat__hook.json"
hook "$HOOK" "$(edit_json Write "$WORK/src/a.py")"
[ "$RC" -eq 0 ] || fail "7 malformed gate: expected exit 0, got $RC: $OUT"
case "$OUT" in *Traceback*) fail "7 malformed gate printed a traceback: $OUT" ;; esac
case "$OUT" in
  *'"permissionDecision": "deny"'*'malformed JSON'*) ;;
  *) fail "7 malformed gate is not a one-line deny: $OUT" ;;
esac
ok "7 a malformed gate denies with one line and no traceback"

# --- 8. no coco_gate.py next to the hook -------------------------------------
cp "$HOOK" "$T/lonely.sh"
chmod +x "$T/lonely.sh"
OUT="$( cd "$WORK" && printf '%s' "$(edit_json Write "$WORK/src/a.py")" \
  | "$T/lonely.sh" 2>&1 )" || fail "8 a lonely hook must exit 0"
[ -z "$OUT" ] || fail "8 a lonely hook printed: $OUT"
ok "8 no verifier next to the hook: exit 0, no output"

# --- T4. the installer guard line, and no network in the hooks ---------------
# The exact guarded line from the hooks' header comment, run as a script file
# with HOME pointing at an empty dir: no coco installed, so exit 0, no output.
EH="$(mktemp -d)"
for f in coco-workflow-pretooluse coco-workflow-context; do
  guard="sh -c '[ -x \"\$HOME/.claude/coco/hooks/$f.sh\" ] && exec \"\$HOME/.claude/coco/hooks/$f.sh\" || exit 0'"
  grep -Fq "$guard" "$HERE/hooks/$f.sh" || fail "T4 $f.sh lacks its installer line"
  printf '%s\n' "$guard" > "$T/guard.sh"
  GRC=0
  GOUT="$( HOME="$EH" sh "$T/guard.sh" 2>&1 )" || GRC=$?
  [ "$GRC" -eq 0 ] || fail "T4 the guarded line exited $GRC with no coco installed"
  [ -z "$GOUT" ] || fail "T4 the guarded line printed: $GOUT"
done
bad="$(grep -nE 'curl|wget|nc |http://|https://' \
  "$HERE/hooks/coco-workflow-pretooluse.sh" "$HERE/hooks/coco-workflow-context.sh" || true)"
[ -z "$bad" ] || fail "T4 the hooks mention the network: $bad"
ok "T4 the guarded sh -c line exits 0 and prints nothing without coco; the hooks use no network"

echo "ok   all coco-workflow hook cases passed"
