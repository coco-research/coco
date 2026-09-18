#!/usr/bin/env python3
"""Generate deterministic fixtures for ship_gate.py's --self-test.

Each fixture is a run directory plus a tiny fixed-date git repository.
Anchors on its own file location, accepts --out for an alternative root,
and pins GIT_AUTHOR_DATE, GIT_COMMITTER_DATE, a fixed author and committer
identity, and every receipt's timestamp from TEAM_FIXED_TS, so two
generations are byte-identical except for .git/index and .git/logs.

gate_state.append_receipt() itself calls datetime.now() for a receipt's
timestamp and gate_state.start_run() does the same for run_id and
started_at, so neither is deterministic across two generations. This
generator therefore reproduces their exact record shape and hash
algorithm by hand, with the wall-clock calls replaced by TEAM_FIXED_TS,
the same technique gate_state's own fixtures/gate_state/make_fixtures.py
uses for the same reason. Every reader in this skill (verify_chain,
derive_status, ship_gate.py itself) only cares about the structure, never
about whether a timestamp is real, so the substitution is transparent to
every consumer.

See README.md for the field shapes each gate file below reproduces; they
were taken from one real run of the committed wave-two scripts, not
guessed.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

FIXED_TS = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
FIXED_NAME = "Team Gate Fixtures"
FIXED_EMAIL = "team-gate-fixtures@example.invalid"


# ---------------------------------------------------------------------------
# git repository helpers (matching the run_gate.py / gate_state.py fixtures)
# ---------------------------------------------------------------------------

def _git_env() -> Dict[str, str]:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = FIXED_NAME
    env["GIT_AUTHOR_EMAIL"] = FIXED_EMAIL
    env["GIT_COMMITTER_NAME"] = FIXED_NAME
    env["GIT_COMMITTER_EMAIL"] = FIXED_EMAIL
    env["GIT_AUTHOR_DATE"] = FIXED_TS
    env["GIT_COMMITTER_DATE"] = FIXED_TS
    return env


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _run_git(args: List[str], cwd: Path, env: Optional[Dict[str, str]] = None) -> str:
    result = subprocess.run(["git"] + args, cwd=str(cwd), env=env,
                             check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _init_repo(repo: Path) -> str:
    _run_git(["init", "-q"], repo)
    _run_git(["config", "user.name", FIXED_NAME], repo)
    _run_git(["config", "user.email", FIXED_EMAIL], repo)
    _run_git(["add", "-A"], repo)
    _run_git(["commit", "-q", "-m", "fixture"], repo, env=_git_env())
    return _run_git(["rev-parse", "HEAD"], repo)


def _second_commit(repo: Path) -> str:
    """Add one tracked file and commit, advancing HEAD. Used only by the
    head-drift fixture, where the run is fully measured before the repo
    moves on."""
    (repo / "SECOND.txt").write_text("advances HEAD after the run was measured\n")
    _run_git(["add", "SECOND.txt"], repo)
    _run_git(["commit", "-q", "-m", "second"], repo, env=_git_env())
    return _run_git(["rev-parse", "HEAD"], repo)


def _make_repo(build_dir: Path, name: str) -> Path:
    repo = build_dir / name / "repo"
    _reset_dir(repo)
    (repo / "README.md").write_text(f"# {name} fixture\n\nBuilt for ship_gate.py --self-test.\n")
    (repo / ".gitignore").write_text(".team-ship/\n")
    return repo


# ---------------------------------------------------------------------------
# Deterministic run-directory helpers, matching gate_state.py's own shapes
# but with every wall-clock read replaced by FIXED_TS.
# ---------------------------------------------------------------------------

def _sha256_json(obj: Dict[str, Any]) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _start_run(build_dir: Path, name: str, repo: Path) -> Path:
    """Write run.json and the .team-ship/RUN pointer by hand, deterministically.

    run_id is the fixture name itself, which is already a filesystem-safe
    slug; state_root is build_dir/name/state.
    """
    state_root = build_dir / name / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    run_dir = state_root / name
    run_dir.mkdir(parents=True)

    run_obj = {
        "run_id": name, "command": "ship", "repo_root": str(repo),
        "started_at": FIXED_TS, "flags": [],
    }
    (run_dir / "run.json").write_text(json.dumps(run_obj, indent=2), encoding="utf-8")

    pointer_dir = repo / ".team-ship"
    pointer_dir.mkdir(parents=True, exist_ok=True)
    (pointer_dir / "RUN").write_text(name, encoding="utf-8")

    return run_dir


def _append_receipt(run_dir: Path, kind: str, detail: Dict[str, Any]) -> None:
    """Deterministic stand-in for gate_state.append_receipt: same record
    shape and hash algorithm, FIXED_TS instead of datetime.now()."""
    receipts_file = run_dir / "receipts.jsonl"
    prev_hash = None
    seq = 1
    if receipts_file.is_file():
        lines = [l for l in receipts_file.read_text(encoding="utf-8").strip().split("\n") if l]
        if lines:
            last = json.loads(lines[-1])
            seq = last["seq"] + 1
            prev_hash = last["hash"]

    record = {"seq": seq, "timestamp": FIXED_TS, "kind": kind, "detail": detail, "prev_hash": prev_hash}
    record["hash"] = _sha256_json(record)

    with receipts_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    head_obj = {"seq": seq, "hash": record["hash"]}
    (run_dir / "head.json").write_text(json.dumps(head_obj), encoding="utf-8")


def _write_gate(run_dir: Path, relpath: str, data: Dict[str, Any]) -> str:
    path = run_dir / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def _append_gate_receipt(run_dir: Path, gate: str, relpath: str, sha256: str, exit_code: int, summary: str) -> None:
    _append_receipt(run_dir, "gate-result", {
        "gate": gate, "gate_file": relpath, "gate_sha256": sha256,
        "exit": exit_code, "summary": summary,
    })


def _append_approval(run_dir: Path) -> None:
    _append_receipt(run_dir, "approval", {"text": "approved"})


# ---------------------------------------------------------------------------
# Gate-file content builders, shaped exactly like the real scripts write
# them (observed from one real run of check_artifacts.py, run_gate.py,
# prove_red.py, verify_independent.py and claim_evidence.py; see README.md).
# ---------------------------------------------------------------------------

def _handoff_data(head: str, cwd: str, exit_code: int = 0) -> Dict[str, Any]:
    violations = [] if exit_code == 0 else ["some input: does not exist"]
    summary = "PASS: all inputs valid" if exit_code == 0 else f"BLOCK: {len(violations)} violation(s)"
    return {
        "argv": ["check_artifacts.py", "stage-inputs"], "cwd": cwd, "head": head,
        "exit": exit_code, "summary": summary, "violations": violations,
    }


def _discover_data(head: str, cwd: str, argv: Optional[List[str]] = None) -> Dict[str, Any]:
    argv = argv or ["pytest", "-q"]
    commands = [{"argv": argv, "source": ".github/workflows/ci.yml", "sourceLine": 9}]
    return {
        "argv": argv, "cwd": cwd, "head": head, "exit": 0,
        "summary": f"discovered 1 command(s); first {' '.join(argv)!r} from .github/workflows/ci.yml:9",
        "source": ".github/workflows/ci.yml", "sourceLine": 9,
        "pins": {}, "commands": commands, "skipped": [],
    }


def _parity_data(head: str, cwd: str) -> Dict[str, Any]:
    return {
        "argv": ["pytest", "-q"], "cwd": cwd, "head": head, "exit": 0,
        "summary": "parity OK for 0 tool(s)", "toolchain": {},
    }


def _run_data(head: str, cwd: str, argv: Optional[List[str]] = None) -> Dict[str, Any]:
    argv = argv or ["pytest", "-q"]
    parsed = {"errors": 0, "failed": 0, "no_tests_collected": False, "passed": 2, "skipped": 0}
    commands = [{"argv": argv, "real_exit": 0, "summary": parsed}]
    return {
        "argv": argv, "cwd": cwd, "head": head, "exit": 0,
        "summary": "1 command(s) passed", "parsed": parsed, "real_exit": 0, "commands": commands,
    }


def _prove_red_data(head: str, cwd: str, exit_code: int = 0) -> Dict[str, Any]:
    if exit_code == 0:
        counts = {"block": 0, "green_fails": 0, "inseparable": 0, "invalid_red": 0,
                   "never_red": 0, "pass": 1, "tests": 1, "unrunnable": 0, "unverified": 0}
        verdict = "PASS"
        summary = "PASS: 1 test(s) proved red then green"
    else:
        counts = {"block": 1, "green_fails": 0, "inseparable": 0, "invalid_red": 0,
                   "never_red": 1, "pass": 0, "tests": 1, "unrunnable": 0, "unverified": 0}
        verdict = "BLOCK"
        summary = "BLOCK: 1 test(s) failed red-green proof"
    tests = [{
        "nodeid": "tests/test_example.py::test_one", "file": "tests/test_example.py",
        "qualname": "test_one", "status": "new", "kind": "test",
        "ast_hash": "0" * 64,
        "green": {"outcome": "pass", "exc_type": None, "message": None},
        "red": {"class": "never-red" if exit_code else "valid-red-assertion",
                 "exc_type": None, "message": "", "last_frame": None, "resolvedTo": None},
        "verdict": verdict,
    }]
    return {
        "argv": ["prove_red.py", "prove"], "base": {"sha": head, "source": "explicit"},
        "counts": counts, "cwd": cwd, "dirty": False, "env_pins": {"python": sys.executable},
        "exit": exit_code, "gate": "tdd-redgreen", "head": head,
        "revert": {"diffstat": ""}, "summary": summary, "tests": tests,
        "worktree": str(Path(cwd) / "worktrees" / "red-fixture"),
    }


def _recheck_data(head: str, cwd: str) -> Dict[str, Any]:
    return {
        "argv": ["prove_red.py", "recheck"], "base": {"sha": head, "source": "explicit"},
        "cwd": cwd, "env_pins": {"python": sys.executable}, "exit": 0,
        "findings": [], "gate": "tdd-recheck", "head": head, "proved_at_head": head,
        "summary": "PASS: 0 finding(s)", "tests": [],
    }


def _coverage_data(head: str, cwd: str, status: str = "MEASURED", exit_code: int = 0) -> Dict[str, Any]:
    if status == "MEASURED":
        return {
            "argv": ["pytest", "-q", "--cov", "--cov-branch"], "cwd": cwd, "exit": 0,
            "head": head, "status": "MEASURED", "summary": "coverage 80%", "pct": 80,
        }
    reason = "no pytest command among the discovered commands" if status == "NOT_APPLICABLE" \
        else "no coverage total line found"
    return {
        "argv": ["pytest", "-q", "--cov", "--cov-branch"] if status != "NOT_APPLICABLE" else None,
        "cwd": cwd, "exit": exit_code, "head": head, "reason": reason, "status": status,
        "summary": f"{status}: {reason}",
    }


def _arch_baseline_data(head: str, cwd: str, status: str = "CURRENT") -> Dict[str, Any]:
    """Shaped like arch_gate.py's cmd_baseline: CURRENT means the index's
    pinnedCommit equals head, exit 0; any other status (STALE,
    NOT_APPLICABLE, DISABLED) is exit 2 and pin is None here, since none of
    these fixtures need a real .arch/index.json on disk to prove the point."""
    exit_code = 0 if status == "CURRENT" else 2
    pin = head if status == "CURRENT" else None
    if pin:
        summary = f"arch baseline: {status} pin={pin[:12]} head={head[:12]}"
    else:
        summary = f"arch baseline: {status} head={head[:12]}"
    return {
        "argv": ["baseline", "--repo-root", cwd], "cwd": cwd, "head": head, "exit": exit_code,
        "summary": summary, "pin": pin, "status": status,
    }


def _arch_plan_data(head: str, cwd: str, mode: str, exit_code: int = 0,
                     component: Optional[str] = None) -> Dict[str, Any]:
    """Shaped like arch_gate.py's _plan_gate wrapper around
    verify_arch_plan.py, for both plan-declare (stage 3) and plan-verify
    (stage 13)."""
    mode_flag = "--declare" if mode == "declare" else "--verify"
    plan_path = str(Path(cwd) / ".team-ship" / "ARCH-PLAN.json")
    argv = ["python3", "verify_arch_plan.py", plan_path, mode_flag, "--repo-root", cwd]
    label = f"plan-{mode}"
    if exit_code == 0:
        stdout_tail = [f"{label}: OK"]
    else:
        descriptor = component or "src/missing/path.ts"
        stdout_tail = [f"BLOCK: component path does not exist: {descriptor}"]
    summary = f"{label}: child_exit={exit_code} -> exit={exit_code}"
    return {
        "argv": argv, "cwd": cwd, "head": head, "exit": exit_code,
        "summary": summary, "child_exit": exit_code, "stdout_tail": stdout_tail,
    }


def _arch_conformance_data(head: str, cwd: str, status: str = "PASS") -> Dict[str, Any]:
    """Shaped like arch_gate.py's cmd_conformance. status "PASS" is a clean
    run; any other status reproduces a non-CURRENT baseline status at
    exit 2, per R2/R3."""
    if status == "PASS":
        exit_code = 0
        gate = "PASS"
        summary = "conformance: PASS"
        validate_exit: Optional[int] = 0
        drift_exit: Optional[int] = 0
        pin: Optional[str] = head
    else:
        exit_code = 2
        gate = "UNVERIFIED"
        summary = f"conformance: baseline status is {status}, cannot be checked honestly"
        validate_exit = None
        drift_exit = None
        pin = None
    return {
        "argv": ["conformance", "--repo-root", cwd], "cwd": cwd, "head": head, "exit": exit_code,
        "summary": summary, "gate": gate, "removes": [], "prunes": [],
        "validate_exit": validate_exit, "drift_exit": drift_exit, "pin": pin,
        "tools_dir": str(Path(cwd) / "skills" / "arch-index" / "scripts"),
    }


def _verify_compare_data(head: str, cwd: str) -> Dict[str, Any]:
    return {
        "argv": ["verify_independent.py", "compare", "gates/8.json", "gates/8-verifier.json"],
        "builder_exit": 0, "builder_failed": 0, "builder_passed": 2, "builder_skipped": 0,
        "cwd": cwd, "exit": 0, "head": head, "mismatches": [],
        "summary": "PASS: compare builder vs verifier gate",
        "verifier_exit": 0, "verifier_failed": 0, "verifier_passed": 2, "verifier_skipped": 0,
    }


def _matrix_data(head: str, cwd: str) -> Dict[str, Any]:
    requirements = [{"id": "R1", "grade": "MET", "gates": ["8.json"]}]
    return {
        "argv": ["claim_evidence.py", "matrix", "PLAN.md"], "cwd": cwd, "exit": 0, "head": head,
        "requirements": requirements,
        "summary": "1 requirement(s): 1 met, 0 not met, 0 unverified",
    }


def _claim_check_data(head: str, cwd: str) -> Dict[str, Any]:
    return {
        "argv": ["claim_evidence.py", "check", "PR-BODY.md"], "cwd": cwd, "exit": 0,
        "head": head, "summary": "no findings", "findings": [],
    }


def _write_evidence(repo: Path, head: str, run_id: str) -> None:
    """EVIDENCE.json/EVIDENCE.md, rendered with render_evidence.render() so
    render_evidence.py --check always agrees with what is on disk."""
    scripts_dir = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(scripts_dir))
    import render_evidence  # noqa: E402

    evidence = {
        "schemaVersion": "1.0", "head": head, "runId": run_id,
        "entries": [{
            "id": "E1", "gate": "test-execution", "verdict": "PASS", "exit": 0, "head": head,
            "command": {"argv": ["pytest", "-q"], "cwd": str(repo)},
            "summary": "1 command(s) passed",
            "detail": {"passed": 2, "failed": 0, "skipped": 0},
        }],
    }
    team_ship = repo / ".team-ship"
    team_ship.mkdir(parents=True, exist_ok=True)
    (team_ship / "EVIDENCE.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (team_ship / "EVIDENCE.md").write_text(render_evidence.render(evidence))


# ---------------------------------------------------------------------------
# Standard stage 1-12 gate set, with a few knobs the individual fixtures use
# ---------------------------------------------------------------------------

def _build_standard(run_dir: Path, repo: Path, head: str, *,
                     skip: Optional[set] = None, gate9_exit: int = 0,
                     gate10_status: str = "MEASURED", gate10_exit: int = 0,
                     gate8_argv: Optional[List[str]] = None, approval: bool = True,
                     arch_baseline_status: str = "CURRENT",
                     arch_plan13_exit: int = 0, arch_plan13_component: Optional[str] = None,
                     arch_conformance_status: str = "PASS") -> None:
    skip = skip or set()
    cwd = str(repo)

    def maybe(relpath: str, gate: str, data: Dict[str, Any], exit_code: int, summary: str) -> None:
        if relpath in skip:
            return
        sha = _write_gate(run_dir, relpath, data)
        _append_gate_receipt(run_dir, gate, relpath, sha, exit_code, summary)

    for n in range(1, 7):
        maybe(f"gates/handoff-{n}.json", f"handoff-{n}", _handoff_data(head, cwd), 0, "PASS: all inputs valid")
    maybe("gates/handoff-approval.json", "handoff-approval", _handoff_data(head, cwd), 0, "PASS: all inputs valid")

    baseline_data = _arch_baseline_data(head, cwd, status=arch_baseline_status)
    maybe("gates/1-arch-baseline.json", "arch-baseline", baseline_data, baseline_data["exit"], baseline_data["summary"])

    plan3_data = _arch_plan_data(head, cwd, "declare")
    maybe("gates/3-arch-plan.json", "arch-plan-declare", plan3_data, plan3_data["exit"], plan3_data["summary"])

    plan13_data = _arch_plan_data(head, cwd, "verify", exit_code=arch_plan13_exit,
                                   component=arch_plan13_component)
    maybe("gates/13-arch-plan.json", "arch-plan-verify", plan13_data, plan13_data["exit"], plan13_data["summary"])

    conformance_data = _arch_conformance_data(head, cwd, status=arch_conformance_status)
    maybe("gates/13-arch.json", "arch-conformance", conformance_data,
          conformance_data["exit"], conformance_data["summary"])

    maybe("gates/7-discover.json", "gate-discovery", _discover_data(head, cwd), 0,
          "discovered 1 command(s); first 'pytest -q' from .github/workflows/ci.yml:9")
    maybe("gates/7.json", "env-parity", _parity_data(head, cwd), 0, "parity OK for 0 tool(s)")

    maybe("gates/8.json", "test-execution", _run_data(head, cwd, argv=gate8_argv), 0, "1 command(s) passed")

    summary9 = "PASS: 1 test(s) proved red then green" if gate9_exit == 0 else "BLOCK: 1 test(s) failed red-green proof"
    maybe("gates/9.json", "tdd-redgreen", _prove_red_data(head, cwd, exit_code=gate9_exit), gate9_exit, summary9)

    data10 = _coverage_data(head, cwd, status=gate10_status, exit_code=gate10_exit)
    maybe("gates/10.json", "coverage", data10, data10["exit"], data10["summary"])

    maybe("gates/8-verifier.json", "test-execution", _run_data(head, cwd), 0, "1 command(s) passed")
    maybe("gates/11.json", "verify-independent-compare", _verify_compare_data(head, cwd), 0,
          "PASS: compare builder vs verifier gate")
    maybe("gates/11-matrix.json", "requirements-matrix", _matrix_data(head, cwd), 0,
          "1 requirement(s): 1 met, 0 not met, 0 unverified")
    maybe("gates/9-recheck.json", "tdd-recheck", _recheck_data(head, cwd), 0, "PASS: 0 finding(s)")
    maybe("gates/12.json", "claim-evidence", _claim_check_data(head, cwd), 0, "no findings")

    if approval:
        _append_approval(run_dir)


def _corrupt_early_receipt(run_dir: Path) -> None:
    """Mutate an early record's detail without recomputing its hash, which
    is what makes gate_state.verify_chain report the chain broken. Chosen
    deliberately over hand-writing a bogus chain from scratch, matching how
    gate_state's own chain-inserted/chain-corrupted-tail fixtures work."""
    receipts_file = run_dir / "receipts.jsonl"
    lines = receipts_file.read_text(encoding="utf-8").strip().split("\n")
    record = json.loads(lines[1])
    record["detail"] = dict(record["detail"], summary="corrupted after the fact")
    lines[1] = json.dumps(record)
    receipts_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _corrupt_line_invalid_json(run_dir: Path, index: int = 1) -> None:
    """Replace one receipts.jsonl line with text that is not valid JSON at
    all, which gate_state.verify_chain's own per-line json.loads catches
    directly while classifying the chain, rather than a hash mismatch on
    an otherwise well-formed record."""
    receipts_file = run_dir / "receipts.jsonl"
    lines = receipts_file.read_text(encoding="utf-8").strip().split("\n")
    lines[index] = lines[index][:10] + "{not valid json"
    receipts_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Per-fixture assembly
