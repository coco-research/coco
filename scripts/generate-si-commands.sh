#!/usr/bin/env bash
# Generate the Super Intelligence command family into a target directory.
#
# The 242 SI commands are not committed. They are stamped out of the nine team
# registries by two generators, which is why an adapter that does not call them
# ships 38 commands where the published total is 280 — and says nothing about it.
# This is the one place that knows how to run them, so a new adapter cannot
# half-implement the step, and a change to the generators cannot be applied to only
# some of the adapters.
#
#   systems/superintelligence/ai/scripts/build_commands.py        225 per-team
#   systems/superintelligence/scripts/build_meta_commands.py       17 cross-team
#
# Usage:
#   bash scripts/generate-si-commands.sh --target <dir> [--dry-run] [--quiet]
#
# Exit codes: 0 generated or legitimately skipped (no python3), 1 the generators
# failed. Adapters run this non-fatally and report the count they got.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SI_DIR="$REPO_ROOT/systems/superintelligence"
TARGET=""
DRY_RUN=0
QUIET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) shift; TARGET="${1:-}" ;;
    --dry-run) DRY_RUN=1 ;;
    --quiet) QUIET=1 ;;
    --help|-h) grep '^#' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "generate-si-commands: unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

if [[ -z "$TARGET" ]]; then
  echo "generate-si-commands: --target is required" >&2
  exit 1
fi

say() { [[ "$QUIET" -eq 1 ]] || echo "$@"; }

if [[ ! -f "$SI_DIR/ai/scripts/build_commands.py" ]]; then
  say "Skip SI generation: $SI_DIR/ai/scripts/build_commands.py not found."
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  say "Skip SI generation: python3 not found. Run $SI_DIR/ai/scripts/build_commands.py manually."
  exit 0
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  say "DRY: generate 242 SI commands into $TARGET"
  exit 0
fi

mkdir -p "$TARGET"

# COCO_SI_COMMANDS_DIR is the documented output override; the generators derive the
# repo root from their own location, so COCO_SI_REPO is left to them.
env COCO_SI_COMMANDS_DIR="$TARGET" python3 "$SI_DIR/ai/scripts/build_commands.py" >/dev/null
if [[ -f "$SI_DIR/scripts/build_meta_commands.py" ]]; then
  env COCO_SI_COMMANDS_DIR="$TARGET" python3 "$SI_DIR/scripts/build_meta_commands.py" >/dev/null
fi

count=0
for file in "$TARGET"/SI*.md; do
  [[ -f "$file" ]] && count=$((count + 1))
done

say "Generated $count SI commands into $TARGET"
