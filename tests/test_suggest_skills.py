"""Exercise the public command against a synthetic, read-only learning store."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SuggestSkillsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="suggest-skills-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.store = self.home / "store"
        self.env = dict(os.environ, HOME=str(self.home),
                        COCO_LEARNING_DIR=str(self.store),
                        TMPDIR=str(self.home), PYTHONDONTWRITEBYTECODE="1")
        self.env.pop("COCO_NO_UPDATE_CHECK", None)
        guard = self.home / "network-guard.cjs"
        guard.write_text("require('https').get = () => { throw Error('network attempted'); };\n")
        self.env["NODE_OPTIONS"] = "--require=" + str(guard)

    def observations(self, counts, age=0, project="demo"):
        path = self.store / "projects" / project / "observations.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = (datetime.datetime.now(datetime.timezone.utc) -
                 datetime.timedelta(days=age)).isoformat()
        with path.open("a") as stream:
            for pattern, count in counts.items():
                for _ in range(count):
                    stream.write(json.dumps({"timestamp": stamp,
                                             "input_summary": pattern}) + "\n")
        return path

    def run_command(self, *flags):
        return subprocess.run(["node", str(ROOT / "bin/coco.js"),
                               "suggest-skills", *flags], env=self.env,
                              capture_output=True, text=True, timeout=10)

    def test_top_three_and_no_writes(self):
        source = self.observations({"rebase then stamp": 9, "run lint": 7,
                                    "review release notes": 5, "fourth": 4})
        self.observations({"rebase then stamp": 1}, project="other")
        self.observations({"old pattern": 20}, age=8)
        before = {str(p): p.read_bytes() for p in self.home.rglob("*") if p.is_file()}
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn('seen 10 times this week', lines[0])
        self.assertIn('"rebase then stamp"', lines[0])
        self.assertIn('"run lint"', lines[1])
        self.assertIn('"review release notes"', lines[2])
        self.assertNotIn('old pattern', result.stdout)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.home.rglob("*") if p.is_file()})

    def test_empty_store_is_not_created(self):
        result = self.run_command("--draft")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "nothing repeated yet")
        self.assertFalse(self.store.exists())

    def test_drafts_are_only_in_new_temp_directory(self):
        self.observations({"write tests": 3, "ship release": 4, "review code": 5})
        before = {p for p in self.home.rglob("*")}
        result = self.run_command("--draft")
        self.assertEqual(result.returncode, 0, result.stderr)
        draft = Path(result.stdout.split('Drafts: ', 1)[1].strip())
        self.assertEqual(draft.parent, self.home)
        created = {p for p in self.home.rglob("*")} - before
        self.assertTrue(all(p == draft or draft in p.parents for p in created))
        stubs = list(draft.glob("*/SKILL.md"))
        self.assertEqual(len(stubs), 3)
        self.assertTrue(all('description:' in p.read_text() for p in stubs))

    def test_invalid_rows_future_events_and_symlinks_are_ignored(self):
        source = self.observations({"real pattern": 3, "one-off": 1})
        with source.open('a') as stream:
            stream.write('invalid\nnull\n[]\n')
            stream.write(json.dumps({'timestamp': 'bad', 'input_summary': 'ignore'}) + '\n')
            stream.write(json.dumps({'timestamp': '2099-01-01T00:00:00Z', 'input_summary': 'future'}) + '\n')
        linked = self.store / 'projects' / 'linked'
        linked.symlink_to(source.parent, target_is_directory=True)
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertIn('seen 3 times', result.stdout)


if __name__ == '__main__':
    unittest.main()
