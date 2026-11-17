"""Validate fresh dev data without loading the live router or held-out split."""
import importlib.util
import json
from pathlib import Path
import sys
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
        self.assertTrue(all(r['split'] == 'dev' and r['draft'] for r in rows))
        self.assertEqual(module.check(rows), [])
        planted = [dict(r) for r in rows]
        planted[0]['prompt'] += ' ' + planted[0]['label']
        self.assertTrue(any('team word' in failure for failure in module.check(planted)))
        planted[0]['id'] = planted[1]['id']
        self.assertTrue(any('duplicate id' in failure for failure in module.check(planted)))


if __name__ == '__main__':
    unittest.main()
