#!/usr/bin/env bash
# Install safety: user files, directories, and symlinks stay; protected files
# stay untouched; failures write nothing; the install lock is exclusive.
# Throwaway HOME, no network. Helpers: tests/lib/install-home.sh.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/install-home.sh"

echo "=== user files, directories, and symlinks are kept; protected files are untouched ==="
H="$WORK/stale"
mkdir -p "$H/.claude/skills/coco/keep" "$H/.claude/projects" "$H/mine-skill"
USER_FILE="$H/.claude/skills/officecli"
USER_DIR="$H/.claude/skills/coco"
USER_LINK="$H/.claude/skills/karpathy-guidelines"
REPLACED="$H/.claude/skills/brainstorming"
OLD_TARGET="$ROOT/skills/coco"
printf 'user owned skill\n' > "$USER_FILE"
printf 'user dir\n' > "$USER_DIR/keep/note"
printf 'user skill\n' > "$H/mine-skill/SKILL.md"
ln -s "$H/mine-skill" "$USER_LINK"
ln -s "$OLD_TARGET" "$REPLACED"
printf 'settings-v1\n' > "$H/.claude/settings.json"
printf 'local-v1\n' > "$H/.claude/settings.local.json"
printf 'cred-v1\n' > "$H/.claude/.credentials.json"
printf 'secret\n' > "$H/.claude/projects/secret"
cp "$USER_FILE" "$WORK/user-before"
cp "$USER_DIR/keep/note" "$WORK/dir-before"
cp "$H/mine-skill/SKILL.md" "$WORK/link-before"
cp "$H/.claude/settings.json" "$WORK/settings-before"
cp "$H/.claude/settings.local.json" "$WORK/local-before"
cp "$H/.claude/.credentials.json" "$WORK/cred-before"
cp "$H/.claude/projects/secret" "$WORK/secret-before"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --json >"$WORK/stale.json" 2>"$WORK/stale.err"; then
  fail "stale install exited non-zero"
fi
cmp -s "$USER_FILE" "$WORK/user-before" || fail "user file was modified"
[[ ! -L "$USER_FILE" ]] || fail "user file was replaced with a symlink"
[[ -d "$USER_DIR" && ! -L "$USER_DIR" ]] || fail "user directory was replaced"
cmp -s "$USER_DIR/keep/note" "$WORK/dir-before" || fail "user directory contents changed"
[[ -L "$USER_LINK" && "$(readlink "$USER_LINK")" == "$H/mine-skill" ]] || fail "user symlink was replaced"
cmp -s "$H/mine-skill/SKILL.md" "$WORK/link-before" || fail "user symlink target changed"
[[ -L "$REPLACED" && "$(readlink "$REPLACED")" == "$ROOT/skills/brainstorming/" ]] || fail "in-repo symlink was not relinked"
cmp -s "$H/.claude/settings.json" "$WORK/settings-before" || fail "settings.json changed"
cmp -s "$H/.claude/settings.local.json" "$WORK/local-before" || fail "settings.local.json changed"
cmp -s "$H/.claude/.credentials.json" "$WORK/cred-before" || fail ".credentials.json changed"
cmp -s "$H/.claude/projects/secret" "$WORK/secret-before" || fail "projects/ file changed"
grep -q "STALE:" "$WORK/stale.err" || fail "STALE warning missing from stderr"
python3 - "$WORK/stale.json" "$USER_FILE" "$USER_DIR" "$USER_LINK" "$REPLACED" "$OLD_TARGET" <<'PY'
import json, sys
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
user_file, user_dir, user_link, replaced, old = sys.argv[2:]
rows = [json.loads(l) for l in lines[:-1]]
skips = [o for o in rows if o.get("op") == "skip"]
def one(pred, label):
    hit = [o for o in skips if pred(o)]
    if len(hit) != 1:
        sys.exit(f"expected one {label}, got {hit or skips}")
one(lambda o: o.get("path") == user_file and o.get("reason") == "user file, not overwritten", "user file skip")
one(lambda o: o.get("path") == user_dir and o.get("reason") == "user file, not overwritten", "user dir skip")
one(lambda o: o.get("path") == user_link and o.get("reason") == "user link, not replaced", "user link skip")
links = [o for o in rows if o.get("op") == "link" and o.get("path") == replaced]
if len(links) != 1 or links[0].get("replaced_link") != old:
    sys.exit(f"replaced_link: {links}")
summary = json.loads(lines[-1])["summary"]
if summary["skip"] != len(skips):
    sys.exit("skip count does not match records")
print("ok   skip kept the user file, directory, and symlink")
PY

