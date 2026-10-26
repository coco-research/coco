#!/usr/bin/env bash
# --workflow-only installs and removes just the target's coco/ workflow pieces.
# A Remove killed partway through finishes on the next run. Throwaway HOME, no
# network. Helpers: tests/lib/install-home.sh.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/install-home.sh"

run_at() {
  local h=$1; shift
  # An empty managed root keeps this machine's real org settings out of the run.
  mkdir -p "$WORK/no-managed"
  HOME="$h" CLAUDE_HOME="$h/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" "$@"
}
save_tree() {
  snap "$1" >"$WORK/$2-snap-before"
  tree_id "$1" >"$WORK/$2-tree-before"
}
same_tree() {
  snap "$1" >"$WORK/$2-snap-now"
  tree_id "$1" >"$WORK/$2-tree-now"
  if ! cmp -s "$WORK/$2-snap-before" "$WORK/$2-snap-now"; then
    diff -u "$WORK/$2-snap-before" "$WORK/$2-snap-now" | head -40 >&2 || true
    fail "snap differs: $2"
  fi
  if ! cmp -s "$WORK/$2-tree-before" "$WORK/$2-tree-now"; then
    diff -u "$WORK/$2-tree-before" "$WORK/$2-tree-now" | head -60 >&2 || true
    fail "tree differs: $2"
  fi
}

echo "=== --workflow-only creates the coco/ pieces and nothing else ==="
H="$WORK/only"
mkdir -p "$H"
save_tree "$H" only
if ! run_at "$H" bash "$ADAPTER" --workflow-only --json >"$WORK/only.json" 2>"$WORK/only.err"; then
  tail -30 "$WORK/only.err" >&2
  fail "--workflow-only install failed"
fi
grep -F "Installed the coco workflow pieces only: no skills, commands, agents or rules." "$WORK/only.err" \
  || fail "the workflow-only receipt line is missing"
grep -F "coco-workflow: hooks linked into" "$WORK/only.err" || fail "the workflow notes are missing"
python3 - "$H" "$ROOT" <<'PY'
import os, sys
home, repo = sys.argv[1:]
target = os.path.join(home, ".claude")
hooks = ("coco-workflow-pretooluse.sh", "coco-workflow-context.sh", "coco-workflow-pre-commit.sh")
want = {home, target, os.path.join(target, ".coco"),
        os.path.join(target, ".coco", "manifest.jsonl"),
        os.path.join(target, "coco"), os.path.join(target, "coco", "bin"),
        os.path.join(target, "coco", "hooks")}
for name in hooks:
    want.add(os.path.join(target, "coco", "hooks", name))
want.add(os.path.join(target, "coco", "bin", "coco-gate"))
got = set()
for dirpath, dirnames, filenames in os.walk(home, followlinks=False):
    got.add(dirpath)
    for name in list(dirnames):
        p = os.path.join(dirpath, name)
        if os.path.islink(p):
            got.add(p)
            dirnames.remove(name)
    for name in filenames:
        got.add(os.path.join(dirpath, name))
extra, missing = sorted(got - want), sorted(want - got)
if extra or missing:
    sys.exit("unexpected under HOME:\n" + "\n".join(extra) + "\nmissing:\n" + "\n".join(missing))
for rel in ("CLAUDE.md", "skills", "commands", "agents"):
    if os.path.lexists(os.path.join(target, rel)):
        sys.exit("%s exists after --workflow-only" % rel)
for rel in ["coco/hooks/" + name for name in hooks] + ["coco/bin/coco-gate"]:
    p = os.path.join(target, rel)
    if not os.path.islink(p) or not os.access(p, os.X_OK):
        sys.exit("%s is not an executable link" % p)
    real = os.path.realpath(p)
    if not real.startswith(os.path.realpath(repo) + os.sep):
        sys.exit("%s resolves outside the checkout: %s" % (p, real))
print("ok   only coco/ and .coco/manifest.jsonl exist under the target")
PY
python3 - "$WORK/only.json" <<'PY'
import json, sys
lines = [l for l in open(sys.argv[1], encoding="utf-8").read().splitlines() if l.strip()]
records = [json.loads(l) for l in lines[:-1]]
summary = json.loads(lines[-1])["summary"]
if summary["link"] != 4:
    sys.exit("summary link %s != 4" % summary["link"])
