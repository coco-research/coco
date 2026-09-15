#!/usr/bin/env bash
# Guard: a hand-maintained adapter enumeration must not drift from adapters/ on
# disk. adapters/ is the ground truth; a Python KNOWN_ADAPTERS-style list or a
# bash `for adapter in ...` loop copies that truth into a second place by hand,
# and the copy goes stale silently the moment a new adapter lands — nothing
# fails, the list is just quietly wrong. tests/smoke.sh and
# .github/workflows/ci.yml both carried exactly this: a `for adapter in
# claude-code cursor grok vscode codex generic hermes; do` loop that never
# picked up aider, cline, roo-code, windsurf, zed, amazon-q,
# github-copilot-cli or vscode-continue.
#
# This is a general drift detector, not a re-check of those two files: it
# asks `git ls-files` for every tracked .sh/.py/.js/.yml/.yaml file (NUL-
# delimited, so a path with a space or an unusual character can't be split
# wrong), scans each for the same two idioms (a bash for-loop, or a
# bracket/brace list literal) whose tokens are mostly adapter names, and
# fails if the tokens it finds disagree with `ls adapters/`. It will catch a
# *new* hardcoded list added later, in a file this script has never heard of,
# the same way it would have caught the two above. Reading from `git
# ls-files` rather than walking the filesystem also means it only ever sees
# this repository's own tracked content: a nested `git worktree` checked out
# somewhere under this tree (this repo's own tooling creates them under
# .claude/worktrees/) holds a complete second copy of every tracked file, and
# a filesystem walk would score that copy as if it were part of this repo.
#
# Known gaps, stated plainly rather than overstated:
#   - .github/workflows/lint-frontmatter.yml's KNOWN_ADAPTERS is excluded on
#     purpose. PR #179 already fixes and gates that exact list (its own
#     tests/check-adapter-list.py), and that list's comment explains it is
#     allowed to run ahead of disk for an adapter landing in its own PR, which
#     is a different (subset, not equality) rule than the one this script
#     enforces. Once #179 merges, this script's exclusion can be dropped.
#   - Prose enumerations (a "claude-code | cursor | ..." help-text line in
#     install.sh / bin/coco.js / bin/coco-bootstrap.sh, or a README table) are
#     not detected. They are not for-loops or list literals, and they do not
#     claim to be exhaustive, so treating them as drift would be noise.
#   - A list built from a variable, a glob, or string concatenation rather
#     than literal tokens is not detected; this only reads literal source text.
#
# Run from repo root: bash tests/check-adapter-drift.sh

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
pass() { echo "  PASS: $1"; }
fail_() { echo "  FAIL: $1"; fail=1; }

REAL_ADAPTERS=$(for d in adapters/*/; do basename "$d"; done | sort)
echo "=== truth: adapters/ ==="
echo "  $(echo "$REAL_ADAPTERS" | tr '\n' ' ')"

echo ""
echo "=== scanning tree for hardcoded adapter enumerations ==="
if python3 - "$REAL_ADAPTERS" <<'PY'
import pathlib, re, subprocess, sys

real = set(sys.argv[1].split())

# git ls-files is the source of truth for "files in this repository": tracked
# content only, NUL-delimited so a path with a space or a newline can't be
# split wrong, and scoped to this worktree's own index so a nested worktree
# checked out on disk (adapters/*/install.sh legitimately mentions only its
# own name, so that whole directory is excluded too) never contributes a
# second, stale copy of a file this repo already tracks. Owned by PR #179;
# see the file header comment for why lint-frontmatter.yml is excluded.
out = subprocess.run(
    ['git', 'ls-files', '-z', '--',
     '*.sh', '*.py', '*.js', '*.yml', '*.yaml',
     ':!adapters/*',
     ':!.github/workflows/lint-frontmatter.yml',
     ':!tests/check-adapter-drift.sh'],
    capture_output=True, text=True, check=True,
).stdout
files = [f for f in out.split('\0') if f]

def report(where, items, real):
    items = sorted(items)
    missing = sorted(real - set(items))
    extra = sorted(set(items) - real)
    print(f'  FAIL: {where} lists {items}')
    if missing:
        print(f'        missing from adapters/: {missing}')
    if extra:
        print(f'        not a real adapters/ directory: {extra}')

drift = False

for f in files:
    try:
        text = pathlib.Path(f).read_text(errors='ignore')
    except OSError:
        continue

    candidates = []

    for m in re.finditer(r'for\s+\w+\s+in\s+([^;\n]+?)\s*;\s*do', text):
        line = text.count('\n', 0, m.start()) + 1
        candidates.append((f'{f}:{line}', m.group(1).split()))

    for m in re.finditer(r'[A-Za-z_][A-Za-z0-9_]*\s*=\s*[\[{]([^\]\}]{0,400})[\]\}]', text, re.DOTALL):
        line = text.count('\n', 0, m.start()) + 1
        items = re.findall(r'''['"]([A-Za-z0-9_.-]+)['"]''', m.group(1))
        candidates.append((f'{f}:{line}', items))

    for where, tokens in candidates:
        if len(tokens) < 3:
            continue
        matched = [t for t in tokens if t in real]
        if len(matched) < 3 or len(matched) < 0.6 * len(tokens):
            continue  # not enough overlap with real adapter names to be this defect
        if set(tokens) != real:
            report(where, tokens, real)
            drift = True

sys.exit(1 if drift else 0)
PY
then
  pass "no hardcoded adapter enumeration disagrees with adapters/"
else
  fail_ "one or more hardcoded adapter enumerations disagree with adapters/ (see above)"
fi

echo ""
echo "=== Summary ==="
if [ "$fail" -eq 0 ]; then
  echo "  no hardcoded adapter list drifts from adapters/"
  exit 0
fi
echo "  fix by deriving the list from adapters/*/ at runtime, or correcting it to match"
exit 1