# ---------------------------------------------------------------------------

def make_all_green(build_dir: Path) -> None:
    name = "all-green"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)


def make_gate_missing_8(build_dir: Path) -> None:
    name = "gate-missing-8"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, skip={"gates/8.json"})
    _write_evidence(repo, head, name)


def make_gate_red_9(build_dir: Path) -> None:
    name = "gate-red-9"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, gate9_exit=1)
    _write_evidence(repo, head, name)


def make_gate_unverified_10(build_dir: Path) -> None:
    name = "gate-unverified-10"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, gate10_status="NOT_APPLICABLE", gate10_exit=2)
    _write_evidence(repo, head, name)


def make_head_drift(build_dir: Path) -> None:
    name = "head-drift"
    repo = _make_repo(build_dir, name)
    head1 = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head1)
    _write_evidence(repo, head1, name)
    _second_commit(repo)  # every gate file above is now stale


def make_chain_broken(build_dir: Path) -> None:
    name = "chain-broken"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    _corrupt_early_receipt(run_dir)


def make_block_receipt(build_dir: Path) -> None:
    name = "block-receipt"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    _append_receipt(run_dir, "block", {"reason": "manual stop for safety"})


def make_gate_timeout_receipt(build_dir: Path) -> None:
    name = "gate-timeout-receipt"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    _append_receipt(run_dir, "gate-timeout", {"tool_use_id": "tool-1", "command": "pytest -q"})


