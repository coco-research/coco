#!/usr/bin/env python3
"""Generate static test fixtures for gate_state.py.

Generates fixture directories deterministically under skills/team-gate/scripts/fixtures/gate_state/.
Use TEAM_FIXED_TS env var (e.g., 2026-01-01T00:00:00Z) to override timestamps for stable hashes.

Fixtures generated:
  - chain-intact: valid 3-record chain with head.json
  - chain-corrupted-tail: last line of receipts.jsonl truncated to 20 chars (invalid JSON)
  - chain-tail-dropped: last full receipt line removed, head.json left untouched
  - chain-inserted: a record spliced with mismatched prev_hash
  - orphan-gate-file: gates/8.json present with no gate-result receipt naming it
  - run-not-started: empty directory (no receipts.jsonl)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any


FIXTURES_DIR = Path(__file__).parent
FIXED_TS = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")


def _sha256_json(obj: Dict[str, Any]) -> str:
    """Compute SHA-256 over canonical JSON."""
    import hashlib
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _setup_fixture_pointer(fixture_dir: Path, fixture_name: str) -> None:
    """Create .team-ship/RUN pointer so find_run can locate this fixture.

    Uses relative path from parent (gate_state) so state_root() + run_id resolves correctly.
    """
    team_ship_dir = fixture_dir / ".team-ship"
    team_ship_dir.mkdir(exist_ok=True)
    (team_ship_dir / "RUN").write_text(f"gate_state/{fixture_name}")


def make_chain_intact():
    """Valid chain with 3 records and matching head.json."""
    fixture_dir = FIXTURES_DIR / "chain-intact"
    fixture_dir.mkdir(exist_ok=True)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    records = []
    prev_hash = None

    for i, kind in enumerate(["run-started", "gate-result", "gate-result"]):
        record = {
            "seq": i + 1,
            "timestamp": FIXED_TS,
            "kind": kind,
            "detail": {"test": i},
            "prev_hash": prev_hash
        }
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        with receipts_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        records.append(record)
        prev_hash = record["hash"]

    head_obj = {"seq": len(records), "hash": records[-1]["hash"]}
    (fixture_dir / "head.json").write_text(json.dumps(head_obj))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-chain-intact"}))
    _setup_fixture_pointer(fixture_dir, "chain-intact")


def make_chain_corrupted_tail():
    """Last line of receipts.jsonl truncated to 20 chars (invalid JSON)."""
    fixture_dir = FIXTURES_DIR / "chain-corrupted-tail"
    fixture_dir.mkdir(exist_ok=True)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    records = []
    prev_hash = None

    for i, kind in enumerate(["run-started", "gate-result", "gate-result"]):
        record = {
            "seq": i + 1,
            "timestamp": FIXED_TS,
            "kind": kind,
            "detail": {"test": i},
            "prev_hash": prev_hash
        }
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        with receipts_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        records.append(record)
        prev_hash = record["hash"]

    lines = receipts_file.read_text().strip().split("\n")
    receipts_file.write_text("\n".join(lines[:-1] + [lines[-1][:20]]))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-corrupted-tail"}))
    _setup_fixture_pointer(fixture_dir, "chain-corrupted-tail")


def make_chain_tail_dropped():
    """Last full receipt line removed, head.json left untouched (mismatch)."""
    fixture_dir = FIXTURES_DIR / "chain-tail-dropped"
    fixture_dir.mkdir(exist_ok=True)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    records = []
    prev_hash = None

    for i, kind in enumerate(["run-started", "gate-result", "gate-result"]):
        record = {
            "seq": i + 1,
            "timestamp": FIXED_TS,
            "kind": kind,
            "detail": {"test": i},
            "prev_hash": prev_hash
        }
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        with receipts_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        records.append(record)
        prev_hash = record["hash"]

    head_obj = {"seq": 3, "hash": records[2]["hash"]}
    (fixture_dir / "head.json").write_text(json.dumps(head_obj))

    lines = receipts_file.read_text().strip().split("\n")
    receipts_file.write_text("\n".join(lines[:-1]))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-tail-dropped"}))
    _setup_fixture_pointer(fixture_dir, "chain-tail-dropped")


def make_chain_inserted():
    """A record spliced into the middle with prev_hash mismatch."""
    fixture_dir = FIXTURES_DIR / "chain-inserted"
    fixture_dir.mkdir(exist_ok=True)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    records = []
    prev_hash = None

    for i, kind in enumerate(["run-started", "gate-result", "gate-result"]):
        record = {
            "seq": i + 1,
            "timestamp": FIXED_TS,
            "kind": kind,
            "detail": {"test": i},
            "prev_hash": prev_hash
        }
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        with receipts_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        records.append(record)
        prev_hash = record["hash"]

    head_obj = {"seq": 3, "hash": records[2]["hash"]}
    (fixture_dir / "head.json").write_text(json.dumps(head_obj))

    lines = receipts_file.read_text().strip().split("\n")
    original_records = [json.loads(line) for line in lines]

    inserted = {**original_records[1], "seq": 99, "prev_hash": original_records[0]["hash"]}
    inserted["hash"] = _sha256_json({k: v for k, v in inserted.items() if k != "hash"})

    new_lines = [lines[0], json.dumps(inserted)] + lines[1:]
    receipts_file.write_text("\n".join(new_lines))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-inserted"}))
    _setup_fixture_pointer(fixture_dir, "chain-inserted")


def make_orphan_gate_file():
    """gates/8.json present with no gate-result receipt naming it."""
    fixture_dir = FIXTURES_DIR / "orphan-gate-file"
    fixture_dir.mkdir(exist_ok=True)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    records = []
    prev_hash = None

    for i, kind in enumerate(["run-started", "gate-result"]):
        record = {
            "seq": i + 1,
            "timestamp": FIXED_TS,
            "kind": kind,
            "detail": {"gate": "test-gate", "gate_file": "gates/7.json"},
            "prev_hash": prev_hash
        }
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        with receipts_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        records.append(record)
        prev_hash = record["hash"]

    head_obj = {"seq": 2, "hash": records[1]["hash"]}
    (fixture_dir / "head.json").write_text(json.dumps(head_obj))

    gates_dir = fixture_dir / "gates"
    gates_dir.mkdir(exist_ok=True)
    (gates_dir / "7.json").write_text(json.dumps({"verdict": "PASS"}))
    (gates_dir / "8.json").write_text(json.dumps({"verdict": "PASS"}))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-orphan"}))
    _setup_fixture_pointer(fixture_dir, "orphan-gate-file")


def make_run_not_started():
    """Empty directory (no receipts.jsonl or head.json)."""
    fixture_dir = FIXTURES_DIR / "run-not-started"
    fixture_dir.mkdir(exist_ok=True)

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-not-started"}))
    _setup_fixture_pointer(fixture_dir, "run-not-started")


def make_gate_timeout_present():
    """A gate-timeout receipt exists, blocking the run."""
    fixture_dir = FIXTURES_DIR / "gate-timeout-present"
    fixture_dir.mkdir(exist_ok=True)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    records = []
    prev_hash = None

    for i, (kind, detail) in enumerate([
        ("run-started", {"repo_root": "/test"}),
        ("gate-result", {"gate": "test-gate", "verdict": "PASS"}),
        ("gate-timeout", {"tool_use_id": "tool-123", "command": "bash"}),
    ]):
        record = {
            "seq": i + 1,
            "timestamp": FIXED_TS,
            "kind": kind,
            "detail": detail,
            "prev_hash": prev_hash
        }
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        with receipts_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        records.append(record)
        prev_hash = record["hash"]

    head_obj = {"seq": 3, "hash": records[2]["hash"]}
    (fixture_dir / "head.json").write_text(json.dumps(head_obj))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-timeout"}))
    _setup_fixture_pointer(fixture_dir, "gate-timeout-present")


def make_orphan_with_prefixed_names():
    """One gate-result naming gates/8.json, but both 8.json and 9.json present (9 is orphan)."""
    fixture_dir = FIXTURES_DIR / "orphan-with-prefixed-names"
    fixture_dir.mkdir(exist_ok=True)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    records = []
    prev_hash = None

    for i, (kind, detail) in enumerate([
        ("run-started", {"repo_root": "/test"}),
        ("gate-result", {"gate": "test-gate", "gate_file": "gates/8.json"}),
    ]):
        record = {
            "seq": i + 1,
            "timestamp": FIXED_TS,
            "kind": kind,
            "detail": detail,
            "prev_hash": prev_hash
        }
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        with receipts_file.open("a") as f:
            f.write(json.dumps(record) + "\n")

        records.append(record)
        prev_hash = record["hash"]

    head_obj = {"seq": 2, "hash": records[1]["hash"]}
    (fixture_dir / "head.json").write_text(json.dumps(head_obj))

    gates_dir = fixture_dir / "gates"
    gates_dir.mkdir(exist_ok=True)
    (gates_dir / "8.json").write_text(json.dumps({"verdict": "PASS"}))
    (gates_dir / "9.json").write_text(json.dumps({"verdict": "PASS"}))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-orphan-prefixed"}))
    _setup_fixture_pointer(fixture_dir, "orphan-with-prefixed-names")


def main():
    """Generate all fixtures."""
    make_chain_intact()
    make_chain_corrupted_tail()
    make_chain_tail_dropped()
    make_chain_inserted()
    make_orphan_gate_file()
    make_orphan_with_prefixed_names()
    make_run_not_started()
    make_gate_timeout_present()

    print(f"Generated fixtures in {FIXTURES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
