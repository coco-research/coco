#!/bin/sh
# coco-workflow pre-commit hook. It lives in .git/hooks (the installer links
# it back to the coco checkout), so it is never committed with the repo, and
# it only warns: while the branch's feature gate has no validly signed plan
# it prints one line naming the stage and the next artifact, and it never
# stops a commit. The required CI check is the lock. No network, no writes.
#
# Chaining: the installer renames a user's existing pre-commit hook and points
# COCO_CHAIN_HOOK at it; that hook then runs last with the same arguments and
# its exit code becomes this hook's exit code.

# coco_gate.py sits beside this hook; resolve symlinks so a hook linked into
# .git/hooks still finds it. A missing python3 or verifier means silence.
# Whatever happens here, the chained hook below still runs: a missing python3 or
# verifier only skips our warning, never the user's own hook (T3).
self="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$0" 2>/dev/null)" || self=""
gate="${self:+$(dirname "$self")/../scripts/coco_gate.py}"
if [ -n "$gate" ] && [ -f "$gate" ]; then
  line="$(python3 "$gate" status --warn 2>/dev/null)" || line=""
  [ -z "$line" ] || echo "coco-workflow (warning): $line" >&2
fi

chain="${COCO_CHAIN_HOOK:-}"
[ -n "$chain" ] && [ -x "$chain" ] && exec "$chain" "$@"
exit 0
