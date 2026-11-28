#!/usr/bin/env python3
"""Assert homepage product rows are complete and index.html matches the render.

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
shipped = data['products']
source = [row for row in data['lab'] if 'href' in row]
lab = [row for row in data['lab'] if 'href' not in row]

print('=== homepage products: shipped=%d source=%d lab=%d ===' % (len(shipped), len(source), len(lab)))

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
        fail_('shipped %s missing %s' % (pid, ', '.join(missing)))
    else:
        pass_('shipped %s has tag, description and an action' % pid)

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
        pass_('source %s href is https' % pid)
    else:
        fail_('source %s href %r is not https' % (pid, href))
    status = row.get('status', '')
    if status.startswith('Source available'):
        pass_('source %s status starts with Source available' % pid)
    else:
        fail_('source %s status %r does not start with Source available' % (pid, status))

for row in lab:
    pid = row.get('id', '?')
    if 'href' in row:
        fail_('lab %s has an href' % pid)
    else:
        pass_('lab %s has no href' % pid)
    status = row.get('status', '')
    if status.startswith('Private'):
        pass_('lab %s status starts with Private' % pid)
    else:
        fail_('lab %s status %r does not start with Private' % (pid, status))

proc = subprocess.run(
    [sys.executable, 'scripts/render-site-products.py', '--check'],
    capture_output=True,
    text=True,
)
if proc.returncode == 0:
    pass_('index.html matches data/products.json')
else:
    fail_('index.html differs from data/products.json (render --check exited %s)' % proc.returncode)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)

# Voice meetings are built into macOS builds only (macOS 14.4 and later); every
# Voice copy surface that mentions "meeting" must state "macOS 14.4".
specs_public = json.loads(Path('data/product-pages-public.json').read_text())
voice_pre_credits = Path('voice/index.html').read_text().partition('<section id="credits"')[0]
whats_voice = re.search(r'<article class="tl-entry">(?:(?!</article>).)*?Coco Voice(?:(?!</article>).)*?</article>', Path('whats-new/index.html').read_text(), re.S)
llms_voice = next((ln for ln in Path('llms.txt').read_text().splitlines() if '[Coco Voice](' in ln), '')
home_voice = re.search(r'<article\b[^>]*class="[^"]*\bcard\b[^"]*"(?:(?!</article>).)*?id="t-voice"(?:(?!</article>).)*?</article>', Path('index.html').read_text(), re.S)
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

# C6 shared nav/drawer parity across */index.html and generated products:* markers on /m0/.
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
    m0_path = root / 'm0' / 'index.html'
    # ponytail: ceiling = 1 absent hand-built page (m0/index.html) before /m0/ lands; upgrade path = pin expected count to 14 and remove this absent-only skip in Part 2 once /m0/ exists on main.
    want_pages = 14 if m0_path.is_file() else 13
    if checked != want_pages:
        errs.append('expected %d top-level pages with shared nav, verified %d' % (want_pages, checked))
    if m0_path.is_file():
        m0_txt = m0_path.read_text()
        for region in ('nav', 'foot'):
            pat = r'<!-- products:%s:start -->\s*(.*?)\s*<!-- products:%s:end -->' % (region, region)
            match = re.search(pat, m0_txt, re.S)
            if not match:
                errs.append('m0/index.html exists without products:%s markers' % region)
            elif region == 'nav' and _norm_nav(match.group(1)) != ref_nav:
                errs.append('m0/index.html products:nav region differs from generated nav/drawer')
    return errs, checked


ref_nav = _norm_nav(Path('products/index.html').read_text())
c6_errs, nav_checked = check_c6_nav(Path('.'), ref_nav)
if c6_errs:
    for err in c6_errs:
        fail_(err)
else:
    pass_('all %d top-level */index.html pages match generated nav/drawer' % nav_checked)

# Self-test: C6 must fail when m0/index.html exists without products:nav or products:foot markers.
with tempfile.TemporaryDirectory(prefix='c6-m0-check-') as tmp:
    troot = Path(tmp)
    absent_errs, _ = check_c6_nav(troot, ref_nav)
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
    not any('m0/index.html' in e for e in absent_errs)
    and any('products:nav' in e for e in no_nav)
    and any('products:foot' in e for e in no_foot)
    and not any('m0/index.html' in e for e in ok_m0)
):
    pass_('C6 self-test: m0 present without products:nav or products:foot fails; absent skips; valid markers pass')
else:
    fail_('C6 self-test failed: absent=%r no_nav=%r no_foot=%r ok_m0=%r' % (absent_errs, no_nav, no_foot, ok_m0))

print()
if fail == 0:
    print('  homepage product rows agree with data/products.json')
    sys.exit(0)
sys.exit(1)
