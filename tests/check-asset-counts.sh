#!/usr/bin/env bash
# Guard: shipped asset counts must agree with the generated truth.
#
# docs/asset-counts.json is produced by scripts/build-index.py from a full walk of
# the tree, so it is correct by construction. This gate fails when any *public*
# count — README badge, package.json description, README prose tables — drifts
# from it.
#
# Command layers (Mira, 2026-08-29):
#   commands.shipped   = in-repo command files (labeled field, not the public total)
#   commands.generated_si = /SI-* commands generated at install from team registries
#   commands.customer_facing = public total = shipped + generated_si (280 = 38 + 242)
# Do not stamp the public command count to commands.shipped.
# Run from repo root: bash tests/check-asset-counts.sh
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
COMMANDS=$(python3 -c "import json;print(json.load(open('docs/asset-counts.json'))['commands']['customer_facing'])")
SHIPPED=$(python3 -c "import json;print(json.load(open('docs/asset-counts.json'))['commands']['shipped'])")
GENERATED=$(python3 -c "import json;print(json.load(open('docs/asset-counts.json'))['commands']['generated_si'])")
AGENTS=$(python3 -c "import json;print(json.load(open('docs/asset-counts.json'))['agents']['total'])")

echo "=== truth: docs/asset-counts.json ==="
echo "  skills=$SKILLS commands.customer_facing=$COMMANDS (public) shipped=$SHIPPED generated=$GENERATED agents=$AGENTS"

if [ "$COMMANDS" != "$((SHIPPED + GENERATED))" ]; then
  fail_ "commands.customer_facing ($COMMANDS) != shipped ($SHIPPED) + generated ($GENERATED)"
else
  pass "commands.customer_facing == shipped + generated"
fi

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

BADGE_COMMANDS=$(grep -oE 'shields\.io/badge/commands-[0-9]+' README.md | grep -oE '[0-9]+$' | head -1 || true)
if [ -n "$BADGE_COMMANDS" ]; then
  if [ "$BADGE_COMMANDS" = "$COMMANDS" ]; then
    pass "commands badge ($BADGE_COMMANDS) matches public total"
  else
    fail_ "README commands badge says $BADGE_COMMANDS, public total is $COMMANDS (do not stamp shipped=$SHIPPED as public)"
  fi
else
  pass "no numeric commands badge found (nothing to check)"
fi

echo ""
echo "=== package.json description ==="
PKG_DESC=$(python3 -c "import json;print(json.load(open('package.json'))['description'])")
while read -r n word; do
  [ -n "$n" ] || continue
  case "$word" in
    skills)   [ "$n" = "$SKILLS" ]   || fail_ "package.json claims $n skills, truth is $SKILLS" ;;
    commands)
      if [ "$n" = "$COMMANDS" ]; then
        :
      elif [ "$n" = "$SHIPPED" ] && [ "$SHIPPED" != "$COMMANDS" ]; then
        fail_ "package.json stamps public commands to shipped files ($n); public total is $COMMANDS"
      else
        fail_ "package.json claims $n commands, public total is $COMMANDS"
      fi
      ;;
    agents)   [ "$n" = "$AGENTS" ]   || fail_ "package.json claims $n agents, truth is $AGENTS" ;;
  esac
done <<CLAIMS
$(printf '%s' "$PKG_DESC" | grep -oE '[0-9]+ (skills|commands|agents)' || true)
CLAIMS
grep -qE '[0-9]+ (skills|commands|agents)' <<<"$PKG_DESC" \
  && pass "package.json count claims all match public totals" \
  || pass "package.json makes no count claims (fine)"

echo ""
echo "=== README prose asset table ==="
PROSE_SKILLS=$(python3 -c "import re; t=open('README.md').read(); m=re.search(r'<h3>(\\d+)</h3><sub>Skills</sub>', t); print(m.group(1) if m else '')")
if [ -n "$PROSE_SKILLS" ]; then
  [ "$PROSE_SKILLS" = "$SKILLS" ] && pass "prose Skills cell matches" \
    || fail_ "README prose Skills cell says $PROSE_SKILLS, truth is $SKILLS"
else
  pass "no prose Skills cell found (nothing to check)"
fi

PROSE_COMMANDS=$(python3 -c "import re; t=open('README.md').read(); m=re.search(r'<h3>(\\d+)</h3><sub>Slash Commands</sub>', t); print(m.group(1) if m else '')")
if [ -n "$PROSE_COMMANDS" ]; then
  [ "$PROSE_COMMANDS" = "$COMMANDS" ] && pass "prose Slash Commands cell matches public total" \
    || fail_ "README prose Slash Commands cell says $PROSE_COMMANDS, public total is $COMMANDS"
else
  pass "no prose Slash Commands cell found (nothing to check)"
fi



echo ""
echo "=== README Technical Specifications Total Skills ==="
SPEC_SKILLS=$(python3 -c "import re; t=open('README.md').read(); m=re.search(r'<tr><td><strong>Total Skills</strong></td><td>(\\d+)', t); print(m.group(1) if m else '')")
if [ -n "$SPEC_SKILLS" ]; then
  if [ "$SPEC_SKILLS" = "$SKILLS" ]; then
    pass "spec Total Skills ($SPEC_SKILLS) matches"
  else
    fail_ "README spec Total Skills says $SPEC_SKILLS, customer-facing is $SKILLS (do not leave a third skills number)"
  fi
else
  pass "no spec Total Skills row (nothing to check)"
fi
# Catch the exact drift class Pike found: a leftover 149 that is not skills.total.
LEFTOVER_149=$(grep -nE '\b149\b' README.md || true)
if [ -n "$LEFTOVER_149" ] && [ "$SKILLS" != "149" ]; then
  fail_ "README still contains 149 (third skills number); customer-facing is $SKILLS: $LEFTOVER_149"
else
  pass "no leftover 149 in README"
fi

echo ""
echo "=== .claude-plugin.json description ==="
if [ -f .claude-plugin.json ]; then
  if python3 tests/check-plugin-counts.py; then
    pass "plugin json customer-facing counts match"
  else
    fail_ "plugin json customer-facing counts mismatch"
  fi
else
  pass "no .claude-plugin.json (nothing to check)"
fi

echo ""
echo "=== Summary ==="
if [ "$fail" -eq 0 ]; then
  echo "  all shipped public counts agree with docs/asset-counts.json"
  exit 0
fi
echo "  fix by regenerating indexes AND updating README/package.json to match public totals"
echo "  (commands.shipped is a labeled field; do not use it as the public command count)"
exit 1
