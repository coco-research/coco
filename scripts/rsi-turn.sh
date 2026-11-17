#!/usr/bin/env bash
# Run one unattended RSI turn across all baseline-ready skill evals.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -e "$ROOT/RSI.OFF" ]; then
  echo "turn: off (RSI.OFF honoured)"
  exit 0
fi

exec python3 "$ROOT/evals/skills/turn.py" "$@"
