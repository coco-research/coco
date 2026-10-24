#!/usr/bin/env bash
# The coco-workflow required check: a feature PR's PRD, architecture and plan
# sign-offs must be real, current and signed by the right role, and the signers,
# the policy and the verifier must all come from the base branch. Every case
# below is either a forgery the gate has to refuse or a legitimate gate it has
# to accept. Nothing here touches the network or the real repo.
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
GATE_SRC="$HERE/scripts/coco_gate.py"
[ -f "$GATE_SRC" ] || { echo "FAIL missing $GATE_SRC" >&2; exit 1; }

T="$(mktemp -d)"
AGENT_PID=""
AGENT_DIR="$(mktemp -d /tmp/cga.XXXXXX)"  # short and 0700: a socket path over ~104 bytes fails on macOS
AGENT_SOCK="$AGENT_DIR/s"
# Keep the real exit status: a cleanup that ends in `|| true` must not turn a failure into a pass.
trap 'rc=$?; rm -rf "$T"; rm -rf "$AGENT_DIR"; [ -z "$AGENT_PID" ] || kill "$AGENT_PID" 2>/dev/null; exit $rc' EXIT
WORK="$T/work"
VG="$T/run/coco_gate.py"
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
# A stray agent would let a private-key case silently use the agent's key, and
# ssh-keygen once blocked for twenty minutes on a dead SSH_AUTH_SOCK.
unset SSH_AUTH_SOCK SSH_AGENT_PID
mkdir -p "$HOME" "$T/keys" "$T/run"

ok() { echo "ok   $1"; }
fail() { echo "FAIL $1" >&2; exit 1; }

# --- throwaway keys -------------------------------------------------------
for k in brain steve design factory outsider; do
  ssh-keygen -t ed25519 -N '' -q -C "$k" -f "$T/keys/$k"
done

# --- a bare origin with a base main that owns the trust roots ------------
git config --global init.defaultBranch main
git config --global commit.gpgsign false
git init --bare -q "$T/origin.git"
git -C "$T/origin.git" symbolic-ref HEAD refs/heads/main
git clone -q "$T/origin.git" "$WORK"
git -C "$WORK" symbolic-ref HEAD refs/heads/main

mkdir -p "$WORK/.coco/gates" "$WORK/scripts" "$WORK/docs/specs/x"
cp "$GATE_SRC" "$WORK/scripts/coco_gate.py"
{
  for k in brain steve design factory; do
    printf '%s namespaces="coco-gate" %s coco-role=%s\n' \
      "$k" "$(cat "$T/keys/$k.pub")" "$k"
  done
} > "$WORK/.coco/allowed_signers"
printf 'approved by hand\nby: rijul\n' > "$WORK/docs/specs/x/decision-approve.md"
# A gate for a branch that does not exist yet, so "deleted in the PR" is testable.
printf '{"schema":1,"note":"placeholder on base"}\n' > "$WORK/.coco/gates/feat__deleted.json"
git -C "$WORK" add -A
git -C "$WORK" commit -qm base
git -C "$WORK" push -q origin main
git -C "$WORK" fetch -q origin

# Exactly the ci.yml recipe: run the base branch's verifier, head copy only as
# the bootstrap fallback.
base_verifier() {
  if git -C "$WORK" show "origin/main:scripts/coco_gate.py" > "$VG" 2>/dev/null; then
    return 0
  fi
  echo "coco-workflow: verifier not on base yet, using head copy"
  cp "$GATE_SRC" "$VG"
}
base_verifier

# --- helpers --------------------------------------------------------------
gate() { ( cd "$WORK" && python3 "$VG" "$@" ); }

# Sets RC and OUT from a CI-shaped verify run on branch $1.
capture() {
  local br="$1"
  shift
  RC=0
  OUT="$( ( cd "$WORK" && GITHUB_REPOSITORY="$REPO" GITHUB_HEAD_REF="$br" \
            python3 "$VG" verify --ci --base main "$@" ) 2>&1 )" || RC=$?
}

want_ok() {
  local name="$1"
  [ "$RC" -eq 0 ] || fail "$name: expected ok, exit $RC: $OUT"
  case "$OUT" in
    *"coco-workflow: ok"*) ok "$name" ;;
    *) fail "$name: no ok line: $OUT" ;;
  esac
}

