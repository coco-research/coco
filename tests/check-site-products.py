#!/usr/bin/env python3
"""Assert product rows are complete (homepage, /products/, /lab/, release feed),
the two-group 2 + 8 = 10 contract holds, Voice meetings copy names macOS 14.4,
shared nav/drawer and footer product lists match across all 14 pages, count
literals agree, stage labels match the /lab/ key, and a11y guards hold.

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
if (len(shipped), len(lab)) == (2, 8):
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

# ---- AC-14: C6 footer parity for Products and In the lab <ul> columns across all 14 pages ----
foot_re = re.compile(r'<footer class="foot".*?</footer>', re.S)
foot_col_res = (
    ('Products', re.compile(r'<div><h2>Products</h2><ul>.*?</ul></div>', re.S)),
    ('In the lab', re.compile(r'<div><h2>In the lab</h2><ul>.*?</ul></div>', re.S)),
)


def _foot_product_cols(text):
    fm = foot_re.search(text)
    if not fm:
        return None
    foot_html = fm.group(0)
    cols = []
    for _, col_re in foot_col_res:
        cm = col_re.search(foot_html)
        if not cm:
            return None
        cols.append(cm.group(0))
    return tuple(cols)


def check_c6_footer_products(root, ref_cols):
    errs = []
    checked = 0
    if not ref_cols:
        return ['reference footer Products / In the lab columns missing'], 0
    for page_p in sorted(root.glob('*/index.html')):
        ptxt = page_p.read_text()
        if '<meta http-equiv="refresh"' in ptxt:
            continue
        if _foot_product_cols(ptxt) == ref_cols:
            checked += 1
        else:
            errs.append('%s: footer Products / In the lab lists differ from generated footer' % page_p)
    if checked != 14:
        errs.append('expected 14 top-level pages with matching footer product lists, verified %d' % checked)
    m0_path = root / 'm0' / 'index.html'
    if not m0_path.is_file():
        errs.append('m0/index.html is missing for footer parity check')
    else:
        m0_txt = m0_path.read_text()
        m_foot = re.search(r'<!-- products:foot:start -->\s*(.*?)\s*<!-- products:foot:end -->', m0_txt, re.S)
        if not m_foot:
            errs.append('m0/index.html missing products:foot markers for footer parity check')
        elif _foot_product_cols(m_foot.group(1)) != ref_cols:
            errs.append('m0/index.html products:foot Products / In the lab lists differ from generated footer')
    return errs, checked


ref_foot_cols = _foot_product_cols(products_html)
c6_foot_errs, foot_checked = check_c6_footer_products(Path('.'), ref_foot_cols)
if c6_foot_errs:
    for err in c6_foot_errs:
        fail_(err)
else:
    pass_('AC-14: all %d top-level */index.html pages match generated footer Products and In the lab lists' % foot_checked)

# Self-test: drifted footer Products or In the lab column must fail; matching footer passes.
with tempfile.TemporaryDirectory(prefix='c6-foot-check-') as tmp:
    troot = Path(tmp)
    for page_p in sorted(Path('.').glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        dst = troot / page_p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(page_p.read_text())
    ok_foot, _ = check_c6_footer_products(troot, ref_foot_cols)
    orig_rk = (troot / 'rijul-kalra' / 'index.html').read_text()
    (troot / 'rijul-kalra' / 'index.html').write_text(orig_rk.replace('<li><a href="../voice/">Coco Voice</a></li>', '<li><a href="../voice/">Voice</a></li>', 1))
    bad_prod_foot, _ = check_c6_footer_products(troot, ref_foot_cols)
    (troot / 'rijul-kalra' / 'index.html').write_text(orig_rk.replace('<li><a href="../aloomannu/">Aloo Mannu</a></li>', '', 1))
    bad_lab_foot, _ = check_c6_footer_products(troot, ref_foot_cols)
if (
    ok_foot == []
    and any('rijul-kalra/index.html' in e for e in bad_prod_foot)
    and any('rijul-kalra/index.html' in e for e in bad_lab_foot)
):
    pass_('AC-14 self-test: drifted footer Products or In the lab list fails; matching footers pass')
else:
    fail_('AC-14 self-test failed: ok=%r bad_prod=%r bad_lab=%r' % (ok_foot, bad_prod_foot, bad_lab_foot))

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

# ---- AC-1 / AC-2: single stage key on /lab/ governs every lab-group chip/badge ----
STAGE_EXPECTED = {
    'Early preview': ('source', 'sh-ring'),
    'Source available': ('source', 'sh-ring'),
    'Archived': ('archived', 'sh-bar'),
    'Private beta': ('beta', 'sh-sq'),
    'Private, in the lab': ('lab', 'sh-dia'),
}


def _stage_base(text):
    return text.split(' \u00b7 ', 1)[0].strip()


def check_stage_labels_and_key(root, catalog_data, pub_specs, lab_specs):
    errs = []
    lab_p = root / 'lab' / 'index.html'
    prod_p = root / 'products' / 'index.html'
    wn_p = root / 'whats-new' / 'index.html'
    for rel, p in (('lab/index.html', lab_p), ('products/index.html', prod_p), ('whats-new/index.html', wn_p)):
        if not p.is_file():
            errs.append('%s is missing for stage-label check' % rel)
    if errs:
        return errs

    lab_txt = lab_p.read_text()
    key_sec = re.search(r'<dl class="facts-grid" aria-label="Stage key">(.*?)</dl>', lab_txt, re.S)
    if not key_sec:
        return ['lab/index.html is missing <dl class="facts-grid" aria-label="Stage key">']
    key_rows = re.findall(
        r'<dt data-stage="([^"]+)"><span class="sh ([^"]+)" aria-hidden="true"></span>([^<]+)</dt>',
        key_sec.group(1),
    )
    key_map = {label.strip(): (skey, shape) for skey, shape, label in key_rows}
    if len(key_rows) != len(key_map) or not key_map:
        errs.append('lab/index.html stage key has duplicate or missing <dt> entries: %r' % (key_rows,))
    if key_map != STAGE_EXPECTED:
        errs.append('lab/index.html stage key drifted: got %r, expected %r' % (key_map, STAGE_EXPECTED))

    sub_m = re.search(r'<p class="sec-sub">(\w+) labels, used the same way on every page\.</p>', lab_txt)
    want_word = _word(len(key_rows), cap=True)
    if not sub_m or sub_m.group(1) != want_word:
        errs.append('lab/index.html stage key count word drifted: got %r, expected %r' % (sub_m.group(1) if sub_m else None, want_word))

    shipped_ids = {r['id'] for r in catalog_data.get('products', [])}
    lab_ids = {r['id'] for r in catalog_data.get('lab', [])}
    card_pat = re.compile(
        r'<article class="dir-card"[^>]*id="p-([^"]+)"[^>]*>.*?'
        r'<span class="stage-chip dir-stage" data-stage="([^"]+)"><span class="sh ([^"]+)" aria-hidden="true"></span>([^<]+)</span>',
        re.S,
    )
    card_labels = {}
    for page_rel, page_txt, expect_ids in (
        ('products/index.html', prod_p.read_text(), shipped_ids | lab_ids),
        ('lab/index.html', lab_txt, lab_ids),
    ):
        found = {}
        for pid, dstage, shape, label in card_pat.findall(page_txt):
            label = label.strip()
            found[pid] = (dstage, shape, label)
            if pid in shipped_ids:
                if dstage != 'released' or shape != 'sh-dot' or not label.startswith('Available now'):
                    errs.append('%s %s: product-group chip drifted (%r, %r, %r)' % (page_rel, pid, dstage, shape, label))
            else:
                base = _stage_base(label)
                if base not in key_map:
                    errs.append('%s %s: stage label %r is not in the /lab/ key' % (page_rel, pid, label))
                else:
                    want_key, want_shape = key_map[base]
                    if (dstage, shape) != (want_key, want_shape):
                        errs.append('%s %s: chip (%r, %r) disagrees with key %r for %r' % (page_rel, pid, dstage, shape, (want_key, want_shape), base))
                prev = card_labels.get(pid)
                if prev is not None and prev != base:
                    errs.append('%s %s: card label %r disagrees with %r' % (page_rel, pid, base, prev))
                card_labels[pid] = base
        if set(found) != expect_ids:
            errs.append('%s: card set drifted: got %r, expected %r' % (page_rel, sorted(found), sorted(expect_ids)))
        stage_words = sorted(set(key_map) | {'Released', 'Available now'})
        for act_m in re.finditer(r'<div class="dir-act">(.*?)</div>', page_txt, re.S):
            act_text = re.sub(r'<[^>]+>', ' ', act_m.group(1)).lower()
            for word in stage_words:
                if word.lower() in act_text:
                    errs.append('%s: card action link carries stage word %r' % (page_rel, word))

    wn_txt = wn_p.read_text()
    wn_chips = re.findall(
        r'<span class="stage-chip" data-stage="([^"]+)"><span class="sh ([^"]+)" aria-hidden="true"></span>([^<]+)</span>',
        wn_txt,
    )
    if not wn_chips:
        errs.append('whats-new/index.html: no stage chips found')
    for dstage, shape, label in wn_chips:
        base = _stage_base(label)
        if base == 'Released':
            if (dstage, shape) != ('released', 'sh-dot'):
                errs.append('whats-new/index.html: Released chip drifted (%r, %r)' % (dstage, shape))
        elif base not in key_map:
            errs.append('whats-new/index.html: stage chip %r is not in the /lab/ key' % label)
        elif (dstage, shape) != key_map[base]:
            errs.append('whats-new/index.html: chip (%r, %r) disagrees with key %r for %r' % (dstage, shape, key_map[base], base))

    specs_all = dict(pub_specs)
    specs_all.update(lab_specs.get('lab', {}))
    hero_re = re.compile(r'<span class="p-badge" data-kind="stage" data-stage="([^"]+)">([^<]+)</span>')
    stage_re = re.compile(r'<span class="stage-badge stage-chip[^"]*" data-stage="([^"]+)">([^<]+)</span>')
    for row in catalog_data.get('products', []) + catalog_data.get('lab', []):
        pid = row['id']
        slug = row['page'].rstrip('/')
        page_p = root / slug / 'index.html'
        if not page_p.is_file():
            errs.append('%s/index.html is missing for stage check' % slug)
            continue
        ptxt = page_p.read_text()
        hm, sm = hero_re.search(ptxt), stage_re.search(ptxt)
        if not hm or not sm:
            errs.append('%s/index.html is missing hero stage badge or stage-card chip' % slug)
            continue
        h_stage, h_label = hm.group(1), hm.group(2).strip()
        s_stage, s_label = sm.group(1), sm.group(2).strip()
        if pid in shipped_ids:
            if h_stage != 'released' or s_stage != 'released' or not h_label.startswith('Available now') or s_label != 'Released':
                errs.append('%s/index.html: product-group badges drifted (%r/%r, %r/%r)' % (slug, h_stage, h_label, s_stage, s_label))
            continue
        spec_st = specs_all.get(pid, {}).get('stage', {})
        spec_base = _stage_base(spec_st.get('chip', ''))
        if spec_base not in key_map:
            errs.append('spec %s: stage.chip %r is not in the /lab/ key' % (pid, spec_st.get('chip')))
        elif spec_st.get('cls') != key_map[spec_base][0]:
            errs.append('spec %s: stage.cls %r != key %r for %r' % (pid, spec_st.get('cls'), key_map[spec_base][0], spec_base))
        for where, dstage, label in (('hero badge', h_stage, h_label), ('stage card', s_stage, s_label)):
            base = _stage_base(label)
            if base not in key_map:
                errs.append('%s/index.html %s: label %r is not in the /lab/ key' % (slug, where, label))
            else:
                if dstage != key_map[base][0]:
                    errs.append('%s/index.html %s: data-stage %r != key %r for %r' % (slug, where, dstage, key_map[base][0], base))
                if pid in card_labels and base != card_labels[pid]:
                    errs.append('%s/index.html %s: label %r disagrees with card label %r' % (slug, where, base, card_labels[pid]))
    return errs


specs_lab = json.loads(Path('data/product-pages-lab.json').read_text())
stage_errs = check_stage_labels_and_key(Path('.'), data, specs_public, specs_lab)
if stage_errs:
    for err in stage_errs:
        fail_(err)
else:
    pass_('AC-1 / AC-2: all lab stage chips, page badges, specs, and /lab/ key agree (5 labels)')

# Self-test: stage-label guard fails on sixth label, shape/key mismatch, card/page mismatch, or key count drift.
with tempfile.TemporaryDirectory(prefix='r1a-stages-') as tmp:
    troot = Path(tmp)
    for rel in (
        'lab/index.html', 'products/index.html', 'whats-new/index.html',
        *[row['page'].rstrip('/') + '/index.html' for row in shipped + lab],
    ):
        dst = troot / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(Path(rel).read_text())
    ok_stage = check_stage_labels_and_key(troot, data, specs_public, specs_lab)

    # 1. Sixth label on jev-use card
    orig_lab = (troot / 'lab' / 'index.html').read_text()
    (troot / 'lab' / 'index.html').write_text(
        orig_lab.replace(
            '<span class="sh sh-ring" aria-hidden="true"></span>Source available</span><span class="lic-chip" data-open="true">Apache-2.0 \u00b7 Open source</span></div>\n          <h3 class="dir-name">jev-use',
            '<span class="sh sh-ring" aria-hidden="true"></span>Pre-alpha</span><span class="lic-chip" data-open="true">Apache-2.0 \u00b7 Open source</span></div>\n          <h3 class="dir-name">jev-use',
        )
    )
    bad_sixth = check_stage_labels_and_key(troot, data, specs_public, specs_lab)

    # 2. Shape mismatch on Archived chip
    (troot / 'lab' / 'index.html').write_text(orig_lab.replace('data-stage="archived"><span class="sh sh-bar"', 'data-stage="archived"><span class="sh sh-ring"', 1))
    bad_shape = check_stage_labels_and_key(troot, data, specs_public, specs_lab)

    # 3. Wrong key count word
    (troot / 'lab' / 'index.html').write_text(orig_lab.replace('Five labels, used the same way', 'Four labels, used the same way', 1))
    bad_word = check_stage_labels_and_key(troot, data, specs_public, specs_lab)

    # 4. Card action link carrying a stage word
    (troot / 'lab' / 'index.html').write_text(orig_lab.replace('Read more<span class="sr-only"> about Coco M0', 'Private, in the lab<span class="sr-only"> Coco M0', 1))
    bad_act = check_stage_labels_and_key(troot, data, specs_public, specs_lab)
    (troot / 'lab' / 'index.html').write_text(orig_lab)

    # 5. Card/page label disagreement on Heliopause
    orig_helio = (troot / 'heliopause' / 'index.html').read_text()
    (troot / 'heliopause' / 'index.html').write_text(orig_helio.replace('Early preview \u00b7 v0.7.3', 'Source available \u00b7 v0.7.3', 1))
    bad_page = check_stage_labels_and_key(troot, data, specs_public, specs_lab)
if (
    ok_stage == []
    and any('not in the /lab/ key' in e for e in bad_sixth)
    and any('disagrees with key' in e for e in bad_shape)
    and any('count word drifted' in e for e in bad_word)
    and any('card action link carries stage word' in e for e in bad_act)
    and any('disagrees with card label' in e for e in bad_page)
):
    pass_('stage-label self-test: sixth label, shape mismatch, key count drift, action stage word, and card/page mismatch all fail')
else:
    fail_('stage-label self-test failed: ok=%r sixth=%r shape=%r word=%r act=%r page=%r' % (ok_stage, bad_sixth, bad_shape, bad_word, bad_act, bad_page))

# ---- AC-3: every <div> with aria-label also carries a role across all 14 pages + index.html ----
div_aria_re = re.compile(r'<div\b[^>]*\baria-label="[^"]*"[^>]*>', re.S)


def check_labelled_divs(root):
    errs = []
    pages = []
    idx_p = root / 'index.html'
    if idx_p.is_file():
        pages.append(idx_p)
    else:
        errs.append('index.html is missing for labelled-div role check')
    for page_p in sorted(root.glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        pages.append(page_p)
    if len(pages) != 15:
        errs.append('expected 15 site HTML pages for labelled-div check, found %d' % len(pages))
    for page_p in pages:
        txt = page_p.read_text()
        for m in div_aria_re.finditer(txt):
            tag = m.group(0)
            if not re.search(r'\brole="[^"]+"', tag):
                errs.append('%s: role-less labelled <div>: %s' % (page_p, tag))
    return errs, len(pages)


div_errs, div_checked = check_labelled_divs(Path('.'))
if div_errs:
    for err in div_errs:
        fail_(err)
else:
    pass_('AC-3: every <div aria-label=...> across all %d pages has a role' % div_checked)

# Self-test: a role-less <div aria-label=...> must fail.
with tempfile.TemporaryDirectory(prefix='r1b-divs-') as tmp:
    troot = Path(tmp)
    (troot / 'index.html').write_text(index_html)
    for page_p in sorted(Path('.').glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        dst = troot / page_p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(page_p.read_text())
    ok_divs, _ = check_labelled_divs(troot)
    orig_coco = (troot / 'coco' / 'index.html').read_text()
    (troot / 'coco' / 'index.html').write_text(orig_coco.replace('role="group" aria-label="Stage and licence"', 'aria-label="Stage and licence"', 1))
    bad_div, _ = check_labelled_divs(troot)
if ok_divs == [] and any('role-less labelled <div>' in e for e in bad_div):
    pass_('AC-3 self-test: role-less labelled <div> fails; all live pages pass')
else:
    fail_('AC-3 self-test failed: ok=%r bad=%r' % (ok_divs, bad_div))

# ---- AC-5: lists, card heading levels, aria-current placement, and .sn-m-priv diamond ----
tag_aria_cur_re = re.compile(r'<(\w+)\b([^>]*\baria-current="([^"]+)"[^>]*)>', re.S)


def check_a11y_structure_and_current(root, catalog_data):
    errs = []
    for rel, expect_cards in (('products/index.html', 10), ('lab/index.html', 8)):
        p = root / rel
        if not p.is_file():
            errs.append('%s is missing for AC-5 check' % rel)
            continue
        txt = p.read_text()
        if 'role="list"' in txt and 'role="listitem"' not in txt:
            errs.append('%s has role="list" without role="listitem" children' % rel)
        if '<h2 class="dir-name">' in txt:
            errs.append('%s uses <h2 class="dir-name"> instead of <h3>' % rel)
        h3_count = txt.count('<h3 class="dir-name">')
        if h3_count != expect_cards:
            errs.append('%s has %d <h3 class="dir-name"> headings, expected %d' % (rel, h3_count, expect_cards))

    idx_p = root / 'index.html'
    if not idx_p.is_file():
        errs.append('index.html is missing for AC-5 check')
    else:
        idx_txt = idx_p.read_text()
        if re.search(r'<button\b[^>]*\baria-current=', idx_txt, re.S):
            errs.append('index.html has aria-current on a <button>')
        if 'aria-current="page"' in idx_txt:
            errs.append('index.html unexpectedly carries aria-current="page"')
        if 'sn-m-priv"><span class="sh sh-sq"' in idx_txt or 'sn-m-priv"><span class="sh sh-dia"' not in idx_txt:
            errs.append('index.html .sn-m-priv marker must use sh-dia (not sh-sq)')

    product_slugs = {row['page'].rstrip('/') for row in catalog_data.get('products', []) + catalog_data.get('lab', [])}
    checked = 0
    for page_p in sorted(root.glob('*/index.html')):
        txt = page_p.read_text()
        if '<meta http-equiv="refresh"' in txt:
            continue
        checked += 1
        slug = page_p.parent.name
        if re.search(r'<button\b[^>]*\baria-current=', txt, re.S):
            errs.append('%s has aria-current on a <button>' % page_p)
        hits = tag_aria_cur_re.findall(txt)
        want_href = '../%s/' % slug
        if len(hits) != 2:
            errs.append('%s has %d aria-current elements, expected 2' % (page_p, len(hits)))
        for tag, attrs, val in hits:
            if tag != 'a' or val != 'page':
                errs.append('%s has aria-current=%r on <%s>, expected <a aria-current="page">' % (page_p, val, tag))
            hm = re.search(r'\bhref="([^"]+)"', attrs)
            if not hm or hm.group(1) != want_href:
                errs.append('%s aria-current link href=%r, expected %r' % (page_p, hm.group(1) if hm else None, want_href))
        if slug == 'products':
            if '<div class="sn-m-foot"><a href="../products/" aria-current="page">Browse all ' not in txt:
                errs.append('products/index.html missing aria-current="page" on dropdown foot Browse all link')
            if '<a class="sn-m-item sn-d-all" href="../products/" aria-current="page">' not in txt:
                errs.append('products/index.html missing aria-current="page" on drawer Browse all link')
            if 'sn-m-priv"><span class="sh sh-sq"' in txt or 'sn-m-priv"><span class="sh sh-dia"' not in txt:
                errs.append('products/index.html .sn-m-priv marker must use sh-dia (not sh-sq)')
        elif slug in product_slugs:
            classes = [re.search(r'\bclass="([^"]+)"', attrs).group(1) if re.search(r'\bclass="([^"]+)"', attrs) else '' for _, attrs, _ in hits]
            if classes != ['sn-m-item', 'sn-m-item']:
                errs.append('%s aria-current product link classes=%r, expected two sn-m-item links' % (page_p, classes))
    if checked != 14:
        errs.append('expected 14 top-level pages for AC-5 check, verified %d' % checked)
    return errs, checked


a11y_errs, a11y_checked = check_a11y_structure_and_current(Path('.'), data)
if a11y_errs:
    for err in a11y_errs:
        fail_(err)
else:
    pass_('AC-5: /products/ and /lab/ lists/headings, .sn-m-priv diamond, and aria-current across all %d pages hold' % a11y_checked)

# ---- AC-17 / AC-18: private lab pages (m0, hermes, teams-ng, aloomannu) hero pill shape & stage prose ----
pill_re = re.compile(r'<span class="p-static-pill"><span class="sh ([^"]+)" aria-hidden="true"></span>([^<]+)</span>')
stage_fact_re = re.compile(r'<dt>Stage</dt><dd>([^<]+)</dd>')


def check_private_stage_prose(root, lab_specs):
    errs = []
    private_specs = lab_specs.get('lab', {})
    if sorted(private_specs) != ['aloomannu', 'hermes', 'm0', 'teams-ng']:
        errs.append('unexpected private lab specs set: %r' % sorted(private_specs))
    for pid, spec in sorted(private_specs.items()):
        slug = spec.get('slug', pid)
        page_label = _stage_base(spec.get('stage', {}).get('chip', ''))
        if page_label not in STAGE_EXPECTED:
            errs.append('private spec %s: stage.chip %r is not in STAGE_EXPECTED' % (pid, page_label))
            continue
        want_shape = STAGE_EXPECTED[page_label][1]
        ta_label = str(spec.get('try_above', {}).get('label', ''))
        if not ta_label.startswith(page_label):
            errs.append('spec %s: try_above.label %r does not start with key label %r' % (pid, ta_label, page_label))
        page_p = root / slug / 'index.html'
        if not page_p.is_file():
            errs.append('%s/index.html is missing for AC-17/AC-18 check' % slug)
            continue
        txt = page_p.read_text()
        pm = pill_re.search(txt)
        if not pm:
            errs.append('%s/index.html is missing .p-static-pill with shape glyph' % slug)
        else:
            got_shape, pill_text = pm.group(1), pm.group(2).strip()
            if got_shape != want_shape:
                errs.append('%s/index.html .p-static-pill shape %r != expected %r for %r' % (slug, got_shape, want_shape, page_label))
            for lbl in STAGE_EXPECTED:
                if lbl.lower() in pill_text.lower() and lbl != page_label:
                    errs.append('%s/index.html hero pill %r mentions other key label %r (expected %r)' % (slug, pill_text, lbl, page_label))
            if not pill_text.startswith(page_label):
                errs.append('%s/index.html hero pill %r does not start with %r' % (slug, pill_text, page_label))
            if pill_text != ta_label:
                errs.append('%s/index.html hero pill %r != spec try_above.label %r' % (slug, pill_text, ta_label))
        fm = stage_fact_re.search(txt)
        if not fm:
            errs.append('%s/index.html is missing <dt>Stage</dt><dd> fact' % slug)
        else:
            fact_text = fm.group(1).strip()
            for lbl in STAGE_EXPECTED:
                if lbl.lower() in fact_text.lower() and lbl != page_label:
                    errs.append('%s/index.html Stage fact %r mentions other key label %r (expected %r)' % (slug, fact_text, lbl, page_label))
            if page_label.lower() not in fact_text.lower():
                errs.append('%s/index.html Stage fact %r does not name key label %r' % (slug, fact_text, page_label))
    return errs


priv_prose_errs = check_private_stage_prose(Path('.'), specs_lab)
if priv_prose_errs:
    for err in priv_prose_errs:
        fail_(err)
else:
    pass_('AC-17 / AC-18: all 4 private lab pages hero pill shapes, try_above.label, and Stage facts agree with their key label')

# Self-test: mismatched pill label, Stage fact label, pill shape, or spec try_above.label must fail.
with tempfile.TemporaryDirectory(prefix='r1b-priv-prose-') as tmp:
    troot = Path(tmp)
    for slug in ('m0', 'hermes', 'teams-ng', 'aloomannu'):
        dst = troot / slug / 'index.html'
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(Path(slug, 'index.html').read_text())
    ok_priv = check_private_stage_prose(troot, specs_lab)

    orig_hermes = (troot / 'hermes' / 'index.html').read_text()
    (troot / 'hermes' / 'index.html').write_text(orig_hermes.replace('Private beta \u2014 no public download yet', 'Private, in the lab \u2014 no public download yet', 1))
    bad_pill_txt = check_private_stage_prose(troot, specs_lab)
    (troot / 'hermes' / 'index.html').write_text(orig_hermes)

    orig_aloo = (troot / 'aloomannu' / 'index.html').read_text()
    (troot / 'aloomannu' / 'index.html').write_text(orig_aloo.replace('Private, in the lab, in daily use inside Coco Research', 'Private beta, in daily lab use', 1))
    bad_fact_txt = check_private_stage_prose(troot, specs_lab)
    (troot / 'aloomannu' / 'index.html').write_text(orig_aloo.replace('<span class="p-static-pill"><span class="sh sh-dia"', '<span class="p-static-pill"><span class="sh sh-sq"', 1))
    bad_pill_shape = check_private_stage_prose(troot, specs_lab)
    (troot / 'aloomannu' / 'index.html').write_text(orig_aloo)

    bad_specs = json.loads(json.dumps(specs_lab))
    bad_specs['lab']['m0']['try_above']['label'] = 'Private, in the lab \u2014 no public download yet'
    bad_spec_ta = check_private_stage_prose(troot, bad_specs)

    orig_m0_p = (troot / 'm0' / 'index.html').read_text()
    (troot / 'm0' / 'index.html').write_text(orig_m0_p.replace('Private beta, used daily \u2014 no public download yet', 'Private beta, drifted \u2014 no public download yet', 1))
    bad_m0_drift = check_private_stage_prose(troot, specs_lab)
    (troot / 'm0' / 'index.html').write_text(orig_m0_p)
if (
    ok_priv == []
    and any('hermes/index.html hero pill' in e for e in bad_pill_txt)
    and any('aloomannu/index.html Stage fact' in e for e in bad_fact_txt)
    and any('aloomannu/index.html .p-static-pill shape' in e for e in bad_pill_shape)
    and any('spec m0: try_above.label' in e for e in bad_spec_ta)
    and any('m0/index.html hero pill' in e and 'spec try_above.label' in e for e in bad_m0_drift)
):
    pass_('AC-17 / AC-18 self-test: mismatched pill text, Stage fact, pill shape, spec try_above.label, and m0 pill drift all fail')
else:
    fail_('AC-17 / AC-18 self-test failed: ok=%r pill=%r fact=%r shape=%r spec=%r m0_drift=%r' % (ok_priv, bad_pill_txt, bad_fact_txt, bad_pill_shape, bad_spec_ta, bad_m0_drift))

# Self-test: button aria-current, h2 card title, role=list, missing m0 aria-current, wrong product href, and sh-sq priv marker all fail.
with tempfile.TemporaryDirectory(prefix='r1b-a11y-') as tmp:
    troot = Path(tmp)
    (troot / 'index.html').write_text(index_html)
    for page_p in sorted(Path('.').glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        dst = troot / page_p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(page_p.read_text())
    ok_a11y, _ = check_a11y_structure_and_current(troot, data)

    orig_prod = (troot / 'products' / 'index.html').read_text()
    (troot / 'products' / 'index.html').write_text(orig_prod.replace('data-products-trigger', 'data-products-trigger aria-current="page"', 1))
    bad_btn, _ = check_a11y_structure_and_current(troot, data)
    (troot / 'products' / 'index.html').write_text(orig_prod.replace('<h3 class="dir-name">', '<h2 class="dir-name">', 1))
    bad_h2, _ = check_a11y_structure_and_current(troot, data)
    (troot / 'products' / 'index.html').write_text(orig_prod.replace('sn-m-priv"><span class="sh sh-dia"', 'sn-m-priv"><span class="sh sh-sq"'))
    bad_priv, _ = check_a11y_structure_and_current(troot, data)
    (troot / 'products' / 'index.html').write_text(orig_prod)

    orig_lab2 = (troot / 'lab' / 'index.html').read_text()
    (troot / 'lab' / 'index.html').write_text(orig_lab2.replace('<div class="dir-grid" role="group"', '<div class="dir-grid" role="list"', 1))
    bad_list, _ = check_a11y_structure_and_current(troot, data)
    (troot / 'lab' / 'index.html').write_text(orig_lab2)

    orig_m0 = (troot / 'm0' / 'index.html').read_text()
    (troot / 'm0' / 'index.html').write_text(orig_m0.replace(' aria-current="page"', ''))
    bad_m0_cur, _ = check_a11y_structure_and_current(troot, data)
    (troot / 'm0' / 'index.html').write_text(orig_m0)

    orig_voice = (troot / 'voice' / 'index.html').read_text()
    (troot / 'voice' / 'index.html').write_text(orig_voice.replace('href="../voice/" aria-current="page"', 'href="../coco/" aria-current="page"', 1))
    bad_href, _ = check_a11y_structure_and_current(troot, data)
if (
    ok_a11y == []
    and any('aria-current on a <button>' in e for e in bad_btn)
    and any('<h2 class="dir-name">' in e for e in bad_h2)
    and any('sh-dia' in e for e in bad_priv)
    and any('role="list" without role="listitem"' in e for e in bad_list)
    and any('m0/index.html has 0 aria-current' in e for e in bad_m0_cur)
    and any("expected '../voice/'" in e for e in bad_href)
):
    pass_('AC-5 self-test: button aria-current, h2 card, sh-sq priv marker, role=list, missing m0 aria-current, and wrong href all fail')
else:
    fail_('AC-5 self-test failed: ok=%r btn=%r h2=%r priv=%r list=%r m0=%r href=%r' % (ok_a11y, bad_btn, bad_h2, bad_priv, bad_list, bad_m0_cur, bad_href))

# ---- AC-6, AC-7, AC-8, AC-9: anchored flags, skip-link rewrite, theme-color, canonical icons ----
CANONICAL_ICONS = {
    '/assets/site/favicon.svg',
    '/assets/site/favicon-32.png',
    '/apple-touch-icon.png',
    '/assets/site/site.webmanifest',
}
icon_link_re = re.compile(r'<link\b([^>]*\brel="(?:icon|apple-touch-icon|manifest)"[^>]*)>', re.S)
theme_meta_re = re.compile(r'<meta\b([^>]*\bname="theme-color"[^>]*)>', re.S)


def check_head_flags_theme_icons(root):
    errs = []
    pages = []
    idx_p = root / 'index.html'
    if idx_p.is_file():
        pages.append(idx_p)
    else:
        errs.append('index.html is missing for head/icons check')
    for page_p in sorted(root.glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        pages.append(page_p)
    if len(pages) != 15:
        errs.append('expected 15 site HTML pages for head/icons check, found %d' % len(pages))

    for page_p in pages:
        txt = page_p.read_text()
        head_m = re.search(r'<head>(.*?)</head>', txt, re.S)
        if not head_m:
            errs.append('%s is missing <head>...</head>' % page_p)
            continue
        head_txt = head_m.group(1)
        html_tag = re.search(r'<html\b[^>]*>', txt)
        locked_dark = bool(html_tag and 'data-theme-locked=' in html_tag.group(0))

        # AC-6: extract and test shipped motion=off and (for themed pages) theme= regexes
        mp = re.search(r'/([^/\n]+)/\.test\(location\.search\)', head_txt)
        if not mp:
            errs.append('%s head script is missing motion=off regex' % page_p)
        else:
            mre = re.compile(mp.group(1))
            for ok_q in ('?motion=off', '?a=1&motion=off', '?motion=off&theme=dark'):
                if not mre.search(ok_q):
                    errs.append('%s motion regex %r failed to match %r' % (page_p, mp.group(1), ok_q))
            for bad_q in ('?motion=office', '?xmotion=off'):
                if mre.search(bad_q):
                    errs.append('%s motion regex %r matched unanchored %r' % (page_p, mp.group(1), bad_q))
        if not locked_dark:
            tp = re.search(r'/([^/\n]+)/\.exec\(location\.search\)', head_txt)
            if not tp:
                errs.append('%s head script is missing theme= regex' % page_p)
            else:
                tre = re.compile(tp.group(1))
                for ok_q, want in (('?theme=light', 'light'), ('?a=1&theme=dark', 'dark'), ('?motion=off&theme=dark&x=1', 'dark')):
                    mt = tre.search(ok_q)
                    if not mt or mt.group(1) != want:
                        errs.append('%s theme regex %r failed to extract %r from %r' % (page_p, tp.group(1), want, ok_q))
                for bad_q in ('?theme=darkblue', '?theme=lightest'):
                    if tre.search(bad_q):
                        errs.append('%s theme regex %r matched unanchored %r' % (page_p, tp.group(1), bad_q))

        # AC-7: static ?motion=off skip link in body + exact head selector and URLSearchParams rewrite
        body_m = re.search(r'<body\b[^>]*>(.*)</body>', txt, re.S)
        body_txt = body_m.group(1) if body_m else ''
        if not re.search(r'<a\b[^>]*class="[^"]*\bskip\b[^"]*"[^>]*href="\?motion=off"', body_txt):
            errs.append('%s body is missing static <a class="skip..." href="?motion=off"> fallback' % page_p)
        if 'a.skip[href="?motion=off"]' not in head_txt:
            errs.append('%s head script is missing exact selector a.skip[href="?motion=off"]' % page_p)
        if 'URLSearchParams(location.search)' not in head_txt or "p.set('motion', 'off')" not in head_txt:
            errs.append('%s head script is missing URLSearchParams skip-link rewrite' % page_p)

        # AC-8: theme-color meta tags (locked-dark single #03050b vs themed light/dark pair)
        tmetas = []
        for attrs in theme_meta_re.findall(head_txt):
            cm = re.search(r'\bcontent="([^"]+)"', attrs)
            mm = re.search(r'\bmedia="([^"]+)"', attrs)
            tmetas.append((cm.group(1) if cm else '', mm.group(1) if mm else ''))
        if locked_dark:
            if tmetas != [('#03050b', '')]:
                errs.append('%s (locked dark) theme-color metas=%r, expected single #03050b with no media' % (page_p, tmetas))
        else:
            want_pair = [('#f3f2ee', '(prefers-color-scheme: light)'), ('#03050b', '(prefers-color-scheme: dark)')]
            if tmetas != want_pair:
                errs.append('%s (themed) theme-color metas=%r, expected %r' % (page_p, tmetas, want_pair))

        # AC-9: root-absolute canonical icon + manifest links
        hrefs = []
        for attrs in icon_link_re.findall(head_txt):
            hm = re.search(r'\bhref="([^"]+)"', attrs)
            hrefs.append(hm.group(1) if hm else '')
        if set(hrefs) != CANONICAL_ICONS or len(hrefs) != len(CANONICAL_ICONS):
            errs.append('%s icon/manifest hrefs=%r, expected canonical %r' % (page_p, hrefs, sorted(CANONICAL_ICONS)))

    for extra_rel in ('coco/guardrails/index.html', 'guides/manage-multiple-ai-coding-agents/index.html'):
        ep = root / extra_rel
        if ep.is_file():
            eh = re.search(r'<head>(.*?)</head>', ep.read_text(), re.S)
            ehrefs = [re.search(r'\bhref="([^"]+)"', a).group(1) for a in icon_link_re.findall(eh.group(1)) if re.search(r'\bhref="([^"]+)"', a)] if eh else []
            if set(ehrefs) != CANONICAL_ICONS or len(ehrefs) != len(CANONICAL_ICONS):
                errs.append('%s icon/manifest hrefs=%r, expected canonical %r' % (extra_rel, ehrefs, sorted(CANONICAL_ICONS)))
    return errs, len(pages)


head_errs, head_checked = check_head_flags_theme_icons(Path('.'))
if head_errs:
    for err in head_errs:
        fail_(err)
else:
    pass_('AC-6..AC-9: anchored flags, URLSearchParams skip-link rewrite, theme-color, and canonical icons hold across all %d pages' % head_checked)

for dup_icon in ('assets/img/favicon.svg', 'assets/site/apple-touch-icon.png'):
    if Path(dup_icon).is_file():
        pass_('AC-9 out-of-scope guard: duplicate icon %s stays on disk' % dup_icon)
    else:
        fail_('duplicate icon %s was unexpectedly removed' % dup_icon)

# Self-test: unanchored motion/theme regex, missing skip rewrite, wrong theme-color, and relative icon all fail.
with tempfile.TemporaryDirectory(prefix='r1c-head-') as tmp:
    troot = Path(tmp)
    (troot / 'index.html').write_text(index_html)
    for page_p in sorted(Path('.').glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        dst = troot / page_p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(page_p.read_text())
    ok_head, _ = check_head_flags_theme_icons(troot)

    orig_idx = (troot / 'index.html').read_text()
    (troot / 'index.html').write_text(orig_idx.replace('motion=off(?:&|$)', 'motion=off', 1))
    bad_motion, _ = check_head_flags_theme_icons(troot)
    (troot / 'index.html').write_text(orig_idx.replace('<meta name="theme-color" content="#03050b">', '<meta name="theme-color" content="#03050b" media="(prefers-color-scheme: dark)">', 1))
    bad_locked_tc, _ = check_head_flags_theme_icons(troot)
    (troot / 'index.html').write_text(orig_idx)

    orig_p = (troot / 'products' / 'index.html').read_text()
    (troot / 'products' / 'index.html').write_text(orig_p.replace('theme=(light|dark)(?:&|$)', 'theme=(light|dark)', 1))
    bad_theme, _ = check_head_flags_theme_icons(troot)
    (troot / 'products' / 'index.html').write_text(orig_p.replace('URLSearchParams(location.search)', 'location.search', 1))
    bad_skip, _ = check_head_flags_theme_icons(troot)
    (troot / 'products' / 'index.html').write_text(orig_p.replace('<meta name="theme-color" content="#f3f2ee" media="(prefers-color-scheme: light)">\n', '', 1))
    bad_themed_tc, _ = check_head_flags_theme_icons(troot)
    (troot / 'products' / 'index.html').write_text(orig_p.replace('href="/assets/site/favicon.svg"', 'href="../assets/img/favicon.svg"', 1))
    bad_icon, _ = check_head_flags_theme_icons(troot)
    (troot / 'products' / 'index.html').write_text(orig_p)

    orig_m0_h = (troot / 'm0' / 'index.html').read_text()
    (troot / 'm0' / 'index.html').write_text(orig_m0_h.replace('a.skip[href="?motion=off"]', 'a.skip[href="?motion=no"]', 1))
    bad_sel, _ = check_head_flags_theme_icons(troot)
    (troot / 'm0' / 'index.html').write_text(orig_m0_h)
if (
    ok_head == []
    and any('matched unanchored' in e and 'motion' in e for e in bad_motion)
    and any('locked dark' in e for e in bad_locked_tc)
    and any('matched unanchored' in e and 'theme' in e for e in bad_theme)
    and any('URLSearchParams skip-link rewrite' in e for e in bad_skip)
    and any('(themed) theme-color' in e for e in bad_themed_tc)
    and any('icon/manifest hrefs' in e for e in bad_icon)
    and any('exact selector a.skip[href="?motion=off"]' in e for e in bad_sel)
):
    pass_('AC-6..AC-9 self-test: unanchored motion/theme, missing skip rewrite, selector typo, theme-color drift, and relative icon all fail')
else:
    fail_('AC-6..AC-9 self-test failed: ok=%r motion=%r locked=%r theme=%r skip=%r themed=%r icon=%r sel=%r' % (ok_head, bad_motion, bad_locked_tc, bad_theme, bad_skip, bad_themed_tc, bad_icon, bad_sel))

# ---- AC-10: footer Licence links end in /LICENSE or #licence ----
def check_licence_hrefs(root, pub_specs):
    errs = []
    for pid, spec in sorted(pub_specs.items()):
        href = str(spec.get('licence_href', ''))
        if not href:
            errs.append('spec %s: missing licence_href' % pid)
            continue
        if not (href.endswith('/LICENSE') or href.endswith('#licence')):
            errs.append('spec %s: licence_href %r does not end in /LICENSE or #licence' % (pid, href))
        slug = spec.get('slug', pid)
        page_p = root / slug / 'index.html'
        if not page_p.is_file():
            errs.append('%s/index.html is missing for licence_href check' % slug)
        elif '<li><a href="%s">Licence</a></li>' % href not in page_p.read_text():
            errs.append('%s/index.html footer missing Licence link %r' % (slug, href))
    return errs


lic_errs = check_licence_hrefs(Path('.'), specs_public)
if lic_errs:
    for err in lic_errs:
        fail_(err)
else:
    pass_('AC-10: all %d public licence_href values and footer links end in /LICENSE or #licence' % len(specs_public))

with tempfile.TemporaryDirectory(prefix='r1d-lic-') as tmp:
    troot = Path(tmp)
    for pid, spec in specs_public.items():
        slug = spec.get('slug', pid)
        dst = troot / slug / 'index.html'
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(Path(slug, 'index.html').read_text())
    ok_lic = check_licence_hrefs(troot, specs_public)
    bad_pub = json.loads(json.dumps(specs_public))
    bad_pub['signal']['licence_href'] = 'https://github.com/coco-research/coco-design-language'
    bad_lic = check_licence_hrefs(troot, bad_pub)
if ok_lic == [] and any('does not end in /LICENSE or #licence' in e for e in bad_lic):
    pass_('AC-10 self-test: repo-root licence_href without /LICENSE fails; live specs pass')
else:
    fail_('AC-10 self-test failed: ok=%r bad=%r' % (ok_lic, bad_lic))

# ---- AC-11: straight "What's new" everywhere (zero curly apostrophe or &rsquo;) ----
curly_wn_re = re.compile(r'What(?:\u2019|\\u2019|&rsquo;)s new')


def check_straight_whats_new(root):
    errs = []
    targets = []
    for rel in ('index.html', 'llms.txt', 'scripts/render-product-pages.py', 'scripts/render-site-products.py', 'scripts/render_product_shared.py'):
        p = root / rel
        if p.is_file():
            targets.append(p)
        else:
            errs.append('%s is missing for AC-11 check' % rel)
    for page_p in sorted(root.glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        targets.append(page_p)
    for p in targets:
        m = curly_wn_re.search(p.read_text())
        if m:
            errs.append('%s contains curly What\'s new (%r)' % (p, m.group(0)))
    return errs, len(targets)


wn_errs, wn_checked = check_straight_whats_new(Path('.'))
if wn_errs:
    for err in wn_errs:
        fail_(err)
else:
    pass_('AC-11: zero curly What\'s new across all %d HTML, llms.txt, and renderer files' % wn_checked)

with tempfile.TemporaryDirectory(prefix='r1d-wn-') as tmp:
    troot = Path(tmp)
    for rel in ('index.html', 'llms.txt', 'scripts/render-product-pages.py', 'scripts/render-site-products.py', 'scripts/render_product_shared.py'):
        dst = troot / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(Path(rel).read_text())
    for page_p in sorted(Path('.').glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        dst = troot / page_p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(page_p.read_text())
    ok_wn, _ = check_straight_whats_new(troot)
    orig_m0_wn = (troot / 'm0' / 'index.html').read_text()
    (troot / 'm0' / 'index.html').write_text(orig_m0_wn.replace("What's new", 'What\u2019s new', 1))
    bad_curly, _ = check_straight_whats_new(troot)
    (troot / 'm0' / 'index.html').write_text(orig_m0_wn.replace("What's new", 'What&rsquo;s new', 1))
    bad_entity, _ = check_straight_whats_new(troot)
if (
    ok_wn == []
    and any("contains curly What's new" in e for e in bad_curly)
    and any("contains curly What's new" in e for e in bad_entity)
):
    pass_('AC-11 self-test: curly apostrophe and &rsquo; in What\'s new both fail; live files pass')
else:
    fail_('AC-11 self-test failed: ok=%r curly=%r entity=%r' % (ok_wn, bad_curly, bad_entity))

# ---- AC-12 / AC-13: m0 bare .st ::before scoped to stateful chips; .links-row .link-pill kept; home Shift+Tab ----
m0_css_txt = Path('m0/index.html').read_text()
if re.search(r'(?m)^\.st::before\b', m0_css_txt):
    fail_('AC-12: m0/index.html still applies unconditional .st::before to bare match chips')
elif '.st-live::before, .st-off::before, .st-plan::before' in m0_css_txt:
    pass_('AC-12: m0/index.html scopes .st ::before box to stateful chips only (bare match chips draw no box)')
else:
    fail_('AC-12: m0/index.html stateful .st ::before rule missing')
if '.links-row .link-pill' in Path('assets/css/product.css').read_text():
    pass_('AC-12 guard: live .links-row .link-pill rule in assets/css/product.css stays intact')
else:
    fail_('AC-12 guard: .links-row .link-pill was unexpectedly removed from assets/css/product.css')
main_js_txt = Path('assets/js/main.js').read_text()
if 'function chromeAfter()' in main_js_txt and 'e.shiftKey && act && act === chromeAfter()' in main_js_txt:
    pass_('AC-13: assets/js/main.js defines chromeAfter() for Shift+Tab from footer into close chapter')
else:
    fail_('AC-13: assets/js/main.js missing chromeAfter() Shift+Tab handler')

# ---- removed claims guard: Voice "Private" phrases and SI /whats-new/ entry text ----
VOICE_REMOVED_PHRASES = (
    'Private, ' + 'on your computer',
    'Private ' + 'desktop speech',
)
SI_COUNT_PLACEHOLDERS = ('{personas}', '{departments}', '{skills}', '{commands}')


def check_removed_claims(root):
    errs = []
    targets = []
    for rel in ('data/products.json', 'data/product-pages-public.json', 'data/product-pages-lab.json', 'index.html', 'llms.txt'):
        p = root / rel
        if p.is_file():
            targets.append(p)
        else:
            errs.append('%s is missing for removed-claims check' % rel)
    for page_p in sorted(root.glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        targets.append(page_p)

    for p in targets:
        low = p.read_text().lower()
        for phrase in VOICE_REMOVED_PHRASES:
            if phrase.lower() in low:
                errs.append('%s contains removed Voice phrase %r' % (p, phrase))

    prod_p = root / 'data' / 'products.json'
    if prod_p.is_file():
        pdata = json.loads(prod_p.read_text())
        si_row = next((r for r in pdata.get('products', []) if r.get('id') == 'coco-si'), None)
        if not si_row:
            errs.append('data/products.json missing coco-si row for removed-claims check')
        else:
            si_wn = str(si_row.get('whats_new', ''))
            if 'open-core' in si_wn.lower():
                errs.append('data/products.json coco-si whats_new contains Open-core: %r' % si_wn)
            for ph in SI_COUNT_PLACEHOLDERS:
                if ph in si_wn:
                    errs.append('data/products.json coco-si whats_new contains count placeholder %r' % ph)

    wn_p = root / 'whats-new' / 'index.html'
    if wn_p.is_file():
        wn_txt = wn_p.read_text()
        si_art = re.search(r'<article class="tl-entry">(?:(?!</article>).)*?Coco Super Intelligence(?:(?!</article>).)*?</article>', wn_txt, re.S)
        if not si_art:
            errs.append('whats-new/index.html missing Coco Super Intelligence entry')
        else:
            art_html = si_art.group(0)
            if 'Released \u00b7 Open-core (Apache-2.0 core)' not in art_html:
                errs.append('whats-new/index.html Coco Super Intelligence entry lost its Open-core licence chip')
            tl_m = re.search(r'<p class="tl-line">(.*?)</p>', art_html, re.S)
            if not tl_m:
                errs.append('whats-new/index.html Coco Super Intelligence entry missing <p class="tl-line">')
            else:
                tl_txt = tl_m.group(1)
                if 'open-core' in tl_txt.lower():
                    errs.append('whats-new/index.html SI entry text contains Open-core: %r' % tl_txt)
                for num in ('493', '231', '389'):
                    if re.search(r'\b%s\b' % num, tl_txt):
                        errs.append('whats-new/index.html SI entry text contains count %s: %r' % (num, tl_txt))
    return errs, len(targets)


claim_errs, claim_checked = check_removed_claims(Path('.'))
if claim_errs:
    for err in claim_errs:
        fail_(err)
else:
    pass_('removed-claims guard: 0 removed Voice phrases across %d files; SI whats_new has no Open-core or count placeholders' % claim_checked)

with tempfile.TemporaryDirectory(prefix='voice-claims-') as tmp:
    troot = Path(tmp)
    for rel in ('data/products.json', 'data/product-pages-public.json', 'data/product-pages-lab.json', 'index.html', 'llms.txt'):
        dst = troot / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(Path(rel).read_text())
    for page_p in sorted(Path('.').glob('*/index.html')):
        if '<meta http-equiv="refresh"' in page_p.read_text():
            continue
        dst = troot / page_p
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(page_p.read_text())
    ok_claims, _ = check_removed_claims(troot)

    orig_prod_html = (troot / 'products' / 'index.html').read_text()
    (troot / 'products' / 'index.html').write_text(orig_prod_html.replace('On your computer.', VOICE_REMOVED_PHRASES[0] + '.', 1))
    bad_v1, _ = check_removed_claims(troot)
    (troot / 'products' / 'index.html').write_text(orig_prod_html)

    orig_wn_html = (troot / 'whats-new' / 'index.html').read_text()
    (troot / 'whats-new' / 'index.html').write_text(orig_wn_html.replace('Desktop speech-to-text', VOICE_REMOVED_PHRASES[1] + '-to-text', 1))
    bad_v2, _ = check_removed_claims(troot)
    (troot / 'whats-new' / 'index.html').write_text(orig_wn_html.replace('<p class="tl-line">Advisory skills', '<p class="tl-line">Open-core advisory skills 493', 1))
    bad_si_wn, _ = check_removed_claims(troot)
    (troot / 'whats-new' / 'index.html').write_text(orig_wn_html)

    orig_pj = (troot / 'data' / 'products.json').read_text()
    (troot / 'data' / 'products.json').write_text(orig_pj.replace('Advisory skills, commands and rules', 'Open-core advisory skills {personas}', 1))
    bad_si_json, _ = check_removed_claims(troot)
if (
    ok_claims == []
    and any('removed Voice phrase' in e for e in bad_v1)
    and any('removed Voice phrase' in e for e in bad_v2)
    and any('SI entry text contains Open-core' in e for e in bad_si_wn)
    and any('SI entry text contains count 493' in e for e in bad_si_wn)
    and any('coco-si whats_new contains Open-core' in e for e in bad_si_json)
    and any('count placeholder' in e for e in bad_si_json)
):
    pass_('removed-claims self-test: restored Voice phrases, SI Open-core, and count placeholders/numbers all fail')
else:
    fail_('removed-claims self-test failed: ok=%r v1=%r v2=%r si_wn=%r si_json=%r' % (ok_claims, bad_v1, bad_v2, bad_si_wn, bad_si_json))

print()
if fail == 0:
    print('  homepage product rows agree with data/products.json')
    sys.exit(0)
sys.exit(1)