echo "=== managed settings are reported and do not change the install ==="
MANAGED="$WORK/managed dir/managed-settings.json"
mkdir -p "$WORK/managed dir"
printf '{}\n' > "$MANAGED"
H="$WORK/managed"
mkdir -p "$H"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" COCO_MANAGED_SETTINGS_PATHS="$WORK/missing-managed.json:$MANAGED" bash "$ADAPTER" --core-only --dry-run --json >"$WORK/managed.json" 2>"$WORK/managed.err"; then
  fail "managed dry-run exited non-zero"
fi
python3 - "$WORK/managed.json" "$MANAGED" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
got = rows[-1]["summary"]["managed_settings"]
if got != sys.argv[2]:
    sys.exit(f"managed_settings {got!r} != {sys.argv[2]!r}")
print("ok   managed_settings reports the first existing file")
PY
grep -F -q "Managed settings: $MANAGED" "$WORK/managed.err" || fail "managed settings line missing from stderr"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" COCO_MANAGED_SETTINGS_PATHS="$WORK/missing-managed.json" bash "$ADAPTER" --core-only --dry-run >"$WORK/managed-none.txt" 2>"$WORK/managed-none.err"; then
  fail "missing managed dry-run exited non-zero"
fi
grep -F -q "Managed settings: none" "$WORK/managed-none.txt" || fail "human output did not say managed settings none"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" COCO_MANAGED_SETTINGS_PATHS="$WORK/missing-managed.json" bash "$ADAPTER" --core-only --dry-run --json >"$WORK/managed-none.json" 2>/dev/null; then
  fail "missing managed json dry-run exited non-zero"
fi
python3 - "$WORK/managed-none.json" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
if rows[-1]["summary"]["managed_settings"] is not None:
    sys.exit(rows[-1]["summary"]["managed_settings"])
print("ok   missing managed settings file reports null")
PY

echo "=== a user SI file is not recorded; a generated name is backed up ==="
H="$WORK/simine"
mkdir -p "$H/.claude/commands"
printf 'mine-bytes-v1\n' > "$H/.claude/commands/SI-mine.md"
printf 'orch-bytes-v1\n' > "$H/.claude/commands/SI-AI-Orchestrate.md"
cp "$H/.claude/commands/SI-mine.md" "$WORK/simine-before"
cp "$H/.claude/commands/SI-AI-Orchestrate.md" "$WORK/siorch-before"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --systems superintelligence --json >"$WORK/simine.json" 2>"$WORK/simine.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/simine.err" >&2
  fail "SI-mine install exited non-zero"
fi
cmp -s "$H/.claude/commands/SI-mine.md" "$WORK/simine-before" || fail "SI-mine.md bytes changed"
python3 - "$WORK/simine.json" "$H/.claude/commands/SI-mine.md" "$H/.claude/commands/SI-AI-Orchestrate.md" "$WORK/siorch-before" <<'PY'
import json, sys
man, mine, generated, orig = sys.argv[1:]
raw = open(man, encoding="utf-8").read()
if mine in raw:
    sys.exit("user SI file appears in the manifest")
orig_bytes = open(orig, "rb").read()
rows = [json.loads(l) for l in raw.splitlines()]
rec = [o for o in rows if o.get("path") == generated]
if len(rec) != 1 or not rec[0].get("backup"):
    sys.exit(f"generated file has no backup: {rec}")
bak = rec[0]["backup"]
if open(bak, "rb").read() != orig_bytes:
    sys.exit("backup is not the pre-existing generated-name file")
kind = [o for o in rows if o.get("op") == "write" and o.get("kind") == "backup" and o.get("path") == bak]
if len(kind) != 1:
    sys.exit(f"missing backup record for {bak}")
print("ok   user SI file untouched and unrecorded; overwritten generated name has a backup")
PY

echo "=== a failing SI generator aborts --dry-run --json with no summary ==="
COPY="$WORK/broken-repo"
cp -cR "$ROOT" "$COPY" 2>/dev/null || { rm -rf "$COPY"; cp -R "$ROOT" "$COPY"; }
cat > "$COPY/systems/superintelligence/ai/scripts/build_commands.py" <<'PY'
import sys
sys.stderr.write("boom: generator failed\n")
sys.exit(1)
PY
H="$WORK/failgen"
mkdir -p "$H"
fail_status=0
HOME="$H" CLAUDE_HOME="$H/.claude" bash "$COPY/adapters/claude-code/install.sh" --dry-run --json >"$WORK/fail.json" 2>"$WORK/fail.err" || fail_status=$?
[[ $fail_status -ne 0 ]] || fail "failing generator: dry-run --json exited 0"
if grep -q '^{"summary":' "$WORK/fail.json"; then
  fail "failing generator: emitted a summary line"
fi
grep -q "boom: generator failed" "$WORK/fail.err" || fail "failing generator: stderr was not printed"
[[ ! -e "$H/.claude" ]] || fail "failing generator dry-run created .claude"
echo "ok   failing generator exits $fail_status and emits no summary"

