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

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any


FIXTURES_DIR = Path(__file__).resolve().parent
FIXED_TS = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")


def _sha256_json(obj: Dict[str, Any]) -> str:
    """Compute SHA-256 over canonical JSON (for receipt hashes only)."""
    import hashlib
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sha256_bytes(path: Path) -> str:
    """Compute SHA-256 over raw file bytes (for gate file / artifact hashes)."""
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _setup_fixture_pointer(fixture_dir: Path, fixture_name: str) -> None:
    """Create .team-ship/RUN pointer so find_run can locate this fixture.

    Uses relative path from parent (gate_state) so state_root() + run_id resolves correctly.
    """
    team_ship_dir = fixture_dir / ".team-ship"
    team_ship_dir.mkdir(parents=True, exist_ok=True)
    (team_ship_dir / "RUN").write_text(f"gate_state/{fixture_name}")


def _get_fixtures_dir(out_dir: str = None) -> Path:
    """Return the fixtures directory, using --out if provided, else default to parent of this script."""
    if out_dir:
        return Path(out_dir)
    return FIXTURES_DIR


def make_chain_intact():
    """Valid chain with 3 records and matching head.json."""
    fixture_dir = FIXTURES_DIR / "chain-intact"
    fixture_dir.mkdir(parents=True, exist_ok=True)

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
    fixture_dir.mkdir(parents=True, exist_ok=True)

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
    fixture_dir.mkdir(parents=True, exist_ok=True)

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
    fixture_dir.mkdir(parents=True, exist_ok=True)

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
    fixture_dir.mkdir(parents=True, exist_ok=True)

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
    gates_dir.mkdir(parents=True, exist_ok=True)
    (gates_dir / "7.json").write_text(json.dumps({"verdict": "PASS"}))
    (gates_dir / "8.json").write_text(json.dumps({"verdict": "PASS"}))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-orphan"}))
    _setup_fixture_pointer(fixture_dir, "orphan-gate-file")


def make_run_not_started():
    """Empty directory (no receipts.jsonl or head.json)."""
    fixture_dir = FIXTURES_DIR / "run-not-started"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-not-started"}))
    _setup_fixture_pointer(fixture_dir, "run-not-started")


def make_gate_timeout_present():
    """A gate-timeout receipt exists, blocking the run."""
    fixture_dir = FIXTURES_DIR / "gate-timeout-present"
    fixture_dir.mkdir(parents=True, exist_ok=True)

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
    fixture_dir.mkdir(parents=True, exist_ok=True)

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
    gates_dir.mkdir(parents=True, exist_ok=True)
    (gates_dir / "8.json").write_text(json.dumps({"verdict": "PASS"}))
    (gates_dir / "9.json").write_text(json.dumps({"verdict": "PASS"}))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-orphan-prefixed"}))
    _setup_fixture_pointer(fixture_dir, "orphan-with-prefixed-names")


