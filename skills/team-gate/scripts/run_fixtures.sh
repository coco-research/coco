#!/usr/bin/env bash
# Run the team-gate self-tests against all static fixtures.
#
# Exports TEAM_FIXED_TS and TEAM_STATE_ROOT so every gate script can operate
# on deterministic fixtures without touching the live repository.
#
# Run from the repository root:
#   bash skills/team-gate/scripts/run_fixtures.sh
#
# Exits 0 when every script's self-test passes, 1 otherwise.

set -u -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"

# Create a temporary directory for all fixture state; clean it on exit.
TEAM_STATE_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEAM_STATE_ROOT"' EXIT

# Fixed timestamp so all fixtures produce deterministic content.
export TEAM_FIXED_TS="2026-01-01T00:00:00Z"
export TEAM_STATE_ROOT

# List of all gate scripts to test, in dependency order.
scripts=(
  "gate_state.py"
  "arch_gate.py"
  "check_artifacts.py"
  "run_gate.py"
  "prove_red.py"
  "verify_independent.py"
  "claim_evidence.py"
  "render_evidence.py"
  "render_approval.py"
  "render_pr_body.py"
  "ship_gate.py"
  "fix_gate.py"
  "brownfield_map.py"
  "hooks_selftest.py"
)

passed=0
total=${#scripts[@]}

for script in "${scripts[@]}"; do
  out="$(mktemp)"
  python3 "$HERE/$script" --self-test >"$out" 2>&1
  rc=$?
  printf '%s: exit %d\n' "$script" "$rc"
  if [ "$rc" -eq 0 ]; then
    ((passed++))
  else
    # A red suite that does not say why costs a debugging round: whoever reads
    # the CI log otherwise has to reproduce the failure locally first, and a
    # failure that reproduces only on one platform is the expensive case. Print
    # a bounded tail of the failing script's own output.
    tail -n 25 "$out" | sed 's/^/    /'
  fi
  rm -f "$out"
done

echo "team-gate fixtures: $passed/$total passed"

if [ "$passed" -ne "$total" ]; then
  exit 1
else
  exit 0
fi
