"""Tests for the skill improve runner: the pure core, the proposer, and one round."""

import contextlib
import hashlib
import io
import json
import os
import pathlib
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
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
        self.assertTrue(callable(improve.paired.boot_p_greater))
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

    def test_dev_verdict_empty(self):
        for base, cand in (({}, {}), ({}, {"d1": 0.5}), ({"d1": 0.5}, {})):
            with self.subTest(base=base, cand=cand):
                err = io.StringIO()
                with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as caught:
                    improve.dev_verdict(base, cand, 0.05, 2)
                self.assertEqual(caught.exception.code, 2)
                self.assertEqual(err.getvalue(), "dev scores must be non-empty\n")

    def test_peek_stats(self):
        base = [0.25, 0.5, 0.75, 1.0]
        cand = [0.5, 0.75, 1.0, 1.0]
        with mock.patch.object(improve.paired, "paired_bootstrap",
                               return_value=(0.25, 0.1, 0.4)) as boot, \
                mock.patch.object(improve.paired, "boot_p_greater", return_value=0.005) as pg:
            stats = improve.peek_stats(base, cand)
        boot.assert_called_once()
        pg.assert_called_once()
        self.assertEqual(stats["n"], 4)
        self.assertEqual(stats["delta"], 0.25)
        self.assertEqual(stats["ci95"], [0.1, 0.4])
        self.assertEqual(stats["p_one_sided"], 0.005)
        self.assertEqual(stats["alpha"], improve.PEEK_ALPHA)
        self.assertLess(improve.PEEK_ALPHA, improve.ALPHA)
        self.assertTrue(stats["pass"])
        with mock.patch.object(improve.paired, "paired_bootstrap", return_value=(0.0, -0.1, 0.1)), \
                mock.patch.object(improve.paired, "boot_p_greater", return_value=0.4):
            self.assertFalse(improve.peek_stats(base, cand)["pass"])
        with mock.patch.object(improve.paired, "paired_bootstrap", return_value=(0.25, 0.1, 0.4)), \
                mock.patch.object(improve.paired, "boot_p_greater", return_value=0.2):
            self.assertFalse(improve.peek_stats(base, cand)["pass"])

    def test_peek_stats_empty(self):
        for base, cand in (([], []), ([], [0.5]), ([0.5], [])):
            with self.subTest(base=base, cand=cand):
                err = io.StringIO()
                with mock.patch.object(improve.paired, "paired_bootstrap",
                                       wraps=improve.paired.paired_bootstrap) as boot, \
                        mock.patch.object(improve.paired, "boot_p_greater",
                                          wraps=improve.paired.boot_p_greater) as pg:
                    with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as caught:
                        improve.peek_stats(base, cand)
                self.assertEqual(caught.exception.code, 2)
                self.assertEqual(err.getvalue(), "held-out scores must be non-empty\n")
                boot.assert_not_called()
                pg.assert_not_called()

    def test_peek_stats_real_bootstrap(self):
        # No mocks: the real paired bootstrap must keep a clear gain and refuse noise.
        base = [0.5] * 24
        self.assertTrue(improve.peek_stats(base, [0.75] * 24)["pass"])
        noise = [0.5 + (0.25 if i % 2 else -0.25) for i in range(24)]
        self.assertFalse(improve.peek_stats(base, noise)["pass"])
        # Swapped arguments (a candidate that is worse) must never pass.
        self.assertFalse(improve.peek_stats([0.75] * 24, base)["pass"])
        self.assertLess(improve.PEEK_ALPHA, improve.ALPHA)

    def test_peeked_in_skips_zero_peek_count(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        rounds = pathlib.Path(tmp.name)
        sha = "ab" * 32
        items = "12" * 32
        (rounds / "r001.json").write_text(json.dumps({
            "round": "r001", "peek_count": 0,
            "hashes": {"items": items},
            "candidate": {"skill_sha256": sha},
        }))
        (rounds / "r002.json").write_text(json.dumps({
            "round": "r002", "peek_count": 1,
            "hashes": {"items": items},
            "candidate": {"skill_sha256": sha},
        }))
        # A round that saved a candidate but never peeked must not block a later one.
        self.assertEqual(improve._peeked_in(rounds, sha, "r003", items), "r002")
        self.assertIsNone(improve._peeked_in(rounds, sha, "r002", items))
        # Same candidate peeked on a different items.jsonl does not count.
        other = "34" * 32
        (rounds / "r004.json").write_text(json.dumps({
            "round": "r004", "peek_count": 1,
            "hashes": {"items": other},
            "candidate": {"skill_sha256": sha},
        }))
        self.assertEqual(improve._peeked_in(rounds, sha, "r005", items), "r002")
        self.assertEqual(improve._peeked_in(rounds, sha, "r005", other), "r004")
        (rounds / "r006.json").write_text(json.dumps({
            "round": "r006", "peek_count": 1,
            "hashes": {"items": items}, "executor": {"kind": "stub"},
            "candidate": {"skill_sha256": "cd" * 32},
        }))
        self.assertIsNone(improve._peeked_in(rounds, "cd" * 32, "r007", items))

    def test_claim_round_publish_is_atomic(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        rounds = pathlib.Path(tmp.name)
        rec = {"skill": "toy", "peek_count": 0}

        def write_dies(path, text):
            pathlib.Path(path).write_bytes(b"{")
            raise OSError("disk full")

        with mock.patch.object(improve, "_write", write_dies):
            with self.assertRaises(OSError):
                improve.claim_round(rounds, dict(rec))
        self.assertEqual([p.name for p in rounds.glob("r*.json")], [])
        self.assertEqual(list(rounds.glob(".*.tmp")), [])
        self.assertEqual(improve.ledger_records(rounds), [])

        taken = rounds / "r001.json"
        taken.write_text('{"round": "r001"}\n')
        rid, path = improve.claim_round(rounds, dict(rec))
        self.assertEqual(rid, "r002")
        self.assertEqual(path.name, "r002.json")
        self.assertEqual(taken.read_text(), '{"round": "r001"}\n')
        saved = json.loads(path.read_text())
        self.assertEqual(saved["round"], "r002")
        self.assertEqual(saved["skill"], "toy")
        self.assertEqual(list(rounds.glob(".*.tmp")), [])

    def test_write_json_atomic_unique_temp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        rounds = pathlib.Path(tmp.name)
        path = rounds / "r001.json"
        path.write_text('{"round": "r001"}\n')
        rec = {"round": "r001", "skill": "toy"}
        improve.write_json_atomic(path, rec)
        improve.write_json_atomic(path, rec)
        self.assertEqual(list(rounds.glob(".*.tmp")), [])
        self.assertEqual(json.loads(path.read_text()), rec)
        good = path.read_text()

        def write_dies(p, text):
            pathlib.Path(p).write_bytes(b"{")
            raise OSError("disk full")

        with mock.patch.object(improve, "_write", write_dies):
            with self.assertRaises(OSError):
                improve.write_json_atomic(path, {"round": "r001", "skill": "torn"})
        self.assertEqual(path.read_text(), good)
        self.assertEqual(list(rounds.glob(".*.tmp")), [])

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

    def test_begin_peek_refuses_a_second_call(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        rec = {"peek_count": 0, "total_peeks": 0}
        improve.begin_peek(rec, pathlib.Path(tmp.name) / "peek.json", {"peeked": False})
        with self.assertRaises(RuntimeError):
            improve.begin_peek(rec, pathlib.Path(tmp.name) / "peek.json", {"peeked": True})

    def test_begin_peek_stops_at_the_lifetime_budget(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = pathlib.Path(tmp.name) / "peek.json"
        path.write_text("sentinel\n")
        rec = {"peek_count": 0, "total_peeks": improve.MAX_TOTAL_PEEKS}
        before = dict(rec)
        state = {"peeked": False}
        with self.assertRaises(RuntimeError) as caught:
            improve.begin_peek(rec, path, state)
        self.assertEqual(str(caught.exception), "held-out peek budget exhausted")
        self.assertEqual(rec, before)
        self.assertFalse(state["peeked"])
        self.assertEqual(path.read_text(), "sentinel\n")
        rec["total_peeks"] = improve.MAX_TOTAL_PEEKS - 1
        improve.begin_peek(rec, path, state)
        self.assertEqual((rec["peek_count"], rec["total_peeks"], rec["outcome"]),
                         (1, improve.MAX_TOTAL_PEEKS, "peeking"))
        self.assertEqual(json.loads(path.read_text())["total_peeks"], improve.MAX_TOTAL_PEEKS)

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


BASE = ("---\nname: toy\ndescription: Toy skill for tests.\n---\n# Toy\n\n"
        "Answer the topic.\n\nRules A:\n- none\n\nRules B:\n- none\n")
RULE_A = BASE.replace("Rules A:\n- none", "Rules A:\n- rule a")
RULE_B = BASE.replace("Rules B:\n- none", "Rules B:\n- rule b")
FRONT_CHANGED = BASE.replace("Toy skill for tests.", "Changed.")
RULE_BC = BASE.replace("Rules A:\n- none", "Rules A:\n- rule b\n- rule c")
RULE_A_ON_B = BASE.replace("Rules B:\n- none", "Rules B:\n- rule a")
RULE_Z = BASE.replace("Rules A:\n- none", "Rules A:\n- rule z")
RULE_Q = BASE.replace("Rules A:\n- none", "Rules A:\n- rule q")
# The same edit as RULE_A, as a unified diff with wrong line numbers.
DIFF_A = ("--- a/SKILL.md\n+++ b/SKILL.md\n@@ -9,4 +9,4 @@\n"
          " Answer the topic.\n \n Rules A:\n-- none\n+- rule a\n")


def fake_stub(skill_md, user_input, **kw):
    topic = user_input.split()[0].split(":", 1)[1]
    return "ans-" + topic if ("- rule " + topic) in skill_md.split("\n") else "idk"


GRADER = '''# GRADER_CANARY_77c1
def grade(item, output):
    hit = item["want"] in output
    return {"score": 1.0 if hit else 0.0,
            "notes": ["hit" if hit else "miss: wanted " + item["want"]]}
'''


def toy_rows(held_canary="", dev_canary=""):
    rows = []
    for n, t in enumerate("aabbccz" + "z", 1):
        rows.append({"id": "d%d" % n, "split": "dev", "want": "ans-" + t,
                     "input": "topic:%s item:d%d %s" % (t, n, dev_canary if n == 1 else "")})
    for n, t in enumerate("aaaabbbbcccc", 1):
        hid = "h4-" + held_canary if (n == 4 and held_canary) else "h%d" % n
        rows.append({"id": hid, "split": "heldout", "want": "ans-" + t,
                     "input": "topic:%s item:h%d %s" % (t, n, held_canary if n == 3 else "")})
    return rows


STUB_PROPOSER = '''import json, os, sys, time
prompt = sys.stdin.read()
i = os.environ["COCO_PROPOSER_INDEX"]
step = json.load(open(os.environ["STUB_PLAN"])).get(i, {})
with open(os.environ["STUB_LOG"], "a") as f:
    f.write(json.dumps({"i": i, "prompt": prompt, "files": sorted(os.listdir(".")),
                        "env": [v for v in os.environ.values() if "items.jsonl" in v]}) + "\\n")
time.sleep(step.get("sleep", 0))
for name, text in step.get("write", {}).items():
    with open(name, "w") as f:
        f.write(text)
if "raw_hex" in step:
    sys.stdout.buffer.write(bytes.fromhex(step["raw_hex"]))
sys.stdout.write(step.get("stdout", ""))
sys.stdout.flush()
sys.exit(step.get("exit", 0))
'''


def fenced(text):
    return "````\n" + text + "````\n"


def write_items(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def make_tree(root, held_canary="", dev_canary=""):
    """Write the toy skill, items, grader and a baseline held-out record. Returns paths."""
    root = pathlib.Path(root)
    skill, ev = root / "skills" / "toy" / "SKILL.md", root / "evals" / "skills" / "toy"
    skill.parent.mkdir(parents=True, exist_ok=True)
    ev.mkdir(parents=True, exist_ok=True)
    skill.write_text(BASE)
    (ev / "grader.py").write_text(GRADER)
    write_items(ev / "items.jsonl", toy_rows(held_canary, dev_canary))
    runs = ev / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    with mock.patch.object(run, "stub", fake_stub), \
            mock.patch.object(score, "git_short", return_value="0000000"):
        rec = score.score_run(
            "toy", "heldout", "stub", ev / "items.jsonl", ev / "grader.py", skill,
            model=None, seed=score.SEED, url=run.DEFAULT_URL)
    (runs / "baseline-heldout.json").write_text(score.record_json(rec))
    # Watched by the round: the router gate and the opener run.py imports.
    for rel in ("evals/routing/check_regression.py",
                "systems/superintelligence/scripts/local_http.py"):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# toy\n")
    return skill, ev / "items.jsonl", ev / "grader.py"


def dev_record(skill, items, grader):
    with mock.patch.object(run, "stub", fake_stub), \
            mock.patch.object(score, "git_short", return_value="0000000"):
        return score.score_run("toy", "dev", "stub", items, grader, skill,
                               model=None, seed=score.SEED, url=run.DEFAULT_URL)


def found_canaries(out, log, canaries):
    """Canaries present in any proposer prompt, any workspace file or the stub's log."""
    blobs = [p.read_bytes() for sub in ("prompts", "ws")
             for p in (out / sub).rglob("*") if p.is_file()]
    blobs.append(log.read_bytes())
    return {c for c in canaries if any(c.encode() in b for b in blobs)}


class ImproveProposerTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = pathlib.Path(tmp.name)
        self.log = self.tmp / "stub.log"
        stub = self.tmp / "stub_proposer.py"
        stub.write_text(STUB_PROPOSER)
        self.argv = [sys.executable, str(stub)]
        env = mock.patch.dict(os.environ, {"STUB_PLAN": str(self.tmp / "plan.json"),
                                           "STUB_LOG": str(self.log)})
        env.start()
        self.addCleanup(env.stop)

    def propose(self, steps, k, tree=None):
        skill, items, grader = tree or make_tree(self.tmp / "tree")
        (self.tmp / "plan.json").write_text(
            json.dumps({str(n): s for n, s in enumerate(steps, 1)}))
        return improve.propose_all(
            "toy", BASE, improve.load_dev_rows(items), dev_record(skill, items, grader),
            self.tmp / "out", self.argv, k, improve.MAX_CHANGED_LINES, {"peeked": False})

    def calls(self):
        return [json.loads(x) for x in self.log.read_text().splitlines()]

    def exits(self, fn, *args):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as caught:
            fn(*args)
        return caught.exception.code, err.getvalue()

    def test_canary_never_reaches_proposer(self):
        held, dev = "HELD_CANARY_" + uuid.uuid4().hex, "DEV_CANARY_" + uuid.uuid4().hex
        tree = make_tree(self.tmp / "tree", held, dev)
        results = self.propose([{"stdout": fenced(RULE_A)}, {"stdout": fenced(RULE_B)}], 2, tree)
        out = self.tmp / "out"
        # The scan could have found them: both canaries sit in files the runner reads.
        self.assertIn(held.encode(), tree[1].read_bytes())
        self.assertIn(b"GRADER_CANARY_77c1", tree[2].read_bytes())
        self.assertEqual(found_canaries(out, self.log, [held, "GRADER_CANARY_77c1"]), set())
        # Positive control: dev material does reach the proposer.
        self.assertIn(dev.encode(), (out / "prompts" / "p1.txt").read_bytes())
        self.assertIn(dev.encode(), (out / "ws" / "p1" / "dev_items.jsonl").read_bytes())
        self.assertEqual(len(self.calls()), 2)
        for n, (call, res) in enumerate(zip(self.calls(), results), 1):
            sent = call["prompt"].encode("utf-8")
            self.assertEqual(sent, (out / "prompts" / ("p%d.txt" % n)).read_bytes())
            self.assertEqual(hashlib.sha256(sent).hexdigest(), res["prompt_sha256"])
            self.assertEqual(call["files"], ["SKILL.md", "dev_items.jsonl", "dev_run.json"])
            self.assertEqual(call["env"], [])

    def test_canary_scan_detects_leak(self):
        held = "HELD_CANARY_" + uuid.uuid4().hex
        tree = make_tree(self.tmp / "tree", held)
        build = improve.build_prompt

        def leaky(*a, **kw):
            return build(*a, **kw) + tree[1].read_text()

        with mock.patch.object(improve, "build_prompt", leaky):
            self.propose([{"stdout": fenced(RULE_A)}], 1, tree)
        self.assertEqual(found_canaries(self.tmp / "out", self.log, [held]), {held})

    def test_workspace_tamper_rejected(self):
        steps = [{"write": {"notes.txt": "x"}, "stdout": fenced(RULE_A)},
                 {"write": {"SKILL.md": "changed\n"}, "stdout": fenced(RULE_B)}]
        with mock.patch.object(improve, "parse_proposal", wraps=improve.parse_proposal) as parse:
            results = self.propose(steps, 2)
        parse.assert_not_called()
        for r in results:
            self.assertEqual((r["status"], r["reason"], r["text"], r["edits"]),
                             ("rejected", "workspace modified", None, []))
        self.assertTrue((self.tmp / "out" / "proposals" / "p1" / "raw.txt").is_file())

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root can read mode-0 files")
    def test_chmod_000_is_rejected_not_a_crash(self):
        proposer = self.tmp / "chmod0.py"
        proposer.write_text(
            "import os, sys\n"
            "os.chmod('SKILL.md', 0)\n"
            "sys.stdout.write(%r)\n" % fenced(RULE_A))
        locked = self.tmp / "out" / "ws" / "p1" / "SKILL.md"

        def restore():
            if locked.exists():
                locked.chmod(0o644)
        self.addCleanup(restore)

        skill, items, grader = make_tree(self.tmp / "tree")
        results = improve.propose_all(
            "toy", BASE, improve.load_dev_rows(items), dev_record(skill, items, grader),
            self.tmp / "out", [sys.executable, str(proposer)], 1,
            improve.MAX_CHANGED_LINES, {"peeked": False})
        self.assertEqual((results[0]["status"], results[0]["reason"]),
                         ("rejected", "workspace modified"))

    def test_missing_proposer_cmd_exits_2(self):
        for value in (None, "", "   ", 'tool "unclosed', "no-such-command-xyz --flag"):
            with mock.patch.dict(os.environ):
                os.environ.pop("COCO_PROPOSER_CMD", None)
                if value is not None:
                    os.environ["COCO_PROPOSER_CMD"] = value
                code, msg = self.exits(improve.require_proposer_cmd)
            self.assertEqual(code, 2, value)
            self.assertEqual(len(msg.splitlines()), 1, value)
        cmd = shlex.join([sys.executable, "--flag", "two words"])
        with mock.patch.dict(os.environ, {"COCO_PROPOSER_CMD": cmd}):
            argv = improve.require_proposer_cmd()
        self.assertTrue(os.path.isabs(argv[0]))
        self.assertEqual(argv[1:], ["--flag", "two words"])
        out = self.tmp / "empty-out"
        out.mkdir()
        tree = self.tmp / "no-proposer-tree"
        make_tree(tree)
        argv = ["--skill", "toy", "--root", str(tree), "--out", str(out),
                "--executor", "stub", "--base-ref", "none"]
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"COCO_ROUTER_GATE_CMD": shlex.join(
                [sys.executable, "-c", "pass"])}):
            os.environ.pop("COCO_PROPOSER_CMD", None)
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as caught:
                    improve.main(argv)
        code = caught.exception.code
        self.assertEqual(2 if isinstance(code, str) else code, 2)
        self.assertEqual(len(err.getvalue().splitlines()), 1)
        self.assertEqual(list(out.iterdir()), [])
        self.assertFalse((tree / "evals" / "skills" / "_rounds").exists())
        self.assertFalse(self.log.exists())

    def test_k_proposals_make_k_calls(self):
        self.assertEqual(len(self.propose([{}, {}], 2)), 2)
        self.assertEqual([c["i"] for c in self.calls()], ["1", "2"])

    def test_proposer_failure_modes_fail_only_that_proposal(self):
        steps = [{"exit": 3, "stdout": fenced(RULE_A)}, {"raw_hex": "fffe"}, {"stdout": "\n \n"},
                 {"stdout": "x" * 2000}, {"stdout": fenced(RULE_A)}]
        with mock.patch.object(improve, "PROPOSER_MAX_BYTES", 1000):
            results = self.propose(steps, 5)
        self.assertEqual([(r["status"], r["reason"]) for r in results], [
            ("failed", "exit 3"), ("failed", "output is not UTF-8"), ("failed", "empty reply"),
            ("failed", "output too large"), ("ok", None)])
        self.assertEqual(len(self.calls()), 5)

    def test_proposer_timeout_fails_the_proposal(self):
        with mock.patch.object(improve, "PROPOSER_TIMEOUT", 1):
            results = self.propose([{"sleep": 30, "stdout": fenced(RULE_A)}], 1)
        self.assertEqual((results[0]["status"], results[0]["reason"]), ("failed", "timeout"))

    def test_run_proposer_timeout_kills_grandchildren(self):
        # 'sleep 30 & sleep 30' keeps a grandchild on the pipes after the shell dies.
        # Record each sleep's pid, then require those pids to be gone: killing only
        # the shell returns (None, "timeout") in ~1s and leaves both sleeps alive.
        bindir, piddir = self.tmp / "bin", self.tmp / "sleep-pids"
        bindir.mkdir()
        piddir.mkdir()
        wrapper = bindir / "sleep"
        wrapper.write_text('#!/bin/sh\necho $$ > "$SLEEP_PIDS/$$"\nexec /bin/sleep "$@"\n')
        wrapper.chmod(0o755)
        ws = self.tmp / "ws-timeout"
        ws.mkdir()

        def reap():
            for name in piddir.iterdir():
                try:
                    os.kill(int(name.name), signal.SIGKILL)
                except (ProcessLookupError, ValueError):
                    pass
        self.addCleanup(reap)

        env = {"PATH": str(bindir) + os.pathsep + os.environ["PATH"],
               "SLEEP_PIDS": str(piddir)}
        with mock.patch.dict(os.environ, env), \
                mock.patch.object(improve, "PROPOSER_TIMEOUT", 1):
            started = time.monotonic()
            got = improve.run_proposer(
                ["sh", "-c", "sleep 30 & sleep 30"], "prompt", ws, 1, {"peeked": False})
            elapsed = time.monotonic() - started
        self.assertEqual(got, (None, "timeout"))
        self.assertLess(elapsed, 10)
        pids = [int(p.name) for p in piddir.iterdir()]
        self.assertGreaterEqual(len(pids), 2)
        for pid in pids:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                continue
            # os.kill(pid, 0) also succeeds for an unreaped zombie.
            stat = subprocess.run(
                ["ps", "-o", "stat=", "-p", str(pid)],
                capture_output=True, text=True).stdout
            self.assertTrue(stat.startswith("Z"), (pid, stat))

    def test_run_proposer_timeout_returns_when_grandchild_leaves_the_group(self):
        # python -c starts a setsid grandchild that sleeps 30 holding inherited
        # stdout, then sleeps itself. killpg cannot reach the grandchild.
        pidfile = self.tmp / "escaped.pid"

        def reap():
            if not pidfile.is_file():
                return
            try:
                os.kill(int(pidfile.read_text()), signal.SIGKILL)
            except (ProcessLookupError, ValueError):
                pass
        self.addCleanup(reap)

        code = (
            "import subprocess,sys,time;"
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],"
            "start_new_session=True);"
            "open(%r,'w').write(str(p.pid));"
            "time.sleep(30)"
        ) % str(pidfile)
        ws = self.tmp / "ws-escaped"
        ws.mkdir()
        with mock.patch.object(improve, "PROPOSER_TIMEOUT", 1):
            started = time.monotonic()
            got = improve.run_proposer(
                [sys.executable, "-c", code], "prompt", ws, 1, {"peeked": False})
            elapsed = time.monotonic() - started
        self.assertEqual(got, (None, "timeout"))
        self.assertLess(elapsed, 15)
        self.assertTrue(pidfile.is_file())
        os.kill(int(pidfile.read_text()), 0)

    def test_run_proposer_bad_shebang_is_spawn_failed(self):
        proposer = self.tmp / "bad-shebang"
        proposer.write_text("#!/nonexistent/interpreter\n")
        proposer.chmod(0o755)
        ws = self.tmp / "ws-spawn"
        ws.mkdir()
        got = improve.run_proposer(
            [str(proposer)], "prompt", ws, 1, {"peeked": False})
        self.assertIsNone(got[0])
        self.assertTrue(got[1].startswith("spawn failed:"), got)

    def test_apply_branch_missing_skill_md_exits_1(self):
        root = self.tmp / "root"
        target = root / "skills" / "toy" / "SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_text("gone\n")
        target.unlink()
        code, msg = self.exits(
            improve.apply_branch, self.tmp / "out", root, "toy", "deadbeef")
        self.assertEqual(code, 1)
        self.assertEqual(msg, "SKILL.md no longer matches the round base\n")

    def test_split_overlap_exits_2(self):
        items = make_tree(self.tmp / "tree")[1]
        improve.check_split_overlap(items)
        rows = toy_rows()
        rows[0]["input"] = rows[8]["input"]
        write_items(items, rows)
        code, msg = self.exits(improve.check_split_overlap, items)
        self.assertEqual(code, 2)
        self.assertEqual(len(msg.splitlines()), 1)
        self.assertIn("d1", msg)

    def test_propose_all_rejects_heldout_rows_before_writing(self):
        out = self.tmp / "held-out"
        rows = [{"id": "h1", "split": "heldout", "input": "secret"}]
        rec = {"split": "dev", "per_item": {"h1": 0.0},
               "outputs": {"h1": "no"}, "notes": {"h1": []}}
        with self.assertRaises(ValueError) as caught:
            improve.propose_all(
                "toy", BASE, rows, rec, out, self.argv, 1,
                improve.MAX_CHANGED_LINES, {"peeked": False})
        self.assertEqual(str(caught.exception),
                         "the proposer workspace takes dev material only")
        self.assertFalse((out / "prompts").exists())

    def test_propose_all_records_each_outcome(self):
        steps = [{"stdout": DIFF_A}, {"stdout": fenced(RULE_A)}, {"stdout": fenced(BASE)},
                 {"stdout": fenced(FRONT_CHANGED)}, {"stdout": fenced(RULE_B)}]
        results = self.propose(steps, 5)
        self.assertEqual([(r["id"], r["focus"], r["status"], r["reason"]) for r in results], [
            ("p1", "d1", "ok", None), ("p2", "d2", "duplicate", "same as p1"),
            ("p3", "d3", "noop", None), ("p4", "d4", "rejected", "front matter changed"),
            ("p5", "d5", "ok", None)])
        first = results[0]
        self.assertEqual((first["text"], first["edits"], first["changed_lines"]),
                         (RULE_A, [(9, 10, ("- rule a",))], 2))
        self.assertEqual(first["skill_sha256"], improve.sha256_text(RULE_A))
        out = self.tmp / "out" / "proposals"
        for n, step in enumerate(steps, 1):
            raw = (out / ("p%d" % n) / "raw.txt").read_bytes()
            self.assertEqual(raw, step["stdout"].encode())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), results[n - 1]["raw_sha256"])
        # Only proposals worth a probe get a parsed SKILL.md.
        self.assertEqual(sorted(p.parent.name for p in out.glob("*/SKILL.md")), ["p1", "p5"])
        self.assertEqual((out / "p5" / "SKILL.md").read_text(), RULE_B)

    def test_failures_and_prompt(self):
        skill, items, grader = make_tree(self.tmp / "tree")
        rows, rec = improve.load_dev_rows(items), dev_record(skill, items, grader)
        got = improve.failures_from(rows, rec)
        self.assertEqual([f["id"] for f in got], ["d1", "d2", "d3", "d4", "d5", "d6"])
        self.assertEqual(got[0], {"id": "d1", "score": 0.0, "input": rows[0]["input"],
                                  "output": "idk", "notes": ["miss: wanted ans-a"]})
        rec["per_item"].update(d3=0.5, d4=1.0)       # d3 sorts last, d4 passes and drops out
        self.assertEqual([f["id"] for f in improve.failures_from(rows, rec)],
                         ["d1", "d2", "d5", "d6", "d7", "d8"])
        fails = [{"id": "f%d" % n, "score": 0.5, "input": "req%d" % n, "output": "out%d" % n,
                  "notes": ["n%d" % n]} for n in (1, 2, 3)]
        fails[1]["input"] = "y" * (improve.CASE_CHARS + 5)
        head, rest = improve.build_prompt("# S {x}", fails, 4, 5, 9, 2, 30).split(
            '<focus_case number="5" of="5">\n')
        focus, others = rest.split("</focus_case>\n\n<other_cases>\n")
        self.assertIn("<skill_md>\n# S {x}\n</skill_md>", head)
        self.assertIn("at most 30 lines", head)
        self.assertIn("2 of 9 dev cases already score 1.0", head)
        self.assertEqual(focus, "id: f2\nscore: 0.50\nrequest:\n" + "y" * improve.CASE_CHARS
                         + "[cut]\nmodel_output:\nout2\ngrader_notes:\n- n2\n\n")
        self.assertEqual(others, "id: f1\nscore: 0.50\nrequest:\nreq1\nmodel_output:\nout1\n"
                         "grader_notes:\n- n1\n\nid: f3\nscore: 0.50\nrequest:\nreq3\n"
                         "model_output:\nout3\ngrader_notes:\n- n3\n\n</other_cases>\n")

    def test_workspace_snapshot_and_fingerprint(self):
        skill, items, grader = make_tree(self.tmp / "tree")
        rows, rec = improve.load_dev_rows(items), dev_record(skill, items, grader)
        ws = self.tmp / "ws"
        hashes = improve.make_workspace(ws, BASE, rows, rec)
        self.assertEqual(sorted(hashes), ["SKILL.md", "dev_items.jsonl", "dev_run.json"])
        for name, digest in hashes.items():
            self.assertEqual(hashlib.sha256((ws / name).read_bytes()).hexdigest(), digest)
        self.assertEqual((ws / "SKILL.md").read_text(), BASE)
        self.assertEqual([json.loads(x) for x in (ws / "dev_items.jsonl").read_text().splitlines()],
                         rows)
        self.assertEqual((ws / "dev_run.json").read_text(), score.record_json(rec))
        with self.assertRaises(ValueError):          # held-out rows never reach a workspace
            improve.make_workspace(self.tmp / "bad", BASE, score.load_items(items), rec)
        self.assertFalse((self.tmp / "bad").exists())
        prev = improve.snapshot(ws)
        self.assertEqual(set(prev), set(hashes))
        for change in (lambda: (ws / "SKILL.md").write_text("x"),
                       lambda: (ws / "new.txt").write_text("x"),
                       lambda: (ws / "sub").mkdir(),
                       lambda: os.symlink("nowhere", ws / "link"),
                       lambda: (ws / "dev_run.json").unlink()):
            change()
            cur = improve.snapshot(ws)
            self.assertNotEqual(cur, prev)
            prev = cur
        self.assertEqual((prev["sub"], prev["link"]), ("dir", "other"))
        one, two = self.tmp / "one.txt", self.tmp / "two.txt"
        one.write_text("a")
        fp = improve.fingerprint([one, two])         # a missing path is left out
        self.assertEqual(fp, {str(one): hashlib.sha256(b"a").hexdigest()})
        one.write_text("b")
        self.assertNotEqual(improve.fingerprint([one, two]), fp)

    def test_snapshot_records_vanished_when_lstat_misses(self):
        ws = self.tmp / "vanish"
        ws.mkdir()
        (ws / "keep.txt").write_text("a")
        (ws / "gone.txt").write_text("b")
        real = pathlib.Path.lstat

        def lstat(self, *args, **kwargs):
            if self.name == "gone.txt":
                raise FileNotFoundError(self)
            return real(self, *args, **kwargs)

        with mock.patch.object(pathlib.Path, "lstat", lstat):
            snap = improve.snapshot(ws)
        self.assertEqual(snap["gone.txt"], "vanished")
        self.assertEqual(snap["keep.txt"], hashlib.sha256(b"a").hexdigest())

    def test_run_proposer_refuses_after_the_peek(self):
        with self.assertRaises(RuntimeError):
            improve.run_proposer(self.argv, "prompt", self.tmp, 1, {"peeked": True})
        self.assertFalse(self.log.exists())

    def test_missing_baseline_hint_names_the_out_file(self):
        runs = self.tmp / "runs"
        cfg = type("Cfg", (), {
            "skill": "toy", "executor": "stub", "model": None,
            "runs_dir": str(runs), "baseline_heldout": None,
        })()
        code, msg = self.exits(
            improve.find_baseline_heldout, cfg,
            {"skill": "s", "items": "i", "grader": "g"}, 0)
        self.assertEqual(code, 2)
        self.assertIn("--out", msg)
        self.assertIn(str(runs), msg)
        self.assertIn("baseline-heldout.json", msg)


    def test_base_check(self):
        repo, home = self.tmp / "repo", self.tmp / "githome"
        home.mkdir()
        rel = "evals/skills/toy/grader.py"
        target = repo / rel
        target.parent.mkdir(parents=True)
        target.write_text(GRADER)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["HOME"] = str(home)
        with mock.patch.dict(os.environ, env, clear=True):
            def git(*args):
                got = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
                self.assertEqual(got.returncode, 0, got.stderr)
            git("init", "-q")
            git("add", rel)
            git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "t")
            self.assertEqual(improve.base_check(repo, "none", [rel]), "skipped")
            with mock.patch.object(improve.subprocess, "run", wraps=subprocess.run) as run_git:
                self.assertEqual(improve.base_check(repo, "HEAD", [rel]), "ok")
            timeout = run_git.call_args.kwargs.get("timeout", 0)
            self.assertGreater(timeout, 0)
            self.assertLess(timeout, float("inf"))
            code, msg = self.exits(improve.base_check, repo, "missing-ref", [rel])
            self.assertEqual((code, msg), (2, "cannot read missing-ref:%s\n" % rel))
            target.write_text(GRADER + "# x\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    improve.base_check(repo, "HEAD", [rel])
            self.assertEqual(caught.exception.code, 1)
            self.assertIn("differs", err.getvalue())

    def test_base_check_git_failures(self):
        rel = "evals/skills/toy/grader.py"
        target = self.tmp / rel
        target.parent.mkdir(parents=True)
        target.write_text(GRADER)
        for exc in (FileNotFoundError("git"), subprocess.TimeoutExpired("git", 30)):
            with self.subTest(error=type(exc).__name__), \
                    mock.patch.object(improve.subprocess, "run", side_effect=exc) as run_git:
                self.assertEqual(improve.base_check(self.tmp, "none", [rel]), "skipped")
                run_git.assert_not_called()
                code, msg = self.exits(improve.base_check, self.tmp, "HEAD", [rel])
                self.assertEqual((code, msg), (2, "cannot read HEAD:%s\n" % rel))
                run_git.assert_called_once()


def reply(text):
    return {"stdout": fenced(text)}


def keep_steps():
    return [reply(RULE_A), reply(RULE_B), reply(BASE), reply(FRONT_CHANGED)]


def file_sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def tree_sha256(root):
    digest = hashlib.sha256()
    root = pathlib.Path(root)
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def ledger_path(root, rid):
    return pathlib.Path(root) / "evals" / "skills" / "_rounds" / "toy" / ("%s.json" % rid)


def last_json(text):
    lines = [ln for ln in text.splitlines() if ln.startswith("{")]
    assert lines, "no JSON line in %r" % text
    return json.loads(lines[-1])


class ImproveRoundTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = pathlib.Path(tmp.name)
        self.log = self.tmp / "stub.log"
        self.stub = self.tmp / "stub_proposer.py"
        self.stub.write_text(STUB_PROPOSER)
        self.tree = self.tmp / "tree"
        make_tree(self.tree)
        self.skill = self.tree / "skills" / "toy" / "SKILL.md"

    def invoke(self, argv, env=None):
        base = {
            "COCO_PROPOSER_CMD": shlex.join([sys.executable, str(self.stub)]),
            "STUB_PLAN": str(self.tmp / "plan.json"),
            "STUB_LOG": str(self.log),
            "COCO_ROUTER_GATE_CMD": shlex.join([sys.executable, "-c", "pass"]),
        }
        if env:
            base.update(env)
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, base), mock.patch.object(run, "stub", fake_stub), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                improve.main(argv)
                code = 0
            except SystemExit as e:
                code = e.code
                if code is None:
                    code = 0
                elif isinstance(code, str):
                    code = 2
        return code, stdout.getvalue(), stderr.getvalue()

    def run_case(self, steps, out, k=4, root=None, extra=None, env=None):
        root = pathlib.Path(root) if root else self.tree
        (self.tmp / "plan.json").write_text(
            json.dumps({str(n): step for n, step in enumerate(steps, 1)}))
        argv = ["--skill", "toy", "--root", str(root), "--out", str(out),
                "--executor", "stub", "--base-ref", "none", "--max-proposals", str(k)]
        if extra:
            argv.extend(extra)
        # Toy items have 12 held-out rows; the production floor is MIN_HELDOUT (20).
        with mock.patch.object(improve, "MIN_HELDOUT", 12):
            code, stdout, stderr = self.invoke(argv, env)
        self.assert_no_abs(root / "evals" / "skills" / "_rounds")
        self.assert_no_abs(out)
        return code, stdout, stderr

    def assert_no_abs(self, root):
        root = pathlib.Path(root)
        if not root.exists():
            return
        prefix = str(self.tmp).encode()
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            self.assertNotIn(prefix, raw, path.name)
            if path.suffix == ".json":
                self._walk_no_abs(json.loads(raw.decode()), path.name)

    def _walk_no_abs(self, obj, where):
        if isinstance(obj, dict):
            for value in obj.values():
                self._walk_no_abs(value, where)
        elif isinstance(obj, list):
            for value in obj:
                self._walk_no_abs(value, where)
        elif isinstance(obj, str):
            self.assertFalse(obj.startswith("/"), "%s: %s" % (where, obj))

    def count_scores(self):
        calls = []
        orig = score.score_run

        def wrapped(name, split, *args, **kwargs):
            calls.append(split)
            return orig(name, split, *args, **kwargs)

        return calls, mock.patch.object(score, "score_run", wrapped)

    def test_keep_path(self):
        before, skills_before = file_sha256(self.skill), tree_sha256(self.tree / "skills")
        out = self.tmp / "out-keep"
        code, stdout, stderr = self.run_case(keep_steps(), out)
        self.assertEqual(code, 0)
        self.assertIn("PEEK:", stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "kept")
        self.assertEqual(rec["peek_count"], 1)
        self.assertEqual(rec["params"]["alpha"], improve.ALPHA)
        self.assertEqual(rec["params"]["peek_alpha"], improve.PEEK_ALPHA)
        self.assertEqual(rec["base_check"], "skipped")
        self.assertEqual(rec["compose"]["chosen"], "composed")
        self.assertTrue(rec["gate"]["peek"]["pass"])
        self.assertEqual(last_json(stdout)["outcome"], "kept")
        by_id = {p["id"]: p for p in rec["proposals"]}
        self.assertEqual(by_id["p3"]["status"], "noop")
        self.assertEqual(by_id["p4"]["status"], "rejected")
        self.assertIn("front matter", by_id["p4"]["reason"])
        branch = out / "branch"
        self.assertEqual((branch / "skills" / "toy" / "SKILL.md").read_text(),
                         RULE_A.replace("Rules B:\n- none", "Rules B:\n- rule b"))
        runs = branch / "evals" / "skills" / "toy" / "runs"
        self.assertTrue((runs / "r001-dev.json").is_file())
        self.assertTrue((runs / "r001-heldout.json").is_file())
        self.assertTrue((branch / "evals" / "skills" / "_rounds" / "toy" / "r001.json").is_file())
        self.assertTrue((out / "skill.diff").is_file())
        for path in (runs / "r001-heldout.json", out / "records" / "cand-heldout.json"):
            held = json.loads(path.read_text())
            self.assertNotIn("outputs", held)
            self.assertNotIn("notes", held)
        self.assertEqual(file_sha256(self.skill), before)
        self.assertEqual(tree_sha256(self.tree / "skills"), skills_before)
        self.assertEqual(self.skill.read_text(), BASE)
        # Records that can be committed carry no absolute paths (no machine paths in the repo).
        committed = list(branch.rglob("*.json")) + [ledger_path(self.tree, "r001")]
        for path in committed:
            text = path.read_text()
            for root in {str(self.tmp), os.path.realpath(self.tmp), str(pathlib.Path.home())}:
                self.assertNotIn(root, text, path.name)

    def test_compose_end_to_end(self):
        out = self.tmp / "out-compose"
        code, stdout, stderr = self.run_case(
            [reply(RULE_A), reply(RULE_BC), reply(RULE_A_ON_B)], out, k=3)
        self.assertEqual(code, 0)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["compose"]["dropped"], [{"id": "p1", "why": "conflicts with p2"}])
        self.assertEqual(rec["compose"]["used"], ["p2", "p3"])
        self.assertEqual(rec["compose"]["composed_dev_mean"], 0.75)
        self.assertEqual(rec["outcome"], "kept")
        self.assertEqual(last_json(stdout)["peek_count"], 1)
        want = RULE_BC.replace("Rules B:\n- none", "Rules B:\n- rule a")
        self.assertEqual((out / "branch" / "skills" / "toy" / "SKILL.md").read_text(), want)

    def test_composed_over_max_growth_falls_back(self):
        pad = 2200
        big_a = RULE_A.replace("Rules A:\n- rule a\n",
                               "Rules A:\n- rule a\n" + ("A" * pad) + "\n")
        big_b = RULE_B.replace("Rules B:\n- rule b\n",
                               "Rules B:\n- rule b\n" + ("B" * pad) + "\n")
        self.assertLessEqual(len(big_a.encode()) - len(BASE.encode()), improve.MAX_GROWTH_BYTES)
        self.assertLessEqual(len(big_b.encode()) - len(BASE.encode()), improve.MAX_GROWTH_BYTES)
        self.assertGreater((len(big_a.encode()) - len(BASE.encode()))
                           + (len(big_b.encode()) - len(BASE.encode())),
                           improve.MAX_GROWTH_BYTES)
        out = self.tmp / "out-growth"
        code, stdout, stderr = self.run_case([reply(big_a), reply(big_b)], out, k=2)
        self.assertEqual(code, 0, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["compose"]["used"], ["p1", "p2"])
        self.assertEqual(rec["compose"]["chosen"], "p1")
        self.assertIsNone(rec["compose"]["composed_dev_mean"])
        self.assertEqual(
            rec["compose"]["why"],
            "composed text grows by more than %d bytes" % improve.MAX_GROWTH_BYTES)
        self.assertEqual((out / "candidate" / "SKILL.md").read_text(), big_a)
        self.assertFalse((out / "records" / "composed-dev.json").exists())

    def test_refuse_at_the_gate(self):
        before, skills_before = file_sha256(self.skill), tree_sha256(self.tree / "skills")
        out = self.tmp / "out-refuse"
        code, stdout, stderr = self.run_case([reply(RULE_Z)], out, k=1)
        self.assertEqual(code, 0)
        self.assertIn("PEEK:", stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "no change")
        self.assertEqual(rec["peek_count"], 1)
        self.assertEqual(last_json(stdout)["peek_count"], 1)
        self.assertFalse(rec["gate"]["peek"]["pass"])
        self.assertFalse((out / "branch").exists())
        self.assertEqual(file_sha256(self.skill), before)
        self.assertEqual(tree_sha256(self.tree / "skills"), skills_before)

    def test_no_winner(self):
        calls, patch = self.count_scores()
        with patch:
            code, stdout, stderr = self.run_case(
                [reply(BASE), reply(RULE_Q)], self.tmp / "out-none", k=2)
        self.assertEqual(code, 0)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "no change")
        self.assertEqual(rec["reason"], "no proposal beat baseline dev by the margin")
        self.assertEqual(rec["peek_count"], 0)
        self.assertEqual(calls.count("heldout"), 0)
        self.assertNotIn("PEEK:", stderr)
        self.assertEqual(last_json(stdout)["peek_count"], 0)

    def test_score_die_keeps_the_message(self):
        orig = score.score_run

        def wrapped(name, split, executor, items_path, grader_path, skill_md_path, **kw):
            if "proposals" in pathlib.Path(skill_md_path).parts:
                score.die("bad record X")
            return orig(name, split, executor, items_path, grader_path, skill_md_path, **kw)

        with mock.patch.object(score, "score_run", wrapped):
            code, stdout, stderr = self.run_case([reply(RULE_A)], self.tmp / "out-die", k=1)
        self.assertEqual(code, 0, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["proposals"][0]["status"], "score_failed")
        self.assertEqual(rec["proposals"][0]["reason"], "bad record X")
        self.assertIn("bad record X", stderr)

    def test_executor_string_exit_propagates(self):
        orig = score.score_run
        msg = "refusing non-local skill executor host 'x'"

        def wrapped(name, split, executor, items_path, grader_path, skill_md_path, **kw):
            if "proposals" in pathlib.Path(skill_md_path).parts:
                raise SystemExit(msg)
            return orig(name, split, executor, items_path, grader_path, skill_md_path, **kw)

        with mock.patch.object(score, "score_run", wrapped):
            code, stdout, stderr = self.run_case([reply(RULE_A)], self.tmp / "out-exec-host", k=1)
        self.assertEqual(code, 2, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertNotEqual(rec["proposals"][0]["status"], "score_failed")
        self.assertEqual(rec["outcome"], "started")
        self.assertEqual(rec["peek_count"], 0)
        self.assertNotIn("PEEK:", stderr)

    def test_one_peek_per_round(self):
        keep_tree, refuse_tree, none_tree = (self.tmp / name for name in ("pk", "pr", "pn"))
        make_tree(keep_tree)
        make_tree(refuse_tree)
        make_tree(none_tree)
        calls, patch = self.count_scores()
        with patch:
            def held():
                return calls.count("heldout")

            n = held()
            code, stdout, stderr = self.run_case(
                [reply(RULE_A), reply(RULE_B)], self.tmp / "out-pk", k=2, root=keep_tree)
            self.assertEqual(code, 0)
            self.assertEqual(held() - n, 1)
            self.assertEqual(last_json(stdout)["outcome"], "kept")
            n = held()
            code, stdout, stderr = self.run_case(
                [reply(RULE_Z)], self.tmp / "out-pr", k=1, root=refuse_tree)
            self.assertEqual(code, 0)
            self.assertEqual(held() - n, 1)
            self.assertEqual(last_json(stdout)["outcome"], "no change")
            n = held()
            code, stdout, stderr = self.run_case(
                [reply(BASE), reply(RULE_Q)], self.tmp / "out-pn", k=2, root=none_tree)
            self.assertEqual(code, 0)
            self.assertEqual(held() - n, 0)

            rec = {"peek_count": 0, "total_peeks": 0}
            improve.begin_peek(rec, self.tmp / "peek.json", {"peeked": False})
            with self.assertRaises(RuntimeError):
                improve.begin_peek(rec, self.tmp / "peek.json", {"peeked": True})

            code, stdout, stderr = self.run_case(
                [reply(RULE_A), reply(RULE_B)], self.tmp / "out-r1", k=2)
            self.assertEqual(code, 0)
            self.assertEqual(last_json(stdout)["round"], "r001")
            code, stdout, stderr = self.run_case([reply(RULE_BC)], self.tmp / "out-r2", k=1)
            self.assertEqual(code, 0)
            summary = last_json(stdout)
            self.assertEqual(summary["round"], "r002")
            # Stub rounds do not spend the held-out cap, so the second peek is still 1.
            self.assertEqual(summary["total_peeks"], 1)
            saved = json.loads(ledger_path(self.tree, "r002").read_text())
            self.assertEqual(saved["total_peeks"], 1)
            self.assertEqual(saved["peek_count"], 1)

            logged = self.log.read_text()
            ledger_path(self.tree, "r003").write_text(json.dumps({
                "round": "r003", "peek_count": 1,
                "hashes": {"items": saved["hashes"]["items"]},
                "executor": {"kind": "ollama"},
            }) + "\n")
            with mock.patch.object(improve, "MAX_TOTAL_PEEKS", 1):
                code, stdout, stderr = self.run_case([reply(RULE_A)], self.tmp / "out-cap", k=1)
            self.assertEqual(code, 1)
            self.assertIn("held-out peek cap reached", stderr)
            self.assertEqual(self.log.read_text(), logged)
            self.assertFalse(ledger_path(self.tree, "r004").exists())

    def test_apply_off_by_default(self):
        skill_sha, skills_sha = file_sha256(self.skill), tree_sha256(self.tree / "skills")
        out = self.tmp / "out-off"
        code, stdout, stderr = self.run_case(keep_steps(), out)
        self.assertEqual(code, 0)
        self.assertEqual(last_json(stdout)["outcome"], "kept")
        self.assertEqual(file_sha256(self.skill), skill_sha)
        self.assertEqual(tree_sha256(self.tree / "skills"), skills_sha)
        runs = self.tree / "evals" / "skills" / "toy" / "runs"
        self.assertEqual([p.name for p in sorted(runs.iterdir())], ["baseline-heldout.json"])

        edited = BASE.replace("Answer the topic.", "Answer it.")
        self.skill.write_text(edited)
        base_sha = json.loads(ledger_path(self.tree, "r001").read_text())["hashes"]["base_skill"]
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as caught:
                improve.apply_branch(out, self.tree, "toy", base_sha)
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("no longer matches", err.getvalue())
        self.assertEqual(self.skill.read_text(), edited)
        self.assertEqual([p.name for p in sorted(runs.iterdir())], ["baseline-heldout.json"])

        applied = self.tmp / "tree-on"
        make_tree(applied)
        out_on = self.tmp / "out-on"
        code, stdout, stderr = self.run_case(keep_steps(), out_on, root=applied, extra=["--apply"])
        self.assertEqual(code, 0)
        self.assertEqual(last_json(stdout)["outcome"], "kept")
        branch_skill = out_on / "branch" / "skills" / "toy" / "SKILL.md"
        self.assertEqual((applied / "skills" / "toy" / "SKILL.md").read_text(), branch_skill.read_text())
        on_runs = applied / "evals" / "skills" / "toy" / "runs"
        branch_runs = out_on / "branch" / "evals" / "skills" / "toy" / "runs"
        for name in ("r001-dev.json", "r001-heldout.json"):
            self.assertEqual((on_runs / name).read_text(), (branch_runs / name).read_text())
        held = json.loads((on_runs / "r001-heldout.json").read_text())
        self.assertNotIn("outputs", held)
        self.assertNotIn("notes", held)

    def test_router_gate(self):
        fail = shlex.join([sys.executable, "-c", "import sys; sys.exit(1)"])
        out = self.tmp / "out-gate"
        code, stdout, stderr = self.run_case(
            [reply(RULE_A)], out, k=1, env={"COCO_ROUTER_GATE_CMD": fail})
        self.assertEqual(code, 1)
        self.assertIn("router gate failed", stderr)
        self.assertFalse(self.log.exists())
        self.assertFalse(ledger_path(self.tree, "r001").exists())
        self.assertFalse((out / "prompts").exists())

        code, stdout, stderr = self.run_case([reply(RULE_A), reply(RULE_B)], self.tmp / "out-gate-ok", k=2)
        self.assertEqual(code, 0)
        self.assertEqual(len(self.log.read_text().splitlines()), 2)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["round"], "r001")
        self.assertEqual(rec["peek_count"], 1)
        self.assertIn(rec["outcome"], ("kept", "no change"))

    def test_proposer_escapes_workspace(self):
        grader = self.tree / "evals" / "skills" / "toy" / "grader.py"
        steps = [{"write": {str(grader): GRADER + "# touched\n"}, "stdout": fenced(RULE_A)}]
        calls, patch = self.count_scores()
        with patch:
            code, stdout, stderr = self.run_case(steps, self.tmp / "out-escape", k=1)
        self.assertEqual(code, 1)
        self.assertNotEqual(grader.read_text(), GRADER)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "aborted")
        self.assertEqual(rec["peek_count"], 0)
        self.assertIn("eval files changed", rec["reason"])
        self.assertEqual(calls.count("heldout"), 0)
        self.assertNotIn("PEEK:", stderr)
        self.assertEqual(last_json(stdout)["outcome"], "aborted")

    def test_escape_aborts_with_no_valid_proposals(self):
        grader = self.tree / "evals" / "skills" / "toy" / "grader.py"
        steps = [{"write": {str(grader): GRADER + "# touched\n"}, "stdout": ""}]
        code, stdout, stderr = self.run_case(steps, self.tmp / "out-escape-early", k=1)
        self.assertEqual(code, 1)
        self.assertNotEqual(grader.read_text(), GRADER)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "aborted")
        self.assertEqual(rec["peek_count"], 0)
        self.assertIn("evals/skills/toy/grader.py", rec["reason"])
        self.assertNotIn("PEEK:", stderr)
        self.assertEqual(last_json(stdout)["outcome"], "aborted")

    def test_others_not_a_gate(self):
        code, stdout, stderr = self.run_case([reply(RULE_Z)], self.tmp / "out-others", k=1)
        self.assertEqual(code, 0, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["gate"]["others"], {
            "status": "not needed",
            "reason": "a round can change only skills/<skill>/SKILL.md",
        })

    def test_peek_budget_is_per_heldout_set(self):
        items_hash = score.sha256_file(self.tree / "evals" / "skills" / "toy" / "items.jsonl")
        rounds = self.tree / "evals" / "skills" / "_rounds" / "toy"
        rounds.mkdir(parents=True)
        # A stub peek, and a real peek of a different items.jsonl, do not spend this set.
        (rounds / "r001.json").write_text(json.dumps({
            "round": "r001", "peek_count": 1,
            "hashes": {"items": items_hash}, "executor": {"kind": "stub"},
        }) + "\n")
        (rounds / "r002.json").write_text(json.dumps({
            "round": "r002", "peek_count": 1,
            "hashes": {"items": "f" * 64}, "executor": {"kind": "ollama"},
        }) + "\n")
        with mock.patch.object(improve, "MAX_TOTAL_PEEKS", 1):
            code, stdout, stderr = self.run_case([reply(RULE_Z)], self.tmp / "out-budget-free", k=1)
        self.assertEqual(code, 0, stderr)
        self.assertIn("PEEK:", stderr)
        rec = json.loads(ledger_path(self.tree, "r003").read_text())
        self.assertEqual(rec["peek_count"], 1)
        self.assertEqual(rec["total_peeks"], 1)

        capped = self.tmp / "capped-tree"
        make_tree(capped)
        same = score.sha256_file(capped / "evals" / "skills" / "toy" / "items.jsonl")
        (capped / "evals" / "skills" / "_rounds" / "toy").mkdir(parents=True)
        (capped / "evals" / "skills" / "_rounds" / "toy" / "r001.json").write_text(json.dumps({
            "round": "r001", "peek_count": 1,
            "hashes": {"items": same}, "executor": {"kind": "ollama"},
        }) + "\n")
        logged = self.log.read_text() if self.log.exists() else ""
        with mock.patch.object(improve, "MAX_TOTAL_PEEKS", 1):
            code, stdout, stderr = self.run_case(
                [reply(RULE_Z)], self.tmp / "out-budget-cap", k=1, root=capped)
        self.assertEqual(code, 1)
        self.assertIn("held-out peek cap reached", stderr)
        self.assertFalse((capped / "evals" / "skills" / "_rounds" / "toy" / "r002.json").exists())
        self.assertEqual(self.log.read_text() if self.log.exists() else "", logged)

    def test_repeat_candidate(self):
        code, stdout, stderr = self.run_case(keep_steps(), self.tmp / "out-rep1")
        self.assertEqual(code, 0)
        self.assertEqual(last_json(stdout)["outcome"], "kept")
        # Stub peeks do not count; the gate reads a real executor's record.
        prior = ledger_path(self.tree, "r001")
        saved = json.loads(prior.read_text())
        saved["executor"]["kind"] = "ollama"
        prior.write_text(json.dumps(saved) + "\n")
        code, stdout, stderr = self.run_case(keep_steps(), self.tmp / "out-rep2")
        self.assertEqual(code, 0)
        rec = json.loads(ledger_path(self.tree, "r002").read_text())
        self.assertEqual(rec["outcome"], "no change")
        self.assertIn("already peeked in r001", rec["reason"])
        self.assertEqual(rec["peek_count"], 0)
        self.assertNotIn("PEEK:", stderr)
        self.assertEqual(self.skill.read_text(), BASE)

    def test_heldout_score_exit_aborts_after_peek(self):
        orig = score.score_run

        def wrapped(name, split, *args, **kwargs):
            if split == "heldout":
                score.die("heldout broke")
            return orig(name, split, *args, **kwargs)

        with mock.patch.object(score, "score_run", wrapped):
            code, stdout, stderr = self.run_case([reply(RULE_Z)], self.tmp / "out-peek-die", k=1)
        self.assertEqual(code, 2, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "aborted")
        self.assertEqual(rec["peek_count"], 1)
        self.assertEqual(
            rec["reason"],
            "held-out scoring failed after the peek was spent: heldout broke")
        self.assertEqual(last_json(stdout)["outcome"], "aborted")
        self.assertEqual(last_json(stdout)["peek_count"], 1)

    def test_heldout_skill_hash_mismatch_aborts_after_peek(self):
        orig = improve.score_split

        def wrapped(cfg, split, skill_md_path):
            rec = orig(cfg, split, skill_md_path)
            if split == "heldout":
                rec = dict(rec, skill_sha256="0" * 64)
            return rec

        with mock.patch.object(improve, "score_split", wrapped):
            code, stdout, stderr = self.run_case([reply(RULE_Z)], self.tmp / "out-held-hash", k=1)
        self.assertEqual(code, 1, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "aborted")
        self.assertEqual(rec["peek_count"], 1)
        self.assertEqual(rec["reason"], "candidate SKILL.md changed during held-out scoring")
        self.assertEqual(last_json(stdout)["outcome"], "aborted")
        self.assertEqual(last_json(stdout)["peek_count"], 1)

    def test_dev_skill_hash_mismatch_fails_the_proposal(self):
        orig = improve.score_split

        def wrapped(cfg, split, skill_md_path):
            rec = orig(cfg, split, skill_md_path)
            if split == "dev" and "proposals" in pathlib.Path(skill_md_path).parts:
                rec = dict(rec, skill_sha256="0" * 64)
            return rec

        with mock.patch.object(improve, "score_split", wrapped):
            code, stdout, stderr = self.run_case([reply(RULE_A)], self.tmp / "out-dev-hash", k=1)
        self.assertEqual(code, 0, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["proposals"][0]["status"], "score_failed")
        self.assertEqual(rec["proposals"][0]["reason"], "proposal SKILL.md changed during scoring")
        self.assertEqual(rec["outcome"], "no change")
        self.assertEqual(rec["peek_count"], 0)
        self.assertNotIn("PEEK:", stderr)

    def test_composed_dev_score_exit_falls_back(self):
        orig = score.score_run

        def wrapped(name, split, executor, items_path, grader_path, skill_md_path, **kw):
            if split == "dev" and pathlib.Path(skill_md_path).parent.name == "candidate":
                score.die("composed broke")
            return orig(name, split, executor, items_path, grader_path, skill_md_path, **kw)

        out = self.tmp / "out-compose-die"
        with mock.patch.object(score, "score_run", wrapped):
            code, stdout, stderr = self.run_case([reply(RULE_A), reply(RULE_B)], out, k=2)
        self.assertEqual(code, 0, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["compose"]["chosen"], "p1")
        self.assertIsNone(rec["compose"]["composed_dev_mean"])
        self.assertEqual(rec["compose"]["why"], "composed broke")
        self.assertEqual((out / "candidate" / "SKILL.md").read_text(), RULE_A)
        self.assertFalse((out / "records" / "composed-dev.json").exists())
        self.assertIn("composed broke", stderr)

        def executor_blow(name, split, executor, items_path, grader_path, skill_md_path, **kw):
            if split == "dev" and pathlib.Path(skill_md_path).parent.name == "candidate":
                raise SystemExit("skill executor down")
            return orig(name, split, executor, items_path, grader_path, skill_md_path, **kw)

        tree = self.tmp / "exec-tree"
        make_tree(tree)
        with mock.patch.object(score, "score_run", executor_blow):
            code, stdout, stderr = self.run_case(
                [reply(RULE_A), reply(RULE_B)], self.tmp / "out-compose-exec", k=2, root=tree)
        self.assertEqual(code, 2, stderr)
        rec = json.loads(ledger_path(tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "started")
        self.assertEqual(rec["peek_count"], 0)
        self.assertIsNone(rec["compose"])
        self.assertNotIn("PEEK:", stderr)

    def test_runner_is_watched_and_hashed(self):
        seen = []
        real_check = improve.base_check

        def spy(root, ref, rels):
            seen.append(list(rels))
            return real_check(root, ref, rels)

        with mock.patch.object(improve, "base_check", spy):
            code, stdout, stderr = self.run_case([reply(RULE_Z)], self.tmp / "out-hash", k=1)
        self.assertEqual(code, 0, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["hashes"]["improve_py"], score.sha256_file(improve.__file__))
        self.assertEqual(rec["hashes"]["router_gate_py"], score.sha256_file(
            self.tree / "evals" / "routing" / "check_regression.py"))
        self.assertEqual(rec["hashes"]["local_http_py"], score.sha256_file(
            self.tree / "systems" / "superintelligence" / "scripts" / "local_http.py"))
        self.assertIn("evals/skills/improve.py", seen[0])
        self.assertIn("evals/routing/check_regression.py", seen[0])
        self.assertIn("systems/superintelligence/scripts/local_http.py", seen[0])

        decoy = self.tmp / "improve.py"
        decoy.write_text("version one\n")
        tree = self.tmp / "tamper-tree"
        make_tree(tree)
        steps = [{"write": {str(decoy): "version two\n"}, "stdout": fenced(RULE_A)}]
        with mock.patch.object(improve, "__file__", str(decoy)):
            code, stdout, stderr = self.run_case(
                steps, self.tmp / "out-tamper", k=1, root=tree)
        self.assertEqual(code, 1, stderr)
        rec = json.loads(ledger_path(tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "aborted")
        self.assertEqual(rec["peek_count"], 0)
        self.assertIn("improve.py", rec["reason"])

    def test_check_regression_change_aborts(self):
        gate = self.tree / "evals" / "routing" / "check_regression.py"
        steps = [{"write": {str(gate): gate.read_text() + "# tamper\n"}, "stdout": fenced(RULE_A)}]
        code, stdout, stderr = self.run_case(steps, self.tmp / "out-gate-tamper", k=1)
        self.assertEqual(code, 1, stderr)
        self.assertNotEqual(gate.read_text(), "# toy\n")
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "aborted")
        self.assertEqual(rec["peek_count"], 0)
        self.assertIn("eval files changed", rec["reason"])
        self.assertIn("check_regression.py", rec["reason"])
        self.assertNotIn("PEEK:", stderr)
        self.assertEqual(last_json(stdout)["outcome"], "aborted")

    def test_proposer_cache_write_aborts(self):
        cache = self.tmp / "round-cache"
        cache.mkdir()
        planted = cache / "planted.json"
        steps = [{"write": {str(planted): "{}\n"}, "stdout": fenced(RULE_A)}]
        with mock.patch.object(run, "CACHE", cache):
            code, stdout, stderr = self.run_case(steps, self.tmp / "out-cache", k=1)
        self.assertTrue(planted.is_file())
        self.assertEqual(code, 1, stderr)
        rec = json.loads(ledger_path(self.tree, "r001").read_text())
        self.assertEqual(rec["outcome"], "aborted")
        self.assertEqual(rec["peek_count"], 0)
        self.assertEqual(rec["reason"], "eval cache changed during the round: round-cache")
        self.assertNotIn("PEEK:", stderr)
        self.assertEqual(last_json(stdout)["outcome"], "aborted")

    def test_heldout_minimum_rejects_19(self):
        root = self.tmp / "min-tree"
        make_tree(root)
        rows = [{"id": "d%d" % n, "split": "dev", "want": "ans-a",
                 "input": "topic:a item:d%d" % n} for n in range(1, 3)]
        rows += [{"id": "h%d" % n, "split": "heldout", "want": "ans-a",
                  "input": "topic:a item:h%d" % n} for n in range(1, 20)]
        write_items(root / "evals" / "skills" / "toy" / "items.jsonl", rows)
        self.assertEqual(improve.MIN_HELDOUT, 20)
        self.assertEqual(len([r for r in rows if r["split"] == "heldout"]), 19)
        argv = ["--skill", "toy", "--root", str(root), "--out", str(self.tmp / "out-min"),
                "--executor", "stub", "--base-ref", "none", "--max-proposals", "1"]
        code, stdout, stderr = self.invoke(argv)
        self.assertEqual(code, 2, stderr)
        self.assertIn("need %d dev and %d held-out" % (improve.MIN_WINS, improve.MIN_HELDOUT),
                      stderr)
        self.assertFalse(ledger_path(root, "r001").exists())


if __name__ == "__main__":
    unittest.main()