def make_no_approval(build_dir: Path) -> None:
    name = "no-approval"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, approval=False)
    _write_evidence(repo, head, name)


def make_override_covers_9(build_dir: Path) -> None:
    name = "override-covers-9"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, gate9_exit=1)
    _write_evidence(repo, head, name)
    _append_receipt(run_dir, "override", {
        "gate": "9", "instruction": "override-covers-9 instruction text", "by": "rijul",
    })


def make_override_cannot_cover_chain(build_dir: Path) -> None:
    name = "override-cannot-cover-chain"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    _append_receipt(run_dir, "override", {
        "gate": "9", "instruction": "trying to override the broken chain itself", "by": "rijul",
    })
    _corrupt_early_receipt(run_dir)


def make_ci_mirror_argv_differs(build_dir: Path) -> None:
    name = "ci-mirror-argv-differs"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, gate8_argv=["pytest", "-v"])
    _write_evidence(repo, head, name)


def make_stage_query_allowed(build_dir: Path) -> None:
    name = "stage-query-allowed"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, skip={
        "gates/8.json", "gates/9.json", "gates/10.json", "gates/8-verifier.json",
        "gates/11.json", "gates/11-matrix.json", "gates/9-recheck.json", "gates/12.json",
    })


def make_stage_query_blocked(build_dir: Path) -> None:
    name = "stage-query-blocked"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, skip={
        "gates/7.json",
        "gates/8.json", "gates/9.json", "gates/10.json", "gates/8-verifier.json",
        "gates/11.json", "gates/11-matrix.json", "gates/9-recheck.json", "gates/12.json",
    })


