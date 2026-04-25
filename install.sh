#!/usr/bin/env bash
# Coco — single-entry installer
#
# Usage:
#   bash install.sh                            # auto-detect IDE, install everything
#   bash install.sh --adapter claude-code      # install for Claude Code
#   bash install.sh --adapter cursor           # install for Cursor
#   bash install.sh --adapter codex            # generate AGENTS.md (Codex)
#   bash install.sh --adapter generic          # generate AGENTS.md (any tool)
#   bash install.sh --adapter claude-code --systems gsd,brain  # add bundles
#   bash install.sh --list                     # list available adapters
#   bash install.sh --dry-run                  # preview only

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADAPTER=""
DRY_RUN=""
SYSTEMS=""

show_help() {
  grep '^#' "$0" | sed 's/^# \?//'
}

list_adapters() {
  echo "Available adapters:"
  for d in "$REPO_ROOT/adapters"/*/; do
    name=$(basename "$d")
    desc=$(jq -r '.description // empty' "$d/manifest.json" 2>/dev/null || echo "")
    printf "  %-15s %s\n" "$name" "$desc"
  done
}

detect_adapter() {
  if [[ -n "${CLAUDECODE:-}" || -d "$HOME/.claude/skills" ]]; then
    echo "claude-code"
  elif [[ -d "$HOME/.cursor" ]]; then
    echo "cursor"
  elif command -v codex &>/dev/null; then
    echo "codex"
  else
    echo "generic"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --adapter) shift; ADAPTER=$1 ;;
    --systems) shift; SYSTEMS=$1 ;;
    --dry-run) DRY_RUN="--dry-run" ;;
    --list) list_adapters; exit 0 ;;
    --help|-h) show_help; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

if [[ -z "$ADAPTER" ]]; then
  ADAPTER=$(detect_adapter)
  echo "Auto-detected adapter: $ADAPTER"
  echo "(override with --adapter <name>)"
fi

ADAPTER_DIR="$REPO_ROOT/adapters/$ADAPTER"
if [[ ! -d "$ADAPTER_DIR" ]]; then
  echo "Unknown adapter: $ADAPTER" >&2
  list_adapters
  exit 1
fi

ARGS=()
[[ -n "$DRY_RUN" ]] && ARGS+=("$DRY_RUN")
[[ -n "$SYSTEMS" ]] && ARGS+=("--systems" "$SYSTEMS")

bash "$ADAPTER_DIR/install.sh" "${ARGS[@]}"