if "workflow" not in summary:
    sys.exit("summary is missing the workflow key")
if summary["block"] != 0 or summary["skip"] != 0 or summary["carried"] != 0:
    sys.exit("workflow-only planned a block, a skip or a carry: %s" % summary)
if any(o.get("op") not in ("link", "write") for o in records):
    sys.exit("workflow-only planned something other than links and writes")
if summary["workflow"].get("settings_file") != ".claude/settings.local.json":
    sys.exit("workflow info: %r" % summary["workflow"])
print("ok   summary carries workflow and plans 4 links")
PY

echo "=== --uninstall --workflow-only round-trips that HOME to nothing ==="
if ! run_at "$H" bash "$ADAPTER" --uninstall --workflow-only >"$WORK/only-un.out" 2>"$WORK/only-un.err"; then
  tail -40 "$WORK/only-un.err" >&2
  fail "workflow-only uninstall failed"
fi
same_tree "$H" only
[[ ! -e "$H/.claude" ]] || fail "workflow-only uninstall left .claude behind"

echo "=== --workflow-only on top of a full install keeps the other rows ==="
H="$WORK/stack"
mkdir -p "$H"
save_tree "$H" stack
if ! run_at "$H" bash "$ADAPTER" >"$WORK/stack-full.out" 2>"$WORK/stack-full.err"; then
  tail -30 "$WORK/stack-full.err" >&2
  fail "default install failed"
fi
MAN="$H/.claude/.coco/manifest.jsonl"
[[ -f "$MAN" ]] || fail "default install wrote no manifest"
cp "$MAN" "$WORK/stack-manifest-full"
save_tree "$H" stack-installed
if ! run_at "$H" bash "$ADAPTER" --workflow-only --json >"$WORK/stack.json" 2>"$WORK/stack.err"; then
  tail -30 "$WORK/stack.err" >&2
  fail "--workflow-only on a full install failed"
fi
python3 - "$WORK/stack.json" <<'PY'
import json, sys
lines = [l for l in open(sys.argv[1], encoding="utf-8").read().splitlines() if l.strip()]
summary = json.loads(lines[-1])["summary"]
if summary.get("carried", 0) <= 0:
    sys.exit("summary carried %r, expected rows from the full install" % summary.get("carried"))
if summary["link"] != 4 or "workflow" not in summary:
    sys.exit("summary: %s" % summary)
print("ok   %s rows carried, 4 links linked" % summary["carried"])
PY
# Only coco/ changed on disk; the manifest's own bytes are excluded on purpose.
tree_id "$H" "$MAN" | grep -v " \.claude/coco" >"$WORK/stack-tree-now"
grep -v '\.coco/manifest\.jsonl' "$WORK/stack-installed-tree-before" >"$WORK/stack-installed-rest"
if ! cmp -s "$WORK/stack-installed-rest" "$WORK/stack-tree-now"; then
  diff -u "$WORK/stack-installed-rest" "$WORK/stack-tree-now" | head -40 >&2 || true
  fail "workflow-only changed more than the manifest"
fi

echo "=== --uninstall --workflow-only removes only the coco/ rows ==="
cp "$MAN" "$WORK/stack-manifest-before-un"
snap "$H" >"$WORK/stack-snap-pre-un"
tree_id "$H" "$MAN" >"$WORK/stack-tree-pre-un"
if ! run_at "$H" bash "$ADAPTER" --uninstall --workflow-only --json \
  >"$WORK/stack-un.json" 2>"$WORK/stack-un.err"; then
  tail -40 "$WORK/stack-un.err" >&2
  fail "workflow-only uninstall on a full install failed"
fi
snap "$H" >"$WORK/stack-snap-post-un"
tree_id "$H" "$MAN" >"$WORK/stack-tree-post-un"
python3 - "$H" "$WORK/stack-snap-pre-un" "$WORK/stack-snap-post-un" "$WORK/stack-un.json" <<'PY'
import json, os, sys
home, before_p, after_p, plan_p = sys.argv[1:]
target = os.path.join(home, ".claude")
coco = os.path.join(target, "coco") + os.sep

