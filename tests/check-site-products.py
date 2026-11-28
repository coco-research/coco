#!/usr/bin/env python3
"""Assert product rows are complete (homepage, /products/, /lab/, release feed),
the two-group 2 + 8 = 10 contract holds, Voice meetings copy names macOS 14.4,
shared nav/drawer regions match across all 14 pages, and count literals agree.

Run from repo root: python3 tests/check-site-products.py
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

fail = 0


def fail_(msg):
    global fail
    print('  FAIL: %s' % msg)
    fail = 1


def pass_(msg):
    print('  PASS: %s' % msg)


data = json.loads(Path('data/products.json').read_text())
if sorted(data) == ['lab', 'products']:
    pass_('data/products.json has exactly two groups: products and lab (no source group)')
else:
    fail_('data/products.json groups are %s, expected exactly products and lab' % sorted(data))
shipped = data.get('products', [])
lab = data.get('lab', [])
source = [r for r in lab if 'href' in r]
private = [r for r in lab if 'href' not in r]

print('=== homepage products: products=%d lab=%d (public source %d, private %d) ===' % (len(shipped), len(lab), len(source), len(private)))
if (len(shipped), len(lab)) == (2, 8) and len(shipped) + len(lab) == 10:
    pass_('2 products + 8 in the lab = 10')
else:
    fail_('expected 2 + 8 = 10, got %d + %d' % (len(shipped), len(lab)))
if [r['id'] for r in shipped] == ['coco-si', 'voice'] and [r['id'] for r in lab] == ['heliopause', 'signal', 'mira', 'jev-use', 'm0', 'hermes', 'teams-ng', 'aloomannu']:
    pass_('group membership and order match the plan (Products: coco-si, voice; In the lab: heliopause ... aloomannu)')
else:
    fail_('group membership or order drifted: %s / %s' % ([r['id'] for r in shipped], [r['id'] for r in lab]))

for row in shipped:
    pid = row.get('id', '?')
    missing = []
    if not row.get('tag'):
        missing.append('tag')
    if not row.get('description_html'):
        missing.append('description')
    if not row.get('actions'):
        missing.append('action')
    if missing:
        fail_('product %s missing %s' % (pid, ', '.join(missing)))
    else:
        pass_('product %s has tag, description and an action' % pid)

for row in shipped:
    art = Path(row.get('art', ''))
    if art.is_file():
        pass_('art %s exists' % art)
    else:
        fail_('art %s is missing' % art)

for row in source:
    pid = row.get('id', '?')
    href = row.get('href', '')
    if href.startswith('https://'):
        pass_('lab %s href is https' % pid)
    else:
        fail_('lab %s href %r is not https' % (pid, href))
    status = row.get('status', '')
    if status.startswith('Source available'):
        pass_('lab %s status starts with Source available' % pid)
    else:
        fail_('lab %s status %r does not start with Source available' % (pid, status))

for row in private:
    pid = row.get('id', '?')
    status = row.get('status', '')
    if status.startswith('Private'):
        pass_('lab %s status starts with Private' % pid)
    else:
        fail_('lab %s status %r does not start with Private' % (pid, status))

alo = next((r for r in lab if r.get('id') == 'aloomannu'), None)
if alo and alo.get('status') == 'Private, in the lab' and 'href' not in alo and alo.get('page') == 'aloomannu/':
    pass_('Aloo Mannu is in the lab as "Private, in the lab", linked to /aloomannu/, with no repository href')
else:
    fail_('Aloo Mannu row is missing or wrong')
for gone in ('status-zero', 'loops'):
    if any(r.get('id') == gone for r in shipped + lab) or Path(gone).exists():
        fail_('%s is still in the data or on disk' % gone)
    else:
        pass_('%s is removed from the data and from disk' % gone)

proc = subprocess.run([sys.executable, 'scripts/render-site-products.py', '--check'], capture_output=True, text=True)
if proc.returncode == 0:
    pass_('index.html and m0/index.html match data/products.json')
else:
    fail_('index.html or m0/index.html differs from data/products.json (render --check exited %s)' % proc.returncode)
    sys.stdout.write(proc.stdout[:2000])
    sys.stderr.write(proc.stderr)

# ---- v1.3 directory fields: drive /products/, /lab/, the menu and /whats-new/ ----
LICENCES = {
    'coco-si': ('Open-core (Apache-2.0 core)', False),
    'voice': ('MIT License \u00b7 Open source', True),
    'signal': ('Apache-2.0 \u00b7 Open source', True),
    'mira': ('AGPL-3.0 \u00b7 Open source', True),
    'jev-use': ('Apache-2.0 \u00b7 Open source', True),
    'heliopause': ('Apache-2.0 \u00b7 Open source', True),
    'm0': ('Private', False),
    'hermes': ('Private', False),
    'teams-ng': ('Private', False),
    'aloomannu': ('Private', False),
}
RELEASES = {
    'coco-si': ('2026-11-26', 'v2.4.0'),
    'voice': ('2026-11-26', 'v0.20.9'),
    'heliopause': ('2026-10-31', 'v0.7.3'),
}
rows = shipped + lab
if len(rows) == 10:
    pass_('catalog holds 10 linked products')
else:
    fail_('catalog holds %d rows, expected 10' % len(rows))
for row in rows:
    pid = row.get('id', '?')
    missing = [k for k in ('for_you', 'who_for', 'licence_short', 'whats_new') if not str(row.get(k, '')).strip()]
    if missing:
        fail_('%s missing %s' % (pid, ', '.join(missing)))
    else:
        pass_('%s has for_you, who_for, licence_short and whats_new' % pid)
    want_lic, want_open = LICENCES.get(pid, (None, None))
    if row.get('licence_short') == want_lic and row.get('open_source') is want_open:
        pass_('%s licence %r, open_source=%s' % (pid, want_lic, want_open))
    else:
        fail_('%s licence/open_source is %r/%r, expected %r/%r' % (pid, row.get('licence_short'), row.get('open_source'), want_lic, want_open))
    rd = row.get('release_date')
    if pid in RELEASES:
        if (rd, row.get('release_version')) == RELEASES[pid] and str(row.get('release_url', '')).startswith('https://github.com/coco-research/') \
                and row['release_url'].endswith('/releases/tag/' + RELEASES[pid][1]):
            pass_('%s release %s %s with a tag URL' % (pid, RELEASES[pid][1], rd))
        else:
            fail_('%s release facts drifted: %r %r' % (pid, rd, row.get('release_version')))
    elif rd is not None:
        fail_('%s has an unexpected release_date %r' % (pid, rd))
    else:
        pass_('%s has no release date, as expected' % pid)
    blob = ' '.join(str(v) for v in row.values())
    if 'Details soon' in blob or 'Coco Teams ' in blob.replace('Coco Teams NG', ''):
        fail_('%s has a stub or a shortened Coco Teams NG name' % pid)
if any('open source' in (r.get('for_you', '') + r.get('whats_new', '')).lower() for r in rows if r.get('id') == 'coco-si'):
    fail_('coco-si copy calls the product open source')
else:
    pass_('coco-si is never called open source')

# ---- editorial copy rules on every data file and rendered page ----
COPY_RULE_FILES = [
    Path('data/products.json'), Path('data/product-pages-public.json'), Path('data/product-pages-lab.json'),
    Path('index.html'), Path('products/index.html'), Path('lab/index.html'), Path('whats-new/index.html'),
    Path('voice/index.html'), Path('llms.txt'),
]
banned = re.compile(r'\bbuilt on\b|built (?:it |this |them )?from scratch|own speech engine', re.I)
voice_only = re.compile(r'notariz|\bsigned\b|\bunsigned\b', re.I)  # never claim Voice builds are signed or notarized
specs_public = json.loads(Path('data/product-pages-public.json').read_text())
voice_row = next((r for r in shipped if r.get('id') == 'voice'), None)
voice_spec = specs_public.get('voice')
voice_blobs = {
    'data/products.json (voice row)': json.dumps(voice_row) if voice_row is not None else '',
    'data/product-pages-public.json (voice spec)': json.dumps(voice_spec) if voice_spec is not None else '',
}
for f in COPY_RULE_FILES:
    txt = f.read_text() if f.is_file() else ''
    if f.name == 'product-pages-public.json':  # credits_html is the Licence credit row: the one place the upstream app is named
        txt = re.sub(r'"credits_html":\s*"(?:[^"\\]|\\.)*"', '"credits_html": ""', txt)
    if f.name == 'index.html' and f.parent.name == 'voice':
        txt = txt.partition('<section id="credits"')[0]  # the Licence credit row is the only place the upstream app may be named
        voice_blobs[str(f)] = txt
    hit = banned.search(txt)
    if hit:
        fail_('%s breaks a copy rule: %r' % (f, hit.group(0)))
    elif re.search(r'handy', txt, re.I):
        fail_('%s names the upstream speech app outside the credit row' % f)
    else:
        bad = [m.group(0) for m in re.finditer(r'super[ -]?intelligence', re.sub(r'<!--.*?-->', '', txt), re.I)
               if m.group(0) not in ('Super Intelligence', 'superintelligence')]
        if bad:
            fail_('%s misspells Coco Super Intelligence: %s' % (f, sorted(set(bad))))
        else:
            pass_('%s: copy rules hold (no built-on / from-scratch / own engine, upstream app unnamed, Coco Super Intelligence spelled in full)' % f)
for name, blob in voice_blobs.items():
    if not blob:
        fail_('%s missing for signed / notarized check' % name)
    elif voice_only.search(blob):
        fail_('%s says Coco Voice builds are signed or notarized' % name)
    else:
        pass_('%s: no signed / notarized claim' % name)

whatsnew_html = Path('whats-new/index.html').read_text()
whats_voice = re.search(r'<article class="tl-entry">(?:(?!</article>).)*?Coco Voice(?:(?!</article>).)*?</article>', whatsnew_html, re.S)
if whats_voice and not voice_only.search(whats_voice.group(0)):
    pass_('whats-new/index.html Coco Voice entry: no signed / notarized claim')
else:
    fail_('whats-new/index.html Coco Voice entry missing or claims signed / notarized')

# Voice meetings are built into macOS builds only (macOS 14.4 and later); every
# Voice copy surface that mentions "meeting" must state "macOS 14.4".
llms_voice = next((ln for ln in Path('llms.txt').read_text().splitlines() if '[Coco Voice](' in ln), '')
index_html = Path('index.html').read_text()
home_voice = re.search(r'<article\b[^>]*class="[^"]*\bcard\b[^"]*"(?:(?!</article>).)*?id="t-voice"(?:(?!</article>).)*?</article>', index_html, re.S)
voice_pre_credits = voice_blobs.get('voice/index.html', '')
meeting_blobs = {
    'data/products.json (voice row)': voice_blobs['data/products.json (voice row)'],
    'data/product-pages-public.json (voice spec)': voice_blobs['data/product-pages-public.json (voice spec)'],
    'voice/index.html (before #credits)': voice_pre_credits,
    'whats-new/index.html (Coco Voice entry)': whats_voice.group(0) if whats_voice else '',
    'llms.txt (Coco Voice line)': llms_voice,
    'index.html (home Coco Voice card)': home_voice.group(0) if home_voice else '',
}
for name, blob in meeting_blobs.items():
    if not blob:
        fail_('%s missing for Voice meetings platform check' % name)
    elif re.search(r'meeting', blob, re.I):
        if 'macOS 14.4' in blob:
            pass_('%s: meetings claim states macOS 14.4' % name)
        else:
            fail_('%s mentions meetings without macOS 14.4' % name)
    else:
        pass_('%s: no meetings claim' % name)
voice_meeting_lines = [
    lineno for lineno, ln in enumerate(voice_pre_credits.splitlines(), 1)
    if re.search(r'meeting', ln, re.I) and 'macOS 14.4' not in ln
]
if voice_meeting_lines:
    fail_('voice/index.html has meetings lines without macOS 14.4: %s' % ', '.join('L%d' % n for n in voice_meeting_lines))
else:
    pass_('voice/index.html: every line mentioning meetings names macOS 14.4')

# ---- generated discovery surface ----
proc = subprocess.run([sys.executable, 'scripts/render-product-pages.py', '--check'], capture_output=True, text=True)
if proc.returncode == 0:
    pass_('9 generated product pages, /products/, /lab/, /whats-new/, sitemap.xml and llms.txt match the data (m0 is hand-built)')
else:
    fail_('generated product surface is stale (render-product-pages --check exited %s)' % proc.returncode)
    sys.stdout.write(proc.stdout[:2000])
products_html = Path('products/index.html').read_text()
lab_html = Path('lab/index.html').read_text()
if products_html.count('<article class="dir-card"') == 10 and 'Aloo Mannu' in products_html and 'href="../aloomannu/"' in products_html:
    pass_('/products/ shows all 10 cards, Aloo Mannu linked')
else:
    fail_('/products/ card count or Aloo Mannu link wrong')
if lab_html.count('<article class="dir-card"') == 8 and 'href="../aloomannu/"' in lab_html and 'Private, in the lab' in lab_html:
    pass_('/lab/ shows the 8 lab projects, Aloo Mannu linked and marked Private, in the lab')
else:
    fail_('/lab/ card count or Aloo Mannu link wrong')
if whatsnew_html.count('<article class="tl-entry">') == 3 and 'href="../aloomannu/"' in whatsnew_html:
    pass_('/whats-new/ shows the three tagged releases and links Aloo Mannu')
else:
    fail_('/whats-new/ release count or Aloo Mannu link wrong')
for name, text in (('products/index.html', products_html), ('lab/index.html', lab_html), ('whats-new/index.html', whatsnew_html)):
    if 'Details soon' in text or 'cdn.jsdelivr' in text or re.search(r'status[- ]zero|coco[- ]loops|/loops/|Source available</button>', text, re.I):
        fail_('%s has a stub, a CDN URL, a removed product or a Source available tab' % name)
    else:
        pass_('%s: zero stubs, zero CDN URLs, zero Status Zero / Coco Loops, no Source available tab' % name)
alo_html = Path('aloomannu/index.html').read_text()
if 'noindex' in alo_html:
    fail_('aloomannu/index.html is still noindex')
else:
    pass_('aloomannu/index.html is indexable (no noindex)')

# ---- C6 shared nav/drawer parity across all 14 top-level pages (m0 required unconditionally) ----
nav_re = re.compile(r'<header class="site-nav".*?</dialog>', re.S)


def _norm_nav(text):
    m = nav_re.search(text)
    return m.group(0).replace(' aria-current="page"', '') if m else None


def check_c6_nav(root, ref_nav):
    errs = []
    checked = 0
    for page_p in sorted(root.glob('*/index.html')):
        ptxt = page_p.read_text()
        if '<meta http-equiv="refresh"' in ptxt:
            continue
        if ref_nav and _norm_nav(ptxt) == ref_nav:
            checked += 1
        else:
            errs.append('%s: nav/drawer differs from generated page nav' % page_p)
    if checked != 14:
        errs.append('expected 14 top-level pages with shared nav, verified %d' % checked)
    m0_path = root / 'm0' / 'index.html'
    if not m0_path.is_file():
        errs.append('m0/index.html is missing')
    else:
        m0_txt = m0_path.read_text()
        for region in ('nav', 'foot'):
            pat = r'<!-- products:%s:start -->\s*(.*?)\s*<!-- products:%s:end -->' % (region, region)
            match = re.search(pat, m0_txt, re.S)
            if not match:
                errs.append('m0/index.html exists without products:%s markers' % region)
            elif region == 'nav' and _norm_nav(match.group(1)) != ref_nav:
                errs.append('m0/index.html products:nav region differs from generated nav/drawer')
    return errs, checked


ref_nav = _norm_nav(products_html)
c6_errs, nav_checked = check_c6_nav(Path('.'), ref_nav)
if c6_errs:
    for err in c6_errs:
        fail_(err)
else:
    pass_('all %d top-level */index.html pages match generated nav/drawer (m0 required)' % nav_checked)

# Self-test: C6 must fail when m0/index.html is absent or lacks products:nav / products:foot markers.
with tempfile.TemporaryDirectory(prefix='c6-m0-check-') as tmp:
    troot = Path(tmp)
    missing_m0, _ = check_c6_nav(troot, ref_nav)
    (troot / 'm0').mkdir()
    (troot / 'm0' / 'index.html').write_text(ref_nav + '\n')
    no_nav, _ = check_c6_nav(troot, ref_nav)
    (troot / 'm0' / 'index.html').write_text('<!-- products:nav:start -->\n%s\n<!-- products:nav:end -->\n' % ref_nav)
    no_foot, _ = check_c6_nav(troot, ref_nav)
    (troot / 'm0' / 'index.html').write_text(
        '<!-- products:nav:start -->\n%s\n<!-- products:nav:end -->\n<!-- products:foot:start -->\n<footer></footer>\n<!-- products:foot:end -->\n'
        % ref_nav
    )
    ok_m0, _ = check_c6_nav(troot, ref_nav)
if (
    any('m0/index.html is missing' in e for e in missing_m0)
    and any('products:nav' in e for e in no_nav)
    and any('products:foot' in e for e in no_foot)
    and not any('m0/index.html' in e for e in ok_m0)
):
    pass_('C6 self-test: absent m0 and missing products:nav or products:foot fail; valid markers pass')
else:
    fail_('C6 self-test failed: missing=%r no_nav=%r no_foot=%r ok_m0=%r' % (missing_m0, no_nav, no_foot, ok_m0))

# ---- guard homepage, /m0/, and /rijul-kalra/ count literals against len(products) and len(lab) ----
NUM_WORDS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve')


def _word(n, cap=False):
    w = NUM_WORDS[n] if 0 <= n < len(NUM_WORDS) else str(n)
    return w.capitalize() if cap else w


def check_count_literals(root, n_prod, n_lab):
    n_total = n_prod + n_lab
    errs = []
    texts = {}
    for rel in ('index.html', 'm0/index.html', 'rijul-kalra/index.html'):
        p = root / rel
        if not p.is_file():
            errs.append('%s is missing' % rel)
        else:
            texts[rel] = p.read_text()
    if errs:
        return errs
    idx_txt = texts['index.html']
    m0_txt = texts['m0/index.html']
    rijul_txt = texts['rijul-kalra/index.html']

    single_checks = [
        ('index.html products-head group-n', idx_txt, r'Products <span class="group-n">(\d+)</span>', (str(n_prod),)),
        ('index.html products-head Browse all', idx_txt, r'<a class="see" href="\./products/">Browse all (\d+) products', (str(n_total),)),
        ('index.html lab-sub group-n', idx_txt, r'In the lab <span class="group-n">(\d+)</span>', (str(n_lab),)),
        ('index.html rail All N', idx_txt, r'<a class="rail-jump" href="\./products/"><span>All (\d+) ', (str(n_total),)),
        ('m0/index.html body Browse all', m0_txt, r'<a class="link-pill" href="\.\./products/">Browse all (\d+) products</a>', (str(n_total),)),
        ('rijul-kalra/index.html count summary', rijul_txt,
         r'<p>(\w+) in all: (\w+) you can use today, and (\w+) in the lab\.</p>',
         (_word(n_total, cap=True), _word(n_prod), _word(n_lab))),
    ]
    for label, haystack, pat, want in single_checks:
        m = re.search(pat, haystack)
        if not (m and m.groups() == want):
            errs.append('%s drifted: got %r, expected %r' % (label, m.groups() if m else None, want))

    m0_browse_all = re.findall(r'Browse all (\d+) products', m0_txt)
    if len(m0_browse_all) != 3 or any(val != str(n_total) for val in m0_browse_all):
        errs.append('m0/index.html Browse all literals drifted: got %r, expected 3 x %r' % (m0_browse_all, str(n_total)))
    return errs


n_prod, n_lab = len(shipped), len(lab)
count_errs = check_count_literals(Path('.'), n_prod, n_lab)
if count_errs:
    for err in count_errs:
        fail_(err)
else:
    pass_('homepage, all 3 /m0/ Browse all literals, and /rijul-kalra/ count literals match %d + %d = %d' % (n_prod, n_lab, n_prod + n_lab))

# Self-test: count-literal guard must fail when m0/index.html has mismatched count literals.
if Path('m0/index.html').is_file() and Path('rijul-kalra/index.html').is_file():
    with tempfile.TemporaryDirectory(prefix='c6-m0-counts-') as tmp:
        troot = Path(tmp)
        (troot / 'm0').mkdir()
        (troot / 'rijul-kalra').mkdir()
        (troot / 'index.html').write_text(index_html)
        m0_live = Path('m0/index.html').read_text()
        (troot / 'm0' / 'index.html').write_text(m0_live)
        (troot / 'rijul-kalra' / 'index.html').write_text(Path('rijul-kalra/index.html').read_text())
        ok_counts = check_count_literals(troot, n_prod, n_lab)
        (troot / 'm0' / 'index.html').write_text(m0_live.replace('Browse all %d products</a>' % (n_prod + n_lab), 'Browse all 9 products</a>', 1))
        bad_body = check_count_literals(troot, n_prod, n_lab)
        (troot / 'm0' / 'index.html').write_text(m0_live.replace('Browse all %d products \u2192' % (n_prod + n_lab), 'Browse all 9 products \u2192', 1))
        bad_nav = check_count_literals(troot, n_prod, n_lab)
    if ok_counts == [] and any('m0/index.html' in e for e in bad_body) and any('m0/index.html' in e for e in bad_nav):
        pass_('count-literal self-test: m0/index.html with mismatched body or nav counts fails; live counts pass')
    else:
        fail_('count-literal self-test failed: ok=%r bad_body=%r bad_nav=%r' % (ok_counts, bad_body, bad_nav))
else:
    fail_('count-literal self-test skipped: m0/index.html or rijul-kalra/index.html is missing')

print()
if fail == 0:
    print('  homepage product rows agree with data/products.json')
    sys.exit(0)
sys.exit(1)
