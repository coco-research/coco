#!/usr/bin/env python3
"""Assert the public website pages agree with docs/released-counts.json.

index.html (repo root) and coco/index.html show the latest release, not
whatever main has counted. docs/released-counts.json is that tag's
asset-counts.json plus "version". README.md and tests/check-asset-counts.sh
stay on main.

Checks skills, commands, agents, personas and departments on both pages.
<span data-count="KEY">N</span> on index.html and every HTML file under
coco/ (coco/skills/ skipped) must use KEY skills, commands or agents, and
N must equal docs/released-counts.json "delivered"[KEY]. No such spans is
a pass.

Run from repo root: python3 tests/check-site-counts.py
"""
from html.parser import HTMLParser
import importlib.util
import json
import os
import re
import sys

_SYNC_SPEC = importlib.util.spec_from_file_location(
    'sync_counts', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'scripts', 'sync-counts.py'))
_SYNC_MOD = importlib.util.module_from_spec(_SYNC_SPEC)
_SYNC_SPEC.loader.exec_module(_SYNC_MOD)
SITE_DEPTS = _SYNC_MOD.SITE_DEPTS

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
for claim in (f'Coco {VERSION} <span', f'Available now, v{VERSION}, on npm'):
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
    ('coco/index.html', r'<meta name="description" content="(\d+) expert personas across (\d+) departments, (\d+) skills, and (\d+) commands', 'meta description', (PERSONAS, DEPARTMENTS, SKILLS, COMMANDS)),
    ('coco/index.html', r'<meta property="og:description" content="(\d+) expert personas across (\d+) departments, (\d+) skills, and (\d+) commands', 'og:description', (PERSONAS, DEPARTMENTS, SKILLS, COMMANDS)),
    ('coco/index.html', r'<meta name="twitter:description" content="(\d+) expert personas across (\d+) departments, (\d+) skills, and (\d+) commands', 'twitter:description', (PERSONAS, DEPARTMENTS, SKILLS, COMMANDS)),
    ('coco/index.html', r'"description": "(\d+) expert personas across (\d+) departments, (\d+) skills, and (\d+) commands', 'JSON-LD description', (PERSONAS, DEPARTMENTS, SKILLS, COMMANDS)),
    ('coco/index.html', r'<span class="kn-num">(\d+)</span><span class="kn-lbl">Expert personas across (\d+) departments</span>', 'key fact (personas, depts)', (PERSONAS, DEPARTMENTS)),
    ('coco/index.html', r'<span class="kn-num">(\d+)</span><span class="kn-lbl">Skills \(', 'key fact (skills)', (SKILLS,)),
    ('coco/index.html', r'<span class="kn-num">(\d+)</span><span class="kn-lbl">Commands across', 'key fact (commands)', (COMMANDS,)),
    ('coco/index.html', r'Ships (\d+) skills, (\d+) commands and (\d+) agents;', 'capability summary', (SKILLS, COMMANDS, AGENTS)),
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

coco_text = open('coco/index.html').read()
if f'"softwareVersion": "{VERSION}"' in coco_text and f'<tr><th>Version</th><td>{VERSION} (' in coco_text:
    pass_(f'coco/index.html: JSON-LD softwareVersion and Version row match {VERSION}')
else:
    fail_(f'coco/index.html: version mismatch against {VERSION}')

# The 3D product motif roster (assets/js/product-motifs-a.js) sizes each
# department cluster from COCO_SI_DEPTS; check it against docs/released-counts.json.
motifs_path = 'assets/js/product-motifs-a.js'
motifs_text = open(motifs_path, encoding='utf-8').read()
m = re.search(r'export const COCO_SI_DEPTS = \[(.*?)\];', motifs_text, re.S)
if not m:
    fail_(f'{motifs_path}: could not find COCO_SI_DEPTS array')
