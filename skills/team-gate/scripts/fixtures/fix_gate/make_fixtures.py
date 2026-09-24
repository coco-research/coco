#!/usr/bin/env python3
"""Generate deterministic fixtures for fix_gate.py's --self-test.

Each fixture is a run directory plus a tiny fixed-date git repository.
Anchors on its own file location, accepts --out for an alternative root,
and pins GIT_AUTHOR_DATE, GIT_COMMITTER_DATE, a fixed author and
committer identity, and every receipt's timestamp from TEAM_FIXED_TS, so
two generations are byte-identical except for .git/index and .git/logs.

gate_state.append_receipt() itself calls datetime.now() for a receipt's
timestamp and gate_state.start_run() does the same for run_id and
started_at, so neither is deterministic across two generations. This
generator therefore reproduces their exact record shape and hash
algorithm by hand, with the wall-clock calls replaced by TEAM_FIXED_TS,
the same technique fixtures/ship_gate/make_fixtures.py uses in this same
skill for the same reason. Every reader (verify_chain, fix_gate.py
itself) only cares about the structure, never about whether a timestamp
is real, so the substitution is transparent to every consumer.

See README.md for where each gate file's field shape came from.
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


def _make_repo(build_dir: Path, name: str) -> Path:
    repo = build_dir / name / "repo"
    _reset_dir(repo)
    (repo / "README.md").write_text(f"# {name} fixture\n\nBuilt for fix_gate.py --self-test.\n")
    (repo / ".gitignore").write_text(".team-ship/\n.team-fix/\n")
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
        "run_id": name, "command": "fix", "repo_root": str(repo),
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


# ---------------------------------------------------------------------------
# Gate-file content builders, shaped exactly like the real scripts write
# them (observed from run_gate.py, prove_red.py and claim_evidence.py; see
# README.md).
# ---------------------------------------------------------------------------

def _discover_data(head: str, cwd: str) -> Dict[str, Any]:
    argv = ["pytest", "-q"]
    commands = [{"argv": argv, "source": ".github/workflows/ci.yml", "sourceLine": 9}]
    return {
        "argv": argv, "cwd": cwd, "head": head, "exit": 0,
        "summary": f"discovered 1 command(s); first {' '.join(argv)!r} from .github/workflows/ci.yml:9",
        "source": ".github/workflows/ci.yml", "sourceLine": 9,
        "pins": {}, "commands": commands, "skipped": [],
    }


def _run_data(head: str, cwd: str) -> Dict[str, Any]:
    argv = ["pytest", "-q"]
    parsed = {"errors": 0, "failed": 0, "no_tests_collected": False, "passed": 1, "skipped": 0}
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
        "nodeid": "tests/test_fix.py::test_bug_is_fixed", "file": "tests/test_fix.py",
        "qualname": "test_bug_is_fixed", "status": "new", "kind": "test",
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


def _recheck_data(head: str, cwd: str, findings: Optional[List[str]] = None) -> Dict[str, Any]:
    findings = findings or []
    exit_code = 1 if findings else 0
    return {
        "argv": ["prove_red.py", "recheck"], "base": {"sha": head, "source": "explicit"},
        "cwd": cwd, "env_pins": {"python": sys.executable}, "exit": exit_code,
        "findings": findings, "gate": "tdd-recheck", "head": head, "proved_at_head": head,
        "summary": f"{'BLOCK' if exit_code else 'PASS'}: {len(findings)} finding(s)",
        "tests": [],
    }


def _matrix_data(head: str, cwd: str, grade: str = "MET") -> Dict[str, Any]:
    gates = ["8.json"] if grade == "MET" else []
    requirements = [{"id": "R1", "grade": grade, "gates": gates}]
    exit_code = {"MET": 0, "NOT MET": 1, "UNVERIFIED": 2}[grade]
    met = 1 if grade == "MET" else 0
    not_met = 1 if grade == "NOT MET" else 0
    unverified = 1 if grade == "UNVERIFIED" else 0
    summary = f"1 requirement(s): {met} met, {not_met} not met, {unverified} unverified"
    return {
        "argv": ["claim_evidence.py", "matrix", ".team-fix/ISSUES.md"], "cwd": cwd,
        "exit": exit_code, "head": head, "requirements": requirements, "summary": summary,
    }


def _claim_check_data(head: str, cwd: str, findings: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    findings = findings or []
    exit_code = 1 if findings else 0
    summary = f"{len(findings)} finding(s)" if findings else "no findings"
    return {
        "argv": ["claim_evidence.py", "check", ".team-fix/FIX-BODY.md"], "cwd": cwd,
        "exit": exit_code, "head": head, "summary": summary, "findings": findings,
    }


# ---------------------------------------------------------------------------
# Standard six-gate set, with a few knobs the individual fixtures use
# ---------------------------------------------------------------------------

def _build_standard(run_dir: Path, repo: Path, head: str, *,
                     skip: Optional[set] = None, gate9_exit: int = 0,
                     recheck_findings: Optional[List[str]] = None,
                     matrix_grade: str = "MET",
                     claim_findings: Optional[List[Dict[str, Any]]] = None) -> None:
    skip = skip or set()
    cwd = str(repo)

    def maybe(relpath: str, gate: str, data: Dict[str, Any]) -> None:
        if relpath in skip:
            return
        sha = _write_gate(run_dir, relpath, data)
        _append_gate_receipt(run_dir, gate, relpath, sha, data["exit"], data["summary"])

    maybe("gates/7-discover.json", "gate-discovery", _discover_data(head, cwd))
    maybe("gates/8.json", "test-execution", _run_data(head, cwd))
    maybe("gates/9.json", "tdd-redgreen", _prove_red_data(head, cwd, exit_code=gate9_exit))
    maybe("gates/9-recheck.json", "tdd-recheck", _recheck_data(head, cwd, findings=recheck_findings))
    maybe("gates/11-matrix.json", "requirements-matrix", _matrix_data(head, cwd, grade=matrix_grade))
    maybe("gates/12.json", "claim-evidence", _claim_check_data(head, cwd, findings=claim_findings))


def _corrupt_early_receipt(run_dir: Path) -> None:
    """Mutate an early record's detail without recomputing its hash, which
    is what makes gate_state.verify_chain report the chain broken. Chosen
    deliberately over hand-writing a bogus chain from scratch, matching how
    fixtures/ship_gate/make_fixtures.py's own chain-broken fixture works."""
    receipts_file = run_dir / "receipts.jsonl"
    lines = receipts_file.read_text(encoding="utf-8").strip().split("\n")
    record = json.loads(lines[1])
    record["detail"] = dict(record["detail"], summary="corrupted after the fact")
    lines[1] = json.dumps(record)
    receipts_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Map gate helper
