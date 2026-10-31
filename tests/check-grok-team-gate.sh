#!/usr/bin/env bash
# Issue #266. On a grok install the /team commands must find their gate scripts:
# team-gate is linked under ~/.grok/skills, the installed commands cite ~/.grok paths
# (a grok-only machine has no ~/.claude), --uninstall removes all of it, and the
# claude-code install of the same commands stays byte-identical to the sources.
# Set COCO_BASE_REF (e.g. origin/main) to also compare the claude-code team commands
# with an install from that ref.
# Run from anywhere: bash tests/check-grok-team-gate.sh
set -euo pipefail

cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0
bad() { echo "FAIL: $1"; fail=1; }
clean_env() { env -u GROK_HOME -u CLAUDE_HOME -u COCO_HOME -u XDG_CONFIG_HOME "$@"; }
mkdir -p "$tmp/grok" "$tmp/claude" "$tmp/base-home"

G="$tmp/grok/.grok"
clean_env HOME="$tmp/grok" bash install.sh --adapter grok >"$tmp/grok.log" 2>&1 \
  || { cat "$tmp/grok.log"; echo "FAIL: grok install exited non-zero"; exit 1; }

HOME="$tmp/grok" python3 "$G/skills/team-gate/scripts/gate_state.py" --help >/dev/null 2>&1 \
  || bad "python3 ~/.grok/skills/team-gate/scripts/gate_state.py --help did not exit 0"

# find -L follows the command symlinks into the clone (BSD grep -R does not).
in_commands() { find -L "$G/commands" -type f -name '*.md' -exec grep "$@" {} + || true; }
left=$(in_commands -lE '~/\.claude/(skills|commands)/')
[[ -z "$left" ]] || bad "installed grok commands still cite ~/.claude/skills/ or ~/.claude/commands/: $left"

cited=$(in_commands -hoE '~/\.grok/(skills|commands)/[A-Za-z0-9_./:-]*[A-Za-z0-9_/-]' | sort -u)
grep -qx '~/.grok/skills/team-gate/scripts/gate_state.py' <<<"$cited" \
  || bad "team:ship does not cite ~/.grok/skills/team-gate/scripts/gate_state.py"
while IFS= read -r p; do
  if [[ -n "$p" && ! -e "$G/${p#\~/.grok/}" ]]; then bad "cited path does not exist: $p"; fi
done <<<"$cited"

clean_env HOME="$tmp/grok" bash adapters/grok/install.sh --uninstall >/dev/null 2>&1 \
  || bad "grok --uninstall exited non-zero"
rest=$(find "$G" ! -type d)
[[ -z "$rest" ]] || bad "grok --uninstall left files behind: $(head -5 <<<"$rest")"

# claude-code reads commands/team as they are: each installed team command must be
# byte-identical to its source.
team_tree() {  # $1 = HOME of a claude-code install; prints "<name> <sha256>" per team command
  local f
  for f in "$1/.claude/commands"/team*.md; do
    printf '%s %s\n' "$(basename "$f")" "$(shasum -a 256 <"$f" | cut -d' ' -f1)"
  done
}
clean_env HOME="$tmp/claude" bash install.sh --adapter claude-code >"$tmp/claude.log" 2>&1 \
  || { cat "$tmp/claude.log"; echo "FAIL: claude-code install exited non-zero"; exit 1; }
want=$(for f in commands/team/*.md; do
  n=$(basename "$f" .md)
  [[ $n == INDEX ]] && continue
  [[ $n == _index ]] && n=team || n="team:$n"
  printf '%s %s\n' "$n.md" "$(shasum -a 256 <"$f" | cut -d' ' -f1)"
done | sort)
[[ "$(team_tree "$tmp/claude" | sort)" == "$want" ]] \
  || bad "claude-code ~/.claude/commands/team* differs from commands/team/"

if [[ -n "${COCO_BASE_REF:-}" ]]; then
  mkdir "$tmp/base"
  git archive "$COCO_BASE_REF" | tar -x -C "$tmp/base"
  clean_env HOME="$tmp/base-home" bash "$tmp/base/install.sh" --adapter claude-code >/dev/null 2>&1 \
    || bad "claude-code install from $COCO_BASE_REF exited non-zero"
  [[ "$(team_tree "$tmp/claude")" == "$(team_tree "$tmp/base-home")" ]] \
    || bad "claude-code ~/.claude/commands/team* differs from the $COCO_BASE_REF install"
fi

[[ $fail -eq 0 ]] || exit 1
echo "PASS: grok /team commands find team-gate and arch-index; uninstall is clean; claude-code unchanged"