def paths(path):
    return set(l.rstrip("\n") for l in open(path, encoding="utf-8") if l.strip())

gone = paths(before_p) - paths(after_p)
added = paths(after_p) - paths(before_p)
if added:
    sys.exit("workflow-only uninstall added paths: %s" % sorted(added))
bad = sorted(p for p in gone if not (os.path.normpath(os.path.join(home, p)) + os.sep).startswith(coco))
if bad:
    sys.exit("workflow-only uninstall removed paths outside coco/: %s" % bad)
rows = [json.loads(l) for l in open(plan_p, encoding="utf-8") if l.strip()]
removes = [o["path"] for o in rows if o.get("op") == "remove"]
if not removes or any(not (p == coco.rstrip(os.sep) or p.startswith(coco)) for p in removes):
    sys.exit("remove records outside coco/: %s" % removes)
print("ok   removed %s paths, all under coco/" % len(gone))
PY
grep -v '\.claude/coco' "$WORK/stack-tree-pre-un" >"$WORK/stack-tree-pre-un-rest"
grep -v '\.claude/coco' "$WORK/stack-tree-post-un" >"$WORK/stack-tree-post-un-rest"
if ! cmp -s "$WORK/stack-tree-pre-un-rest" "$WORK/stack-tree-post-un-rest"; then
  diff -u "$WORK/stack-tree-pre-un-rest" "$WORK/stack-tree-post-un-rest" | head -40 >&2 || true
  fail "workflow-only uninstall changed something outside coco/"
fi
python3 - "$WORK/stack-manifest-before-un" "$MAN" "$H/.claude" <<'PY'
import json, os, sys
before_p, after_p, target = sys.argv[1:]
coco = os.path.join(target, "coco")

def raw_rows(path):
    out = []
    for line in open(path, "rb").read().splitlines():
        obj = json.loads(line.decode("utf-8"))
        if "summary" in obj:
            continue
        out.append((obj, line))
    return out

def summary_of(path):
    rows = [json.loads(l) for l in open(path, "rb").read().splitlines() if b'"summary"' in l]
    return rows[-1]["summary"]

def workflow(path):
    return path == coco or path.startswith(coco + os.sep)

before = raw_rows(before_p)
keep = sorted(line for obj, line in before if not workflow(obj.get("path")))
after = sorted(line for obj, line in raw_rows(after_p))
if keep != after:
    sys.exit("other manifest rows changed:\n" + "\n".join(
        repr(x) for x in (set(keep) ^ set(after))))
old, new = summary_of(before_p), summary_of(after_p)
if "workflow" not in old:
    sys.exit("the workflow-only install's summary lost its workflow key")
if "workflow" in new:
    sys.exit("the rewritten summary still carries workflow")
if set(new) != set(old) - {"workflow"}:
    sys.exit("summary keys %s != %s" % (sorted(new), sorted(old)))
for op in ("link", "write", "block", "skip"):
    if new[op] != sum(1 for obj, _line in raw_rows(after_p)
                     if obj.get("op") == op and not obj.get("carried")):
        sys.exit("summary %s count does not match the rows that remain" % op)
print("ok   %s other rows kept byte for byte" % len(after))
PY

echo "=== a full --uninstall after that still round-trips the HOME ==="
if ! run_at "$H" bash "$ADAPTER" --uninstall >"$WORK/stack-un-full.out" 2>"$WORK/stack-un-full.err"; then
  tail -40 "$WORK/stack-un-full.err" >&2
  fail "full uninstall after a workflow-only uninstall failed"
fi
same_tree "$H" stack

