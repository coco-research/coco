"""Grader checks for the generate-tests and humanizer pilots. No network, no model."""
import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]

# Hand rewrite of hu01: every fact, none of the grader's tell patterns, similar length.
_CLEAN = (
    "The flagship dashboard has a new release. We added three new filters, "
    "made the export flow simpler, and cut load times by 42 percent. People "
    "on the Plus plan now get a redesigned sidebar that makes large projects "
    "easier to scan. We also fixed a sync bug that was reported on Tuesday. "
    "Most of the other changes are small layout fixes you will barely notice. "
    "The faster pages are the part that shows up first, especially when a "
    "board has a lot of rows and someone is trying to find one number in a hurry."
)

# Same rewrite with two facts removed (42 percent, Tuesday).
_DROPPED = (
    "The flagship dashboard has a new release. We added three new filters, "
    "made the export flow simpler, and cut load times by a wide margin. People "
    "on the Plus plan now get a redesigned sidebar that makes large projects "
    "easier to scan. We also fixed a sync bug that was reported earlier in the "
    "week. Most of the other changes are small layout fixes you will barely "
    "notice. The faster pages are the part that shows up first, especially when "
    "a board has a lot of rows and someone is trying to find one number in a hurry."
)

_GT_FIELDS = ("id", "split", "input", "func", "impl", "mutants", "reference_tests")
_HU_FIELDS = ("id", "split", "input", "text", "facts")

# Probe test files run through the grader's sandboxed runner. Each passes only
# when the sandbox does its job, so a green run proves the sandbox held.
_WRITE_PROBE = (
    "import os\n"
    "\n"
    "import unittest\n"
    "\n"
    "\n"
    "class Probe(unittest.TestCase):\n"
    "    def test_home_write_denied(self):\n"
    "        path = os.path.expanduser('~/.skill-sandbox-probe')\n"
    "        with self.assertRaises(OSError):\n"
    "            with open(path, 'w') as handle:\n"
    "                handle.write('x')\n"
)

_NET_PROBE = (
    "import unittest\n"
    "import urllib.request\n"
    "\n"
    "\n"
    "class Probe(unittest.TestCase):\n"
    "    def test_network_denied(self):\n"
    "        with self.assertRaises(OSError) as caught:\n"
    "            urllib.request.urlopen('http://127.0.0.1:9', timeout=2)\n"
    "        error = caught.exception\n"
    "        errno = getattr(error, 'errno', None)\n"
    "        if errno is None:\n"
    "            errno = getattr(getattr(error, 'reason', None), 'errno', None)\n"
    "        self.assertEqual(errno, 1)\n"
)


def _load(name):
    path = ROOT / "evals" / "skills" / name / "grader.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_") + "_grader", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Tests that expect a real score from actually running the model-written tests
# need a usable OS sandbox; skip them when this host cannot start one.
SANDBOX = _load("generate-tests").sandbox_cmd("/tmp") is not None


def _items(name):
    path = ROOT / "evals" / "skills" / name / "items.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _assert_split(test, items):
    ids = [item["id"] for item in items]
    test.assertEqual(len(ids), len(set(ids)))
    test.assertEqual(len(items), 36)
    test.assertEqual(sum(item["split"] == "dev" for item in items), 12)
    test.assertEqual(sum(item["split"] == "heldout" for item in items), 24)  # held-out is larger so the keep gate can see a real gain


class GenerateTestsGraderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load("generate-tests")
        cls.items = _items("generate-tests")

    def setUp(self):
        # Grading runs model-written code, which is gated behind this variable.
        patcher = mock.patch.dict(os.environ, {self.mod.UNTRUSTED_ENV: "1"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _clamp(self):
        return next(item for item in self.items if item["func"] == "clamp")

    @unittest.skipUnless(SANDBOX, "no usable OS sandbox on this host")
    def test_reference_block_scores_one(self):
        item = self._clamp()
        for opener in ("```python\n", "```\n"):
            output = opener + item["reference_tests"] + "```"
            self.assertEqual(self.mod.grade(item, output)["score"], 1.0)

    def test_reference_scores_zero_without_env(self):
        item = self._clamp()
        output = "```python\n" + item["reference_tests"] + "```"
        with mock.patch.dict(os.environ):
            os.environ.pop(self.mod.UNTRUSTED_ENV, None)
            result = self.mod.grade(item, output)
        self.assertEqual(result["score"], 0.0)
        self.assertIn(self.mod.NOT_RUN_NOTE, result["notes"])

    def test_sandbox_cmd_none_without_tools(self):
        with mock.patch.object(self.mod.shutil, "which", return_value=None):
            self.assertIsNone(self.mod.sandbox_cmd("/tmp/x"))

    def test_sandbox_cmd_none_with_only_unshare(self):
        # unshare -rn blocks the network but not writes, so it must never be used.
        def which(name):
            return "/usr/bin/unshare" if name == "unshare" else None

        with mock.patch.object(self.mod.shutil, "which", side_effect=which):
            self.assertIsNone(self.mod.sandbox_cmd("/tmp/x"))

    def test_sandbox_cmd_none_when_sandbox_exec_probe_fails(self):
        def which(name):
            return "/usr/bin/sandbox-exec" if name == "sandbox-exec" else None

        failure = mock.Mock(returncode=1)
        self.mod._sandbox_exec_works.cache_clear()
        self.addCleanup(self.mod._sandbox_exec_works.cache_clear)
        with mock.patch.object(self.mod.shutil, "which", side_effect=which), \
                mock.patch.object(self.mod.subprocess, "run", return_value=failure):
            self.assertIsNone(self.mod.sandbox_cmd("/tmp/x"))

    @unittest.skipUnless(shutil.which("sandbox-exec"), "sandbox-exec not available")
    def test_sandbox_blocks_home_write(self):
        probe = Path(os.path.expanduser("~/.skill-sandbox-probe"))
        probe.unlink(missing_ok=True)
        self.addCleanup(lambda: probe.unlink(missing_ok=True))
        with tempfile.TemporaryDirectory() as tmp:
            result = self.mod._run_in_sandbox(_WRITE_PROBE, tmp)
        self.assertIsNotNone(result)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(probe.exists())

    @unittest.skipUnless(shutil.which("sandbox-exec"), "sandbox-exec not available")
    def test_sandbox_blocks_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.mod._run_in_sandbox(_NET_PROBE, tmp)
        self.assertIsNotNone(result)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(SANDBOX, "no usable OS sandbox on this host")
    def test_false_assertion_scores_zero(self):
        item = self._clamp()
        output = (
            "```python\n"
            "import unittest\n"
            "from impl import clamp\n"
            "\n"
            "class T(unittest.TestCase):\n"
            "    def test_false(self):\n"
            "        self.assertEqual(clamp(5, 0, 10), 999)\n"
            "```"
        )
        result = self.mod.grade(item, output)
        self.assertEqual(result["score"], 0.0)
        self.assertIn("tests fail on the correct function", result["notes"])

    @unittest.skipUnless(SANDBOX, "no usable OS sandbox on this host")
    def test_weak_test_scores_between(self):
        item = self._clamp()
        output = (
            "```python\n"
            "import unittest\n"
            "from impl import clamp\n"
            "\n"
            "class T(unittest.TestCase):\n"
            "    def test_below(self):\n"
            "        self.assertEqual(clamp(-3, 0, 10), 0)\n"
            "```"
        )
        score = self.mod.grade(item, output)["score"]
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_no_code_block_scores_zero(self):
        result = self.mod.grade(self._clamp(), "Check the boundaries and the swapped case.")
        self.assertEqual(result["score"], 0.0)

    @unittest.skipUnless(SANDBOX, "no usable OS sandbox on this host")
    def test_runs_do_not_share_a_directory(self):
        # The test fails if a file from an earlier run is present, then leaves one.
        # Fresh directories: every mutant run passes too, so all survive (score 0).
        # A shared directory would make every mutant look caught (score 1).
        leftover = (
            "import os, unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_fresh(self):\n"
            "        self.assertFalse(os.path.exists('leftover'))\n"
            "        open('leftover', 'w').write('x')\n"
        )
        with mock.patch.dict(os.environ, {"COCO_SKILL_EXEC_UNTRUSTED": "1"}):
            result = self.mod.grade(self.items[0], "```python\n" + leftover + "```")
        self.assertEqual(result["score"], 0.0, result["notes"])

    def test_items_file(self):
        _assert_split(self, self.items)
        for item in self.items:
            for field in _GT_FIELDS:
                self.assertIn(field, item, item["id"])
            self.assertIsInstance(item["impl"], str)
            self.assertIsInstance(item["reference_tests"], str)
            self.assertEqual(len(item["mutants"]), 3, item["id"])

    def test_reference_tests_kill_every_mutant(self):
        # The reference tests are repository files, not model output, so they run
        # without the sandbox and this check runs on every CI host.
        for item in self.items:
            self.assertTrue(_trusted_pass(item["impl"], item["reference_tests"]), item["id"])
            for index, mutant in enumerate(item["mutants"], start=1):
                self.assertFalse(
                    _trusted_pass(mutant, item["reference_tests"]),
                    f"{item['id']} mutant {index} survived",
                )


def _trusted_pass(impl_src, test_src):
    """Run repository-authored tests against impl_src, unsandboxed (trusted input only)."""
    import subprocess
    import sys
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "impl.py").write_text(impl_src)
        Path(tmp, "test_ref.py").write_text(test_src)
        result = subprocess.run(
            [sys.executable, "-E", "-s", "-B", "-m", "unittest", "-q", "test_ref"],
            cwd=tmp, capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0


class HumanizerGraderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load("humanizer")
        cls.items = _items("humanizer")
        cls.item = next(item for item in cls.items if item["id"] == "hu01")

    def test_multi_part_answer_scores_only_the_final_rewrite(self):
        # The skill delivers a draft, "still-AI" bullets and a final rewrite.
        item = self.items[0]
        clean = " ".join(f"We noted {fact}." for fact in item["facts"])
        clean += " " + " ".join(["The update went out and people liked it."] * 6)
        answer = (
            "## Draft\n" + item["text"] + "\n\n## Still AI\n- em dashes, delve\n\n"
            "## Final rewrite\n" + clean + "\n\n## Summary of changes\nRemoved the tells."
        )
        self.assertGreaterEqual(self.mod.grade(item, answer)["score"], 0.95)
        self.assertEqual(self.mod.final_rewrite(answer), clean)

    def test_final_rewrite_falls_back_to_whole_output(self):
        self.assertEqual(self.mod.final_rewrite("just one paragraph"), "just one paragraph")
        self.assertEqual(self.mod.final_rewrite("**Final rewrite**\nText here."), "Text here.")
        self.assertEqual(self.mod.final_rewrite("Final rewrite:\nText here.\nSummary:\nx"), "Text here.")


    def test_identical_text_scores_low(self):
        result = self.mod.grade(self.item, self.item["text"])
        self.assertLessEqual(result["score"], 0.55)

    def test_clean_rewrite_scores_high(self):
        result = self.mod.grade(self.item, _CLEAN)
        self.assertGreaterEqual(result["score"], 0.95)
        self.assertFalse(any(note.startswith("tell:") for note in result["notes"]))
        self.assertFalse(any("length guard" in note for note in result["notes"]))

    def test_dropping_two_facts_lowers_score(self):
        full = self.mod.grade(self.item, _CLEAN)
        dropped = self.mod.grade(self.item, _DROPPED)
        self.assertFalse(any("length guard" in note for note in full["notes"]))
        self.assertFalse(any("length guard" in note for note in dropped["notes"]))
        self.assertFalse(any(note.startswith("tell:") for note in dropped["notes"]))
        self.assertLess(dropped["score"], full["score"])

    def test_five_word_output_triggers_length_guard(self):
        short = "Five words go right here"
        self.assertEqual(len(short.split()), 5)
        result = self.mod.grade(self.item, short)
        self.assertTrue(any("length guard" in note for note in result["notes"]))

    def test_items_file(self):
        _assert_split(self, self.items)
        for item in self.items:
            for field in _HU_FIELDS:
                self.assertIn(field, item, item["id"])
            self.assertIsInstance(item["text"], str)
            self.assertGreaterEqual(len(item["facts"]), 3, item["id"])
            self.assertLessEqual(len(item["facts"]), 5, item["id"])
            for fact in item["facts"]:
                self.assertIsInstance(fact, str)
                self.assertIn(fact, item["text"], item["id"])


if __name__ == "__main__":
    unittest.main()
