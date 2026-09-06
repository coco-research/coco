"""Tests for the Coco Learning System Brain DB sync."""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "systems", "learning", "scripts"))

from coco_learning.models import Instinct
from coco_learning.storage import save_instinct, ensure_dirs
from coco_learning.brain_sync import (
    instinct_to_decision,
    sync_instincts_to_brain,
    get_sync_status,
    _find_brain_db,
)


class TestBrainSync(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ["COCO_LEARNING_DIR"] = self.tmpdir
        self.project_id = "brainproj123456789"
        ensure_dirs(self.project_id)
        
        # Create a mock Brain DB
        self.brain_dir = os.path.join(self.tmpdir, ".brain")
        os.makedirs(self.brain_dir, exist_ok=True)
        self.brain_db = os.path.join(self.brain_dir, "brain.db")
        conn = sqlite3.connect(self.brain_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                status TEXT DEFAULT 'proposed',
                created_at TEXT,
                tags TEXT
            )
        """)
        conn.commit()
        conn.close()
        
        # Point brain_sync to our test DB
        os.environ["COCO_BRAIN_DB"] = self.brain_db

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.environ.pop("COCO_LEARNING_DIR", None)
        os.environ.pop("COCO_BRAIN_DB", None)

    def _make_instinct(self, confidence=0.7, domain="testing", pattern="Test pattern"):
        inst = Instinct(
            id=f"inst-20260905-{domain[:6]}",
            pattern=pattern,
            domain=domain,
            confidence=confidence,
            evidence_count=10,
            created_at="2026-09-05T10:00:00Z",
            updated_at="2026-09-05T10:00:00Z",
            source_project=self.project_id,
            tags=["test"],
        )
        save_instinct(inst, self.project_id)
        return inst

    def test_instinct_to_decision_format(self):
        inst = self._make_instinct(confidence=0.75, domain="security", pattern="Check auth")
        decision = instinct_to_decision(inst)
        self.assertIn("[security]", decision["title"])
        self.assertIn("Check auth", decision["title"])
        self.assertEqual(decision["status"], "accepted")
        self.assertIn("coco-learning", decision["tags"])

    def test_instinct_to_decision_proposed_status(self):
        inst = self._make_instinct(confidence=0.55)
        decision = instinct_to_decision(inst)
        self.assertEqual(decision["status"], "proposed")

    def test_sync_no_brain_db(self):
        os.environ.pop("COCO_BRAIN_DB", None)
        result = sync_instincts_to_brain(project_root="/nonexistent/path")
        self.assertGreater(len(result["errors"]), 0)
        self.assertIn("not found", result["errors"][0])

    def test_sync_no_eligible_instincts(self):
        result = sync_instincts_to_brain(self.project_id, min_confidence=0.5)
        self.assertEqual(result["synced"], 0)

    def test_sync_creates_decisions(self):
        self._make_instinct(confidence=0.7)
        result = sync_instincts_to_brain(self.project_id, min_confidence=0.5)
        self.assertEqual(result["synced"], 1)
        self.assertEqual(len(result["decisions"]), 1)
        
        # Verify in DB
        conn = sqlite3.connect(self.brain_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM decisions WHERE tags LIKE '%coco-learning%'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)

    def test_sync_skips_already_synced(self):
        self._make_instinct(confidence=0.7)
        sync_instincts_to_brain(self.project_id, min_confidence=0.5)
        result = sync_instincts_to_brain(self.project_id, min_confidence=0.5)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["synced"], 0)

    def test_sync_respects_min_confidence(self):
        self._make_instinct(confidence=0.4, pattern="Low confidence")
        result = sync_instincts_to_brain(self.project_id, min_confidence=0.5)
        self.assertEqual(result["synced"], 0)

    def test_sync_dry_run(self):
        self._make_instinct(confidence=0.7)
        result = sync_instincts_to_brain(self.project_id, min_confidence=0.5, dry_run=True)
        self.assertEqual(result["synced"], 1)
        
        # Verify NOT in DB
        conn = sqlite3.connect(self.brain_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM decisions")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 0)

    def test_get_sync_status_no_db(self):
        os.environ.pop("COCO_BRAIN_DB", None)
        status = get_sync_status("/nonexistent")
        self.assertFalse(status["brain_db_found"])

    def test_get_sync_status_with_db(self):
        self._make_instinct(confidence=0.7)
        sync_instincts_to_brain(self.project_id, min_confidence=0.5)
        status = get_sync_status()
        self.assertTrue(status["brain_db_found"])
        self.assertEqual(status["learning_decisions"], 1)


if __name__ == "__main__":
    unittest.main()
