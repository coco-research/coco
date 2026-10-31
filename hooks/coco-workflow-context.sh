#!/bin/sh
# coco-workflow UserPromptSubmit hook: one line naming the stage and the next
# artifact, or nothing at all. The required CI check is the lock; this only
# reminds the agent where the gate stands. No network, no files written.
#
# The installer prints this hook line (a collaborator without coco gets exit 0
# and nothing happens):
# sh -c '[ -x "$HOME/.claude/coco/hooks/coco-workflow-context.sh" ] && exec "$HOME/.claude/coco/hooks/coco-workflow-context.sh" || exit 0'

self="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$0" 2>/dev/null)" || exit 0
[ -n "$self" ] || exit 0
gate="$(dirname "$self")/../scripts/coco_gate.py"
[ -f "$gate" ] || exit 0
line="$(python3 "$gate" status --line 2>/dev/null)" || exit 0
[ -n "$line" ] || exit 0
python3 - "$line" <<'PY'
import json, sys
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                         "additionalContext": sys.argv[1]}}))
PY
exit 0
