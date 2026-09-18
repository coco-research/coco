#!/usr/bin/env python3
"""Manage the persistent state for team gate validation runs.

Exported library functions (for import by other scripts):

  state_root() -> Path: ~/.team/runs, overridable by env TEAM_STATE_ROOT
  find_run(cwd) -> Path|None: walk up from cwd to find .team-ship/RUN
  start_run(repo_root, command, flags) -> run_id: creates run dir and writes run.json
  append_receipt(run_dir, kind, detail, hook_payload=None) -> dict: append to receipts.jsonl
  verify_chain(run_dir) -> ChainResult: status in {ok, broken, unrunnable}, reason string
  derive_status(run_dir) -> dict: stage_cursor, build_rounds, status, last_gate (derived only)

Receipt kind is a closed set: run-started, stage-opened, artifact-written, agent-spawned,
agent-returned, gate-result, worktree-registered, approval, block, override, pr-opened,
stop-checked, certified, gate-timeout. Any other kind raises InvalidReceiptKind.

CLI modes:
  python3 gate_state.py start <repo_root> <command> [flags...]
  python3 gate_state.py status
  python3 gate_state.py verify-chain
  python3 gate_state.py receipt <kind> <json-detail> [--hook-payload - | --hook-payload PATH]
  python3 gate_state.py --self-test

Exit contract: 0 = ok, 1 = broken, 2 = unrunnable (invalid kind, state unreadable, run not found, bad arguments, corrupt receipts tail). Reason on stderr in one line.

Receipt chain detects accidental corruption and truncation via head.json (seq + hash of
last record), and cross-reference of gates/*.json against gate-result receipts. It is
not claimed as integrity against the model, because the model runs at the same uid and
can rewrite the whole file. Integrity against the model rests on re-derivation: a hook
re-reads HEAD, recomputes the tree digest, and re-parses the stored raw output.

ReceiptFileCorrupt is raised by append_receipt if receipts.jsonl exists, is non-empty,
and does not end with a newline or does not have a valid JSON object (with integer seq)
as its last non-empty line. The write is aborted (file unchanged) and exit code 2 returned.
"""

import argparse
import dataclasses
import fcntl
import hashlib
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any


RECEIPT_KINDS = {
    "run-started", "stage-opened", "artifact-written", "agent-spawned",
    "agent-returned", "gate-result", "worktree-registered", "approval",
    "block", "override", "pr-opened", "stop-checked", "certified", "gate-timeout"
}


class InvalidReceiptKind(ValueError):
    """Raised when an invalid receipt kind is encountered."""
    pass


class ReceiptFileCorrupt(ValueError):
    """Raised when receipts.jsonl has a corrupt tail (incomplete JSON or no trailing newline)."""
    pass


@dataclasses.dataclass
class ChainResult:
    """Result of verifying receipt chain integrity."""
    status: str  # "ok", "broken", or "unrunnable"
    reason: str


def state_root() -> Path:
    """Return the state root directory, overridable by TEAM_STATE_ROOT."""
    env = os.environ.get("TEAM_STATE_ROOT")
    if env:
        return Path(env)
    return Path.home() / ".team" / "runs"


def find_run(cwd: Path) -> Optional[Path]:
    """Walk up from cwd to find .team-ship/RUN, read run id, return run directory."""
    current = Path(cwd).resolve()
    while current != current.parent:
        marker = current / ".team-ship" / "RUN"
        if marker.is_file():
            try:
                run_id = marker.read_text(encoding="utf-8").strip()
                if run_id:
                    run_dir = state_root() / run_id
                    if run_dir.is_dir():
                        return run_dir
            except Exception:
                pass
        current = current.parent
    return None


