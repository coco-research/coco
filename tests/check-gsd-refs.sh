#!/usr/bin/env bash
# Guard: @<repo-relative-path> context-loading references inside systems/gsd/
# must resolve to a real file.
#
# PR #144 replaced 58 broken @$HOME/.claude/get-shit-done/ external paths in
# GSD skill files with @systems/gsd/ repo-relative ones. The vendored bundle
# only ships agents/, skills/*/SKILL.md, README.md, and workflows/autonomous.md
# (see CREDITS.md), so a repo-relative path that assumes the upstream's full
# workflows/references/templates layout still dangles even after the rewrite.
# This check fails loudly instead of letting a skill silently point at
# nothing.
#
# Run from repo root: bash tests/check-gsd-refs.sh

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

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

if [ "$fail" -ne 0 ]; then
  echo "FAIL: systems/gsd/ context-loading references are broken."
  echo "      Repo-relative @systems/gsd/... paths must point at a file this"
  echo "      repo actually vendors (agents/, skills/*/SKILL.md, README.md,"
  echo "      workflows/autonomous.md)."
  exit 1
fi

echo "PASS: all systems/gsd/ context-loading references resolve."
