#!/usr/bin/env bash
# scripts/check-personas.py: the good fixture passes, and each bad fixture fails
# naming only its own rule. Then the checker must run over the real tree without
# crashing (exit 0 or 1; real-persona failures are reported, not gated here).
# Works under bash 5 and macOS /bin/bash 3.2.
# Run from anywhere: bash tests/check-personas-test.sh
set -u
cd "$(dirname "$0")/.."

CHECK=scripts/check-personas.py
DIR=tests/fixtures/personas/edtech/personas
fail=0
fail_() { echo "  FAIL: $1"; fail=1; }
pass() { echo "  PASS: $1"; }

if out=$(python3 "$CHECK" "$DIR/good.md" 2>/dev/null); then
  pass "good.md -> exit 0"
else
  fail_ "good.md should pass, got: $out"
fi

for rule in a b c d e f g h; do
  f=$(ls "$DIR"/bad-"$rule"-*.md 2>/dev/null | head -n 1)
  if [ -z "$f" ]; then fail_ "no fixture for rule ($rule)"; continue; fi
  out=$(python3 "$CHECK" "$f" 2>/dev/null)
  rc=$?
  if [ "$rc" -ne 1 ]; then fail_ "$f: exit $rc, want 1"; continue; fi
  if ! printf '%s\n' "$out" | grep -q "($rule)"; then fail_ "$f: rule ($rule) not named: $out"; continue; fi
  if printf '%s\n' "$out" | grep -v "($rule)" | grep -q .; then fail_ "$f: other rules fired: $out"; continue; fi
  pass "$(basename "$f") -> exit 1 naming ($rule) only"
done

# A Python traceback also exits 1, so require the summary line over every file and no traceback.
shopt -s nullglob
real=(systems/superintelligence/*/personas/*.md)
shopt -u nullglob
if [ "${#real[@]}" -eq 0 ]; then
  fail_ "glob matched no persona files; real tree was not checked"
else
  err=$(python3 "$CHECK" "${real[@]}" 2>&1 >/dev/null)
  rc=$?
  if [ "$rc" -le 1 ] && printf '%s\n' "$err" | grep -q "^check-personas: [0-9]*/${#real[@]} pass$" \
     && ! printf '%s\n' "$err" | grep -q Traceback; then
    pass "real tree checked: $err"
  else
    fail_ "real tree run crashed (exit $rc): $err"
  fi
fi

[ "$fail" -eq 0 ] && echo "check-personas-test: all passed" || echo "check-personas-test: FAILED"
exit "$fail"