def make_no_run(build_dir: Path) -> None:
    name = "no-run"
    repo = _make_repo(build_dir, name)
    _init_repo(repo)
    state_root = build_dir / name / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    state_root.mkdir(parents=True)


def make_receipts_malformed_line(build_dir: Path) -> None:
    """M1: one receipts.jsonl line is not valid JSON at all. This is caught
    by gate_state.verify_chain's own per-line parsing before ship_gate.py
    ever reads receipts.jsonl a second time, so it must classify the chain
    broken, not fall through to ship_gate's own exit 2."""
    name = "receipts-malformed-line"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    _corrupt_line_invalid_json(run_dir)


def make_override_covers_approval(build_dir: Path) -> None:
    """M2: no approval receipt was ever appended, but an override naming
    "approval" covers it. An override is a stronger human act than the
    approval it stands in for."""
    name = "override-covers-approval"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, approval=False)
    _write_evidence(repo, head, name)
    _append_receipt(run_dir, "override", {
        "gate": "approval", "instruction": "override-covers-approval instruction text", "by": "rijul",
    })


def make_check_from_subdirectory(build_dir: Path) -> None:
    """M4: an otherwise all-green run, checked with --repo-root pointed at
    an empty subdirectory rather than the repository root itself."""
    name = "check-from-subdirectory"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    (repo / "sub").mkdir(parents=True, exist_ok=True)