want_fail() {
  local name="$1" want="${2:-}"
  [ "$RC" -ne 0 ] || fail "$name: expected FAIL, got exit 0: $OUT"
  case "$OUT" in
    *"coco-workflow: FAIL"*) ;;
    *) fail "$name: no FAIL line: $OUT" ;;
  esac
  if [ -n "$want" ]; then
    case "$OUT" in
      *"$want"*) ;;
      *) fail "$name: FAIL does not mention '$want': $OUT" ;;
    esac
  fi
  ok "$name"
}

# A fresh branch off base: no local edits and no untracked gate or policy files.
# Gate files tracked on base (feat__deleted.json) stay, as they would in a real repo.
reset() {
  git -C "$WORK" checkout -q -B "$1" origin/main
  git -C "$WORK" checkout -q -- .
  git -C "$WORK" clean -fdq -- .coco
  mkdir -p "$WORK/.coco/gates"
}

docs() {
  local d="$WORK/docs/specs/$1"
  mkdir -p "$d"
  printf '# prd\n' > "$d/prd.md"
  printf '# arch\n' > "$d/arch.md"
  printf '# plan\n' > "$d/plan.md"
  printf '# mock\n' > "$d/mock.md"
}

init_gate() {
  local b="$1" s="$2"
  shift 2
  gate init --branch "$b" --size feature --builder si-brain \
    --prd "docs/specs/$s/prd.md" --arch "docs/specs/$s/arch.md" \
    --plan "docs/specs/$s/plan.md" --ui 'web/**' "$@"
}

sign_stage() {
  local st="$1" who="$2"
  shift 2
  gate sign --stage "$st" --signer "$who" --key "$T/keys/$who" "$@"
}

# A gate with no artifacts and no chain: the shape a protected-path-only PR uses.
small_gate() {
  mkdir -p "$WORK/.coco/gates"
  python3 - "$WORK/.coco/gates/$(printf '%s' "$1" | sed 's|/|__|g').json" \
    "$REPO" "$1" <<'PY'
import json, sys
path, repo, branch = sys.argv[1:4]
json.dump({"schema": 1, "repo": repo, "branch": branch, "size": "small",
           "builder": "si-brain", "signoffs": []}, open(path, "w"), indent=2)
PY
}

signed_gate() {
  init_gate "$1" "$2"
  sign_stage prd brain
  sign_stage arch steve
  sign_stage plan steve
}

drop_stage() {
  python3 - "$WORK/.coco/gates/$1.json" "$2" <<'PY'
import json, sys
path, stage = sys.argv[1], sys.argv[2]
gate = json.load(open(path))
gate["signoffs"] = [s for s in gate["signoffs"] if s.get("stage") != stage]
json.dump(gate, open(path, "w"), indent=2)
PY
}

# The forger: builds the canonical message itself, so these cases are not
# trusting the code under test to construct the thing being signed.
cat > "$T/forge.py" <<'PY'
import hashlib, json, os, subprocess, sys
path, stage, signer, key, ns = sys.argv[1:6]
over = dict(arg.split("=", 1) for arg in sys.argv[6:])
gate = json.load(open(path))
artifacts = gate.get("artifacts") or {}
artifact = over.get("artifact") or artifacts.get(stage) or "size:small"
sha = hashlib.sha256(b"small").hexdigest() if stage == "size" else \
    hashlib.sha256(open(artifact, "rb").read()).hexdigest()
base = over.get("base") or subprocess.check_output(
    ["git", "merge-base", "HEAD", "origin/main"],
    stdin=subprocess.DEVNULL, timeout=60).decode().strip()
entry = {"repo": gate["repo"], "branch": gate["branch"], "base": base,
         "stage": stage, "size": gate["size"], "artifact": artifact, "sha256": sha,
         "prev": over.get("prev", ""), "decision": over.get("decision", ""),
         "signer": signer, "at": over.get("at", "2026-01-01T00:00:00Z")}
keys = ("repo", "branch", "base", "stage", "size", "artifact", "sha256", "prev",
        "decision", "signer", "at")
