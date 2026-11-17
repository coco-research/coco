#!/usr/bin/env bash
# Gate: pack picker prompt, non-TTY/--yes/--packs/--all flags, replica exclusion,
# and per-pack --uninstall removal list. Runs hermetically in a temp HOME + TMPDIR.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REAL_GIT="$(command -v git)"
BASH_UNDER_TEST="${BASH:-/bin/bash}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/tmp" "$WORK/no-managed" "$WORK/bin"

fail() { echo "FAIL: $*" >&2; exit 1; }
snap() { (cd "$1" && find . -print | LC_ALL=C sort); }

cat > "$WORK/bin/git" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
export COPYFILE_DISABLE=1
if [ "${1:-}" = "clone" ]; then
  for arg in "$@"; do dest="$arg"; done
  mkdir -p "$dest"
  ( cd "$COCO_ROOT" && "$REAL_GIT" ls-files -z | tar --null -T - -cf - ) | ( cd "$dest" && tar -xf - )
  "$REAL_GIT" init -q "$dest"
  exit 0
fi
exec "$REAL_GIT" "$@"
EOS
chmod +x "$WORK/bin/git"

run_env() {
  local h="$1"; shift
  mkdir -p "$h"
  env -i PATH="$WORK/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin" \
    HOME="$h" TMPDIR="$WORK/tmp" CLAUDE_HOME="$h/.claude" \
    PYTHONDONTWRITEBYTECODE=1 COCO_NO_UPDATE_CHECK=1 \
    COCO_MANAGED_ROOT="$WORK/no-managed" REAL_GIT="$REAL_GIT" COCO_ROOT="$ROOT" "$@"
}

run_pty() {
  local h="$1" input="$2" out="$3"; shift 3
  run_env "$h" python3 - "$input" "$out" "$@" <<'PY'
import os, pty, select, subprocess, sys, time
inp, out_path, cmd = sys.argv[1], sys.argv[2], sys.argv[3:]
master, slave = pty.openpty()
proc = subprocess.Popen(cmd, stdin=slave, stdout=slave, stderr=slave, close_fds=True)
os.close(slave)
sent, buf, deadline = False, bytearray(), time.monotonic() + 30.0
while True:
    if inp and not sent and (b"[Y/n]" in buf or proc.poll() is not None):
        os.write(master, inp.encode("utf-8"))
        sent = True
    r, _, _ = select.select([master], [], [], 0.05)
    if r:
        try: chunk = os.read(master, 4096)
        except OSError: chunk = b""
        if chunk: buf.extend(chunk)
        elif proc.poll() is not None: break
    elif proc.poll() is not None:
        break
    if time.monotonic() > deadline:
        proc.kill(); os.close(master); sys.exit(124)
os.close(master)
open(out_path, "wb").write(bytes(buf).replace(b"\r\n", b"\n"))
sys.exit(proc.wait())
PY
}

EXPECTED_MOCK="Packs: [x] core [x] gsd [x] brain [x] cognee [x] hyperframes [x] si [x] m0 [ ] reverse-skill · Install 7 packs? [Y/n]"

run_env "$WORK/base" "$BASH_UNDER_TEST" "$ROOT/adapters/claude-code/install.sh" >/dev/null 2>&1
snap "$WORK/base" > "$WORK/base.list"

echo "=== (a) interactive PTY via npx/coco.js shows mock, asks 1 [Y/n], matches baseline ==="
mkdir -p "$WORK/npx-cwd"
( cd "$WORK/npx-cwd" && run_pty "$WORK/pty-def" $'y\n' "$WORK/pty-def.out" node "$ROOT/bin/coco.js" --adapter claude-code )
grep -Fq "$EXPECTED_MOCK" "$WORK/pty-def.out" || { tail -20 "$WORK/pty-def.out" >&2; fail "missing mock picker line"; }
[[ "$(grep -Fc '[Y/n]' "$WORK/pty-def.out")" -eq 1 ]] || fail "expected 1 prompt"
cmp -s "$WORK/base.list" <(snap "$WORK/pty-def") || fail "PTY default file list differs from baseline"

if run_pty "$WORK/pty-no" $'n\n' "$WORK/pty-no.out" "$BASH_UNDER_TEST" "$ROOT/install.sh" --adapter claude-code; then
  fail "answering n at [Y/n] should exit non-zero"
fi
[[ ! -e "$WORK/pty-no/.claude" ]] || fail "answering n created .claude"

echo "=== (b) --packs gsd installs only core + gsd; --all includes reverse-skill; replica excluded ==="
run_env "$WORK/gsd-ref" "$BASH_UNDER_TEST" "$ROOT/adapters/claude-code/install.sh" --systems gsd >/dev/null 2>&1
run_pty "$WORK/pty-gsd" "" "$WORK/pty-gsd.out" "$BASH_UNDER_TEST" "$ROOT/install.sh" --adapter claude-code --packs gsd
grep -Fq '[Y/n]' "$WORK/pty-gsd.out" && fail "--packs prompted on TTY"
cmp -s <(snap "$WORK/gsd-ref") <(snap "$WORK/pty-gsd") || fail "--packs gsd != core + gsd"
[[ -L "$WORK/pty-gsd/.claude/get-shit-done" && -L "$WORK/pty-gsd/.claude/skills/brainstorming" ]] || fail "missing core or gsd"
[[ ! -e "$WORK/pty-gsd/.claude/commands/SI.md" && ! -e "$WORK/pty-gsd/.claude/skills/m0" ]] || fail "unexpected pack installed"

