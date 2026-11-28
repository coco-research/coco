#!/usr/bin/env python3
"""Assert product rows are complete, the two-group 2 + 8 = 10 contract holds,
Voice meetings copy names macOS 14.4, and shared nav/drawer regions match.

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
    missing = [k for k in ('tag', 'description_html') if not row.get(k)]
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
        fail_('art %s is missing for %s' % (art, row.get('id', '?')))

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
alo = next((r for r in lab if r['id'] == 'aloomannu'), None)
if alo and alo['status'] == 'Private, in the lab' and 'href' not in alo and alo['page'] == 'aloomannu/':
    pass_('Aloo Mannu is in the lab as "Private, in the lab", linked to /aloomannu/, with no repository href')
else:
    fail_('Aloo Mannu row is missing or wrong')
for gone in ('status-zero', 'loops'):
    if any(r['id'] == gone for r in shipped + lab) or Path(gone).exists():
        fail_('%s is still in the data or on disk' % gone)
    else:
        pass_('%s is removed from the data and from disk' % gone)

proc = subprocess.run([sys.executable, 'scripts/render-site-products.py', '--check'], capture_output=True, text=True)
if proc.returncode == 0:
    pass_('rendered regions in index.html (and m0/index.html when present) match data/products.json')
else:
    fail_('rendered regions differ from data/products.json (render-site-products --check exited %s)' % proc.returncode)
    sys.stdout.write(proc.stdout[:2000])
    sys.stderr.write(proc.stderr)

# ---- Voice meetings platform rule: macOS 14.4 and later across every copy surface ----
specs_public = json.loads(Path('data/product-pages-public.json').read_text())
voice_pre_credits = Path('voice/index.html').read_text().partition('<section id="credits"')[0]
whats_voice = re.search(
    r'<article class="tl-entry">(?:(?!</article>).)*?Coco Voice(?:(?!</article>).)*?</article>',
    Path('whats-new/index.html').read_text(),
    re.S,
)
llms_voice = next((ln for ln in Path('llms.txt').read_text().splitlines() if '[Coco Voice](' in ln), '')
home_voice = re.search(
    r'<article\b[^>]*class="[^"]*\bcard\b[^"]*"(?:(?!</article>).)*?id="t-voice"(?:(?!</article>).)*?</article>',
    Path('index.html').read_text(),
    re.S,
)
meeting_blobs = {
    'data/products.json (voice row)': json.dumps(next(r for r in shipped if r['id'] == 'voice')),
    'data/product-pages-public.json (voice spec)': json.dumps(specs_public['voice']),
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

# ---- C6 shared nav/drawer/footer parity and generated products:nav region on /m0/ ----
nav_re = re.compile(r'<header class="site-nav".*?</dialog>', re.S)
foot_re = re.compile(r'<footer class="foot".*?</footer>', re.S)


def _norm_nav(text):
    m = nav_re.search(text)
    return m.group(0).replace(' aria-current="page"', '') if m else None


def _region_inner(text, name):
    m = re.search(r'<!-- products:%s:start -->\s*(.*?)\s*<!-- products:%s:end -->' % (name, name), text, re.S)
    return m.group(1) if m else None


def check_m0_regions(root, ref_nav, ref_foot):
    """Verify m0/index.html wraps its nav and footer in generated products:* regions."""
    m0_path = root / 'm0' / 'index.html'
    # ponytail: ceiling = 1 absent hand-built page (m0/index.html) before /m0/ lands; upgrade path = remove this absent-only skip in Part 2 once /m0/ exists on main.
    if not m0_path.is_file():
        return []
    txt = m0_path.read_text()
    errs = []
    nav_inner = _region_inner(txt, 'nav')
    if nav_inner is None:
        errs.append('m0/index.html exists without products:nav markers')
    elif _norm_nav(nav_inner) != ref_nav:
        errs.append('m0/index.html products:nav region differs from generated nav/drawer')
    foot_inner = _region_inner(txt, 'foot')
    if foot_inner is None:
        errs.append('m0/index.html exists without products:foot markers')
    elif ref_foot and foot_inner.strip() != ref_foot.strip():
        errs.append('m0/index.html products:foot region differs from generated footer')
    return errs


products_html = Path('products/index.html').read_text()
ref_nav = _norm_nav(products_html)
ref_foot_m = foot_re.search(products_html)
ref_foot = ref_foot_m.group(0) if ref_foot_m else None
nav_checked = 0
for page_p in sorted(Path('.').glob('*/index.html')):
    ptxt = page_p.read_text()
    if '<meta http-equiv="refresh"' in ptxt:
        continue
    if ref_nav and _norm_nav(ptxt) == ref_nav:
        nav_checked += 1
    else:
        fail_('%s: nav/drawer differs from generated page nav' % page_p)
# ponytail: ceiling = 1 absent hand-built page (m0/index.html) before /m0/ lands; upgrade path = pin expected count to 14 in Part 2 once /m0/ exists on main.
want_pages = 14 if Path('m0/index.html').is_file() else 13
if nav_checked == want_pages:
    pass_('all %d top-level */index.html pages match the generated nav/drawer byte-for-byte' % nav_checked)
else:
    fail_('expected %d top-level pages with shared nav, verified %d' % (want_pages, nav_checked))

m0_errs = check_m0_regions(Path('.'), ref_nav, ref_foot)
if m0_errs:
    for err in m0_errs:
        fail_(err)
elif Path('m0/index.html').is_file():
    pass_('m0/index.html: generated products:nav and products:foot regions match')
else:
    pass_('m0/index.html absent: products:nav check skipped only on absence')

# Self-test: C6 must fail when m0/index.html exists without products:nav or products:foot markers.
with tempfile.TemporaryDirectory(prefix='c6-m0-check-') as tmp:
    troot = Path(tmp)
    assert check_m0_regions(troot, ref_nav, ref_foot) == [], 'absent m0 should skip'
    (troot / 'm0').mkdir()
    (troot / 'm0' / 'index.html').write_text(ref_nav + '\n' + (ref_foot or ''))
    no_nav = check_m0_regions(troot, ref_nav, ref_foot)
    (troot / 'm0' / 'index.html').write_text('<!-- products:nav:start -->\n%s\n<!-- products:nav:end -->\n%s\n' % (ref_nav, ref_foot or ''))
    no_foot = check_m0_regions(troot, ref_nav, ref_foot)
    (troot / 'm0' / 'index.html').write_text(
        '<!-- products:nav:start -->\n%s\n<!-- products:nav:end -->\n<!-- products:foot:start -->\n%s\n<!-- products:foot:end -->\n'
        % (ref_nav, ref_foot or '')
    )
    ok_m0 = check_m0_regions(troot, ref_nav, ref_foot)
if any('products:nav' in e for e in no_nav) and any('products:foot' in e for e in no_foot) and ok_m0 == []:
    pass_('C6 self-test: m0 present without products:nav or products:foot fails; valid markers pass')
else:
    fail_('C6 self-test failed: no_nav=%r no_foot=%r ok_m0=%r' % (no_nav, no_foot, ok_m0))

print()
if fail == 0:
    print('  homepage product rows agree with data/products.json')
    sys.exit(0)
sys.exit(1)
