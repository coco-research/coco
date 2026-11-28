#!/usr/bin/env bash
# Regression tests for the README skills-count drift tripwire.
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mkdir -p "$tmp/tests" "$tmp/docs"
tr -d '\r' < "$repo/tests/check-asset-counts.sh" > "$tmp/tests/check-asset-counts.sh"
cp "$repo/docs/asset-counts.json" "$tmp/docs/"
cp "$repo/package.json" "$tmp/"

run_checker() {
  if bash "$tmp/tests/check-asset-counts.sh" > "$tmp/output" 2>&1; then
    checker_status=0
  else
    checker_status=$?
  fi
}

assert_no_skills_drift() {
  if grep -q 'ASSET_COUNT_SKILLS_DRIFT' "$tmp/output"; then
    echo "FAIL: legitimate non-skills count tripped the skills drift check"
    grep 'ASSET_COUNT_SKILLS_DRIFT' "$tmp/output"
    exit 1
  fi
  if ! grep -q 'ASSET_COUNT_SKILLS_CHECK_OK' "$tmp/output"; then
    echo "FAIL: checker did not reach the skills drift check (status $checker_status)"
    tail -30 "$tmp/output"
    exit 1
  fi
}

assert_skills_drift() {
  if ! grep -q 'ASSET_COUNT_SKILLS_DRIFT' "$tmp/output"; then
    echo "FAIL: skills count drift was not detected (checker status $checker_status)"
    tail -30 "$tmp/output"
    exit 1
  fi
}

cat > "$tmp/README.md" <<'EOF'
# coco

<sub><strong>Core install:</strong> 79 skills + 46 commands + 17 agents + 15 rules (149 active assets).</sub>
EOF
run_checker
assert_no_skills_drift
echo "PASS: non-skills 149 in README does not trip the skills drift check"

for phrase in '149 Skills' 'Skills: 149' '<h3>149</h3><sub>Skills</sub>' '<h3>149</h3><sub>skills</sub>'; do
  cat > "$tmp/README.md" <<EOF
# coco

$phrase
EOF
  run_checker
  assert_skills_drift
done

echo "PASS: common skills-count phrasings trip the skills drift check"