run_pty "$WORK/pty-all" "" "$WORK/pty-all.out" "$BASH_UNDER_TEST" "$ROOT/install.sh" --adapter claude-code --all
grep -Fq '[Y/n]' "$WORK/pty-all.out" && fail "--all prompted on TTY"
[[ -L "$WORK/pty-all/.claude/skills/apk-reverse" ]] || fail "--all missed reverse-skill"

FAKE="$WORK/fake-repo"
mkdir -p "$FAKE/scripts" "$FAKE/systems/replica" "$FAKE/systems/demo-opt"
cp "$ROOT/scripts/installable-bundles.sh" "$FAKE/scripts/installable-bundles.sh"
for p in "$ROOT"/systems/*/pack.json; do d="$(basename "$(dirname "$p")")"; mkdir -p "$FAKE/systems/$d"; cp "$p" "$FAKE/systems/$d/"; done
printf '{"name":"replica","title":"Replica","summary":"Excluded","kind":"ours","licence":"MIT"}\n' > "$FAKE/systems/replica/pack.json"
printf '{"name":"demo-opt","title":"Demo","summary":"Optional","kind":"ours","licence":"MIT","explicit_only":true}\n' > "$FAKE/systems/demo-opt/pack.json"
LINE="$("$BASH_UNDER_TEST" "$FAKE/scripts/installable-bundles.sh" --picker-line)"
[[ "$LINE" == *"[ ] demo-opt"* && "$LINE" != *"replica"* ]] || fail "pack.json/replica check failed: $LINE"
"$BASH_UNDER_TEST" "$FAKE/scripts/installable-bundles.sh" --resolve-install replica >/dev/null 2>&1 && fail "replica accepted" || true

echo "=== (c) --yes and no-TTY never prompt ==="
run_pty "$WORK/pty-yes" "" "$WORK/pty-yes.out" "$BASH_UNDER_TEST" "$ROOT/install.sh" --adapter claude-code --yes
grep -Fq '[Y/n]' "$WORK/pty-yes.out" && fail "--yes prompted on TTY"
cmp -s "$WORK/base.list" <(snap "$WORK/pty-yes") || fail "--yes != baseline"

run_env "$WORK/notty" "$BASH_UNDER_TEST" "$ROOT/install.sh" --adapter claude-code < /dev/null > "$WORK/notty.out" 2>&1
grep -Fq '[Y/n]' "$WORK/notty.out" && fail "no-TTY prompted"
cmp -s "$WORK/base.list" <(snap "$WORK/notty") || fail "no-TTY != baseline"

echo "=== (d) --uninstall --packs x prints removal list BEFORE removing, matching exact removed files ==="
UHOME="$WORK/uninst"
run_env "$UHOME" "$BASH_UNDER_TEST" "$ROOT/install.sh" --adapter claude-code --yes >/dev/null 2>&1
snap "$UHOME" > "$WORK/u0.list"

run_env "$UHOME" COCO_INSTALL_TEST_HOOKS=1 COCO_INSTALL_FAIL_AT="$UHOME/.claude/get-shit-done" \
  "$BASH_UNDER_TEST" "$ROOT/install.sh" --adapter claude-code --uninstall --packs gsd > "$WORK/u-abort.out" 2>&1 && fail "expected abort" || true
grep -Fq "Remove: $UHOME/.claude/get-shit-done" "$WORK/u-abort.out" || fail "not printed before removing"
cmp -s "$WORK/u0.list" <(snap "$UHOME") || fail "aborted uninstall modified tree"

run_env "$UHOME" node "$ROOT/bin/coco.js" --uninstall --packs gsd > "$WORK/u-gsd.out" 2>&1
snap "$UHOME" > "$WORK/u1.list"
sed -n "s|^Remove: $UHOME/|./|p" "$WORK/u-gsd.out" | LC_ALL=C sort > "$WORK/u-gsd.printed"
[[ -s "$WORK/u-gsd.printed" ]] && cmp -s "$WORK/u-gsd.printed" <(comm -23 "$WORK/u0.list" "$WORK/u1.list") || fail "gsd printed != removed"

run_env "$UHOME" "$BASH_UNDER_TEST" "$ROOT/install.sh" --uninstall --packs si > "$WORK/u-si.out" 2>&1
snap "$UHOME" > "$WORK/u2.list"
sed -n "s|^Remove: $UHOME/|./|p" "$WORK/u-si.out" | LC_ALL=C sort > "$WORK/u-si.printed"
[[ -s "$WORK/u-si.printed" ]] && cmp -s "$WORK/u-si.printed" <(comm -23 "$WORK/u1.list" "$WORK/u2.list") || fail "si printed != removed"
[[ ! -e "$UHOME/.claude/commands/SI.md" && -L "$UHOME/.claude/skills/brainstorming" && -L "$UHOME/.claude/skills/m0" ]] || fail "post-uninstall state wrong"

echo "PASS: pack picker checks passed ($BASH_UNDER_TEST)"
