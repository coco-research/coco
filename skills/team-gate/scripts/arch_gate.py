#!/usr/bin/env python3
"""Gate architecture conformance by invoking validate_index.py and arch_drift.py.

Exits 0 when conformance passes, 1 when a block exists, 2 when unrunnable or
unverified.

Pass rules (from commands/team/architecture.md lines 93-117):
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

Exit codes: 0 pass, 1 block, 2 unrunnable or unverified.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def resolve_tools_dir(repo_root):
    """Resolve the arch-index scripts directory.

    Returns a tuple (tools_dir, error_reason). On success, tools_dir is set and
    error_reason is None. On failure, tools_dir is None and error_reason contains
    the reason string.

    Resolution order:
    1. ARCH_INDEX_SCRIPTS environment variable (must exist and contain both scripts)
    2. <repo_root>/skills/arch-index/scripts (if it contains both scripts)
    3. ~/.claude/skills/arch-index/scripts

    Args:
        repo_root: The repository root path

    Returns:
        Tuple of (tools_dir, error_reason). Either tools_dir or error_reason is None.
    """
    required_scripts = ["validate_index.py", "arch_drift.py"]

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


def main():
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
                    # Copy both scripts
                    for script in ["validate_index.py", "arch_drift.py"]:
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
                for script in ["validate_index.py", "arch_drift.py"]:
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
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