def make_gates_14_is_directory(build_dir: Path) -> None:
    """N1: gates/14.json already exists as a directory, so the atomic
    write inside ship_gate.py check must fail closed with Unmeasurable
    (os.replace raises IsADirectoryError), never a traceback."""
    name = "gates-14-is-directory"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    (run_dir / "gates" / "14.json").mkdir(parents=True, exist_ok=True)


def make_recheck_before_proof(build_dir: Path) -> None:
    """N3: the latest gate-result receipt for gates/9-recheck.json has a
    LOWER seq than the latest one for gates/9.json, as if the recheck had
    run before the proof it is meant to recheck. The chain itself stays
    valid; only the receipt ordering is wrong. Built by skipping both
    files in _build_standard and appending them by hand in the reverse of
    its usual order."""
    name = "recheck-before-proof"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)
    _build_standard(run_dir, repo, head, skip={"gates/9.json", "gates/9-recheck.json"})

    sha = _write_gate(run_dir, "gates/9-recheck.json", _recheck_data(head, cwd))
    _append_gate_receipt(run_dir, "tdd-recheck", "gates/9-recheck.json", sha, 0, "PASS: 0 finding(s)")

    sha = _write_gate(run_dir, "gates/9.json", _prove_red_data(head, cwd))
    _append_gate_receipt(run_dir, "tdd-redgreen", "gates/9.json", sha, 0, "PASS: 1 test(s) proved red then green")

    _write_evidence(repo, head, name)


