#!/usr/bin/env python3
"""Assert every adapters/ directory is allowed by lint-frontmatter's KNOWN_ADAPTERS.

KNOWN_ADAPTERS (.github/workflows/lint-frontmatter.yml) is allowed to run ahead
of disk on purpose — its own comment says an adapter may be listed there before
it lands, so a skill can declare support for it in the same release. So this
checks adapters.list is a subset of KNOWN_ADAPTERS, not equality. A shipped
adapter missing from KNOWN_ADAPTERS is still a real bug: it makes lint-frontmatter
reject any skill that legitimately declares support for it.

Run from repo root: python3 tests/check-adapter-list.py
"""
import json
import re
import sys

adapters = json.load(open('docs/asset-counts.json'))['adapters']['list']
workflow = open('.github/workflows/lint-frontmatter.yml').read()

m = re.search(r'KNOWN_ADAPTERS = \[(.*?)\]', workflow, re.S)
if not m:
    print('FAIL: could not find KNOWN_ADAPTERS in .github/workflows/lint-frontmatter.yml')
    sys.exit(1)

known = re.findall(r"'([^']+)'", m.group(1))
missing = [a for a in adapters if a not in known]
if missing:
    print(f'FAIL: adapters/ has {missing} not in lint-frontmatter.yml KNOWN_ADAPTERS '
          f'(a skill declaring supports: [{missing[0]}] would fail lint even though '
          f'adapters/{missing[0]}/ exists)')
    sys.exit(1)
print(f'PASS: all {len(adapters)} adapters/ directories are allowed by KNOWN_ADAPTERS')

# The vscode-continue adapter must be documented and agree across docs (#237): an install
# section, uninstall steps, and no leftover claim that the adapter is "planned" / "not stable".
install = open('docs/install.md').read()
uninstall = install.split('\n## Uninstall', 1)[-1].split('\n## ', 1)[0]
if 'vscode-continue' not in adapters:
    print('FAIL: vscode-continue is no longer in adapters.list; update this check')
    sys.exit(1)
if not re.search(r'^## VS Code with Continue\b', install, re.M):
    print('FAIL: docs/install.md has no "## VS Code with Continue" section for the vscode-continue adapter')
    sys.exit(1)
if '~/.continue' not in uninstall:
    print('FAIL: docs/install.md Uninstall section has no steps for ~/.continue (vscode-continue)')
    sys.exit(1)
if '--adapter vscode-continue' not in open('docs/getting-started.md').read():
    print('FAIL: docs/getting-started.md does not route Continue to --adapter vscode-continue')
    sys.exit(1)
if 'VS Code adapter (Continue-based) planned' in open('docs/guides/comparison.md').read():
    print('FAIL: docs/guides/comparison.md still calls the shipped vscode-continue adapter "planned"')
    sys.exit(1)
print('PASS: vscode-continue is documented consistently (install, uninstall, getting-started, comparison)')
