#!/usr/bin/env bash
# Claude Code adapter — wires Coco artifacts into ~/.claude/
#
# Usage:
#   bash adapters/claude-code/install.sh                    # core + every bundle
#   bash adapters/claude-code/install.sh --core-only        # core only, no bundles
#   bash adapters/claude-code/install.sh --systems gsd      # only the GSD bundle
#   bash adapters/claude-code/install.sh --dry-run          # preview only
#   bash adapters/claude-code/install.sh --json             # JSONL on stdout, manifest on a real install
#   bash adapters/claude-code/install.sh --dry-run --json   # plan only; writes nothing
#   bash adapters/claude-code/install.sh --uninstall        # undo the manifest; keep edited user files
#   bash adapters/claude-code/install.sh --uninstall --dry-run --json   # what Remove will undo; writes nothing
#   bash adapters/claude-code/install.sh --workflow   # also link coco-gate and the workflow hooks; prints the hook lines
#   bash adapters/claude-code/install.sh --workflow-only  # only the workflow pieces, no skills, commands, agents or rules
#   bash adapters/claude-code/install.sh --uninstall --workflow-only   # remove only the coco/ workflow pieces
#
# Bundles default to every bundle that ships skills or agents, derived by
# scripts/installable-bundles.sh so a new bundle needs no edit here. --core-only opts out
# of all of them and wins over --systems; --systems <list> replaces the default set.
#
# The engine is scripts/claude_install.py. This wrapper only parses flags, picks
# bundles, and execs it. It stays on bash 3.2: no associative arrays.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_HOME="${CLAUDE_HOME:-$HOME/.claude}"
DRY_RUN=0
JSON=0
UNINSTALL=0
SYSTEMS=()
CORE_ONLY=0
EXPLICIT=0
WORKFLOW=0
WORKFLOW_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --json) JSON=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --core-only) CORE_ONLY=1 ;;
    --workflow) WORKFLOW=1 ;;
    --workflow-only) WORKFLOW_ONLY=1 ;;
    --systems)
      shift
      EXPLICIT=1
      IFS=',' read -ra SYSTEMS <<< "${1:-}"
      ;;
    --help|-h)
      bash "$REPO_ROOT/scripts/print-usage.sh" "$0"
      exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

if [[ $WORKFLOW_ONLY -eq 1 && ( $EXPLICIT -eq 1 || $CORE_ONLY -eq 1 ) ]]; then
  echo "--workflow-only cannot be combined with --systems or --core-only" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "coco install needs python3 (macOS: xcode-select --install; Linux: your package manager)" >&2
  exit 1
fi

if [[ $UNINSTALL -eq 1 ]]; then
  args=(--uninstall)
  if [[ $DRY_RUN -eq 1 ]]; then args+=(--dry-run); fi
  if [[ $JSON -eq 1 ]]; then args+=(--json); fi
  if [[ $WORKFLOW_ONLY -eq 1 ]]; then args+=(--workflow-only); fi
  exec python3 "$REPO_ROOT/scripts/claude_install.py" \
    --repo "$REPO_ROOT" --target "$TARGET_HOME" "${args[@]}"
fi

args=()
if [[ $DRY_RUN -eq 1 ]]; then args+=(--dry-run); fi
if [[ $JSON -eq 1 ]]; then args+=(--json); fi
if [[ $WORKFLOW -eq 1 ]]; then args+=(--workflow); fi
if [[ $WORKFLOW_ONLY -eq 1 ]]; then args+=(--workflow-only); fi

# No flag means every bundle in the default allow-list. --core-only wins over --systems,
# and --workflow-only takes no bundles at all.
if [[ $CORE_ONLY -eq 1 || $WORKFLOW_ONLY -eq 1 ]]; then
  SYSTEMS=()
elif [[ $EXPLICIT -eq 0 ]]; then
  while IFS= read -r bundle; do
    [[ -n "$bundle" ]] && SYSTEMS+=("$bundle")
  done < <(bash "$REPO_ROOT/scripts/installable-bundles.sh" --one-per-line 2>/dev/null || true)
  if [[ ${#SYSTEMS[@]} -eq 0 ]]; then
    echo "WARNING: scripts/installable-bundles.sh listed no bundles; installing core only." >&2
  fi
fi

for sys in "${SYSTEMS[@]:-}"; do
  [[ -n "$sys" ]] || continue
  args+=(--system "$sys")
done

# bash 3.2 + set -u: "${args[@]}" is unbound when the array is empty.
if [[ ${#args[@]} -gt 0 ]]; then
  exec python3 "$REPO_ROOT/scripts/claude_install.py" \
    --repo "$REPO_ROOT" --target "$TARGET_HOME" "${args[@]}"
fi
exec python3 "$REPO_ROOT/scripts/claude_install.py" \
  --repo "$REPO_ROOT" --target "$TARGET_HOME"
