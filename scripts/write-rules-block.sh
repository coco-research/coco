#!/usr/bin/env bash
# Replace the Coco-managed rules block in a CLAUDE.md, or append it if absent.
#
# Usage: printf '%s\n' "$block" | bash scripts/write-rules-block.sh <target> [--plan|--remove]
#
# --plan writes nothing. If a real run would keep a .coco-bak, the path is printed
# on stdout; otherwise stdout is empty.
# --remove drops the marked block and writes the file back through a symlink.
# Stdin is ignored. An unterminated block is left untouched and exits 3.
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

usage="usage: write-rules-block.sh <target> [--plan|--remove] < block"
target=${1:?$usage}
mode=apply
if [[ $# -gt 1 ]]; then
  if [[ $# -ne 2 ]]; then
    echo "$usage" >&2
    exit 2
  fi
  case "$2" in
    --plan) mode=plan ;;
    --remove) mode=remove ;;
    *) echo "$usage" >&2; exit 2 ;;
  esac
fi
start="<!-- coco:rules-start -->"
end="<!-- coco:rules-end -->"
block=$(cat)

if [[ ! -f "$target" ]]; then
  [[ $mode == plan || $mode == remove ]] && exit 0
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
  [[ $mode == remove ]] && exit 3
  exit 0
fi

# Same marker scan as an install, without appending a new block.
if [[ $mode == remove ]]; then
  if ! cmp -s "$tmp" "$target"; then
    cat "$tmp" > "$target"
  fi
  echo "Removed rules block from $target"
  exit 0
fi

if [[ -s "$tmp" ]]; then
  printf '\n%s\n' "$block" >> "$tmp"
else
  printf '%s\n' "$block" > "$tmp"
fi

if [[ $mode == plan ]]; then
  if ! cmp -s "$tmp" "$target"; then
    printf '%s\n' "$target.coco-bak"
  fi
  rm -f "$tmp"
  exit 0
fi

if ! cmp -s "$tmp" "$target"; then
  cp -p "$target" "$target.coco-bak"
  cat "$tmp" > "$target"
fi
echo "Wrote rules block to $target"
