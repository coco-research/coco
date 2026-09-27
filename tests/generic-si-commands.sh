#!/usr/bin/env bash
# Issue #242: a clean-machine generic/codex first run must ship the Super
# Intelligence command family and the 13 team front doors, not just the bundles.
# Before the fix it listed 175 skills, 0 /SI-* commands, 0 front doors.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# Keep the host's own adapter homes out of the runs; HOME is the only path input.
CLEAN=(env -u CLAUDE_HOME -u CURSOR_HOME -u COCO_HOME -u XDG_CONFIG_HOME)
fail() { echo "FAIL: $1"; exit 1; }

# --- Case 1: clean-HOME default first run -----------------------------------
mkdir -p "$tmp/p1" "$tmp/h1"
if ! (cd "$tmp/p1" && "${CLEAN[@]}" HOME="$tmp/h1" bash "$ROOT/install.sh" \
    --adapter generic >"$tmp/log1" 2>&1); then
  fail "clean-HOME default: install.sh exited non-zero; log: $tmp/log1"
fi

agents="$tmp/p1/AGENTS.md"
si_dir="$tmp/h1/.coco/si-commands"
[[ -f "$agents" ]] || fail "clean-HOME default: $agents was not written"

si_listed=$(awk '/^## Super Intelligence Commands$/{f=1;next} /^## /{f=0} f' "$agents" \
  | grep -c '^- `/SI' || true)
[[ "$si_listed" -ge 1 ]] || fail "clean-HOME default: no /SI- commands listed in the Super Intelligence Commands section"

[[ -f "$si_dir/SI.md" ]] || fail "clean-HOME default: $si_dir/SI.md missing"
compgen -G "$si_dir/SI-*.md" >/dev/null || fail "clean-HOME default: no SI-*.md files in $si_dir"

while IFS= read -r cmd; do
  [[ -n "$cmd" ]] || continue
  [[ -f "$si_dir/${cmd#/}.md" ]] || fail "clean-HOME default: listed command $cmd has no file in $si_dir"
done < <(awk '/^## Super Intelligence Commands$/{f=1;next} /^## /{f=0} f' "$agents" \
  | sed -n 's/^- `\(\/SI[^`]*\)`.*/\1/p')

doors=$(grep -c '^- \*\*[a-z-]*-super-intelligence\*\*' "$agents" || true)
[[ "$doors" -eq 13 ]] || fail "clean-HOME default: expected 13 *-super-intelligence front doors, found $doors"

grep -Eq 'SI commands[[:space:]]*: [1-9][0-9]*' "$tmp/log1" \
  || fail "clean-HOME default: receipt does not report a non-zero SI command count"

# --- Case 2: --core-only must not generate or list the family ----------------
mkdir -p "$tmp/p2" "$tmp/h2"
if ! (cd "$tmp/p2" && "${CLEAN[@]}" HOME="$tmp/h2" bash "$ROOT/install.sh" \
    --adapter generic --core-only >"$tmp/log2" 2>&1); then
  fail "core-only: install.sh exited non-zero; log: $tmp/log2"
fi

[[ -e "$tmp/h2/.coco/si-commands" ]] && fail "core-only: created $tmp/h2/.coco/si-commands"
agents2="$tmp/p2/AGENTS.md"
[[ -f "$agents2" ]] || fail "core-only: $agents2 was not written"
if grep -q '^- `/SI' "$agents2"; then
  fail "core-only: AGENTS.md lists /SI- command lines"
fi
if ! awk '/^## Super Intelligence Commands$/{f=1;next} /^## /{f=0} f' "$agents2" \
    | grep -q 'Not generated:'; then
  fail "core-only: SI section does not say it was not generated"
fi

# --- Case 3: --dry-run writes nothing ----------------------------------------
mkdir -p "$tmp/p3" "$tmp/h3"
if ! (cd "$tmp/p3" && "${CLEAN[@]}" HOME="$tmp/h3" bash "$ROOT/install.sh" \
    --adapter generic --dry-run >"$tmp/log3" 2>&1); then
  fail "dry-run: install.sh exited non-zero; log: $tmp/log3"
fi

[[ -e "$tmp/h3/.coco" ]] && fail "dry-run: wrote $tmp/h3/.coco"
[[ -f "$tmp/p3/AGENTS.md" ]] && fail "dry-run: wrote $tmp/p3/AGENTS.md"

echo "PASS: generic first-run install ships the SI command family and front doors"
