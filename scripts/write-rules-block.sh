#!/usr/bin/env bash
# Replace the Coco-managed rules block in a CLAUDE.md, or append it if absent.
#
# Usage: printf '%s\n' "$block" | bash scripts/write-rules-block.sh <target>
#
# The block on stdin must start with <!-- coco:rules-start --> and end with
# <!-- coco:rules-end -->. Shared by the claude-code and hermes adapters, which
# used to carry an inline awk that had three faults this script exists to fix:
#   - a start marker without an end marker made awk skip to end of file, and the
#     result overwrote the user's CLAUDE.md, deleting everything after the block;
#   - the blank line written before the block sat outside the markers, so every
#     install added one more;
#   - `mv tmp target` replaced a symlinked CLAUDE.md (dotfiles setups) with a copy.
# Now: an unterminated block leaves the file untouched and warns; trailing blank
# lines are trimmed so repeat runs are byte-identical; the file is written through
# (`cat >`), keeping a symlink a symlink and its mode; a .coco-bak copy is kept.

set -euo pipefail

target=${1:?usage: write-rules-block.sh <target> < block}
start="<!-- coco:rules-start -->"
end="<!-- coco:rules-end -->"
block=$(cat)

if [[ ! -f "$target" ]]; then
  printf '%s\n' "$block" > "$target"
  echo "Wrote rules block to $target"
  exit 0
fi

tmp=$(mktemp "${TMPDIR:-/tmp}/coco-rules.XXXXXX")
trap 'rm -f "$tmp"' EXIT

# Markers are compared with any trailing CR removed, so a CRLF file still matches;
# every kept line is printed exactly as it was. Exit 3 means an unterminated block.
if ! awk -v s="$start" -v e="$end" '
    { line = $0; sub(/\r$/, "", line) }
    line == s { if (skip) exit 3; skip = 1; next }
    line == e && skip { skip = 0; next }
    skip { next }
    { buf[++n] = $0; bare[n] = line }
    END {
      if (skip) exit 3
      while (n > 0 && bare[n] == "") n--
      for (i = 1; i <= n; i++) print buf[i]
    }
  ' "$target" > "$tmp"; then
  echo "WARNING: $target has a Coco rules block with no end marker ($end)." >&2
  echo "         Left it unchanged. Restore the marker, then re-run the installer." >&2
  exit 0
fi

if [[ -s "$tmp" ]]; then
  printf '\n%s\n' "$block" >> "$tmp"
else
  printf '%s\n' "$block" > "$tmp"
fi

if ! cmp -s "$tmp" "$target"; then
  cp -p "$target" "$target.coco-bak"
  cat "$tmp" > "$target"
fi
echo "Wrote rules block to $target"
