#!/usr/bin/env bash
# The rules block an install writes into CLAUDE.md must never damage the user's file.
# Runs the real claude-code adapter (--core-only, into a throwaway CLAUDE_HOME) and
# scripts/write-rules-block.sh, and fails on any of the faults that used to ship:
# growth on re-run, deletion of text after an unterminated block, a symlinked
# CLAUDE.md turned into a copy, and a duplicate block for CRLF markers.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
fail=0
check() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }
install_rules() { CLAUDE_HOME="$1" bash "$ROOT/adapters/claude-code/install.sh" --core-only >/dev/null 2>&1; }
blocks() { grep -c 'coco:rules-start' "$1" || true; }

# 1. Re-running the installer is byte-identical, and user text on both sides survives.
H="$WORK/h1"; mkdir -p "$H"
printf 'user top\n' > "$H/CLAUDE.md"
install_rules "$H"
printf 'user notes after block\n' >> "$H/CLAUDE.md"
install_rules "$H"; cp "$H/CLAUDE.md" "$WORK/run2"
install_rules "$H"
check "re-install is byte-identical"         'cmp -s "$WORK/run2" "$H/CLAUDE.md"'
check "exactly one block"                    '[[ $(blocks "$H/CLAUDE.md") == 1 ]]'
check "text above the block survives"        'grep -q "^user top$" "$H/CLAUDE.md"'
check "text below the block survives"        'grep -q "^user notes after block$" "$H/CLAUDE.md"'

# 2. A start marker with no end marker leaves the file untouched.
H="$WORK/h2"; mkdir -p "$H"
printf 'keep\n<!-- coco:rules-start -->\nold\nprecious user text\n' > "$H/CLAUDE.md"
cp "$H/CLAUDE.md" "$WORK/before"
out=$(printf '<!-- coco:rules-start -->\nnew\n<!-- coco:rules-end -->\n' \
      | bash "$ROOT/scripts/write-rules-block.sh" "$H/CLAUDE.md" 2>&1)
check "unterminated block: file unchanged"   'cmp -s "$WORK/before" "$H/CLAUDE.md"'
check "unterminated block: warns"            '[[ "$out" == *WARNING* ]]'

# 3. A symlinked CLAUDE.md stays a symlink, and its target gets the block.
H="$WORK/h3"; mkdir -p "$H" "$WORK/dotfiles"
printf 'dotfile content\n' > "$WORK/dotfiles/CLAUDE.md"
ln -s "$WORK/dotfiles/CLAUDE.md" "$H/CLAUDE.md"
install_rules "$H"
check "symlink preserved"                    '[[ -L "$H/CLAUDE.md" ]]'
check "symlink target updated"               '[[ $(blocks "$WORK/dotfiles/CLAUDE.md") == 1 ]]'

# 4. CRLF line endings: the old block is still found and replaced, not duplicated.
H="$WORK/h4"; mkdir -p "$H"
printf 'win\r\n<!-- coco:rules-start -->\r\nold\r\n<!-- coco:rules-end -->\r\n' > "$H/CLAUDE.md"
install_rules "$H"
check "CRLF block replaced, not duplicated"  '[[ $(blocks "$H/CLAUDE.md") == 1 ]]'
check "CRLF user line kept as-is"            'grep -q $'"'"'^win\r$'"'"' "$H/CLAUDE.md"'

exit $fail
