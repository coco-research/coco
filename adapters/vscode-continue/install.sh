#!/usr/bin/env bash
# VS Code (via Continue) adapter — STUB
#
# Status: Planned for v0.2.
# Issue: https://github.com/rkz91/coco/issues/4
#
# This stub exists so `bash install.sh --adapter vscode-continue` returns a
# clear "not yet implemented" message instead of a confusing error.
#
# What v0.2 will do:
#   - Read Coco's skills/, commands/, rules/ libraries
#   - Translate to Continue's config schema
#   - Write to ~/.continue/config.json
#   - Idempotent on re-run

set -euo pipefail

cat <<'EOF'
The VS Code (via Continue) adapter is planned for Coco v0.2.

Track progress: https://github.com/rkz91/coco/issues/4

For now, you can use Coco with VS Code in two ways:
  1. Install the generic adapter; it generates AGENTS.md which Continue reads:
       bash install.sh --adapter generic
  2. Install for Cursor and use Cursor as your VS Code-like editor:
       bash install.sh --adapter cursor

Want to help build this adapter? Open a PR — issue #4 describes the work.
EOF

exit 0
