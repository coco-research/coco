#!/bin/bash
# Stop the brainstorm server and clean up
# Usage: stop-server.sh <screen_dir>
#
# Kills the server process. Only deletes session directory if it's
# under /tmp (ephemeral). Persistent directories (.superpowers/) are
# kept so mockups can be reviewed later.

set -euo pipefail

SCREEN_DIR="${1:-}"

if [[ -z "$SCREEN_DIR" ]]; then
  echo '{"error": "Usage: stop-server.sh <screen_dir>"}'
  exit 1
fi

# No directory → nothing to stop or delete. Matches the old "not_running" path
# without ever calling rm.
if [[ ! -d "$SCREEN_DIR" ]]; then
  echo '{"status": "not_running"}'
  exit 0
fi

# Canonicalize BEFORE the /tmp prefix check. `[[ $path == /tmp/* ]]` is a glob,
# so `/tmp/../Users/you` used to match and `rm -rf` whatever it resolved to.
# `pwd -P` also maps macOS `/tmp` → `/private/tmp`.
SCREEN_DIR="$(cd "$SCREEN_DIR" && pwd -P)"
TMP_ROOT="$(cd /tmp && pwd -P)"

PID_FILE="${SCREEN_DIR}/.server.pid"
had_pid=0
if [[ -f "$PID_FILE" ]]; then
  pid=$(tr -d '[:space:]' < "$PID_FILE")
  if [[ "$pid" =~ ^[0-9]+$ ]]; then
    kill "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE" "${SCREEN_DIR}/.server.log"
  had_pid=1
fi

# Never delete /tmp itself — only a session directory under it.
case "$SCREEN_DIR" in
  "$TMP_ROOT"/*)
    if [[ "$had_pid" -eq 1 ]]; then
      rm -rf "$SCREEN_DIR"
    fi
    ;;
esac

if [[ "$had_pid" -eq 1 ]]; then
  echo '{"status": "stopped"}'
else
  echo '{"status": "not_running"}'
fi