def make_rounds_exceeded(build_dir: Path) -> None:
    """R5: four stage-opened receipts with stage=6, exceeding the limit of 3.
    The rounds row should exit 1."""
    name = "rounds-exceeded"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    for i in range(4):
        _append_receipt(run_dir, "stage-opened", {"stage": 6})


def make_rounds_overridden(build_dir: Path) -> None:
    """R5: four build rounds (exceeding 3) but overridden by an override receipt
    naming gate 'rounds'. The verdict should be PASS_WITH_OVERRIDE."""
    name = "rounds-overridden"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    for i in range(4):
        _append_receipt(run_dir, "stage-opened", {"stage": 6})
    _append_receipt(run_dir, "override", {
        "gate": "rounds", "instruction": "rounds-overridden instruction text", "by": "rijul",
    })


def make_rounds_three(build_dir: Path) -> None:
    """R5: exactly three stage-opened receipts with stage=6, at the limit.
    The rounds row should exit 0."""
    name = "rounds-three"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head)
    _write_evidence(repo, head, name)
    for i in range(3):
        _append_receipt(run_dir, "stage-opened", {"stage": 6})


def make_arch_not_applicable_blocks(build_dir: Path) -> None:
    """R3: the baseline is NOT_APPLICABLE (models a repository with no
    .arch/index.json), and gates/13-arch.json reproduces that status at
    exit 2. Not overridden: the run BLOCKs, naming stage 13 and the arch
    gate file."""
    name = "arch-not-applicable-blocks"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, arch_baseline_status="NOT_APPLICABLE",
                     arch_conformance_status="NOT_APPLICABLE")
    _write_evidence(repo, head, name)


