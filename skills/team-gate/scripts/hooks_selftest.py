#!/usr/bin/env python3
"""Self-test for the four team-gate hooks under skills/team-gate/hooks/.

For each hook this builds a temporary repository (a real git repo with a
commit) plus a temporary TEAM_STATE_ROOT and a run started through
gate_state.start_run (via the gate_state.py CLI, the same entry point the
hooks themselves use), feeds one fixture payload from
skills/team-gate/hooks/fixtures/<hook>/ to `node <hook>` with the payload
on stdin and cwd set to the fixture repository, and asserts the hook's
stdout, its exit code, and the receipts it appended.

Deep gate state (stages 7 to 12, which belong to run_gate.py, prove_red.py,
verify_independent.py and claim_evidence.py) is hand-fabricated the same
way ship_gate.py's own --self-test fixtures are built: a JSON gate file
under run_dir/gates/ plus a matching gate-result receipt appended through
gate_state.py's own "receipt" CLI, the single writer of receipts.jsonl.
ship_gate.py's own evaluation of a gate file reads only its "head" and
"exit" fields, so this is a faithful, minimal stand-in, not a shortcut
that changes what is being measured. Handoff gates (stages 1 to 6) are
produced by actually running check_artifacts.py against real artifact
files, since those are cheap and the real code path.

Exit contract: 0 = every case OK, 1 = at least one FAIL.
No em dash, no section sign, stdlib only.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
HOOKS_DIR = SCRIPTS_DIR.parent / "hooks"
FIXTURES_DIR = HOOKS_DIR / "fixtures"
GATE_STATE_PY = SCRIPTS_DIR / "gate_state.py"
SHIP_GATE_PY = SCRIPTS_DIR / "ship_gate.py"
CHECK_ARTIFACTS_PY = SCRIPTS_DIR / "check_artifacts.py"
RENDER_EVIDENCE_PY = SCRIPTS_DIR / "render_evidence.py"
INSTALL_PY = HOOKS_DIR / "install.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import gate_state  # noqa: E402  (RECEIPT_KINDS is used to sanity-check every kind this file appends)

RESULTS = []


def report(hook, case, expected, got, ok):
    status = "OK" if ok else "FAIL"
    line = f"{hook}/{case}: expected {expected} got {got} {status}"
    RESULTS.append((line, ok))
    print(line)
    return ok


# ---------------------------------------------------------------------------
# repository and run construction
# ---------------------------------------------------------------------------

def _git_env():
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "Team Gate Selftest",
        "GIT_AUTHOR_EMAIL": "team-gate-selftest@example.invalid",
        "GIT_COMMITTER_NAME": "Team Gate Selftest",
        "GIT_COMMITTER_EMAIL": "team-gate-selftest@example.invalid",
    })
    return env


def make_repo(tmp: Path) -> Path:
    repo = tmp / "repo"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "README.md").write_text("fixture repo for hooks_selftest.py\n")
    (repo / ".gitignore").write_text(".team-ship/\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, env=_git_env(), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=repo, env=_git_env(), check=True)
    return repo


def git_head(repo: Path) -> str:
    proc = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                           capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def start_run(repo: Path, state_root: Path, hooks_mode: str = "observe", command: str = "ship"):
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(state_root)
    proc = subprocess.run(
        [sys.executable, str(GATE_STATE_PY), "start", str(repo), command, f"hooks={hooks_mode}"],
        capture_output=True, text=True, env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gate_state start failed: {proc.stderr}")
    run_id = proc.stdout.strip()
    return run_id, state_root / run_id


def run_hook(hook_name: str, payload: dict, cwd: Path, state_root: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(state_root)
    return subprocess.run(
        ["node", str(HOOKS_DIR / hook_name)],
        input=json.dumps(payload), cwd=str(cwd), env=env, capture_output=True, text=True,
    )


def run_hook_raw(hook_name: str, raw_stdin: str, cwd: Path, state_root: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(state_root)
    return subprocess.run(
        ["node", str(HOOKS_DIR / hook_name)],
        input=raw_stdin, cwd=str(cwd), env=env, capture_output=True, text=True,
    )


def load_fixture(hook_dir: str, case: str) -> dict:
    p = FIXTURES_DIR / hook_dir / f"{case}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def receipts(run_dir: Path):
    p = run_dir / "receipts.jsonl"
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def latest(run_dir: Path, kind: str, pred=None):
    found = None
    for r in receipts(run_dir):
        if r.get("kind") != kind:
            continue
        if pred is not None and not pred(r):
            continue
        if found is None or r.get("seq", 0) > found.get("seq", 0):
            found = r
    return found


def check_artifacts(repo: Path, state_root: Path, *args) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(state_root)
    return subprocess.run(
        [sys.executable, str(CHECK_ARTIFACTS_PY), *args, "--repo-root", str(repo)],
        capture_output=True, text=True, env=env,
    )


def gate_state_receipt(repo: Path, state_root: Path, kind: str, detail: dict) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(state_root)
    assert kind in gate_state.RECEIPT_KINDS, f"not a real receipt kind: {kind}"
    return subprocess.run(
        [sys.executable, str(GATE_STATE_PY), "receipt", kind, json.dumps(detail)],
        cwd=str(repo), capture_output=True, text=True, env=env,
    )


def _fixture_lines(n: int) -> str:
    return "\n".join(f"Line {i} of the fixture content, safe and boring." for i in range(1, n + 1)) + "\n"


def seed_manifest_artifacts(repo: Path) -> None:
    """Real, valid content for the manifest's stage 1-6 artifacts, so
    check_artifacts.py stage-inputs can genuinely pass rather than be
    faked."""
    team_ship = repo / ".team-ship"
    team_ship.mkdir(parents=True, exist_ok=True)
    (team_ship / "RESEARCH-BRIEF.md").write_text(_fixture_lines(22))
    (team_ship / "ARCHITECTURE-OPTIONS.md").write_text("## Chosen option\n\n" + _fixture_lines(12))
    (team_ship / "PLAN.md").write_text(_fixture_lines(14))
    (team_ship / "REVIEW-FINDINGS.md").write_text(_fixture_lines(4))
    (team_ship / "BROWNFIELD-MAP.md").write_text(
        "## Summary\n\n" + _fixture_lines(3)
        + "\n## Entry points\n\n" + _fixture_lines(3)
        + "\n## Impact\n\n" + _fixture_lines(3)
        + "\n## Tests\n\n" + _fixture_lines(2)
        + "\n## Limits\n\n" + _fixture_lines(2)
    )


def seed_handoffs(repo: Path, state_root: Path, upto: int) -> None:
    """Run check_artifacts.py stage-inputs 1..upto for real, producing real
    gates/handoff-<n>.json files and gate-result receipts, and hand-fabricate
    the architecture gate files ship_gate requires beside them since 02281f0:
    gates/1-arch-baseline.json at stage 1 (status CURRENT, exit 0) and
    gates/3-arch-plan.json at stage 3 (exit 0). Both carry the current HEAD."""
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    run_dir = state_root / (repo / ".team-ship" / "RUN").read_text(encoding="utf-8").strip()
    for n in range(1, upto + 1):
        proc = check_artifacts(repo, state_root, "stage-inputs", str(n))
        if proc.returncode != 0:
            raise RuntimeError(f"handoff-{n} setup failed: {proc.stderr}")
        if n == 1:
            write_gate(run_dir, repo, state_root, "gates/1-arch-baseline.json", "arch-baseline", {
                "argv": ["baseline", "--repo-root", str(repo)], "cwd": str(repo), "head": head,
                "exit": 0, "summary": f"arch baseline: CURRENT pin={head[:12]} head={head[:12]}",
                "pin": head, "status": "CURRENT",
            })
        if n == 3:
            write_gate(run_dir, repo, state_root, "gates/3-arch-plan.json", "arch-plan-declare", {
                "argv": ["plan-declare", "--repo-root", str(repo)], "cwd": str(repo), "head": head,
                "exit": 0, "summary": "declare: PASS", "child_exit": 0,
            })


def write_gate(run_dir: Path, repo: Path, state_root: Path, relpath: str, gate_name: str, data: dict) -> None:
    """Hand-fabricate one gate file plus its gate-result receipt, in the
    same field shapes ship_gate.py's own --self-test fixtures use. Only
    "head" and "exit" are read by ship_gate.py's own evaluation; the rest
    documents what a real run of the owning script would have written."""
    path = run_dir / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(content)
    sha256 = hashlib.sha256(content).hexdigest()
    detail = {
        "gate": gate_name, "gate_file": relpath, "gate_sha256": sha256,
        "exit": data["exit"], "summary": data["summary"],
    }
    proc = gate_state_receipt(repo, state_root, "gate-result", detail)
    if proc.returncode != 0:
        raise RuntimeError(f"failed to append gate-result for {relpath}: {proc.stderr}")


def seed_deep_gates(run_dir: Path, repo: Path, state_root: Path, head: str, skip=None) -> None:
    """Stages 7 to 12: hand-fabricated, deterministic, skip-able."""
    skip = skip or set()
    cwd = str(repo)
    argv = ["pytest", "-q"]

    def maybe(relpath, gate_name, data):
        if relpath in skip:
            return
        write_gate(run_dir, repo, state_root, relpath, gate_name, data)

    maybe("gates/7-discover.json", "gate-discovery", {
        "argv": argv, "cwd": cwd, "head": head, "exit": 0,
        "summary": "discovered 1 command(s)",
        "source": ".github/workflows/ci.yml", "sourceLine": 9, "pins": {},
        "commands": [{"argv": argv, "source": ".github/workflows/ci.yml", "sourceLine": 9}],
        "skipped": [],
    })
    maybe("gates/7.json", "env-parity", {
        "argv": argv, "cwd": cwd, "head": head, "exit": 0,
        "summary": "parity OK for 0 tool(s)", "toolchain": {},
    })
    maybe("gates/8.json", "test-execution", {
        "argv": argv, "cwd": cwd, "head": head, "exit": 0, "summary": "1 command(s) passed",
        "commands": [{"argv": argv, "real_exit": 0,
                       "summary": {"passed": 2, "failed": 0, "skipped": 0, "errors": 0, "no_tests_collected": False}}],
    })
    maybe("gates/9.json", "tdd-redgreen", {
        "argv": ["prove_red.py", "prove"], "cwd": cwd, "head": head, "exit": 0,
        "summary": "PASS: 1 test(s) proved red then green",
    })
    maybe("gates/10.json", "coverage", {
        "argv": argv + ["--cov", "--cov-branch"], "cwd": cwd, "head": head, "exit": 0,
        "status": "MEASURED", "summary": "coverage 80%", "pct": 80,
    })
    maybe("gates/8-verifier.json", "test-execution", {
        "argv": argv, "cwd": cwd, "head": head, "exit": 0, "summary": "1 command(s) passed",
    })
    maybe("gates/11.json", "verify-independent-compare", {
        "argv": ["verify_independent.py", "compare"], "cwd": cwd, "head": head, "exit": 0,
        "summary": "PASS: compare builder vs verifier gate",
    })
    maybe("gates/11-matrix.json", "requirements-matrix", {
        "argv": ["claim_evidence.py", "matrix"], "cwd": cwd, "head": head, "exit": 0,
        "summary": "1 requirement(s): 1 met, 0 not met, 0 unverified",
    })
    maybe("gates/9-recheck.json", "tdd-recheck", {
        "argv": ["prove_red.py", "recheck"], "cwd": cwd, "head": head, "exit": 0,
        "summary": "PASS: 0 finding(s)",
    })
    maybe("gates/12.json", "claim-evidence", {
        "argv": ["claim_evidence.py", "check"], "cwd": cwd, "head": head, "exit": 0, "summary": "no findings",
    })
    maybe("gates/13-arch-plan.json", "arch-plan-verify", {
        "argv": ["plan-verify", "--repo-root", cwd], "cwd": cwd, "head": head, "exit": 0,
        "summary": "verify: PASS", "child_exit": 0,
    })
    maybe("gates/13-arch.json", "arch-conformance", {
        "argv": ["conformance", "--repo-root", cwd], "cwd": cwd, "head": head, "exit": 0,
        "summary": "conformance: PASS", "gate": "PASS", "status": "CURRENT", "pin": head,
        "removes": [], "prunes": [], "validate_exit": 0, "drift_exit": 0,
    })


def write_evidence(repo: Path, run_dir: Path, state_root: Path, head: str) -> None:
    run_id = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))["run_id"]
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
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(state_root)
    proc = subprocess.run(
        [sys.executable, str(RENDER_EVIDENCE_PY), "--repo-root", str(repo)],
        capture_output=True, text=True, env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"render_evidence.py failed: {proc.stderr}")


def seed_all_green(repo: Path, run_dir: Path, state_root: Path, skip=None) -> str:
    """Build a fully-green ship state (or one with named gates skipped) so
    ship_gate.py check / stage <n> exercise the real aggregator, not a
    stand-in. Returns HEAD."""
    seed_manifest_artifacts(repo)
    seed_handoffs(repo, state_root, 6)
    head = git_head(repo)
    seed_deep_gates(run_dir, repo, state_root, head, skip=skip)
    gate_state_receipt(repo, state_root, "approval", {"text": "approve"})
    write_evidence(repo, run_dir, state_root, head)
    return head


# ---------------------------------------------------------------------------
# team-turn-log.js
# ---------------------------------------------------------------------------

def test_team_turn_log() -> bool:
    hook = "team-turn-log.js"
    all_ok = True

    def with_run(case):
        tmp = Path(tempfile.mkdtemp(prefix="ttl_"))
        repo = make_repo(tmp)
        state_root = tmp / "state"
        _, run_dir = start_run(repo, state_root, "observe")
        payload = load_fixture("team-turn-log", case)
        payload["cwd"] = str(repo)
        proc = run_hook(hook, payload, repo, state_root)
        return proc, run_dir, payload, tmp

    # approve-plain
    proc, run_dir, payload, tmp = with_run("approve-plain")
    ok = proc.returncode == 0 and proc.stdout == ""
    r = latest(run_dir, "approval")
    expected_sha = hashlib.sha256(payload["prompt"].encode("utf-8")).hexdigest()
    ok = ok and r is not None and r["detail"]["text"] == "approve" and r["detail"]["sha256"] == expected_sha
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "approve-plain", "exit 0, no stdout, approval receipt", f"exit {proc.returncode}, receipt {r}", ok)

    # approve-with-noise
    proc, run_dir, payload, tmp = with_run("approve-with-noise")
    r = latest(run_dir, "approval")
    ok = proc.returncode == 0 and proc.stdout == "" and r is not None and r["detail"]["text"] == payload["prompt"]
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "approve-with-noise", "exit 0, no stdout, approval receipt", f"exit {proc.returncode}, receipt {r}", ok)

    # no-approval
    proc, run_dir, _, tmp = with_run("no-approval")
    recs = receipts(run_dir)
    ok = proc.returncode == 0 and proc.stdout == "" and recs == []
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "no-approval", "exit 0, no stdout, no receipt", f"exit {proc.returncode}, receipts {recs}", ok)

    # override
    proc, run_dir, _, tmp = with_run("override")
    r = latest(run_dir, "override")
    ok = (proc.returncode == 0 and proc.stdout == "" and r is not None
          and r["detail"]["gate"] == "coverage"
          and r["detail"]["instruction"] == "pilot repository has no pytest, accepted by Rijul"
          and r["detail"]["by"] == "user")
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "override", "exit 0, no stdout, override receipt", f"exit {proc.returncode}, receipt {r}", ok)

    # no-run: a plain directory with no .team-ship/RUN anywhere upward
    tmp = Path(tempfile.mkdtemp(prefix="ttl_norun_"))
    state_root = tmp / "state"
    payload = load_fixture("team-turn-log", "no-run")
    payload["cwd"] = str(tmp)
    proc = run_hook(hook, payload, tmp, state_root)
    ok = proc.returncode == 0 and proc.stdout == ""
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "no-run", "exit 0, no stdout", f"exit {proc.returncode}, stdout {proc.stdout!r}", ok)

    # approved-question: a clarifying question is never an approval
    proc, run_dir, _, tmp = with_run("approved-question")
    recs = receipts(run_dir)
    ok = proc.returncode == 0 and proc.stdout == "" and recs == []
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "approved-question", "exit 0, no stdout, no receipt", f"exit {proc.returncode}, receipts {recs}", ok)

    # proceeding-caution: "proceeding" must not match "proceed" without a word boundary
    proc, run_dir, _, tmp = with_run("proceeding-caution")
    recs = receipts(run_dir)
    ok = proc.returncode == 0 and proc.stdout == "" and recs == []
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "proceeding-caution", "exit 0, no stdout, no receipt", f"exit {proc.returncode}, receipts {recs}", ok)

    # not-yet: negated approval
    proc, run_dir, _, tmp = with_run("not-yet")
    recs = receipts(run_dir)
    ok = proc.returncode == 0 and proc.stdout == "" and recs == []
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "not-yet", "exit 0, no stdout, no receipt", f"exit {proc.returncode}, receipts {recs}", ok)

    # approve-with-tail: phrase followed by a colon is a valid word boundary
    proc, run_dir, payload, tmp = with_run("approve-with-tail")
    r = latest(run_dir, "approval")
    ok = proc.returncode == 0 and proc.stdout == "" and r is not None and r["detail"]["text"] == payload["prompt"]
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "approve-with-tail", "exit 0, no stdout, approval receipt", f"exit {proc.returncode}, receipt {r}", ok)

    # lgtm-bang: exclamation mark is a valid trailing-punctuation and word-boundary character
    proc, run_dir, payload, tmp = with_run("lgtm-bang")
    r = latest(run_dir, "approval")
    ok = proc.returncode == 0 and proc.stdout == "" and r is not None and r["detail"]["text"] == payload["prompt"]
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "lgtm-bang", "exit 0, no stdout, approval receipt", f"exit {proc.returncode}, receipt {r}", ok)

    # override-without-colon: no colon after the gate name, so it never matches the override form
    proc, run_dir, _, tmp = with_run("override-without-colon")
    recs = receipts(run_dir)
    ok = proc.returncode == 0 and proc.stdout == "" and recs == []
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "override-without-colon", "exit 0, no stdout, no receipt", f"exit {proc.returncode}, receipts {recs}", ok)

    # approve-but-not-yet: a negation token anywhere in the prompt fails closed
    proc, run_dir, _, tmp = with_run("approve-but-not-yet")
    recs = receipts(run_dir)
    ok = proc.returncode == 0 and proc.stdout == "" and recs == []
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "approve-but-not-yet", "exit 0, no stdout, no receipt", f"exit {proc.returncode}, receipts {recs}", ok)

    return all_ok


# ---------------------------------------------------------------------------
# team-artifact-guard.js
# ---------------------------------------------------------------------------

def test_team_artifact_guard() -> bool:
    hook = "team-artifact-guard.js"
    all_ok = True

    # write-evidence-md, observe: would-deny, no stdout
    tmp = Path(tempfile.mkdtemp(prefix="tag_evd_obs_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    payload = load_fixture("team-artifact-guard", "write-evidence-md")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == payload["tool_use_id"])
    ok = (proc.returncode == 0 and proc.stdout == "" and cert is not None
          and cert["detail"]["decision"] == "would-deny"
          and "written only by team-gate scripts" in (cert["detail"]["reason"] or ""))
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "write-evidence-md-observe", "exit 0, no stdout, certified would-deny", f"exit {proc.returncode}, cert {cert}", ok)

    # write-evidence-md, enforce: deny on stdout
    tmp = Path(tempfile.mkdtemp(prefix="tag_evd_enf_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "enforce")
    payload = load_fixture("team-artifact-guard", "write-evidence-md")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    stdout_json = None
    try:
        stdout_json = json.loads(proc.stdout)
    except Exception:
        pass
    cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == payload["tool_use_id"])
    ok = (
        proc.returncode == 0
        and stdout_json is not None
        and stdout_json.get("hookSpecificOutput", {}).get("hookEventName") == "PreToolUse"
        and stdout_json.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
        and "written only by team-gate scripts" in stdout_json.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
        and cert is not None and cert["detail"]["decision"] == "deny"
    )
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "write-evidence-md-enforce", "exit 0, deny JSON on stdout, certified deny", f"exit {proc.returncode}, stdout {proc.stdout!r}", ok)

    # write-stage-2-before-stage-1: enforce, deny naming the missing gate
    tmp = Path(tempfile.mkdtemp(prefix="tag_s2before1_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "enforce")
    seed_manifest_artifacts(repo)  # content would be valid; handoff-1 is deliberately never run
    # A non-empty receipt chain is required before ship_gate.py can measure
    # anything at all (an empty receipts.jsonl is UNRUNNABLE, not BLOCK);
    # run-started only marks that the run exists, it satisfies no gate.
    gate_state_receipt(repo, state_root, "run-started", {"command": "ship"})
    payload = load_fixture("team-artifact-guard", "write-stage-2-before-stage-1")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    stdout_json = None
    try:
        stdout_json = json.loads(proc.stdout)
    except Exception:
        pass
    reason = stdout_json.get("hookSpecificOutput", {}).get("permissionDecisionReason", "") if stdout_json else ""
    cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == payload["tool_use_id"])
    ok = (proc.returncode == 0 and stdout_json is not None
          and stdout_json.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
          and "handoff-1" in reason
          and cert is not None and cert["detail"]["decision"] == "deny" and cert["detail"]["stage"] == 2)
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "write-stage-2-before-stage-1", "exit 0, deny naming gates/handoff-1.json", f"exit {proc.returncode}, reason {reason!r}", ok)

    # write-stage-2-allowed: observe, allow, then Post appends artifact-written + stage-opened + passing stage-output
    tmp = Path(tempfile.mkdtemp(prefix="tag_s2ok_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    seed_manifest_artifacts(repo)
    seed_handoffs(repo, state_root, 1)
    pre_payload = load_fixture("team-artifact-guard", "write-stage-2-allowed")
    pre_payload["cwd"] = str(repo)
    pre_proc = run_hook(hook, pre_payload, repo, state_root)
    pre_cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == pre_payload["tool_use_id"])
    pre_ok = pre_proc.returncode == 0 and pre_proc.stdout == "" and pre_cert is not None and pre_cert["detail"]["decision"] == "allow"
    all_ok &= report(hook, "write-stage-2-allowed-pre", "exit 0, no stdout, certified allow", f"exit {pre_proc.returncode}, cert {pre_cert}", pre_ok)

    post_payload = dict(pre_payload)
    post_payload["hook_event_name"] = "PostToolUse"
    post_payload["tool_response"] = {"filePath": ".team-ship/ARCHITECTURE-OPTIONS.md"}
    post_proc = run_hook(hook, post_payload, repo, state_root)
    artifact_written = latest(run_dir, "artifact-written",
                               lambda r: r["detail"].get("path") == ".team-ship/ARCHITECTURE-OPTIONS.md" and isinstance(r["detail"].get("stage"), int))
    stage_opened = latest(run_dir, "stage-opened", lambda r: r["detail"].get("stage") == 2)
    block = latest(run_dir, "block")
    post_ok = (post_proc.returncode == 0 and post_proc.stdout == ""
               and artifact_written is not None and stage_opened is not None and block is None)
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "write-stage-2-allowed-post", "exit 0, no stdout, artifact-written + stage-opened, no block", f"exit {post_proc.returncode}, artifact_written {artifact_written is not None}, stage_opened {stage_opened is not None}, block {block}", post_ok)

    # write-outside-team-ship: silent, no receipt
    tmp = Path(tempfile.mkdtemp(prefix="tag_outside_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    payload = load_fixture("team-artifact-guard", "write-outside-team-ship")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    recs = receipts(run_dir)
    ok = proc.returncode == 0 and proc.stdout == "" and recs == []
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "write-outside-team-ship", "exit 0, no stdout, no receipt", f"exit {proc.returncode}, receipts {recs}", ok)

    # post-without-certified: gate-timeout
    tmp = Path(tempfile.mkdtemp(prefix="tag_postnocert_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    seed_manifest_artifacts(repo)  # file exists on disk, as if the write already happened
    payload = load_fixture("team-artifact-guard", "post-without-certified")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    timeout = latest(run_dir, "gate-timeout", lambda r: r["detail"].get("tool_use_id") == payload["tool_use_id"])
    ok = proc.returncode == 0 and proc.stdout == "" and timeout is not None
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "post-without-certified", "exit 0, no stdout, gate-timeout receipt", f"exit {proc.returncode}, timeout {timeout}", ok)

    # post-failing-artifact: certified allow exists (via a synthetic Pre), but the
    # written content is invalid, so check_artifacts.py stage-output fails and a
    # block receipt is appended.
    tmp = Path(tempfile.mkdtemp(prefix="tag_postfail_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    seed_manifest_artifacts(repo)
    seed_handoffs(repo, state_root, 1)
    post_payload = load_fixture("team-artifact-guard", "post-failing-artifact")
    post_payload["cwd"] = str(repo)
    pre_synthetic = dict(post_payload)
    pre_synthetic["hook_event_name"] = "PreToolUse"
    pre_synthetic.pop("tool_response", None)
    pre_proc = run_hook(hook, pre_synthetic, repo, state_root)
    pre_cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == post_payload["tool_use_id"])
    assert pre_proc.returncode == 0 and pre_cert is not None and pre_cert["detail"]["decision"] == "allow", (
        f"setup for post-failing-artifact did not certify allow: {pre_proc.stderr} {pre_cert}"
    )
    (repo / ".team-ship" / "ARCHITECTURE-OPTIONS.md").write_text("too short\n")  # fails minLines and the "chosen" heading
    post_proc = run_hook(hook, post_payload, repo, state_root)
    block = latest(run_dir, "block", lambda r: r["detail"].get("path") == ".team-ship/ARCHITECTURE-OPTIONS.md")
    ok = post_proc.returncode == 0 and post_proc.stdout == "" and block is not None
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "post-failing-artifact", "exit 0, no stdout, block receipt", f"exit {post_proc.returncode}, block {block}", ok)

    return all_ok


# ---------------------------------------------------------------------------
# team-stage-guard.js
# ---------------------------------------------------------------------------

def test_team_stage_guard() -> bool:
    hook = "team-stage-guard.js"
    all_ok = True

    # pr-create-all-green: observe, allow, then Post records pr-opened
    tmp = Path(tempfile.mkdtemp(prefix="tsg_green_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    seed_all_green(repo, run_dir, state_root)
    pre_payload = load_fixture("team-stage-guard", "pr-create-all-green")
    pre_payload["cwd"] = str(repo)
    pre_proc = run_hook(hook, pre_payload, repo, state_root)
    pre_cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == pre_payload["tool_use_id"])
    pre_ok = pre_proc.returncode == 0 and pre_proc.stdout == "" and pre_cert is not None and pre_cert["detail"]["decision"] == "allow"
    all_ok &= report(hook, "pr-create-all-green-pre", "exit 0, no stdout, certified allow", f"exit {pre_proc.returncode}, cert {pre_cert}", pre_ok)

    post_payload = load_fixture("team-stage-guard", "post-pr-create")
    post_payload["cwd"] = str(repo)
    post_proc = run_hook(hook, post_payload, repo, state_root)
    opened = latest(run_dir, "pr-opened")
    post_ok = (post_proc.returncode == 0 and post_proc.stdout == ""
               and opened is not None and opened["detail"]["url"] == "https://github.com/example/repo/pull/42")
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "pr-create-all-green-post", "exit 0, no stdout, pr-opened with url", f"exit {post_proc.returncode}, opened {opened}", post_ok)

    # pr-create-blocked: enforce, deny naming gate 8
    tmp = Path(tempfile.mkdtemp(prefix="tsg_blocked_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "enforce")
    seed_all_green(repo, run_dir, state_root, skip={"gates/8.json"})
    payload = load_fixture("team-stage-guard", "pr-create-blocked")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    stdout_json = None
    try:
        stdout_json = json.loads(proc.stdout)
    except Exception:
        pass
    reason = stdout_json.get("hookSpecificOutput", {}).get("permissionDecisionReason", "") if stdout_json else ""
    cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == payload["tool_use_id"])
    ok = (proc.returncode == 0 and stdout_json is not None
          and stdout_json.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
          and "8" in reason and "gates/8.json" in reason
          and cert is not None and cert["detail"]["decision"] == "deny")
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "pr-create-blocked", "exit 0, deny naming gates/8.json", f"exit {proc.returncode}, reason {reason!r}", ok)

    # pr-create-unmeasurable: enforce, deny "cannot measure" on a run with zero receipts
    tmp = Path(tempfile.mkdtemp(prefix="tsg_unmeasurable_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "enforce")
    payload = load_fixture("team-stage-guard", "pr-create-unmeasurable")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    stdout_json = None
    try:
        stdout_json = json.loads(proc.stdout)
    except Exception:
        pass
    reason = stdout_json.get("hookSpecificOutput", {}).get("permissionDecisionReason", "") if stdout_json else ""
    ok = (proc.returncode == 0 and stdout_json is not None
          and stdout_json.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
          and reason == "cannot measure")
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "pr-create-unmeasurable", "exit 0, deny 'cannot measure'", f"exit {proc.returncode}, reason {reason!r}", ok)

    # git-push-blocked: enforce, deny (same ship_gate.py check, different command)
    tmp = Path(tempfile.mkdtemp(prefix="tsg_gitpush_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "enforce")
    seed_all_green(repo, run_dir, state_root, skip={"gates/8.json"})
    payload = load_fixture("team-stage-guard", "git-push-blocked")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    stdout_json = None
    try:
        stdout_json = json.loads(proc.stdout)
    except Exception:
        pass
    cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == payload["tool_use_id"])
    ok = (proc.returncode == 0 and stdout_json is not None
          and stdout_json.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
          and cert is not None and cert["detail"]["matched"] == "git-push")
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "git-push-blocked", "exit 0, deny, certified matched git-push", f"exit {proc.returncode}, cert {cert}", ok)

    # ordinary-bash: silent, no receipt
    tmp = Path(tempfile.mkdtemp(prefix="tsg_ordinary_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    payload = load_fixture("team-stage-guard", "ordinary-bash")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    recs = receipts(run_dir)
    ok = proc.returncode == 0 and proc.stdout == "" and recs == []
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "ordinary-bash", "exit 0, no stdout, no receipt", f"exit {proc.returncode}, receipts {recs}", ok)

    # agent-spawn-builder-before-stage-6: observe, would-deny (handoff-5 never run)
    tmp = Path(tempfile.mkdtemp(prefix="tsg_agentbuild_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    seed_manifest_artifacts(repo)
    seed_handoffs(repo, state_root, 4)  # stops before handoff-5, so stage 6 is not reachable
    payload = load_fixture("team-stage-guard", "agent-spawn-builder-before-stage-6")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    spawned = latest(run_dir, "agent-spawned")
    cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == payload["tool_use_id"])
    ok = (proc.returncode == 0 and proc.stdout == "" and spawned is not None
          and cert is not None and cert["detail"]["decision"] == "would-deny"
          and cert["detail"]["matched"] == "agent-build-before-6")
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "agent-spawn-builder-before-stage-6", "exit 0, no stdout, agent-spawned + certified would-deny", f"exit {proc.returncode}, cert {cert}", ok)

    # agent-spawn-researcher: observe, allow
    tmp = Path(tempfile.mkdtemp(prefix="tsg_agentresearch_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    pre_payload = load_fixture("team-stage-guard", "agent-spawn-researcher")
    pre_payload["cwd"] = str(repo)
    pre_proc = run_hook(hook, pre_payload, repo, state_root)
    spawned = latest(run_dir, "agent-spawned")
    pre_cert = latest(run_dir, "certified", lambda r: r["detail"]["tool_use_id"] == pre_payload["tool_use_id"])
    pre_ok = (pre_proc.returncode == 0 and pre_proc.stdout == "" and spawned is not None
              and pre_cert is not None and pre_cert["detail"]["decision"] == "allow")
    all_ok &= report(hook, "agent-spawn-researcher", "exit 0, no stdout, agent-spawned + certified allow", f"exit {pre_proc.returncode}, cert {pre_cert}", pre_ok)

    # post-agent: agent-returned, paired with the researcher spawn above
    post_payload = load_fixture("team-stage-guard", "post-agent")
    post_payload["cwd"] = str(repo)
    post_proc = run_hook(hook, post_payload, repo, state_root)
    returned = latest(run_dir, "agent-returned", lambda r: r["detail"].get("tool_use_id") == post_payload["tool_use_id"])
    post_ok = post_proc.returncode == 0 and post_proc.stdout == "" and returned is not None
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "post-agent", "exit 0, no stdout, agent-returned receipt", f"exit {post_proc.returncode}, returned {returned}", post_ok)

    return all_ok


# ---------------------------------------------------------------------------
# team-stop-guard.js
# ---------------------------------------------------------------------------

def test_team_stop_guard() -> bool:
    hook = "team-stop-guard.js"
    all_ok = True

    # in-flight-first-stop, observe: would-block, no stdout
    tmp = Path(tempfile.mkdtemp(prefix="tstop_inflight_obs_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "observe")
    seed_manifest_artifacts(repo)
    seed_handoffs(repo, state_root, 2)  # stage-opened(2) so there is something "in flight"
    gate_state_receipt(repo, state_root, "stage-opened", {"stage": 2})
    payload = load_fixture("team-stop-guard", "in-flight-first-stop")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    checked = latest(run_dir, "stop-checked")
    ok = (proc.returncode == 0 and proc.stdout == "" and checked is not None
          and checked["detail"]["decision"] == "would-block"
          and "stage 2" in checked["detail"]["reason"])
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "in-flight-first-stop-observe", "exit 0, no stdout, stop-checked would-block naming stage 2", f"exit {proc.returncode}, checked {checked}", ok)

    # in-flight-first-stop, enforce: block on stdout
    tmp = Path(tempfile.mkdtemp(prefix="tstop_inflight_enf_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "enforce")
    seed_manifest_artifacts(repo)
    seed_handoffs(repo, state_root, 2)
    gate_state_receipt(repo, state_root, "stage-opened", {"stage": 2})
    payload = load_fixture("team-stop-guard", "in-flight-first-stop")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    stdout_json = None
    try:
        stdout_json = json.loads(proc.stdout)
    except Exception:
        pass
    checked = latest(run_dir, "stop-checked")
    ok = (proc.returncode == 0 and stdout_json is not None
          and stdout_json.get("decision") == "block"
          and "stage 2" in stdout_json.get("reason", "")
          and checked is not None and checked["detail"]["decision"] == "block")
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "in-flight-first-stop-enforce", "exit 0, block JSON on stdout naming stage 2", f"exit {proc.returncode}, stdout {proc.stdout!r}", ok)

    # in-flight-re-entry: stop_hook_active true, allow regardless of state
    tmp = Path(tempfile.mkdtemp(prefix="tstop_reentry_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "enforce")
    payload = load_fixture("team-stop-guard", "in-flight-re-entry")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    checked = latest(run_dir, "stop-checked")
    ok = proc.returncode == 0 and proc.stdout == "" and checked is not None and checked["detail"]["decision"] == "allow"
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "in-flight-re-entry", "exit 0, no stdout, stop-checked allow", f"exit {proc.returncode}, checked {checked}", ok)

    # background-tasks: allow regardless of state
    tmp = Path(tempfile.mkdtemp(prefix="tstop_bgtasks_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "enforce")
    payload = load_fixture("team-stop-guard", "background-tasks")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    checked = latest(run_dir, "stop-checked")
    ok = proc.returncode == 0 and proc.stdout == "" and checked is not None and checked["detail"]["decision"] == "allow"
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "background-tasks", "exit 0, no stdout, stop-checked allow", f"exit {proc.returncode}, checked {checked}", ok)

    # pr-opened: allow, even though the run never reached stage 14
    tmp = Path(tempfile.mkdtemp(prefix="tstop_propened_"))
    repo = make_repo(tmp)
    state_root = tmp / "state"
    _, run_dir = start_run(repo, state_root, "enforce")
    gate_state_receipt(repo, state_root, "pr-opened", {"url": "https://github.com/example/repo/pull/1"})
    payload = load_fixture("team-stop-guard", "pr-opened")
    payload["cwd"] = str(repo)
    proc = run_hook(hook, payload, repo, state_root)
    checked = latest(run_dir, "stop-checked")
    ok = proc.returncode == 0 and proc.stdout == "" and checked is not None and checked["detail"]["decision"] == "allow"
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "pr-opened", "exit 0, no stdout, stop-checked allow", f"exit {proc.returncode}, checked {checked}", ok)

    # no-run: silent
    tmp = Path(tempfile.mkdtemp(prefix="tstop_norun_"))
    state_root = tmp / "state"
    payload = load_fixture("team-stop-guard", "no-run")
    payload["cwd"] = str(tmp)
    proc = run_hook(hook, payload, tmp, state_root)
    ok = proc.returncode == 0 and proc.stdout == ""
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "no-run", "exit 0, no stdout", f"exit {proc.returncode}, stdout {proc.stdout!r}", ok)

    return all_ok


# ---------------------------------------------------------------------------
# cross-cutting cases, run against every hook
# ---------------------------------------------------------------------------

HOOKS = ["team-turn-log.js", "team-artifact-guard.js", "team-stage-guard.js", "team-stop-guard.js"]


def test_no_active_run() -> bool:
    all_ok = True
    generic = {
        "team-turn-log.js": {"hook_event_name": "UserPromptSubmit", "prompt": "approve"},
        "team-artifact-guard.js": {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_use_id": "t1",
                                    "tool_input": {"file_path": ".team-ship/PLAN.md", "content": "x"}},
        "team-stage-guard.js": {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_use_id": "t1",
                                 "tool_input": {"command": "gh pr create"}},
        "team-stop-guard.js": {"hook_event_name": "Stop", "stop_hook_active": False, "background_tasks": []},
    }
    for hook in HOOKS:
        tmp = Path(tempfile.mkdtemp(prefix="noactiverun_"))
        state_root = tmp / "state"
        payload = dict(generic[hook])
        payload["cwd"] = str(tmp)
        proc = run_hook(hook, payload, tmp, state_root)
        ok = proc.returncode == 0 and proc.stdout == ""
        shutil.rmtree(tmp, ignore_errors=True)
        all_ok &= report(hook, "no-active-run", "exit 0, no stdout", f"exit {proc.returncode}, stdout {proc.stdout!r}", ok)
    return all_ok


def test_malformed_json() -> bool:
    all_ok = True
    for hook in HOOKS:
        tmp = Path(tempfile.mkdtemp(prefix="malformed_"))
        state_root = tmp / "state"
        proc = run_hook_raw(hook, "{not valid json", tmp, state_root)
        ok = proc.returncode == 0 and proc.stdout == ""
        shutil.rmtree(tmp, ignore_errors=True)
        all_ok &= report(hook, "malformed-json", "exit 0, no stdout, no crash", f"exit {proc.returncode}, stdout {proc.stdout!r}, stderr {proc.stderr!r}", ok)
    return all_ok


# ---------------------------------------------------------------------------
# install.py
# ---------------------------------------------------------------------------

def run_install(args):
    return subprocess.run([sys.executable, str(INSTALL_PY)] + list(args), capture_output=True, text=True)


def test_install() -> bool:
    hook = "install.py"
    all_ok = True

    # install-fresh: empty settings, four entries added, --check exits 0
    tmp = Path(tempfile.mkdtemp(prefix="install_fresh_"))
    proc = run_install(["--project", str(tmp)])
    settings_path = tmp / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.is_file() else None
    events_present = sorted((settings or {}).get("hooks", {}).keys())
    check_proc = run_install(["--project", str(tmp), "--check"])
    ok = (proc.returncode == 0 and settings is not None
          and events_present == ["PostToolUse", "PreToolUse", "Stop", "UserPromptSubmit"]
          and check_proc.returncode == 0)
    all_ok &= report(hook, "install-fresh", "exit 0, four events registered, --check exit 0",
                      f"exit {proc.returncode}, events {events_present}, check exit {check_proc.returncode}", ok)

    # install-idempotent: second run leaves the file byte-identical
    before = settings_path.read_bytes()
    proc2 = run_install(["--project", str(tmp)])
    after = settings_path.read_bytes()
    ok = proc2.returncode == 0 and before == after
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "install-idempotent", "exit 0, file byte-identical",
                      f"exit {proc2.returncode}, identical {before == after}", ok)

    # install-preserves: an unrelated PreToolUse hook and a permissions key
    # survive untouched, and a pre-team-gate backup is written.
    tmp = Path(tempfile.mkdtemp(prefix="install_preserve_"))
    claude_dir = tmp / ".claude"
    claude_dir.mkdir(parents=True)
    settings_path = claude_dir / "settings.json"
    original = {
        "permissions": {"allow": ["Bash(ls:*)"]},
        "hooks": {
            "PreToolUse": [
                {"matcher": "Read", "hooks": [{"type": "command", "command": "node /opt/other/read-guard.js", "timeout": 30}]}
            ]
        },
    }
    settings_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
    proc = run_install(["--project", str(tmp)])
    result = json.loads(settings_path.read_text(encoding="utf-8"))
    permissions_intact = result.get("permissions") == original["permissions"]
    unrelated_hook_intact = any(
        e.get("matcher") == "Read" and e.get("hooks") == original["hooks"]["PreToolUse"][0]["hooks"]
        for e in result.get("hooks", {}).get("PreToolUse", [])
    )
    backup_path = settings_path.with_name("settings.json.bak-team-gate")
    backup_matches_original = backup_path.is_file() and json.loads(backup_path.read_text(encoding="utf-8")) == original
    ok = proc.returncode == 0 and permissions_intact and unrelated_hook_intact and backup_matches_original
    all_ok &= report(hook, "install-preserves", "exit 0, unrelated hook and permissions intact, backup written",
                      f"exit {proc.returncode}, permissions_ok {permissions_intact}, hook_ok {unrelated_hook_intact}, backup_ok {backup_matches_original}", ok)

    # install-remove: leaves the unrelated hook, deletes the four
    proc_remove = run_install(["--project", str(tmp), "--remove"])
    after_remove = json.loads(settings_path.read_text(encoding="utf-8"))
    pre_entries = after_remove.get("hooks", {}).get("PreToolUse", [])
    unrelated_still_there = any(e.get("matcher") == "Read" for e in pre_entries)
    team_gate_gone_from_pre = not any(
        command_names_a_team_gate_file(h.get("command", ""))
        for e in pre_entries for h in e.get("hooks", [])
    )
    no_other_team_gate_events = not any(k in after_remove.get("hooks", {}) for k in ("UserPromptSubmit", "Stop", "PostToolUse"))
    ok = proc_remove.returncode == 0 and unrelated_still_there and team_gate_gone_from_pre and no_other_team_gate_events
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "install-remove", "exit 0, unrelated hook kept, team-gate entries removed",
                      f"exit {proc_remove.returncode}, unrelated_kept {unrelated_still_there}, team_gate_gone {team_gate_gone_from_pre}, other_events_gone {no_other_team_gate_events}", ok)

    # install-check-missing: --check on a file without them exits 1
    tmp = Path(tempfile.mkdtemp(prefix="install_checkmissing_"))
    claude_dir = tmp / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "settings.json").write_text(json.dumps({"hooks": {}}, indent=2) + "\n", encoding="utf-8")
    proc = run_install(["--project", str(tmp), "--check"])
    ok = proc.returncode == 1
    shutil.rmtree(tmp, ignore_errors=True)
    all_ok &= report(hook, "install-check-missing", "exit 1", f"exit {proc.returncode}", ok)

    return all_ok


def command_names_a_team_gate_file(command: str) -> bool:
    team_gate_files = ("team-turn-log.js", "team-artifact-guard.js", "team-stage-guard.js", "team-stop-guard.js")
    return any(f in (command or "") for f in team_gate_files)


def main() -> int:
    if not FIXTURES_DIR.is_dir():
        print("ERROR: fixtures directory not found:", FIXTURES_DIR, file=sys.stderr)
        return 2

    suites = [
        test_team_turn_log,
        test_team_artifact_guard,
        test_team_stage_guard,
        test_team_stop_guard,
        test_no_active_run,
        test_malformed_json,
        test_install,
    ]

    all_ok = True
    for suite in suites:
        all_ok = suite() and all_ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
