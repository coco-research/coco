#!/usr/bin/env python3
"""Assert every adapters/<name>/ is listed in the --adapter help of bin/coco.js and bin/coco-bootstrap.sh (#234).

The npm package ships only bin/, so those two lists cannot be derived from
adapters/ at runtime; this check keeps the copies in sync with the directory.

Run from repo root: python3 tests/check-help-adapters.py
"""
import os
import re
import subprocess
import sys

real = sorted(d for d in os.listdir('adapters') if os.path.isdir(f'adapters/{d}'))


def listed(text):
    """Adapter tokens in the '--adapter <name> a | b | ...' block, up to the next flag."""
    m = re.search(r'--adapter <name>(.*?)(?=\n\s*#?\s*--\w)', text, re.S)
    return set(re.findall(r'[a-z][a-z0-9-]*', re.sub(r'^\s*#', '', m.group(1), flags=re.M))) if m else set()


sources = {
    'bin/coco.js --help': subprocess.run(['node', 'bin/coco.js', '--help'], capture_output=True, text=True,
                                         env={**os.environ, 'COCO_NO_UPDATE_CHECK': '1'}).stdout,
    'bin/coco-bootstrap.sh': open('bin/coco-bootstrap.sh').read(),
}
bad = False
for name, text in sources.items():
    found = listed(text)
    missing = [a for a in real if a not in found]
    extra = sorted(found - set(real))
    if missing:
        print(f'FAIL: {name} --adapter list is missing {missing}')
        bad = True
    if extra:
        print(f'FAIL: {name} --adapter list advertises non-existent adapters {extra}')
        bad = True
if bad:
    sys.exit(1)
print(f'PASS: all {len(real)} adapters/ directories are listed in the CLI help and bootstrap header')