echo "=== missing python3 exits 1 and writes nothing ==="
NOBIN="$WORK/nobin"
mkdir -p "$NOBIN"
ln -s /usr/bin/dirname "$NOBIN/dirname"
BASH_BIN=$(command -v bash)
H="$WORK/nopy"
mkdir -p "$H"
printf 'keep\n' > "$H/keep"
tree_id "$H" >"$WORK/nopy-before"
py_status=0
PATH="$NOBIN" HOME="$H" CLAUDE_HOME="$H/.claude" "$BASH_BIN" "$ADAPTER" --dry-run >"$WORK/nopy.out" 2>"$WORK/nopy.err" || py_status=$?
[[ $py_status -eq 1 ]] || fail "missing python3: exit $py_status"
grep -F -x "coco install needs python3 (macOS: xcode-select --install; Linux: your package manager)" "$WORK/nopy.err" || fail "missing python3: message"
[[ ! -s "$WORK/nopy.out" ]] || fail "missing python3: wrote stdout"
[[ ! -e "$H/.claude" ]] || fail "missing python3: created .claude"
tree_id "$H" >"$WORK/nopy-after"
cmp -s "$WORK/nopy-before" "$WORK/nopy-after" || fail "missing python3: HOME changed"
echo "ok   missing python3 exits 1 and writes nothing"

echo "=== a generator that fails after planning leaves HOME unchanged ==="
COPY="$WORK/planfail-repo"
cp -cR "$ROOT" "$COPY" 2>/dev/null || { rm -rf "$COPY"; cp -R "$ROOT" "$COPY"; }
cat > "$COPY/systems/superintelligence/ai/scripts/build_commands.py" <<'PY'
import os, sys
if "--list" in sys.argv:
    d = os.environ["COCO_SI_COMMANDS_DIR"]
    for name in ("SI-Hold.md", "SI-File.md", "SI-Link.md"):
        sys.stdout.write("  would write %s/%s\n" % (d, name))
    sys.exit(0)
sys.stderr.write("boom after plan\n")
sys.exit(1)
PY
cat > "$COPY/systems/superintelligence/scripts/build_meta_commands.py" <<'PY'
import sys
if "--list" in sys.argv:
    sys.exit(0)
sys.stderr.write("meta should not run\n")
sys.exit(1)
PY
H="$WORK/planfail"
mkdir -p "$H/.claude/commands" "$H/outside"
printf 'hold-target\n' > "$H/outside/hold-target"
printf 'file-bytes\n' > "$H/.claude/commands/SI-File.md"
printf 'link-target\n' > "$COPY/link-target.md"
ln -s "$H/outside/hold-target" "$H/.claude/commands/SI-Hold.md"
ln -s "$COPY/link-target.md" "$H/.claude/commands/SI-Link.md"
printf 'sentinel\n' > "$H/sentinel"
tree_id "$H" >"$WORK/planfail-before"
pf_status=0
HOME="$H" CLAUDE_HOME="$H/.claude" bash "$COPY/adapters/claude-code/install.sh" --systems superintelligence >"$WORK/planfail.out" 2>"$WORK/planfail.err" || pf_status=$?
[[ $pf_status -ne 0 ]] || fail "plan-fail generator exited 0"
grep -q "boom after plan" "$WORK/planfail.err" || fail "plan-fail: boom missing from stderr"
# Generators run once into a staging dir and fail before any HOME write, so the
# old --list pass (which printed Skip for the held link) is gone.
grep -q "Done." "$WORK/planfail.out" && fail "plan-fail: said Done" || true
tree_id "$H" >"$WORK/planfail-after"
if ! cmp -s "$WORK/planfail-before" "$WORK/planfail-after"; then
  diff -u "$WORK/planfail-before" "$WORK/planfail-after" | head -80 >&2 || true
  fail "plan-fail: HOME changed"
fi
echo "ok   generator failure after planning restored HOME"

echo "=== two user symlinks with the same basename both survive ==="
COPY="$WORK/twolink-repo"
cp -cR "$ROOT" "$COPY" 2>/dev/null || { rm -rf "$COPY"; cp -R "$ROOT" "$COPY"; }
cat > "$COPY/systems/superintelligence/ai/scripts/build_commands.py" <<'PY'
import os, sys
d = os.environ["COCO_SI_COMMANDS_DIR"]
names = ("Same.md", "nested/Same.md")
if "--list" in sys.argv:
    for name in names:
        sys.stdout.write("  would write %s/%s\n" % (d, name))
    sys.exit(0)
