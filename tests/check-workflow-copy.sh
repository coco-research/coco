#!/usr/bin/env bash
# Public copy for the Coco workflow skills avoids overclaiming words (GC rulings lab-0511/0513)
# and internal names. Fails on any hit, printing the file and line.
set -euo pipefail
cd "$(dirname "$0")/.."
files=$(ls skills/coco-spec/SKILL.md skills/coco-spec/references/*.md skills/coco-workflow/SKILL.md 2>/dev/null || true)
[ -n "$files" ] || { echo "no workflow skill files found" >&2; exit 1; }
words='enforc|can.?t escape|cannot escape|\bsafe\b|\breviewed\b|guarantee|\bblocks\b|\bprotects\b'
names='\b(Rijul|Steve|Cyra|Kanika|Emma|Atlas|Heliopause)\b|\bthe Lab\b|\bHQ\b'
paths='~/|/Users/'
rc=0
for pattern in "$words" "$names" "$paths"; do
  # shellcheck disable=SC2086
  if grep -n -i -E "$pattern" $files; then rc=1; fi
done
[ "$rc" -eq 0 ] && echo "ok   workflow skill copy: no banned words, internal names or machine paths"
exit "$rc"
