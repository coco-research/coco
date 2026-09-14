#!/usr/bin/env bash
# Windsurf (Codeium) adapter — wires Coco artifacts into ~/.codeium/windsurf/
#
# Usage:
#   bash adapters/windsurf/install.sh
#   bash adapters/windsurf/install.sh --systems gsd,brain
#   bash adapters/windsurf/install.sh --dry-run

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_HOME="${WINDSURF_HOME:-$HOME/.codeium/windsurf}"
DRY_RUN=0
SYSTEMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "$1" ;;
    --help|-h) grep '^#' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

run() { [[ $DRY_RUN -eq 1 ]] && echo "DRY: $*" || "$@"; }

link_dir() {
  local src=$1 dst=$2
  # Safety: refuse to remove anything outside TARGET_HOME
  case "$dst" in
    "$TARGET_HOME"/*) ;;
    *) echo "REFUSE: $dst is outside $TARGET_HOME — skipping"; return ;;
  esac
  [[ -e "$dst" && ! -L "$dst" ]] && { echo "Skip (exists, not symlink): $dst"; return; }
  [[ -L "$dst" ]] && run rm "$dst"
  run mkdir -p "$(dirname "$dst")"
  run ln -sf "$src" "$dst"
  echo "Linked: $dst -> $src"
}

echo "Coco · Windsurf adapter"
echo "Source: $REPO_ROOT"
echo "Target: $TARGET_HOME"

# Skills
for skill in "$REPO_ROOT/skills"/*/; do
  name=$(basename "$skill")
  link_dir "$skill" "$TARGET_HOME/skills/$name"
done

# Rules (copy .mdc files for Windsurf compatibility)
if [[ -d "$REPO_ROOT/rules/cursor-mdc" ]]; then
  run mkdir -p "$TARGET_HOME/rules"
  for mdc in "$REPO_ROOT/rules/cursor-mdc"/*.mdc; do
    [[ -f "$mdc" ]] || continue
    name=$(basename "$mdc")
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "DRY: cp $mdc $TARGET_HOME/rules/$name"
    else
      cp "$mdc" "$TARGET_HOME/rules/$name"
      echo "Copied: $TARGET_HOME/rules/$name"
    fi
  done
fi

# Agents
for agent in "$REPO_ROOT/agents"/*.md; do
  [[ -f "$agent" ]] || continue
  name=$(basename "$agent")
  link_dir "$agent" "$TARGET_HOME/agents/$name"
done

# Systems bundles
for sys in "${SYSTEMS[@]:-}"; do
  [[ -n "$sys" ]] || continue
  sys_dir="$REPO_ROOT/systems/$sys"
  [[ -d "$sys_dir" ]] || { echo "Unknown system: $sys" >&2; continue; }
  if [[ -d "$sys_dir/skills" ]]; then
    for s in "$sys_dir/skills"/*/; do
      name=$(basename "$s")
      link_dir "$s" "$TARGET_HOME/skills/$name"
    done
  fi
  if [[ -d "$sys_dir/agents" ]]; then
    for a in "$sys_dir/agents"/*.md; do
      [[ -f "$a" ]] || continue
      name=$(basename "$a")
      link_dir "$a" "$TARGET_HOME/agents/$name"
    done
  fi
done

echo "Done."
