#!/usr/bin/env python3
"""The evolution loop's committed ledger, state/ledger.jsonl.

One JSON record per event, append only, newest last, in the shape state/README.md
documents:

  {"cycle", "proposal", "action", "reason", "by", "diff_sha256", "head_sha", "at"}

The ledger is created on the first write, so a missing file is an empty ledger. A line
that does not parse, or does not carry that shape, is an error and never a silent skip:
the rejections are the part of the ledger that matters, and a skipped line could be one.

Exit contract (docs/rules.md R1): 0 pass, 1 blocked by a guard, 2 unrunnable.

API:
  append(record, path=LEDGER)                 write one line atomically
  rejected_recent(diff_sha256, path=LEDGER)   True if that diff was rejected in the window
  read(path=LEDGER)                           every record, oldest first
  All three raise LedgerError on a malformed record or ledger.

CLI:
  ledger.py append --record JSON [--ledger PATH]
      0 appended; 2 record refused, ledger malformed or unwritable
  ledger.py rejected-recent SHA256 [--ledger PATH]
      0 not rejected in the window; 1 rejected in the window; 2 ledger or hash malformed
  ledger.py --self-test
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LEDGER = Path(__file__).resolve().parent.parent / "state" / "ledger.jsonl"
FIELDS = ("cycle", "proposal", "action", "reason", "by", "diff_sha256", "head_sha", "at")
ACTIONS = ("proposed", "merged", "rejected")
DECIDERS = ("loop", "owner")
CYCLE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}$")  # same pattern as proposal-schema.json
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOW = 2  # cycles


class LedgerError(Exception):
    """The record or the ledger is malformed, or the ledger cannot be read or written."""


def _problem(record):
    """Why a record is malformed, or None if it is well formed."""
    if not isinstance(record, dict):
        return "not a JSON object"
    missing = [f for f in FIELDS if not isinstance(record.get(f), str)]
    if missing:
        return "missing or non-string field(s): " + ", ".join(missing)
    if not CYCLE_RE.match(record["cycle"]):
        return f"cycle {record['cycle']!r} is not YYYY-MM"
    if record["action"] not in ACTIONS:
        return f"action {record['action']!r} is not one of {', '.join(ACTIONS)}"
    if record["by"] not in DECIDERS:
        return f"by {record['by']!r} is not one of {', '.join(DECIDERS)}"
    if not SHA256_RE.match(record["diff_sha256"]):
        return "diff_sha256 is not 64 lowercase hex characters"
    if record["action"] == "rejected" and not record["reason"].strip():
        return "a rejection must carry its reason (state/README.md)"
    return None


def _parse(text, path):
    if text and not text.endswith("\n"):
        raise LedgerError(f"{path}: last line is not newline terminated (a torn write?)")
    records = []
    for n, line in enumerate(text.split("\n")[:-1], 1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            raise LedgerError(f"{path} line {n}: not valid JSON ({e.msg})")
        problem = _problem(record)
        if problem:
            raise LedgerError(f"{path} line {n}: {problem}")
        records.append(record)
    return records


def _load(path):
    """(raw bytes, records). A missing ledger is empty: it is created on the first write."""
    try:
        raw = Path(path).read_bytes()
    except FileNotFoundError:
        return b"", []
    except OSError as e:
        raise LedgerError(f"cannot read {path}: {e}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise LedgerError(f"{path}: not UTF-8 ({e})")
    return raw, _parse(text, path)


def read(path=LEDGER):
    return _load(path)[1]


def append(record, path=LEDGER):
    """Append one record as one JSON line. The ledger is either unchanged or one line longer."""
    problem = _problem(record)
    if problem:
        raise LedgerError(f"record refused: {problem}")
    path = Path(path)
    old, _ = _load(path)  # refuse to extend a ledger that is already malformed
    line = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
    # ponytail: atomic by rewrite, not by O_APPEND. The whole ledger is copied to a temp
    # file beside it and os.replace()d over it, so a reader sees the old ledger or the new
    # one and never a torn line. Ceiling: O(ledger size) per append, and last writer wins
    # if two processes append at once. Fine for one writer per cycle and tens of rows a
    # month. Upgrade path: os.open(O_APPEND) with fcntl.flock if the ledger ever gets
    # concurrent writers or grows large.
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".ledger-", suffix=".tmp")
        with os.fdopen(fd, "wb") as f:
            f.write(old + line)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, (path.stat().st_mode & 0o777) if old else 0o644)
        os.replace(tmp, path)
    except OSError as e:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
        raise LedgerError(f"cannot write {path}: {e}")


def _window(records):
    # ponytail: the two cycle window is the two most recent cycle ids present in the
    # ledger (YYYY-MM sorts chronologically), not calendar months and not relative to a
    # passed-in current cycle, because the planned signature is rejected_recent(diff_sha256)
    # and a wall clock would break determinism. The loop validates before it records, so at
    # validation time these are the previous two cycles. Ceiling: a cycle that wrote no row
    # does not count, and a caller that already appended rows for the current cycle sees
    # current plus previous. Upgrade path: an optional current-cycle argument once evolve.py
    # (plan task 8) fixes how a cycle id is minted.
    return sorted({r["cycle"] for r in records})[-WINDOW:]


def rejected_recent(diff_sha256, path=LEDGER):
    """True if a ledger row rejected this diff hash inside the two cycle window."""
    records = read(path)
    window = _window(records)
    return any(r["action"] == "rejected" and r["diff_sha256"] == diff_sha256
               and r["cycle"] in window for r in records)


def _say(msg):
    print(f"ledger: {msg}", file=sys.stderr)


def _cli(args):
    if args.cmd == "append":
        try:
            record = json.loads(args.record)
        except json.JSONDecodeError as e:
            _say(f"record refused: --record is not valid JSON ({e.msg})")
            return 2
        append(record, args.ledger)
        _say(f"appended {record['action']} {record['proposal']} to {args.ledger}")
        return 0
    if args.cmd == "rejected-recent":
        if not SHA256_RE.match(args.diff_sha256):
            _say("diff sha256 must be 64 lowercase hex characters")
            return 2
        if not Path(args.ledger).exists():
            _say(f"no ledger at {args.ledger} yet, so nothing has been rejected")
            return 0
        window = ", ".join(_window(read(args.ledger)))
        if rejected_recent(args.diff_sha256, args.ledger):
            _say(f"{args.diff_sha256[:12]} was rejected inside the two cycle window ({window})")
            return 1
        _say(f"{args.diff_sha256[:12]} not rejected inside the two cycle window ({window})")
        return 0
    _say("nothing to do: give append, rejected-recent or --self-test")
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(description="The evolution loop's committed ledger.")
    parser.add_argument("--self-test", action="store_true", help="run the fixture cases")
    sub = parser.add_subparsers(dest="cmd")
    a = sub.add_parser("append", help="append one record")
    a.add_argument("--record", required=True, help="the record, as one JSON object")
    a.add_argument("--ledger", default=str(LEDGER))
    r = sub.add_parser("rejected-recent", help="exit 1 if the diff was rejected in the window")
    r.add_argument("diff_sha256")
    r.add_argument("--ledger", default=str(LEDGER))
    args = parser.parse_args(argv)  # argparse exits 2 on a usage error, which is R1's 2
    if args.self_test:
        return _self_test()
    try:
        return _cli(args)
    except LedgerError as e:
        _say(str(e))
        return 2
    except Exception as e:  # R1: unrunnable is exit 2 with one line, never a traceback
        _say(f"unrunnable: {type(e).__name__}: {e}")
        return 2


# ---------------------------------------------------------------- self-test

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ledger"
SHA_OUTSIDE = "a" * 64   # rejected in 2026-08, which is outside the window
SHA_MERGED = "b" * 64    # proposed and merged in 2026-09, never rejected
SHA_OLDER = "d" * 64     # rejected in 2026-09, the older cycle inside the window
SHA_LATEST = "c" * 64    # rejected in 2026-10, the latest cycle


def _record(**over):
    rec = {"cycle": "2026-11", "proposal": "2026-11-1", "action": "proposed",
           "reason": "zero invocations in the window despite three edits", "by": "loop",
           "diff_sha256": "e" * 64, "head_sha": "1" * 40, "at": "2026-11-01T00:00:00Z"}
    rec.update(over)
    return rec


def _self_test():
    results = []

    def cli(*args):
        return subprocess.run([sys.executable, __file__, *args], capture_output=True, text=True)

    def case(name, fn):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "ledger"
            shutil.copytree(FIXTURES, work)
            try:
                fn(work)
                results.append((name, None))
            except AssertionError as e:
                results.append((name, str(e) or "assertion failed"))

    def expect(res, rc, needle):
        assert res.returncode == rc, f"exit {res.returncode}, want {rc}; stderr: {res.stderr.strip()}"
        assert needle in res.stderr, f"stderr lacks {needle!r}: {res.stderr.strip()}"

    def append_to_missing(work):
        ledger = work / "new.jsonl"
        rec = _record()
        expect(cli("append", "--ledger", str(ledger), "--record", json.dumps(rec)), 0, "appended")
        assert ledger.read_text() == json.dumps(rec, sort_keys=True) + "\n", "not one canonical line"
        leftovers = [p.name for p in work.iterdir() if p.name.startswith(".ledger-")]
        assert not leftovers, f"temp files left behind: {leftovers}"

    def append_to_chain(work):
        ledger = work / "chain.jsonl"
        before = ledger.read_bytes()
        rec = _record()
        expect(cli("append", "--ledger", str(ledger), "--record", json.dumps(rec)), 0, "appended")
        after = ledger.read_bytes()
        assert after.startswith(before), "existing rows were changed"
        assert after[len(before):] == (json.dumps(rec, sort_keys=True) + "\n").encode(), "bad new line"
        assert len(read(ledger)) == len(before.splitlines()) + 1, "not exactly one row longer"

    def rejected_latest(work):
        expect(cli("rejected-recent", SHA_LATEST, "--ledger", str(work / "chain.jsonl")),
               1, "rejected inside the two cycle window (2026-09, 2026-10)")

    def rejected_older(work):
        expect(cli("rejected-recent", SHA_OLDER, "--ledger", str(work / "chain.jsonl")),
               1, "rejected inside the two cycle window")

    def not_rejected_outside(work):
        expect(cli("rejected-recent", SHA_OUTSIDE, "--ledger", str(work / "chain.jsonl")),
               0, "not rejected inside the two cycle window")

    def not_rejected_merged(work):
        expect(cli("rejected-recent", SHA_MERGED, "--ledger", str(work / "chain.jsonl")),
               0, "not rejected inside the two cycle window")

    def malformed_line(work):
        expect(cli("rejected-recent", SHA_LATEST, "--ledger", str(work / "malformed.jsonl")),
               2, "line 2: not valid JSON")

    def malformed_blocks_append(work):
        ledger = work / "malformed.jsonl"
        before = ledger.read_bytes()
        expect(cli("append", "--ledger", str(ledger), "--record", json.dumps(_record())),
               2, "line 2: not valid JSON")
        assert ledger.read_bytes() == before, "a malformed ledger was extended"

    def shape_error_is_error(work):
        ledger = work / "shape.jsonl"
        good = json.dumps(_record(), sort_keys=True)
        ledger.write_text(good + "\n" + json.dumps({"cycle": "2026-11"}) + "\n")
        expect(cli("rejected-recent", SHA_LATEST, "--ledger", str(ledger)), 2, "line 2: missing")

    def torn_last_line(work):
        ledger = work / "torn.jsonl"
        ledger.write_text((work / "chain.jsonl").read_text().rstrip("\n"))
        expect(cli("rejected-recent", SHA_LATEST, "--ledger", str(ledger)), 2, "newline terminated")

    def missing_ledger(work):
        ledger = work / "absent.jsonl"
        expect(cli("rejected-recent", SHA_LATEST, "--ledger", str(ledger)), 0, "no ledger")
        assert not ledger.exists(), "a read created the ledger"

    def rejection_needs_reason(work):
        ledger = work / "chain.jsonl"
        before = ledger.read_bytes()
        rec = _record(action="rejected", by="owner", reason="  ")
        expect(cli("append", "--ledger", str(ledger), "--record", json.dumps(rec)), 2, "reason")
        assert ledger.read_bytes() == before, "a refused record was written"

    def bad_hash_argument(work):
        expect(cli("rejected-recent", "not-a-hash", "--ledger", str(work / "chain.jsonl")),
               2, "64 lowercase hex")

    def unwritable_ledger(work):
        ledger = work / "no-such-dir" / "ledger.jsonl"
        expect(cli("append", "--ledger", str(ledger), "--record", json.dumps(_record())),
               2, "cannot write")

    for name, fn in [
        ("append to a missing ledger creates it with one line", append_to_missing),
        ("append to an existing chain adds exactly one line", append_to_chain),
        ("rejected-recent true, latest cycle", rejected_latest),
        ("rejected-recent true, older cycle inside the window", rejected_older),
        ("rejected-recent false, rejected outside the window", not_rejected_outside),
        ("rejected-recent false, never rejected", not_rejected_merged),
        ("malformed line is an error, exit 2", malformed_line),
        ("malformed ledger is not extended", malformed_blocks_append),
        ("JSON line without the record shape is an error", shape_error_is_error),
        ("torn last line is an error", torn_last_line),
        ("missing ledger file reads as empty", missing_ledger),
        ("rejection without a reason is refused", rejection_needs_reason),
        ("malformed hash argument is exit 2", bad_hash_argument),
        ("unwritable ledger is exit 2", unwritable_ledger),
    ]:
        case(name, fn)

    for name, err in results:
        print(f"{'PASS' if err is None else 'FAIL'}  {name}" + ("" if err is None else f": {err}"))
    passed = sum(1 for _, err in results if err is None)
    print(f"ledger self-test: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
