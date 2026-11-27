#!/usr/bin/env python3
"""Assert every published count place agrees with docs/asset-counts.json.

The places are the ones scripts/sync-counts.py rewrites. An out-of-date place
prints one line, for example
  README.md:235: personas says 495, docs/asset-counts.json says 510. Run: python3 scripts/sync-counts.py
then "check-count-sync: N file(s) out of date", and exits 1.

--self-test proves the tool in a temp copy of the tracked tree: a planted stale
count is reported, sync-counts.py fixes it, a persona change syncs without
touching the site files, --site syncs the site, the never-synced paths stay
byte-identical, and the existing count tests still pass after each sync.

Run from repo root:
  python3 tests/check-count-sync.py
  python3 tests/check-count-sync.py --self-test
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC = os.path.join(ROOT, 'scripts', 'sync-counts.py')
SITE_FILES = ['index.html', 'coco/index.html', 'assets/js/kinetic.js',
              'assets/js/layout.js', 'assets/js/world.js',
              'assets/js/product-motifs-a.js']


def never_synced(rel):
    return (rel.startswith(('sbom/', '.metagpt/', '.arch/'))
            or re.match(r'evals/(.+/)?runs/', rel) is not None
            or re.fullmatch(r'docs/readme/how-it-works-[^/]*\.svg', rel) is not None
            or rel == 'assets/site/coco-ads-launch.mp4')


def run(cwd, *args):
    p = subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def digest(tmp, rels):
    out = {}
    for rel in rels:
        with open(os.path.join(tmp, rel), 'rb') as fh:
            out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def self_test():
    failures = 0

    def expect(ok, what, detail=''):
        nonlocal failures
        print(f'  {"PASS" if ok else "FAIL"}: {what}')
        if not ok:
            failures += 1
            if detail:
                print('    ' + detail.strip().replace('\n', '\n    '))

    tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.split('\0')
    with tempfile.TemporaryDirectory(prefix='count-sync-') as tmp:
        for rel in filter(None, tracked):
            src = os.path.join(ROOT, rel)
            if os.path.isfile(src) and not os.path.islink(src):
                os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True)
                shutil.copyfile(src, os.path.join(tmp, rel))
        here = [rel for rel in tracked if rel and os.path.isfile(os.path.join(tmp, rel))]
        frozen = sorted(rel for rel in here if never_synced(rel))
        site = [rel for rel in SITE_FILES if os.path.isfile(os.path.join(tmp, rel))]
        expect(bool(frozen), f'never-synced paths found to hash ({len(frozen)} files)')
        check = os.path.join(ROOT, 'tests', 'check-count-sync.py')
        truth = json.load(open(os.path.join(tmp, 'docs/asset-counts.json')))['personas']['total']

        # (1) a planted stale count is reported in the FRAME 205 shape, exit 1
        readme = os.path.join(tmp, 'README.md')
        text = open(readme).read()
        planted = text.replace(f'<h3>{truth}</h3><sub>Expert Personas</sub>',
                               f'<h3>{truth - 1}</h3><sub>Expert Personas</sub>')
        open(readme, 'w').write(planted)
        line = planted[:planted.index('<sub>Expert Personas</sub>')].count('\n') + 1
        code, out = run(tmp, check)
        want = (f'README.md:{line}: personas says {truth - 1}, docs/asset-counts.json says {truth}. '
                f'Run: python3 scripts/sync-counts.py')
        expect(code == 1 and want in out.splitlines()
               and out.splitlines()[-1] == 'check-count-sync: 1 file out of date',
               'planted stale count fails with the FRAME 205 lines', out)

        # (2) sync-counts.py fixes it
        code, out = run(tmp, SYNC)
        expect(code == 0 and open(readme).read() == text, 'sync-counts.py restores the planted count', out)
        code, out = run(tmp, check)
        expect(code == 0, 'check-count-sync passes after the sync', out)

        # (3) a persona change (15 new gtm) syncs without --site; site files untouched
        before_site, before_frozen = digest(tmp, site), digest(tmp, frozen)
        asset = os.path.join(tmp, 'docs/asset-counts.json')
        counts = json.load(open(asset))
        counts['personas']['total'] += 15
        counts['personas']['by_department']['gtm'] += 15
        json.dump(counts, open(asset, 'w'), indent=2)
        code, out = run(tmp, check)
        expect(code == 1, 'a persona change leaves places out of date until synced', out)
        code, out = run(tmp, SYNC)
        expect(code == 0, 'sync-counts.py rewrites the batch change', out)
        expect(digest(tmp, site) == before_site, f'without --site the {len(site)} site files are byte-identical')
        expect(digest(tmp, frozen) == before_frozen, 'without --site the never-synced paths are byte-identical')
        n = counts['personas']['total']
        expect(f'badge/personas-{n}-' in open(readme).read(), f'README badge now says {n}')

        # (5) the existing count tests still pass on the synced tree
        for test in ('tests/check-persona-counts.py', 'tests/check-site-counts.py'):
            code, out = run(tmp, os.path.join(ROOT, test))
            expect(code == 0, f'{test} passes after the sync', out)
        code, out = run(tmp, check)
        expect(code == 0, 'check-count-sync passes after the sync', out)

        # (4) a release: --site syncs the site from released-counts only
        released = os.path.join(tmp, 'docs/released-counts.json')
        rel_counts = json.load(open(released))
        rel_counts['personas'] = counts['personas']
        json.dump(rel_counts, open(released, 'w'), indent=2)
        before_live = digest(tmp, ['README.md', 'package.json', 'docs/install.md'])
        code, out = run(tmp, os.path.join(ROOT, 'tests/check-site-counts.py'))
        expect(code == 1, 'a release leaves the site out of date until --site runs', out)
        code, out = run(tmp, SYNC, '--site')
        expect(code == 0, 'sync-counts.py --site rewrites the site', out)
        expect(digest(tmp, frozen) == before_frozen, 'with --site the never-synced paths are byte-identical')
        expect(digest(tmp, ['README.md', 'package.json', 'docs/install.md']) == before_live,
               '--site leaves the live public text alone')
        code, out = run(tmp, os.path.join(ROOT, 'tests/check-site-counts.py'))
        expect(code == 0, 'tests/check-site-counts.py passes after --site', out)

    print('self-test:', 'all cases pass' if not failures else f'{failures} case(s) failed')
    return 1 if failures else 0


def main(argv):
    if '--self-test' in argv:
        return self_test()
    p = subprocess.run([sys.executable, SYNC, '--check'])
    return p.returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
