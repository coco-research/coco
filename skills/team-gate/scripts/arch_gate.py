#!/usr/bin/env python3
"""Gate architecture conformance by invoking validate_index.py and arch_drift.py.

Exits 0 when conformance passes, 1 when a block exists, 2 when unrunnable or
unverified.

Standalone flag-only invocation (unchanged), pass rules from
commands/team/architecture.md lines 93-117:
  - Any failed validate_index.py check: BLOCK (exit 1)
  - Component with zero surviving primary paths (REMOVE verdict): BLOCK (exit 1)
  - Index pinned to commit != HEAD: UNVERIFIED (exit 2)
  - Drift detected but not reconciled: UNVERIFIED (exit 2)
  - PRUNE verdict only: exit 0 but print MAJOR line to stdout
  - Subprocess fails to run: exit 2

Writes result JSON to --out (default .arch/ARCH-GATE.json):
  {gate, exit, removes, prunes, validate_exit, drift_exit, pin, head, reason, tools_dir}

Usage:
    python3 arch_gate.py --repo-root .
    python3 arch_gate.py --repo-root . --index .arch/index.json --out .arch/ARCH-GATE.json
    python3 arch_gate.py --self-test

Run-aware subcommands (each requires an active run started via gate_state.py;
absence of a run is exit 2). Run resolution matches brownfield_map.py's
_resolve_context exactly: gate_state.find_run() walks up from --repo-root to
the .team-ship/RUN pointer, then --repo-root's own git toplevel is checked
against run.json's own repo_root; a mismatch is refused before anything is
written. Each writes a gate file under run_dir/gates (argv, cwd, head, exit,
summary, plus its own fields), atomically, followed by a gate-result receipt;
a receipt failure is exit 2.

  baseline --repo-root <r>       Stage 1. Records {pin, head, status} to
                                  gates/1-arch-baseline.json. status is
                                  DISABLED when the run was started with a
                                  no-arch flag, NOT_APPLICABLE when
                                  <root>/.arch/index.json is absent, STALE
                                  when the pin is not HEAD, CURRENT
                                  otherwise. Exit 0 for CURRENT, 2 for the
                                  other three, never 1.

  plan-declare --repo-root <r>   Stage 3. Runs verify_arch_plan.py
                                  <root>/.team-ship/ARCH-PLAN.json --declare
                                  --repo-root <root> with no shell, a
                                  120-second timeout, cwd at <root>. Writes
                                  gates/3-arch-plan.json. Exit 0 when the
                                  child exits 0, 1 when it exits 1 (a shape
                                  violation, a real BLOCK), 2 when the child
                                  cannot run, times out, or reports the plan
                                  itself unreadable (its own exit 2, which
                                  covers ARCH-PLAN.json being absent).

  plan-verify --repo-root <r>    Stage 13. Same wrapper with --verify,
                                  writing gates/13-arch-plan.json. The same
                                  three-way exit mapping applies. Note:
                                  verify_arch_plan.py's --verify mode reports
                                  an unresolvable declaredAtCommit as its own
                                  violation but exits 1 for it exactly like a
                                  real missing-path or out-of-scope BLOCK; it
                                  does not distinguish the two by exit code.
                                  This wrapper therefore does not invent a
                                  distinction the child does not make: every
                                  child exit of 1 maps to this gate's exit 1,
                                  and only a launch failure, a timeout, or
                                  the child's own distinct exit 2 (plan
                                  unreadable) maps to this gate's exit 2.

  conformance --repo-root <r>    Stage 13. Reads gates/1-arch-baseline.json.
                                  Absent baseline is exit 2, status
                                  NO_BASELINE. A recorded status of DISABLED,
                                  NOT_APPLICABLE or STALE reproduces that
                                  status with exit 2. CURRENT runs
                                  validate_index.py and arch_drift.py with
                                  the present pass rules minus the pin-vs-HEAD
                                  check: inside a run the pin is expected to
                                  be behind HEAD after the build (Stage 6 has
                                  committed), so that comparison is only ever
                                  made once, at Stage 1 by baseline. Every
                                  resolved path (NO_BASELINE, DISABLED,
                                  NOT_APPLICABLE, STALE or CURRENT) writes
                                  gates/13-arch.json with a gate-result
                                  receipt; .arch/ARCH-GATE.json, the
                                  committed human-facing record, is written
                                  only on the CURRENT path.

Exit codes: 0 pass, 1 block, 2 unrunnable or unverified.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_state


def resolve_tools_dir(repo_root):
    """Resolve the arch-index scripts directory.

    Returns a tuple (tools_dir, error_reason). On success, tools_dir is set and
    error_reason is None. On failure, tools_dir is None and error_reason contains
    the reason string.

    Resolution order:
    1. ARCH_INDEX_SCRIPTS environment variable (must exist and contain all required scripts)
    2. <repo_root>/skills/arch-index/scripts (if it contains all required scripts)
    3. ~/.claude/skills/arch-index/scripts

    Args:
        repo_root: The repository root path

    Returns:
        Tuple of (tools_dir, error_reason). Either tools_dir or error_reason is None.
    """
    required_scripts = ["validate_index.py", "arch_drift.py", "verify_arch_plan.py"]

    # Try ARCH_INDEX_SCRIPTS env var first
    env_tools_dir = os.environ.get("ARCH_INDEX_SCRIPTS")
    if env_tools_dir:
        env_tools_dir = os.path.abspath(env_tools_dir)
        if all(os.path.isfile(os.path.join(env_tools_dir, script)) for script in required_scripts):
            return env_tools_dir, None
        # ARCH_INDEX_SCRIPTS is set but incomplete; error, don't fall through
        return None, f"arch-index scripts not found in {env_tools_dir}"

    # Try <repo_root>/skills/arch-index/scripts
    repo_tools_dir = os.path.join(repo_root, "skills", "arch-index", "scripts")
    if all(os.path.isfile(os.path.join(repo_tools_dir, script)) for script in required_scripts):
        return repo_tools_dir, None

    # Fall back to ~/.claude/skills/arch-index/scripts
    home_tools_dir = os.path.expanduser("~/.claude/skills/arch-index/scripts")
    if all(os.path.isfile(os.path.join(home_tools_dir, script)) for script in required_scripts):
        return home_tools_dir, None

    # None of the locations have both scripts
    return None, f"arch-index scripts not found in {home_tools_dir}"


def run_command(cmd, cwd):
    """Run a command and return (exit_code, stdout, stderr).

    Returns (None, "", error_msg) if the subprocess cannot launch (distinct from exit code).
    """
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError as exc:
        return None, "", f"command not found: {exc}"
    except Exception as exc:
        return None, "", f"subprocess error: {exc}"


def git_rev_parse(root, ref):
    """Get a git revision, return None if not found."""
    exit_code, out, _ = run_command(["git", "rev-parse", ref], cwd=root)
    return out.strip() if exit_code == 0 else None


RUN_AWARE_SUBCOMMANDS = ("baseline", "plan-declare", "plan-verify", "conformance")


def main():
    argv = sys.argv[1:]
    if argv and argv[0] in RUN_AWARE_SUBCOMMANDS:
        return dispatch_run_aware(argv[0], argv[1:])

    ap = argparse.ArgumentParser(
        description="Gate architecture conformance against index and drift."
    )
    ap.add_argument("--repo-root", default=".", help="repository root")
    ap.add_argument("--index", default=None, help="path to .arch/index.json")
    ap.add_argument("--out", default=None, help="path to write .arch/ARCH-GATE.json")
    ap.add_argument("--self-test", action="store_true", help="run self-test on fixtures")
    args = ap.parse_args()

    root = os.path.abspath(args.repo_root)
    index_path = args.index or os.path.join(root, ".arch", "index.json")
    out_path = args.out or os.path.join(root, ".arch", "ARCH-GATE.json")

    if args.self_test:
        return self_test(root)

    # Resolve tools directory
    tools_dir, tools_error = resolve_tools_dir(root)
    if tools_error:
        print(f"ERROR: {tools_error}", file=sys.stderr)
        return 2

    # Check pin vs HEAD
    pin = None
    head = git_rev_parse(root, "HEAD")
    if not head:
        reason = "HEAD not found; not a git repository"
        exit_code = 2
        print(reason, file=sys.stderr)
        return exit_code

    # Load index to get the pinned commit
    if not os.path.isfile(index_path):
        reason = f"index not found at {index_path}"
        print(reason, file=sys.stderr)
        return 2

    try:
        with open(index_path) as fh:
            index = json.load(fh)
        pin = index.get("pinnedCommit")
    except (json.JSONDecodeError, IOError) as exc:
        reason = f"cannot read index: {exc}"
        print(reason, file=sys.stderr)
        return 2

    # Check for stale pin
    pin_path = os.path.join(root, ".arch", "pinned-commit")
    if os.path.isfile(pin_path):
        with open(pin_path) as fh:
            file_pin = fh.read().strip()
        if file_pin:
            pin = file_pin

    if pin and pin != head:
        reason = (
            f"UNVERIFIED: index pinned to {pin[:12]}, HEAD is {head[:12]}; "
            f"reconcile with /team arch build"
        )
        print(reason, file=sys.stderr)
        result = {
            "gate": "UNVERIFIED",
            "exit": 2,
            "removes": [],
            "prunes": [],
            "validate_exit": None,
            "drift_exit": None,
            "pin": pin,
            "head": head,
            "reason": reason,
            "tools_dir": tools_dir,
        }
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as fh:
            json.dump(result, fh, indent=2)
        return 2

    # Run validate_index.py
    validate_script = os.path.join(tools_dir, "validate_index.py")
    validate_exit, _, validate_err = run_command(
        ["python3", validate_script, index_path, "--repo-root", root, "--quiet"],
        cwd=root,
    )

    # Run arch_drift.py with temp output file
    drift_script = os.path.join(tools_dir, "arch_drift.py")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        drift_exit, _, drift_err = run_command(
            ["python3", drift_script, "--repo-root", root, "--out", tmp_path],
            cwd=root,
        )

        # Read drift JSON
        drift_data = {}
        if drift_exit == 0 and os.path.isfile(tmp_path):
            try:
                with open(tmp_path) as fh:
                    drift_data = json.load(fh)
            except json.JSONDecodeError:
                pass

        # Extract verdicts
        removes = [
            c["id"]
            for c in drift_data.get("components", [])
            if c.get("verdict") == "REMOVE"
        ]
        prunes = [
            c["id"]
            for c in drift_data.get("components", [])
            if c.get("verdict") == "PRUNE"
        ]

        # Apply pass rules in order: launch failures first, then other blocks
        exit_code = 0
        reason_parts = []

        # Check if subprocesses failed to launch
        if validate_exit is None:
            exit_code = 2
            reason_parts.append(f"validate_index.py failed to launch: {validate_err}")
        if drift_exit is None:
            exit_code = 2
            reason_parts.append(f"arch_drift.py failed to launch: {drift_err}")

        if exit_code == 2:
            reason = "; ".join(reason_parts)
        else:
            # Compute all block conditions
            reason_parts = []

            if removes:
                reason_parts.append(f"REMOVE: {len(removes)} component(s) ({', '.join(removes)})")
                exit_code = 1

            if prunes:
                reason_parts.append(f"PRUNE: {len(prunes)} component(s) ({', '.join(prunes)})")
                if exit_code == 0:
                    print(f"MAJOR: PRUNE {' '.join(prunes)}")

            if validate_exit != 0:
                reason_parts.append(f"validate_index.py failed (exit {validate_exit})")
                exit_code = 1

            if drift_exit != 0:
                reason_parts.append(f"arch_drift.py failed (exit {drift_exit})")
                if exit_code != 1:
                    exit_code = 2

            reason = "; ".join(reason_parts) if reason_parts else ""

        # Write result JSON
        result = {
            "gate": "BLOCK" if exit_code == 1 else "UNVERIFIED" if exit_code == 2 else "PASS",
            "exit": exit_code,
            "removes": removes,
            "prunes": prunes,
            "validate_exit": validate_exit,
            "drift_exit": drift_exit,
            "pin": pin,
            "head": head,
            "reason": reason,
            "tools_dir": tools_dir,
        }

        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as fh:
            json.dump(result, fh, indent=2)

        # Print summary line
        print(
            f"gate={result['gate']} exit={exit_code} removes={len(removes)} "
            f"prunes={len(prunes)} validate_exit={validate_exit} drift_exit={drift_exit}",
            file=sys.stderr,
        )

        if exit_code != 0 and reason:
            print(reason, file=sys.stderr)

        return exit_code

    finally:
        if os.path.isfile(tmp_path):
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Run-aware subcommands: baseline, plan-declare, plan-verify, conformance
# ---------------------------------------------------------------------------

def _atomic_write(path, content_bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.tmp"
    tmp.write_bytes(content_bytes)
    os.replace(str(tmp), str(path))


def _write_gate_and_receipt(run_dir, filename, data, gate_name, exit_code, summary):
    """Write a gate file under run_dir/gates and append its gate-result receipt.

    Returns None on success, or an exit code (2) on failure.
    """
    gate_file = run_dir / "gates" / filename
    content = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        _atomic_write(gate_file, content)
    except OSError as exc:
        print(f"ERROR: cannot write {gate_file}: {exc}", file=sys.stderr)
        return 2
    try:
        gate_sha256 = hashlib.sha256(gate_file.read_bytes()).hexdigest()
        gate_state.append_receipt(run_dir, "gate-result", {
            "gate": gate_name,
            "gate_file": f"gates/{gate_file.name}",
            "gate_sha256": gate_sha256,
            "exit": exit_code,
            "summary": summary,
        })
    except Exception as exc:
        try:
            gate_file.unlink()
        except OSError:
            pass
        print(f"ERROR: cannot append receipt: {exc}", file=sys.stderr)
        return 2
    return None


def _resolve_context(repo_root_arg):
    """Resolve (repo_root, run_dir, head) for a run-aware subcommand, or print
    one ERROR line and return None.

    Mirrors brownfield_map.py's _resolve_context: gate_state.find_run() walks
    up from repo_root_arg to the .team-ship/RUN pointer, then repo_root_arg's
    own git toplevel is checked against run.json's own repo_root. A mismatch
    is refused before anything is written. The recorded repo_root wins from
    that point on; the raw argument is discarded.
    """
    repo_root_input = Path(repo_root_arg).resolve()
    run_dir = gate_state.find_run(repo_root_input)
    if run_dir is None:
        print(f"ERROR: no active run found under {repo_root_input}", file=sys.stderr)
        return None

    run_json_path = run_dir / "run.json"
    try:
        run_obj = json.loads(run_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: run.json unreadable: {exc}", file=sys.stderr)
        return None

    recorded_root_str = run_obj.get("repo_root")
    if not recorded_root_str:
        print(f"ERROR: run.json missing repo_root: {run_json_path}", file=sys.stderr)
        return None
    recorded_root = Path(recorded_root_str).resolve()

    try:
        toplevel_result = subprocess.run(
            ["git", "-C", str(repo_root_input), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
    except OSError as exc:
        print(f"ERROR: repository unreadable: git rev-parse --show-toplevel failed: {exc}",
              file=sys.stderr)
        return None
    if toplevel_result.returncode != 0:
        print(f"ERROR: repository unreadable: git rev-parse --show-toplevel failed: "
              f"{toplevel_result.stderr.strip()}", file=sys.stderr)
        return None
    toplevel = Path(toplevel_result.stdout.strip()).resolve()

    if toplevel != recorded_root:
        print(f"ERROR: repo-root mismatch: --repo-root {repo_root_input} is inside "
              f"repository {toplevel}, run {run_dir.name} belongs to {recorded_root}",
              file=sys.stderr)
        return None

    repo_root = recorded_root

    try:
        head_result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
    except OSError as exc:
        print(f"ERROR: repository unreadable: git rev-parse HEAD failed: {exc}", file=sys.stderr)
        return None
    if head_result.returncode != 0:
        print(f"ERROR: repository unreadable: git rev-parse HEAD failed: "
              f"{head_result.stderr.strip()}", file=sys.stderr)
        return None
    return repo_root, run_dir, head_result.stdout.strip()


def _flag_is_no_arch(flag):
    if not isinstance(flag, str):
        return False
    normalized = flag.strip().lower().lstrip("-").replace("_", "-")
    return normalized == "no-arch"


def _run_flags(run_dir):
    try:
        run_obj = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    flags = run_obj.get("flags")
    return flags if isinstance(flags, list) else []


def _pin_from_index_and_file(repo_root, index):
    """Same precedence arch_drift.py and the standalone mode use: index.json's
    pinnedCommit, overridden by .arch/pinned-commit when that file exists and
    is non-empty."""
    pin = index.get("pinnedCommit")
    pin_path = repo_root / ".arch" / "pinned-commit"
    if pin_path.is_file():
        file_pin = pin_path.read_text().strip()
        if file_pin:
            pin = file_pin
    return pin


def cmd_baseline(repo_root_arg):
    ctx = _resolve_context(repo_root_arg)
    if ctx is None:
        return 2
    repo_root, run_dir, head = ctx
    argv = ["baseline", "--repo-root", repo_root_arg]
    cwd = str(repo_root)

    flags = _run_flags(run_dir)
    index_path = repo_root / ".arch" / "index.json"

    pin = None
    if _arch_disabled(flags):
        status = "DISABLED"
    elif not index_path.is_file():
        status = "NOT_APPLICABLE"
    else:
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: cannot read index: {exc}", file=sys.stderr)
            return 2
        pin = _pin_from_index_and_file(repo_root, index)
        status = "CURRENT" if pin == head else "STALE"

    exit_code = 0 if status == "CURRENT" else 2
    if pin:
        summary = f"arch baseline: {status} pin={pin[:12]} head={head[:12]}"
    else:
        summary = f"arch baseline: {status} head={head[:12]}"

    data = {
        "argv": argv, "cwd": cwd, "head": head, "exit": exit_code, "summary": summary,
        "pin": pin, "status": status,
    }
    rc = _write_gate_and_receipt(run_dir, "1-arch-baseline.json", data,
                                  "arch-baseline", exit_code, summary)
    if rc is not None:
        return rc

    print(summary, file=sys.stderr)
    return exit_code


def _arch_disabled(flags):
    return any(_flag_is_no_arch(f) for f in flags)


def _run_verify_arch_plan(tools_dir, plan_path, mode_flag, root, timeout=120):
    """Invoke verify_arch_plan.py in --declare or --verify mode.

    Returns (child_exit, stdout, stderr, launch_error, cmd). child_exit is
    None and launch_error is set when the subprocess could not be started or
    timed out; launch_error is None otherwise.
    """
    script = os.path.join(tools_dir, "verify_arch_plan.py")
    cmd = ["python3", script, str(plan_path), mode_flag, "--repo-root", str(root)]
    try:
        result = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True,
                                 timeout=timeout, check=False)
        return result.returncode, result.stdout, result.stderr, None, cmd
    except subprocess.TimeoutExpired:
        return None, "", "", f"verify_arch_plan.py timed out after {timeout}s", cmd
    except OSError as exc:
        return None, "", "", f"verify_arch_plan.py failed to launch: {exc}", cmd


def _map_plan_exit(child_exit):
    """Map verify_arch_plan.py's exit to this gate's exit: 0 stays 0. 2 (the
    plan itself unreadable, absent or invalid JSON) stays 2, since that is
    the child's own distinct code and is always distinguishable from a real
    BLOCK. Any other non-zero exit, including 1 for a real shape or built
    violation, is 1. --verify's own "cannot compare against declaredAtCommit"
    violation also exits 1 from the child, indistinguishable by exit code
    alone from a real missing-path or out-of-scope BLOCK, so it folds into
    this same exit-1 bucket rather than inventing a distinction the child
    does not make."""
    if child_exit is None:
        return 2
    if child_exit == 0:
        return 0
    if child_exit == 2:
        return 2
    return 1


def _plan_gate(repo_root_arg, mode_flag, gate_filename, gate_name, stage_label):
    ctx = _resolve_context(repo_root_arg)
    if ctx is None:
        return 2
    repo_root, run_dir, head = ctx

    tools_dir, tools_error = resolve_tools_dir(str(repo_root))
    if tools_error:
        print(f"ERROR: {tools_error}", file=sys.stderr)
        return 2

    plan_path = repo_root / ".team-ship" / "ARCH-PLAN.json"
    child_exit, stdout, stderr, launch_error, cmd = _run_verify_arch_plan(
        tools_dir, plan_path, mode_flag, repo_root)

    exit_code = _map_plan_exit(child_exit)
    stdout_lines = [ln for ln in stdout.splitlines() if ln.strip()]
    stdout_tail = stdout_lines[-40:]

    if launch_error:
        summary = f"{stage_label}: {launch_error}"
    else:
        summary = f"{stage_label}: child_exit={child_exit} -> exit={exit_code}"

    data = {
        "argv": cmd, "cwd": str(repo_root), "head": head, "exit": exit_code,
        "summary": summary, "child_exit": child_exit, "stdout_tail": stdout_tail,
    }
    rc = _write_gate_and_receipt(run_dir, gate_filename, data, gate_name, exit_code, summary)
    if rc is not None:
        return rc

    if exit_code != 0:
        for line in stdout_lines:
            print(line, file=sys.stderr)
        if launch_error:
            print(launch_error, file=sys.stderr)
    print(summary, file=sys.stderr)
    return exit_code


def cmd_plan_declare(repo_root_arg):
    return _plan_gate(repo_root_arg, "--declare", "3-arch-plan.json",
                       "arch-plan-declare", "plan-declare")


def cmd_plan_verify(repo_root_arg):
    return _plan_gate(repo_root_arg, "--verify", "13-arch-plan.json",
                       "arch-plan-verify", "plan-verify")


def cmd_conformance(repo_root_arg):
    ctx = _resolve_context(repo_root_arg)
    if ctx is None:
        return 2
    repo_root, run_dir, head = ctx
    argv = ["conformance", "--repo-root", repo_root_arg]
    cwd = str(repo_root)

    tools_dir, tools_error = resolve_tools_dir(str(repo_root))
    if tools_error:
        print(f"ERROR: {tools_error}", file=sys.stderr)
        return 2

    baseline_path = run_dir / "gates" / "1-arch-baseline.json"
    if not baseline_path.is_file():
        exit_code = 2
        summary = "conformance: no baseline recorded; run the baseline subcommand first"
        data = {
            "argv": argv, "cwd": cwd, "head": head, "exit": exit_code, "summary": summary,
            "tools_dir": tools_dir, "status": "NO_BASELINE", "pin": None,
        }
        rc = _write_gate_and_receipt(run_dir, "13-arch.json", data, "arch-conformance",
                                      exit_code, summary)
        if rc is not None:
            return rc
        print(summary, file=sys.stderr)
        return exit_code

    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"conformance: baseline gate file unreadable: {exc}", file=sys.stderr)
        return 2

    baseline_status = baseline.get("status")
    pin = baseline.get("pin")

    if baseline_status != "CURRENT":
        exit_code = 2
        summary = (f"conformance: baseline status is {baseline_status}, "
                    f"cannot be checked honestly")
        data = {
            "argv": argv, "cwd": cwd, "head": head, "exit": exit_code, "summary": summary,
            "tools_dir": tools_dir, "status": baseline_status, "pin": pin,
        }
        rc = _write_gate_and_receipt(run_dir, "13-arch.json", data, "arch-conformance",
                                      exit_code, summary)
        if rc is not None:
            return rc
        print(summary, file=sys.stderr)
        return exit_code

    index_path = repo_root / ".arch" / "index.json"
    validate_script = os.path.join(tools_dir, "validate_index.py")
    validate_exit, _, validate_err = run_command(
        ["python3", validate_script, str(index_path), "--repo-root", str(repo_root), "--quiet"],
        cwd=str(repo_root),
    )

    drift_script = os.path.join(tools_dir, "arch_drift.py")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        drift_exit, _, drift_err = run_command(
            ["python3", drift_script, "--repo-root", str(repo_root), "--out", tmp_path],
            cwd=str(repo_root),
        )

        drift_data = {}
        if drift_exit == 0 and os.path.isfile(tmp_path):
            try:
                with open(tmp_path) as fh:
                    drift_data = json.load(fh)
            except json.JSONDecodeError:
                pass

        removes = [
            c["id"] for c in drift_data.get("components", []) if c.get("verdict") == "REMOVE"
        ]
        prunes = [
            c["id"] for c in drift_data.get("components", []) if c.get("verdict") == "PRUNE"
        ]

        exit_code = 0
        reason_parts = []

        if validate_exit is None:
            exit_code = 2
            reason_parts.append(f"validate_index.py failed to launch: {validate_err}")
        if drift_exit is None:
            exit_code = 2
            reason_parts.append(f"arch_drift.py failed to launch: {drift_err}")

        if exit_code == 2:
            reason = "; ".join(reason_parts)
        else:
            reason_parts = []

            if removes:
                reason_parts.append(f"REMOVE: {len(removes)} component(s) ({', '.join(removes)})")
                exit_code = 1

            if prunes:
                reason_parts.append(f"PRUNE: {len(prunes)} component(s) ({', '.join(prunes)})")
                if exit_code == 0:
                    print(f"MAJOR: PRUNE {' '.join(prunes)}")

            if validate_exit != 0:
                reason_parts.append(f"validate_index.py failed (exit {validate_exit})")
                exit_code = 1

            if drift_exit != 0:
                reason_parts.append(f"arch_drift.py failed (exit {drift_exit})")
                if exit_code != 1:
                    exit_code = 2

            reason = "; ".join(reason_parts) if reason_parts else ""

        gate = "BLOCK" if exit_code == 1 else "UNVERIFIED" if exit_code == 2 else "PASS"
        summary = reason if reason else f"conformance: {gate}"

        data = {
            "argv": argv, "cwd": cwd, "head": head, "exit": exit_code, "summary": summary,
            "gate": gate, "removes": removes, "prunes": prunes,
            "validate_exit": validate_exit, "drift_exit": drift_exit,
            "pin": pin, "tools_dir": tools_dir, "status": baseline_status,
        }

        rc = _write_gate_and_receipt(run_dir, "13-arch.json", data, "arch-conformance",
                                      exit_code, summary)
        if rc is not None:
            return rc

        # The committed, human-facing record. Kept at the same path the
        # standalone mode has always used, so downstream tooling and the
        # Stage 11 clean checkout keep reading one file regardless of mode.
        # Written only on the CURRENT path; the non-CURRENT branches above
        # return before reaching here.
        legacy_out = repo_root / ".arch" / "ARCH-GATE.json"
        legacy_data = dict(data)
        legacy_data["reason"] = reason
        os.makedirs(legacy_out.parent, exist_ok=True)
        with open(legacy_out, "w") as fh:
            json.dump(legacy_data, fh, indent=2)

        print(
            f"gate={gate} exit={exit_code} removes={len(removes)} prunes={len(prunes)} "
            f"validate_exit={validate_exit} drift_exit={drift_exit}",
            file=sys.stderr,
        )
        if exit_code != 0 and reason:
            print(reason, file=sys.stderr)
        return exit_code
    finally:
        if os.path.isfile(tmp_path):
            os.unlink(tmp_path)


def dispatch_run_aware(name, rest):
    ap = argparse.ArgumentParser(prog=f"arch_gate.py {name}",
                                  description=f"Run the {name} gate for the active run.")
    ap.add_argument("--repo-root", required=True, help="repository root, or a subdirectory of it")
    args = ap.parse_args(rest)

    if name == "baseline":
        return cmd_baseline(args.repo_root)
    if name == "plan-declare":
        return cmd_plan_declare(args.repo_root)
    if name == "plan-verify":
        return cmd_plan_verify(args.repo_root)
    if name == "conformance":
        return cmd_conformance(args.repo_root)
    print(f"unknown subcommand: {name}", file=sys.stderr)
    return 2


_REAL_ARCH_INDEX_SCRIPTS = str(Path(__file__).resolve().parents[2] / "arch-index" / "scripts")


def _ra_isolated_copy(build_dir, name, start_run=True, flags=None):
    """Copy a generated fixture into a fresh temporary directory, point
    TEAM_STATE_ROOT at a fresh state directory beside it, and optionally
    start a run against the copy through the gate_state API (which is what
    writes the .team-ship/RUN pointer)."""
    tmp_root = Path(tempfile.mkdtemp(prefix=f"arch_gate_{name}_"))
    copy_path = tmp_root / name
    shutil.copytree(build_dir / name, copy_path)
    state_root = tmp_root / "state"
    state_root.mkdir()
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(state_root)
    os.environ["TEAM_STATE_ROOT"] = str(state_root)
    if start_run:
        gate_state.start_run(str(copy_path), "ship", flags or [])
    return copy_path, env


def _ra_invoke(subcommand, repo_root, env, needs_tools=False):
    call_env = dict(env)
    if needs_tools:
        call_env["ARCH_INDEX_SCRIPTS"] = _REAL_ARCH_INDEX_SCRIPTS
    return subprocess.run([sys.executable, __file__, subcommand, "--repo-root", str(repo_root)],
                           capture_output=True, text=True, timeout=60, env=call_env)


def _ra_extra_commit(repo_path):
    """Advance HEAD past a recorded baseline pin by touching an already
    claimed file, the way a build stage's commit would."""
    target = repo_path / "src" / "a" / "main.rs"
    with target.open("a") as fh:
        fh.write("// build addition\n")
    subprocess.run(["git", "add", "-A"], cwd=str(repo_path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "build addition"], cwd=str(repo_path),
                    check=True, capture_output=True)