msg = "\n".join(["coco-gate/1"] + ["%s=%s" % (k, entry[k]) for k in keys]) + "\n"
msg_path = os.path.join(os.path.dirname(path), "forge.msg")
open(msg_path, "w").write(msg)
subprocess.check_call(["ssh-keygen", "-Y", "sign", "-f", key, "-n", ns, msg_path],
                      stdin=subprocess.DEVNULL, timeout=60,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
entry["sig"] = open(msg_path + ".sig").read()
gate.setdefault("signoffs", []).append(entry)
json.dump(gate, open(path, "w"), indent=2)
PY
forge() { ( cd "$WORK" && python3 "$T/forge.py" "$@" ); }

# --- 1. happy path --------------------------------------------------------
reset feat/happy
docs happy
signed_gate feat/happy happy
capture feat/happy
want_ok "1 happy path: prd brain, arch steve, plan steve"

# --- 2. missing gates -----------------------------------------------------
reset feat/nogate
docs nogate
capture feat/nogate
want_fail "2a no gate on a feature branch" "no gate for feature branch"

reset fix/y
capture fix/y
want_ok "2b no gate on a non-feature branch"

reset feat/deleted
rm -f "$WORK/.coco/gates/feat__deleted.json"
capture feat/deleted
want_fail "2c a gate deleted on a branch that has one on base" "deleted"

# --- 3. a gate with no sign-offs -----------------------------------------
reset feat/unsigned
docs unsigned
init_gate feat/unsigned unsigned
capture feat/unsigned
want_fail "3 a gate with no sign-offs is rejected" "prd"

# --- 4. the gate file itself is edited after signing ----------------------
reset feat/tamper
docs tamper
signed_gate feat/tamper tamper
python3 - "$WORK/.coco/gates/feat__tamper.json" <<'PY'
import json, sys
path = sys.argv[1]
gate = json.load(open(path))
gate["signoffs"][0]["sha256"] = "0" * 64
json.dump(gate, open(path, "w"), indent=2)
PY
capture feat/tamper
want_fail "4 an edited sha256 no longer matches the signed message" \
  "signature does not verify"

# --- 5. the artifact is edited after signing ------------------------------
reset feat/late
docs late
signed_gate feat/late late
printf 'late edit\n' >> "$WORK/docs/specs/late/prd.md"
capture feat/late
want_fail "5 an artifact edited after signing" "artifact changed after signing"

# --- 6. agent-written signatures -----------------------------------------
reset feat/outsider
docs outsider
init_gate feat/outsider outsider
sign_stage prd brain
sign_stage arch steve
gate sign --stage plan --signer steve --key "$T/keys/outsider"
capture feat/outsider
want_fail "6a an outsider key under a trusted name" "signature does not verify"

reset feat/factory
docs factory
init_gate feat/factory factory
gate sign --stage prd --signer factory --key "$T/keys/factory"
capture feat/factory
want_fail "6b a role in no_sign_roles is rejected" "no_sign_roles"

reset feat/builder
docs builder
gate init --branch feat/builder --size feature --builder steve \
  --prd docs/specs/builder/prd.md --arch docs/specs/builder/arch.md \
  --plan docs/specs/builder/plan.md --ui 'web/**'
sign_stage prd brain
sign_stage arch steve
capture feat/builder
want_fail "6c the gate builder cannot sign its own gate" "gate builder"

# --- 7. a key added on the branch is ignored in CI -----------------------
reset feat/keyadd
docs keyadd
signed_gate feat/keyadd keyadd
printf 'steve namespaces="coco-gate" %s coco-role=steve\n' \
  "$(cat "$T/keys/outsider.pub")" >> "$WORK/.coco/allowed_signers"
drop_stage feat__keyadd plan
gate sign --stage plan --signer steve --key "$T/keys/outsider"
capture feat/keyadd
want_fail "7 a key added on the branch is ignored in ci" "signature does not verify"
# Control: the branch's own signers file is what would have said yes.
if ! ( cd "$WORK" && python3 "$VG" verify --branch feat/keyadd ) >/dev/null 2>&1; then
  fail "7b control: the branch's own signers did not accept the forged plan"
fi
ok "7b control: the branch's own signers file would have accepted it"

# --- 8. a policy loosened on the branch is ignored in CI -----------------
reset feat/policy
docs policy
signed_gate feat/policy policy
cat > "$WORK/.coco/workflow.json" <<'JSON'
{"feature_branches":["feat/*"],
 "stages":{"prd":["brain"],"arch":["steve","council","brain"],
           "plan":["steve","council"],"mock":["design"],"approve":["steve"]},
 "no_sign_roles":["factory"],"approver_key":"relay"}
JSON
drop_stage feat__policy arch
drop_stage feat__policy plan
sign_stage arch brain
sign_stage plan steve
capture feat/policy
want_fail "8 a policy loosened on the branch is ignored in ci" "may not sign arch"

# --- 9. the wrong namespace ----------------------------------------------
reset feat/ns
docs ns
signed_gate feat/ns ns
drop_stage feat__ns prd
forge "$WORK/.coco/gates/feat__ns.json" prd brain "$T/keys/brain" other
capture feat/ns
want_fail "9 a signature made in another namespace" "signature does not verify"

# --- 10. stage order and replay ------------------------------------------
reset feat/empty
docs empty
signed_gate feat/empty empty
drop_stage feat__empty arch
drop_stage feat__empty plan
forge "$WORK/.coco/gates/feat__empty.json" arch steve "$T/keys/steve" coco-gate
capture feat/empty
want_fail "10a arch signed with an empty prev" "prev does not match the prd"

reset feat/replay
docs replay
signed_gate feat/replay replay
python3 - "$WORK/.coco/gates/feat__replay.json" "$T/prd-signoff.json" <<'PY'
import json, sys
gate = json.load(open(sys.argv[1]))
entry = [s for s in gate["signoffs"] if s["stage"] == "prd"][0]
json.dump(entry, open(sys.argv[2], "w"))
PY
reset feat/copy
docs copy
init_gate feat/copy copy
python3 - "$WORK/.coco/gates/feat__copy.json" "$T/prd-signoff.json" <<'PY'
import json, sys
gate = json.load(open(sys.argv[1]))
gate["signoffs"].append(json.load(open(sys.argv[2])))
json.dump(gate, open(sys.argv[1], "w"), indent=2)
PY
capture feat/copy
want_fail "10b a prd sign-off replayed on another branch" "feat/replay"

# --- 11. size=small -------------------------------------------------------
reset feat/small
docs small
gate init --branch feat/small --size small --builder si-brain \
  --prd docs/specs/small/prd.md --arch docs/specs/small/arch.md \
  --plan docs/specs/small/plan.md --ui 'web/**'
capture feat/small
want_fail "11a size=small without a size sign-off" "unsigned size=small"
sign_stage size steve
capture feat/small
want_ok "11b size=small signed by a stages.arch role"

# --- 12. UI changes need a mock and an approval --------------------------
reset feat/ui
docs ui
signed_gate feat/ui ui
printf 'web/a.js\n' > "$T/changed.txt"
capture feat/ui --changed "$T/changed.txt"
want_fail "12a a ui change without a mock" "mock"
sign_stage mock design --artifact docs/specs/ui/mock.md
sign_stage approve steve --artifact docs/specs/ui/mock.md \
  --decision docs/specs/x/decision-approve.md
capture feat/ui --changed "$T/changed.txt"
want_ok "12b a ui change with mock and approval"

reset feat/uibranch
docs uibranch
signed_gate feat/uibranch uibranch
printf 'by: rijul\n' > "$WORK/docs/specs/uibranch/decision.md"
sign_stage mock design --artifact docs/specs/uibranch/mock.md
sign_stage approve steve --artifact docs/specs/uibranch/mock.md \
  --decision docs/specs/uibranch/decision.md
capture feat/uibranch --changed "$T/changed.txt"
want_fail "12c a decision record that only exists on the branch" "decision record"

# --- 13. fail closed ------------------------------------------------------
reset feat/badjson
printf 'not json at all\n' > "$WORK/.coco/gates/feat__badjson.json"
RC=0
OUT="$( ( cd "$WORK" && GITHUB_REPOSITORY="$REPO" GITHUB_HEAD_REF=feat/badjson \
          python3 "$VG" verify --ci --base main ) 2>&1 )" || RC=$?
[ "$RC" -eq 1 ] || fail "13a malformed json: expected exit 1, got $RC: $OUT"
case "$OUT" in
  *Traceback*) fail "13a malformed json printed a traceback: $OUT" ;;
