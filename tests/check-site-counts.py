#!/usr/bin/env python3
"""Assert the public website pages agree with docs/released-counts.json.

index.html (repo root) and coco/index.html show the latest release, not
whatever main has counted. docs/released-counts.json is that tag's
asset-counts.json plus "version". README.md and tests/check-asset-counts.sh
stay on main.

Checks skills, commands, agents, personas and departments on both pages.

Run from repo root: python3 tests/check-site-counts.py
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


counts = json.load(open('docs/released-counts.json'))
SKILLS = counts['skills']['total']
COMMANDS = counts['commands']['customer_facing']
AGENTS = counts['agents']['total']
PERSONAS = counts['personas']['total']
DEPARTMENTS = counts['departments']['total']

VERSION = counts['version']
# The released version the counts come from must be the version the homepage names.
index_text = open('index.html').read()
for claim in (f'CoCo {VERSION} <span', f'Available now, v{VERSION}, on npm'):
    if claim in index_text:
        pass_(f'index.html: names release {VERSION} ({claim.split(" <")[0]})')
    else:
        fail_(f'index.html: expected "{claim}" to match docs/released-counts.json version {VERSION}')

print(f'=== truth: skills={SKILLS} commands={COMMANDS} agents={AGENTS} '
      f'personas={PERSONAS} departments={DEPARTMENTS} ===')

# (file, pattern, label, truth)
CHECKS = [
    ('index.html', r'data-count="(\d+)">\d+</span> <span class="unit">experts\.', 'flagship stat (personas)', (PERSONAS,)),
    ('index.html', r'data-count="(\d+)">\d+</span> <span class="unit">departments\.', 'flagship stat (departments)', (DEPARTMENTS,)),
    ('index.html', r'<span class="nw">(\d+) skills, (\d+) commands\.</span>', 'flagship facts (skills, commands)', (SKILLS, COMMANDS)),
    ('coco/index.html', r'<meta name="description" content="Each of the (\d+) requires a live, checkable source\. Then (\d+) skills', 'meta description (personas, skills)', (PERSONAS, SKILLS)),
    ('coco/index.html', r'<meta property="og:description" content="Each of the (\d+) requires a live, checkable source\. Then (\d+) skills', 'og:description (personas, skills)', (PERSONAS, SKILLS)),
    ('coco/index.html', r'<meta name="twitter:description" content="Each of the (\d+) requires a live, checkable source\. Then (\d+) skills', 'twitter:description (personas, skills)', (PERSONAS, SKILLS)),
    ('coco/index.html', r'<p class="sub reveal">Each of the (\d+) requires a live, checkable source\. Then (\d+) skills', 'on-page sub (personas, skills)', (PERSONAS, SKILLS)),
    ('coco/index.html', r'(\d+) expert personas across (\d+) departments, bar length', 'hero image alt (personas, departments)', (PERSONAS, DEPARTMENTS)),
    ('coco/index.html', r'(\d+) experts, broken out by department', 'figcaption (personas)', (PERSONAS,)),
    ('coco/index.html', r'<p class="n">(\d+)</p><p class="lbl">Expert personas</p>', 'stat tile (personas)', (PERSONAS,)),
    ('coco/index.html', r'<p class="n">(\d+)</p><p class="lbl">Departments</p>', 'stat tile (departments)', (DEPARTMENTS,)),
    ('coco/index.html', r'<p class="n">(\d+)</p><p class="lbl">Commands</p>', 'stat tile (commands)', (COMMANDS,)),
    ('coco/index.html', r'<p class="n">(\d+)</p><p class="lbl">Agents</p>', 'stat tile (agents)', (AGENTS,)),
    ('coco/index.html', r'<h2 class="reveal">(\d+) skills\. One instruction set each\.</h2>', 'section heading (skills)', (SKILLS,)),
    ('coco/index.html', r'<tr><th>Skills</th><td>(\d+) in the repository', 'spec table row (skills)', (SKILLS,)),
    ('coco/index.html', r'<tr><th>Commands</th><td>(\d+) customer-facing', 'spec table row (commands)', (COMMANDS,)),
    ('coco/index.html', r'<tr><th>Agents</th><td>(\d+)\.', 'spec table row (agents)', (AGENTS,)),
    ('coco/index.html', r'<tr><th>Personas</th><td>(\d+) across (\d+) departments', 'spec table row (personas, departments)', (PERSONAS, DEPARTMENTS)),
]

for path, pattern, label, expect in CHECKS:
    text = open(path).read()
    m = re.search(pattern, text)
    if not m:
        fail_(f'{path}: could not find {label} claim (pattern not found)')
        continue
    got = tuple(int(g) for g in m.groups())
    if got != expect:
        fail_(f'{path}: {label} claims {got}, truth is {expect}')
    else:
        pass_(f'{path}: {label} {got} matches')

# The hero SVG diagram (coco/index.html) draws one dot per persona, grouped by
# department, from a hardcoded `depts` array. A stale array renders a stale
# diagram even after every text claim on the page is fixed.
coco_text = open('coco/index.html').read()
m = re.search(r'var depts=\[(.*?)\];', coco_text, re.S)
if not m:
    fail_('coco/index.html: could not find the hero diagram depts array')
else:
    dot_counts = [int(n) for n in re.findall(r',(\d+)\]', m.group(1))]
    if len(dot_counts) != DEPARTMENTS:
        fail_(f'coco/index.html: hero diagram depts array has {len(dot_counts)} entries, '
              f'truth is {DEPARTMENTS} departments')
    else:
        pass_(f'coco/index.html: hero diagram depts array entry count ({len(dot_counts)}) matches')
    if sum(dot_counts) != PERSONAS:
        fail_(f'coco/index.html: hero diagram depts array sums to {sum(dot_counts)}, truth is {PERSONAS}')
    else:
        pass_(f'coco/index.html: hero diagram depts array sum ({sum(dot_counts)}) matches')

print()
if fail == 0:
    print('  all site-page counts agree with docs/released-counts.json')
    sys.exit(0)
sys.exit(1)
