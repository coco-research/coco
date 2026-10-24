#!/usr/bin/env bash
# The Claude Code installer reports every write as JSONL, and a real install
# saves the same lines to $CLAUDE_HOME/.coco/manifest.jsonl. Throwaway HOME,
# no network. Same shape as tests/check-claude-md-block.sh.
# Safety checks live in tests/check-install-safety.sh.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/install-home.sh"

echo "=== dry-run --json writes nothing and is JSONL ==="
H="$WORK/dry"
mkdir -p "$H"
snap "$H" > "$WORK/dry-before"
DRY_START=$(python3 -c 'import time; print("%.6f" % time.time())')
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --dry-run --json >"$WORK/dry.json" 2>"$WORK/dry.err"; then
  echo "installer failed; stderr:" >&2
  cat "$WORK/dry.err" >&2
  fail "dry-run --json exited non-zero"
fi
DRY_SECONDS=$(python3 -c 'import time,sys; print("%.3f" % (time.time()-float(sys.argv[1])))' "$DRY_START")
# Reported, not gated: wall-clock limits flake on loaded CI runners.
echo "dry-run seconds: $DRY_SECONDS"
snap "$H" > "$WORK/dry-after"
cmp -s "$WORK/dry-before" "$WORK/dry-after" || fail "dry-run changed the HOME tree"
[[ ! -e "$H/.claude" ]] || fail "dry-run created .claude"
grep -q "Coco · Claude Code adapter" "$WORK/dry.err" || fail "human text did not go to stderr"
grep -q "Linked:" "$WORK/dry.json" && fail "human text leaked to stdout" || true
check_jsonl "$WORK/dry.json" "$H/.claude" plan

echo "=== real install --json matches the manifest ==="
H="$WORK/real"
mkdir -p "$H"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --json >"$WORK/real.json" 2>"$WORK/real.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/real.err" >&2
  fail "install --json exited non-zero"
fi
MAN="$H/.claude/.coco/manifest.jsonl"
[[ -f "$MAN" ]] || fail "manifest missing"
cmp -s "$WORK/real.json" "$MAN" || fail "stdout JSONL differs from the manifest"
check_jsonl "$MAN" "$H/.claude" install
python3 - "$MAN" "$H/.claude/CLAUDE.md" <<'PY'
import hashlib, json, sys
man, claude = sys.argv[1:]
rows = [json.loads(l) for l in open(man, encoding="utf-8")]
block = [o for o in rows if o.get("op") == "block"][0]
if block.get("created") is not True or block.get("backup") is not None:
    sys.exit(f"fresh CLAUDE.md should be created with no backup: {block}")
digest = hashlib.sha256(open(claude, "rb").read()).hexdigest()
if block.get("sha256_after") != digest:
    sys.exit("fresh block sha256_after does not match CLAUDE.md")
kinds = {o.get("kind") for o in rows if o.get("op") == "write"}
if not {"dir", "manifest", "generated"} <= kinds:
    sys.exit(f"fresh kinds missing: {kinds}")
print("ok   fresh install created CLAUDE.md and recorded dirs, manifest, generated files")
PY
echo "FRESH SUMMARY $(tail -n 1 "$WORK/real.json")"

echo "=== second install keeps prior bytes; new files are pristine backups ==="
H="$WORK/again"
mkdir -p "$H"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --json >"$WORK/again.json" 2>"$WORK/again.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/again.err" >&2
  fail "setup install --json exited non-zero"
fi
MAN="$H/.claude/.coco/manifest.jsonl"
snap_tree "$H" "$WORK/real-before.json"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" >"$WORK/human.txt" 2>"$WORK/human.err"; then
  fail "second install exited non-zero"
fi
snap_tree "$H" "$WORK/again-after.json"
python3 - "$H/.claude" "$WORK/real-before.json" "$WORK/again-after.json" <<'PY'
import json, os, sys
target, before_path, after_path = sys.argv[1:]
before = json.load(open(before_path))
after = json.load(open(after_path))
manifest = os.path.join(target, ".coco", "manifest.jsonl")
backup = os.path.join(target, ".coco", "backup")
bad = []
for p, meta in before.items():
    if p == manifest:
        continue
    if after.get(p) != meta:
        bad.append("changed " + p)
for p in after:
    if p not in before and p != backup and not p.startswith(backup + os.sep):
        bad.append("new " + p)
if bad:
    sys.exit("re-install touched more than the manifest and .coco/backup:\n" + "\n".join(bad[:40]))
