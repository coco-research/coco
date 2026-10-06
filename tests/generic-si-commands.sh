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

# --- Case 4: HOME path containing a space must not split command paths -------
mkdir -p "$tmp/p4" "$tmp/h4 space"
if ! (cd "$tmp/p4" && "${CLEAN[@]}" HOME="$tmp/h4 space" bash "$ROOT/install.sh" \
    --adapter generic >"$tmp/log4" 2>&1); then
  fail "spaced HOME: install.sh exited non-zero; log: $tmp/log4"
fi

agents4="$tmp/p4/AGENTS.md"
si_dir4="$tmp/h4 space/.coco/si-commands"
[[ -f "$agents4" ]] || fail "spaced HOME: $agents4 was not written"
[[ -d "$si_dir4" ]] || fail "spaced HOME: SI directory $si_dir4 missing"

si_listed4=$(awk '/^## Super Intelligence Commands$/{f=1;next} /^## /{f=0} f' "$agents4" \
  | grep -c '^- `/SI' || true)
[[ "$si_listed4" -eq 342 ]] \
  || fail "spaced HOME: expected exactly 342 /SI command lines, found $si_listed4"

junk4=$(awk '/^## Super Intelligence Commands$/{f=1;next} /^## /{f=0} f' "$agents4" \
  | grep '^- `' | grep -v '^- `/SI' || true)
[[ -z "$junk4" ]] || fail "spaced HOME: junk line in SI section: $junk4"

while IFS= read -r cmd4; do
  [[ -n "$cmd4" ]] || continue
  [[ -f "$si_dir4/${cmd4#/}.md" ]] \
    || fail "spaced HOME: listed command $cmd4 has no file in $si_dir4"
done < <(awk '/^## Super Intelligence Commands$/{f=1;next} /^## /{f=0} f' "$agents4" \
  | sed -n 's/^- `\(\/SI[^`]*\)`.*/\1/p')

# --- Case 5: a failing SI generator is reported, cleaned up, and non-fatal ---
brokencopy="$tmp/repo-broken"
cp -R "$ROOT" "$brokencopy"
cat >"$brokencopy/scripts/generate-si-commands.sh" <<'BROKEN'
#!/usr/bin/env bash
# Test stub: fails after creating the target dir, like a broken generator.
target=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) shift; target="${1:-}" ;;
  esac
  shift || true
done
[[ -n "$target" ]] && mkdir -p "$target"
echo "BROKEN GENERATOR: simulated failure" >&2
exit 1
BROKEN
chmod +x "$brokencopy/scripts/generate-si-commands.sh"

mkdir -p "$tmp/p5" "$tmp/h5"
if ! (cd "$tmp/p5" && "${CLEAN[@]}" HOME="$tmp/h5" bash "$brokencopy/install.sh" \
    --adapter generic >"$tmp/log5" 2>&1); then
  fail "generator failure: install.sh exited non-zero; log: $tmp/log5"
fi

agents5="$tmp/p5/AGENTS.md"
[[ -f "$agents5" ]] || fail "generator failure: $agents5 was not written"
grep -q 'BROKEN GENERATOR: simulated failure' "$tmp/log5" \
  || fail "generator failure: warning lacks generator output; log: $tmp/log5"
grep -q '^Systems: .*SI commands not generated' "$agents5" \
  || fail "generator failure: Systems header does not report missing SI commands"
grep -q 'SI commands not generated' "$tmp/log5" \
  || fail "generator failure: receipt does not report missing SI commands"
[[ -e "$tmp/h5/.coco/si-commands" ]] \
  && fail "generator failure: left behind $tmp/h5/.coco/si-commands"

echo "PASS: generic first-run install ships the SI command family and front doors"
