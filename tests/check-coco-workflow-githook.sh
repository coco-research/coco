#!/usr/bin/env bash
# The coco-workflow git hooks: the pre-commit hook only warns — one stderr line
# naming the stage and the next artifact while the branch's feature gate has no
# validly signed plan, then exit 0, or the exit code of a COCO_CHAIN_HOOK chain
# hook an installer parked beside the user's old pre-commit — and the H7
# check-show gate: a show checklist passes only when every task box is ticked
# and two valid show sign-offs cover it, a steve and a distinct reviewer,
# design or council. Agent-only signing, no network, no real repo.
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
GATE_SRC="$HERE/scripts/coco_gate.py"
HOOK_SRC="$HERE/hooks/coco-workflow-pre-commit.sh"
[ -f "$GATE_SRC" ] || { echo "FAIL missing $GATE_SRC" >&2; exit 1; }
[ -f "$HOOK_SRC" ] || { echo "FAIL missing $HOOK_SRC" >&2; exit 1; }

T="$(mktemp -d)"
AGENT_PID=""
AGENT_DIR="$(mktemp -d /tmp/cgh.XXXXXX)"  # short and 0700: a long socket path fails on macOS
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
unset SSH_AUTH_SOCK SSH_AGENT_PID
mkdir -p "$HOME" "$T/keys"

ok() { echo "ok   $1"; }
fail() { echo "FAIL $1" >&2; exit 1; }

# --- throwaway keys; every signature goes through ssh-agent -----------------
for k in brain steve design reviewer factory outsider; do
  ssh-keygen -t ed25519 -N '' -q -C "$k" -f "$T/keys/$k"
done
AGENT_ENV="$(ssh-agent -a "$AGENT_SOCK" -s 2>&1)" || fail "cannot start ssh-agent: $AGENT_ENV"
SSH_AUTH_SOCK="$(printf '%s\n' "$AGENT_ENV" | sed -n 's/^SSH_AUTH_SOCK=\([^;]*\);.*/\1/p')"
SSH_AGENT_PID="$(printf '%s\n' "$AGENT_ENV" | sed -n 's/^SSH_AGENT_PID=\([^;]*\);.*/\1/p')"
[ -n "$SSH_AUTH_SOCK" ] && [ -n "$SSH_AGENT_PID" ] \
  || fail "cannot parse ssh-agent output: $AGENT_ENV"
export SSH_AUTH_SOCK SSH_AGENT_PID
AGENT_PID="$SSH_AGENT_PID"
for k in brain steve design reviewer factory outsider; do
  ssh-add "$T/keys/$k" </dev/null >/dev/null 2>&1 || fail "ssh-add $k failed"
done

# --- a temp repo that owns the signers, the verifier and the hook ------------
git config --global init.defaultBranch main
git config --global commit.gpgsign false
git init -q "$WORK"
mkdir -p "$WORK/.coco/gates" "$WORK/scripts" "$WORK/hooks" "$WORK/docs/specs/h"
cp "$GATE_SRC" "$WORK/scripts/coco_gate.py"
cp "$HOOK_SRC" "$WORK/hooks/coco-workflow-pre-commit.sh"
chmod +x "$WORK/hooks/"*.sh
{
  for k in brain steve design reviewer factory; do
    printf '%s namespaces="coco-gate" %s coco-role=%s\n' \
      "$k" "$(cat "$T/keys/$k.pub")" "$k"
  done
} > "$WORK/.coco/allowed_signers"
printf '# prd\n' > "$WORK/docs/specs/h/prd.md"
printf '# arch\n' > "$WORK/docs/specs/h/arch.md"
printf '# plan\n' > "$WORK/docs/specs/h/plan.md"
git -C "$WORK" add -A
git -C "$WORK" commit -qm base
git -C "$WORK" checkout -q -b feat/hook

