#!/usr/bin/env bash
# Packed bin -> fake clone -> Claude Code install -> uninstall. No network.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REAL_GIT="$(command -v git)"
[ -n "$REAL_GIT" ] || { echo "FAIL: git not on PATH" >&2; exit 1; }

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

mkdir -p "$T/pack" "$T/extract" "$T/home" "$T/cwd" "$T/bin" "$T/no-hooks" "$T/npm-cache"

# adapters/claude-code/install.sh and the root install.sh take flags only.
# Neither reads a prompt, so stdin is /dev/null and no skip-prompt flag is passed.
cat > "$T/bin/git" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
export COPYFILE_DISABLE=1
if [ "${1:-}" = "clone" ]; then
  dest=""
  for arg in "$@"; do dest="$arg"; done
  [ -n "$dest" ]
  mkdir -p "$dest"
  # Tracked files of this checkout (real git ls-files), then a plain git init.
  ( cd "$COCO_ROOT" && "$REAL_GIT" ls-files -z | tar --null -T - -cf - ) | ( cd "$dest" && tar -xf - )
  "$REAL_GIT" init -q "$dest"
  exit 0
fi
exec "$REAL_GIT" "$@"
EOS
chmod +x "$T/bin/git"

# A private cache: npm pack stays offline and does not read ~/.npm.
if ! ( cd "$T/pack" && npm pack "$ROOT" --ignore-scripts --offline --cache "$T/npm-cache" >"$T/npm-pack.log" 2>&1 ); then
  cat "$T/npm-pack.log" >&2
  fail "npm pack failed"
fi
tarball=("$T/pack"/*.tgz)
[ -f "${tarball[0]}" ] || fail "npm pack produced no tarball"
tar -xzf "${tarball[0]}" -C "$T/extract"
BIN="$T/extract/package/bin/coco.js"
[ -f "$BIN" ] || fail "packed bin missing at $BIN"

run_cli() {
  env \
    REAL_GIT="$REAL_GIT" \
    COCO_ROOT="$ROOT" \
    HOME="$T/home" \
    COCO_NO_UPDATE_CHECK=1 \
    PATH="$T/bin:$PATH" \
    "$@"
}

if ! ( cd "$T/cwd" && run_cli node "$BIN" install --adapter claude-code < /dev/null >"$T/install.out" 2>"$T/install.err" ); then
  tail -40 "$T/install.err" >&2 || true
  tail -20 "$T/install.out" >&2 || true
  fail "install exited non-zero"
fi

python3 - "$T/install.out" "$ROOT/docs/delivered-counts.json" <<'PY'
import json, re, sys
text = open(sys.argv[1], encoding="utf-8").read()
want = json.load(open(sys.argv[2], encoding="utf-8"))
m = re.search(
    r"Installed for Claude Code:\n"
    r"  Slash commands : (\d+).*\n"
    r"  Skills\s+: (\d+)\n"
    r"  Subagents\s+: (\d+)\n",
    text,
)
if not m:
    sys.stderr.write("FAIL: install output has no Claude Code receipt\n")
    sys.exit(1)
got = {"commands": int(m.group(1)), "skills": int(m.group(2)), "agents": int(m.group(3))}
keys = ("skills", "commands", "agents")
if any(got[k] != want[k] for k in keys):
    sys.stderr.write(
        "FAIL: receipt counts %s != docs/delivered-counts.json %s\n"
        % (
            " ".join("%s=%s" % (k, got[k]) for k in keys),
            " ".join("%s=%s" % (k, want[k]) for k in keys),
        )
    )
    sys.exit(1)
PY

# adapters/claude-code/install.sh sets TARGET_HOME=${CLAUDE_HOME:-$HOME/.claude}.
# Generated commands are written under that home's commands/ directory.
si="$T/home/.claude/commands/SI-Decide.md"
[ -s "$si" ] || fail "expected non-empty $si"

clone="$(cd "$T/cwd/coco" && pwd)"
clone_p="$(cd "$T/cwd/coco" && pwd -P)"

# The fake clone is only copied files plus git init: no origin, and every file
# uncommitted. uninstall refuses that (cloneRejection, then localWork) before
# it removes symlinks. Record the official origin and one commit that the
# remote ref also has, with hooks and signing off, so the sweep runs.
"$REAL_GIT" -C "$clone" remote add origin https://github.com/coco-research/coco.git
"$REAL_GIT" -C "$clone" add -A
"$REAL_GIT" -C "$clone" \
  -c user.name=e2e \
  -c user.email=e2e@example.com \
  -c commit.gpgsign=false \
  -c core.hooksPath="$T/no-hooks" \
  commit -qm settled
"$REAL_GIT" -C "$clone" update-ref refs/remotes/origin/main HEAD

if ! run_cli node "$BIN" uninstall "$clone" < /dev/null >"$T/uninst.out" 2>"$T/uninst.err"; then
  tail -30 "$T/uninst.err" >&2 || true
  fail "uninstall exited non-zero"
fi

python3 - "$T/home" "$clone" "$clone_p" <<'PY'
import os, sys
home = sys.argv[1]
roots = [os.path.normpath(p) for p in sys.argv[2:]]
base = os.path.join(home, ".claude")
bad = []

def inside(path):
    path = os.path.normpath(path)
    return any(path == root or path.startswith(root + os.sep) for root in roots)

def walk(directory):
    try:
        names = os.listdir(directory)
    except OSError:
        return
    for name in names:
        path = os.path.join(directory, name)
        if os.path.islink(path):
            target = os.path.normpath(os.path.join(os.path.dirname(path), os.readlink(path)))
            if inside(target):
                bad.append(path + " -> " + target)
        elif os.path.isdir(path):
            walk(path)

if os.path.isdir(base):
    walk(base)
if bad:
    sys.stderr.write("FAIL: symlink under HOME/.claude still points into the clone\n")
    sys.stderr.write("\n".join(bad) + "\n")
    sys.exit(1)
PY

echo "PASS: npx claude-code install and uninstall"