esac
[ "$(printf '%s\n' "$OUT" | wc -l | tr -d ' ')" -eq 1 ] \
  || fail "13a malformed json should be one line: $OUT"
want_fail "13a malformed gate json" "malformed JSON"

reset feat/escape
docs escape
signed_gate feat/escape escape
python3 - "$WORK/.coco/gates/feat__escape.json" <<'PY'
import json, sys
path = sys.argv[1]
gate = json.load(open(path))
gate["artifacts"]["prd"] = "../x"
json.dump(gate, open(path, "w"), indent=2)
PY
capture feat/escape
want_fail "13b an artifact path that escapes the repo" "../x"

# --- 14. the verifier cannot be swapped in the PR ------------------------
reset feat/verifier
docs verifier
init_gate feat/verifier verifier
cat > "$WORK/scripts/coco_gate.py" <<'PY'
import sys
print("coco-workflow: ok forged")
sys.exit(0)
PY
base_verifier
if cmp -s "$VG" "$WORK/scripts/coco_gate.py"; then
  fail "14: the job copied the head verifier, not the base one"
fi
capture feat/verifier
want_fail "14 a PR that edits the verifier cannot forge the gate"
if ! ( cd "$WORK" && GITHUB_REPOSITORY="$REPO" GITHUB_HEAD_REF=feat/verifier \
       python3 scripts/coco_gate.py verify --ci --base main ) >/dev/null 2>&1; then
  fail "14b control: the forged verifier did not pass its own gate"
