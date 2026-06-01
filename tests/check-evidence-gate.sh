#!/usr/bin/env bash
# Guard: the test-integrity ("evidence gate") language must stay present in the
# /team pipeline command files. This prevents a future edit from silently
# removing the gates that stop /team:ship from reporting false test results.
#
# Run from repo root: bash tests/check-evidence-gate.sh

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
T=commands/team

require() {
  # require <file> <grep-pattern> <human label>
  if ! grep -qiE "$2" "$1" 2>/dev/null; then
    echo "  MISSING in $1: $3"
    fail=1
  fi
}

# Shared protocol must exist and carry its core rules.
if [ ! -f "$T/evidence.md" ]; then
  echo "  MISSING: $T/evidence.md (Test Evidence Protocol)"
  fail=1
else
  require "$T/evidence.md" "evidence or it did" "guiding principle"
  require "$T/evidence.md" "skipped.*(never|≠).*pass|never a pass" "skip != pass rule"
  require "$T/evidence.md" "EVIDENCE\.md"                  "EVIDENCE.md artifact"
fi

# Ship pipeline must keep the hard gates + PR-open gate.
require "$T/ship.md" "Hard Gate"        "hard gate section"
require "$T/ship.md" "Stage 8"          "test-execution gate"
require "$T/ship.md" "Stage 11"         "independent-verify gate"
require "$T/ship.md" "Stage 12"         "claim-vs-evidence gate"
require "$T/ship.md" "EVIDENCE\.md"     "evidence artifact ref"
require "$T/ship.md" "BLOCK"            "BLOCK semantics"

# Test / develop pipelines must run the protocol, not narrate.
require "$T/test.md"    "Test Evidence Protocol|team:evidence" "protocol ref"
require "$T/test.md"    "UNVERIFIED"                            "skip handling"
require "$T/develop.md" "EVIDENCE\.md"                          "evidence capture"

# Verify must be independent re-execution, not self-report trust.
require "$T/verify.md" "Independent Re-Execution|independent re-exec" "independent re-exec"
require "$T/verify.md" "must NOT read the builder|not read the builder" "independence rule"

if [ "$fail" -ne 0 ]; then
  echo "FAIL: /team test-integrity gates are incomplete. See TEAM-SHIP-TESTING-INTEGRITY plan."
  exit 1
fi

echo "PASS: /team evidence-gate language present."
