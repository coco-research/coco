#!/bin/sh
# coco-workflow PreToolUse hook: while the current branch's gate has size=feature
# and its plan sign-off does not verify with the work tree's rules, Edit, Write,
# MultiEdit and NotebookEdit on code paths are refused with one line naming the
# pending artifact. The required CI check is the lock; this hook only nudges, so
# anything it cannot check passes. No network, no files written.
#
# The installer prints this hook line (a collaborator without coco gets exit 0
# and nothing happens):
# sh -c '[ -x "$HOME/.claude/coco/hooks/coco-workflow-pretooluse.sh" ] && exec "$HOME/.claude/coco/hooks/coco-workflow-pretooluse.sh" || exit 0'

# tool_name and the target path, read from the JSON on stdin with python3 (not jq).
# `python3 -c`, not a heredoc: a heredoc would replace stdin and the JSON would be lost.
target="$(python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except ValueError:
    sys.exit(0)
data = data if isinstance(data, dict) else {}
item = data.get("tool_input") if isinstance(data.get("tool_input"), dict) else {}
path = item.get("file_path") or item.get("notebook_path") or ""
if data.get("tool_name") in ("Edit", "Write", "MultiEdit", "NotebookEdit") and path:
    print(path)
' 2>/dev/null)" || exit 0
[ -n "$target" ] || exit 0

# coco_gate.py sits next to this hook; resolve symlinks so a linked hook still
# finds it. A missing verifier (or a missing python3) means allow, silently.
self="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$0" 2>/dev/null)" || exit 0
[ -n "$self" ] || exit 0
gate="$(dirname "$self")/../scripts/coco_gate.py"
[ -f "$gate" ] || exit 0

msg="$(python3 "$gate" check-edit --path "$target" 2>/dev/null)"
rc=$?
if [ "$rc" -eq 2 ] && [ -n "$msg" ]; then
  python3 - "$msg" <<'PY'
import json, sys
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                         "permissionDecision": "deny",
                                         "permissionDecisionReason": sys.argv[1]}}))
PY
fi
exit 0
