#!/usr/bin/env bash
# Coco — single-entry installer
#
# Usage:
#   bash install.sh                            # auto-detect IDE, install core + all bundles
#   bash install.sh --adapter claude-code      # install for Claude Code
#   bash install.sh --adapter cursor           # install for Cursor
#   bash install.sh --adapter vscode           # install for VS Code / Copilot CLI
#   bash install.sh --adapter codex            # generate AGENTS.md (Codex)
#   bash install.sh --adapter generic          # generate AGENTS.md (any tool)
#   bash install.sh --core-only                # core only, no bundles
#   bash install.sh --adapter claude-code --systems gsd,brain  # only these bundles
#   bash install.sh --list                     # list available adapters
#   bash install.sh --dry-run                  # preview only
#
# Every bundle under systems/ that ships skills or agents is installed by default. That
# set is derived by scripts/installable-bundles.sh, so a new bundle needs no edit here.
# --core-only opts out of all bundles and wins over --systems; --systems <list>
# replaces the default set.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADAPTER=""
DRY_RUN=""
SYSTEMS=""
CORE_ONLY=""

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
  elif [[ -d "$HOME/.copilot" || -d "$HOME/Library/Application Support/Code/User" || -d "${XDG_CONFIG_HOME:-$HOME/.config}/Code/User" ]]; then
    echo "vscode"
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
    --core-only) CORE_ONLY=1 ;;
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

# The default bundle set is offered only to adapters that advertise support for the flag.
# An adapter that declares no bundles installs the core only, which is what --core-only
# would ask for anyway; handing it a flag it does not accept would turn a plain install
# into an error.
adapter_supports_systems() {
  local manifest="$ADAPTER_DIR/manifest.json"
  [[ -f "$manifest" ]] || return 1
  local list=""
  if command -v python3 >/dev/null 2>&1; then
    list=$(python3 -c 'import json,sys; print(",".join(json.load(open(sys.argv[1])).get("supports_systems") or []))' "$manifest" 2>/dev/null) || list=""
  elif command -v jq >/dev/null 2>&1; then
    list=$(jq -r '(.supports_systems // []) | join(",")' "$manifest" 2>/dev/null) || list=""
  fi
  [[ -n "$list" ]]
}

ARGS=()
[[ -n "$DRY_RUN" ]] && ARGS+=("$DRY_RUN")

if [[ -n "$CORE_ONLY" ]]; then
  # Explicit opt-out: no bundles, and never an error, even alongside --systems.
  adapter_supports_systems && ARGS+=("--core-only")
elif [[ -n "$SYSTEMS" ]]; then
  ARGS+=("--systems" "$SYSTEMS")
else
  # No --systems: install every bundle that ships skills or agents, so a plain run
  # delivers the advertised totals instead of a silent subset.
  DEFAULT_SYSTEMS="$(bash "$REPO_ROOT/scripts/installable-bundles.sh" 2>/dev/null || true)"
  if [[ -n "$DEFAULT_SYSTEMS" ]] && adapter_supports_systems; then
    ARGS+=("--systems" "$DEFAULT_SYSTEMS")
  fi
fi

if [[ ${#ARGS[@]} -gt 0 ]]; then
  bash "$ADAPTER_DIR/install.sh" "${ARGS[@]}"
else
  bash "$ADAPTER_DIR/install.sh"
fi

# Report installed version + how to stay current (no network call here).
if [[ -z "$DRY_RUN" ]]; then
  VER="$(python3 -c "import json;print(json.load(open('$REPO_ROOT/package.json'))['version'])" 2>/dev/null || echo "?")"
  echo
  echo "Coco v$VER installed. Check for updates anytime:"
  echo "  bash \"$REPO_ROOT/scripts/check-update.sh\"      # git clones"
  echo "  npx cocosuperintelligence version                      # npm installs"
fi
