"""meta_select.select() records one opt-in, local M0 row per call (router eval audit step 4)."""

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "systems", "superintelligence", "scripts"))

import meta_select  # noqa: E402

PROMPT = "secret launch plan: should we price the compliance product at $40k?"
FAKE = {"prompt": PROMPT, "method": "embed", "delegate": True, "delegate_team": "risk-compliance-id",
        "teams": [{"team_key": "risk-compliance"}, {"team_key": "legal-ip"}]}


class M0RecordTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "thread.db")
        self.env = mock.patch.dict(os.environ, {"M0_DB": self.db}, clear=False)
        self.env.start()
        os.environ.pop(meta_select.M0_FLAG, None)
        self.sel = mock.patch.object(meta_select, "_select", return_value=dict(FAKE))
        self.sel.start()

    def tearDown(self):
        self.sel.stop()
        self.env.stop()
        self.tmp.cleanup()

    def rows(self):
        if not os.path.exists(self.db):
            return []
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in conn.execute("SELECT * FROM operational_thread")]
        finally:
            conn.close()

    def test_off_by_default(self):
        meta_select.select(PROMPT)
        self.assertFalse(os.path.exists(self.db))

    def test_flag_other_than_1_is_off(self):
        os.environ[meta_select.M0_FLAG] = "true"
        meta_select.select(PROMPT)
        self.assertFalse(os.path.exists(self.db))

    def test_one_row_per_call_with_hash_teams_delegate(self):
        os.environ[meta_select.M0_FLAG] = "1"
        meta_select.select(PROMPT)
        meta_select.select(PROMPT + " v2")
        rows = self.rows()
        self.assertEqual(len(rows), 2)
        meta = json.loads(rows[0]["meta_json"])
        import hashlib
        self.assertIn(meta["prompt_sha256"], {hashlib.sha256(p.encode()).hexdigest() for p in (PROMPT, PROMPT + " v2")})
        self.assertEqual(meta["teams"], ["risk-compliance", "legal-ip"])
        self.assertTrue(meta["delegate"])
        self.assertEqual(meta["delegate_team"], "risk-compliance")
        self.assertEqual(rows[0]["project"], meta_select.M0_PROJECT)

    def test_never_stores_raw_prompt(self):
        os.environ[meta_select.M0_FLAG] = "1"
        meta_select.select(PROMPT)
        blob = json.dumps(self.rows())
        for fragment in ("secret launch plan", "$40k", "compliance product"):
            self.assertNotIn(fragment, blob)
        with open(self.db, "rb") as f:
            self.assertNotIn(b"secret launch plan", f.read())

    def test_write_failure_does_not_break_routing(self):
        os.environ[meta_select.M0_FLAG] = "1"
        broken = mock.Mock()
        broken.write.side_effect = RuntimeError("disk full")
        out = meta_select.select(PROMPT)  # real store works
        self.assertEqual(out["teams"][0]["team_key"], "risk-compliance")
        self.assertIsNone(meta_select.m0_record(PROMPT, out, store=broken))

    def test_keyword_path_records_no_delegate(self):
        os.environ[meta_select.M0_FLAG] = "1"
        self.sel.stop()
        try:
            with mock.patch.object(meta_select, "select_embed", side_effect=OSError("no endpoint")):
                out = meta_select.select("plan our series A pitch")
        finally:
            self.sel.start()
        self.assertEqual(out["method"], "keyword")
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        meta = json.loads(rows[0]["meta_json"])
        self.assertFalse(meta["delegate"])
        self.assertIsNone(meta["delegate_team"])
        self.assertEqual(meta["method"], "keyword")


if __name__ == "__main__":
    unittest.main()
