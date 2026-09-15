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
