#!/usr/bin/env python3
"""Rewrite the published persona and department counts from one source of truth.

Default: the live public text (README.md, package.json, agents/README.md, docs/
and HOW-IT-WORKS.html) takes its numbers from docs/asset-counts.json, so a
persona change moves every count in the same commit.

--site: only the website files (index.html, coco/index.html,
assets/js/product-motifs-a.js), from docs/released-counts.json. The site shows
the last release, so run this in a release change only.

--check: change nothing; print each count that is out of date and exit 1.

Only anchored sentence patterns are rewritten: the claims that
tests/check-persona-counts.py and tests/check-site-counts.py read, plus the
same kind of sentence-anchored claim in docs/prd.md, docs/rules.md and
docs/tasks.md. No other file and no other number is touched (run records, the
SBOM, the painted-in numbers in images and video, the site scripts).

Run from repo root: python3 scripts/sync-counts.py [--check] [--site]
"""
import json
import re
import sys

DEPT_ROWS = {  # README department table row label -> by_department key
    'Engineering': 'engineering', 'AI': 'ai', 'Product & Design': 'product-design',
    'Finance': 'finance', 'Trading': 'trading', 'Legal & IP': 'legal-ip',
    'Risk & Compliance (GRC)': 'risk-compliance', 'Strategy': 'strategy',
    'Data & Analytics': 'data-analytics', 'Climate & Energy': 'climate-energy',
    'Education & EdTech': 'education-edtech',
    'Healthcare & Life Sciences': 'healthcare-life-sciences', 'Sales / GTM / Marketing': 'gtm',
}
SITE_DEPTS = {  # coco/index.html hero diagram label -> by_department key
    'Engineering': 'engineering', 'AI': 'ai', 'Product & design': 'product-design',
    'Finance': 'finance', 'Trading': 'trading', 'Legal & IP': 'legal-ip',
    'Risk & compliance': 'risk-compliance', 'Strategy': 'strategy',
    'Data & analytics': 'data-analytics', 'Climate & energy': 'climate-energy',
    'Education & edtech': 'education-edtech',
    'Healthcare & life sciences': 'healthcare-life-sciences', 'Sales & GTM': 'gtm',
}

P, D = 'personas', 'departments'

# (file, pattern, one key per capture group)
PLACES = [
    ('README.md', r'(\d+) personas across (\d+) departments, \*\*\d+ skills\*\*\[\^installed\]', (P, D)),
    ('README.md', r'badge/personas-(\d+)-', (P,)),
    ('README.md', r'cross-team board of (\d+) personas, each modeled on the public writing', (P,)),
    ('README.md', r'`/SI-Decide` seats 16-32 of (\d+) personas across (\d+) departments\.', (P, D)),
    ('README.md', r'The orchestrator scores (\d+) personas across (\d+) departments on domain fit', (P, D)),
    ('README.md', r'\*\*(\d+) expert personas\*\*, organized across (\d+) specialized departments:', (P, D)),
    ('README.md', r'The (\d+)-persona roster was compiled', (P,)),
    ('README.md', r'The \*\*(\d+)-persona advisory board\*\*', (P,)),
    ('README.md', r'<h3>(\d+)</h3><sub>Expert Personas</sub>', (P,)),
    ('README.md', r'<strong>Expert Personas</strong></td><td>(\d+) across (\d+) departments', (P, D)),
] + [
    ('README.md', r'\| \*\*' + re.escape(label) + r'\*\* \| (\d+) \|', ('dept:' + key,))
    for label, key in DEPT_ROWS.items()
] + [
    ('package.json', r'advisory board of (\d+) world-class minds', (P,)),
    ('agents/README.md', r'the \*\*(\d+) Super Intelligence personas\*\*', (P,)),
    ('docs/install.md', r'`superintelligence` \| (\d+)-persona expert board', (P,)),
    ('docs/INDEX.md', r'(\d+)-persona expert board \(', (P,)),
    ('docs/prd.md', r'\| Personas \| (\d+) \| Across (\d+) Super Intelligence departments \|', (P, D)),
    ('docs/rules.md', r'15 rules, (\d+) personas across (\d+) departments', (P, D)),
    ('docs/tasks.md', r'Persona scale toward 1000 \| [^|\n]*the roster is at (\d+) \|', (P,)),
    ('systems/superintelligence/HOW-IT-WORKS.html',
     r'<div class="stat"><b>(\d+)</b><span>modeled experts</span></div>', (P,)),
]

