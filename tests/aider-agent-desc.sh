#!/usr/bin/env bash
# Aider AGENTS.md must carry each agent's full description (issue #259): the installer
# used to cut it at 120 bytes, mid-word and sometimes mid-UTF-8-character.
# Runs the installer in a temp dir: it writes AGENTS.md into the current directory.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)
tmp=$(mktemp -d)
mkdir -p "$tmp/home"
trap 'rm -rf "$tmp"' EXIT

(cd "$tmp" && HOME="$tmp/home" bash "$ROOT/adapters/aider/install.sh" --systems gsd >/dev/null)

python3 - "$ROOT/agents" "$ROOT/systems/gsd/agents" "$tmp/AGENTS.md" <<'PY'
import pathlib, shlex, subprocess, sys
out = pathlib.Path(sys.argv[3]).read_text(encoding="utf-8")
bad = 0
for d in (sys.argv[1], sys.argv[2]):
    for f in sorted(pathlib.Path(d).glob("*.md")):
        if f.stem in ("INDEX", "README", "PROMPT-DEFENSE"):
            continue
        qf = shlex.quote(str(f))
        cmd = f"grep -m1 '^description:' {qf} 2>/dev/null | sed 's/^description: *\"*//;s/\"*$//' || true"
        desc = subprocess.check_output(cmd, shell=True, text=True).rstrip('\n')
        if not desc:
            print(f"FAIL: {f.stem} has no description")
            bad += 1
            continue
        if f"### {f.stem}\n{desc}\n" not in out:
            print(f"FAIL: {f.stem} description is not in AGENTS.md in full")
            bad += 1
sys.exit(1 if bad else 0)
PY