else:
    entries = [(lbl, int(n)) for lbl, n in re.findall(r"\['([^']+)',\s*(\d+)\]", m.group(1))]
    if len(entries) != DEPARTMENTS:
        fail_(f'{motifs_path}: COCO_SI_DEPTS has {len(entries)} entries, truth is {DEPARTMENTS} departments')
    else:
        pass_(f'{motifs_path}: COCO_SI_DEPTS entry count ({len(entries)}) matches')
    if sum(n for _, n in entries) != PERSONAS:
        fail_(f'{motifs_path}: COCO_SI_DEPTS sums to {sum(n for _, n in entries)}, truth is {PERSONAS}')
    else:
        pass_(f'{motifs_path}: COCO_SI_DEPTS sum ({sum(n for _, n in entries)}) matches')
    by_dept = counts['personas']['by_department']
    seen_labels = set()
    mismatches = []
    for lbl, n in entries:
        if lbl in seen_labels:
            mismatches.append(f'duplicate label {lbl!r}')
        seen_labels.add(lbl)
        key = SITE_DEPTS.get(lbl)
        if key is None:
            mismatches.append(f'unknown label {lbl!r}')
        elif n != by_dept.get(key):
            mismatches.append(f'{lbl!r} says {n}, released-counts[{key!r}] says {by_dept.get(key)}')
    missing_labels = sorted(set(SITE_DEPTS) - seen_labels)
    if missing_labels:
        mismatches.append(f'missing labels {missing_labels}')
    if mismatches:
        fail_(f'{motifs_path}: COCO_SI_DEPTS mismatch: {"; ".join(mismatches)}')
    else:
        pass_(f'{motifs_path}: all {len(entries)} COCO_SI_DEPTS entries match docs/released-counts.json')

# <span data-count="KEY">N</span> is the delivered-count claim. The flagship
# stats use <span class="num" data-count="495"> and are checked above.
SPAN_RE = re.compile(r'<span data-count="([^"]*)">([^<]*)</span>')
DELIVERED_KEYS = ('skills', 'commands', 'agents')


def html_pages():
    yield 'index.html'
    for dirpath, dirnames, filenames in os.walk('coco'):
        rel = dirpath.replace('\\', '/')
        if rel == 'coco':
            dirnames[:] = [d for d in dirnames if d != 'skills']
        if rel == 'coco/skills' or rel.startswith('coco/skills/'):
            continue
        for name in sorted(filenames):
            if name.endswith('.html'):
                yield rel + '/' + name


span_total = 0
for path in html_pages():
    text = open(path).read()
    for match in SPAN_RE.finditer(text):
        span_total += 1
        line = text.count('\n', 0, match.start()) + 1
        key = match.group(1)
        raw = match.group(2).strip()
        where = f'{path}:{line}'
        if key not in DELIVERED_KEYS:
            fail_(f'{where}: data-count key "{key}" is not one of {", ".join(DELIVERED_KEYS)}')
            continue
        if not raw.isdecimal():
            fail_(f'{where}: data-count "{key}" value "{match.group(2)}" is not numeric')
            continue
        got = int(raw)
        expect = counts['delivered'][key]
        if got != expect:
            fail_(f'{where}: data-count "{key}" is {got}, delivered is {expect}')
        else:
            pass_(f'{where}: data-count "{key}" {got} matches delivered')
if span_total == 0:
    pass_('no <span data-count="KEY"> spans on index.html or under coco/; check passed')


def _iter_strings(obj, prefix=''):
    if isinstance(obj, str):
        yield prefix, obj
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from _iter_strings(item, f'{prefix}[{i}]')
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _iter_strings(v, f'{prefix}.{k}' if prefix else k)


PUB_PATH = 'data/product-pages-public.json'
SEMVER_RE = re.compile(r'(?<![0-9.])v?(\d+\.\d+\.\d+)(?!\.\d|\d)')
REL_COUNT_RE = re.compile(r'\b(\d+)\s+(?:tagged|GitHub)\s+releases\b')
with open(PUB_PATH, encoding='utf-8') as fh:
    pub_text = fh.read()
pub_places = [(pat, keys) for p, pat, keys in _SYNC_MOD.SITE_PLACES if p == PUB_PATH]
pub_errs = []
for pat, keys in pub_places:
    ms = list(re.finditer(pat, pub_text))
    if not ms:
        pub_errs.append(f'pattern not found: /{pat}/')
    for m in ms:
        for i, key in enumerate(keys, 1):
            want = _SYNC_MOD.value(counts, key)
            got = m.group(i) if isinstance(want, str) else int(m.group(i))
            if got != want:
                line = pub_text.count('\n', 0, m.start(i)) + 1
                pub_errs.append(f'line {line}: {key} says {got}, truth is {want}')
for msg in pub_errs:
    fail_(f'{PUB_PATH}: {msg}')
if not pub_errs:
    pass_(f'{PUB_PATH}: all {len(pub_places)} coco-si count/version places match docs/released-counts.json')