def _sha256_json(obj: Dict[str, Any]) -> str:
    """Compute SHA-256 over canonical JSON (sorted keys, no spaces)."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _contained_path(base: Path, rel: str, seq: int, label: str) -> tuple:
    """Validate and resolve a relative path within a base directory.

    Returns (path, None) if valid, (None, reason) if not.
    Checks: non-empty string, not absolute, no empty/. /.. segments, resolves within base,
    no symlinks, no control characters (< 0x20 or >= 0x7f), and for gate_file specifically
    must be exactly [gates, <name>].
    """
    if not rel or not isinstance(rel, str):
        return None, f"receipt {seq} {label} malformed: {rel!r}"

    if os.path.isabs(rel):
        return None, f"receipt {seq} {label} malformed: {rel!r}"

    if any(ord(c) < 0x20 or ord(c) >= 0x7f for c in rel):
        return None, f"receipt {seq} {label} malformed: {rel!r}"

    segments = rel.split("/")
    if any(seg in ("", ".", "..") for seg in segments):
        return None, f"receipt {seq} {label} malformed: {rel!r}"

    if label == "gate_file":
        if len(segments) != 2 or segments[0] != "gates" or not segments[1]:
            return None, f"receipt {seq} {label} malformed: {rel!r}"

    candidate = base / rel
    if candidate.is_symlink():
        return None, f"receipt {seq} {rel!r} is a symlink"

    if candidate.exists() and not candidate.is_file():
        return None, f"receipt {seq} {rel!r} is not a regular file"

    try:
        resolved = candidate.resolve(strict=False)
        if not resolved.is_relative_to(base.resolve()):
            return None, f"receipt {seq} {rel!r} resolves outside {base}"
    except (ValueError, RuntimeError):
        return None, f"receipt {seq} {rel!r} resolves outside {base}"

    return candidate, None


def start_run(repo_root: str, command: str, flags: list) -> str:
    """Create a run directory, write run.json, write .team-ship/RUN pointer.

    Returns run_id (directory name under state_root).
    """
    root = Path(repo_root).resolve()
    root_dir = state_root()
    root_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")[:-3]
    run_dir = root_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    run_obj = {
        "run_id": run_id,
        "command": command,
        "repo_root": str(root),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "flags": flags
    }

    run_file = run_dir / "run.json"
    run_file.write_text(json.dumps(run_obj, indent=2), encoding="utf-8")

    pointer_dir = root / ".team-ship"
    pointer_dir.mkdir(parents=True, exist_ok=True)
    pointer_file = pointer_dir / "RUN"
    pointer_file.write_text(run_id, encoding="utf-8")

    return run_id


def append_receipt(run_dir: Path, kind: str, detail: Dict[str, Any],
                   hook_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Append a hashed receipt to receipts.jsonl and update head.json under exclusive file lock.

    Fields: seq, timestamp, kind, detail, session_id, tool_use_id, agent_id,
    agent_type, permission_mode, cwd (last six from hook_payload if present),
    prev_hash, hash.

    Raises InvalidReceiptKind if kind not in RECEIPT_KINDS.
    Returns the written record.

    Thread-safe: acquires an exclusive lock on run_dir/.receipts.lock for the duration
    of reading the last seq, appending to receipts.jsonl, and updating head.json.
    """
    if kind not in RECEIPT_KINDS:
        raise InvalidReceiptKind(f"invalid receipt kind: {kind!r}")

    run_dir = Path(run_dir)
    receipts_file = run_dir / "receipts.jsonl"
    lock_file = run_dir / ".receipts.lock"

    lock_fd = None
    try:
        lock_fd = os.open(str(lock_file), os.O_CREAT | os.O_WRONLY, 0o644)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        prev_hash = None
        seq = 1
        if receipts_file.is_file():
            raw_content = receipts_file.read_text(encoding="utf-8")
            if raw_content:
                if not raw_content.endswith("\n"):
                    raise ReceiptFileCorrupt("receipts.jsonl corrupt tail: does not end with newline")
                lines = raw_content.strip().split("\n")
                if lines:
                    try:
                        last = json.loads(lines[-1])
                        if not isinstance(last.get("seq"), int):
                            raise ReceiptFileCorrupt("receipts.jsonl corrupt tail: last record has no valid seq")
                        seq = last.get("seq", 0) + 1
                        prev_hash = last.get("hash")
                    except json.JSONDecodeError as e:
                        raise ReceiptFileCorrupt(f"receipts.jsonl corrupt tail: {e}")

        record = {
            "seq": seq,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "detail": detail,
            "prev_hash": prev_hash
        }

        if hook_payload:
            for key in ["session_id", "tool_use_id", "agent_id", "agent_type", "permission_mode", "cwd"]:
                if key in hook_payload:
                    record[key] = hook_payload[key]

        record_without_hash = {k: v for k, v in record.items() if k != "hash"}
        record["hash"] = _sha256_json(record_without_hash)

        with receipts_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        head_obj = {"seq": seq, "hash": record["hash"]}
        head_tmp = run_dir / "head.json.tmp"
        head_tmp.write_text(json.dumps(head_obj), encoding="utf-8")
        os.replace(str(head_tmp), str(run_dir / "head.json"))

        return record
    finally:
        if lock_fd is not None:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)


