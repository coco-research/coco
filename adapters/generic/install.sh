#!/usr/bin/env bash
# Generic adapter — produces AGENTS.md for any tool that reads it.
# Aider, Continue, Windsurf, Cline, and others all consume AGENTS.md.
#
# Identical behavior to adapters/codex/install.sh — Codex is the
# canonical AGENTS.md consumer; this exists for clarity for users
# of other tools.
#
# Usage:
#   bash adapters/generic/install.sh                      # write ./AGENTS.md, all bundles
#   bash adapters/generic/install.sh --core-only          # core set only, no bundles
#   bash adapters/generic/install.sh --systems gsd,brain  # only these bundles
#   bash adapters/generic/install.sh -o PATH              # write to PATH
#   bash adapters/generic/install.sh --dry-run
#
# Bundles default to every bundle that actually ships something
# (scripts/installable-bundles.sh), not to the core alone: defaulting to core folded about
# a third of the framework into AGENTS.md and said nothing about it. --systems overrides
# the default, --core-only asks for the core set, and --systems wins if both are given.
#
# Every flag is forwarded to adapters/codex/install.sh, which does the work.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# --help is answered here rather than forwarded, so it describes this adapter and the flags
# it takes instead of printing Codex's header.
for arg in "$@"; do
  case "$arg" in
    --help|-h) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0 ;;
  esac
done

# The codex installer writes the receipt, so it is told which tool it is standing in for.
exec env COCO_ADAPTER_LABEL=generic bash "$REPO_ROOT/adapters/codex/install.sh" "$@"
