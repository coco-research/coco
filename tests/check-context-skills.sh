#!/usr/bin/env bash
# Guard: the four vendored context-engineering skills keep name == folder, and
# every offline example script they ship still runs.
#
# Offline only: no network, no API keys. Each script's stub paths are used as
# shipped. A script that stops on ModuleNotFoundError (a package this Python
# lacks) is skipped with the reason printed, never faked. A skill with no script
# says so and moves on.
#
# Paths stay relative to the repo root so the word-split loop survives a
# checkout path with spaces in it. Bash 3.2 safe.
# Run from anywhere: bash tests/check-context-skills.sh

set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)

SKILLS="context-degradation memory-systems multi-agent-patterns harness-engineering"
PY=${PYTHON:-python3}
"$PY" -I -c pass || { echo "FAIL: $PY does not run"; exit 1; }
RUN_DIR=$(mktemp -d)
trap 'rm -rf "$RUN_DIR"' EXIT

fail=0
ran=0
skipped=0

for s in $SKILLS; do
  dir="skills/$s"
  if [ ! -f "$dir/SKILL.md" ]; then
    echo "FAIL $s: missing SKILL.md"
    fail=1
    continue
  fi
  name=$(sed -n 's/^name:[[:space:]]*//p' "$dir/SKILL.md" | head -n 1)
  if [ "$name" != "$s" ]; then
    echo "FAIL $s: frontmatter name is '$name'"
    fail=1
  fi

  scripts=$(ls "$dir"/scripts/*.py "$dir"/tests/test_*.py 2>/dev/null || true)
  if [ -z "$scripts" ]; then
    echo "NONE $s: no example script ships with this skill"
    continue
  fi

  for f in $scripts; do
    # -E -s, not -I: -I also drops the script's own folder from sys.path, so a
    # sibling module the skill ships would fail to import.
    if (cd "$RUN_DIR" && "$PY" -E -s "$ROOT/$f" >"$RUN_DIR/out.txt" 2>&1); then
      echo "PASS $f"
      ran=$((ran + 1))
    elif missing=$(sed -n "s/^ModuleNotFoundError: No module named '\([^']*\)'.*/\1/p" "$RUN_DIR/out.txt" | tail -n 1) && [ -n "$missing" ]; then
      echo "SKIP $f: needs $missing, not installed (offline, but not stdlib)"
      skipped=$((skipped + 1))
    else
      echo "FAIL $f:"
      tail -n 20 "$RUN_DIR/out.txt"
      fail=1
    fi
  done
done

echo "context skills: $ran ran, $skipped skipped"
exit "$fail"
