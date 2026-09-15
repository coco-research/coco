#!/usr/bin/env python3
"""Assert every published Super Intelligence team/cell/command claim matches
the live registries.

Team and command totals come from docs/asset-counts.json (departments.total,
commands.generated_si) — the same file every other count gate reads. Cell
totals are not tracked there, so they are summed live from the per-team
`cells` field in systems/superintelligence/registry.json, the machine-readable
meta-registry that build_commands.py and build_meta_commands.py themselves
read. Neither source is a filesystem walk: both are a single committed file
read by path, and every claim below is checked at a hardcoded, known path —
this gate does not discover its candidate files by scanning the tree.

Covers: systems/superintelligence/README.md, HOW-IT-WORKS.html,
.arch/ANALYSIS.md, docs/install.md, .github/workflows/ci.yml,
adapters/pi-desktop/install.sh, scripts/build-delivery-index.py, and
systems/superintelligence/scripts/build_meta_commands.py.

Does NOT cover: the per-bundle skill/agent counts other bundles state (e.g.
GSD's "68 skills and 24 agents") — those are unrelated claims about a
different bundle, so no rule here matches a bare "N teams" or "N commands"
generically; every pattern is anchored to the specific sentence it checks.
Does NOT cover dated historical notes that explicitly name an author and a
past date while explaining a superseded number (scripts/build-index.py's and
tests/check-asset-counts.sh's "Mira, 2026-08-29" comments, and the
AUDITED-2026-06-11 section of HOW-IT-WORKS.html) — those describe what was
true then, not a live claim, and rewriting them would destroy the point
they are making.

Run from repo root: python3 tests/check-si-counts.py
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
TEAMS = counts['departments']['total']
COMMANDS = counts['commands']['generated_si']
SKILLS = counts['skills']['total']
PERSONAS = counts['personas']['total']
PUBLIC_COMMANDS = counts['commands']['customer_facing']

registry = json.load(open('systems/superintelligence/registry.json'))
CELLS = sum(t['cells'] for t in registry['teams'].values())

print(f'=== truth: {TEAMS} SI teams, {CELLS} cells, {COMMANDS} generated commands '
      f'({SKILLS} skills / {PUBLIC_COMMANDS} commands published, {PERSONAS} personas) ===')


def check_one(path, pattern, label, expect, group=1):
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


def check_two(path, pattern, label, expect1, expect2):
    text = open(path).read()
    m = re.search(pattern, text)
    if not m:
        fail_(f'{path}: could not find {label} claim (pattern not found)')
        return
    n1, n2 = int(m.group(1)), int(m.group(2))
    if n1 != expect1 or n2 != expect2:
        fail_(f'{path}: {label} claims {n1}/{n2}, truth is {expect1}/{expect2}')
    else:
        pass_(f'{path}: {label} ({n1}/{n2}) matches')


def check_present(path, literal, label):
    text = open(path).read()
    if literal not in text:
        fail_(f'{path}: could not find {label} ({literal!r} not present)')
    else:
        pass_(f'{path}: {label} present')


README = 'systems/superintelligence/README.md'
check_one(README, r'\*\*All (\d+) teams built and activated\.\*\*', 'teams-built prose', TEAMS)
check_one(README, r'Meta-registry \((\d+) teams, default_team, build status\)', 'layout comment', TEAMS)

HOW = 'systems/superintelligence/HOW-IT-WORKS.html'
check_one(HOW, r'There are (\d+) slash commands under the hood', 'hero prose', COMMANDS)
check_one(HOW, r'<div class="stat"><b>(\d+)</b><span>expert teams</span></div>', 'stat tile teams', TEAMS)
check_one(HOW, r'<div class="stat"><b>(\d+)</b><span>specialist cells</span></div>', 'stat tile cells', CELLS)
check_one(HOW, r'<div class="stat"><b>(\d+)</b><span>slash commands</span></div>', 'stat tile commands', COMMANDS)
check_two(HOW, r'against all (\d+) teams \+ (\d+) cells', 'diagram scoring line', TEAMS, CELLS)
check_one(HOW, r'Once you know it, you know all (\d+):', 'grammar prose', COMMANDS)
check_one(HOW, r'<h3>The (\d+) teams</h3>', 'teams-table heading', TEAMS)

# The heading number and the table it introduces must agree — this is the exact
# bug this gate exists to catch: a heading bumped to 13 with a table still
# listing 9 rows.
how_text = open(HOW).read()
table_m = re.search(r'<h3>The \d+ teams</h3>\s*<table>(.*?)</table>', how_text, re.S)
if not table_m:
    fail_(f'{HOW}: could not find the teams table under the "The N teams" heading')
else:
    rows = re.findall(r'<tr><td><code>[^<]+</code></td>', table_m.group(1))
    if len(rows) != TEAMS:
        fail_(f'{HOW}: teams table has {len(rows)} rows, truth is {TEAMS} teams')
    else:
        pass_(f'{HOW}: teams table row count ({len(rows)}) matches')

ARCH = '.arch/ANALYSIS.md'
check_one(ARCH, r'The (\d+)-command Super Intelligence family', 'executive summary', COMMANDS)
check_one(ARCH, r'(\d+) more are generated at install', 'command surface component', COMMANDS)
check_two(ARCH, r'Super Intelligence\n\((\d+) skills over (\d+) personas\)',
          'bundled systems component', TEAMS, PERSONAS)
check_one(ARCH, r'(\d+) commands derive from thirteen', 'key decision', COMMANDS)

INSTALL = 'docs/install.md'
check_one(INSTALL, r'`superintelligence` \| 495-persona expert board, generates (\d+) commands at install',
          'bundle table row', COMMANDS)

CI = '.github/workflows/ci.yml'
check_one(CI, r'invoking the Super Intelligence generators drops (\d+) commands', 'delivery-index comment', COMMANDS)

PI = 'adapters/pi-desktop/install.sh'
check_two(PI, r'framework advertises (\d+) skills and (\d+) commands', 'default-bundle comment', SKILLS, PUBLIC_COMMANDS)
check_one(PI, r'The (\d+) SI-\* commands are not committed', 'SI-family comment', COMMANDS)
check_present(PI, 'generated from the thirteen team registries', 'team-registry count comment')
check_one(PI, r'the ordinary install still gets all (\d+)\.', 'bundle-default comment', COMMANDS)
check_one(PI, r'so the (\d+) Super', 'missing-generator warning', COMMANDS)

DELIV = 'scripts/build-delivery-index.py'
check_one(DELIV, r'command family \((\d+) commands\) is generated at', 'module docstring', COMMANDS)
check_two(DELIV, r'report (\d+) commands where macOS reports (\d+)\.', 'platform-neutrality comment',
          COMMANDS, PUBLIC_COMMANDS)

META = 'systems/superintelligence/scripts/build_meta_commands.py'
check_one(META, r'Do NOT dump the full (\d+)-command surface', 'dispatch template', COMMANDS)

print()
if fail == 0:
    print('  all published Super Intelligence team/cell/command claims agree with the live registries')
    sys.exit(0)
sys.exit(1)
