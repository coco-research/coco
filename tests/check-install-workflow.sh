#!/usr/bin/env bash
# --workflow links the three workflow hooks and coco-gate, prints the hook lines
# for a settings file, and writes no settings file itself. Throwaway HOME, no
# network. Helpers: tests/lib/install-home.sh.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/install-home.sh"

# realpath, so a checkout reached through a symlink still matches its own links.
ROOT_REAL=$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$ROOT")

# The guarded line the installer prints for PreToolUse, spelled with $HOME.
LINE=$(python3 - <<'PY'
path = "$HOME/.claude/coco/hooks/coco-workflow-pretooluse.sh"
print("sh -c '[ -x \"%s\" ] && exec \"%s\" || exit 0'" % (path, path))
PY
)

run_at() {
  HOME="$1" CLAUDE_HOME="$1/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" \
    bash "$ADAPTER" "${@:2}"
}

echo "=== --core-only --workflow links four files and prints the hook lines ==="
H="$WORK/workflow"
mkdir -p "$H"
if ! run_at "$H" --core-only --workflow >"$WORK/wf.out" 2>"$WORK/wf.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/wf.err" >&2
  fail "--workflow install exited non-zero"
fi
for rel in coco/hooks/coco-workflow-pretooluse.sh coco/hooks/coco-workflow-context.sh \
           coco/hooks/coco-workflow-pre-commit.sh coco/bin/coco-gate; do
  p="$H/.claude/$rel"
  [[ -L "$p" ]] || fail "not a symlink: $p"
  real="$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$p")"
  [[ "$real" == "$ROOT_REAL"/* ]] || fail "$p resolves outside the checkout: $real"
  [[ -x "$p" ]] || fail "not executable: $p"
done
grep -qF ".claude/settings.local.json" "$WORK/wf.out" || fail "settings path missing from stdout"
grep -qF "$LINE" "$WORK/wf.out" || fail "PreToolUse hook line missing from stdout"
FOUND=$(find "$H" \( -name settings.json -o -name settings.local.json \))
[[ -z "$FOUND" ]] || fail "settings file written: $FOUND"
python3 - "$H/.claude/.coco/manifest.jsonl" "$H/.claude" <<'PY'
import json, os, sys
man, target = sys.argv[1:]
rows = [json.loads(l) for l in open(man, encoding="utf-8")]
for rel in ("coco/hooks/coco-workflow-pretooluse.sh", "coco/hooks/coco-workflow-context.sh",
            "coco/hooks/coco-workflow-pre-commit.sh", "coco/bin/coco-gate"):
    p = os.path.join(target, rel)
    hit = [o for o in rows if o.get("op") == "link" and o.get("path") == p]
    if len(hit) != 1:
        sys.exit(f"expected one link row for {p}, got {hit}")
print("ok   four link rows in the manifest")
PY
if ! "$H/.claude/coco/bin/coco-gate" --help >"$WORK/wf-gate.out" 2>&1; then
  fail "coco-gate --help exited non-zero"
fi
grep -q "usage" "$WORK/wf-gate.out" || fail "coco-gate --help printed no usage"
HOME="$H" sh -c "$LINE" </dev/null || fail "hook line exited non-zero with the hook linked"
HOME="$WORK/nobody" sh -c "$LINE" </dev/null || fail "hook line exited non-zero without coco"

echo "=== --dry-run --json reports the same line and writes nothing ==="
H="$WORK/workflow-dry"
mkdir -p "$H"
snap "$H" > "$WORK/wf-dry-before"
if ! run_at "$H" --core-only --workflow --dry-run --json >"$WORK/wf-dry.json" 2>"$WORK/wf-dry.err"; then
  fail "--workflow --dry-run --json exited non-zero"
fi
snap "$H" > "$WORK/wf-dry-after"
cmp -s "$WORK/wf-dry-before" "$WORK/wf-dry-after" || fail "dry-run changed the HOME tree"
python3 - "$WORK/wf-dry.json" "$LINE" <<'PY'
import json, sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
want = sys.argv[2]
workflow = json.loads(lines[-1])["summary"].get("workflow") or {}
if workflow.get("settings_file") != ".claude/settings.local.json":
    sys.exit(f"settings_file: {workflow.get('settings_file')!r}")
command = workflow["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
if command != want:
    sys.exit(f"PreToolUse command: {command!r} != {want!r}")
print("ok   dry-run summary carries the guarded hook line")
PY

echo "=== --core-only without --workflow leaves the workflow alone ==="
H="$WORK/workflow-off"
mkdir -p "$H"
if ! run_at "$H" --core-only --json >"$WORK/wf-off.json" 2>"$WORK/wf-off.err"; then
  fail "plain --core-only install exited non-zero"
fi
[[ ! -e "$H/.claude/coco" ]] || fail "plain install created .claude/coco"
python3 - "$WORK/wf-off.json" <<'PY'
import json, sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
if "workflow" in json.loads(lines[-1])["summary"]:
    sys.exit("plain install summary carries a workflow key")
print("ok   plain install has no workflow key")
PY

echo "=== the root installer passes --workflow to claude-code only ==="
if ! HOME="$WORK/root-home" CLAUDE_HOME="$WORK/root-home/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" \
  bash "$ROOT/install.sh" --adapter claude-code --core-only --workflow --dry-run \
  >"$WORK/wf-root.out" 2>"$WORK/wf-root.err"; then
  fail "root --adapter claude-code --workflow exited non-zero"
fi
if HOME="$WORK/root-home" CLAUDE_HOME="$WORK/root-home/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" \
  bash "$ROOT/install.sh" --adapter codex --workflow --dry-run \
  >"$WORK/wf-root.out" 2>"$WORK/wf-root.err"; then
  fail "root --adapter codex --workflow exited zero"
fi
grep -q "claude-code" "$WORK/wf-root.err" || fail "the refusal does not name claude-code"

echo "=== a target with an apostrophe in its path gets a quoted hook line ==="
H="$WORK/it's here"
AH="$WORK/apostrophe-home"
mkdir -p "$H" "$AH"
if ! HOME="$AH" CLAUDE_HOME="$H/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" \
  bash "$ADAPTER" --core-only --workflow --json >"$WORK/wf-quote.json" 2>"$WORK/wf-quote.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/wf-quote.err" >&2
  fail "--workflow install with an apostrophe in the target exited non-zero"
fi
CMD=$(python3 - "$WORK/wf-quote.json" <<'PY'
import json, sys
lines = [l for l in open(sys.argv[1], encoding="utf-8").read().splitlines() if l.strip()]
workflow = json.loads(lines[-1])["summary"]["workflow"]
print(workflow["hooks"]["PreToolUse"][0]["hooks"][0]["command"])
PY
)
printf '#!/bin/sh\nexit 7\n' > "$WORK/seven.sh"
chmod +x "$WORK/seven.sh"
ln -sfn "$WORK/seven.sh" "$H/.claude/coco/hooks/coco-workflow-pretooluse.sh"
RC=0
HOME="$AH" sh -c "$CMD" </dev/null || RC=$?
[[ "$RC" -eq 7 ]] || fail "the quoted hook line did not reach its hook (exit $RC): $CMD"
echo "ok   the hook line for a target containing an apostrophe runs that target"

echo "ok   --core-only --workflow links coco-gate and the three workflow hooks, prints the hook lines, writes no settings file"