fi
ok "14b control: the head verifier would have said ok"

# --- 15. size is part of the signed message ------------------------------
reset feat/sizeedit
docs sizeedit
signed_gate feat/sizeedit sizeedit
capture feat/sizeedit
want_ok "15a the chain verifies before the gate is edited"
python3 - "$WORK/.coco/gates/feat__sizeedit.json" <<'PY'
import json, sys
gate = json.load(open(sys.argv[1]))
gate["size"] = "small"
json.dump(gate, open(sys.argv[1], "w"), indent=2)
PY
capture feat/sizeedit
want_fail "15b editing size in the gate voids the sign-offs" "size"

# --- 16. a sign-off is bound to the history it was made on ---------------
reset feat/orphancopy
git -C "$WORK" checkout -q --orphan orphan-tmp
git -C "$WORK" commit -q -m orphan --allow-empty
ORPHAN="$(git -C "$WORK" rev-parse HEAD)"
docs orphancopy
init_gate feat/orphancopy orphancopy
for st in prd arch plan; do
  case "$st" in
    prd) who=brain ;;
    *) who=steve ;;
  esac
  gate sign --stage "$st" --signer "$who" --key "$T/keys/$who" \
    --branch feat/orphancopy --base-commit "$ORPHAN"
done
git -C "$WORK" checkout -q -B feat/orphancopy origin/main
docs orphancopy
capture feat/orphancopy
want_fail "16 a sign-off made on an unrelated history" \
  "sign-off not on this history"

# --- 17. no gate and a big diff -----------------------------------------
reset fix/y
printf '200\t150\tbin/coco.js\n' > "$T/numstat.txt"
capture fix/y --changed-numstat "$T/numstat.txt"
want_fail "17a no gate and 350 changed code lines" \
  "no gate and 350 changed lines (limit 300)"
printf '300\t60\tdocs/specs/big.md\n' > "$T/numstat.txt"
capture fix/y --changed-numstat "$T/numstat.txt"
want_ok "17b no gate and 360 changed lines, all docs and markdown"

# --- 18. protected paths need an infra sign-off -------------------------
reset fix/prot
mkdir -p "$WORK/.github/workflows"
printf 'name: coco-workflow\n' > "$WORK/.github/workflows/coco-workflow.yml"
git -C "$WORK" add .github/workflows/coco-workflow.yml
git -C "$WORK" commit -qm prot
capture fix/prot
want_fail "18a a protected path with no infra sign-off" \
  "protected path changed without infra sign-off: .github/workflows/coco-workflow.yml"
small_gate fix/prot
sign_stage infra steve
capture fix/prot
want_ok "18b a protected path with a steve infra sign-off"

