#!/usr/bin/env bash
# `coco uninstall` must remove the update-check cache the CLI itself created (#264).
# Runs against a throwaway HOME and clone dir; no git, no network.
set -euo pipefail

CLI="$(cd "$(dirname "$0")/.." && pwd)/bin/coco.js"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/home/.coco" "$T/clone"
echo '{}' > "$T/home/.coco/.update-check.json"

HOME="$T/home" node "$CLI" uninstall "$T/clone" >/dev/null

[ ! -e "$T/home/.coco/.update-check.json" ] || { echo "FAIL: .update-check.json left behind"; exit 1; }
[ ! -e "$T/home/.coco" ] || { echo "FAIL: empty ~/.coco left behind"; exit 1; }
[ ! -e "$T/clone" ] || { echo "FAIL: clone left behind"; exit 1; }

# A ~/.coco holding other files must survive.
mkdir -p "$T/home/.coco" "$T/clone"
echo '{}' > "$T/home/.coco/.update-check.json"; echo keep > "$T/home/.coco/other"
HOME="$T/home" node "$CLI" uninstall "$T/clone" >/dev/null
[ -f "$T/home/.coco/other" ] || { echo "FAIL: removed unrelated ~/.coco content"; exit 1; }
echo "PASS: uninstall removes the update-check cache"