print("ok   re-install left prior bytes; new files are under .coco/backup")
PY
# A re-install marks every generated SI file it replaced, so the two manifests
# differ in exactly that field.
python3 - "$WORK/again.json" "$MAN" <<'PY'
import json, sys
first = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
second = [json.loads(l) for l in open(sys.argv[2], encoding="utf-8")]

def strip(rows):
    return [{k: v for k, v in o.items() if k != "replaces"} for o in rows]

if strip(first) != strip(second):
    sys.exit("second manifest changed more than the replaces field")
if any("replaces" in o for o in first):
    sys.exit("first install recorded replaces")
replaced = [o for o in second if o.get("op") == "write" and o.get("kind") == "generated"]
if not replaced:
    sys.exit("second install recorded no generated writes")
bad = [o["path"] for o in replaced if o.get("replaces") != "previous coco file"]
if bad:
    sys.exit("generated record without replaces: %s" % bad[:5])
block = [o for o in second if o.get("op") == "block"][0]
if block.get("created") is not True:
    sys.exit(f"re-install lost created: {block}")
print("ok   second manifest differs only by replaces, block created is still true")
PY
grep -q "^Wrote: " "$WORK/human.txt" || fail "human output has no Wrote: lines"
grep -q "^Linked: " "$WORK/human.txt" || fail "human output has no Linked: lines"
grep -q "Installed for Claude Code:" "$WORK/human.txt" || fail "human receipt missing"

echo "=== a HOME path with a space and a quote is still JSON ==="
Q="$WORK/home \"quoted\""
mkdir -p "$Q"
if ! HOME="$WORK" CLAUDE_HOME="$Q/.claude" bash "$ROOT/install.sh" --adapter claude-code --core-only --dry-run --json >"$WORK/quote.json" 2>"$WORK/quote.err"; then
  fail "quoted dry-run --json exited non-zero"
fi
python3 - "$WORK/quote.json" "$Q/.claude" <<'PY'
import json, sys
target = sys.argv[2]
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
if not lines:
    sys.exit("empty")
saw_quote = False
for i, line in enumerate(lines):
    obj = json.loads(line)
    if i == len(lines) - 1:
        if obj["summary"]["target"] != target:
            sys.exit(f"target {obj['summary']['target']!r}")
        if '"' not in obj["summary"]["target"]:
            sys.exit("decoded target lost the quote")
    elif '"' in obj.get("path", ""):
        saw_quote = True
if not saw_quote:
    sys.exit("no record path kept the quote")
print("ok   quoted path survived JSON")
PY
if ! HOME="$WORK" CLAUDE_HOME="$Q/.claude" bash "$ROOT/install.sh" --adapter claude-code --core-only --json >"$WORK/quote-real.json" 2>"$WORK/quote-real.err"; then
  fail "quoted install --json exited non-zero"
fi
python3 -c '
import json,sys
p=sys.argv[1]
lines=open(p,encoding="utf-8").read().splitlines()
for line in lines:
    json.loads(line)
print("ok   quoted manifest parses")
' "$Q/.claude/.coco/manifest.jsonl"
cmp -s "$WORK/quote-real.json" "$Q/.claude/.coco/manifest.jsonl" || fail "quoted install stdout differs from manifest"

echo "=== dry-run paths equal the paths a real install creates or changes ==="
H="$WORK/equiv"
mkdir -p "$H/.claude/skills/coco/keep" "$H/.claude/commands" "$H/.claude/projects" "$H/mine-skill"
printf 'user owned skill\n' > "$H/.claude/skills/officecli"
printf 'user dir\n' > "$H/.claude/skills/coco/keep/note"
printf 'user skill\n' > "$H/mine-skill/SKILL.md"
ln -s "$H/mine-skill" "$H/.claude/skills/karpathy-guidelines"
ln -s "$ROOT/skills/coco" "$H/.claude/skills/brainstorming"
printf 'user rules\n' > "$H/.claude/CLAUDE.md"
printf 'user si bytes\n' > "$H/user-si.md"
ln -s "$H/user-si.md" "$H/.claude/commands/SI-AI.md"
printf 'old coco command\n\nMade with CoCo Super Intelligence.\n' > "$H/.claude/commands/SI-AI-Orchestrate.md"
printf 'settings-v1\n' > "$H/.claude/settings.json"
printf 'local-v1\n' > "$H/.claude/settings.local.json"
printf 'cred-v1\n' > "$H/.claude/.credentials.json"
printf 'secret\n' > "$H/.claude/projects/secret"
cp "$H/.claude/CLAUDE.md" "$WORK/equiv-claude"
cp "$H/.claude/commands/SI-AI-Orchestrate.md" "$WORK/equiv-si"
cp "$H/user-si.md" "$WORK/equiv-user-si"
cp "$H/.claude/settings.json" "$WORK/equiv-settings"
cp "$H/.claude/.credentials.json" "$WORK/equiv-cred"
snap_tree "$H" "$WORK/equiv-tree.json"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" bash "$ADAPTER" --dry-run --json >"$WORK/equiv-plan.json" 2>"$WORK/equiv-plan.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -40 "$WORK/equiv-plan.err" >&2
  fail "equivalence dry-run exited non-zero"
