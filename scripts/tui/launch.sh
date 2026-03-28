#!/bin/bash
# CoCo TUI Dashboard — Launch Script
# Usage: ~/.coco/tui/launch.sh
#
# Runs the persistent CoCo dashboard in the terminal.
# Press Ctrl+C to quit.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DASHBOARD="$SCRIPT_DIR/dashboard.py"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found"
    exit 1
fi

# Check rich is installed
if ! python3 -c "import rich" 2>/dev/null; then
    echo "Error: 'rich' Python package not installed"
    echo "Install with: pip3 install rich"
    exit 1
fi

# Check Outlook is running (optional warning)
if ! pgrep -x "Microsoft Outlook" &>/dev/null; then
    echo "⚠ Outlook is not running — calendar and email panels will be empty."
    echo "  Start Outlook, then press Enter to continue..."
    read -r
fi

# Run dashboard
exec python3 "$DASHBOARD" "$@"