# --- 19. a .pub key signs through ssh-agent -----------------------------
reset feat/agent
docs agent
init_gate feat/agent agent
sign_stage prd brain
sign_stage arch steve
AGENT_ENV="$(ssh-agent -a "$AGENT_SOCK" -s 2>&1)" || fail "19 cannot start ssh-agent: $AGENT_ENV"
eval "$AGENT_ENV" >/dev/null
[ -n "${SSH_AGENT_PID:-}" ] || fail "19 ssh-agent did not start"
AGENT_PID="$SSH_AGENT_PID"
ssh-add "$T/keys/steve" </dev/null >/dev/null 2>&1 || fail "19 ssh-add failed"
gate sign --stage plan --signer steve --key "$T/keys/steve.pub"
capture feat/agent
want_ok "19 a .pub key signs through ssh-agent"
ssh-agent -k >/dev/null 2>&1 || true
unset SSH_AUTH_SOCK SSH_AGENT_PID
AGENT_PID=""

# --- 20. workflow hygiene: pinned actions, no secrets, read-only ---------
WF="$HERE/.github/workflows/coco-workflow.yml"
[ -f "$WF" ] || fail "20 the reusable workflow file is missing"
bad="$(grep -nE '(^|[[:space:]])uses:' "$WF" | grep -vE '@[0-9a-f]{40}[[:space:]]+#' || true)"
[ -z "$bad" ] || fail "20a a uses: is not pinned to a 40-hex commit: $bad"
bad="$(grep -n 'secrets\.' "$WF" || true)"
[ -z "$bad" ] || fail "20b the workflow mentions secrets: $bad"
# Every permissions block holds exactly one entry, contents: read.
bad="$(awk '/^[[:space:]]*permissions:/ { p=1; ind=match($0,/[^ ]/); if ($0 !~ /permissions:[[:space:]]*$/) print NR": "$0; next }
  p && NF { if (match($0,/[^ ]/) <= ind) { p=0 } else if ($0 !~ /^[[:space:]]+contents: read[[:space:]]*$/) print NR": "$0 }' "$WF" || true)"
[ -z "$bad" ] || fail "20c permissions is not exactly read-only: $bad"
bad="$(grep -nE '^[[:space:]]+[a-z-]+:[[:space:]]*(write|none|read-all|write-all)' \
  "$WF" || true)"
[ -z "$bad" ] || fail "20d a permission value is not read: $bad"
ok "20 every action pinned, no secrets, permissions read-only"

# --- 21. the bootstrap PR is exempt from the protected-path rule ---------
git -C "$WORK" checkout -q main
git -C "$WORK" rm -q scripts/coco_gate.py
git -C "$WORK" commit -qm "drop the verifier for the bootstrap case"
git -C "$WORK" push -q origin main
git -C "$WORK" fetch -q origin
base_verifier
reset fix/boot
mkdir -p "$WORK/.githooks"
printf '#!/bin/sh\n' > "$WORK/.githooks/pre-push"
git -C "$WORK" add .githooks/pre-push
git -C "$WORK" commit -qm boot
capture fix/boot
want_ok "21 the bootstrap PR: protected paths are exempt"
case "$OUT" in
  *bootstrap*) ok "21b the notice says why the rule was skipped" ;;
  *) fail "21b no bootstrap notice: $OUT" ;;
esac

# --- 22. a repo with no signers file on base has not adopted the workflow ---
git -C "$WORK" checkout -q main
git -C "$WORK" rm -q .coco/allowed_signers
git -C "$WORK" commit -qm "no signers yet"
git -C "$WORK" push -q origin main
git -C "$WORK" fetch -q origin
reset feat/unadopted
capture feat/unadopted
want_ok "22 no signers on base: not adopted, the check passes"
case "$OUT" in
  *"not adopted"*) ok "22b the notice says the repo has not adopted the workflow" ;;
  *) fail "22b no not-adopted notice: $OUT" ;;
esac

capture feat/unadopted --base no-such-branch
[ "$RC" -ne 0 ] || fail "22c an unreadable base must fail, not count as not adopted: $OUT"
ok "22c an unreadable base fails closed"

echo "ok   all coco-workflow cases passed"
