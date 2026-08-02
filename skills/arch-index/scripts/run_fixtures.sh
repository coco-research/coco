#!/usr/bin/env bash
# Assert the validator's behaviour against all three fixtures.
#
# Run from the repository root:
#   bash skills/arch-index/scripts/run_fixtures.sh
#
# Exits 0 when every assertion holds, 1 otherwise. This is the regression gate for
# any change to validate_index.py.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
V="$HERE/validate_index.py"
F="$HERE/fixtures"
fail=0

pass() { printf '  PASS  %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fail=1; }

echo "validator fixtures — repo root $ROOT"
echo

# 1. good.json must exit 0 with no violations.
out="$(python3 "$V" "$F/good.json" --repo-root "$ROOT" --quiet 2>/dev/null)"
rc=$?
if [ "$rc" -eq 0 ] && [ -z "$out" ]; then
  pass "good.json exits 0 with no violations"
else
  bad "good.json expected exit 0 and no output, got exit $rc: $out"
fi

# 1b. good.json must verify nine paths against this repository.
verified="$(python3 "$V" "$F/good.json" --repo-root "$ROOT" 2>&1 >/dev/null \
  | sed -n 's/^paths verified: \([0-9]*\).*/\1/p')"
if [ "$verified" = "9" ]; then
  pass "good.json verifies 9 paths"
else
  bad "good.json expected 9 verified paths, got '${verified:-none}'"
fi

# 2. bad-paths.json must exit 1 and name the fabricated path.
out="$(python3 "$V" "$F/bad-paths.json" --repo-root "$ROOT" --quiet 2>/dev/null)"
rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "src/nonexistent"; then
  pass "bad-paths.json exits 1 and names src/nonexistent"
else
  bad "bad-paths.json expected exit 1 naming src/nonexistent, got exit $rc"
fi

# 3. bad-invariants.json must exit 1 with exactly four violation lines.
lines="$(python3 "$V" "$F/bad-invariants.json" --repo-root "$ROOT" --quiet 2>/dev/null \
  | wc -l | tr -d ' ')"
if [ "$lines" = "4" ]; then
  pass "bad-invariants.json emits exactly 4 violation lines"
else
  bad "bad-invariants.json expected 4 violation lines, got $lines"
fi

# 3b. Those four lines must be checks 2, 7, 8 and 10 — no substitutions.
got="$(python3 "$V" "$F/bad-invariants.json" --repo-root "$ROOT" --quiet 2>/dev/null \
  | sed -n 's/^CHECK \([0-9]*\) .*/\1/p' | sort -n | tr '\n' ',' )"
if [ "$got" = "2,7,8,10," ]; then
  pass "bad-invariants.json trips exactly checks 2, 7, 8, 10"
else
  bad "bad-invariants.json expected checks 2,7,8,10, got ${got:-none}"
fi

# 4. A missing index must be a violation, never a silent pass.
out="$(python3 "$V" "$F/does-not-exist.json" --repo-root "$ROOT" --quiet 2>/dev/null)"
rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "CHECK 0"; then
  pass "a missing index exits 1 as CHECK 0, never a pass"
else
  bad "a missing index expected exit 1 with CHECK 0, got exit $rc"
fi

# ---------------------------------------------------------------------------
# Forward plans: verify_arch_plan.py
# ---------------------------------------------------------------------------
echo
echo "forward plan fixtures"

P="$HERE/verify_arch_plan.py"
HEADSHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo '')"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

stamp() {
  # Fixtures ship declaredAtCommit as a placeholder because the real value is
  # repository-specific. Stamp it with the given commit before running.
  python3 -c "
import json, pathlib, sys
d = json.loads(pathlib.Path(sys.argv[1]).read_text())
d['declaredAtCommit'] = sys.argv[3]
pathlib.Path(sys.argv[2]).write_text(json.dumps(d))
" "$1" "$2" "$3"
}

stamp "$F/plan-good.json"      "$TMP/good.json"    "$HEADSHA"
stamp "$F/plan-unbuilt.json"   "$TMP/unbuilt.json" "$HEADSHA"
stamp "$F/plan-bad-shape.json" "$TMP/bad.json"     "$HEADSHA"

# 5. A well-formed plan passes shape checks.
python3 "$P" "$TMP/good.json" --declare --quiet >/dev/null 2>&1 \
  && pass "plan-good passes --declare" \
  || bad "plan-good should pass --declare"