echo "=== a killed Remove finishes on the next run ==="
for variant in link claudemd afterblock generated; do
  H="$WORK/kill-$variant"
  mkdir -p "$H/.claude"
  printf 'user rules one line\n' > "$H/.claude/CLAUDE.md"
  install_args=(--workflow)
  if [[ $variant == generated ]]; then
    # A coco-owned SI command, so the install restores it from a backup on Remove.
    mkdir -p "$H/.claude/commands"
    printf 'user orchestrate v1\n\nMade with CoCo Super Intelligence.\n' \
      > "$H/.claude/commands/SI-AI-Orchestrate.md"
    install_args=(--systems superintelligence --workflow)
  fi
  save_tree "$H" "kill-$variant"
  if ! run_at "$H" bash "$ADAPTER" "${install_args[@]}" \
    >"$WORK/kill-$variant.out" 2>"$WORK/kill-$variant.err"; then
    tail -30 "$WORK/kill-$variant.err" >&2
    fail "kill ($variant): the install failed"
  fi
  MAN="$H/.claude/.coco/manifest.jsonl"
  [[ -f "$MAN" ]] || fail "kill ($variant): no manifest"
  case "$variant" in
    link)
      KILL=$(python3 - "$MAN" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
links = [r["path"] for r in rows if r.get("op") == "link"]
print(links[len(links) // 2])
PY
)
      ;;
    claudemd) KILL="$H/.claude/CLAUDE.md" ;;
    afterblock|generated) KILL="$H/.claude/coco/hooks/coco-workflow-pretooluse.sh" ;;
  esac
  LINKS_BEFORE=$(find "$H/.claude" -type l | wc -l | tr -d ' ')
  kill_status=0
  run_at "$H" env COCO_INSTALL_KILL_AT="$KILL" bash "$ADAPTER" --uninstall --json \
    >"$WORK/kill-$variant-killed.json" 2>"$WORK/kill-$variant-killed.err" || kill_status=$?
  [[ $kill_status -eq 137 ]] || fail "kill ($variant): exit $kill_status"
  [[ -f "$MAN" ]] || fail "kill ($variant): the manifest was removed"
  LINKS_AFTER=$(find "$H/.claude" -type l | wc -l | tr -d ' ')
  [[ "$LINKS_AFTER" -lt "$LINKS_BEFORE" ]] || fail "kill ($variant): nothing was removed"
  if ! run_at "$H" bash "$ADAPTER" --uninstall --json \
    >"$WORK/kill-$variant-again.json" 2>"$WORK/kill-$variant-again.err"; then
    tail -40 "$WORK/kill-$variant-again.err" >&2
    fail "kill ($variant): the re-run failed"
  fi
  same_tree "$H" "kill-$variant"
  echo "ok   killed at $KILL, re-run restored HOME"
done

echo "=== a killed --uninstall --workflow-only finishes on the next run ==="
H="$WORK/wfkill"
mkdir -p "$H"
save_tree "$H" wfkill
if ! run_at "$H" bash "$ADAPTER" --workflow >"$WORK/wfkill-full.out" 2>"$WORK/wfkill-full.err"; then
  tail -30 "$WORK/wfkill-full.err" >&2
  fail "wfkill: the full install failed"
fi
if ! run_at "$H" bash "$ADAPTER" --workflow-only >"$WORK/wfkill-wf.out" 2>"$WORK/wfkill-wf.err"; then
  tail -30 "$WORK/wfkill-wf.err" >&2
  fail "wfkill: the workflow-only install failed"
fi
MAN="$H/.claude/.coco/manifest.jsonl"
cp "$MAN" "$WORK/wfkill-manifest"
KILL=$(python3 - "$MAN" "$H/.claude" <<'PY'
import json, os, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
coco = os.path.join(sys.argv[2], "coco")
links = [r["path"] for r in rows if r.get("op") == "link"
         and (r["path"] == coco or r["path"].startswith(coco + os.sep))]
print(links[1])
PY
)
snap "$H" >"$WORK/wfkill-mid-snap"
tree_id "$H" "$MAN" >"$WORK/wfkill-mid-tree"
kill_status=0
run_at "$H" env COCO_INSTALL_KILL_AT="$KILL" bash "$ADAPTER" --uninstall --workflow-only --json \
  >"$WORK/wfkill-killed.json" 2>"$WORK/wfkill-killed.err" || kill_status=$?
