#!/usr/bin/env bash
# Public copy for the Coco workflow skills: no overclaiming words (GC rulings lab-0511/0513), no internal
# names or machine paths, and the GC-approved sentences (lab-0513, lab-0559) still there word for word.
# Fails on any hit or any missing sentence, printing the file and the text.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f skills/coco-spec/SKILL.md ] || { echo "missing skills/coco-spec/SKILL.md" >&2; exit 1; }
# Every markdown file of both workflow skills, so a new reference file can't escape the scan.
shopt -s nullglob
files=(skills/coco-spec/*.md skills/coco-spec/references/*.md skills/coco-workflow/*.md skills/coco-workflow/references/*.md)
words='\benforc|can.?t escape|cannot escape|\bsafe\b|\breviewed\b|guarantee|\bblocks\b|\bprotects\b'
names='\b(Rijul|Steve|Cyra|Kanika|Emma|Atlas|Heliopause)\b|\bthe Lab\b|\bHQ\b'
paths='~/|/Users/'
rc=0
for pattern in "$words" "$names" "$paths"; do
  if grep -n -i -E "$pattern" "${files[@]}"; then rc=1; fi
done
# Approved wording, pinned: "<file>|<exact text>". Each pinned sentence stays on one line of its file.
# Rewording any of these needs a new GC read.
while IFS='|' read -r file text; do
  [ -n "$file" ] || continue
  if [ ! -f "$file" ]; then echo "missing $file (it holds approved wording)" >&2; rc=1; continue; fi
  if ! grep -q -F -- "$text" "$file"; then echo "approved wording missing from $file: $text" >&2; rc=1; fi
done <<'PINS'
skills/coco-spec/SKILL.md|The short workflow file that runs the check is the exception: GitHub runs it as the pull request has it, so a pull request can change it to skip the check. Require code-owner review on `.github/` and `.coco/`, and turn on the branch rule that makes that review required, with no bypass.
skills/coco-spec/SKILL.md|This holds only if the repo makes `coco-workflow` a required check and limits who can merge. GitHub admins can bypass branch rules unless that's turned off.
skills/coco-spec/SKILL.md|Each role has its own key, so one leaked key affects only that role.
skills/coco-spec/SKILL.md|a build agent is never given a signing key
skills/coco-spec/SKILL.md|Skipping a gate is refused, not warned about (see Where the gate stops).
skills/coco-spec/SKILL.md|Coco Research isn't affiliated with MetaGPT or FoundationAgents.
CREDITS.md|Coco Research isn't affiliated with MetaGPT or FoundationAgents.
PINS
[ "$rc" -eq 0 ] && echo "ok   workflow skill copy: no banned words, internal names or machine paths; approved wording present"
exit "$rc"