# ---------------------------------------------------------------------------

def _map_data(head: str, cwd: str) -> Dict[str, Any]:
    """Generate gates/handoff-1-map.json for the map stage."""
    return {
        "argv": ["brownfield_map.py", "--repo-root", cwd],
        "binary": "ripwire",
        "cwd": cwd,
        "elapsed_seconds": 1.23,
        "exit": 0,
        "head": head,
        "languages": 3,
        "ripwire_version": "ripwire 0.6.1",
        "summary": "brownfield map written",
        "symbols": 456,
    }


# ---------------------------------------------------------------------------
# Per-fixture assembly
# ---------------------------------------------------------------------------

def make_all_green(build_dir: Path) -> None:
    name = "all-green"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head)


def make_map_missing(build_dir: Path) -> None:
    name = "map-missing"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, skip={"gates/handoff-1-map.json"})


def make_map_overridden(build_dir: Path) -> None:
    name = "map-overridden"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)

    # Skip the map gate (missing), then override it
    _build_standard(run_dir, repo, head, skip={"gates/handoff-1-map.json"})

    # Add override receipt for the missing map
    _append_receipt(run_dir, "override", {
        "gate": "map", "instruction": "map-overridden instruction text", "by": "rijul",
    })


def make_map_earlier_head(build_dir: Path) -> None:
    """Map gate recorded at first commit, then a second commit moves HEAD.
    All other gates written at the new HEAD. The map's recorded head is an
    ancestor of HEAD, so it should pass via the ancestor check."""
    name = "map-earlier-head"
    repo = _make_repo(build_dir, name)
    first_head = _init_repo(repo)
    cwd = str(repo)

    # Start the run (creates run.json and state directory)
    run_dir = _start_run(build_dir, name, repo)

    # Write map gate with first commit's head
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(first_head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    # Make a second commit to move HEAD
    (repo / "file2.txt").write_text("second commit\n")
    _run_git(["add", "-A"], repo)
    _run_git(["commit", "-q", "-m", "second"], repo, env=_git_env())
    second_head = _run_git(["rev-parse", "HEAD"], repo)

    # Write all other gates at the new HEAD
    _build_standard(run_dir, repo, second_head)


def make_map_foreign_head(build_dir: Path) -> None:
    """Map gate's head set to a non-existent commit SHA or from an unrelated
    repository. HEAD doesn't have that commit as an ancestor, so the ancestor
    check fails and head-drift is reported."""
    name = "map-foreign-head"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Create a map gate with a foreign head: 40 hex digits that don't exist
    foreign_head = "a" * 40
    map_data = _map_data(head, cwd)
    map_data["head"] = foreign_head
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", map_data)
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head)


def make_red_green_never_red(build_dir: Path) -> None:
    name = "red-green-never-red"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head, gate9_exit=1)


def make_recheck_hash_changed(build_dir: Path) -> None:
    name = "recheck-hash-changed"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head, recheck_findings=[
        "hash changed: tests/test_fix.py::test_bug_is_fixed recorded 000000000000 now 111111111111",
    ])


def make_matrix_not_met(build_dir: Path) -> None:
    name = "matrix-not-met"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head, matrix_grade="NOT MET")


def make_claim_uncited(build_dir: Path) -> None:
    name = "claim-uncited"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head, claim_findings=[{
        "line": 3, "text": "Fixed 12 failing tests.", "type": "uncited",
        "claim": "12", "reason": "quantitative claim has no [E<n>] citation",
    }])