for name in names:
    p = os.path.join(d, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("GENERATED\n")
sys.exit(0)
PY
cat > "$COPY/systems/superintelligence/scripts/build_meta_commands.py" <<'PY'
import sys
sys.exit(0)
PY
H="$WORK/twolink"
mkdir -p "$H/.claude/commands/nested" "$H/outside"
printf 'alpha\n' > "$H/outside/alpha"
printf 'beta\n' > "$H/outside/beta"
ln -s "$H/outside/alpha" "$H/.claude/commands/Same.md"
ln -s "$H/outside/beta" "$H/.claude/commands/nested/Same.md"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$COPY/adapters/claude-code/install.sh" --systems superintelligence >"$WORK/twolink.out" 2>"$WORK/twolink.err"; then
  tail -40 "$WORK/twolink.err" >&2
  fail "two-link install exited non-zero"
fi
[[ -L "$H/.claude/commands/Same.md" && -L "$H/.claude/commands/nested/Same.md" ]] || fail "same-basename links are not both symlinks"
[[ "$(readlink "$H/.claude/commands/Same.md")" == "$H/outside/alpha" ]] || fail "Same.md link lost"
[[ "$(readlink "$H/.claude/commands/nested/Same.md")" == "$H/outside/beta" ]] || fail "nested Same.md link lost"
printf 'alpha\n' > "$WORK/alpha-expect"
printf 'beta\n' > "$WORK/beta-expect"
cmp -s "$H/outside/alpha" "$WORK/alpha-expect" || fail "alpha bytes changed"
cmp -s "$H/outside/beta" "$WORK/beta-expect" || fail "beta bytes changed"
echo "ok   two same-basename user links survived"

echo "=== a held install lock stops a second install ==="
H="$WORK/lock"
mkdir -p "$H/.claude"
printf 'keep\n' > "$H/keep"
tree_id "$H" >"$WORK/lock-before"
# Hold the same flock a running install takes (system temp dir, keyed by realpath of the target).
python3 - "$H/.claude" "$WORK/lock.ready" <<'PY' &
import fcntl, hashlib, os, sys, tempfile, time
key = hashlib.sha256(os.path.realpath(sys.argv[1]).encode("utf-8")).hexdigest()
fh = open(os.path.join(tempfile.gettempdir(), "coco-install-%s.lock" % key), "a+")
fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
open(sys.argv[2], "w").close()
time.sleep(30)
PY
holder=$!
for _ in $(seq 1 100); do [[ -e "$WORK/lock.ready" ]] && break; sleep 0.1; done
[[ -e "$WORK/lock.ready" ]] || fail "lock holder did not start"
lk_status=0
HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only >"$WORK/lock.out" 2>"$WORK/lock.err" || lk_status=$?
[[ $lk_status -eq 1 ]] || fail "held lock: exit $lk_status"
grep -F -q "another coco install is running for this target; wait for it to finish" "$WORK/lock.err" || fail "held lock: message"
tree_id "$H" >"$WORK/lock-after"
if ! cmp -s "$WORK/lock-before" "$WORK/lock-after"; then
  diff -u "$WORK/lock-before" "$WORK/lock-after" | head -40 >&2 || true
  fail "held lock: HOME changed"
fi
dr_status=0
HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --dry-run >"$WORK/lockdry.out" 2>"$WORK/lockdry.err" || dr_status=$?
[[ $dr_status -eq 0 ]] || fail "dry-run while locked exited $dr_status"
kill "$holder" 2>/dev/null || true; wait "$holder" 2>/dev/null || true
mkdir -p "$WORK/dry" "$WORK/real"
if ! HOME="$WORK/dry" CLAUDE_HOME="$WORK/dry/.claude" bash "$ADAPTER" --dry-run --json >"$WORK/dry.json" 2>"$WORK/lock-dry.err"; then
  echo "installer failed; stderr:" >&2
  cat "$WORK/lock-dry.err" >&2
  fail "dry-run --json exited non-zero"
fi
if ! HOME="$WORK/real" CLAUDE_HOME="$WORK/real/.claude" bash "$ADAPTER" --json >"$WORK/real.json" 2>"$WORK/lock-real.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/lock-real.err" >&2
  fail "install --json exited non-zero"
fi
grep -F -q 'install.lock' "$WORK/dry.json" && fail "plan contains install.lock"
grep -F -q 'install.lock' "$WORK/real.json" && fail "manifest contains install.lock"
[[ ! -e "$WORK/real/.claude/.coco/install.lock" ]] || fail "successful install left install.lock"
echo "ok   install lock is exclusive and stays out of the plan"

echo "=== a symlinked directory inside the target cannot escape ==="
H="$WORK/escape"
OUT="$WORK/escape-out"
mkdir -p "$H/.claude" "$OUT"
printf 'sentinel\n' > "$OUT/sentinel"
ln -s "$OUT" "$H/.claude/skills"
tree_id "$H" >"$WORK/esc-h-before"
tree_id "$OUT" >"$WORK/esc-o-before"
esc_status=0
HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only >"$WORK/esc.out" 2>"$WORK/esc.err" || esc_status=$?
[[ $esc_status -ne 0 ]] || fail "escape: install exited 0"
tree_id "$H" >"$WORK/esc-h-after"
tree_id "$OUT" >"$WORK/esc-o-after"
if ! cmp -s "$WORK/esc-h-before" "$WORK/esc-h-after"; then
  diff -u "$WORK/esc-h-before" "$WORK/esc-h-after" | head -40 >&2 || true
  fail "escape: HOME changed"
fi
if ! cmp -s "$WORK/esc-o-before" "$WORK/esc-o-after"; then
  diff -u "$WORK/esc-o-before" "$WORK/esc-o-after" | head -40 >&2 || true
  fail "escape: wrote outside"
fi
echo "ok   symlinked skills dir is refused and nothing is written outside"

echo "=== a failure mid-apply restores HOME byte for byte ==="
H="$WORK/rollback"
mkdir -p "$H/.claude/skills"
printf 'user file stays\n' > "$H/.claude/user-file"
printf 'user rules stay\n' > "$H/.claude/CLAUDE.md"
ln -s "$ROOT/skills/coco" "$H/.claude/skills/brainstorming"
printf 'sentinel\n' > "$H/sentinel"
tree_id "$H" >"$WORK/rb-before"
rb_status=0
HOME="$H" CLAUDE_HOME="$H/.claude" COCO_INSTALL_FAIL_AT="$H/.claude/.coco/manifest.jsonl" \
  bash "$ADAPTER" --core-only --json >"$WORK/rb.json" 2>"$WORK/rb.err" || rb_status=$?
[[ $rb_status -ne 0 ]] || fail "rollback: exit 0"
tree_id "$H" >"$WORK/rb-after"
if ! cmp -s "$WORK/rb-before" "$WORK/rb-after"; then
  diff -u "$WORK/rb-before" "$WORK/rb-after" | head -80 >&2 || true
  fail "rollback: HOME changed"
fi
[[ ! -e "$H/.claude/.coco/install.lock" ]] || fail "rollback: left install.lock"
if grep -q '{"summary":' "$WORK/rb.json"; then
  fail "rollback: emitted a summary"
fi
if grep -q '^Done\.$' "$WORK/rb.err" || grep -q '^Done\.$' "$WORK/rb.json"; then
  fail "rollback: said Done"
fi
echo "ok   mid-apply failure restored HOME"

echo "=== an OSError mid-apply restores HOME byte for byte ==="
if [[ "$(id -u)" -eq 0 ]]; then
  echo "skip (running as root)"
else
H="$WORK/oserr"
mkdir -p "$H/.claude/agents"
chmod 555 "$H/.claude/agents"
trap 'chmod 755 "$WORK/oserr/.claude/agents" 2>/dev/null || true; rm -rf "$WORK"' EXIT
printf 'sentinel\n' > "$H/sentinel"
tree_id "$H" >"$WORK/os-before"
os_status=0
HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --json >"$WORK/os.json" 2>"$WORK/os.err" || os_status=$?
[[ $os_status -eq 1 ]] || fail "oserror: exit $os_status"
tree_id "$H" >"$WORK/os-after"
if ! cmp -s "$WORK/os-before" "$WORK/os-after"; then
  diff -u "$WORK/os-before" "$WORK/os-after" | head -80 >&2 || true
  fail "oserror: HOME changed"
fi
[[ ! -e "$H/.claude/.coco/install.lock" ]] || fail "oserror: left install.lock"
if grep -q '{"summary":' "$WORK/os.json"; then
  fail "oserror: emitted a summary"
fi
if grep -q '^Done\.$' "$WORK/os.err" || grep -q '^Done\.$' "$WORK/os.json"; then
  fail "oserror: said Done"
fi
if grep -q 'Traceback' "$WORK/os.err"; then
  fail "oserror: traceback instead of one line"
fi
grep -q 'Permission denied' "$WORK/os.err" || fail "oserror: missing error line"
chmod 755 "$H/.claude/agents"
trap 'rm -rf "$WORK"' EXIT
echo "ok   OSError mid-apply restored HOME"
fi

echo "=== a symlinked CLAUDE.md rolls back to the link and the original bytes ==="
H="$WORK/linkrb"
mkdir -p "$H/.claude/dot"
printf 'original rules\n' > "$H/.claude/dot/CLAUDE.md"
ln -s "$H/.claude/dot/CLAUDE.md" "$H/.claude/CLAUDE.md"
cp "$H/.claude/dot/CLAUDE.md" "$WORK/linkrb-bytes"
tree_id "$H" >"$WORK/linkrb-before"
link_status=0
HOME="$H" CLAUDE_HOME="$H/.claude" COCO_INSTALL_FAIL_AT="$H/.claude/.coco/manifest.jsonl" \
  bash "$ADAPTER" --core-only >"$WORK/linkrb.out" 2>"$WORK/linkrb.err" || link_status=$?
[[ $link_status -eq 1 ]] || fail "link rollback: exit $link_status"
grep -F "Wrote rules block to $H/.claude/CLAUDE.md" "$WORK/linkrb.out" "$WORK/linkrb.err" >/dev/null \
  || fail "link rollback: block write did not happen"
[[ -L "$H/.claude/CLAUDE.md" && "$(readlink "$H/.claude/CLAUDE.md")" == "$H/.claude/dot/CLAUDE.md" ]] \
  || fail "link rollback: CLAUDE.md is no longer that symlink"
cmp -s "$H/.claude/dot/CLAUDE.md" "$WORK/linkrb-bytes" || fail "link rollback: dot bytes changed"
tree_id "$H" >"$WORK/linkrb-after"
if ! cmp -s "$WORK/linkrb-before" "$WORK/linkrb-after"; then
  diff -u "$WORK/linkrb-before" "$WORK/linkrb-after" | head -40 >&2 || true
  fail "link rollback: HOME changed"
fi
if grep -q '^Done\.$' "$WORK/linkrb.err" || grep -q '^Done\.$' "$WORK/linkrb.out"; then
  fail "link rollback: said Done"
fi
echo "ok   symlinked CLAUDE.md rolled back to the link and original bytes"

echo "=== a dangling symlink outside the repo is left in place ==="
H="$WORK/dangling"
mkdir -p "$H/.claude/skills"
ln -s "$H/no-such-skill" "$H/.claude/skills/brainstorming"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --json >"$WORK/dang.json" 2>"$WORK/dang.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/dang.err" >&2
  fail "dangling user link install exited non-zero"
fi
[[ "$(readlink "$H/.claude/skills/brainstorming")" == "$H/no-such-skill" ]] || fail "dangling user link was replaced"
python3 - "$WORK/dang.json" "$H/.claude/skills/brainstorming" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
hit = [o for o in rows if o.get("path") == sys.argv[2]]
if len(hit) != 1 or hit[0].get("op") != "skip" or hit[0].get("reason") != "user link, not replaced":
    sys.exit("dangling skip: %s" % hit)
print("ok   dangling user link was skipped")
PY

echo "=== the adapter runs under /bin/bash ==="
if [[ -x /bin/bash ]]; then
  H="$WORK/bash32dry"
  mkdir -p "$H"
  if ! HOME="$H" CLAUDE_HOME="$H/.claude" /bin/bash "$ADAPTER" --core-only --dry-run --json >"$WORK/b32.json" 2>"$WORK/b32.err"; then
    echo "bash 3.2 dry-run stderr:" >&2
    cat "$WORK/b32.err" >&2
    fail "bash 3.2 dry-run failed"
  fi
  H="$WORK/bash32real"
  mkdir -p "$H"
  if ! HOME="$H" CLAUDE_HOME="$H/.claude" /bin/bash "$ADAPTER" --core-only >"$WORK/b32real.out" 2>"$WORK/b32real.err"; then
    echo "bash 3.2 install stderr:" >&2
    tail -30 "$WORK/b32real.err" >&2
    fail "bash 3.2 install failed"
  fi
  echo "ok   adapter runs under /bin/bash"
else
  echo "skip /bin/bash is missing"
fi

# Dry-run paths vs the files a real install creates or changes.
# allow is an unchanged symlink the plan lists; its bytes live at another path.
assert_plan_equals() {
  snap_tree "$1" "$WORK/plan-equals-after.json"
  python3 - "$2" "$3" "$4" "${5:-}" "$WORK/plan-equals-after.json" <<'PY'
import json, sys
before_path, plan_path, real_path, allow, after_path = sys.argv[1:6]
before = json.load(open(before_path, encoding="utf-8"))
after = json.load(open(after_path, encoding="utf-8"))

def paths(file):
    out, skips = [], []
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
real, _real_skips = paths(real_path)
if len(plan) != len(set(plan)):
    sys.exit("dry-run plan has duplicate paths")
if set(plan) != set(real):
    sys.exit("dry-run paths differ from the real manifest:\n" + "\n".join(sorted(set(plan) ^ set(real))[:40]))
adjusted = set(plan)
if allow:
    if allow not in adjusted:
        sys.exit("plan is missing %s" % allow)
    if before.get(allow) != after.get(allow):
        sys.exit("allowed path changed: %s" % allow)
    adjusted.discard(allow)
if adjusted != changed:
    only_plan = sorted(adjusted - changed)[:40]
    only_disk = sorted(changed - adjusted)[:40]
    sys.exit("plan paths != created or changed paths\nplan only:\n" + "\n".join(only_plan) + "\ndisk only:\n" + "\n".join(only_disk))
for p in plan_skips:
    if p in changed:
        sys.exit("skip path was changed: %s" % p)
print("ok   plan paths match the install diff")
PY
}

echo "=== a CLAUDE.md symlink outside the target is not touched ==="
H="$WORK/outlink"
OUT="$WORK/outlink-target"
mkdir -p "$H/.claude" "$OUT"
printf 'outside rules\n' > "$OUT/CLAUDE.md"
cp "$OUT/CLAUDE.md" "$WORK/outlink-bytes"
ln -s "$OUT/CLAUDE.md" "$H/.claude/CLAUDE.md"
snap_tree "$H" "$WORK/outlink-before.json"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --dry-run --json >"$WORK/outlink-plan.json" 2>"$WORK/outlink-plan.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/outlink-plan.err" >&2
  fail "outside link dry-run exited non-zero"
fi
cmp -s "$OUT/CLAUDE.md" "$WORK/outlink-bytes" || fail "outside link dry-run changed the target file"
[[ ! -e "$OUT/CLAUDE.md.coco-bak" ]] || fail "outside link dry-run created a coco-bak"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --json >"$WORK/outlink.json" 2>"$WORK/outlink.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/outlink.err" >&2
  fail "outside link install exited non-zero"
fi
cmp -s "$OUT/CLAUDE.md" "$WORK/outlink-bytes" || fail "outside link target bytes changed"
[[ ! -e "$OUT/CLAUDE.md.coco-bak" ]] || fail "outside link target coco-bak exists"
[[ ! -e "$H/.claude/CLAUDE.md.coco-bak" ]] || fail "outside link wrote CLAUDE.md.coco-bak"
[[ ! -e "$H/.claude/.coco/backup/CLAUDE.md" ]] || fail "outside link wrote a CLAUDE.md backup"
[[ -L "$H/.claude/CLAUDE.md" && "$(readlink "$H/.claude/CLAUDE.md")" == "$OUT/CLAUDE.md" ]] || fail "outside link was replaced"
[[ -L "$H/.claude/skills/brainstorming" ]] || fail "outside link: rest of install did not run"
grep -F -x "Skip: $H/.claude/CLAUDE.md (CLAUDE.md links outside the target; rules block not added)" "$WORK/outlink.err" || fail "outside link: human note missing"
python3 - "$WORK/outlink.json" "$H/.claude/CLAUDE.md" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
claude = sys.argv[2]
blocks = [o for o in rows if o.get("op") == "block"]
if blocks:
    sys.exit("outside link recorded a block: %s" % blocks)
hit = [o for o in rows if o.get("path") == claude]
if len(hit) != 1 or hit[0].get("op") != "skip" or hit[0].get("reason") != "CLAUDE.md links outside the target; rules block not added":
    sys.exit("outside link skip: %s" % hit)
baks = [o for o in rows if "CLAUDE.md" in o.get("path", "") and o.get("op") != "skip"]
if baks:
    sys.exit("outside link planned a CLAUDE.md write: %s" % baks)
print("ok   outside CLAUDE.md link was skipped")
PY
assert_plan_equals "$H" "$WORK/outlink-before.json" "$WORK/outlink-plan.json" "$WORK/outlink.json"

echo "=== a dangling CLAUDE.md symlink is not touched ==="
H="$WORK/dangmd"
mkdir -p "$H/.claude" "$WORK/nowhere"
ln -s "$WORK/nowhere/CLAUDE.md" "$H/.claude/CLAUDE.md"
snap_tree "$H" "$WORK/dangmd-before.json"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --dry-run --json >"$WORK/dangmd-plan.json" 2>"$WORK/dangmd-plan.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/dangmd-plan.err" >&2
  fail "dangling CLAUDE.md dry-run exited non-zero"
fi
[[ ! -e "$WORK/nowhere/CLAUDE.md" ]] || fail "dangling CLAUDE.md dry-run created the target"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --json >"$WORK/dangmd.json" 2>"$WORK/dangmd.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/dangmd.err" >&2
  fail "dangling CLAUDE.md install exited non-zero"
fi
[[ ! -e "$WORK/nowhere/CLAUDE.md" ]] || fail "dangling CLAUDE.md created the target"
[[ ! -e "$WORK/nowhere/CLAUDE.md.coco-bak" ]] || fail "dangling CLAUDE.md created a coco-bak"
[[ ! -e "$H/.claude/CLAUDE.md.coco-bak" ]] || fail "dangling CLAUDE.md wrote CLAUDE.md.coco-bak"
[[ ! -e "$H/.claude/.coco/backup/CLAUDE.md" ]] || fail "dangling CLAUDE.md wrote a backup"
[[ -L "$H/.claude/CLAUDE.md" && "$(readlink "$H/.claude/CLAUDE.md")" == "$WORK/nowhere/CLAUDE.md" ]] || fail "dangling CLAUDE.md link changed"
grep -F -x "Skip: $H/.claude/CLAUDE.md (CLAUDE.md is a dangling link; rules block not added)" "$WORK/dangmd.err" || fail "dangling CLAUDE.md: human note missing"
python3 - "$WORK/dangmd.json" "$H/.claude/CLAUDE.md" <<'PY'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
claude = sys.argv[2]
if any(o.get("op") == "block" for o in rows):
    sys.exit("dangling CLAUDE.md recorded a block")
hit = [o for o in rows if o.get("path") == claude]
if len(hit) != 1 or hit[0].get("op") != "skip" or hit[0].get("reason") != "CLAUDE.md is a dangling link; rules block not added":
    sys.exit("dangling CLAUDE.md skip: %s" % hit)
print("ok   dangling CLAUDE.md link was skipped")
PY
assert_plan_equals "$H" "$WORK/dangmd-before.json" "$WORK/dangmd-plan.json" "$WORK/dangmd.json"

echo "=== a CLAUDE.md symlink inside the target keeps the link and a pristine backup ==="
H="$WORK/inlink"
mkdir -p "$H/.claude/dot"
printf 'original rules\n' > "$H/.claude/dot/CLAUDE.md"
ln -s "$H/.claude/dot/CLAUDE.md" "$H/.claude/CLAUDE.md"
cp "$H/.claude/dot/CLAUDE.md" "$WORK/inlink-bytes"
snap_tree "$H" "$WORK/inlink-before.json"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --dry-run --json >"$WORK/inlink-plan.json" 2>"$WORK/inlink-plan.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/inlink-plan.err" >&2
  fail "inside link dry-run exited non-zero"
fi
cmp -s "$H/.claude/dot/CLAUDE.md" "$WORK/inlink-bytes" || fail "inside link dry-run changed the resolved file"
[[ -L "$H/.claude/CLAUDE.md" ]] || fail "inside link dry-run replaced the symlink"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only --json >"$WORK/inlink.json" 2>"$WORK/inlink.err"; then
  echo "installer failed; stderr tail:" >&2
  tail -30 "$WORK/inlink.err" >&2
  fail "inside link install exited non-zero"
fi
[[ -L "$H/.claude/CLAUDE.md" && "$(readlink "$H/.claude/CLAUDE.md")" == "$H/.claude/dot/CLAUDE.md" ]] || fail "inside link is no longer that symlink"
cmp -s "$H/.claude/.coco/backup/CLAUDE.md" "$WORK/inlink-bytes" || fail "inside link backup is not the original bytes"
[[ ! -e "$H/.claude/.coco/backup/dot/CLAUDE.md" ]] || fail "inside link backed up under the resolved relative path"
grep -q "coco:rules-start" "$H/.claude/dot/CLAUDE.md" || fail "inside link did not write through to the resolved file"
python3 - "$WORK/inlink.json" "$H/.claude/CLAUDE.md" "$H/.claude/dot/CLAUDE.md" <<'PY'
import json, os, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
claude, resolved = sys.argv[2:]
resolved = os.path.realpath(resolved)
paths = [o.get("path") for o in rows if o.get("op") in ("link", "write", "block")]
# Plan path is spelled under the target; realpath may be /private/var on macOS.
listed = [p for p in paths if p != claude and os.path.realpath(p) == resolved]
if claude not in paths or not listed:
    sys.exit("plan must list CLAUDE.md and the resolved file")
block = [o for o in rows if o.get("op") == "block" and o.get("path") == claude]
if len(block) != 1:
    sys.exit("inside link block: %s" % block)
rec = block[0]
if rec.get("created") is not False or rec.get("replaced_link") is not None or "replaced_link" not in rec:
    sys.exit("inside link block fields: %s" % rec)
if rec.get("link_target") != resolved:
    sys.exit("link_target %r != %r" % (rec.get("link_target"), resolved))
bak = os.path.join(os.path.dirname(claude), ".coco", "backup", "CLAUDE.md")
if rec.get("backup") != bak:
    sys.exit("backup %r != %r" % (rec.get("backup"), bak))
print("ok   inside CLAUDE.md link kept, backup is the original")
PY
check_jsonl "$WORK/inlink.json" "$H/.claude" install
assert_plan_equals "$H" "$WORK/inlink-before.json" "$WORK/inlink-plan.json" "$WORK/inlink.json" "$H/.claude/CLAUDE.md"
cp "$H/.claude/.coco/backup/CLAUDE.md" "$WORK/inlink-bak"
printf 'APPENDED\n' >> "$H/.claude/dot/CLAUDE.md"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ADAPTER" --core-only >/dev/null 2>"$WORK/inlink-again.err"; then
  fail "inside link re-install exited non-zero"
fi
cmp -s "$H/.claude/.coco/backup/CLAUDE.md" "$WORK/inlink-bak" || fail "inside link re-install overwrote the pristine backup"
[[ -L "$H/.claude/CLAUDE.md" ]] || fail "inside link re-install replaced the symlink"

echo "PASS: install safety"
