"""Tests for the Coco Learning System pattern detector."""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "systems", "learning", "scripts"))

from coco_learning.models import Observation
from coco_learning.storage import append_observation, ensure_dirs, list_instincts
from coco_learning.detector import detect_patterns, run_detection_cycle, load_observations


class TestDetector(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ["COCO_LEARNING_DIR"] = self.tmpdir
        self.project_id = "testproj999999"
        ensure_dirs(self.project_id)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.environ.pop("COCO_LEARNING_DIR", None)

    def _seed(self, events):
        for event, tool, inp, out in events:
            obs = Observation(
                timestamp="2026-09-05T22:00:00Z",
                event=event, session="s1", tool=tool,
                input_summary=inp, output_summary=out,
                project_id=self.project_id, project_name="test",
            )
            append_observation(obs)

    def test_no_observations_returns_empty(self):
        result = detect_patterns(self.project_id)
        self.assertEqual(result, [])

    def test_below_min_evidence_returns_empty(self):
        self._seed([
            ("PostToolUse", "Bash", "npm test", "passed"),
            ("PostToolUse", "Bash", "npm test", "passed"),
        ])
        result = detect_patterns(self.project_id, min_evidence=3)
        self.assertEqual(result, [])

    def test_detects_testing_pattern(self):
        self._seed([
            ("PostToolUse", "Bash", "npm test", "12 passed"),
            ("PostToolUse", "Bash", "pytest", "all green"),
            ("PostToolUse", "Bash", "cargo test", "ok"),
        ])
        result = detect_patterns(self.project_id, min_evidence=3)
        patterns = [i.pattern for i in result]
        self.assertTrue(any("test" in p.lower() for p in patterns))

    def test_detects_security_pattern(self):
        self._seed([
            ("PostToolUse", "Write", "password=secret", "wrote"),
            ("PostToolUse", "Edit", "api_key=abc", "updated"),
            ("PostToolUse", "Write", "token=xyz", "saved"),
        ])
        result = detect_patterns(self.project_id, min_evidence=3)
        patterns = [i.pattern for i in result]
        self.assertTrue(any("secret" in p.lower() for p in patterns))

    def test_reinforces_existing_instinct(self):
        self._seed([
            ("PostToolUse", "Bash", "npm test", "pass"),
            ("PostToolUse", "Bash", "npm test", "pass"),
            ("PostToolUse", "Bash", "npm test", "pass"),
        ])
        first = run_detection_cycle(self.project_id, auto_save=True)
        self.assertGreater(len(first), 0)
        first_evidence = first[0].evidence_count

        # Add more observations and re-detect
        self._seed([
            ("PostToolUse", "Bash", "npm test", "pass again"),
            ("PostToolUse", "Bash", "npm test", "still passing"),
        ])
        second = run_detection_cycle(self.project_id, auto_save=True)
        self.assertGreater(len(second), 0)
        # Evidence should have increased
        self.assertGreaterEqual(second[0].evidence_count, first_evidence)

    def test_run_detection_cycle_saves_to_disk(self):
        self._seed([
            ("PostToolUse", "Bash", "git commit -m fix", "done"),
            ("PostToolUse", "Bash", "git commit -m feat", "done"),
            ("PostToolUse", "Bash", "git commit -m refactor", "done"),
        ])
        instincts = run_detection_cycle(self.project_id, auto_save=True)
        self.assertGreater(len(instincts), 0)
        # Verify persisted
        on_disk = list_instincts(self.project_id)
        self.assertGreater(len(on_disk), 0)

    def test_load_observations_respects_limit(self):
        self._seed([
            ("PostToolUse", "Bash", f"cmd-{i}", "out") for i in range(20)
        ])
        obs = load_observations(self.project_id, limit=5)
        self.assertEqual(len(obs), 5)

    def test_confidence_increases_with_evidence(self):
        self._seed([
            ("PostToolUse", "Bash", "npm test", "pass") for _ in range(10)
        ])
        result = detect_patterns(self.project_id, min_evidence=3)
        self.assertGreater(len(result), 0)
        inst = result[0]
        self.assertGreater(inst.confidence, 0.3)
        self.assertLessEqual(inst.confidence, 0.9)


if __name__ == "__main__":
    unittest.main()
