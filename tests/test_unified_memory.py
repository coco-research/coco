"""Tests for the Coco Unified Memory cross-agent context vault."""

import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "systems", "learning", "scripts"))

from coco_learning.models import Instinct
from coco_learning.storage import save_instinct, ensure_dirs
from coco_learning.unified_memory import (
    init_vault,
    upsert_entry,
    resolve_context,
    sync_all_sources,
    format_context_block,
)


class TestUnifiedMemory(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ["COCO_LEARNING_DIR"] = self.tmpdir
        os.environ["COCO_VAULT_DB"] = os.path.join(self.tmpdir, "vault.db")
        self.project_id = "memproj123456789"
        ensure_dirs(self.project_id)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.environ.pop("COCO_LEARNING_DIR", None)
        os.environ.pop("COCO_VAULT_DB", None)

    def test_init_vault_creates_db(self):
        db_path = init_vault()
        self.assertTrue(db_path.exists())
        conn = sqlite3.connect(str(db_path))
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()
        self.assertIn("context_entries", tables)
        self.assertIn("access_log", tables)

    def test_upsert_insert_and_update(self):
        eid = upsert_entry(
            source="instinct", source_id="inst-001",
            domain="testing", content="Run tests always",
            project_id=self.project_id, relevance_score=0.7,
            tags=["testing"],
        )
        self.assertGreater(eid, 0)

        # Update same entry
        eid2 = upsert_entry(
            source="instinct", source_id="inst-001",
            domain="testing", content="Run tests always (updated)",
            project_id=self.project_id, relevance_score=0.8,
        )
        self.assertEqual(eid, eid2)

        # Verify only one row
        conn = sqlite3.connect(os.environ["COCO_VAULT_DB"])
        count = conn.execute("SELECT COUNT(*) FROM context_entries").fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)

    def test_resolve_context_empty_vault(self):
        results = resolve_context(self.project_id)
        self.assertEqual(results, [])

    def test_resolve_context_returns_ranked(self):
        upsert_entry("instinct", "i1", "testing", "Low score", self.project_id, 0.3)
        upsert_entry("instinct", "i2", "security", "High score", self.project_id, 0.9)
        upsert_entry("instinct", "i3", "workflow", "Mid score", self.project_id, 0.6)

        results = resolve_context(self.project_id, limit=3)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["source_id"], "i2")
        self.assertAlmostEqual(results[0]["score"], 0.9)

    def test_resolve_context_logs_access(self):
        upsert_entry("instinct", "i1", "testing", "Content", self.project_id, 0.5)
        resolve_context(self.project_id, session_id="sess-abc", role="code-reviewer")

        conn = sqlite3.connect(os.environ["COCO_VAULT_DB"])
        logs = conn.execute("SELECT * FROM access_log").fetchall()
        conn.close()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0][1], "sess-abc")
        self.assertEqual(logs[0][2], "code-reviewer")

    def test_sync_all_sources_instincts(self):
        inst = Instinct(
            id="inst-20260905-sync01", pattern="Sync test pattern",
            domain="testing", confidence=0.65, evidence_count=8,
            created_at="2026-09-05T10:00:00Z", updated_at="2026-09-05T10:00:00Z",
            source_project=self.project_id, tags=["sync"],
        )
        save_instinct(inst, self.project_id)

        stats = sync_all_sources(self.project_id)
        self.assertEqual(stats["instincts"], 1)

        results = resolve_context(self.project_id)
        self.assertEqual(len(results), 1)
        self.assertIn("Sync test pattern", results[0]["content"])

    def test_format_context_block_empty(self):
        self.assertEqual(format_context_block([]), "")

    def test_format_context_block_rendered(self):
        entries = [
            {"source": "instinct", "domain": "testing", "content": "Run tests", "tags": ["t"]},
            {"source": "decision", "domain": "workflow", "content": "Commit often", "tags": []},
        ]
        block = format_context_block(entries)
        self.assertIn("<unified_memory>", block)
        self.assertIn("</unified_memory>", block)
        self.assertIn("[instinct:testing]", block)
        self.assertIn("[decision:workflow]", block)
        self.assertIn("tags: t", block)


if __name__ == "__main__":
    unittest.main()
