#!/usr/bin/env bash
# Regression test for issue #473: a bare "149" in README (e.g. the core-install
# "(149 active assets)" total) must not trip the skills leftover check.
# Runs the real check-asset-counts.sh against a fixture repo whose README holds
# 149 only as a non-skills count.
set -uo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"

mkdir -p "$tmp/tests" "$tmp/docs"
tr -d '\r' < "$repo/tests/check-asset-counts.sh" > "$tmp/tests/check-asset-counts.sh"  # tolerate CRLF checkouts
cp "$repo/docs/asset-counts.json" "$tmp/docs/"
cp "$repo/package.json" "$tmp/"
cat > "$tmp/README.md" <<'EOF'
# coco

<sub><strong>Core install:</strong> 79 skills + 46 commands + 17 agents + 15 rules (149 active assets).</sub>
EOF

out="$(bash "$tmp/tests/check-asset-counts.sh" 2>&1)"
rm -rf "$tmp"
if grep -q "README still contains 149" <<<"$out"; then
  echo "FAIL: bare 149 (non-skills count) tripped the skills leftover check"
  grep "149" <<<"$out"
  exit 1
fi
if ! grep -q "no leftover 149 in README" <<<"$out"; then
  echo "FAIL: checker did not reach the leftover check (vacuous pass guard)"
  exit 1
fi
echo "PASS: non-skills 149 in README does not trip the leftover check"
exit 0
