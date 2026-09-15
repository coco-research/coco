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
# scans every tracked .sh/.py/.js/.yml/.yaml file for the same two idioms (a
# bash for-loop, or a bracket/brace list literal) whose tokens are mostly
# adapter names, and fails if the tokens it finds disagree with `ls adapters/`.
# It will catch a *new* hardcoded list added later, in a file this script has
# never heard of, the same way it would have caught the two above.
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
import pathlib, re, sys

real = set(sys.argv[1].split())
exts = {'.sh', '.py', '.js', '.yml', '.yaml'}
skip_dirs = {'.git', 'node_modules'}
# Owned by PR #179; see the file header comment for why.
skip_files = {
    pathlib.Path('.github/workflows/lint-frontmatter.yml'),
    pathlib.Path('tests/check-adapter-drift.sh'),
}

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

for path in sorted(pathlib.Path('.').rglob('*')):
    if not path.is_file() or path.suffix not in exts:
        continue
    if any(part in skip_dirs for part in path.parts):
        continue
    if path.parts[:1] == ('adapters',):
        continue  # adapters/<name>/install.sh legitimately mentions only its own name
    if path in skip_files:
        continue
    try:
        text = path.read_text(errors='ignore')
    except OSError:
        continue

    candidates = []

    for m in re.finditer(r'for\s+\w+\s+in\s+([^;\n]+?)\s*;\s*do', text):
        line = text.count('\n', 0, m.start()) + 1
        candidates.append((f'{path}:{line}', m.group(1).split()))

    for m in re.finditer(r'[A-Za-z_][A-Za-z0-9_]*\s*=\s*[\[{]([^\]\}]{0,400})[\]\}]', text, re.DOTALL):
        line = text.count('\n', 0, m.start()) + 1
        items = re.findall(r'''['"]([A-Za-z0-9_.-]+)['"]''', m.group(1))
        candidates.append((f'{path}:{line}', items))

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
