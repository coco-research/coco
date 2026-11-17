"""Validate fresh dev data without loading the live router or held-out split."""
import importlib.util
from collections import Counter
import json
from pathlib import Path
import sys
import subprocess
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def checker():
    spec = importlib.util.spec_from_file_location('routing_items', ROOT / 'evals/routing/check_items.py')
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {'meta_select': None}):
        spec.loader.exec_module(module)
    return module


class DevItemsTest(unittest.TestCase):
    def test_checker_needs_no_router(self):
        self.assertTrue(callable(checker().check))

    def test_dev_coverage_and_leak_guard(self):
        rows = [json.loads(line) for line in
                (ROOT / 'evals/routing/items-descriptions-dev.jsonl').read_text().splitlines()]
        module = checker()
        self.assertEqual(len(rows), 120)
        self.assertEqual(len({r['label'] for r in rows}), 12)
        self.assertEqual(set(Counter(r['label'] for r in rows).values()), {10})
        self.assertTrue(all(r['split'] == 'dev' and r['draft'] for r in rows))
        teams = sorted({r['label'] for r in rows})
        self.assertEqual(module.check(rows, teams=teams), [])
        planted = [dict(r) for r in rows]
        planted[0]['prompt'] += ' ' + planted[0]['label']
        self.assertTrue(any('team word' in failure for failure in module.check(planted, teams=teams)))
        planted[0]['id'] = planted[1]['id']
        self.assertTrue(any('duplicate id' in failure for failure in module.check(planted, teams=teams)))

    def test_explicit_subset_ignores_other_installed_domains(self):
        module = checker()
        rows = [json.loads(line) for line in
                (ROOT / 'evals/routing/items-descriptions-dev.jsonl').read_text().splitlines()]
        teams = sorted({r['label'] for r in rows})
        names = {team: team for team in teams}
        names['additional-domain'] = 'Additional Domain'
        with mock.patch.object(module, 'team_names', return_value=names):
            self.assertEqual(module.check(rows, teams=teams), [])
            self.assertTrue(any('additional-domain' in f for f in module.check(rows)))
        result = subprocess.run([
            sys.executable, '-B', str(ROOT / 'evals/routing/check_items.py'),
            str(ROOT / 'evals/routing/items-descriptions-dev.jsonl'), '--teams', *teams],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
