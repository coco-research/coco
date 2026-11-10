"""Fixture tests for the rule-check graders: brainstorming, api-design-principles,
writing-skills.

Each grader scores one behaviour per item with regexes, so the tests pin: a hand-written
good answer scores full marks and a hand-written bad one scores well below it, every item
cites a line that is really in its SKILL.md, an answer that only repeats the brief scores
at most half, and the grader stays fast on runaway input.

    python3 -m unittest tests/test_skill_graders_rules_b.py -v
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


class BrainstormingTest(RuleGraderChecks, unittest.TestCase):
    skill, item_id = "brainstorming", "bs01"
    good = """Brainstorming skill activated. Before any code, let's agree on a short design for the habit
tracker, and I'll build nothing until you approve it.

First question: should the water reminders follow a fixed schedule, or adapt to how much was logged?
"""
    bad = """```python
import schedule  # habit tracker: remind people to drink water
schedule.every().hour.do(print, "Drink water")
```
"""


class ApiDesignPrinciplesTest(RuleGraderChecks, unittest.TestCase):
    skill, item_id = "api-design-principles", "ap01"
    good = """Resources are nouns; the HTTP method carries the action.

GET /orders - list orders (paginated)
POST /orders - create an order
GET /orders/{id} - read one order
PATCH /orders/{id} - update an order, including setting its status to cancelled

Replace POST /createOrder, POST /getOrderById and POST /cancelOrder with these routes.
"""
    bad = """POST /createOrder
POST /getOrderById
POST /cancelOrder

Keep the order endpoints as they are.
"""


class WritingSkillsTest(RuleGraderChecks, unittest.TestCase):
    skill, item_id = "writing-skills", "ws01"
    good = """---
name: condition-based-waiting
description: Use when tests are flaky, hang, or use a fixed sleep to wait for async work
---
"""
    bad = """---
name: Async Test Helpers!
description: I wrote this to poll conditions instead of sleep calls
---
"""


if __name__ == "__main__":
    unittest.main()
