"""Grader and item-file checks for the code-verification skill pilot. No network."""

import importlib.util
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PILOT = ROOT / "evals" / "skills" / "code-verification"
SKILL = ROOT / "skills" / "code-verification" / "SKILL.md"

_FENCE = re.compile(r"Verify this change:\n\n```([A-Za-z0-9]+)\n(.*)\n```\Z", re.S)
_HEADING = re.compile(r"^### Category \d+: (.+)$", re.M)
# Obvious keyword for each heading, in the order the skill lists them.
_HINTS = ("TDZ", "import", "reference", "dead code", "react state", "mock", "css")


def _load_grade():
    path = PILOT / "grader.py"
    spec = importlib.util.spec_from_file_location("code_verification_grader", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.grade


def _items():
    rows = []
    for line in (PILOT / "items.jsonl").read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _categories():
    return _HEADING.findall(SKILL.read_text())


def _body(item):
    match = _FENCE.search(item["input"])
    if not match:
        return None, None
    return match.group(1), match.group(2).split("\n")


class TestCodeVerificationGrader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = _items()
        cls.names = _categories()

    def setUp(self):
        # Instance attribute so the function is not bound as a method.
        self.grader = _load_grade()

    def _fail_items(self):
        return [it for it in self.items if it["verdict"] == "FAIL"]

    def _one(self, category):
        for it in self._fail_items():
            if it["category"] == category:
                return it
        self.fail("no FAIL row for " + category)

    def _report(self, item, hint, line):
        return "Result: FAIL\n%s\nline %s\n%s\n" % (hint, line, item["token"])

    def test_perfect_report_scores_one(self):
        self.assertEqual(len(self.names), len(_HINTS))
        for name, hint in zip(self.names, _HINTS):
            item = self._one(name)
            report = self._report(item, hint, item["line"])
            got = self.grader(item, report)
            self.assertEqual(got["score"], 1.0, report)
            self.assertEqual(got["notes"], [])

    def test_wrong_line_loses_point_three(self):
        item = self._one(self.names[0])
        report = "Result: FAIL\n%s\nline 999\n" % _HINTS[0]
        self.assertNotIn(item["token"], report)
        got = self.grader(item, report)
        self.assertEqual(got["score"], 0.7)
        self.assertTrue(any("line" in note or "token" in note for note in got["notes"]))

    def test_wrong_category_loses_point_three(self):
        item = self._one(self.names[0])
        report = self._report(item, _HINTS[1], item["line"])
        got = self.grader(item, report)
        self.assertEqual(got["score"], 0.7)
        self.assertTrue(any("category" in note for note in got["notes"]))

    def test_fail_verdict_on_pass_row_scores_zero(self):
        item = next(it for it in self.items if it["verdict"] == "PASS")
        for report in ("Result: FAIL\n", "Result: PASS\nFAIL\n"):
            got = self.grader(item, report)
            self.assertEqual(got["score"], 0.0, report)
            self.assertTrue(got["notes"])

    def test_clean_pass_scores_one_and_spurious_category_scores_half(self):
        item = next(it for it in self.items if it["verdict"] == "PASS")
        clean = self.grader(item, "Result: PASS\n")
        self.assertEqual(clean["score"], 1.0)
        self.assertEqual(clean["notes"], [])
        half = self.grader(item, "Result: PASS\nimport mismatch\n")
        self.assertEqual(half["score"], 0.5)
        self.assertTrue(any("spurious" in note for note in half["notes"]))

    def test_empty_output_scores_zero(self):
        for item in (self._fail_items()[0], next(it for it in self.items if it["verdict"] == "PASS")):
            got = self.grader(item, "")
            self.assertEqual(got["score"], 0.0)
            self.assertTrue(got["notes"])
            self.assertTrue(all(isinstance(note, str) for note in got["notes"]))


class TestCodeVerificationItems(unittest.TestCase):
    def test_items_file(self):
        items = _items()
        names = _categories()
        self.assertEqual(len(names), 7)
        self.assertEqual(len(set(names)), 7)
        self.assertEqual([it["id"] for it in items], ["cv%02d" % n for n in range(1, 37)])
        self.assertEqual(len({it["id"] for it in items}), 36)

        required = ("id", "split", "input", "verdict", "category", "line", "token")
        dev = [it for it in items if it["split"] == "dev"]
        held = [it for it in items if it["split"] == "heldout"]
        self.assertEqual(len(dev), 12)
        self.assertEqual(len(held), 24)
        bodies = {"dev": set(), "heldout": set()}
        fail_cats = {"dev": set(), "heldout": set()}
        fails = passes = 0

        for it in items:
            n = int(it["id"][2:])
            self.assertEqual(it["split"], "dev" if n <= 12 else "heldout")
            for key in required:
                self.assertIn(key, it)
            self.assertIn(it["verdict"], ("FAIL", "PASS"))
            lang, lines = _body(it)
            self.assertIn(lang, ("python", "javascript", "typescript"), it["id"])
            self.assertIsNotNone(lines, it["id"])
            self.assertGreaterEqual(len(lines), 10, it["id"])
            self.assertLessEqual(len(lines), 40, it["id"])
            self.assertNotIn(it["input"], bodies[it["split"]])
            bodies[it["split"]].add(it["input"])
            if it["verdict"] == "PASS":
                passes += 1
                self.assertIsNone(it["category"], it["id"])
                self.assertIsNone(it["line"], it["id"])
                self.assertIsNone(it["token"], it["id"])
            else:
                fails += 1
                self.assertIn(it["category"], names, it["id"])
                self.assertIs(type(it["line"]), int, it["id"])
                self.assertGreaterEqual(it["line"], 1, it["id"])
                self.assertLessEqual(it["line"], len(lines), it["id"])
                self.assertIsInstance(it["token"], str)
                self.assertTrue(it["token"], it["id"])
                self.assertIn(it["token"], lines[it["line"] - 1], it["id"])
                fail_cats[it["split"]].add(it["category"])

        self.assertEqual(fails, 27)
        self.assertEqual(passes, 9)
        self.assertEqual(fail_cats["dev"], set(names))
        self.assertEqual(fail_cats["heldout"], set(names))
        self.assertTrue(bodies["dev"].isdisjoint(bodies["heldout"]))


if __name__ == "__main__":
    unittest.main()
