"""meta_select.select() records one opt-in, local M0 row per call, plus outcome rows."""

import contextlib
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "systems", "superintelligence", "scripts"))

import meta_select  # noqa: E402

PROMPT = "secret launch plan: should we price the compliance product at $40k?"
# Far enough past 600s that a slow test run cannot fall back inside the window.
REROUTE_GAP_S = 1000
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

    def parsed(self):
        out = []
        for row in self.rows():
            raw = row.get("meta_json")
            row = dict(row)
            row["meta"] = json.loads(raw) if raw else {}
            out.append(row)
        return out

    def decision_rows(self):
        return [r for r in self.parsed() if "prompt_hmac_sha256" in r["meta"] and "outcome" not in r["meta"]]

    def outcome_rows(self):
        return [r for r in self.parsed() if "outcome" in r["meta"]]

    def newest_decision(self):
        rows = self.decision_rows()
        self.assertTrue(rows)
        return max(rows, key=lambda r: (r["ts"], r["id"]))

    def shift_ts(self, row_id, seconds_ago):
        stamp = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
        ts = stamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")
        conn = sqlite3.connect(self.db)
        try:
            cur = conn.execute("UPDATE operational_thread SET ts = ? WHERE id = ?", (ts, row_id))
            conn.commit()
            self.assertEqual(cur.rowcount, 1)
        finally:
            conn.close()

    def assert_exit2(self, argv):
        """Exit 2 with stdout empty and one line on stderr. Returns that line."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as caught:
                meta_select.main(argv)
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(out.getvalue(), "")
        text = err.getvalue()
        self.assertEqual(text.count("\n"), 1)
        self.assertTrue(text.strip())
        return text.strip()

    def run_summary(self, *extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            meta_select.main(["--outcomes-summary", *extra])
        return json.loads(buf.getvalue())

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
        import hashlib, hmac
        salt_path = os.path.join(self.tmp.name, meta_select.M0_SALT_NAME)
        self.assertEqual(os.stat(salt_path).st_mode & 0o777, 0o600)
        salt = open(salt_path, "rb").read()
        self.assertEqual(len(salt), 32)
        macs = {hmac.new(salt, p.encode(), hashlib.sha256).hexdigest() for p in (PROMPT, PROMPT + " v2")}
        self.assertIn(meta["prompt_hmac_sha256"], macs)
        self.assertNotIn(hashlib.sha256(PROMPT.encode()).hexdigest(), json.dumps(rows))
        self.assertIn(meta["prompt_hmac_sha256"][:12], rows[0]["text"] if "text" in rows[0] else json.dumps(rows[0]))
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
        broken.db_path = self.db
        broken.write.side_effect = RuntimeError("disk full")
        with mock.patch.object(meta_select, "_m0_store", return_value=broken):
            out = meta_select.select(PROMPT)
        self.assertEqual(out["teams"][0]["team_key"], "risk-compliance")
        broken.write.assert_called_once()

    def test_store_sys_exit_does_not_break_routing(self):
        os.environ[meta_select.M0_FLAG] = "1"
        with mock.patch.object(meta_select, "_m0_store", side_effect=SystemExit(2)):
            out = meta_select.select(PROMPT)
        self.assertEqual(out["teams"][0]["team_key"], "risk-compliance")
        self.assertEqual(self.rows(), [])

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

    def test_same_prompt_within_600s_writes_one_rerouted(self):
        os.environ[meta_select.M0_FLAG] = "1"
        meta_select.select(PROMPT)
        first = self.newest_decision()["id"]
        meta_select.select(PROMPT)
        # Same inputs hash to one decision id, so the second write does not insert.
        outcomes = self.outcome_rows()
        self.assertEqual(len(outcomes), 1)
        self.assertEqual([r["id"] for r in self.decision_rows()], [first])
        row = outcomes[0]
        self.assertEqual(row["project"], meta_select.M0_PROJECT)
        self.assertEqual(row["kind"], "ambient_signal")
        self.assertEqual(row["source_tool"], "meta_select")
        self.assertEqual(row["meta"], {"decision_id": first, "outcome": "rerouted"})
        self.assertEqual(row["text"], f"router outcome rerouted {first[:12]}")

    def test_different_prompts_do_not_reroute(self):
        os.environ[meta_select.M0_FLAG] = "1"
        meta_select.select(PROMPT)
        meta_select.select(PROMPT + " v2")
        self.assertEqual(self.outcome_rows(), [])
        self.assertEqual(len(self.decision_rows()), 2)

    def test_same_prompt_after_600s_does_not_reroute(self):
        os.environ[meta_select.M0_FLAG] = "1"
        meta_select.select(PROMPT)
        first = self.newest_decision()["id"]
        self.shift_ts(first, REROUTE_GAP_S)
        meta_select.select(PROMPT)
        self.assertEqual(self.outcome_rows(), [])
        self.assertEqual([r["id"] for r in self.decision_rows()], [first])

    def test_outcome_cli(self):
        self.assert_exit2(["--outcome", "kept"])
        self.assertFalse(os.path.exists(self.db))

        os.environ[meta_select.M0_FLAG] = "1"
        self.assert_exit2(["--outcome", "kept"])
        self.assert_exit2(["--outcome", "bad", "--decision", "0" * 64])
        self.assertEqual(self.outcome_rows(), [])

        meta_select.select(PROMPT)
        first = self.newest_decision()["id"]
        self.shift_ts(first, 5)
        meta_select.select(PROMPT + " v2")
        second = self.newest_decision()["id"]
        self.assertNotEqual(first, second)

        self.assert_exit2(["--outcome", "nope"])
        self.assertEqual(self.outcome_rows(), [])

        meta_select.main(["--outcome", "kept"])
        meta_select.main(["--outcome", "overridden", "--decision", first])
        by_outcome = {r["meta"]["outcome"]: r for r in self.outcome_rows()}
        self.assertEqual(set(by_outcome), {"kept", "overridden"})
        self.assertEqual(by_outcome["kept"]["meta"]["decision_id"], second)
        self.assertEqual(by_outcome["kept"]["text"], f"router outcome kept {second[:12]}")
        self.assertEqual(by_outcome["overridden"]["meta"]["decision_id"], first)
        self.assertEqual(by_outcome["overridden"]["text"], f"router outcome overridden {first[:12]}")

        os.environ.pop(meta_select.M0_FLAG, None)
        before = len(self.rows())
        self.assert_exit2(["--outcome", "bad"])
        self.assertEqual(len(self.rows()), before)

    def test_outcomes_summary_counts(self):
        self.assert_exit2(["--outcomes-summary"])
        self.assertFalse(os.path.exists(self.db))

        os.environ[meta_select.M0_FLAG] = "1"
        empty = self.run_summary()
        self.assertEqual(empty, {
            "days": 7,
            "decisions": 0,
            "outcomes": {"kept": 0, "overridden": 0, "rerouted": 0, "bad": 0},
            "no_outcome_kept": 0,
        })

        # Ages are past the reroute window, so planting rows does not write rerouted.
        plan = [
            (" A", 2 * 3600, None),
            (" B", 30 * 3600, None),
            (" C", 30 * 3600, "kept"),
            (" D", 3 * 86400, "overridden"),
            (" E", 3 * 86400, "rerouted"),
            (" F", 4 * 86400, "bad"),
            (" G", 8 * 86400, None),
        ]
        for suffix, age, outcome in plan:
            meta_select.select(PROMPT + suffix)
            row_id = self.newest_decision()["id"]
            self.shift_ts(row_id, age)
            if outcome == "rerouted":
                meta_select._write_outcome(meta_select._m0_store(), row_id, outcome)
            elif outcome:
                meta_select.main(["--outcome", outcome, "--decision", row_id])

        before = len(self.rows())
        report = self.run_summary("--days", "7")
        self.assertEqual(len(self.rows()), before)
        self.assertEqual(report["days"], 7)
        self.assertEqual(report["decisions"], 6)
        self.assertEqual(report["outcomes"], {"kept": 1, "overridden": 1, "rerouted": 1, "bad": 1})
        self.assertEqual(report["no_outcome_kept"], 1)

    def test_cli_errors_go_to_stderr_with_stdout_empty(self):
        cases = [
            (False, ["--outcome", "kept"], "COCO_ROUTER_M0=1 required"),
            (False, ["--outcomes-summary"], "COCO_ROUTER_M0=1 required"),
            (True, ["--outcomes-summary", "--days", "0"], "invalid days"),
            (True, ["--outcomes-summary", "--days", "x"], "invalid days"),
            (True, ["--outcomes-summary", "--days"], "invalid days"),
            (True, ["--outcome"], "unknown outcome"),
            (True, ["--outcome", "nope"], "unknown outcome"),
            (True, ["--outcome", "rerouted"], "unknown outcome"),
            (True, ["--outcome", "kept"], "no decision found"),
            (True, ["--outcome", "kept", "--decision", "0" * 64], "no decision found"),
            (True, ["--outcome", "kept", "--decision"], "no decision found"),
        ]
        for flag_on, argv, message in cases:
            with self.subTest(argv=argv, flag_on=flag_on):
                if flag_on:
                    os.environ[meta_select.M0_FLAG] = "1"
                else:
                    os.environ.pop(meta_select.M0_FLAG, None)
                self.assertEqual(self.assert_exit2(argv), message)
        self.assertEqual(self.outcome_rows(), [])

    def test_double_dash_ends_options(self):
        os.environ[meta_select.M0_FLAG] = "1"
        # Each of these starts with a CLI command word. After `--` it is just the prompt.
        for argv, prompt in (
            (["--", "--outcome bad"], "--outcome bad"),
            (["--", "--outcome", "kept"], "--outcome kept"),
            (["--", "--outcomes-summary"], "--outcomes-summary"),
        ):
            with self.subTest(argv=argv):
                out = io.StringIO()
                with mock.patch.object(meta_select, "_select", return_value=dict(FAKE)) as sel:
                    with contextlib.redirect_stdout(out):
                        meta_select.main(argv)
                sel.assert_called_once_with(prompt)
                self.assertEqual(json.loads(out.getvalue())["method"], "embed")  # a routing result
        self.assertEqual(self.outcome_rows(), [])
        self.assertEqual(len(self.decision_rows()), 3)

    def test_double_dash_alone_is_usage_not_a_prompt(self):
        os.environ[meta_select.M0_FLAG] = "1"
        with mock.patch.object(meta_select, "_select") as sel:
            with self.assertRaises(SystemExit) as caught:
                meta_select.main(["--"])
        self.assertTrue(str(caught.exception.code).startswith("usage:"))
        sel.assert_not_called()
        self.assertEqual(self.rows(), [])

    def test_outcomes_summary_flags_a_full_page(self):
        os.environ[meta_select.M0_FLAG] = "1"
        store = meta_select._m0_store()
        cap = meta_select.SUMMARY_LIMIT

        def write_kept(first, stop):
            for i in range(first, stop):
                digest = hashlib.sha256(str(i).encode()).hexdigest()
                meta_select._write_outcome(store, digest, "kept")

        write_kept(0, cap - 1)  # one short of a full page: complete, so no flag
        report = self.run_summary()
        self.assertEqual(report["outcomes"]["kept"], cap - 1)
        self.assertNotIn("truncated", report)
        self.assertNotIn("rows_read", report)

        write_kept(cap - 1, cap)  # exactly a full page: older rows may exist, so flag it
        report = self.run_summary()
        self.assertIs(report["truncated"], True)
        self.assertEqual(report["rows_read"], cap)
        self.assertEqual(report["outcomes"]["kept"], cap)

        write_kept(cap, cap + 1)  # past the page: the oldest row is not counted
        report = self.run_summary()
        self.assertIs(report["truncated"], True)
        self.assertEqual(report["rows_read"], cap)
        self.assertEqual(report["outcomes"]["kept"], cap)

    def test_outcome_rows_omit_prompt_and_hmac(self):
        os.environ[meta_select.M0_FLAG] = "1"
        meta_select.select(PROMPT)
        first = self.newest_decision()
        digest = first["meta"]["prompt_hmac_sha256"]
        meta_select.select(PROMPT)
        meta_select.main(["--outcome", "bad", "--decision", first["id"]])
        blob = json.dumps(self.outcome_rows())
        self.assertNotIn(digest, blob)
        self.assertNotIn("prompt_hmac_sha256", blob)
        for fragment in ("secret launch plan", "$40k", "compliance product"):
            self.assertNotIn(fragment, blob)
        for row in self.outcome_rows():
            self.assertEqual(set(row["meta"]), {"decision_id", "outcome"})

    def test_reroute_lookup_error_still_records_decision(self):
        os.environ[meta_select.M0_FLAG] = "1"
        real = meta_select._m0_store()

        class Boom:
            db_path = real.db_path

            def read(self, *args, **kwargs):
                raise RuntimeError("lookup down")

            def write(self, payload):
                return real.write(payload)

        with mock.patch.object(meta_select, "_m0_store", return_value=Boom()):
            out = meta_select.select(PROMPT)
        self.assertEqual(out["teams"][0]["team_key"], "risk-compliance")
        rows = self.decision_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(self.outcome_rows(), [])
        self.assertIn("prompt_hmac_sha256", rows[0]["meta"])


if __name__ == "__main__":
    unittest.main()