def make_arch_not_applicable_overridden(build_dir: Path) -> None:
    """R3: identical to arch-not-applicable-blocks, but an override
    receipt names gate "arch", covering gates/13-arch.json's NOT_APPLICABLE
    state. The verdict becomes PASS_WITH_OVERRIDE."""
    name = "arch-not-applicable-overridden"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, arch_baseline_status="NOT_APPLICABLE",
                     arch_conformance_status="NOT_APPLICABLE")
    _write_evidence(repo, head, name)
    _append_receipt(run_dir, "override", {
        "gate": "arch", "instruction": "arch-not-applicable-overridden instruction text", "by": "rijul",
    })


def make_arch_plan_missing_path(build_dir: Path) -> None:
    """A component declared new or modified whose path is missing is what
    verify_arch_plan.py's --verify mode reports as its own violation;
    arch_gate.py's plan-verify wrapper maps that child exit 1 straight
    through to gates/13-arch-plan.json's own exit 1. Not overridden: BLOCK,
    naming gates/13-arch-plan.json."""
    name = "arch-plan-missing-path"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, arch_plan13_exit=1,
                     arch_plan13_component="src/webhook-ingest/handler.ts")
    _write_evidence(repo, head, name)


# R15: ship_gate.py's head rule is scoped to when a gate runs. These three
# fixtures prove the scoped rule: a run that commits between the pre-build
# gates and the build's own gates still passes (make_all_green_after_build),
# a pre-build gate recorded at a genuinely foreign head is still head drift
# and still not overridable (make_pre_build_foreign_head), and a post-build
# gate recorded at an ancestor of HEAD (not HEAD itself) is still head
# drift, since stage 8 measures the built tree (make_post_build_ancestor_head).
PRE_BUILD_GATES = {
    "gates/handoff-1.json", "gates/handoff-2.json", "gates/handoff-3.json",
    "gates/handoff-4.json", "gates/handoff-5.json", "gates/handoff-6.json",
    "gates/handoff-approval.json",
    "gates/1-arch-baseline.json", "gates/3-arch-plan.json",
}
POST_BUILD_GATES = {
    "gates/7-discover.json", "gates/7.json", "gates/8.json", "gates/9.json",
    "gates/10.json", "gates/8-verifier.json", "gates/11.json",
    "gates/11-matrix.json", "gates/9-recheck.json", "gates/12.json",
    "gates/13-arch-plan.json", "gates/13-arch.json",
}


