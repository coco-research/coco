#!/usr/bin/env python3
"""Assert homepage product rows are complete and index.html matches the render.

Run from repo root: python3 tests/check-site-products.py
"""
import json
import subprocess
import sys
from pathlib import Path

fail = 0


def fail_(msg):
    global fail
    print('  FAIL: %s' % msg)
    fail = 1


def pass_(msg):
    print('  PASS: %s' % msg)


data = json.loads(Path('data/products.json').read_text())
shipped = data['shipped']
lab = data['lab']

print('=== homepage products: shipped=%d lab=%d ===' % (len(shipped), len(lab)))

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

paused = [row.get('id', '?') for row in shipped if 'paused' in row.get('tag', '').lower()]
if paused:
    fail_('shipped tag contains "paused": %s' % ', '.join(paused))
else:
    pass_('no shipped tag contains "paused"')

for row in shipped:
    art = Path(row.get('art', ''))
    if art.is_file():
        pass_('art %s exists' % art)
    else:
        fail_('art %s is missing' % art)

for row in lab:
    pid = row.get('id', '?')
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

print()
if fail == 0:
    print('  homepage product rows agree with data/products.json')
    sys.exit(0)
sys.exit(1)
