#!/usr/bin/env bash
# Cursor adapter — wires Coco artifacts into ~/.cursor/
#
# Usage:
#   bash adapters/cursor/install.sh
#   bash adapters/cursor/install.sh --dry-run

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_HOME="${CURSOR_HOME:-$HOME/.cursor}"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --help|-h) grep '^#' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

run() {
  if [[ $DRY_RUN -eq 1 ]]; then echo "DRY: $*"; else "$@"; fi
}

link_dir() {
  local src=$1 dst=$2
  [[ -e "$dst" && ! -L "$dst" ]] && { echo "Skip (exists, not symlink): $dst"; return; }
  [[ -L "$dst" ]] && run rm "$dst"
  run mkdir -p "$(dirname "$dst")"
  run ln -sf "$src" "$dst"
  echo "Linked: $dst -> $src"
}

echo "Coco · Cursor adapter"
echo "Source: $REPO_ROOT"
echo "Target: $TARGET_HOME"

# Skills
for skill in "$REPO_ROOT/skills"/*/; do
  name=$(basename "$skill")
  link_dir "$skill" "$TARGET_HOME/skills/$name"
done

# Rules — symlink .mdc files (idempotent; replaces any prior symlink pointing
# back to this repo).  Earlier versions used `cp`, which made re-runs
# non-idempotent and orphaned old copies on Coco updates.
run mkdir -p "$TARGET_HOME/rules"
for mdc in "$REPO_ROOT/rules/cursor-mdc"/*.mdc; do
  name=$(basename "$mdc")
  link_dir "$mdc" "$TARGET_HOME/rules/$name"
done

# Cursor-specific helper skills
for skill in "$REPO_ROOT/adapters/cursor/skills"/*/; do
  name=$(basename "$skill")
  link_dir "$skill" "$TARGET_HOME/skills/$name"
done

echo "Done."
