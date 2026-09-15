#!/usr/bin/env python3
"""Assert README.md's freeform skills/commands prose matches docs/asset-counts.json.

The pre-existing checks in tests/check-asset-counts.sh only ever read the shields
badge, the stat-tile <h3> cells, and the "Total Skills" spec-table row. Five
sentences say the same numbers in plain prose and were never covered by anything,
so they drifted independently: the hero line, the Skills Catalog opener (with a
"core + bundle" breakdown), the "Full catalog" summary, and two "Core install"
sentences (one HTML, one prose) each carrying a four-way breakdown.

Each check below is anchored to one specific, known sentence rather than any
"N skills" occurrence in the file. A generic version of that pattern would
false-positive on legitimate per-bundle prose that is correct as written and
not supposed to equal the repo-wide total or the core-only counts — e.g. "An
orchestration engine of **68 skills and 24 agents**" (GSD) or "**6 skills**"
(Brain). This script does not check those, or any other skills/commands mention
in the tree; it covers exactly the five sentences below. New prose claims of the
repo-wide total or the core-only breakdown need a new anchored check added here.

Where a sentence carries a breakdown, this also asserts the parts sum to the
stated total, independent of comparing each part to the source of truth — this
is the exact defect class found here: a total that was updated while its own
parenthetical breakdown was left at a stale sum.

Run from repo root: python3 tests/check-skills-commands-prose.py
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
SKILLS = counts['skills']['total']
SKILLS_CORE = counts['skills']['core']
SKILLS_BUNDLE = counts['skills']['bundle']
COMMANDS = counts['commands']['customer_facing']
COMMANDS_SHIPPED = counts['commands']['shipped']
AGENTS_CORE = counts['agents']['core']
RULES = counts['rules']

print(f'=== truth: skills={SKILLS} (core={SKILLS_CORE}, bundle={SKILLS_BUNDLE}) '
      f'commands.customer_facing={COMMANDS} (shipped={COMMANDS_SHIPPED}) '
      f'agents.core={AGENTS_CORE} rules={RULES} ===')

README = 'README.md'
text = open(README).read()


def check(pattern, label, expect_groups):
    """expect_groups: tuple of expected ints, matched 1:1 against capture groups."""
    m = re.search(pattern, text)
    if not m:
        fail_(f'{README}: could not find {label} (pattern not found)')
        return
    got = tuple(int(g) for g in m.groups())
    if got != expect_groups:
        fail_(f'{README}: {label} claims {got}, truth is {expect_groups}')
    else:
        pass_(f'{README}: {label} {got} matches')


def check_sum(parts, total, label):
    if sum(parts) != total:
        fail_(f'{README}: {label} breakdown {parts} sums to {sum(parts)}, not its own stated total {total}')
    else:
        pass_(f'{README}: {label} breakdown {parts} sums to its own stated total ({total})')


# 1. Hero line: "then **N skills**, **M commands**, and disk-persistent state..."
check(r'then \*\*(\d+) skills\*\*, \*\*(\d+) commands\*\*, and disk-persistent state',
      'hero line', (SKILLS, COMMANDS))

# 2. Skills Catalog opener: "CoCo ships **N skills** (X core + Y across bundles)."
m = re.search(r'CoCo ships \*\*(\d+) skills\*\* \((\d+) core \+ (\d+) across bundles\)', text)
if not m:
    fail_(f'{README}: could not find Skills Catalog opener (pattern not found)')
else:
    total, core, bundle = (int(g) for g in m.groups())
    if (total, core, bundle) != (SKILLS, SKILLS_CORE, SKILLS_BUNDLE):
        fail_(f'{README}: Skills Catalog opener claims total={total} core={core} bundle={bundle}, '
              f'truth is total={SKILLS} core={SKILLS_CORE} bundle={SKILLS_BUNDLE}')
    else:
        pass_(f'{README}: Skills Catalog opener ({total}, {core}, {bundle}) matches')
    check_sum((core, bundle), total, 'Skills Catalog opener')

# 3. Full catalog summary: "every one of the N skills"
check(r'Full catalog — every one of the (\d+) skills', 'full catalog summary', (SKILLS,))

# 4. "Core install:" HTML sub line with a four-way breakdown.
m = re.search(
    r'<sub><strong>Core install:</strong> (\d+) active assets '
    r'\((\d+) Skills, (\d+) Commands, (\d+) Agents, (\d+) Rules\)</sub>', text)
if not m:
    fail_(f'{README}: could not find "Core install:" sub line (pattern not found)')
else:
    total, sk, cm, ag, ru = (int(g) for g in m.groups())
    expect = (SKILLS_CORE, COMMANDS_SHIPPED, AGENTS_CORE, RULES)
    if (sk, cm, ag, ru) != expect:
        fail_(f'{README}: "Core install:" sub line claims {(sk, cm, ag, ru)}, truth is {expect}')
    else:
        pass_(f'{README}: "Core install:" sub line {(sk, cm, ag, ru)} matches')
    check_sum((sk, cm, ag, ru), total, '"Core install:" sub line')

# 5. "Core install ships N skills + M commands + K agents + R rules (Q active assets)." prose sentence.
m = re.search(
    r'Core install ships (\d+) skills \+ (\d+) commands \+ (\d+) agents \+ (\d+) rules '
    r'\((\d+) active assets\)', text)
if not m:
    fail_(f'{README}: could not find "Core install ships" prose sentence (pattern not found)')
else:
    sk, cm, ag, ru, total = (int(g) for g in m.groups())
    expect = (SKILLS_CORE, COMMANDS_SHIPPED, AGENTS_CORE, RULES)
    if (sk, cm, ag, ru) != expect:
        fail_(f'{README}: "Core install ships" prose claims {(sk, cm, ag, ru)}, truth is {expect}')
    else:
        pass_(f'{README}: "Core install ships" prose {(sk, cm, ag, ru)} matches')
    check_sum((sk, cm, ag, ru), total, '"Core install ships" prose')

print()
if fail == 0:
    print('  all README skills/commands prose claims agree with docs/asset-counts.json')
    sys.exit(0)
sys.exit(1)
