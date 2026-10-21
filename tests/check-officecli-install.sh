#!/usr/bin/env bash
# The officecli skill and /officecli command must install, and must not tell an
# agent to fetch a remote installer or run `officecli install`.
# Points the claude-code installer at a throwaway HOME, same idea as
# tests/smoke-home.sh and tests/check-claude-md-block.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
fail=0
check() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }

H="$WORK/home"
mkdir -p "$H"
if ! HOME="$H" CLAUDE_HOME="$H/.claude" bash "$ROOT/adapters/claude-code/install.sh" >"$WORK/install.log" 2>&1; then
  echo "FAIL installer exited non-zero; last lines of its output:"
  tail -20 "$WORK/install.log"
  exit 1
fi

SKILL="$H/.claude/skills/officecli/SKILL.md"
CMD="$H/.claude/commands/officecli.md"

check "installed skill"    '[[ -f "$SKILL" ]]'
check "installed command"  '[[ -f "$CMD" ]]'
check "repo license"       '[[ -f "$ROOT/skills/officecli/LICENSE" ]]'
check "repo notice"        '[[ -f "$ROOT/skills/officecli/NOTICE" ]]'
check "installed license"  '[[ -f "$H/.claude/skills/officecli/LICENSE" ]]'
check "installed notice"   '[[ -f "$H/.claude/skills/officecli/NOTICE" ]]'

if [[ ! -f "$SKILL" || ! -f "$CMD" ]]; then
  exit 1
fi

check "skill names brew install" 'grep -q "brew install officecli" "$SKILL"'
check "skill skips update check" 'grep -q "OFFICECLI_SKIP_UPDATE=1" "$SKILL"'

# `| sh` is matched as a shell command (end of line or whitespace after it).
# A fixed-string search also hits upstream table cells such as "| sheet".
forbid() {
  local label=$1 file=$2 needle=$3
  if grep -F -q -- "$needle" "$file"; then
    echo "FAIL $label contains: $needle"
    fail=1
  else
    echo "ok   $label has no: $needle"
  fi
}
forbid_re() {
  local label=$1 file=$2 pattern=$3
  if grep -E -q -- "$pattern" "$file"; then
    echo "FAIL $label matches: $pattern"
    fail=1
  else
    echo "ok   $label has no: $pattern"
  fi
}

for pair in "skill|$SKILL" "command|$CMD"; do
  label=${pair%%|*}
  file=${pair#*|}
  forbid_re "$label" "$file" '\| bash([[:space:]]|$)'
  forbid_re "$label" "$file" '\| sh([[:space:]]|$)'
  forbid "$label" "$file" 'iex'
  forbid "$label" "$file" 'd.officecli.ai/install'
done

# A prohibition may name the command. An instruction to run it may not.
instructs_install() {
  local file=$1 line
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      *'officecli install'*)
        case "$line" in
          *[Nn]ever*|*[Dd]o\ not*|*[Dd]on\'t*|*[Mm]ust\ not*) ;;
          *) return 1 ;;
        esac
        ;;
    esac
  done < "$file"
  return 0
}

check "skill does not order officecli install"    'instructs_install "$SKILL"'
check "command does not order officecli install"  'instructs_install "$CMD"'

if [[ "$fail" -eq 0 ]]; then
  echo "PASS: officecli install instructions"
fi
exit "$fail"
