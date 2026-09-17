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

Exit contract: 0 = ok, 1 = broken, 2 = unrunnable (invalid kind, state unreadable, run not found, bad arguments). Reason on stderr in one line.

Receipt chain detects accidental corruption and truncation via head.json (seq + hash of
last record), and cross-reference of gates/*.json against gate-result receipts. It is
not claimed as integrity against the model, because the model runs at the same uid and
can rewrite the whole file. Integrity against the model rests on re-derivation: a hook
re-reads HEAD, recomputes the tree digest, and re-parses the stored raw output.
"""

import argparse
import dataclasses
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
    """Append a hashed receipt to receipts.jsonl and update head.json.

    Fields: seq, timestamp, kind, detail, session_id, tool_use_id, agent_id,
    agent_type, permission_mode, cwd (last six from hook_payload if present),
    prev_hash, hash.

    Raises InvalidReceiptKind if kind not in RECEIPT_KINDS.
    Returns the written record.
    """
    if kind not in RECEIPT_KINDS:
        raise InvalidReceiptKind(f"invalid receipt kind: {kind!r}")

    run_dir = Path(run_dir)
    receipts_file = run_dir / "receipts.jsonl"

    prev_hash = None
    seq = 1
    if receipts_file.is_file():
        lines = receipts_file.read_text(encoding="utf-8").strip().split("\n")
        if lines:
            try:
                last = json.loads(lines[-1])
                seq = last.get("seq", 0) + 1
                prev_hash = last.get("hash")
            except json.JSONDecodeError:
                pass

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


def verify_chain(run_dir: Path) -> ChainResult:
    """Verify receipt chain integrity.

    Checks:
    1. If receipts.jsonl exists, head.json must exist
    2. Last record's seq and hash must equal head.json's values
    3. Every record's hash is correct (no modification)
    4. Every record's prev_hash links correctly
    5. Seq is contiguous from 1
    6. Every gates/*.json file is named by some gate-result receipt

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

        for record in records:
            if record.get("kind") == "gate-timeout":
                tool_use_id = record.get("detail", {}).get("tool_use_id", "unknown")
                return ChainResult("broken", f"gate-timeout: {tool_use_id}")

        gate_names = set()
        for record in records:
            if record.get("kind") == "gate-result":
                gate_file = record.get("detail", {}).get("gate_file")
                if gate_file:
                    gate_names.add(Path(gate_file).name)

        gates_dir = run_dir / "gates"
        if gates_dir.is_dir():
            for gate_file in gates_dir.glob("*.json"):
                if gate_file.name not in gate_names:
                    return ChainResult("broken", f"orphan gate file: {gate_file.name} (receipt dropped)")

        return ChainResult("ok", "chain intact")

    except Exception as e:
        return ChainResult("broken", str(e))


def derive_status(run_dir: Path) -> Dict[str, Any]:
    """Derive status from receipts.

    Returns dict with stage_cursor, build_rounds, status, last_gate.
    Nothing stores these. Derived only.

    build_rounds is the count of stage-opened receipts whose detail.stage == 6.
    Each loop-back to Build re-opens stage 6.
    """
    run_dir = Path(run_dir)
    receipts_file = run_dir / "receipts.jsonl"

    result = {
        "stage_cursor": None,
        "build_rounds": 0,
        "status": "no-runs",
        "last_gate": None
    }

    if not receipts_file.is_file():
        return result

    try:
        lines = receipts_file.read_text(encoding="utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines if line.strip()]

        if not records:
            return result

        for record in records:
            kind = record.get("kind")
            if kind == "stage-opened":
                stage = record.get("detail", {}).get("stage")
                if stage == 6:
                    result["build_rounds"] += 1
                result["stage_cursor"] = stage
            elif kind == "gate-result":
                result["last_gate"] = record.get("detail", {}).get("gate")
            elif kind == "gate-timeout":
                result["status"] = "blocked"
                return result

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
            except InvalidReceiptKind as e:
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

    invalid_kind_env = os.environ.copy()
    invalid_kind_env["TEAM_STATE_ROOT"] = str(test_root.parent)
    proc = subprocess.run(
        [sys.executable, __file__, "receipt", "bogus-kind", '{}'],
        cwd=str(test_root / "chain-intact"),
        env=invalid_kind_env,
        capture_output=True,
        text=True
    )
    invalid_status = "OK" if proc.returncode == 2 else "FAIL"
    results.append(("bogus-kind", 2, proc.returncode, invalid_status))

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

    all_ok = all(s == "OK" for r in results for s in [r[-1]] if len(r) >= 3)
    for result in results:
        if len(result) == 3:
            name, expected, status = result
            print(f"{name}: expected {expected} {status}")
        elif len(result) == 4:
            name, expected, actual, status = result
            print(f"{name}: expected {expected} got {actual} {status}")
        else:
            name, expected, actual, exp_stderr, act_stderr, status = result
            print(f"{name}: expected {expected} got {actual} stderr contains {exp_stderr!r} {status}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