def make_all_green_after_build(build_dir: Path) -> None:
    """R15: stage 1 to 6 gate files, the approval receipt, the arch
    baseline and plan-declare are recorded at the repository's first
    commit. One more fixed-date commit then moves HEAD, and every stage 7
    to 14 gate file, EVIDENCE.json and the stage 13 arch files are written
    at the new HEAD. The scoped head rule must still pass: stages 1 to 6
    match by ancestry, the built-tree stages match by strict equality."""
    name = "all-green-after-build"
    repo = _make_repo(build_dir, name)
    head1 = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)

    _build_standard(run_dir, repo, head1, skip=POST_BUILD_GATES, approval=True)

    head2 = _second_commit(repo)

    _build_standard(run_dir, repo, head2, skip=PRE_BUILD_GATES, approval=False)

    _write_evidence(repo, head2, name)


def make_pre_build_foreign_head(build_dir: Path) -> None:
    """R15: gates/handoff-3.json is recorded at a sha that is not an
    ancestor of HEAD at all, standing in for a gate file carried over from
    an unrelated run. The scoped head rule still classifies this as head
    drift, and unconditional head drift is never overridable: an override
    receipt naming "3" is present but does not cover it."""
    name = "pre-build-foreign-head"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)
    _build_standard(run_dir, repo, head, skip={"gates/handoff-3.json"})
    _write_evidence(repo, head, name)

    foreign_head = "f" * 40
    data = _handoff_data(foreign_head, cwd)
    sha = _write_gate(run_dir, "gates/handoff-3.json", data)
    _append_gate_receipt(run_dir, "handoff-3", "gates/handoff-3.json", sha, 0, data["summary"])

    _append_receipt(run_dir, "override", {
        "gate": "3", "instruction": "pre-build-foreign-head instruction text", "by": "rijul",
    })


def make_post_build_ancestor_head(build_dir: Path) -> None:
    """R15: gates/8.json is recorded at an earlier commit that is an
    ancestor of the current HEAD, not HEAD itself. Stage 8 measures the
    built tree, so R15 keeps strict equality for it: an ancestor is not
    enough, and this must still be head drift, proving the scoped rule
    narrows to stages 1 to 6 rather than loosening every gate file."""
    name = "post-build-ancestor-head"
    repo = _make_repo(build_dir, name)
    head1 = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)
    head2 = _second_commit(repo)

    _build_standard(run_dir, repo, head2, skip={"gates/8.json"})

    data = _run_data(head1, cwd)
    sha = _write_gate(run_dir, "gates/8.json", data)
    _append_gate_receipt(run_dir, "test-execution", "gates/8.json", sha, 0, "1 command(s) passed")

    _write_evidence(repo, head2, name)


def make_baseline_missing(build_dir: Path) -> None:
    """gates/1-arch-baseline.json is never written: missing blocks stage 1
    like any other missing gate (it is not exempted the way a present but
    UNVERIFIED baseline is), so a stage 2 query lists it under missing."""
    name = "baseline-missing"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, skip={"gates/1-arch-baseline.json"})
    _write_evidence(repo, head, name)


FIXTURE_MAKERS = [
    make_all_green,
    make_gate_missing_8,
    make_gate_red_9,
    make_gate_unverified_10,
    make_head_drift,
    make_chain_broken,
    make_block_receipt,
    make_gate_timeout_receipt,
    make_no_approval,
    make_override_covers_9,
    make_override_cannot_cover_chain,
    make_ci_mirror_argv_differs,
    make_stage_query_allowed,
    make_stage_query_blocked,
    make_no_run,
    make_receipts_malformed_line,
    make_override_covers_approval,
    make_check_from_subdirectory,
    make_gates_14_is_directory,
    make_recheck_before_proof,
    make_rounds_exceeded,
    make_rounds_overridden,
    make_rounds_three,
    make_arch_not_applicable_blocks,
    make_arch_not_applicable_overridden,
    make_arch_plan_missing_path,
    make_baseline_missing,
    make_all_green_after_build,
    make_pre_build_foreign_head,
    make_post_build_ancestor_head,
]


def generate_fixtures(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for maker in FIXTURE_MAKERS:
        maker(out_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate fixtures for ship_gate.py.")
    parser.add_argument("--out", default=None, help="output directory (default: _build next to this file)")
    args = parser.parse_args()
    out_dir = Path(args.out).resolve() if args.out else Path(__file__).resolve().parent / "_build"
    generate_fixtures(out_dir)
    print(f"wrote fixtures to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
