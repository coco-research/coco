#!/usr/bin/env bash
# Guard: every superintelligence roster front door carries the same frontmatter
# key set.
#
# The nine original systems/superintelligence/*/SKILL.md files drifted into two
# shapes: six carried a `name` slug, three carried none, and none carried a
# `description`, and lint-frontmatter.yml never walked this depth, so the drift
# shipped silently. This gate checks the normalized shape directly, at the depth
# the widened lint gate still does not reach, and it runs in the required
# lint-and-test job rather than on the self-hosted lint-frontmatter runner that has
# never once executed successfully.
#
# Files are enumerated with `git ls-files`, not a filesystem walk: a filesystem
# walk previously picked up nested git worktrees under .claude/worktrees/ and
# false-positived on paths that are not part of this repository's own tree.
#
# Run from repo root: bash tests/check-roster-frontmatter.sh

set -euo pipefail
cd "$(dirname "$0")/.."

REQUIRED_KEYS=(name description team_id team_name last_updated schema_version)
# personas_count and cells_count are deliberately excluded: nothing in the tree
# reads them from a roster SKILL.md's frontmatter, and hand-copying a fact the
# tree does not regenerate is exactly the stale-count defect this repository has
# spent the week cleaning up elsewhere.
FORBIDDEN_KEYS=(personas_count cells_count)

fail=0
checked=0

while IFS= read -r -d '' file; do
  checked=$((checked + 1))

  fm=$(python3 - "$file" <<'PY'
import sys, yaml
path = sys.argv[1]
text = open(path).read()
if not text.startswith('---'):
    print('__NO_FRONTMATTER__')
    sys.exit(0)
parts = text.split('---', 2)
if len(parts) < 3:
    print('__NO_FRONTMATTER__')
    sys.exit(0)
try:
    data = yaml.safe_load(parts[1]) or {}
except yaml.YAMLError as e:
    print(f'__YAML_ERROR__:{e}')
    sys.exit(0)
print('\n'.join(sorted(str(k) for k in data.keys())))
PY
)

  if [ "$fm" = "__NO_FRONTMATTER__" ]; then
    echo "  FAIL: $file has no frontmatter block"
    fail=1
    continue
  fi
  if [[ "$fm" == __YAML_ERROR__:* ]]; then
    echo "  FAIL: $file has malformed YAML frontmatter: ${fm#__YAML_ERROR__:}"
    fail=1
    continue
  fi

  for key in "${REQUIRED_KEYS[@]}"; do
    if ! grep -qx "$key" <<<"$fm"; then
      echo "  FAIL: $file is missing required key \"$key\""
      fail=1
    fi
  done
  for key in "${FORBIDDEN_KEYS[@]}"; do
    if grep -qx "$key" <<<"$fm"; then
      echo "  FAIL: $file carries hand-maintained \"$key\" in frontmatter (not consumed anywhere; drop it)"
      fail=1
    fi
  done
done < <(git ls-files -z 'systems/superintelligence/*/SKILL.md')

echo ""
echo "=== Summary ==="
echo "  checked $checked roster front doors"
if [ "$fail" -eq 0 ]; then
  echo "  all roster front doors carry the normalized key set"
  exit 0
fi
exit 1