def verify_chain(run_dir: Path) -> ChainResult:
    """Verify receipt chain integrity.

    Checks:
    1. If receipts.jsonl exists, head.json must exist
    2. Last record's seq and hash must equal head.json's values
    3. Every record's hash is correct (no modification)
    4. Every record's prev_hash links correctly
    5. Seq is contiguous from 1
    6. Every gates/*.json file is named by some gate-result receipt
    7. For each distinct gate_file, only the receipt with highest seq is verified against disk
    8. For each distinct artifact path, only the receipt with highest seq is verified against disk

    Returns ChainResult with status in {ok, broken, unrunnable}.
    """
    run_dir = Path(run_dir)
    receipts_file = run_dir / "receipts.jsonl"
    head_file = run_dir / "head.json"

    if not receipts_file.is_file():
        return ChainResult("unrunnable", "run not started (receipts.jsonl not found)")

    if not head_file.is_file():
        return ChainResult("broken", "head.json missing (truncation)")

    try:
        head_obj = json.loads(head_file.read_text(encoding="utf-8"))
        head_seq = head_obj.get("seq")
        head_hash = head_obj.get("hash")
    except (json.JSONDecodeError, OSError):
        return ChainResult("broken", "head.json unreadable")

    try:
        lines = receipts_file.read_text(encoding="utf-8").strip().split("\n")
        if not lines or not lines[0]:
            return ChainResult("broken", "receipts.jsonl is empty")

        records = []
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                return ChainResult("broken", f"line {i+1}: JSON parse error")

        if not records:
            return ChainResult("broken", "no records in receipts.jsonl")

        last_record = records[-1]
        if last_record.get("seq") != head_seq or last_record.get("hash") != head_hash:
            return ChainResult("broken", f"truncation: head records seq {head_seq}, file ends at seq {last_record.get('seq')}")

        for i, record in enumerate(records):
            expected_seq = i + 1
            if record.get("seq") != expected_seq:
                return ChainResult("broken", f"seq mismatch: expected {expected_seq}, got {record.get('seq')}")

            stored_hash = record.get("hash")
            record_without_hash = {k: v for k, v in record.items() if k != "hash"}
            computed_hash = _sha256_json(record_without_hash)

            if stored_hash != computed_hash:
                return ChainResult("broken", f"seq {expected_seq}: hash mismatch (corruption)")

            if i > 0:
                expected_prev = records[i - 1].get("hash")
                if record.get("prev_hash") != expected_prev:
                    return ChainResult("broken", f"seq {expected_seq}: prev_hash mismatch (insertion)")

            # T1: Validate detail is an object before using it
            detail = record.get("detail")
            if not isinstance(detail, dict):
                seq = record.get("seq")
                return ChainResult("broken", f"receipt {seq} detail malformed")

            if record.get("kind") == "gate-timeout":
                tool_use_id = detail.get("tool_use_id", "unknown")
                return ChainResult("broken", f"gate-timeout: {tool_use_id!r}")

        gate_names = set()
        for record in records:
            if record.get("kind") == "gate-result":
                detail = record.get("detail")
                gate_file = detail.get("gate_file")
                if gate_file:
                    gate_names.add(Path(gate_file).name)

        gates_dir = run_dir / "gates"
        if gates_dir.is_dir():
            for gate_file in gates_dir.glob("*.json"):
                if gate_file.name not in gate_names:
                    return ChainResult("broken", f"orphan gate file: {gate_file.name} (receipt dropped)")

        # Build latest gate and artifact maps: for each distinct file, keep only the receipt with highest seq
        latest_gate: Dict[str, Dict[str, Any]] = {}
        latest_artifact: Dict[str, Dict[str, Any]] = {}

        for record in records:
            detail = record.get("detail")
            if not isinstance(detail, dict):
                continue

            if record.get("kind") == "gate-result":
                gate_file = detail.get("gate_file")
                if gate_file:
                    # Keep receipt with highest seq for this gate_file
                    if gate_file not in latest_gate or record.get("seq", 0) > latest_gate[gate_file].get("seq", 0):
                        latest_gate[gate_file] = record

            elif record.get("kind") == "artifact-written":
                path = detail.get("path")
                sha256 = detail.get("sha256")
                # Validate artifact-written detail has both path and sha256, or neither
                if (path and not sha256) or (sha256 and not path):
                    seq = record.get("seq")
                    return ChainResult("broken", f"receipt {seq} artifact-written detail incomplete")
                if path and sha256:
                    # Keep receipt with highest seq for this path
                    if path not in latest_artifact or record.get("seq", 0) > latest_artifact[path].get("seq", 0):
                        latest_artifact[path] = record

        # Count artifact-written receipts that need repo_root
        artifact_count = len(latest_artifact)

        run_obj = None
        if artifact_count > 0:
            try:
                run_file = run_dir / "run.json"
                if run_file.is_file():
                    run_obj = json.loads(run_file.read_text(encoding="utf-8"))
                else:
                    return ChainResult("broken", f"run.json missing; {artifact_count} artifact path(s) cannot be checked")
            except (json.JSONDecodeError, OSError) as e:
                return ChainResult("broken", f"run.json unreadable: {e}; {artifact_count} artifact path(s) cannot be checked")

        # Validate all receipts for path containment (every receipt, even superseded ones)
        for record in records:
            detail = record.get("detail")
            seq = record.get("seq")

            if record.get("kind") == "gate-result":
                gate_file = detail.get("gate_file")
                if gate_file:
                    # Validate path containment for every receipt
                    gate_path, reason = _contained_path(run_dir, gate_file, seq, "gate_file")
                    if reason:
                        return ChainResult("broken", reason)

            elif record.get("kind") == "artifact-written":
                path = detail.get("path")
                if path:
                    # Validate path containment for every receipt
                    if "repo_root" not in run_obj:
                        return ChainResult("broken", f"run.json has no repo_root; {artifact_count} artifact path(s) cannot be checked")

                    repo_root_str = run_obj["repo_root"]
                    if not os.path.isabs(repo_root_str) and ("/" in repo_root_str or repo_root_str in ("", ".", "..")):
                        return ChainResult("broken", f"run.json repo_root malformed: {repo_root_str!r}")

                    if os.path.isabs(repo_root_str):
                        repo_root = Path(repo_root_str)
                    else:
                        repo_root = (run_dir / repo_root_str).resolve()

                    artifact_path, reason = _contained_path(repo_root, path, seq, "artifact path")
                    if reason:
                        return ChainResult("broken", reason)

        # Two-way verification: only check latest receipts against disk
        for gate_file, record in latest_gate.items():
            seq = record.get("seq")
            gate_sha256 = record["detail"].get("gate_sha256")

            # If gate_sha256 is missing, it's broken
            if not gate_sha256:
                return ChainResult("broken", f"receipt {seq} gate-result has no gate_sha256")

            # Path containment already validated above
            gate_path, reason = _contained_path(run_dir, gate_file, seq, "gate_file")
            if reason:
                return ChainResult("broken", reason)

            # Check file exists
            if not gate_path.is_file():
                return ChainResult("broken", f"receipt {seq} names {gate_file!r} which does not exist")

            # Compare sha256 (raw bytes)
            actual_sha = hashlib.sha256(gate_path.read_bytes()).hexdigest()
            if actual_sha != gate_sha256:
                return ChainResult("broken", f"receipt {seq} {gate_file!r} sha256 mismatch: recorded {gate_sha256[:12]} actual {actual_sha[:12]}")

        for path, record in latest_artifact.items():
            seq = record.get("seq")
            sha256_val = record["detail"].get("sha256")

            if "repo_root" not in run_obj:
                return ChainResult("broken", f"run.json has no repo_root; {artifact_count} artifact path(s) cannot be checked")

            repo_root_str = run_obj["repo_root"]
            if not os.path.isabs(repo_root_str) and ("/" in repo_root_str or repo_root_str in ("", ".", "..")):
                return ChainResult("broken", f"run.json repo_root malformed: {repo_root_str!r}")

            if os.path.isabs(repo_root_str):
                repo_root = Path(repo_root_str)
            else:
                repo_root = (run_dir / repo_root_str).resolve()

            # Path containment already validated above
            artifact_path, reason = _contained_path(repo_root, path, seq, "artifact path")
            if reason:
                return ChainResult("broken", reason)

            # Check file exists
            if not artifact_path.is_file():
                return ChainResult("broken", f"receipt {seq} names {path!r} which does not exist")

            # Compare sha256
            actual_sha = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
            if actual_sha != sha256_val:
                return ChainResult("broken", f"receipt {seq} {path!r} sha256 mismatch: recorded {sha256_val[:12]} actual {actual_sha[:12]}")

        return ChainResult("ok", "chain intact")

    except Exception as e:
        return ChainResult("broken", str(e))


