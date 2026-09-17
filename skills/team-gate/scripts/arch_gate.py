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
  {gate, exit, removes, prunes, validate_exit, drift_exit, pin, head, reason}

Usage:
    python3 arch_gate.py --repo-root .
    python3 arch_gate.py --repo-root . --index .arch/index.json --out .arch/ARCH-GATE.json
    python3 arch_gate.py --self-test

Exit codes: 0 pass, 1 block, 2 unrunnable or unverified.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd, cwd):
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError as exc:
        return 2, "", f"command not found: {exc}"
    except Exception as exc:
        return 2, "", f"subprocess error: {exc}"


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
        }
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as fh:
            json.dump(result, fh, indent=2)
        return 2

    # Run validate_index.py
    validate_script = os.path.join(
        os.path.dirname(__file__), "..", "..", "arch-index", "scripts", "validate_index.py"
    )
    validate_exit, _, _ = run_command(
        ["python3", validate_script, index_path, "--repo-root", root, "--quiet"],
        cwd=root,
    )

    # Run arch_drift.py with temp output file
    drift_script = os.path.join(
        os.path.dirname(__file__), "..", "..", "arch-index", "scripts", "arch_drift.py"
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        drift_exit, _, _ = run_command(
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

        # Apply pass rules
        exit_code = 0
        reason = ""

        if validate_exit != 0:
            exit_code = 1
            reason = f"validate_index.py failed (exit {validate_exit})"
        elif drift_exit != 0:
            exit_code = 2
            reason = f"arch_drift.py failed to run (exit {drift_exit})"
        elif removes:
            exit_code = 1
            reason = f"BLOCK: {len(removes)} component(s) with REMOVE verdict"
        elif prunes:
            # PRUNE only: pass but print MAJOR line
            print(f"MAJOR: PRUNE {' '.join(prunes)}")

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
    """Run all fixtures and assert exact exit codes."""
    test_dir = os.path.join(os.path.dirname(__file__), "fixtures", "arch_gate")
    if not os.path.isdir(test_dir):
        print("FAIL: fixtures directory does not exist", file=sys.stderr)
        return 1

    fixtures = ["remove-verdict", "prune-verdict", "clean", "stale-pin"]
    all_pass = True

    for fixture_name in fixtures:
        fixture_root = os.path.join(test_dir, fixture_name)
        if not os.path.isdir(fixture_root):
            print(f"FAIL  {fixture_name:20s} -> fixture directory missing")
            all_pass = False
            continue

        # Expected exit codes per fixture
        expected = {
            "remove-verdict": 1,
            "prune-verdict": 0,
            "clean": 0,
            "stale-pin": 2,
        }

        # Run the gate
        exit_code = main.__code__.co_consts  # dummy, we need to call main with args

        # Simulate argparse for this test
        old_argv = sys.argv
        try:
            sys.argv = ["arch_gate.py", "--repo-root", fixture_root]
            exit_code = main()
        except SystemExit as exc:
            exit_code = exc.code or 0
        finally:
            sys.argv = old_argv

        expected_code = expected.get(fixture_name, 0)
        passed = exit_code == expected_code
        print(f"  {'PASS' if passed else 'FAIL'}  {fixture_name:20s} exit={exit_code} (expect {expected_code})")
        if not passed:
            all_pass = False

    print()
    print(f"{len(fixtures)} fixture(s): {'all pass' if all_pass else 'SOME FAILED'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