# 6. And passes verification, because its declared paths already exist here.
python3 "$P" "$TMP/good.json" --verify --repo-root "$ROOT" --quiet >/dev/null 2>&1 \
  && pass "plan-good passes --verify" \
  || bad "plan-good should pass --verify"

# 7. THE CENTRAL CASE. A plan declaring an unbuilt component must pass --declare
#    (nothing is built yet, so path existence is not a defect) and fail --verify
#    (after the build, the declared paths must be real). This asymmetry is the whole
#    reason the forward stage works at all.
python3 "$P" "$TMP/unbuilt.json" --declare --quiet >/dev/null 2>&1 \
  && pass "plan-unbuilt passes --declare (paths not yet built is not a defect)" \
  || bad "plan-unbuilt should pass --declare"

out="$(python3 "$P" "$TMP/unbuilt.json" --verify --repo-root "$ROOT" --quiet 2>/dev/null)"
rc=$?
if [ "$rc" -eq 1 ] && printf '%s' "$out" | grep -q "services/webhooks"; then
  pass "plan-unbuilt FAILS --verify naming the unbuilt path"
else
  bad "plan-unbuilt should fail --verify naming services/webhooks, got exit $rc"
fi

lines="$(printf '%s' "$out" | grep -c 'BUILT 1')"
[ "$lines" = "2" ] \
  && pass "plan-unbuilt reports both declared paths as missing" \
  || bad "plan-unbuilt expected 2 BUILT 1 lines, got $lines"

# 8. Shape violations are caught before the build, and existence checks are not
#    run against a malformed plan (which would bury the real problem in noise).
got="$(python3 "$P" "$TMP/bad.json" --declare --quiet 2>/dev/null \
  | sed -n 's/^SHAPE \([0-9]*\) .*/\1/p' | sort -n | tr '\n' ',')"
[ "$got" = "3,4,9,10," ] \
  && pass "plan-bad-shape trips exactly SHAPE 3, 4, 9, 10" \
  || bad "plan-bad-shape expected SHAPE 3,4,9,10, got ${got:-none}"

n="$(python3 "$P" "$TMP/bad.json" --verify --repo-root "$ROOT" --quiet 2>/dev/null \
  | grep -c 'BUILT')"
[ "$n" = "0" ] \
  && pass "a malformed plan reports no BUILT checks (shape failures reported alone)" \
  || bad "malformed plan should not run BUILT checks, got $n"

# 9. Out-of-scope enforcement fires when a declared-off-limits tree really changed.
if [ -n "$HEADSHA" ]; then
  oldsha="$(git -C "$ROOT" log --format=%H | sed -n '5p')"
  changed="$(git -C "$ROOT" diff --name-only "$oldsha"..HEAD 2>/dev/null \
    | grep '/' | cut -d/ -f1 | sort -u | head -1)"
  if [ -n "$changed" ]; then
    python3 -c "
import json, pathlib, sys
d = json.loads(pathlib.Path(sys.argv[1]).read_text())
d['declaredAtCommit'] = sys.argv[3]
d['outOfScope'] = [sys.argv[4]]
d['components'] = [c for c in d['components']
                   if sys.argv[4] not in c['intendedPaths']['directories']]
for c in d['components']:
    c['connections'] = []
pathlib.Path(sys.argv[2]).write_text(json.dumps(d))
" "$F/plan-good.json" "$TMP/oos.json" "$oldsha" "$changed"
    o="$(python3 "$P" "$TMP/oos.json" --verify --repo-root "$ROOT" --quiet 2>/dev/null)"
    if printf '%s' "$o" | grep -q 'BUILT 2 out-of-scope'; then
      pass "out-of-scope violations detected under '$changed'"
    else
      bad "out-of-scope violations under '$changed' were not detected"
    fi
  else
    echo "  SKIP  out-of-scope check: no changed top-level directory in range"
  fi
fi

# 10. An unreadable plan exits 2 and is never mistaken for a pass.
python3 "$P" "$TMP/does-not-exist.json" --declare --quiet >/dev/null 2>&1
[ "$?" -eq 2 ] \
  && pass "a missing plan exits 2, never a pass" \
  || bad "a missing plan should exit 2"

echo
if [ "$fail" -eq 0 ]; then
  echo "all fixture assertions hold"
else
  echo "fixture assertions FAILED"
fi
exit "$fail"