[[ $kill_status -eq 137 ]] || fail "wfkill: exit $kill_status"
if ! run_at "$H" bash "$ADAPTER" --uninstall --workflow-only --json \
  >"$WORK/wfkill-again.json" 2>"$WORK/wfkill-again.err"; then
  tail -40 "$WORK/wfkill-again.err" >&2
  fail "wfkill: the re-run failed"
fi
snap "$H" >"$WORK/wfkill-snap-after"
tree_id "$H" "$MAN" >"$WORK/wfkill-tree-after"
python3 - "$H" "$WORK/wfkill-mid-snap" "$WORK/wfkill-snap-after" <<'PY'
import os, sys
home, before_p, after_p = sys.argv[1:]
coco = os.path.join(home, ".claude", "coco") + os.sep

def paths(path):
    return set(l.rstrip("\n") for l in open(path, encoding="utf-8") if l.strip())

gone = paths(before_p) - paths(after_p)
added = paths(after_p) - paths(before_p)
if added:
    sys.exit("the re-run added paths: %s" % sorted(added))
bad = sorted(p for p in gone if not (os.path.normpath(os.path.join(home, p)) + os.sep).startswith(coco))
if bad:
    sys.exit("the re-run removed paths outside coco/: %s" % bad)
if not gone:
    sys.exit("the re-run removed nothing")
print("ok   only coco/ went away after the re-run")
PY
grep -v '\.claude/coco' "$WORK/wfkill-mid-tree" >"$WORK/wfkill-mid-tree-rest"
grep -v '\.claude/coco' "$WORK/wfkill-tree-after" >"$WORK/wfkill-tree-after-rest"
if ! cmp -s "$WORK/wfkill-mid-tree-rest" "$WORK/wfkill-tree-after-rest"; then
  diff -u "$WORK/wfkill-mid-tree-rest" "$WORK/wfkill-tree-after-rest" | head -40 >&2 || true
  fail "the re-run changed something outside coco/"
fi
python3 - "$WORK/wfkill-manifest" "$MAN" "$H/.claude" <<'PY'
import json, os, sys
before_p, after_p, target = sys.argv[1:]
coco = os.path.join(target, "coco")

def raw_rows(path):
    out = []
    for line in open(path, "rb").read().splitlines():
        obj = json.loads(line.decode("utf-8"))
        if "summary" in obj:
            continue
        out.append((obj, line))
    return out

def workflow(path):
    return path == coco or path.startswith(coco + os.sep)

keep = sorted(line for obj, line in raw_rows(before_p) if not workflow(obj.get("path")))
after = sorted(line for obj, line in raw_rows(after_p))
if keep != after:
    sys.exit("other manifest rows changed after the killed run")
print("ok   %s other manifest rows are intact" % len(after))
PY
if ! run_at "$H" bash "$ADAPTER" --uninstall >"$WORK/wfkill-un.out" 2>"$WORK/wfkill-un.err"; then
  tail -40 "$WORK/wfkill-un.err" >&2
  fail "wfkill: the final full uninstall failed"
fi
same_tree "$H" wfkill

echo "=== dry runs write nothing and list only the workflow paths ==="
H="$WORK/wfdry"
mkdir -p "$H"
if ! run_at "$H" bash "$ADAPTER" --core-only >"$WORK/wfdry-core.out" 2>"$WORK/wfdry-core.err"; then
  tail -30 "$WORK/wfdry-core.err" >&2
  fail "wfdry: the core install failed"
fi
save_tree "$H" wfdry-core
if ! run_at "$H" bash "$ADAPTER" --uninstall --workflow-only \
  >"$WORK/wfdry-none.out" 2>"$WORK/wfdry-none.err"; then
  tail -30 "$WORK/wfdry-none.err" >&2
  fail "wfdry: the uninstall with no workflow rows failed"
fi
grep -F "nothing to uninstall (no workflow rows)" "$WORK/wfdry-none.out" "$WORK/wfdry-none.err" >/dev/null \
  || fail "wfdry: the no-workflow-rows message is missing"
same_tree "$H" wfdry-core
if ! run_at "$H" bash "$ADAPTER" --workflow-only >"$WORK/wfdry-wf.out" 2>"$WORK/wfdry-wf.err"; then
  tail -30 "$WORK/wfdry-wf.err" >&2
  fail "wfdry: the workflow-only install failed"
