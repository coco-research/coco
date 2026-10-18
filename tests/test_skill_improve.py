"""Pure core of the skill improve runner: parsing, composing, and decisions."""

import contextlib
import hashlib
import io
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "evals", "skills"))

import improve  # noqa: E402
import run  # noqa: E402
import score  # noqa: E402


class ImproveCoreTest(unittest.TestCase):
    def test_module_wiring_and_sha256(self):
        self.assertIs(improve.run, run)
        self.assertIs(improve.score, score)
        self.assertTrue(callable(improve.paired.paired_bootstrap))
        self.assertTrue(callable(improve.paired._boot_p_greater))
        self.assertEqual(improve.sha256_text(""), hashlib.sha256(b"").hexdigest())
        self.assertEqual(improve.sha256_text("abc"), hashlib.sha256(b"abc").hexdigest())
        self.assertIsInstance(improve.Reject("x"), Exception)
        self.assertEqual(str(improve.Reject("why")), "why")

    def test_frontmatter_and_strip_outer_fence(self):
        text = "---\nname: toy\n---\nbody\n"
        self.assertEqual(improve.frontmatter(text), "---\nname: toy\n---\n")
        self.assertEqual(improve.frontmatter("body\n"), "")
        self.assertEqual(improve.frontmatter("---\nonly\n"), "")
        self.assertEqual(improve.strip_outer_fence("```\n# Toy\nbody\n```\n"), "# Toy\nbody\n")
        self.assertEqual(improve.strip_outer_fence("~~~markdown\n# Toy\n~~~\n"), "# Toy\n")
        self.assertEqual(improve.strip_outer_fence("# Toy\nbody\n"), "# Toy\nbody\n")
        self.assertEqual(improve.strip_outer_fence("plain\n"), "plain\n")

    def test_edit_script_and_n_changed(self):
        base = ["a", "b", "c", "d"]
        self.assertEqual(improve.edit_script(base, ["a", "b", "c", "d"]), [])
        self.assertEqual(improve.n_changed([]), 0)
        edits = improve.edit_script(base, ["a", "B", "c", "D"])
        self.assertEqual(edits, [(1, 2, ("B",)), (3, 4, ("D",))])
        self.assertEqual(improve.n_changed(edits), 4)
        insert = improve.edit_script(base, ["a", "b", "X", "c", "d"])
        self.assertEqual(insert, [(2, 2, ("X",))])
        self.assertEqual(improve.n_changed(insert), 1)

    def test_apply_edits_and_dedup(self):
        base = ["a", "b", "c", "d"]
        edits = [(1, 2, ("B",)), (3, 4, ("D",)), (1, 2, ("B",))]
        self.assertEqual(improve.apply_edits(base, edits), ["a", "B", "c", "D"])
        self.assertEqual(improve.apply_edits(base, []), base)

    def test_conflict_and_compose(self):
        self.assertTrue(improve.conflict((1, 2, ("x",)), (1, 2, ("y",))))
        self.assertTrue(improve.conflict((0, 2, ("x",)), (1, 3, ("y",))))
        self.assertFalse(improve.conflict((0, 1, ("x",)), (2, 3, ("y",))))
        same = (1, 2, ("x",))
        self.assertFalse(improve.conflict(same, same))
        base = ["a", "b", "c", "d", "e"]
        ranked = [("p1", [(1, 2, ("B",))]),
                  ("p2", [(1, 2, ("Z",))]),
                  ("p3", [(3, 4, ("D",))])]
        lines, used, dropped = improve.compose(base, ranked, cap=10)
        self.assertEqual(lines, ["a", "B", "c", "D", "e"])
        self.assertEqual(used, ["p1", "p3"])
        self.assertEqual(dropped, [{"id": "p2", "why": "conflicts with p1"}])
        lines, used, dropped = improve.compose(base, ranked, cap=3)
        self.assertEqual(lines, ["a", "B", "c", "d", "e"])
        self.assertEqual(used, ["p1"])
        self.assertEqual(dropped, [{"id": "p2", "why": "conflicts with p1"},
                                   {"id": "p3", "why": "over the composed cap"}])

    def test_dev_verdict(self):
        base = {"d1": 0.5, "d2": 0.5, "d3": 0.5, "d4": 0.5}
        gain = {"d1": 0.625, "d2": 0.625, "d3": 0.5, "d4": 0.5}
        v = improve.dev_verdict(base, gain, 0.05, 2)
        self.assertEqual(v["wins"], 2)
        self.assertEqual(v["losses"], 0)
        self.assertEqual(v["gain"], 0.0625)
        self.assertEqual(v["mean"], 0.5625)
        self.assertTrue(v["pass"])
        self.assertFalse(improve.dev_verdict(base, gain, 0.07, 2)["pass"])
        tie = {"d1": 0.625, "d2": 0.625, "d3": 0.375, "d4": 0.375}
        v = improve.dev_verdict(base, tie, 0.05, 2)
        self.assertEqual(v["wins"], 2)
        self.assertEqual(v["losses"], 2)
        self.assertFalse(v["wins"] > v["losses"])
        self.assertFalse(v["pass"])
        tiny = {"d1": 0.5, "d2": 0.5, "d3": 0.5, "d4": 0.505}
        v = improve.dev_verdict(base, tiny, 0.0, 1)
        self.assertEqual(v["wins"], 0)
        self.assertFalse(v["pass"])

    def test_peek_stats(self):
        base = [0.25, 0.5, 0.75, 1.0]
        cand = [0.5, 0.75, 1.0, 1.0]
        with mock.patch.object(improve.paired, "paired_bootstrap",
                               return_value=(0.25, 0.1, 0.4)) as boot, \
                mock.patch.object(improve.paired, "_boot_p_greater", return_value=0.01) as pg:
            stats = improve.peek_stats(base, cand)
        boot.assert_called_once()
        pg.assert_called_once()
        self.assertEqual(stats["n"], 4)
        self.assertEqual(stats["delta"], 0.25)
        self.assertEqual(stats["ci95"], [0.1, 0.4])
        self.assertEqual(stats["p_one_sided"], 0.01)
        self.assertEqual(stats["alpha"], improve.ALPHA)
        self.assertTrue(stats["pass"])
        with mock.patch.object(improve.paired, "paired_bootstrap", return_value=(0.0, -0.1, 0.1)), \
                mock.patch.object(improve.paired, "_boot_p_greater", return_value=0.4):
            self.assertFalse(improve.peek_stats(base, cand)["pass"])
        with mock.patch.object(improve.paired, "paired_bootstrap", return_value=(0.25, 0.1, 0.4)), \
                mock.patch.object(improve.paired, "_boot_p_greater", return_value=0.2):
            self.assertFalse(improve.peek_stats(base, cand)["pass"])

    def test_others_check(self):
        own = "skills/toy/SKILL.md"
        self.assertEqual(improve.others_check([own], "toy"),
                         {"status": "skipped", "reason": "only " + own + " changed"})
        self.assertEqual(improve.others_check([], "toy"),
                         {"status": "skipped", "reason": "only " + own + " changed"})
        self.assertEqual(
            improve.others_check([own, "skills/toy/extra.md", "skills/other/SKILL.md"], "toy"),
            {"status": "failed",
             "reason": "shared files changed: skills/other/SKILL.md, skills/toy/extra.md"})

    def test_die(self):
        for code in (1, 2):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    improve.die("boom", code=code)
            self.assertEqual(caught.exception.code, code)
            self.assertEqual(err.getvalue(), "boom\n")

    def test_parse_proposal_plain_and_noop(self):
        base = "# Toy\none\ntwo\n"
        self.assertEqual(improve.parse_proposal(base, base, "toy"), (base, []))
        text, edits = improve.parse_proposal("# Toy\none\nTWO\n", base, "toy")
        self.assertEqual(text, "# Toy\none\nTWO\n")
        self.assertEqual(edits, [(2, 3, ("TWO",))])
        self.assertEqual(improve.parse_proposal("```\n# Toy\none\nTWO\n```\n", base, "toy"),
                         ("# Toy\none\nTWO\n", [(2, 3, ("TWO",))]))
        self.assertEqual(improve.parse_proposal("# Toy\r\none\r\nTWO\r\n\r\n", base, "toy"),
                         ("# Toy\none\nTWO\n", [(2, 3, ("TWO",))]))

    def test_parse_proposal_applies_diff(self):
        base = "# Toy\none\ntwo\n"
        diff = ("--- a/skills/toy/SKILL.md\n"
                "+++ b/skills/toy/SKILL.md\n"
                "@@ -1,3 +1,3 @@\n"
                " # Toy\n"
                " one\n"
                "-two\n"
                "+TWO\n")
        self.assertEqual(improve.parse_proposal(diff, base, "toy"),
                         ("# Toy\none\nTWO\n", [(2, 3, ("TWO",))]))

    def test_parse_proposal_rejects(self):
        fm = "---\nname: toy\n---\nbody\nalpha\nbeta\n"
        cases = [
            ("", "empty reply"),
            ("\n\n\n", "empty reply"),
            ("# Toy\nbody\x00\n", "NUL byte"),
            ("---\nname: other\n---\nbody\nalpha\nbeta\n", "front matter changed"),
        ]
        for raw, needle in cases:
            with self.assertRaises(improve.Reject) as caught:
                improve.parse_proposal(raw, fm, "toy")
            self.assertIn(needle, str(caught.exception))
        plain = "# Toy\na\nb\nc\nd\ne\n"
        with self.assertRaises(improve.Reject) as caught:
            improve.parse_proposal("# Toy\nA\nB\nC\nD\nE\n", plain, "toy", max_changed=1)
        self.assertIn("too many changed lines", str(caught.exception))
        big = "x" * (improve.MAX_GROWTH_BYTES + 100)
        with self.assertRaises(improve.Reject) as caught:
            improve.parse_proposal("# Toy\n" + big + "\n", "# Toy\nx\n", "toy")
        self.assertIn("too large", str(caught.exception))

    def test_apply_diff_rejects(self):
        base_lines = ["# Toy", "one", "two", ""]

        def bad(diff_text, needle, lines=None):
            with self.assertRaises(improve.Reject) as caught:
                improve.apply_diff(lines if lines is not None else base_lines, diff_text, "toy")
            self.assertIn(needle, str(caught.exception))

        self.assertEqual(
            improve.apply_diff(base_lines,
                               "--- a/skills/toy/SKILL.md\n"
                               "+++ b/skills/toy/SKILL.md\n"
                               "@@ -1,3 +1,3 @@\n # Toy\n one\n-two\n+TWO\n", "toy"),
            ["# Toy", "one", "TWO", ""])
        bad("--- a/other.txt\n+++ b/other.txt\n@@ -1 +1 @@\n-a\n+b\n",
            "diff touches another file")
        bad("this is prose\n", "diff has no hunks")
        bad("--- /dev/null\n+++ b/skills/toy/SKILL.md\n@@ -1 +1 @@\n-a\n+b\n",
            "creates, deletes or renames")
        bad("--- a/skills/toy/SKILL.md\n+++ b/skills/toy/SKILL.md\n"
            "new file mode 100644\n@@ -1 +1 @@\n-a\n+b\n",
            "creates, deletes or renames")
        bad("--- a/skills/toy/SKILL.md\n+++ b/skills/toy/SKILL.md\n"
            "@@ -1 +1 @@\n-missing\n+added\n",
            "does not match")
        bad("--- a/skills/toy/SKILL.md\n+++ b/skills/toy/SKILL.md\n"
            "@@ -2,2 +2,2 @@\n x\n-y\n+Y\n",
            "hunk 1 is ambiguous", lines=["x", "y", "x", "y"])
        bad("--- a/skills/toy/SKILL.md\n+++ b/skills/toy/SKILL.md\n"
            "@@ -3,1 +3,1 @@\n-c\n+C\n"
            "@@ -1,1 +1,1 @@\n-a\n+A\n",
            "hunks overlap or are out of order", lines=["a", "b", "c", "d"])


if __name__ == "__main__":
    unittest.main()
