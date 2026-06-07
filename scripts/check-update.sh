#!/usr/bin/env bash
# check-update.sh — report whether a newer Coco is available on origin/main.
#
# For users who installed via `git clone` (not the npm CLI). Offline-safe: prints
# nothing useful and exits 0 if there is no network or no git. Privacy: talks only
# to the git remote (github.com), no telemetry. Disable with COCO_NO_UPDATE_CHECK=1.
#
#   bash scripts/check-update.sh
set -euo pipefail

[ -n "${COCO_NO_UPDATE_CHECK:-}" ] && exit 0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Not a git clone — update check skipped."; exit 0; }

local_v="$(python3 -c "import json;print(json.load(open('package.json'))['version'])" 2>/dev/null || echo "?")"

if ! git fetch --quiet origin main 2>/dev/null; then
  echo "Offline — could not check for updates (local v${local_v})."
  exit 0
fi

behind="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
remote_v="$(git show origin/main:package.json 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "$local_v")"

if [ "${behind:-0}" -gt 0 ]; then
  echo "⬆  Coco update available — ${behind} commit(s) behind origin/main (local v${local_v}, latest v${remote_v})."
  echo "   Update:  git -C \"$REPO_ROOT\" pull --ff-only && bash \"$REPO_ROOT/install.sh\""
else
  echo "✓  Coco is up to date (v${local_v})."
fi