def derive_status(run_dir: Path) -> Dict[str, Any]:
    """Derive status from receipts.

    Returns dict with stage_cursor, build_rounds, status, last_gate, superseded_receipts.
    Nothing stores these. Derived only.

    build_rounds is the count of stage-opened receipts whose detail.stage == 6.
    Each loop-back to Build re-opens stage 6.

    superseded_receipts is the count of gate-result and artifact-written receipts
    that are not the latest for their respective gate_file or path.
    """
    run_dir = Path(run_dir)
    receipts_file = run_dir / "receipts.jsonl"

    result = {
        "stage_cursor": None,
        "build_rounds": 0,
        "status": "no-runs",
        "last_gate": None,
        "superseded_receipts": 0
    }

    if not receipts_file.is_file():
        return result

    try:
        lines = receipts_file.read_text(encoding="utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines if line.strip()]

        if not records:
            return result

        # Build latest gate and artifact maps
        latest_gate: Dict[str, int] = {}
        latest_artifact: Dict[str, int] = {}

        for record in records:
            detail = record.get("detail")
            if not isinstance(detail, dict):
                seq = record.get("seq")
                result["status"] = "unreadable"
                result["stage_cursor"] = None
                result["build_rounds"] = 0
                result["last_gate"] = None
                result["superseded_receipts"] = 0
                return result

            kind = record.get("kind")
            if kind == "stage-opened":
                stage = detail.get("stage")
                if stage == 6:
                    result["build_rounds"] += 1
                result["stage_cursor"] = stage
            elif kind == "gate-result":
                result["last_gate"] = detail.get("gate")
                gate_file = detail.get("gate_file")
                if gate_file:
                    seq = record.get("seq", 0)
                    if gate_file not in latest_gate or seq > latest_gate[gate_file]:
                        latest_gate[gate_file] = seq
            elif kind == "artifact-written":
                path = detail.get("path")
                if path:
                    seq = record.get("seq", 0)
                    if path not in latest_artifact or seq > latest_artifact[path]:
                        latest_artifact[path] = seq
            elif kind == "gate-timeout":
                result["status"] = "blocked"
                return result

        # Count superseded receipts
        superseded_count = 0
        for record in records:
            detail = record.get("detail")
            if not isinstance(detail, dict):
                continue

            kind = record.get("kind")
            seq = record.get("seq", 0)

            if kind == "gate-result":
                gate_file = detail.get("gate_file")
                if gate_file and latest_gate.get(gate_file) != seq:
                    superseded_count += 1
            elif kind == "artifact-written":
                path = detail.get("path")
                if path and latest_artifact.get(path) != seq:
                    superseded_count += 1

        result["superseded_receipts"] = superseded_count

        if result["status"] == "blocked":
            return result

        if result["stage_cursor"] is not None:
            result["status"] = "in-progress"
        elif records:
            result["status"] = "completed"

        return result

    except Exception:
        result["status"] = "unreadable"
        return result


def main():
    ap = argparse.ArgumentParser(description="Manage team gate validation run state.")
    sp = ap.add_subparsers(dest="mode", help="mode")

    sp_start = sp.add_parser("start", help="start a new run")
    sp_start.add_argument("repo_root", help="repository root")
    sp_start.add_argument("command", help="command being run")
    sp_start.add_argument("flags", nargs="*", help="command flags")

    sp.add_parser("status", help="show run status")
    sp.add_parser("verify-chain", help="verify receipt chain integrity")

    sp_receipt = sp.add_parser("receipt", help="append a receipt")
    sp_receipt.add_argument("kind", help="receipt kind")
    sp_receipt.add_argument("detail", help="detail JSON")
    sp_receipt.add_argument("--hook-payload", type=str, help="hook payload (- for stdin, or file path)")

    ap.add_argument("--self-test", action="store_true", help="run self-tests")

    args = ap.parse_args()

    if args.self_test:
        return self_test()

    try:
        if args.mode == "start":
            run_id = start_run(args.repo_root, args.command, args.flags)
            print(run_id)
            return 0

        current_run = find_run(Path.cwd())
        if not current_run:
            print("no active run (no .team-ship/RUN found)", file=sys.stderr)
            return 2

        if args.mode == "status":
            status = derive_status(current_run)
            print(json.dumps(status, indent=2))
            if status.get("status") == "blocked":
                return 1
            elif status.get("status") == "unreadable":
                return 2
            return 0

        if args.mode == "verify-chain":
            result = verify_chain(current_run)
            print(result.reason, file=sys.stderr)
            if result.status == "ok":
                return 0
            elif result.status == "broken":
                return 1
            else:
                return 2

        if args.mode == "receipt":
            try:
                detail = json.loads(args.detail)
            except json.JSONDecodeError as e:
                print(f"detail JSON parse error: {e}", file=sys.stderr)
                return 2

            hook_payload = None
            if args.hook_payload:
                try:
                    if args.hook_payload == "-":
                        hook_text = sys.stdin.read()
                    else:
                        hook_text = Path(args.hook_payload).read_text(encoding="utf-8")
                    hook_payload = json.loads(hook_text)
                except (json.JSONDecodeError, OSError) as e:
                    print(f"hook payload parse error: {e}", file=sys.stderr)
                    return 2

            try:
                record = append_receipt(current_run, args.kind, detail, hook_payload)
                print(json.dumps(record))
                return 0
            except (InvalidReceiptKind, ReceiptFileCorrupt) as e:
                print(str(e), file=sys.stderr)
                return 2

        print(f"unknown mode: {args.mode}", file=sys.stderr)
        return 2

    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2


def self_test():
    """Run self-tests against generated fixtures via subprocess."""
    import tempfile
    import shutil

    test_root = Path(__file__).parent / "fixtures" / "gate_state"
    if not test_root.is_dir():
        print("fixtures not found (run make_fixtures.py first)", file=sys.stderr)
        return 1

    fixtures = [
        ("chain-intact", 0, None),
        ("chain-corrupted-tail", 1, "truncation"),
        ("chain-tail-dropped", 1, "truncation"),
        ("chain-inserted", 1, None),
        ("orphan-gate-file", 1, "orphan"),
        ("orphan-with-prefixed-names", 1, "9.json"),
        ("gate-timeout-present", 1, None),
        ("run-not-started", 2, None),
        ("gate-file-missing", 1, "does not exist"),
        ("gate-file-altered", 1, "sha256 mismatch"),
        ("gate-file-reformatted", 1, "sha256 mismatch"),
        ("gate-file-traversal", 1, "malformed"),
        ("gate-file-empty-name", 1, "malformed"),
        ("gate-file-symlink", 1, "is a symlink"),
        ("gate-file-one-segment", 1, "malformed"),
        ("gate-file-nested", 1, "malformed"),
        ("artifact-path-traversal", 1, "malformed"),
        ("artifact-path-absolute", 1, "malformed"),
        ("artifact-path-symlink", 1, "is a symlink"),
        ("repo-root-traversal", 1, "repo_root malformed"),
        ("artifact-path-directory", 1, "is not a regular file"),
        ("run-json-unreadable", 1, "run.json unreadable"),
        ("artifact-without-repo-root", 1, "has no repo_root"),
        ("detail-not-object", 1, "detail malformed"),
        ("gate-rereceipted-current", 0, None),
        ("gate-rereceipted-stale", 1, "sha256 mismatch"),
        ("artifact-rereceipted-current", 0, None),
        ("artifact-detail-incomplete", 1, "artifact-written detail incomplete"),
    ]

    results = []
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(test_root.parent)

    for name, expected_exit, expected_stderr in fixtures:
        fixture_dir = test_root / name
        if not fixture_dir.is_dir():
            print(f"{name}: SKIP (fixture dir not found)", file=sys.stderr)
            results.append((name, expected_exit, "SKIP"))
            continue

        proc = subprocess.run(
            [sys.executable, __file__, "verify-chain"],
            cwd=str(fixture_dir),
            env=env,
            capture_output=True,
            text=True
        )

        exit_ok = proc.returncode == expected_exit
        stderr_ok = expected_stderr is None or expected_stderr in proc.stderr
        status = "OK" if (exit_ok and stderr_ok) else "FAIL"
        if expected_stderr:
            results.append((name, expected_exit, proc.returncode, expected_stderr, proc.stderr[:50], status))
        else:
            results.append((name, expected_exit, proc.returncode, status))

    # bogus-kind test: copy fixture to temp and run receipt on it
    try:
        import tempfile as tmpmod
        import shutil
        fixture_to_copy = test_root / "chain-intact"
        if fixture_to_copy.is_dir():
            temp_bogus = Path(tmpmod.mkdtemp(prefix="gate_state_bogus_"))
            shutil.copytree(fixture_to_copy, temp_bogus / "chain-intact")
            invalid_kind_env = os.environ.copy()
            invalid_kind_env["TEAM_STATE_ROOT"] = str(temp_bogus)
            proc = subprocess.run(
                [sys.executable, __file__, "receipt", "bogus-kind", '{}'],
                cwd=str(temp_bogus / "chain-intact"),
                env=invalid_kind_env,
                capture_output=True,
                text=True
            )
            invalid_status = "OK" if proc.returncode == 2 else "FAIL"
            results.append(("bogus-kind", 2, proc.returncode, invalid_status))
            shutil.rmtree(temp_bogus, ignore_errors=True)
        else:
            results.append(("bogus-kind", "fixture not found", "SKIP"))
    except Exception as e:
        results.append(("bogus-kind", f"exception: {e}", "FAIL"))

    proc = subprocess.run(
        [sys.executable, __file__, "status"],
        cwd=str(test_root / "gate-timeout-present"),
        env=env,
        capture_output=True,
        text=True
    )
    timeout_status = "OK" if proc.returncode == 1 else "FAIL"
    results.append(("status-gate-timeout", 1, proc.returncode, timeout_status))

    proc = subprocess.run(
        [sys.executable, __file__, "status"],
        cwd=str(test_root / "chain-intact"),
        env=env,
        capture_output=True,
        text=True
    )
    intact_status = "OK" if proc.returncode == 0 else "FAIL"
    results.append(("status-chain-intact", 0, proc.returncode, intact_status))

    # Receipt-corrupt-tail test: copy fixture to temp and try to append to a fixture with corrupt tail
    try:
        import tempfile as tmpmod
        import shutil
        corrupt_fixture = test_root / "receipt-corrupt-tail"
        if corrupt_fixture.is_dir():
            temp_corrupt = Path(tmpmod.mkdtemp(prefix="gate_state_corrupt_"))
            (temp_corrupt / "gate_state").mkdir(parents=True, exist_ok=True)
            shutil.copytree(corrupt_fixture, temp_corrupt / "gate_state" / "receipt-corrupt-tail")
            corrupt_fixture_temp = temp_corrupt / "gate_state" / "receipt-corrupt-tail"
            receipts_file = corrupt_fixture_temp / "receipts.jsonl"
            sha_before = __import__("hashlib").sha256(receipts_file.read_bytes()).hexdigest() if receipts_file.is_file() else None
            corrupt_env = os.environ.copy()
            corrupt_env["TEAM_STATE_ROOT"] = str(temp_corrupt)
            proc = subprocess.run(
                [sys.executable, __file__, "receipt", "run-started", '{}'],
                cwd=str(corrupt_fixture_temp),
                env=corrupt_env,
                capture_output=True,
                text=True
            )
            sha_after = __import__("hashlib").sha256(receipts_file.read_bytes()).hexdigest() if receipts_file.is_file() else None
            corrupt_exit_ok = proc.returncode == 2
            corrupt_stderr_ok = "corrupt tail" in proc.stderr
            corrupt_unchanged = sha_before == sha_after
            corrupt_status = "OK" if (corrupt_exit_ok and corrupt_stderr_ok and corrupt_unchanged) else "FAIL"
            results.append(("receipt-corrupt-tail", 2, proc.returncode, corrupt_status))
            shutil.rmtree(temp_corrupt, ignore_errors=True)
        else:
            results.append(("receipt-corrupt-tail", "fixture not found", "SKIP"))
    except Exception as e:
        results.append(("receipt-corrupt-tail", f"exception: {e}", "FAIL"))

    # Concurrent-appends live test: 8 subprocesses x 5 receipts each = 40 total
    try:
        import tempfile as tmpmod
        temp_root = Path(tmpmod.mkdtemp(prefix="gate_state_concurrent_"))
        concurrent_env = os.environ.copy()
        concurrent_env["TEAM_STATE_ROOT"] = str(temp_root)

        # Start a fresh run
        proc_start = subprocess.run(
            [sys.executable, __file__, "start", str(temp_root.parent), "concurrent-test"],
            env=concurrent_env,
            capture_output=True,
            text=True
        )
        if proc_start.returncode != 0:
            results.append(("concurrent-appends", "start", "FAIL"))
        else:
            run_id = proc_start.stdout.strip()
            run_dir = temp_root / run_id

            # Launch 8 subprocesses, each appending 5 receipts
            procs = []
            for i in range(8):
                for j in range(5):
                    payload = json.dumps({"session_id": f"test-{i}", "tool_use_id": f"tool-{i}-{j}"})
                    proc = subprocess.Popen(
                        [sys.executable, __file__, "receipt", "stage-opened", '{"stage": 1}', "--hook-payload", "-"],
                        cwd=str(run_dir),
                        env=concurrent_env,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    proc.stdin.write(payload)
                    proc.stdin.close()
                    procs.append(proc)

            # Wait for all subprocesses to complete
            for proc in procs:
                proc.wait()

            # Verify: read receipts.jsonl and check seq contiguity
            receipts_file = run_dir / "receipts.jsonl"
            if receipts_file.is_file():
                lines = receipts_file.read_text(encoding="utf-8").strip().split("\n")
                records = [json.loads(line) for line in lines if line.strip()]
                record_count = len(records)
                seq_values = [r.get("seq") for r in records]

                # Check: 40 records, seq 1-40 contiguous, no duplicates
                seq_ok = (
                    record_count == 40 and
                    seq_values == list(range(1, 41))
                )

                # Verify chain via subprocess
                proc_verify = subprocess.run(
                    [sys.executable, __file__, "verify-chain"],
                    cwd=str(run_dir),
                    env=concurrent_env,
                    capture_output=True,
                    text=True
                )
                verify_ok = proc_verify.returncode == 0

                # Check head.json seq
                head_file = run_dir / "head.json"
                head_seq_ok = False
                if head_file.is_file():
                    head_obj = json.loads(head_file.read_text(encoding="utf-8"))
                    head_seq_ok = head_obj.get("seq") == 40

                concurrent_ok = seq_ok and verify_ok and head_seq_ok
                concurrent_status = "OK" if concurrent_ok else "FAIL"
                results.append(("concurrent-appends", 40, record_count, seq_ok, verify_ok, head_seq_ok, concurrent_status))
            else:
                results.append(("concurrent-appends", "no-receipts", "FAIL"))

        shutil.rmtree(temp_root, ignore_errors=True)
    except Exception as e:
        results.append(("concurrent-appends", f"exception: {e}", "FAIL"))

    all_ok = all(s == "OK" for r in results for s in [r[-1]] if len(r) >= 3)
    for result in results:
        if len(result) == 3:
            name, expected, status = result
            print(f"{name}: expected {expected} {status}")
        elif len(result) == 4:
            name, expected, actual, status = result
            print(f"{name}: expected {expected} got {actual} {status}")
        elif len(result) == 7:
            name, expect_count, actual_count, seq_ok, verify_ok, head_ok, status = result
            print(f"{name}: {actual_count} records (expect {expect_count}), seq_contiguous={seq_ok}, verify-chain={verify_ok}, head.seq={head_ok} {status}")
        else:
            name, expected, actual, exp_stderr, act_stderr, status = result
            print(f"{name}: expected {expected} got {actual} stderr contains {exp_stderr!r} {status}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
