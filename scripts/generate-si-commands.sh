#!/usr/bin/env bash
# Generate the Super Intelligence command family into a target directory.
#
# The 342 SI commands are not committed. They are stamped out of the thirteen team
# registries by two generators, which is why an adapter that does not call them
# ships 44 commands where the published total is 386 — and says nothing about it.
# This is the one place that knows how to run them, so a new adapter cannot
# half-implement the step, and a change to the generators cannot be applied to only
# some of the adapters.
#
#   systems/superintelligence/ai/scripts/build_commands.py        325 per-team
#   systems/superintelligence/scripts/build_meta_commands.py       17 cross-team
#
# Usage:
#   bash scripts/generate-si-commands.sh --target <dir> [--dry-run] [--quiet] [--manifest]
#
# Exit codes: 0 generated or legitimately skipped (no python3), 1 the generators
# failed. Failure prints the generator's stderr and exits before any path is
# listed, so a manifest install cannot record a plan that omits the SI files.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SI_DIR="$REPO_ROOT/systems/superintelligence"
TARGET=""
DRY_RUN=0
QUIET=0
MANIFEST=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) shift; TARGET="${1:-}" ;;
    --dry-run) DRY_RUN=1 ;;
    --quiet) QUIET=1 ;;
    --manifest) MANIFEST=1 ;;
    --help|-h) bash "$REPO_ROOT/scripts/print-usage.sh" "$0"; exit 0 ;;
    *) echo "generate-si-commands: unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

if [[ -z "$TARGET" ]]; then
  echo "generate-si-commands: --target is required" >&2
  exit 1
fi

say() { [[ "$QUIET" -eq 1 ]] || echo "$@"; }

# Paths the generators themselves name (--list / "would write"). Sorted, unique.
# python3's status is checked on its own: a pipe would report sed, and a process
# substitution would hide a failure from the caller. Stderr is the generator's.
planned_paths() {
  local py tmp err list_out py_status
  tmp=$(mktemp "${TMPDIR:-/tmp}/coco-si-plan.XXXXXX")
  err=$(mktemp "${TMPDIR:-/tmp}/coco-si-plan-err.XXXXXX")
  for py in "$SI_DIR/ai/scripts/build_commands.py" "$SI_DIR/scripts/build_meta_commands.py"; do
    [[ -f "$py" ]] || continue
    list_out=$(mktemp "${TMPDIR:-/tmp}/coco-si-plan-out.XXXXXX")
    py_status=0
    env COCO_SI_COMMANDS_DIR="$TARGET" python3 "$py" --list >"$list_out" 2>"$err" || py_status=$?
    if [[ $py_status -ne 0 ]]; then
      cat "$err" >&2
      rm -f "$tmp" "$err" "$list_out"
      exit "$py_status"
    fi
    sed -n 's/^  would write //p' "$list_out" >> "$tmp"
    rm -f "$list_out"
  done
  rm -f "$err"
  if [[ -s "$tmp" ]]; then
    LC_ALL=C sort -u "$tmp"
  fi
  rm -f "$tmp"
}

# Planned paths for a dry run. Names only; the bodies are not written.
manifest_plan() {
  local path planned
  planned=$(planned_paths) || return $?
  while IFS= read -r path; do
    [[ -n "$path" ]] || continue
    printf 'PLAN: %s\n' "$path"
  done <<< "$planned"
}

if [[ ! -f "$SI_DIR/ai/scripts/build_commands.py" ]]; then
  say "Skip SI generation: $SI_DIR/ai/scripts/build_commands.py not found."
  exit 0
fi

if ! command -v python3 >/dev/null 2>&1; then
  say "Skip SI generation: python3 not found. Run $SI_DIR/ai/scripts/build_commands.py manually."
  exit 0
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  say "DRY: generate 342 SI commands into $TARGET"
  if [[ $MANIFEST -eq 1 ]]; then
    manifest_plan || exit $?
  fi
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
if [[ $MANIFEST -eq 1 ]]; then
  # Intersect the generator's own names with files this run left behind.
  # find SI*.md would record a user's SI-mine.md, and uninstall would delete it.
  planned=$(planned_paths) || exit $?
  while IFS= read -r file; do
    [[ -n "$file" && -f "$file" && ! -L "$file" ]] || continue
    printf 'Wrote: %s\n' "$file"
    count=$((count + 1))
  done <<< "$planned"
else
  for file in "$TARGET"/SI*.md; do
    [[ -f "$file" ]] && count=$((count + 1))
  done
fi

say "Generated $count SI commands into $TARGET"