SITE_PLACES = [
    ('index.html', r'data-count="(\d+)">(\d+)</span> <span class="unit">experts\.', (P, P)),
    ('index.html', r'data-count="(\d+)">(\d+)</span> <span class="unit">departments\.', (D, D)),
    ('index.html', r'<span class="nw">(\d+) skills, (\d+) commands\.</span>', ('skills', 'commands')),
    ('coco/index.html', r'content="Each of the (\d+) requires a live, checkable source\. Then (\d+) skills',
     (P, 'skills')),
    ('coco/index.html', r'<p class="sub reveal">Each of the (\d+) requires a live, checkable source\. Then (\d+) skills',
     (P, 'skills')),
    ('coco/index.html', r'<p class="n">(\d+)</p><p class="lbl">Expert personas</p>', (P,)),
    ('coco/index.html', r'<p class="n">(\d+)</p><p class="lbl">Departments</p>', (D,)),
    ('coco/index.html', r'<p class="n">(\d+)</p><p class="lbl">Commands</p>', ('commands',)),
    ('coco/index.html', r'<p class="n">(\d+)</p><p class="lbl">Agents</p>', ('agents',)),
    ('coco/index.html', r'<h2 class="reveal">(\d+) skills\. One instruction set each\.</h2>', ('skills',)),
    ('coco/index.html', r'<tr><th>Skills</th><td>(\d+) in the repository', ('skills',)),
    ('coco/index.html', r'<tr><th>Commands</th><td>(\d+) \(', ('commands',)),
    ('coco/index.html', r'<tr><th>Agents</th><td>(\d+) delivered by', ('agents',)),
    ('coco/index.html', r'<tr><th>Personas</th><td>(\d+) across (\d+) departments', (P, D)),
    ('coco/index.html', r'The board: (\d+) departments, (\d+) seats\.', (D, P)),
    ('coco/index.html', r'The board diagram: (\d+) departments, (\d+) seats, drawn to scale\.', (D, P)),
    ('coco/index.html', r'/personas/\. Sum = (\d+)\.', (P,)),
] + [
    ('coco/index.html', r'\["' + re.escape(label) + r'",(\d+)\]', ('dept:' + key,))
    for label, key in SITE_DEPTS.items()
] + [
    ('assets/js/product-motifs-a.js', r"\['" + re.escape(label) + r"', (\d+)\]", ('dept:' + key,))
    for label, key in SITE_DEPTS.items()
]


def value(counts, key):
    if key.startswith('dept:'):
        return counts['personas']['by_department'][key[5:]]
    return {
        P: counts['personas']['total'],
        D: counts['departments']['total'],
        'skills': counts['skills']['total'],
        'commands': counts['commands']['customer_facing'],
        'agents': counts['agents']['total'],
    }[key]


def label(key):
    return key[5:] + ' personas' if key.startswith('dept:') else key


def main(argv):
    check, site = '--check' in argv, '--site' in argv
    unknown = [a for a in argv if a not in ('--check', '--site')]
    if unknown:
        print(f'sync-counts: unknown argument {unknown[0]}; usage: sync-counts.py [--check] [--site]',
              file=sys.stderr)
        return 2
    source = 'docs/released-counts.json' if site else 'docs/asset-counts.json'
    run = 'python3 scripts/sync-counts.py' + (' --site' if site else '')
    counts = json.load(open(source))
    places = SITE_PLACES if site else PLACES

    stale, missing, changed = [], [], set()
    texts = {}
    for path, pattern, keys in places:
        if path not in texts:
            with open(path, encoding='utf-8') as fh:
                texts[path] = fh.read()
        text = texts[path]
        matches = list(re.finditer(pattern, text))
        if not matches:
            missing.append(f'{path}: could not find the claim /{pattern}/ (pattern not found)')
            continue
        # Rewrite back to front so earlier offsets stay valid.
        for m in reversed(matches):
            for g in range(len(keys), 0, -1):
                want = value(counts, keys[g - 1])
                got = int(m.group(g))
                if got == want:
                    continue
                line = text.count('\n', 0, m.start(g)) + 1
                stale.append((path, line, f'{path}:{line}: {label(keys[g - 1])} says {got}, '
                              f'{source} says {want}. Run: {run}'))
                text = text[:m.start(g)] + str(want) + text[m.end(g):]
                changed.add(path)
        texts[path] = text

    for msg in missing:
        print(msg, file=sys.stderr)
    if check:
        for _, _, msg in sorted(stale):
            print(msg)
        files = len({path for path, _, _ in stale})
        if files:
            print(f'check-count-sync: {files} file{"s" if files != 1 else ""} out of date')
        elif not missing:
            print(f'check-count-sync: all {len(places)} places match {source}')
        return 1 if stale or missing else 0

    for path in sorted(changed):
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(texts[path])
    print(f'sync-counts: {len(stale)} count(s) rewritten in {len(changed)} file(s) from {source}')
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
