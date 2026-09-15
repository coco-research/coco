"""Tests for the Coco Learning System CLI."""

import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "systems", "learning", "scripts"))

from coco_learning.models import Instinct, Observation
from coco_learning.storage import append_observation, ensure_dirs, save_instinct
from coco_learning.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ["COCO_LEARNING_DIR"] = self.tmpdir
        self.project_id = "cliproj123456789"
        ensure_dirs(self.project_id)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.environ.pop("COCO_LEARNING_DIR", None)

    def _capture(self, argv):
        stdout = StringIO()
        stderr = StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout, stderr
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, stdout.getvalue(), stderr.getvalue()

    def test_status_empty(self):
        code, out, _ = self._capture(["status"])
        self.assertEqual(code, 0)
        self.assertIn("Total active instincts: 0", out)

    def test_status_with_project(self):
        inst = Instinct(
            id="inst-20260905-aaaaaa", pattern="Test pattern",
            domain="testing", confidence=0.55, evidence_count=5,
            created_at="2026-09-05T10:00:00Z", updated_at="2026-09-05T10:00:00Z",
            source_project=self.project_id,
        )
        save_instinct(inst, self.project_id)
        code, out, _ = self._capture(["status", "--project", self.project_id])
        self.assertEqual(code, 0)
        self.assertIn("Project", out)
        self.assertIn("Count: 1", out)

    def test_evolve_requires_project(self):
        # argparse exits with code 2 when required arg missing; our handler catches None
        try:
            code, out, err = self._capture(["evolve"])
            # If we get here, handler caught it
            self.assertEqual(code, 1)
            self.assertIn("--project is required", err)
        except SystemExit as e:
            # argparse raised SystemExit(2) before handler ran — acceptable
            self.assertEqual(e.code, 2)

    def test_evolve_no_observations(self):
        code, out, _ = self._capture(["evolve", "--project", self.project_id])
        self.assertEqual(code, 0)
        self.assertIn("No new patterns", out)

    def test_list_empty(self):
        code, out, _ = self._capture(["list"])
        self.assertEqual(code, 0)
        self.assertIn("No instincts found", out)

    def test_list_with_filter(self):
        inst = Instinct(
            id="inst-20260905-bbbbbb", pattern="Security rule",
            domain="security", confidence=0.6, evidence_count=4,
            created_at="2026-09-05T10:00:00Z", updated_at="2026-09-05T10:00:00Z",
            source_project=self.project_id,
        )
        save_instinct(inst, self.project_id)
        code, out, _ = self._capture(["list", "--project", self.project_id, "--domain", "security"])
        self.assertEqual(code, 0)
        self.assertIn("Security rule", out)

        code2, out2, _ = self._capture(["list", "--project", self.project_id, "--domain", "performance"])
        self.assertEqual(code2, 0)
        self.assertIn("No instincts found", out2)

    def test_promote_not_found(self):
        code, _, err = self._capture(["promote", "inst-20260905-zzzzzz", "--from-project", self.project_id])
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_promote_success(self):
        inst = Instinct(
            id="inst-20260905-cccccc", pattern="Promotable pattern",
            domain="workflow", confidence=0.75, evidence_count=12,
            created_at="2026-09-05T10:00:00Z", updated_at="2026-09-05T10:00:00Z",
            source_project=self.project_id,
        )
        save_instinct(inst, self.project_id)
        code, out, _ = self._capture(["promote", "inst-20260905-cccccc", "--from-project", self.project_id])
        self.assertEqual(code, 0)
        self.assertIn("Promoted", out)

    def test_delete_not_found(self):
        code, _, err = self._capture(["delete", "inst-20260905-zzzzzz"])
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_delete_success(self):
        inst = Instinct(
            id="inst-20260905-dddddd", pattern="To delete",
            domain="testing", confidence=0.4, evidence_count=2,
            created_at="2026-09-05T10:00:00Z", updated_at="2026-09-05T10:00:00Z",
            source_project=self.project_id,
        )
        save_instinct(inst, self.project_id)
        code, out, _ = self._capture(["delete", "inst-20260905-dddddd", "--project", self.project_id])
        self.assertEqual(code, 0)
        self.assertIn("Deleted", out)


if __name__ == "__main__":
    unittest.main()
