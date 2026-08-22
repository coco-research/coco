#!/usr/bin/env bash
# Guard: shipped asset counts must agree with the generated truth.
#
# docs/asset-counts.json is produced by scripts/build-index.py from a full walk of
# the tree, so it is correct by construction. This gate fails when any *shipped*
# count — README badge, package.json description, README prose tables — drifts
# from it. Run from repo root: bash tests/check-asset-counts.sh
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
fail_() { echo "  FAIL: $1"; fail=1; }
pass() { echo "  PASS: $1"; }

if [ ! -f docs/asset-counts.json ]; then
  echo "docs/asset-counts.json missing — run python3 scripts/build-index.py"
  exit 1
fi

SKILLS=$(python3 -c "import json;print(json.load(open('docs/asset-counts.json'))['skills']['total'])")
COMMANDS=$(python3 -c "import json;print(json.load(open('docs/asset-counts.json'))['commands']['total'])")
AGENTS=$(python3 -c "import json;print(json.load(open('docs/asset-counts.json'))['agents']['total'])")

echo "=== truth: docs/asset-counts.json ==="
echo "  skills=$SKILLS commands=$COMMANDS agents=$AGENTS"

echo ""
echo "=== README badge ==="
BADGE_SKILLS=$(grep -oE 'shields\.io/badge/skills-[0-9]+' README.md | grep -oE '[0-9]+$' | head -1 || true)
if [ -n "$BADGE_SKILLS" ]; then
  if [ "$BADGE_SKILLS" = "$SKILLS" ]; then
    pass "skills badge ($BADGE_SKILLS) matches"
  else
    fail_ "README skills badge says $BADGE_SKILLS, disk truth is $SKILLS"
  fi
else
  pass "no numeric skills badge found (nothing to check)"
fi

echo ""
echo "=== package.json description ==="
PKG_DESC=$(python3 -c "import json;print(json.load(open('package.json'))['description'])")
for n in $(printf '%s' "$PKG_DESC" | grep -oE '[0-9]+ (skills|commands|agents)' | grep -oE '^[0-9]+'); do :; done
# Check each "<N> <word>" claim in the description against the JSON.
while read -r n word; do
  [ -n "$n" ] || continue
  case "$word" in
    skills)   [ "$n" = "$SKILLS" ]   || fail_ "package.json claims $n skills, truth is $SKILLS" ;;
    commands) [ "$n" = "$COMMANDS" ] || fail_ "package.json claims $n commands, truth is $COMMANDS" ;;
    agents)   [ "$n" = "$AGENTS" ]   || fail_ "package.json claims $n agents, truth is $AGENTS" ;;
  esac
done <<EOF
$(printf '%s' "$PKG_DESC" | grep -oE '[0-9]+ (skills|commands|agents)' || true)
EOF
grep -qE '[0-9]+ (skills|commands|agents)' <<<"$PKG_DESC" \
  && pass "package.json count claims all match" \
  || pass "package.json makes no count claims (fine)"

echo ""
echo "=== README prose asset table ==="
# The <td><h3>N</h3>...<sub>Skills</sub></td> block. Extract pairs and compare.
PROSE_SKILLS=$(python3 - "$SKILLS" <<'PY'
import re, sys
text = open('README.md').read()
truth = sys.argv[1]
m = re.search(r'<h3>(\d+)</h3><sub>Skills</sub>', text)
print(m.group(1) if m else '')
PY
)
if [ -n "$PROSE_SKILLS" ]; then
  [ "$PROSE_SKILLS" = "$SKILLS" ] && pass "prose Skills cell matches" \
    || fail_ "README prose Skills cell says $PROSE_SKILLS, truth is $SKILLS"
else
  pass "no prose Skills cell found (nothing to check)"
fi

echo ""
echo "=== Summary ==="
if [ "$fail" -eq 0 ]; then
  echo "  all shipped counts agree with docs/asset-counts.json"
  exit 0
fi
echo "  fix by regenerating indexes AND updating README/package.json to match"
exit 1