with open('data/products.json', encoding='utf-8') as fh:
    products_raw = json.load(fh)
products_by_id = {r['id']: r for g in ('products', 'shipped', 'source', 'lab') for r in products_raw.get(g, ()) if 'id' in r}
for pid, entry in json.loads(pub_text).items():
    strings = list(_iter_strings(entry))
    if 'version' in entry:
        ver, row = entry['version'], products_by_id.get(pid, {})
        mp = re.search(r'\bv(\d+\.\d+\.\d+)\b', f"{row.get('tag', '')} {row.get('status', '')}")
        pver = row.get('version') or (mp.group(1) if mp else None)
        bad = [] if isinstance(ver, str) and re.fullmatch(r'\d+\.\d+\.\d+', ver) else [f'invalid version {ver!r}']
        bad.extend(f'{fp} says {m.group(1)}' for fp, s in strings for m in SEMVER_RE.finditer(s) if m.group(1) != ver)
        if pver and pver != ver:
            bad.append(f'data/products.json says {pver}')
        if bad:
            fail_(f'{PUB_PATH}: {pid} version {ver} mismatch: {"; ".join(bad)}')
        else:
            pass_(f'{PUB_PATH}: {pid} version {ver} is consistent')
    if 'progress' in entry:
        now, mx = entry['progress'].get('now'), entry['progress'].get('max')
        rels = [(fp, int(m.group(1))) for fp, s in strings for m in REL_COUNT_RE.finditer(s)]
        bad = [f'{fp} says {n}' for fp, n in rels if n != now]
        if type(now) is not int or type(mx) is not int or now != mx:
            bad.insert(0, f'progress now={now!r} max={mx!r}')
        if not any(fp == 'progress.count' for fp, _ in rels):
            bad.append('progress.count missing release count')
        if bad:
            fail_(f'{PUB_PATH}: {pid} release count mismatch: {"; ".join(bad)}')
        else:
            pass_(f'{PUB_PATH}: {pid} release count ({now}) consistent ({len(rels)} mentions)')
class _DrawerParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False); self.on, self.n, self.o, self.c, self.s, self.seen, self.e = False, 0, 0, 0, [], {}, []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs); cls = set((a.get('class') or '').split())
        if not self.on:
            if tag == 'dialog' and ('sn-drawer' in cls or a.get('id') == 'site-mobile-drawer'):
                self.on, self.n, self.o, self.c, self.s, self.seen = True, self.n + 1, 0, 0, [(tag, cls)], {'sn-d-all': 0, 'sn-d-top': 0, 'sn-d-foot': 0}
            return
        self.o += tag == 'div'
        for k in cls & self.seen.keys():
            self.seen[k] += 1
            if 'sn-d-body' not in self.s[-1][1] or any('sn-m-grid' in c for _, c in self.s): self.e.append(f'.{k} not direct child of .sn-d-body')
        if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'): self.s.append((tag, cls))
    def handle_endtag(self, tag):
        if not self.on: return
        if tag == 'dialog':
            if any(t == 'div' for t, _ in self.s[1:]) or self.o != self.c or any(v != 1 for v in self.seen.values()): self.e.append(f'divs {self.o}/{self.c} seen={self.seen}')
            self.on, self.s = False, []; return
        self.c += tag == 'div'; idx = next((i for i in range(len(self.s) - 1, 0, -1) if self.s[i][0] == tag), None)
        if idx is not None: del self.s[idx:]
        elif tag == 'div': self.e.append('extra </div>')
for dpath in sorted({p for p in ['coco/index.html'] + [f'{d}/index.html' for d in os.listdir('.') if os.path.isfile(f'{d}/index.html')] if p == 'coco/index.html' or 'sn-drawer' in open(p, encoding='utf-8').read()}):
    dp = _DrawerParser(); dp.feed(open(dpath, encoding='utf-8').read()); dp.close(); bad = dp.on or dp.n != 1 or dp.e
    (fail_ if bad else pass_)(f'{dpath}: drawer {"FAILED" if bad else "balanced"} ({dp.o}/{dp.c} divs; {"; ".join(dp.e) or ".sn-d-all/.sn-d-top/.sn-d-foot direct under .sn-d-body"})')
print()
if fail == 0:
    print('  all site-page counts agree with docs/released-counts.json')
    sys.exit(0)
sys.exit(1)
