"""Fixture tests for the rule-check graders: systematic-debugging, test-driven-development,
verification-before-completion.

Each grader scores one behaviour per item with regexes, so the tests pin: a hand-written
good answer scores full marks and a hand-written bad one scores well below it, every item
cites a line that is really in its SKILL.md, an answer that only repeats the brief scores
at most half, and the grader stays fast on runaway input.

    python3 -m unittest tests/test_skill_graders_rules_a.py -v
"""

import pathlib
import sys
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS = ROOT / "evals" / "skills"
sys.path.insert(0, str(SKILLS))

import score  # noqa: E402

SIZES = {"dev": 12, "heldout": 24}  # improve.py needs at least 20 held-out rows to run a round
IRRELEVANT = "The weather is lovely today. Pancakes need flour, eggs and milk."
NASTY = ("\n" * 100000, " \n" * 50000, "def test_" * 20000, "I think " * 20000, "- [" * 50000, "run " * 50000)


class RuleGraderChecks:
    skill = item_id = good = bad = None

    @classmethod
    def setUpClass(cls):
        path = SKILLS / cls.skill
        cls.rows = score.load_items(path / "items.jsonl")
        cls.grade = staticmethod(score.load_grader(path / "grader.py"))
        cls.item = next(r for r in cls.rows if r["id"] == cls.item_id)
        assert cls.item["split"] == "dev", "design fixtures against dev rows only"

    def test_good_answer_beats_bad_answer(self):
        good, bad = self.grade(self.item, self.good), self.grade(self.item, self.bad)
        self.assertEqual((good["score"], good["notes"]), (1.0, []))
        self.assertLessEqual(bad["score"], 0.5, bad["notes"])

    def test_items_are_well_formed(self):
        skill_md = (ROOT / "skills" / self.skill / "SKILL.md").read_text()
        for split, n in SIZES.items():
            self.assertEqual(sum(r["split"] == split for r in self.rows), n, split)
        self.assertEqual(len({r["input"] for r in self.rows}), len(self.rows), "two rows share an input")
        for row in self.rows:
            self.assertIn(row["rule"], skill_md, row["id"])
            self.assertTrue(row["terms"], row["id"])
            for term in row["terms"]:
                self.assertIn(term.lower(), row["input"].lower(), row["id"])

    def test_echo_empty_and_irrelevant_answers_score_low(self):
        for row in self.rows:
            self.assertLessEqual(self.grade(row, "stub:" + row["input"])["score"], 0.5, row["id"])
            for output in ("", IRRELEVANT, None):
                self.assertEqual(self.grade(row, output)["score"], 0.0, (row["id"], output))

    def test_degenerate_input_stays_fast(self):
        for row in {r["check"]: r for r in self.rows}.values():  # one row per check
            for text in NASTY:
                start = time.monotonic()
                score._check_result(row["id"], self.grade(row, text))
                self.assertLess(time.monotonic() - start, 2, (row["id"], text[:20]))


class SystematicDebuggingTest(RuleGraderChecks, unittest.TestCase):
    skill, item_id = "systematic-debugging", "sd01"
    good = """Systematic Debugging skill activated. No quick fix until we know the root cause.

1. Read the full stack trace for the NoneType error at cart/totals.py line 88.
2. Reproduce it locally with a cart that has no coupon, using Tuesday's pricing build.
3. Check what the pricing deploy changed in the values cart/totals.py reads.
"""
    bad = "Wrap line 88 of totals.py in a try/except and return 0 when the value is NoneType. Ship it."


class TestDrivenDevelopmentTest(RuleGraderChecks, unittest.TestCase):
    skill, item_id = "test-driven-development", "td01"
    good = """Test first:

```python
def test_slugify_joins_words_with_hyphens():
    assert slugify("Hello World") == "hello-world"
```

Run it and watch it fail with a NameError, because slugify does not exist yet. Then the code:

```python
def slugify(title):
    return "-".join(title.lower().split())
```
"""
    bad = """```python
def slugify(title):
    return "-".join(title.lower().split())

def test_slugify():
    assert slugify("Hello World") == "hello-world"
```
"""


class VerificationBeforeCompletionTest(RuleGraderChecks, unittest.TestCase):
    skill, item_id = "verification-before-completion", "vb01"
    good = """I can't tell the team it's finished yet. First run `pytest tests/test_export.py`, read the
output and check the exit code. Once it shows 0 failures, send:

"CSV export in reports/export.py is in. pytest tests/test_export.py: 34 passed, exit code 0."
"""
    bad = ("Great news team: CSV export in reports/export.py is finished and should work fine. "
           "Tests live in pytest tests/test_export.py.")


if __name__ == "__main__":
    unittest.main()
