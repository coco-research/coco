#!/usr/bin/env bash
# Guard: references inside systems/gsd/ must be legitimate, in one of two ways.
#
# The vendored systems/gsd/ bundle ships only agents/*.md, skills/*/SKILL.md,
# README.md, and one workflow file, workflows/autonomous.md (see CREDITS.md:
# "68 skills + 24 agents"). Everything else these files load, workflows,
# references, templates, and the gsd-tools.cjs binary, comes from a separate
# GSD installation at $HOME/.claude/get-shit-done/ (confirmed present on a
# machine with GSD installed). So two different reference forms are both
# correct, and this check enforces a different invariant for each:
#
#   1. A repo-relative @systems/gsd/... reference must resolve to a file that
#      actually exists in this repository. (PR #144 originally rewrote every
#      external reference to this form without vendoring the targets, which
#      produced 67 dangling links; this half of the gate catches that again.)
#   2. A reference to $HOME/.claude/get-shit-done/... is a legitimate pointer
#      to the external dependency, not a defect, so it is never flagged as
#      dangling here. But systems/gsd/README.md must say plainly that this
#      external dependency exists, so a future contributor cannot reintroduce
#      undocumented external paths and leave a reader to discover the
#      dependency by trial and error.
#
# Run from repo root: bash tests/check-gsd-refs.sh

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

# Part 1: repo-relative references must resolve inside the repo.
for f in systems/gsd/README.md systems/gsd/agents/*.md systems/gsd/skills/*/SKILL.md; do
  [ -f "$f" ] || continue

  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    target=${ref#@}
    if [ ! -f "$target" ]; then
      echo "  DANGLING (in $f): $ref -> $target missing"
      fail=1
    fi
  done < <(grep -oE '@systems/gsd/[A-Za-z0-9._/-]+\.md' "$f" | sort -u)
done

# Part 2: any $HOME/.claude/get-shit-done/ external reference requires
# systems/gsd/README.md to declare that dependency.
if grep -rlq '\$HOME/\.claude/get-shit-done/' systems/gsd/agents/*.md systems/gsd/skills/*/SKILL.md 2>/dev/null; then
  if ! grep -q 'get-shit-done' systems/gsd/README.md; then
    echo "  UNDOCUMENTED: systems/gsd/ files reference \$HOME/.claude/get-shit-done/"
    echo "                but systems/gsd/README.md never mentions get-shit-done."
    fail=1
  fi
fi

if [ "$fail" -ne 0 ]; then
  echo "FAIL: systems/gsd/ references are broken."
  echo "      Repo-relative @systems/gsd/... paths must point at a file this"
  echo "      repo actually vendors. \$HOME/.claude/get-shit-done/... paths are"
  echo "      the legitimate external GSD dependency, but README.md must"
  echo "      declare it."
  exit 1
fi

echo "PASS: systems/gsd/ references are either repo-relative and resolve, or"
echo "      external and declared in README.md."