HOOK="$WORK/hooks/coco-workflow-pre-commit.sh"
gate() { ( cd "$WORK" && python3 scripts/coco_gate.py "$@" ); }
sign() {
  local st="$1" who="$2" key="$3"
  shift 3
  gate sign --stage "$st" --signer "$who" --key "$T/keys/$key.pub" "$@"
}

# Runs the pre-commit hook from inside the work tree; sets RC, OUT (stdout)
# and ERR (stderr, where a warning belongs).
precommit() {
  RC=0
  OUT="$( cd "$WORK" && "$HOOK" 2>"$T/hook.err" )" || RC=$?
  ERR="$(cat "$T/hook.err")"
}

# Runs check-show on checklist $1 (further args pass through); sets RC and OUT.
show() {
  local cl="$1"
  shift
  RC=0
  OUT="$( cd "$WORK" && python3 scripts/coco_gate.py check-show --checklist "$cl" "$@" 2>&1 )" || RC=$?
}

checklist() { printf '# show\n- [x] thing one\n- [x] thing two\n' > "$WORK/$1"; }

# --- 1. no gate: the hook stays silent ---------------------------------------
precommit
[ "$RC" -eq 0 ] || fail "1 no gate: expected exit 0, got $RC: $OUT$ERR"
[ -z "$OUT$ERR" ] || fail "1 no gate: expected no output, got: $OUT$ERR"
ok "1 pre-commit with no gate: no output, exit 0"

# --- 2. feature gate, plan unsigned: a warning on stderr, still exit 0 -------
gate init --branch feat/hook --size feature --builder si-brain \
  --prd docs/specs/h/prd.md --arch docs/specs/h/arch.md --plan docs/specs/h/plan.md
sign prd brain brain
sign arch steve steve
precommit
[ "$RC" -eq 0 ] || fail "2a plan unsigned: expected exit 0, got $RC: $OUT$ERR"
case "$ERR" in
  *"coco-workflow (warning): stage plan; next: docs/specs/h/plan.md"*) ;;
  *) fail "2a no warning naming the stage and next artifact: $ERR" ;;
esac
[ -z "$OUT" ] || fail "2a the warning belongs on stderr, not stdout: $OUT"
ok "2a feature gate, plan unsigned: warning on stderr, exit 0"

gate sign --stage plan --signer steve --key "$T/keys/outsider.pub"
precommit
[ "$RC" -eq 0 ] || fail "2b forged plan: expected exit 0, got $RC: $OUT$ERR"
case "$ERR" in
  *"coco-workflow (warning): stage plan"*) ;;
  *) fail "2b a forged plan sign-off must still warn: $ERR" ;;
esac
ok "2b a forged plan sign-off still warns (validity, not presence)"

# --- 3. plan signed: silence --------------------------------------------------
sign plan steve steve
precommit
[ "$RC" -eq 0 ] || fail "3 plan signed: expected exit 0, got $RC: $OUT$ERR"
[ -z "$OUT$ERR" ] || fail "3 plan signed: expected no output, got: $OUT$ERR"
ok "3 pre-commit with the plan signed: no output, exit 0"

# --- 4/T3. chaining: COCO_CHAIN_HOOK runs last and wins the exit code --------
printf '#!/bin/sh\necho chained ran\nexit 3\n' > "$T/chain.sh"
chmod +x "$T/chain.sh"
git -C "$WORK" checkout -q -b feat/t3
gate init --branch feat/t3 --size feature --builder si-brain \
  --prd docs/specs/h/prd.md --arch docs/specs/h/arch.md --plan docs/specs/h/plan.md
sign prd brain brain --branch feat/t3
sign arch steve steve --branch feat/t3
precommit
[ "$RC" -eq 0 ] || fail "T3 ours alone: expected exit 0, got $RC: $ERR"
case "$ERR" in
  *"coco-workflow (warning): stage plan"*) ;;
  *) fail "T3 ours alone should still warn: $ERR" ;;