def make_override_covers_matrix(build_dir: Path) -> None:
    name = "override-covers-matrix"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head, matrix_grade="NOT MET")
    _append_receipt(run_dir, "override", {
        "gate": "11-matrix", "instruction": "override-covers-matrix instruction text", "by": "rijul",
    })


def make_chain_broken(build_dir: Path) -> None:
    name = "chain-broken"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head)
    _corrupt_early_receipt(run_dir)


def make_unused_override(build_dir: Path) -> None:
    name = "unused-override"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head)
    _append_receipt(run_dir, "override", {
        "gate": "8", "instruction": "unused override instruction text", "by": "rijul",
    })


def make_recheck_before_proof(build_dir: Path) -> None:
    """Every gate passes on its own terms, but gates/9-recheck.json's own
    gate-result receipt is appended before gates/9.json's, so the
    recheck's receipt ends up with a lower seq than the proof's. Built by
    hand rather than through _build_standard, because the file content
    and the receipt append order need to diverge: gates/9.json's file is
    written early (so its sha256 is fixed and correct) but its receipt is
    appended last."""
    name = "recheck-before-proof"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    def write_and_receipt(relpath: str, gate: str, data: Dict[str, Any]) -> None:
        sha = _write_gate(run_dir, relpath, data)
        _append_gate_receipt(run_dir, gate, relpath, sha, data["exit"], data["summary"])

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    write_and_receipt("gates/7-discover.json", "gate-discovery", _discover_data(head, cwd))
    write_and_receipt("gates/8.json", "test-execution", _run_data(head, cwd))

    nine_data = _prove_red_data(head, cwd, exit_code=0)
    nine_sha = _write_gate(run_dir, "gates/9.json", nine_data)

    write_and_receipt("gates/9-recheck.json", "tdd-recheck", _recheck_data(head, cwd))
    _append_gate_receipt(run_dir, "tdd-redgreen", "gates/9.json", nine_sha, nine_data["exit"], nine_data["summary"])

    write_and_receipt("gates/11-matrix.json", "requirements-matrix", _matrix_data(head, cwd))
    write_and_receipt("gates/12.json", "claim-evidence", _claim_check_data(head, cwd))


def make_no_run(build_dir: Path) -> None:
    name = "no-run"
    repo = _make_repo(build_dir, name)
    _init_repo(repo)
    state_root = build_dir / name / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    state_root.mkdir(parents=True)


def make_stage_query_allowed(build_dir: Path) -> None:
    name = "stage-query-allowed"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head, skip={"gates/12.json"})


def make_stage_query_blocked(build_dir: Path) -> None:
    name = "stage-query-blocked"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    _build_standard(run_dir, repo, head, skip={"gates/handoff-1-map.json", "gates/7-discover.json", "gates/12.json"})


def make_rounds_exceeded(build_dir: Path) -> None:
    """R5: four stage-opened receipts with stage=6, exceeding the limit of 3.
    The rounds row should exit 1."""
    name = "rounds-exceeded"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head)
    for i in range(4):
        _append_receipt(run_dir, "stage-opened", {"stage": 6})


def make_rounds_overridden(build_dir: Path) -> None:
    """R5: four build rounds (exceeding 3) but overridden by an override receipt
    naming gate 'rounds'. The verdict should be PASS_WITH_OVERRIDE."""
    name = "rounds-overridden"
    repo = _make_repo(build_dir, name)
    head = _init_repo(repo)
    run_dir = _start_run(build_dir, name, repo)
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head)
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
    cwd = str(repo)

    # Write map stage first
    sha = _write_gate(run_dir, "gates/handoff-1-map.json", _map_data(head, cwd))
    _append_gate_receipt(run_dir, "brownfield-map", "gates/handoff-1-map.json", sha, 0, "brownfield map written")

    _build_standard(run_dir, repo, head)
    for i in range(3):
        _append_receipt(run_dir, "stage-opened", {"stage": 6})


FIXTURE_MAKERS = [
    make_all_green,
    make_map_missing,
    make_map_overridden,
    make_map_earlier_head,
    make_map_foreign_head,
    make_red_green_never_red,
    make_recheck_hash_changed,
    make_matrix_not_met,
    make_claim_uncited,
    make_override_covers_matrix,
    make_chain_broken,
    make_unused_override,
    make_recheck_before_proof,
    make_no_run,
    make_stage_query_allowed,
    make_stage_query_blocked,
    make_rounds_exceeded,
    make_rounds_overridden,
    make_rounds_three,
]


def generate_fixtures(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for maker in FIXTURE_MAKERS:
        maker(out_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate fixtures for fix_gate.py.")
    parser.add_argument("--out", default=None, help="output directory (default: _build next to this file)")
    args = parser.parse_args()
    out_dir = Path(args.out).resolve() if args.out else Path(__file__).resolve().parent / "_build"
    generate_fixtures(out_dir)
    print(f"wrote fixtures to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
