"""Verify pinned runtime bytes, every literal reference, and conservative links."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from claude_install import Installer


class RuntimeTest(unittest.TestCase):
    def test_pin_and_references(self):
        bundle = ROOT / 'systems/gsd'
        manifest = json.loads((bundle / 'runtime-pin.json').read_text())
        self.assertEqual(manifest['commit'], 'bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815')
        runtime = bundle / 'runtime'
        gsd_tracked = [r for r in manifest['files'] if not r.get('upstream_path')]
        self.assertEqual(len(gsd_tracked), manifest.get('upstream_get_shit_done_count', 299))
        self.assertEqual(len(gsd_tracked), 299)
        actual_files = sorted(
            str(p.relative_to(runtime))
            for p in runtime.rglob('*')
            if p.is_file() and p.name != 'LICENSE'
        )
        pinned_paths = sorted(r['path'] for r in manifest['files'])
        self.assertEqual(actual_files, pinned_paths)
        self.assertIn('bin/lib/secrets.cjs', actual_files)
        self.assertIn('bin/lib/secrets.generated.cjs', actual_files)
        self.assertIn('bin/lib/installer-migrations/002-codex-legacy-hooks-json.cjs', actual_files)
        self.assertIn('workflows/settings-advanced.md', actual_files)
        self.assertIn('workflows/settings-integrations.md', actual_files)
        self.assertIn('bin/shared/model-catalog.json', actual_files)
        for row in manifest['files']:
            data = (runtime / row['path']).read_bytes()
            self.assertEqual(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
                             row['git_blob'], row['path'])
        self.assertEqual(hashlib.sha256((runtime / 'LICENSE').read_bytes()).hexdigest(),
                         manifest['license_sha256'])
        refs = set()
        for source in list((bundle / 'skills').glob('*/SKILL.md')) + list((bundle / 'agents').glob('*.md')):
            refs.update(re.findall(r'get-shit-done/([A-Za-z0-9._/-]+\.(?:md|cjs|json))', source.read_text()))
        self.assertGreaterEqual(len(refs), 89)
        for ref in refs:
            self.assertTrue((runtime / ref).is_file(), ref)

    def test_gsd_tools_init_new_project_runs_in_temp_dir(self):
        tool = ROOT / 'systems/gsd/runtime/bin/gsd-tools.cjs'
        with tempfile.TemporaryDirectory(prefix='gsd-init-') as temp:
            proc = subprocess.run(
                ['node', str(tool), 'init', 'new-project'],
                cwd=temp,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

    def test_absent_owned_and_user_paths(self):
        with tempfile.TemporaryDirectory(prefix='gsd-runtime-') as temp:
            target = Path(temp) / 'claude'
            target.mkdir()
            dest = target / 'get-shit-done'
            for _ in range(2):
                installer = Installer(str(ROOT), str(target), ['gsd'], False, False)
                installer.plan_system('gsd')
                with contextlib.redirect_stdout(io.StringIO()):
                    for op in installer.ops:
                        installer.apply(op)
                self.assertTrue(dest.is_symlink())
                self.assertEqual(dest.resolve(), (ROOT / 'systems/gsd/runtime').resolve())
            dest.unlink()
            dest.mkdir()
            marker = dest / 'user.txt'
            marker.write_text('preserve this')
            installer = Installer(str(ROOT), str(target), ['gsd'], False, False)
            installer.plan_system('gsd')
            log = io.StringIO()
            with contextlib.redirect_stdout(log):
                for op in installer.ops:
                    installer.apply(op)
            self.assertFalse(dest.is_symlink())
            self.assertEqual(marker.read_text(), 'preserve this')
            self.assertIn("kept your get-shit-done", log.getvalue())

    def test_foreign_and_dangling_links_are_preserved(self):
        with tempfile.TemporaryDirectory(prefix='gsd-user-links-') as temp:
            root = Path(temp)
            for name, present in [('foreign', True), ('dangling', False)]:
                target = root / name
                target.mkdir()
                user = root / ('user-' + name)
                if present:
                    user.mkdir()
                    (user / 'marker.txt').write_text('keep')
                dest = target / 'get-shit-done'
                dest.symlink_to(user, target_is_directory=True)
                before = os.readlink(dest)
                installer = Installer(str(ROOT), str(target), ['gsd'], False, False)
                installer.plan_system('gsd')
                with contextlib.redirect_stdout(io.StringIO()):
                    for op in installer.ops:
                        installer.apply(op)
                self.assertTrue(dest.is_symlink())
                self.assertEqual(os.readlink(dest), before)
                self.assertEqual(user.exists(), present)
                if present:
                    self.assertEqual((user / 'marker.txt').read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