esac
RC=0
OUT="$( cd "$WORK" && COCO_CHAIN_HOOK="$T/chain.sh" "$HOOK" 2>"$T/hook.err" )" || RC=$?
ERR="$(cat "$T/hook.err")"
[ "$RC" -eq 3 ] || fail "T3 chained: expected exit 3, got $RC: $OUT$ERR"
case "$ERR" in
  *"coco-workflow (warning): stage plan"*) ;;
  *) fail "T3 the warning must print before the chain hook runs: $ERR" ;;
esac
case "$OUT" in
  *"chained ran"*) ;;
  *) fail "T3 the chain hook did not run: $OUT" ;;
esac
ok "T3 chained to an exit-3 hook: exit 3, warning first; alone ours exits 0"
# T3b: a hook copy with no coco_gate.py beside it still runs the user's hook.
mkdir -p "$T/lonely/hooks"
cp "$HOOK" "$T/lonely/hooks/pre-commit"
RC=0
OUT="$( cd "$WORK" && COCO_CHAIN_HOOK="$T/chain.sh" "$T/lonely/hooks/pre-commit" 2>&1 )" || RC=$?
[ "$RC" -eq 3 ] || fail "T3b no verifier: the user's hook must still decide (exit 3), got $RC: $OUT"
case "$OUT" in *"chained ran"*) ;; *) fail "T3b no verifier: the chain hook did not run: $OUT" ;; esac
ok "T3b no verifier beside the hook: the user's hook still runs and decides"
chmod -x "$T/chain.sh"
RC=0
OUT="$( cd "$WORK" && COCO_CHAIN_HOOK="$T/chain.sh" "$HOOK" 2>&1 )" || RC=$?
[ "$RC" -ne 0 ] || fail "T3c a chained hook that can't run must not pass: $OUT"
case "$OUT" in *"is not executable"*) ;; *) fail "T3c no reason given: $OUT" ;; esac
chmod +x "$T/chain.sh"
ok "T3c a configured chain hook that isn't executable stops the commit with a reason"

# --- 5. check-show: an unticked box is named ---------------------------------
CL=docs/specs/h/show.md
printf '# show\n- [x] done\n- [ ] ship it\n' > "$WORK/$CL"
sign show steve steve --checklist "$CL"
sign show reviewer reviewer --checklist "$CL"
show "$CL"
[ "$RC" -eq 1 ] || fail "5 unticked: expected exit 1, got $RC: $OUT"
case "$OUT" in
  *"unticked: - [ ] ship it"*) ;;
  *) fail "5 the FAIL line does not name the unticked box: $OUT" ;;
esac
ok "5 an unticked box fails and is named"

# --- 6. one steve sign-off is not enough -------------------------------------
CL=docs/specs/h/show6.md
checklist "$CL"
sign show steve steve --checklist "$CL"
show "$CL"
[ "$RC" -eq 1 ] || fail "6 one sign-off: expected exit 1, got $RC: $OUT"
case "$OUT" in
  *"no valid show sign-off by reviewer, design or council"*) ;;
  *) fail "6 the FAIL does not name the missing role: $OUT" ;;
esac
ok "6 all ticked, one steve sign-off: FAIL"

# --- 7. steve plus reviewer: ok, with --signers honoured ---------------------
sign show reviewer reviewer --checklist "$CL"
show "$CL" --signers .coco/allowed_signers
[ "$RC" -eq 0 ] || fail "7 steve+reviewer: expected exit 0, got $RC: $OUT"
case "$OUT" in
  *"coco-workflow: ok show $CL"*) ;;
  *) fail "7 no ok line: $OUT" ;;
esac
ok "7 steve plus reviewer: ok show, and --signers is honoured"

