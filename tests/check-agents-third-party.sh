#!/usr/bin/env bash
# Vendored agents: every row of agents/THIRD-PARTY.md names a real agent file and
# licence file, and a Claude Code install links those agents but never links
# THIRD-PARTY.md itself or anything under agents/licenses/.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
H=$(mktemp -d)
trap 'rm -rf "$H"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }

rows=$(grep -E '^\| `[^`]+\.md` \|' "$ROOT/agents/THIRD-PARTY.md" || true)
[[ -n "$rows" ]] || fail "agents/THIRD-PARTY.md has no file rows"
files=()
while IFS= read -r row; do
  f=$(sed -E 's/^\| `([^`]+)`.*/\1/' <<<"$row")
  lic=$(awk -F'|' '{print $(NF-1)}' <<<"$row" | tr -d ' `')
  [[ -f "$ROOT/agents/$f" ]] || fail "THIRD-PARTY.md lists agents/$f, which does not exist"
  [[ -f "$ROOT/agents/$lic" ]] || fail "THIRD-PARTY.md names agents/$lic, which does not exist"
  files+=("$f")
done <<<"$rows"

out=$(HOME="$H" bash "$ROOT/adapters/claude-code/install.sh" --dry-run 2>&1)
for f in "${files[@]}"; do
  grep -qF "/.claude/agents/$f" <<<"$out" || fail "vendored agent $f is not linked"
done
if grep -qE '/\.claude/agents/(THIRD-PARTY\.md|licenses)' <<<"$out"; then
  fail "THIRD-PARTY.md or agents/licenses/ is linked into ~/.claude/agents"
fi
echo "PASS: ${#files[@]} vendored agents linked; THIRD-PARTY.md and licences not linked"