def _ra_gate_data(copy_path, gate_filename):
    """Read a gate file's parsed JSON for the run started against copy_path.
    Returns None when the run, the file or its JSON cannot be found."""
    run_dir = gate_state.find_run(copy_path)
    if run_dir is None:
        return None
    gate_file = run_dir / "gates" / gate_filename
    if not gate_file.is_file():
        return None
    try:
        return json.loads(gate_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _check_gate_status(label, copy_path, gate_filename, expected_status):
    data = _ra_gate_data(copy_path, gate_filename)
    status = data.get("status") if data else None
    ok = data is not None and status == expected_status
    print(f"  {'PASS' if ok else 'FAIL'}  {label:36s} status={status!r} "
          f"(expect {expected_status!r})")
    return ok


def _ra_gate_receipt_present(copy_path, gate_filename):
    run_dir = gate_state.find_run(copy_path)
    if run_dir is None:
        return False
    receipts_file = run_dir / "receipts.jsonl"
    if not receipts_file.is_file():
        return False
    target = f"gates/{gate_filename}"
    for line in receipts_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("kind") == "gate-result" and rec.get("detail", {}).get("gate_file") == target:
            return True
    return False


def _check_receipt_present(label, copy_path, gate_filename):
    ok = _ra_gate_receipt_present(copy_path, gate_filename)
    print(f"  {'PASS' if ok else 'FAIL'}  {label:36s} receipt-present={ok}")
    return ok


def _check_verify_chain(label, copy_path, env):
    gate_state_script = Path(__file__).resolve().parent / "gate_state.py"
    proc = subprocess.run([sys.executable, str(gate_state_script), "verify-chain"],
                           cwd=str(copy_path), env=env, capture_output=True, text=True,
                           timeout=30)
    ok = proc.returncode == 0
    print(f"  {'PASS' if ok else 'FAIL'}  {label:36s} exit={proc.returncode} (expect 0)")
    return ok


def _self_test_run_aware():
    """Exercise baseline, plan-declare, plan-verify and conformance, each on
    a temporary copy of a generated fixture with a run started through the
    gate_state API and the .team-ship/RUN pointer written."""
    fixtures_dir = Path(__file__).resolve().parent / "fixtures" / "arch_gate"
    build_dir = fixtures_dir / "_build"
    make_fixtures = fixtures_dir / "make_fixtures.py"

    result = subprocess.run([sys.executable, str(make_fixtures)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAIL  make_fixtures.py -> {result.stderr}", file=sys.stderr)
        return False

    all_ok = True

    def check(name, proc, expected_exit, contains=None):
        nonlocal all_ok
        ok = proc.returncode == expected_exit
        if ok and contains and contains not in proc.stderr:
            ok = False
        suffix = f" contains={contains!r}" if contains else ""
        print(f"  {'PASS' if ok else 'FAIL'}  {name:36s} exit={proc.returncode} "
              f"(expect {expected_exit}){suffix}")
        if not ok:
            all_ok = False
        return ok

    # baseline-current: clean fixture, pin==head at run start, CURRENT.
    copy_path, env = _ra_isolated_copy(build_dir, "clean")
    check("baseline-current", _ra_invoke("baseline", copy_path, env), 0)

    # baseline-stale: stale-pin fixture, pin != head already at Stage 1.
    copy_path, env = _ra_isolated_copy(build_dir, "stale-pin")
    check("baseline-stale", _ra_invoke("baseline", copy_path, env), 2, "STALE")

    # baseline-no-index: no .arch/index.json at all.
    copy_path, env = _ra_isolated_copy(build_dir, "no-index")
    check("baseline-no-index", _ra_invoke("baseline", copy_path, env), 2, "NOT_APPLICABLE")

    # baseline-disabled: the run was started with a no-arch flag.
    copy_path, env = _ra_isolated_copy(build_dir, "clean", flags=["--no-arch"])
    check("baseline-disabled", _ra_invoke("baseline", copy_path, env), 2, "DISABLED")

    # declare-pass / declare-fail / declare-no-plan.
    copy_path, env = _ra_isolated_copy(build_dir, "arch-plan-declare-pass")
    check("declare-pass", _ra_invoke("plan-declare", copy_path, env, needs_tools=True), 0)

    copy_path, env = _ra_isolated_copy(build_dir, "arch-plan-declare-fail")
    check("declare-fail", _ra_invoke("plan-declare", copy_path, env, needs_tools=True),
          1, "kebab-case")

    copy_path, env = _ra_isolated_copy(build_dir, "no-index")
    check("declare-no-plan", _ra_invoke("plan-declare", copy_path, env, needs_tools=True),
          2, "ARCH-PLAN.json")

    # verify-pass / verify-missing-path.
    copy_path, env = _ra_isolated_copy(build_dir, "arch-plan-verify-pass")
    check("verify-pass", _ra_invoke("plan-verify", copy_path, env, needs_tools=True), 0)

    copy_path, env = _ra_isolated_copy(build_dir, "arch-plan-verify-missing-path")
    check("verify-missing-path", _ra_invoke("plan-verify", copy_path, env, needs_tools=True),
          1, "webhook-ingest")

    # conformance-current-after-commit: baseline records CURRENT, then one
    # more commit moves HEAD past the recorded pin, then conformance still
    # passes. This is the R2 proof: currency is judged once, at baseline
    # time, never re-checked here.
    copy_path, env = _ra_isolated_copy(build_dir, "clean")
    check("conformance-current-after-commit/baseline", _ra_invoke("baseline", copy_path, env), 0)
    _ra_extra_commit(copy_path)
    check("conformance-current-after-commit",
          _ra_invoke("conformance", copy_path, env, needs_tools=True), 0)
    ok = _check_gate_status("conformance-current-after-commit/gate-file",
                             copy_path, "13-arch.json", "CURRENT")
    all_ok = all_ok and ok

    # conformance-stale-baseline: baseline itself already recorded STALE.
    copy_path, env = _ra_isolated_copy(build_dir, "stale-pin")
    check("conformance-stale-baseline/baseline", _ra_invoke("baseline", copy_path, env),
          2, "STALE")
    check("conformance-stale-baseline",
          _ra_invoke("conformance", copy_path, env, needs_tools=True), 2, "STALE")
    ok = _check_gate_status("conformance-stale-baseline/gate-file",
                             copy_path, "13-arch.json", "STALE")
    all_ok = all_ok and ok

    # conformance-no-baseline: conformance run without ever running baseline.
    copy_path, env = _ra_isolated_copy(build_dir, "clean")
    check("conformance-no-baseline", _ra_invoke("conformance", copy_path, env, needs_tools=True),
          2, "no baseline")
    ok = _check_gate_status("conformance-no-baseline/gate-file",
                             copy_path, "13-arch.json", "NO_BASELINE")
    all_ok = all_ok and ok

    # conformance-not-applicable: baseline over a repository with no
    # .arch/index.json records NOT_APPLICABLE; conformance reproduces the
    # same status, now with the gate file present and a receipt appended.
    copy_path, env = _ra_isolated_copy(build_dir, "no-index")
    check("conformance-not-applicable/baseline", _ra_invoke("baseline", copy_path, env),
          2, "NOT_APPLICABLE")
    check("conformance-not-applicable",
          _ra_invoke("conformance", copy_path, env, needs_tools=True), 2, "NOT_APPLICABLE")
    ok = _check_gate_status("conformance-not-applicable/gate-file",
                             copy_path, "13-arch.json", "NOT_APPLICABLE")
    all_ok = all_ok and ok
    ok = _check_receipt_present("conformance-not-applicable/receipt",
                                 copy_path, "13-arch.json")
    all_ok = all_ok and ok
    ok = _check_verify_chain("conformance-not-applicable/verify-chain", copy_path, env)
    all_ok = all_ok and ok

    # conformance-disabled: baseline over a run started with a no-arch flag
    # records DISABLED; conformance reproduces the same status the same way.
    copy_path, env = _ra_isolated_copy(build_dir, "clean", flags=["--no-arch"])
    check("conformance-disabled/baseline", _ra_invoke("baseline", copy_path, env),
          2, "DISABLED")
    check("conformance-disabled",
          _ra_invoke("conformance", copy_path, env, needs_tools=True), 2, "DISABLED")
    ok = _check_gate_status("conformance-disabled/gate-file",
                             copy_path, "13-arch.json", "DISABLED")
    all_ok = all_ok and ok
    ok = _check_receipt_present("conformance-disabled/receipt", copy_path, "13-arch.json")
    all_ok = all_ok and ok
    ok = _check_verify_chain("conformance-disabled/verify-chain", copy_path, env)
    all_ok = all_ok and ok

    # repo-root-mismatch: --repo-root points at the nested, unrelated
    # repository. find_run() walks up and finds the outer run, but the
    # toplevel cross-check refuses before anything is written.
    copy_path, env = _ra_isolated_copy(build_dir, "repo-root-mismatch")
    nested = copy_path / "nested-unrelated"
    check("repo-root-mismatch", _ra_invoke("baseline", nested, env), 2, "repo-root mismatch")

    # no-run: no run was ever started against this copy.
    copy_path, env = _ra_isolated_copy(build_dir, "no-index", start_run=False)
    check("no-run", _ra_invoke("baseline", copy_path, env), 2, "no active run")

    print()
    print(f"run-aware subcommands: {'all pass' if all_ok else 'SOME FAILED'}")
    return all_ok


def self_test(root):
    """Run all fixtures as subprocesses and assert exact exit codes."""
    test_dir = os.path.join(os.path.dirname(__file__), "fixtures", "arch_gate")
    build_dir = os.path.join(test_dir, "_build")

    if not os.path.isdir(test_dir):
        print("FAIL: fixtures directory does not exist", file=sys.stderr)
        return 1

    # Auto-build fixtures if needed
    if not os.path.isdir(build_dir):
        print("Building fixtures...", file=sys.stderr)
        script = os.path.join(test_dir, "make_fixtures.sh")
        try:
            subprocess.run(["bash", script], check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            print(f"FAIL: fixture build failed: {exc}", file=sys.stderr)
            return 1

    fixtures = ["remove-verdict", "prune-verdict", "clean", "stale-pin", "tools-dir-env", "tools-dir-repo", "tools-dir-env-missing"]
    all_pass = True

    # Expected exit codes per fixture
    expected = {
        "remove-verdict": 1,
        "prune-verdict": 0,
        "clean": 0,
        "stale-pin": 2,
        "tools-dir-env": 0,
        "tools-dir-repo": 0,
        "tools-dir-env-missing": 2,
    }

    for fixture_name in fixtures:
        env = os.environ.copy()

        # All fixtures run on temporary copies to keep in-tree _build clean

        # Determine the source fixture to copy
        if fixture_name in ["tools-dir-env", "tools-dir-env-missing"]:
            source_fixture = os.path.join(build_dir, "clean")
        elif fixture_name == "tools-dir-repo":
            source_fixture = os.path.join(build_dir, "clean")
        else:
            source_fixture = os.path.join(build_dir, fixture_name)

        if not os.path.isdir(source_fixture):
            print(f"FAIL  {fixture_name:20s} -> source fixture missing")
            all_pass = False
            continue

        # Set up environment for tools-dir tests
        if fixture_name == "tools-dir-env":
            # Copy clean fixture to temp and run with ARCH_INDEX_SCRIPTS env var set
            real_scripts = os.path.expanduser("~/.claude/skills/arch-index/scripts")
            if not os.path.isdir(real_scripts):
                print(f"SKIP  {fixture_name:20s} -> real scripts not found")
                continue

            clean_fixture = os.path.join(build_dir, "clean")
            if not os.path.isdir(clean_fixture):
                print(f"FAIL  {fixture_name:20s} -> clean fixture missing")
                all_pass = False
                continue

            tmpfixture = tempfile.mkdtemp()
            try:
                # Copy the clean fixture into tmpfixture
                shutil.copytree(clean_fixture, os.path.join(tmpfixture, "repo"))
                fixture_root = os.path.join(tmpfixture, "repo")

                tmpdir = tempfile.mkdtemp()
                try:
                    # Copy the required scripts
                    for script in ["validate_index.py", "arch_drift.py", "verify_arch_plan.py"]:
                        src = os.path.join(real_scripts, script)
                        dst = os.path.join(tmpdir, script)
                        if os.path.isfile(src):
                            shutil.copy2(src, dst)
                    env["ARCH_INDEX_SCRIPTS"] = tmpdir
                    proc = subprocess.run(
                        [sys.executable, __file__, "--repo-root", fixture_root],
                        capture_output=True,
                        text=True,
                        env=env
                    )
                    exit_code = proc.returncode
                    stderr = proc.stderr

                    expected_code = expected.get(fixture_name, 0)
                    passed = exit_code == expected_code
                    print(f"  {'PASS' if passed else 'FAIL'}  {fixture_name:20s} exit={exit_code} (expect {expected_code})")

                    # Check that tools_dir is recorded in the JSON
                    if passed:
                        try:
                            gate_file = os.path.join(fixture_root, ".arch", "ARCH-GATE.json")
                            if os.path.isfile(gate_file):
                                with open(gate_file) as fh:
                                    gate_data = json.load(fh)
                                if "tools_dir" not in gate_data or gate_data["tools_dir"] != tmpdir:
                                    print(f"    WARNING: tools_dir not correctly recorded", file=sys.stderr)
                                    all_pass = False
                        except Exception:
                            pass

                    if not passed:
                        all_pass = False
                finally:
                    shutil.rmtree(tmpdir)
            finally:
                shutil.rmtree(tmpfixture)
            continue

        elif fixture_name == "tools-dir-repo":
            # Create a temporary copy of the clean fixture and add skills/arch-index/scripts to it
            env.pop("ARCH_INDEX_SCRIPTS", None)
            real_scripts = os.path.expanduser("~/.claude/skills/arch-index/scripts")
            if not os.path.isdir(real_scripts):
                print(f"SKIP  {fixture_name:20s} -> real scripts not found")
                continue

            clean_fixture = os.path.join(build_dir, "clean")
            if not os.path.isdir(clean_fixture):
                print(f"FAIL  {fixture_name:20s} -> clean fixture missing")
                all_pass = False
                continue

            tmpfixture = tempfile.mkdtemp()
            try:
                # Copy the clean fixture into tmpfixture
                shutil.copytree(clean_fixture, os.path.join(tmpfixture, "repo"))
                fixture_with_scripts = os.path.join(tmpfixture, "repo")

                # Create skills/arch-index/scripts in the fixture
                scripts_dest = os.path.join(fixture_with_scripts, "skills", "arch-index", "scripts")
                os.makedirs(scripts_dest, exist_ok=True)
                for script in ["validate_index.py", "arch_drift.py", "verify_arch_plan.py"]:
                    src = os.path.join(real_scripts, script)
                    dst = os.path.join(scripts_dest, script)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)

                # Run with the fixture that has repo scripts
                proc = subprocess.run(
                    [sys.executable, __file__, "--repo-root", fixture_with_scripts],
                    capture_output=True,
                    text=True,
                    env=env
                )
                exit_code = proc.returncode
                stderr = proc.stderr

                expected_code = expected.get(fixture_name, 0)
                passed = exit_code == expected_code
                print(f"  {'PASS' if passed else 'FAIL'}  {fixture_name:20s} exit={exit_code} (expect {expected_code})")

                # Check that tools_dir points to repo scripts
                if passed:
                    try:
                        gate_file = os.path.join(fixture_with_scripts, ".arch", "ARCH-GATE.json")
                        if os.path.isfile(gate_file):
                            with open(gate_file) as fh:
                                gate_data = json.load(fh)
                            expected_tools_dir = os.path.join(fixture_with_scripts, "skills", "arch-index", "scripts")
                            if "tools_dir" not in gate_data or gate_data["tools_dir"] != expected_tools_dir:
                                print(f"    WARNING: tools_dir not correctly recorded", file=sys.stderr)
                                all_pass = False
                    except Exception:
                        pass

                if not passed:
                    all_pass = False
            finally:
                shutil.rmtree(tmpfixture)
            continue

        elif fixture_name == "tools-dir-env-missing":
            # Copy clean fixture to temp and run with empty ARCH_INDEX_SCRIPTS
            clean_fixture = os.path.join(build_dir, "clean")
            if not os.path.isdir(clean_fixture):
                print(f"FAIL  {fixture_name:20s} -> clean fixture missing")
                all_pass = False
                continue

            tmpfixture = tempfile.mkdtemp()
            try:
                # Copy the clean fixture into tmpfixture
                shutil.copytree(clean_fixture, os.path.join(tmpfixture, "repo"))
                fixture_root = os.path.join(tmpfixture, "repo")

                tmpdir = tempfile.mkdtemp()
                try:
                    env["ARCH_INDEX_SCRIPTS"] = tmpdir
                    proc = subprocess.run(
                        [sys.executable, __file__, "--repo-root", fixture_root],
                        capture_output=True,
                        text=True,
                        env=env
                    )
                    exit_code = proc.returncode
                    stderr = proc.stderr

                    expected_code = expected.get(fixture_name, 0)
                    passed = exit_code == expected_code
                    print(f"  {'PASS' if passed else 'FAIL'}  {fixture_name:20s} exit={exit_code} (expect {expected_code})")

                    # Check stderr contains "arch-index scripts not found"
                    if passed and "arch-index scripts not found" not in stderr:
                        print(f"    WARNING: expected error message not in stderr", file=sys.stderr)
                        all_pass = False

                    if not passed:
                        all_pass = False
                finally:
                    shutil.rmtree(tmpdir)
            finally:
                shutil.rmtree(tmpfixture)
            continue

        # Standard fixtures - run on temporary copy
        tmpfixture = tempfile.mkdtemp()
        try:
            shutil.copytree(source_fixture, os.path.join(tmpfixture, "fixture"))
            fixture_root = os.path.join(tmpfixture, "fixture")

            # Run as subprocess
            proc = subprocess.run(
                [sys.executable, __file__, "--repo-root", fixture_root],
                capture_output=True,
                text=True,
                env=env
            )
            exit_code = proc.returncode
            stderr = proc.stderr

            expected_code = expected.get(fixture_name, 0)
            passed = exit_code == expected_code
            print(f"  {'PASS' if passed else 'FAIL'}  {fixture_name:20s} exit={exit_code} (expect {expected_code})")

            # For remove-verdict, assert REMOVE is mentioned in stderr
            if fixture_name == "remove-verdict" and passed:
                if "REMOVE" not in stderr:
                    print(f"    WARNING: REMOVE not in stderr output", file=sys.stderr)
                    all_pass = False

            if not passed:
                all_pass = False
        finally:
            shutil.rmtree(tmpfixture)

    print()
    print(f"{len(fixtures)} fixture(s): {'all pass' if all_pass else 'SOME FAILED'}")

    ra_all_pass = _self_test_run_aware()
    all_pass = all_pass and ra_all_pass

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
