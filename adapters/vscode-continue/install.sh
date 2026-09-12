#!/usr/bin/env bash
# VS Code (via Continue) adapter — wires Coco artifacts into ~/.continue/
#
# Usage:
#   bash adapters/vscode-continue/install.sh
#   bash adapters/vscode-continue/install.sh --systems gsd,brain
#   bash adapters/vscode-continue/install.sh --dry-run

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_HOME="${CONTINUE_HOME:-$HOME/.continue}"
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

echo "Coco · VS Code (Continue) adapter"
echo "Source: $REPO_ROOT"
echo "Target: $TARGET_HOME"

# Skills → Continue custom slash commands directory
for skill in "$REPO_ROOT/skills"/*/; do
  name=$(basename "$skill")
  link_dir "$skill" "$TARGET_HOME/skills/$name"
done

# Agents
for agent in "$REPO_ROOT/agents"/*.md; do
  [[ -f "$agent" ]] || continue
  name=$(basename "$agent")
  link_dir "$agent" "$TARGET_HOME/agents/$name"
done

# Rules as context providers
if [[ -d "$REPO_ROOT/rules" ]]; then
  run mkdir -p "$TARGET_HOME/rules"
  for rule in "$REPO_ROOT/rules"/*.md; do
    [[ -f "$rule" ]] || continue
    name=$(basename "$rule")
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "DRY: cp $rule $TARGET_HOME/rules/$name"
    else
      cp "$rule" "$TARGET_HOME/rules/$name"
      echo "Copied: $TARGET_HOME/rules/$name"
    fi
  done
fi

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