# --- 8. editing the checklist voids the sign-offs (sha) ----------------------
printf '%s\n' '- [x] late addition' >> "$WORK/$CL"
show "$CL"
[ "$RC" -eq 1 ] || fail "8 edited checklist: expected exit 1, got $RC: $OUT"
case "$OUT" in
  *FAIL*) ;;
  *) fail "8 no FAIL line: $OUT" ;;
esac
ok "8 the checklist edited after signing: FAIL (sha)"

# --- 9. two sign-offs both by steve are not two signers ----------------------
CL=docs/specs/h/show9.md
checklist "$CL"
sign show steve steve --checklist "$CL"
sign show steve steve --checklist "$CL"
show "$CL"
[ "$RC" -eq 1 ] || fail "9 two steves: expected exit 1, got $RC: $OUT"
case "$OUT" in
  *"no valid show sign-off by reviewer, design or council"*) ;;
  *) fail "9 the FAIL does not name the distinct-signer rule: $OUT" ;;
esac
ok "9 two sign-offs both by steve: FAIL (two distinct signers and roles)"

# --- 10. a factory-role sign-off counts for nothing --------------------------
CL=docs/specs/h/show10.md
checklist "$CL"
sign show steve steve --checklist "$CL"
sign show factory factory --checklist "$CL"
show "$CL"
[ "$RC" -eq 1 ] || fail "10 factory: expected exit 1, got $RC: $OUT"
case "$OUT" in
  *"no valid show sign-off by reviewer, design or council"*) ;;
  *) fail "10 the factory sign-off counted for something: $OUT" ;;
esac
ok "10 a factory-role sign-off counts for nothing"

# --- 11. malformed sign-offs file: one line, no traceback --------------------
CL=docs/specs/h/show11.md
checklist "$CL"
printf 'not json at all\n' > "$WORK/$CL.signoffs.json"
show "$CL"
[ "$RC" -eq 1 ] || fail "11 malformed: expected exit 1, got $RC: $OUT"
case "$OUT" in *Traceback*) fail "11 printed a traceback: $OUT" ;; esac
[ "$(printf '%s\n' "$OUT" | wc -l | tr -d ' ')" -eq 1 ] \
  || fail "11 should be exactly one line: $OUT"
case "$OUT" in *malformed*) ;; *) fail "11 no malformed message: $OUT" ;; esac
ok "11 malformed sign-offs JSON: one line, exit 1, no traceback"

# --- 12. a checklist path that escapes the repo is refused --------------------
show ../outside.md
[ "$RC" -eq 1 ] || fail "12 traversal: expected exit 1, got $RC: $OUT"
case "$OUT" in
  *"not a repo-relative path"*) ;;
  *) fail "12 the FAIL does not name the path rule: $OUT" ;;
esac
ok "12 a --checklist containing .. is refused"

# 13. show sign with no --checklist, and a sign-offs file of the wrong shape: one clean line each.
RC=0; OUT="$( (cd "$WORK" && python3 "$GATE_SRC" sign --stage show --signer steve --key "$T/keys/steve.pub") 2>&1 )" || RC=$?
[ "$RC" -ne 0 ] || fail "13a show sign without --checklist was accepted"
case "$OUT" in *"show needs --checklist"*) ;; *) fail "13a wrong message: $OUT" ;; esac
printf '# s\n- [x] a\n' > "$WORK/docs/specs/h/shape.md"
printf '[1, {"stage": "show"}]\n' > "$WORK/docs/specs/h/shape.md.signoffs.json"
RC=0; OUT="$( (cd "$WORK" && python3 "$GATE_SRC" check-show --checklist docs/specs/h/shape.md) 2>&1 )" || RC=$?
[ "$RC" -eq 1 ] || fail "13b wrong-shape sign-offs: expected exit 1, got $RC: $OUT"
case "$OUT" in *"not a list of sign-off objects"*) ;; *) fail "13b wrong message: $OUT" ;; esac
ok "13 show without --checklist and a wrong-shape sign-offs file each fail with one clean line"

echo "ok   all coco-workflow git-hook cases passed"
