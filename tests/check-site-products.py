#!/usr/bin/env python3
"""Assert homepage product rows are complete and index.html matches the render.

Run from repo root: python3 tests/check-site-products.py
"""
import html
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

fail = 0


def fail_(msg):
    global fail
    print('  FAIL: %s' % msg)
    fail = 1


def pass_(msg):
    print('  PASS: %s' % msg)


data = json.loads(Path('data/products.json').read_text())
shipped = data['shipped']
source = data['source']
lab = data['lab']

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

index = Path('index.html').read_text()

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
    image = row.get('image')
    if image:
        src = image.get('src') or ''
        if Path(src).is_file():
            pass_('lab %s image %s exists' % (pid, src))
        else:
            fail_('lab %s image %r is missing' % (pid, src))
        alt = image.get('alt')
        if isinstance(alt, str) and alt.strip():
            pass_('lab %s image alt is set' % pid)
        else:
            fail_('lab %s image alt is empty' % pid)
        width, height = image.get('width'), image.get('height')
        if type(width) is int and type(height) is int:
            pass_('lab %s image is %sx%s' % (pid, width, height))
        else:
            fail_('lab %s image width/height must be integers' % pid)
    if ('id="lab-%s"' % pid) in index:
        pass_('index.html has id lab-%s' % pid)
    else:
        fail_('index.html missing id lab-%s' % pid)
    mailto = 'mailto:support@cocoresearch.org?subject=' + quote('Tester seat: ' + row.get('name', ''))
    if mailto in index:
        pass_('lab %s has a tester mailto' % pid)
    else:
        fail_('lab %s missing tester mailto' % pid)
    name_link = '<h4><a class="inline" href="?motion=off#lab-%s">%s</a></h4>' % (
        pid, html.escape(row.get('name') or '', quote=False))
    if name_link in index:
        pass_('lab %s name links to ?motion=off#lab-%s' % (pid, pid))
    else:
        fail_('lab %s name does not link to ?motion=off#lab-%s' % (pid, pid))

door = 'class="lab-sub lab-door"'
door_mailto = 'href="mailto:support@cocoresearch.org?subject=Tester%20seat"'
if door in index and door_mailto in index:
    pass_('index.html has the lab-door mailto')
else:
    fail_('index.html missing the lab-door mailto')

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

print()
if fail == 0:
    print('  homepage product rows agree with data/products.json')
    sys.exit(0)
sys.exit(1)