fi
save_tree "$H" wfdry
if ! run_at "$H" bash "$ADAPTER" --workflow-only --dry-run --json >"$WORK/wfdry-plan.json" 2>"$WORK/wfdry-plan.err"; then
  tail -30 "$WORK/wfdry-plan.err" >&2
  fail "wfdry: the install dry run failed"
fi
if ! run_at "$H" bash "$ADAPTER" --uninstall --workflow-only --dry-run --json \
  >"$WORK/wfdry-remove.json" 2>"$WORK/wfdry-remove.err"; then
  tail -30 "$WORK/wfdry-remove.err" >&2
  fail "wfdry: the uninstall dry run failed"
fi
same_tree "$H" wfdry
python3 - "$WORK/wfdry-remove.json" "$H/.claude" <<'PY'
import json, os, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
coco = os.path.join(sys.argv[2], "coco")
removes = [o["path"] for o in rows if o.get("op") == "remove"]
if not removes:
    sys.exit("the uninstall dry run removed nothing")
bad = [p for p in removes if not (p == coco or p.startswith(coco + os.sep))]
if bad:
    sys.exit("remove records outside coco/: %s" % bad)
want = set(os.path.join(coco, "hooks", name) for name in
           ("coco-workflow-pretooluse.sh", "coco-workflow-context.sh", "coco-workflow-pre-commit.sh"))
want.add(os.path.join(coco, "bin", "coco-gate"))
want.add(os.path.join(coco, "hooks"))
want.add(os.path.join(coco, "bin"))
want.add(coco)
if set(removes) != want:
    sys.exit("remove records\n%r\n!= %r" % (sorted(set(removes)), sorted(want)))
print("ok   the dry run lists the %s workflow paths" % len(removes))
PY

echo "=== the root installer passes --workflow-only to claude-code only ==="
mkdir -p "$WORK/root-home"
if ! HOME="$WORK/root-home" CLAUDE_HOME="$WORK/root-home/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" \
  bash "$ROOT/install.sh" --adapter claude-code --workflow-only --dry-run --json \
  >"$WORK/root-wf.json" 2>"$WORK/root-wf.err"; then
  tail -30 "$WORK/root-wf.err" >&2
  fail "root --adapter claude-code --workflow-only exited non-zero"
fi
python3 - "$WORK/root-wf.json" <<'PY'
import json, sys
lines = [l for l in open(sys.argv[1], encoding="utf-8").read().splitlines() if l.strip()]
summary = json.loads(lines[-1])["summary"]
if "workflow" not in summary or summary["link"] != 4:
    sys.exit("root plan: %s" % summary)
print("ok   the root installer planned 4 workflow links and no bundles")
PY
codex_status=0
HOME="$WORK/root-home" CLAUDE_HOME="$WORK/root-home/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" \
  bash "$ROOT/install.sh" --adapter codex --workflow-only --dry-run \
  >"$WORK/root-codex.out" 2>"$WORK/root-codex.err" || codex_status=$?
[[ $codex_status -eq 1 ]] || fail "root --adapter codex --workflow-only exited $codex_status"
grep -q "claude-code" "$WORK/root-codex.err" || fail "the refusal does not name claude-code"
for extra in --core-only "--systems gsd"; do
  combo_status=0
  # shellcheck disable=SC2086  # $extra is one or two words on purpose
  HOME="$WORK/root-home" CLAUDE_HOME="$WORK/root-home/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" \
    bash "$ROOT/install.sh" --adapter claude-code --workflow-only $extra --dry-run \
    >"$WORK/root-combo.out" 2>"$WORK/root-combo.err" || combo_status=$?
  [[ $combo_status -eq 1 ]] || fail "root --workflow-only $extra exited $combo_status, not 1"
  grep -q "cannot be combined" "$WORK/root-combo.err" || fail "root --workflow-only $extra: no refusal message"
done

echo "ok   --workflow-only installs and removes only the coco/ pieces, and a killed Remove finishes"
