#!/usr/bin/env python3
"""Assert every published persona/department claim matches docs/asset-counts.json.

Covers README.md, package.json, agents/README.md, docs/install.md, docs/INDEX.md,
systems/superintelligence/HOW-IT-WORKS.html and assets/og-image.svg. The two
website pages (index.html, coco/index.html) are covered separately by
check-site-counts.py, since they publish the same figures under a different set
of patterns.

Run from repo root: python3 tests/check-persona-counts.py
"""
import json
import re
import sys

fail = 0


def fail_(msg):
    global fail
    print(f'  FAIL: {msg}')
    fail = 1


def pass_(msg):
    print(f'  PASS: {msg}')


counts = json.load(open('docs/asset-counts.json'))
PERSONAS = counts['personas']['total']
BY_DEPARTMENT = counts['personas']['by_department']
DEPARTMENTS = counts['departments']['total']

print(f'=== truth: {PERSONAS} personas across {DEPARTMENTS} departments ===')


def check_one(path, pattern, label, group=1, expect=PERSONAS):
    text = open(path).read()
    m = re.search(pattern, text)
    if not m:
        fail_(f'{path}: could not find {label} claim (pattern not found)')
        return
    n = int(m.group(group))
    if n != expect:
        fail_(f'{path}: {label} claims {n}, truth is {expect}')
    else:
        pass_(f'{path}: {label} ({n}) matches')


README = 'README.md'
check_one(README, r'advisory board of (\d+) world-class minds', 'hero line')
check_one(README, r'badge/personas-(\d+)-', 'personas badge')
check_one(README, r'cross-team board of (\d+) named experts', 'named-experts prose')
check_one(README, r'(\d+)-persona roster was compiled', 'roster-compiled prose')
check_one(README, r'<h3>(\d+)</h3><sub>Expert Personas</sub>', 'stat tile')
check_one(README, r"The \*\*(\d+)-persona advisory board\*\*", 'system-bundles prose')
check_one(README, r'<strong>Expert Personas</strong></td><td>(\d+) across', 'spec table row')

# The department breakdown table must carry every department, once, at its real
# persona count — not just a total that happens to add up.
readme_text = open(README).read()
m = re.search(
    r'\*\*(\d+) expert personas\*\*, organized across (\d+) specialized departments:\n\n'
    r'\| Department \| Experts \| Focus \|\n\|---\|---:\|---\|\n(.*?)\n\n', readme_text, re.S)
if not m:
    fail_(f'{README}: could not find the department breakdown table')
else:
    header_personas, header_depts = int(m.group(1)), int(m.group(2))
    if header_personas != PERSONAS:
        fail_(f'{README}: department table header claims {header_personas} personas, truth is {PERSONAS}')
    else:
        pass_(f'{README}: department table header personas ({header_personas}) matches')
    if header_depts != DEPARTMENTS:
        fail_(f'{README}: department table header claims {header_depts} departments, truth is {DEPARTMENTS}')
    else:
        pass_(f'{README}: department table header departments ({header_depts}) matches')
    rows = re.findall(r'\|\s*\*\*[^|]+\*\*\s*\|\s*(\d+)\s*\|', m.group(3))
    row_sum = sum(int(r) for r in rows)
    if len(rows) != DEPARTMENTS:
        fail_(f'{README}: department table has {len(rows)} rows, truth is {DEPARTMENTS} departments')
    else:
        pass_(f'{README}: department table row count ({len(rows)}) matches')
    if row_sum != PERSONAS:
        fail_(f'{README}: department table rows sum to {row_sum}, truth is {PERSONAS}')
    else:
        pass_(f'{README}: department table row sum ({row_sum}) matches')

check_one('package.json', r'advisory board of (\d+) world-class minds', 'description persona claim')
check_one('agents/README.md', r'the \*\*(\d+) Super Intelligence personas\*\*', 'personas bullet')
check_one('docs/install.md', r'`superintelligence` \| (\d+)-persona expert board', 'system bundles row')
check_one('docs/INDEX.md', r'(\d+)-persona expert board \(', 'by-system-bundle line')
check_one('systems/superintelligence/HOW-IT-WORKS.html',
          r'<div class="stat"><b>(\d+)</b><span>modeled experts</span></div>', 'stat block')
check_one('assets/og-image.svg', r'An advisory board of (\d+) world-class', 'social card text')

print()
if fail == 0:
    print('  all published persona/department claims agree with docs/asset-counts.json')
    sys.exit(0)
sys.exit(1)
