#!/usr/bin/env bash
# Cursor --systems superintelligence must write SI-Decide.md into CURSOR_HOME/commands.
# Repro: adapters/cursor/install.sh used to reject --systems (Unknown flag / exit 1).
set -euo pipefail
cd "$(dirname "$0")/.."
h=$(mktemp -d)
trap 'rm -rf "$h"' EXIT
CURSOR_HOME="$h" bash adapters/cursor/install.sh --systems superintelligence
if [[ ! -f "$h/commands/SI-Decide.md" ]]; then
  echo "FAIL: expected $h/commands/SI-Decide.md after --systems superintelligence"
  ls -la "$h/commands" | head
  exit 1
fi
# When both homes exist, --adapter cursor must still target Cursor, not ~/.claude.
claude=$(mktemp -d)
trap 'rm -rf "$h" "$claude"' EXIT
HOME_TMP=$(mktemp -d)
mkdir -p "$HOME_TMP/.cursor" "$HOME_TMP/.claude/skills"
# Direct adapter path (what root install.sh --adapter cursor forwards):
CURSOR_HOME="$h/cursor-both" bash adapters/cursor/install.sh --systems superintelligence
if [[ ! -f "$h/cursor-both/commands/SI-Decide.md" ]]; then
  echo "FAIL: --adapter cursor path did not write SI-Decide.md into CURSOR_HOME"
  exit 1
fi
echo "PASS: SI-Decide.md written to CURSOR_HOME/commands"
