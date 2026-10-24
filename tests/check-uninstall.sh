#!/usr/bin/env bash
# Uninstall undoes a Claude Code install from its manifest.
# Edited files stay. Throwaway HOME. Helpers: tests/lib/install-home.sh.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/install-home.sh"

run_at() {
  local h=$1; shift
  # An empty managed root keeps this machine's real org settings out of the run.
  mkdir -p "$WORK/no-managed"
  HOME="$h" CLAUDE_HOME="$h/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" "$@"
}
install_core() {
  local h=$1
  if ! run_at "$h" bash "$ADAPTER" --core-only >"$WORK/install.out" 2>"$WORK/install.err"; then
    tail -30 "$WORK/install.err" >&2
    fail "install failed: $h"
  fi
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

echo "=== fresh HOME round-trip ==="
H="$WORK/fresh"
mkdir -p "$H"
save_tree "$H" fresh
install_core "$H"
if ! run_at "$H" bash "$ADAPTER" --uninstall >"$WORK/fresh-un.out" 2>"$WORK/fresh-un.err"; then
  tail -40 "$WORK/fresh-un.err" >&2
  fail "fresh uninstall failed"
fi
same_tree "$H" fresh
[[ ! -e "$H/.claude" ]] || fail "fresh: .claude remains"
echo "ok   fresh HOME matches the pre-install tree"

echo "=== populated HOME: dry-run matches the real uninstall, then the tree matches ==="
H="$WORK/pop"
OLD="$ROOT/skills/coco"
mkdir -p "$H/.claude/skills/coco/keep" "$H/.claude/commands" "$H/.claude/projects" "$H/mine-skill"
printf 'user owned skill\n' > "$H/.claude/skills/officecli"
printf 'user dir\n' > "$H/.claude/skills/coco/keep/note"
printf 'user skill\n' > "$H/mine-skill/SKILL.md"
ln -s "$H/mine-skill" "$H/.claude/skills/karpathy-guidelines"
ln -s "$OLD" "$H/.claude/skills/brainstorming"
printf 'user rules\n' > "$H/.claude/CLAUDE.md"
printf 'user si bytes\n' > "$H/.claude/commands/SI-mine.md"
printf 'settings-v1\n' > "$H/.claude/settings.json"
printf 'local-v1\n' > "$H/.claude/settings.local.json"
printf 'cred-v1\n' > "$H/.claude/.credentials.json"
printf 'secret\n' > "$H/.claude/projects/secret"
cp "$H/.claude/settings.json" "$WORK/pop-settings"
cp "$H/.claude/settings.local.json" "$WORK/pop-local"
cp "$H/.claude/.credentials.json" "$WORK/pop-cred"
cp "$H/.claude/projects/secret" "$WORK/pop-secret"
cp "$H/.claude/commands/SI-mine.md" "$WORK/pop-si"
save_tree "$H" pop
install_core "$H"
[[ "$(readlink "$H/.claude/skills/brainstorming")" != "$OLD" ]] || fail "install did not replace the link"
snap_tree "$H" "$WORK/pop-before.json"
if ! run_at "$H" bash "$ADAPTER" --uninstall --dry-run --json >"$WORK/pop-dry.json" 2>"$WORK/pop-dry.err"; then
  tail -40 "$WORK/pop-dry.err" >&2
  fail "populated dry-run failed"
fi
snap_tree "$H" "$WORK/pop-dry-after.json"
python3 - "$WORK/pop-before.json" "$WORK/pop-dry-after.json" <<'PY'
import json, sys
if json.load(open(sys.argv[1])) != json.load(open(sys.argv[2])):
    sys.exit("dry-run changed the populated HOME")
print("ok   uninstall dry-run wrote nothing")
PY
if grep -q '^Done\.$' "$WORK/pop-dry.json" || grep -q '^Uninstall$' "$WORK/pop-dry.json"; then
  fail "dry-run human text leaked to stdout"
fi
echo "=== sample uninstall dry-run ==="
python3 - "$WORK/pop-dry.json" <<'PY'
import json, sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
body = [line for line in lines if "summary" not in json.loads(line)]
for line in body[:5]:
    print("SAMPLE", line)
print("SAMPLE", lines[-1])
PY
if ! run_at "$H" bash "$ADAPTER" --uninstall --json >"$WORK/pop-real.json" 2>"$WORK/pop-real.err"; then
  tail -40 "$WORK/pop-real.err" >&2
  fail "populated uninstall failed"
fi
snap_tree "$H" "$WORK/pop-after.json"
python3 - "$H/.claude" "$WORK/pop-before.json" "$WORK/pop-after.json" \
  "$WORK/pop-dry.json" "$WORK/pop-real.json" "$VERSION" "$COMMIT" <<'PY'
import json, os, sys
target, before_p, after_p, dry_p, real_p, version, commit = sys.argv[1:]
target = os.path.abspath(target)
before = json.load(open(before_p))
after = json.load(open(after_p))

def load(path):
    remove, skip, summary = [], [], None
    seen = set()
    for line in open(path, encoding="utf-8"):
        obj = json.loads(line)
        if "summary" in obj:
            summary = obj["summary"]
            continue
        op = obj.get("op")
        if op not in ("remove", "skip"):
            sys.exit("bad op: %s" % obj)
        p = obj.get("path")
        if p in seen:
            sys.exit("duplicate path: %s" % p)
        seen.add(p)
        if not (p == target or p.startswith(target + os.sep)):
            sys.exit("path outside target: %s" % p)
        if op == "remove":
            remove.append(p)
        else:
            if not isinstance(obj.get("reason"), str) and obj.get("restore") != "block-stripped":
                sys.exit("skip reason: %s" % obj)
            skip.append(p)
    return remove, skip, summary

def check_summary(summary, nremove, nskip, label):
    need = ("adapter", "version", "commit", "target", "remove", "skip", "paths", "managed_settings")
    missing = [k for k in need if k not in summary]
    if missing:
        sys.exit("%s summary missing %s" % (label, missing))
    if summary["adapter"] != "claude-code" or summary["version"] != version:
        sys.exit("%s summary identity: %s" % (label, summary))
    if summary["commit"] != (commit or None) or summary["target"] != target:
        sys.exit("%s summary target/commit: %s" % (label, summary))
    if summary["remove"] != nremove or summary["skip"] != nskip or summary["paths"] != nremove:
        sys.exit("%s summary counts: %s" % (label, summary))
    ms = summary["managed_settings"]
    if not isinstance(ms, list) or not all(isinstance(m, str) for m in ms):
        sys.exit("managed_settings %r" % ms)

dry_r, dry_s, dry_sum = load(dry_p)
real_r, real_s, real_sum = load(real_p)
check_summary(dry_sum, len(dry_r), len(dry_s), "dry")
check_summary(real_sum, len(real_r), len(real_s), "real")
if dry_sum["managed_settings"] != real_sum["managed_settings"]:
    sys.exit("managed_settings drifted")
if set(dry_r) != set(real_r) or set(dry_s) != set(real_s):
    sys.exit("dry-run paths differ from the real uninstall")
changed = {p for p, meta in after.items() if before.get(p) != meta}
changed |= {p for p in before if p not in after}
if set(real_r) != changed:
    only_plan = sorted(set(real_r) - changed)[:30]
    only_disk = sorted(changed - set(real_r))[:30]
    sys.exit("remove paths != changed paths\nplan only:\n" + "\n".join(only_plan) + "\ndisk only:\n" + "\n".join(only_disk))
for p in real_s:
    if p in changed:
        sys.exit("skip path was changed: %s" % p)
print("ok   dry-run remove/skip paths match the uninstall diff")
PY
[[ "$(readlink "$H/.claude/skills/brainstorming")" == "$OLD" ]] || fail "replaced_link was not recreated"
cmp -s "$H/.claude/settings.json" "$WORK/pop-settings" || fail "settings.json changed"
cmp -s "$H/.claude/settings.local.json" "$WORK/pop-local" || fail "settings.local.json changed"
cmp -s "$H/.claude/.credentials.json" "$WORK/pop-cred" || fail ".credentials.json changed"
cmp -s "$H/.claude/projects/secret" "$WORK/pop-secret" || fail "projects/secret changed"
cmp -s "$H/.claude/commands/SI-mine.md" "$WORK/pop-si" || fail "SI-mine.md changed"
[[ -d "$H/.claude/skills/coco/keep" && ! -L "$H/.claude/skills/coco" ]] || fail "user skill dir was removed"
same_tree "$H" pop
if ! run_at "$H" bash "$ADAPTER" --uninstall >"$WORK/pop-again.out" 2>"$WORK/pop-again.err"; then
  fail "second uninstall failed"
fi
grep -F "nothing to uninstall (no manifest)" "$WORK/pop-again.out" "$WORK/pop-again.err" >/dev/null \
  || fail "second uninstall did not say nothing to uninstall"
echo "ok   populated HOME matches the pre-install tree"

echo "=== an edited generated file is kept; an unedited one is restored ==="
H="$WORK/probe"
mkdir -p "$H"
install_core "$H"
python3 - "$H/.claude/.coco/manifest.jsonl" <<'PY'
import hashlib, json, os, sys
man = sys.argv[1]
home = json.loads(open(man, encoding="utf-8").read().splitlines()[-1])["summary"]["target"]
root = os.path.join(home, ".coco", "backup")
os.makedirs(root)
gen, orig = b"generated\n", b"original\n"
pairs = (("probe-keep.txt", gen), ("probe-restore.txt", gen))
recs = []
for name, data in pairs:
    path = os.path.join(home, name)
    bak = os.path.join(root, name)
    open(path, "wb").write(data)
    open(bak, "wb").write(orig)
    os.chmod(path, 0o644)
    os.chmod(bak, 0o640)
    gsha = hashlib.sha256(data).hexdigest()
    osha = hashlib.sha256(orig).hexdigest()
    rec = {"op": "write", "path": path, "kind": "generated", "sha256": gsha, "sha256_after": gsha, "backup": bak}
    bak_rec = {"op": "write", "path": bak, "kind": "backup", "sha256": osha, "sha256_after": osha}
    recs.extend((rec, bak_rec))
with open(man, "a", encoding="utf-8") as fh:
    for rec in recs:
        fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
open(os.path.join(home, "probe-keep.txt"), "ab").write(b"edited\n")
PY
if ! run_at "$H" bash "$ADAPTER" --uninstall --json >"$WORK/probe.json" 2>"$WORK/probe.err"; then
  tail -40 "$WORK/probe.err" >&2
  fail "probe uninstall failed"
fi
python3 - "$H/.claude" "$WORK/probe.json" <<'PY'
import json, os, sys
home, src = sys.argv[1:]
# The manifest's target spelling wins over the shell path (/var vs /private/var).
rows = [json.loads(line) for line in open(src, encoding="utf-8")]
target = [o for o in rows if "summary" in o][-1]["summary"]["target"]
keep = os.path.join(target, "probe-keep.txt")
restore = os.path.join(target, "probe-restore.txt")
keep_bak = os.path.join(target, ".coco", "backup", "probe-keep.txt")
restore_bak = os.path.join(target, ".coco", "backup", "probe-restore.txt")
if open(keep, "rb").read() != b"generated\nedited\n":
    sys.exit("edited generated file was not kept")
if open(keep_bak, "rb").read() != b"original\n":
    sys.exit("backup of the edited file was removed or changed")
if open(restore, "rb").read() != b"original\n":
    sys.exit("unedited generated file was not restored")
mode = os.stat(restore).st_mode & 0o777
if mode != 0o640:
    sys.exit("restored mode is %o" % mode)
if os.path.lexists(restore_bak):
    sys.exit("backup of the restored file is still there")
skips = [o for o in rows if o.get("path") == keep]
if len(skips) != 1 or skips[0].get("op") != "skip" or skips[0].get("reason") != "edited since install, kept":
    sys.exit("edited file skip: %s" % skips)
removes = [o for o in rows if o.get("path") == restore]
if len(removes) != 1 or removes[0].get("op") != "remove":
    sys.exit("restored file remove: %s" % removes)
print("ok   edited generated file kept, unedited file restored")
PY

echo "=== an edited CLAUDE.md keeps the edit and loses only the block ==="
H="$WORK/editmd"
mkdir -p "$H/.claude"
printf 'user rules\n' > "$H/.claude/CLAUDE.md"
install_core "$H"
cp "$H/.claude/.coco/backup/CLAUDE.md" "$WORK/edit-bak"
printf 'APPENDED\n' >> "$H/.claude/CLAUDE.md"
if ! run_at "$H" bash "$ADAPTER" --uninstall --json >"$WORK/edit.json" 2>"$WORK/edit.err"; then
  tail -40 "$WORK/edit.err" >&2
  fail "edited CLAUDE.md uninstall failed"
fi
grep -q '^user rules$' "$H/.claude/CLAUDE.md" || fail "user rules line missing"
grep -q '^APPENDED$' "$H/.claude/CLAUDE.md" || fail "appended edit missing"
if grep -q 'coco:rules-start' "$H/.claude/CLAUDE.md"; then
  fail "rules block still present"
fi
cmp -s "$H/.claude/.coco/backup/CLAUDE.md" "$WORK/edit-bak" || fail "pristine backup was not kept"
python3 - "$WORK/edit.json" "$H/.claude/CLAUDE.md" <<'PY'
import json, os, sys
rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8")]
want = os.path.abspath(sys.argv[2])
hit = [o for o in rows if o.get("op") == "remove" and os.path.abspath(o.get("path", "")) == want]
if len(hit) != 1 or hit[0].get("restore") != "block-stripped":
    sys.exit("block-stripped record: %s" % hit)
print("ok   edited CLAUDE.md kept the edit and dropped the block")
PY

echo "=== a replaced inside-target CLAUDE.md symlink keeps the link ==="
H="$WORK/inlink"
mkdir -p "$H/.claude/dot"
printf 'original rules\n' > "$H/.claude/dot/CLAUDE.md"
ln -s "$H/.claude/dot/CLAUDE.md" "$H/.claude/CLAUDE.md"
cp "$H/.claude/dot/CLAUDE.md" "$WORK/inlink-bytes"
save_tree "$H" inlink
install_core "$H"
if ! run_at "$H" bash "$ADAPTER" --uninstall >"$WORK/inlink-un.out" 2>"$WORK/inlink-un.err"; then
  tail -40 "$WORK/inlink-un.err" >&2
  fail "inside-link uninstall failed"
fi
[[ -L "$H/.claude/CLAUDE.md" && "$(readlink "$H/.claude/CLAUDE.md")" == "$H/.claude/dot/CLAUDE.md" ]] \
  || fail "inside-link symlink was not kept"
cmp -s "$H/.claude/dot/CLAUDE.md" "$WORK/inlink-bytes" || fail "inside-link bytes were not restored"
same_tree "$H" inlink
echo "ok   inside-target CLAUDE.md link kept and bytes restored"

echo "=== a failure mid-uninstall leaves HOME unchanged ==="
H="$WORK/boom"
mkdir -p "$H/.claude"
printf 'user rules stay\n' > "$H/.claude/CLAUDE.md"
install_core "$H"
save_tree "$H" boom
boom_status=0
run_at "$H" env COCO_INSTALL_FAIL_AT="$H/.claude/.coco/manifest.jsonl" \
  bash "$ADAPTER" --uninstall --json >"$WORK/boom.json" 2>"$WORK/boom.err" || boom_status=$?
[[ $boom_status -eq 1 ]] || fail "boom: exit $boom_status"
same_tree "$H" boom
if grep -q '{"summary":' "$WORK/boom.json"; then
  fail "boom: emitted a summary"
fi
if grep -q '^Done\.$' "$WORK/boom.err" || grep -q '^Done\.$' "$WORK/boom.json"; then
  fail "boom: said Done"
fi
[[ ! -e "$H/.claude/.coco/install.lock" ]] || fail "boom: left install.lock"
echo "ok   mid-uninstall failure restored HOME"

echo "=== a hostile manifest line is ignored ==="
H="$WORK/hostile"
OUT="$WORK/hostile-out"
mkdir -p "$H" "$OUT"
printf 'sentinel\n' > "$OUT/sentinel"
printf 'evil\n' > "$OUT/evil"
save_tree "$H" hostile
save_tree "$OUT" hostile-out
install_core "$H"
python3 - "$H/.claude/.coco/manifest.jsonl" "$OUT/sentinel" "$OUT/evil" <<'PY'
import json, os, sys
man, sentinel, evil = sys.argv[1:]
home = json.loads(open(man, encoding="utf-8").read().splitlines()[-1])["summary"]["target"]
lines = [
    "{not-json",
    json.dumps({"op": "write", "path": sentinel, "kind": "generated", "sha256_after": "deadbeef"}),
    json.dumps({
        "op": "write", "path": os.path.join(home, "probe-x"), "kind": "generated",
        "sha256_after": "deadbeef", "backup": evil,
    }),
    json.dumps({
        "op": "write", "path": os.path.join(home, "probe-y"), "kind": "generated",
        "sha256_after": "deadbeef",
        "backup": os.path.join(home, ".coco", "backup-evil", "x"),
    }),
]
with open(man, "a", encoding="utf-8") as fh:
    for line in lines:
        fh.write(line + "\n")
PY
if ! run_at "$H" bash "$ADAPTER" --uninstall >"$WORK/hostile-un.out" 2>"$WORK/hostile-un.err"; then
  tail -40 "$WORK/hostile-un.err" >&2
  fail "hostile uninstall failed"
fi
same_tree "$H" hostile
same_tree "$OUT" hostile-out
echo "ok   hostile manifest lines were ignored"

echo "=== a protected path in the manifest refuses the uninstall ==="
H="$WORK/guard"
mkdir -p "$H"
install_core "$H"
printf 'settings-v1\n' > "$H/.claude/settings.json"
python3 - "$H/.claude/.coco/manifest.jsonl" <<'PY'
import hashlib, json, os, sys
man = sys.argv[1]
home = json.loads(open(man, encoding="utf-8").read().splitlines()[-1])["summary"]["target"]
path = os.path.join(home, "settings.json")
digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
rec = {"op": "write", "path": path, "kind": "generated", "sha256": digest, "sha256_after": digest}
with open(man, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
PY
save_tree "$H" guard
guard_status=0
run_at "$H" bash "$ADAPTER" --uninstall --json >"$WORK/guard.json" 2>"$WORK/guard.err" || guard_status=$?
[[ $guard_status -eq 1 ]] || fail "protected: exit $guard_status"
grep -F "REFUSE:" "$WORK/guard.err" >/dev/null || fail "protected: missing refusal"
same_tree "$H" guard
if grep -q '{"summary":' "$WORK/guard.json"; then
  fail "protected: emitted a summary"
fi
echo "ok   protected path refused and HOME was not modified"

echo "PASS: uninstall"