def make_gate_file_missing():
    """Receipt names gates/8.json with gate_sha256, but file does not exist."""
    fixture_dir = FIXTURES_DIR / "gate-file-missing"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    records = []
    prev_hash = None

    gate_json = {"verdict": "PASS"}
    gate_sha = _sha256_json(gate_json)

    for i, (kind, detail) in enumerate([
        ("run-started", {"repo_root": "/test"}),
        ("gate-result", {"gate": "test-gate", "gate_file": "gates/8.json", "gate_sha256": gate_sha}),
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

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-gate-missing"}))
    _setup_fixture_pointer(fixture_dir, "gate-file-missing")


def make_gate_file_altered():
    """Gate file present but altered after receipt was created."""
    fixture_dir = FIXTURES_DIR / "gate-file-altered"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    # Write the gate file with original content and compute sha256 from raw bytes
    gates_dir = fixture_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    gate_file = gates_dir / "8.json"
    original_content = {"verdict": "PASS"}
    gate_file.write_text(json.dumps(original_content))
    gate_sha = _sha256_bytes(gate_file)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    for i, (kind, detail) in enumerate([
        ("run-started", {"repo_root": "/test"}),
        ("gate-result", {"gate": "test-gate", "gate_file": "gates/8.json", "gate_sha256": gate_sha}),
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

    # Now alter the file to create the test case
    gate_file.write_text(json.dumps({"verdict": "FAIL"}))

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-gate-altered"}))
    _setup_fixture_pointer(fixture_dir, "gate-file-altered")


def make_gate_file_traversal():
    """Gate file name contains path traversal (..)."""
    fixture_dir = FIXTURES_DIR / "gate-file-traversal"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    records = []
    prev_hash = None

    for i, (kind, detail) in enumerate([
        ("run-started", {"repo_root": "/test"}),
        ("gate-result", {"gate": "test-gate", "gate_file": "../run.json", "gate_sha256": "abc123"}),
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

    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-gate-traversal"}))
    _setup_fixture_pointer(fixture_dir, "gate-file-traversal")


def make_gate_file_empty_name():
    """Gate file name is empty: gates/"""
    fixture_dir = FIXTURES_DIR / "gate-file-empty-name"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("gate-result", {"gate": "x", "gate_file": "gates/", "gate_sha256": "abc"}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-empty"}))
    _setup_fixture_pointer(fixture_dir, "gate-file-empty-name")


def make_gate_file_symlink():
    """gates/8.json is a relative symlink to ../outside.json."""
    fixture_dir = FIXTURES_DIR / "gate-file-symlink"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    outside_json = {"verdict": "PASS"}
    outside_sha = _sha256_json(outside_json)

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("gate-result", {"gate": "x", "gate_file": "gates/8.json", "gate_sha256": outside_sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-symlink"}))

    gates_dir = fixture_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)

    (fixture_dir / "outside.json").write_text(json.dumps(outside_json))
    link_target = gates_dir / "8.json"
    if link_target.is_symlink() or link_target.exists():
        link_target.unlink()
    os.symlink("../outside.json", str(link_target))

    _setup_fixture_pointer(fixture_dir, "gate-file-symlink")


def make_artifact_path_traversal():
    """Artifact path contains .. traversal."""
    fixture_dir = FIXTURES_DIR / "artifact-path-traversal"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    secret_content = "secret"
    import hashlib
    secret_sha = hashlib.sha256(secret_content.encode("utf-8")).hexdigest()

    repo_dir = fixture_dir / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("artifact-written", {"path": "../secret.txt", "sha256": secret_sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-traversal", "repo_root": "repo"}))

    (fixture_dir / "secret.txt").write_text(secret_content)
    _setup_fixture_pointer(fixture_dir, "artifact-path-traversal")


def make_artifact_path_absolute():
    """Artifact path is absolute and non-existent."""
    fixture_dir = FIXTURES_DIR / "artifact-path-absolute"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    import hashlib
    fixed_abs_path = "/nonexistent/abs/artifact.txt"
    sha = hashlib.sha256("absolute".encode("utf-8")).hexdigest()

    repo_dir = fixture_dir / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("artifact-written", {"path": fixed_abs_path, "sha256": sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-absolute", "repo_root": "repo"}))

    _setup_fixture_pointer(fixture_dir, "artifact-path-absolute")


def make_artifact_path_symlink():
    """Artifact path is a symlink."""
    fixture_dir = FIXTURES_DIR / "artifact-path-symlink"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    content = "symlink"
    import hashlib
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    repo_dir = fixture_dir / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("artifact-written", {"path": "EVIDENCE.md", "sha256": sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-artifact-symlink", "repo_root": "repo"}))

    (fixture_dir / "outside.md").write_text(content)
    link_target = repo_dir / "EVIDENCE.md"
    if link_target.is_symlink() or link_target.exists():
        link_target.unlink()
    os.symlink("../outside.md", str(link_target))

    _setup_fixture_pointer(fixture_dir, "artifact-path-symlink")


def make_gate_file_one_segment():
    """Gate file is exactly one segment (no gates/ directory)."""
    fixture_dir = FIXTURES_DIR / "gate-file-one-segment"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    gates_dir = fixture_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    gate_file = gates_dir / "8.json"
    gate_json = {"verdict": "PASS"}
    gate_file.write_text(json.dumps(gate_json))
    gate_sha = _sha256_bytes(gate_file)

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("gate-result", {"gate": "x", "gate_file": "8.json", "gate_sha256": gate_sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-one-seg"}))

    _setup_fixture_pointer(fixture_dir, "gate-file-one-segment")


def make_gate_file_nested():
    """Gate file has nested path gates/sub/8.json."""
    fixture_dir = FIXTURES_DIR / "gate-file-nested"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    gates_subdir = fixture_dir / "gates" / "sub"
    gates_subdir.mkdir(parents=True, exist_ok=True)
    gate_file = gates_subdir / "8.json"
    gate_json = {"verdict": "PASS"}
    gate_file.write_text(json.dumps(gate_json))
    gate_sha = _sha256_bytes(gate_file)

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("gate-result", {"gate": "x", "gate_file": "gates/sub/8.json", "gate_sha256": gate_sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-nested"}))


    _setup_fixture_pointer(fixture_dir, "gate-file-nested")


def make_repo_root_traversal():
    """repo_root contains path traversal."""
    fixture_dir = FIXTURES_DIR / "repo-root-traversal"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    import hashlib
    content = "data"
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("artifact-written", {"path": "test.txt", "sha256": sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-traversal", "repo_root": "../../other"}))

    _setup_fixture_pointer(fixture_dir, "repo-root-traversal")


def make_artifact_path_directory():
    """Artifact path points to a directory, not a file."""
    fixture_dir = FIXTURES_DIR / "artifact-path-directory"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    import hashlib
    sha = hashlib.sha256("content".encode("utf-8")).hexdigest()

    repo_dir = fixture_dir / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("artifact-written", {"path": "adir", "sha256": sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-dir", "repo_root": "repo"}))

    (repo_dir / "adir").mkdir(parents=True, exist_ok=True)
    _setup_fixture_pointer(fixture_dir, "artifact-path-directory")


def make_run_json_unreadable():
    """run.json contains invalid JSON."""
    fixture_dir = FIXTURES_DIR / "run-json-unreadable"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    import hashlib
    content = "data"
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("artifact-written", {"path": "test.txt", "sha256": sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text("{not json")

    _setup_fixture_pointer(fixture_dir, "run-json-unreadable")


def make_artifact_without_repo_root():
    """run.json exists but has no repo_root field."""
    fixture_dir = FIXTURES_DIR / "artifact-without-repo-root"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    import hashlib
    content = "data"
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("artifact-written", {"path": "test.txt", "sha256": sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-no-root"}))

    _setup_fixture_pointer(fixture_dir, "artifact-without-repo-root")


def make_receipt_corrupt_tail():
    """receipts.jsonl has a partial line at the end (no trailing newline)."""
    fixture_dir = FIXTURES_DIR / "receipt-corrupt-tail"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    for i, kind in enumerate(["run-started", "gate-result"]):
        record = {
            "seq": i + 1,
            "timestamp": FIXED_TS,
            "kind": kind,
            "detail": {"test": i},
            "prev_hash": prev_hash
        }
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record))  # No newline at end
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-corrupt-tail"}))
    _setup_fixture_pointer(fixture_dir, "receipt-corrupt-tail")


def make_detail_not_object():
    """gate-result receipt where detail is null instead of a dict."""
    fixture_dir = FIXTURES_DIR / "detail-not-object"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    gate_json = {"verdict": "PASS"}
    gate_sha = _sha256_json(gate_json)

    gates_dir = fixture_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    (gates_dir / "check.json").write_text(json.dumps(gate_json))

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("gate-result", None),  # Null detail
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-detail-null"}))
    _setup_fixture_pointer(fixture_dir, "detail-not-object")



def make_gate_file_reformatted():
    """Gate file with same JSON content but different whitespace."""
    fixture_dir = FIXTURES_DIR / "gate-file-reformatted"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    records = []
    prev_hash = None

    # Write the gate file with compact JSON and compute sha256 from raw bytes
    gates_dir = fixture_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    gate_file = gates_dir / "check.json"
    gate_json = {"verdict":"PASS"}  # Compact
    gate_file.write_text(json.dumps(gate_json, separators=(',', ':')))
    gate_sha = _sha256_bytes(gate_file)

    receipts_file = fixture_dir / "receipts.jsonl"
    receipts_file.write_text("")

    for i, (kind, detail) in enumerate([
        ("run-started", {}),
        ("gate-result", {"gate": "x", "gate_file": "gates/check.json", "gate_sha256": gate_sha}),
    ]):
        record = {"seq": i + 1, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
        record["hash"] = _sha256_json({k: v for k, v in record.items() if k != "hash"})
        if i == 0:
            (fixture_dir / "receipts.jsonl").write_text(json.dumps(record) + "\n")
        else:
            with (fixture_dir / "receipts.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")
        records.append(record)
        prev_hash = record["hash"]

    (fixture_dir / "head.json").write_text(json.dumps({"seq": 2, "hash": records[1]["hash"]}))
    (fixture_dir / "run.json").write_text(json.dumps({"run_id": "test-reformatted"}))
    
    # Now reformat the file with pretty-printed JSON (different whitespace, same content)
    gate_file.write_text(json.dumps(gate_json, indent=2))
    
    _setup_fixture_pointer(fixture_dir, "gate-file-reformatted")

def main():
    """Generate all fixtures."""
    global FIXTURES_DIR

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="Output directory for fixtures (default: script directory)")
    args = parser.parse_args()

    if args.out:
        FIXTURES_DIR = Path(args.out)

    make_chain_intact()
    make_chain_corrupted_tail()
    make_chain_tail_dropped()
    make_chain_inserted()
    make_orphan_gate_file()
    make_orphan_with_prefixed_names()
    make_run_not_started()
    make_gate_timeout_present()
    make_gate_file_missing()
    make_gate_file_altered()
    make_gate_file_traversal()
    make_gate_file_empty_name()
    make_gate_file_symlink()
    make_gate_file_one_segment()
    make_gate_file_nested()
    make_artifact_path_traversal()
    make_artifact_path_absolute()
    make_artifact_path_symlink()
    make_repo_root_traversal()
    make_artifact_path_directory()
    make_run_json_unreadable()
    make_artifact_without_repo_root()
    make_receipt_corrupt_tail()
    make_detail_not_object()
    make_gate_file_reformatted()

    print(f"Generated fixtures in {FIXTURES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
