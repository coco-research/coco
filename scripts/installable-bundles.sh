#!/usr/bin/env bash
# Print the bundles that can actually be installed, comma-separated on one line.
#
# "All bundles" has to mean all bundles that ship something. Three directories
# under systems/ hold documentation only — `team` and `learning` ship no skills and
# no agents — and a flag that names them installs nothing, which is exactly the
# phantom-bundle confusion the systems/INDEX.md note was added to kill. Deriving the
# list from the tree rather than hardcoding it means adding a bundle cannot be
# forgotten here.
#
# Usage:
#   python3 scripts/build-delivery-index.py            # via the index generator
#   bash scripts/installable-bundles.sh                # prints, e.g. "brain,cognee,..."
#   bash scripts/installable-bundles.sh --one-per-line

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ONE_PER_LINE=0
[[ "${1:-}" == "--one-per-line" ]] && ONE_PER_LINE=1

found=()
for dir in "$REPO_ROOT"/systems/*/; do
  [[ -d "$dir" ]] || continue
  name="$(basename "$dir")"

  # Skills live in three different shapes here — skills/<name>/SKILL.md,
  # <team>/SKILL.md for the superintelligence rosters, and nested inside an
  # adapter — so ask the tree rather than assuming one of them.
  installable=0
  if [[ -n "$(find "$dir" -name SKILL.md -print -quit 2>/dev/null)" ]]; then
    installable=1
  else
    for agent in "$dir"agents/*.md; do
      [[ -f "$agent" ]] && installable=1 && break
    done
  fi

  [[ "$installable" -eq 1 ]] && found+=("$name")
done

if [[ "${#found[@]}" -eq 0 ]]; then
  exit 0
fi

if [[ "$ONE_PER_LINE" -eq 1 ]]; then
  printf '%s\n' "${found[@]}"
else
  ( IFS=,; printf '%s\n' "${found[*]}" )
fi
