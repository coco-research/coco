#!/bin/bash
# CoCo TUI Dashboard — Ghostty Launcher
# Opens the TUI dashboard in a new Ghostty window.
# Falls back to Terminal.app if Ghostty is not installed.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DASHBOARD="$SCRIPT_DIR/dashboard.py"

# Already running?
if pgrep -f "dashboard.py" >/dev/null 2>&1; then
    echo "TUI dashboard is already running."
    exit 0
fi

# Try Ghostty first, fall back to Terminal.app
if [ -d "/Applications/Ghostty.app" ]; then
    # Use open -na with -e flag to run the python command directly
    open -na "Ghostty" --args -e "python3" "$DASHBOARD"
    echo "CoCo TUI launched in Ghostty window."
else
    osascript -e "tell application \"Terminal\" to do script \"python3 $DASHBOARD\"" &>/dev/null &
    echo "CoCo TUI launched in Terminal.app window."
fi
