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
)

passed=0
total=${#scripts[@]}

for script in "${scripts[@]}"; do
  python3 "$HERE/$script" --self-test >/dev/null 2>&1
  rc=$?
  if [ "$rc" -eq 0 ]; then
    ((passed++))
  fi
  printf '%s: exit %d\n' "$script" "$rc"
done

echo "team-gate fixtures: $passed/$total passed"

if [ "$passed" -ne "$total" ]; then
  exit 1
else
  exit 0
fi
