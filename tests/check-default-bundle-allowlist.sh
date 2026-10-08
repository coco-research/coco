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
echo "=== Formula/coco.rb caveats match installer behaviour (--systems replaces; uninstall covers install.md's dirs) ==="
# --systems REPLACES the default set, so a caveat example must say so, never "add bundles".
if ! grep -qE -- '--systems' Formula/coco.rb; then
  fail_ "Formula/coco.rb caveats no longer contain a --systems example"
elif grep -E -- '--systems' Formula/coco.rb | grep -v -F 'replaces the default set' >/dev/null; then
  fail_ "Formula/coco.rb has a --systems example that does not say it replaces the default set"
else
  pass "every --systems example in Formula/coco.rb says it replaces the default set"
fi
# The Formula's symlink-uninstall find must cover every dir install.md's find covers.
# Only the "Symlink-based adapters" uninstall code block, not every find/for line in install.md.
uninstall_block="$(awk '/^## Uninstall/{u=1} u&&/^Symlink-based adapters/{s=1} s&&/^```bash/{c=1;next} c&&/^```/{exit} c' docs/install.md)"
doc_dirs="$(printf '%s\n' "$uninstall_block" | grep -E '^(find|for) ' | grep -oE '(~/\.[^ /]+|\$HOME/Library[^"]*|\$\{?XDG_CONFIG_HOME[^"]*|"[^"]+")' | tr -d '\"' | grep -v '^\$base' | grep -v '^\${CLONE}' | sort -u || true)"
formula_find="$(grep -E '(find|for) ' Formula/coco.rb | tr -d '\"' | tr ';' ' ' | tr '\n' ' ' || true)"

# Verify the test itself: a simulated doc finding a path the formula lacks must fail.
mock_doc_dirs="$(echo "$doc_dirs" | sed 's/^Code$/Code - Fake/')"
mock_missing=""
if [[ "$mock_doc_dirs" == "$doc_dirs" ]]; then
  fail_ "self-test could not build a mock: docs/install.md has no 'Code' path to mutate"
  mock_missing="mock"  # skip the vacuous-pass branch below
fi
while IFS= read -r d; do
  [[ -n "$d" ]] || continue
  [[ " $formula_find " == *" $d "* ]] || mock_missing="$mock_missing $d"
done <<< "$mock_doc_dirs"
if [[ -z "$mock_missing" ]]; then
  fail_ "self-test failed: modifying docs/install.md path to 'Code - Fake' did not trigger a failure"
else
  pass "self-test passed: mismatch between docs/install.md and Formula/coco.rb is caught"
fi

missing=""
while IFS= read -r d; do
  [[ -n "$d" ]] || continue
  [[ " $formula_find " == *" $d "* ]] || missing="$missing $d"
done <<< "$doc_dirs"
if [[ -z "$doc_dirs" ]]; then
  fail_ "could not read the uninstall find line from docs/install.md"
elif [[ -n "$missing" ]]; then
  fail_ "Formula/coco.rb uninstall find misses:$missing (docs/install.md covers: $(echo $doc_dirs | tr '\n' ' '))"
else
  pass "Formula/coco.rb uninstall find covers every dir docs/install.md covers"
fi

echo ""
echo "=== Summary ==="
if [[ "$fail" -eq 0 ]]; then
  echo "  all default-bundle-allowlist checks passed"
  exit 0
fi
echo "  some check(s) failed"
exit 1