fi
snap_tree "$H" "$WORK/equiv-dry-after.json"
python3 - "$WORK/equiv-tree.json" "$WORK/equiv-dry-after.json" <<'PY'
import json, sys
before = json.load(open(sys.argv[1]))
after = json.load(open(sys.argv[2]))
if after != before:
    sys.exit("dry-run changed the equivalence HOME")
print("ok   equivalence dry-run wrote nothing")
PY
if ! HOME="$H" CLAUDE_HOME="$H/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" bash "$ADAPTER" --json >"$WORK/equiv-real.json" 2>"$WORK/equiv-real.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -40 "$WORK/equiv-real.err" >&2
  fail "equivalence install exited non-zero"
fi
snap_tree "$H" "$WORK/equiv-after.json"
python3 - "$H" "$H/.claude" "$WORK/equiv-tree.json" "$WORK/equiv-after.json" "$WORK/equiv-plan.json" "$WORK/equiv-real.json" "$ROOT/skills/coco" "$WORK/equiv-claude" "$WORK/equiv-si" <<'PY'
import json, os, sys
root, target, before_path, after_path, plan_path, real_path, old_link, orig_claude, orig_si = sys.argv[1:]
before = json.load(open(before_path))
after = json.load(open(after_path))

def paths(file):
    out = []
    skips = []
    for line in open(file, encoding="utf-8"):
        obj = json.loads(line)
        op = obj.get("op")
        if op in ("link", "write", "block"):
            out.append(obj["path"])
        elif op == "skip":
            skips.append(obj["path"])
    return out, skips

changed = {p for p, meta in after.items() if before.get(p) != meta}
changed |= {p for p in before if p not in after}
plan, plan_skips = paths(plan_path)
real, real_skips = paths(real_path)
if len(plan) != len(set(plan)):
    sys.exit("dry-run plan has duplicate paths")
if set(plan) != set(real):
    sys.exit("dry-run paths differ from the real manifest:\n" + "\n".join(sorted(set(plan) ^ set(real))[:40]))
if set(plan_skips) != set(real_skips):
    sys.exit("dry-run skip paths differ from the real manifest:\n" + "\n".join(sorted(set(plan_skips) ^ set(real_skips))[:40]))
if set(plan) != changed:
    only_plan = sorted(set(plan) - changed)[:40]
    only_disk = sorted(changed - set(plan))[:40]
    sys.exit("plan paths != created or changed paths\nplan only:\n" + "\n".join(only_plan) + "\ndisk only:\n" + "\n".join(only_disk))
missing = [p for p in plan if p not in after]
if missing:
    sys.exit("planned path missing after install:\n" + "\n".join(missing[:20]))
for p in plan_skips:
    if p in changed:
        sys.exit(f"skip path was changed: {p}")
rows = [json.loads(l) for l in open(real_path, encoding="utf-8")]
block = [o for o in rows if o.get("op") == "block"][0]
pristine = os.path.join(target, ".coco", "backup", "CLAUDE.md")
if block.get("created") is not False or block.get("backup") != pristine:
    sys.exit(f"block backup: {block}")
if open(pristine, "rb").read() != open(orig_claude, "rb").read():
    sys.exit("pristine CLAUDE.md backup is not the original")
si_bak = os.path.join(target, ".coco", "backup", "commands", "SI-AI-Orchestrate.md")
if open(si_bak, "rb").read() != open(orig_si, "rb").read():
    sys.exit("pristine SI backup is not the original")
link = [o for o in rows if o.get("path") == os.path.join(target, "skills", "brainstorming")]
if len(link) != 1 or link[0].get("replaced_link") != old_link:
    sys.exit(f"replaced_link: {link}")
user_si = os.path.join(target, "commands", "SI-AI.md")
if not os.path.islink(user_si) or os.readlink(user_si) != os.path.join(root, "user-si.md"):
    sys.exit("SI user symlink was not restored")
