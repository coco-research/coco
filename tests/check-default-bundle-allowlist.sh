#!/usr/bin/env bash
# Guard: the default install bundle set must stay a reviewed, explicit
# allow-list (scripts/installable-bundles.sh) and must never silently grow by
# scanning systems/. That scan is exactly what once let systems/reverse-skill —
# a vendored reverse-engineering and security-testing bundle — join every
# default install the moment the directory existed, with no review at all.
#
# Run from repo root: bash tests/check-default-bundle-allowlist.sh

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
pass() { echo "  PASS: $1"; }
fail_() { echo "  FAIL: $1"; fail=1; }

# Every directory under systems/ that has been reviewed and given a disposition,
# whether or not it installs by default. Adding a directory to systems/ without
# adding it here is the drift this gate exists to catch. reverse-skill is named
# here deliberately excluded from the default set below; team and learning ship
# no SKILL.md or agent and were never installable either way.
KNOWN_BUNDLES=(brain cognee gsd hyperframes superintelligence m0 reverse-skill team learning)

echo "=== every systems/* directory has a reviewed disposition ==="
drift=0
for dir in systems/*/; do
  [[ -d "$dir" ]] || continue
  name="$(basename "$dir")"
  known=0
  for candidate in "${KNOWN_BUNDLES[@]}"; do
    [[ "$name" == "$candidate" ]] && known=1 && break
  done
  if [[ "$known" -eq 0 ]]; then
    fail_ "systems/$name is not in KNOWN_BUNDLES (tests/check-default-bundle-allowlist.sh) — review it, then decide whether scripts/installable-bundles.sh should add it to the default set"
    drift=1
  fi
done
[[ "$drift" -eq 0 ]] && pass "no undeclared directory under systems/"

echo ""
echo "=== reverse-skill is excluded from the default bundle set ==="
default_csv="$(bash scripts/installable-bundles.sh)"
if [[ ",$default_csv," == *,reverse-skill,* ]]; then
  fail_ "reverse-skill is in the default bundle set: $default_csv"
else
  pass "default bundle set does not include reverse-skill ($default_csv)"
fi

echo ""
echo "=== reverse-skill stays reachable through an explicit --systems flag ==="
tmp_home="$(mktemp -d)"
out="$(HOME="$tmp_home" AGENTS_HOME="$tmp_home/agents" PI_AGENT_HOME="$tmp_home/pi-agent" \
  bash adapters/pi-desktop/install.sh --dry-run --systems reverse-skill 2>&1 || true)"
rm -rf "$tmp_home"
if echo "$out" | grep -q 'Bundles.*reverse-skill'; then
  pass "adapters/pi-desktop/install.sh --systems reverse-skill selects the bundle"
else
  fail_ "--systems reverse-skill did not select the bundle:"
  echo "$out" | sed 's/^/    /'
fi

echo ""
echo "=== Summary ==="
if [[ "$fail" -eq 0 ]]; then
  echo "  all default-bundle-allowlist checks passed"
  exit 0
fi
echo "  some check(s) failed"
exit 1