if open(os.path.join(root, "user-si.md"), "rb").read() != b"user si bytes\n":
    sys.exit("SI user symlink target was written through")
print("ok   plan paths match the install diff")
# samples for the report
plan_rows = [json.loads(l) for l in open(plan_path, encoding="utf-8")]
def show(pred, label):
    hit = next(o for o in plan_rows if pred(o))
    print("SAMPLE", label, json.dumps(hit, separators=(",", ":")))
show(lambda o: o.get("op") == "write" and o.get("kind") == "backup" and o.get("path", "").endswith("/.coco/backup/CLAUDE.md"), "backup")
show(lambda o: o.get("op") == "link" and "replaced_link" in o, "replaced_link")
show(lambda o: o.get("op") == "skip" and o.get("reason") == "user link, not replaced", "skip")
PY
cmp -s "$H/.claude/settings.json" "$WORK/equiv-settings" || fail "equivalence settings.json changed"
cmp -s "$H/.claude/.credentials.json" "$WORK/equiv-cred" || fail "equivalence .credentials.json changed"
cmp -s "$H/user-si.md" "$WORK/equiv-user-si" || fail "user SI target bytes changed"
cp "$H/.claude/.coco/backup/CLAUDE.md" "$WORK/pristine-claude"
cp "$H/.claude/.coco/backup/commands/SI-AI-Orchestrate.md" "$WORK/pristine-si"
printf 'APPENDED\n' >> "$H/.claude/CLAUDE.md"
printf 'APPENDED\n' >> "$H/.claude/commands/SI-AI-Orchestrate.md"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" COCO_MANAGED_ROOT="$WORK/no-managed" bash "$ADAPTER" >/dev/null 2>"$WORK/equiv-again.err"; then
  fail "second equivalence install exited non-zero"
fi
cmp -s "$H/.claude/.coco/backup/CLAUDE.md" "$WORK/pristine-claude" || fail "second install overwrote the pristine CLAUDE.md backup"
cmp -s "$H/.claude/.coco/backup/commands/SI-AI-Orchestrate.md" "$WORK/pristine-si" || fail "second install overwrote the pristine SI backup"
grep -q "APPENDED" "$H/.claude/CLAUDE.md.coco-bak" || fail "coco-bak was not refreshed with the edited CLAUDE.md"
grep -q "APPENDED" "$H/.claude/CLAUDE.md" || fail "user text below the block was dropped"
grep -q "coco:rules-start" "$H/.claude/CLAUDE.md" || fail "rules block missing after re-install"

echo "=== dangling and old-coco links keep replaced_link across a re-install ==="
# The dangling target is a missing path inside this repo. A dangling link whose
# text points outside the repo is a user link and is not replaced (see safety).
H="$WORK/relink"
mkdir -p "$H/.claude/skills" "$H/old-coco/skills"
DANGLING="$ROOT/skills/brainstorming/does-not-exist"
OLD_COCO="$ROOT/skills/coco"
ln -s "$DANGLING" "$H/.claude/skills/brainstorming"
ln -s "$OLD_COCO" "$H/.claude/skills/officecli"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --json >"$WORK/relink-1.json" 2>"$WORK/relink-1.err"; then
  fail "first relink install exited non-zero"
fi
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --json >"$WORK/relink-2.json" 2>"$WORK/relink-2.err"; then
  fail "second relink install exited non-zero"
fi
cmp -s "$WORK/relink-1.json" "$WORK/relink-2.json" || fail "relink re-install manifest changed"
python3 - "$WORK/relink-2.json" "$H/.claude/skills/brainstorming" "$DANGLING" "$H/.claude/skills/officecli" "$OLD_COCO" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
pairs = [(sys.argv[2], sys.argv[3]), (sys.argv[4], sys.argv[5])]
for path, old in pairs:
    hit = [o for o in rows if o.get("op") == "link" and o.get("path") == path]
    if len(hit) != 1 or hit[0].get("replaced_link") != old:
        sys.exit(f"replaced_link lost for {path}: {hit}")
block = [o for o in rows if o.get("op") == "block"][0]
if block.get("created") is not True:
    sys.exit(f"relink re-install lost created: {block}")
print("ok   dangling and old-coco replaced_link survived re-install")
PY
[[ "$(readlink "$H/.claude/skills/brainstorming")" == "$ROOT/skills/brainstorming/" ]] || fail "dangling skill was not relinked"
[[ "$(readlink "$H/.claude/skills/officecli")" == "$ROOT/skills/officecli/" ]] || fail "old-coco skill was not relinked"

echo "PASS: install manifest"
