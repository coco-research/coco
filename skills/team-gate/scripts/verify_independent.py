#!/usr/bin/env python3
"""Verify Stage 11: Independent verification via clean git worktree.

Exit contract: 0 = pass, 1 = block (independence failed), 2 = unrunnable (git unavailable, state unreadable).

Subcommands:
  setup: creates a detached git worktree at HEAD, asserts .team-ship/ is absent,
         registers the worktree, and prints the path and claude -p invocation.
  compare <builder-gate-json> <verifier-gate-json>: compares builder and verifier
         gate results (exit, passed, skipped, failed). Any difference is exit 1.
  teardown: removes the worktree and appends a receipt.
"""

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Union

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_state


def verify_prompt(run_gate_abs: str) -> str:
    """Return the verifier prompt with run_gate path substituted."""
    return f"""You are the independent verifier for Stage 11. You are in a clean git worktree at the commit under review. Do not read .team-ship/EVIDENCE.md, .team-ship/EVIDENCE.json, any REVIEW-*.md, or any builder claim. Read .team-ship/PLAN.md for the requirements. Run these three commands in order and report only their three exit codes, one per line, nothing else: `python3 {run_gate_abs} --repo-root . --role verifier discover`; `python3 {run_gate_abs} --repo-root . --role verifier run`; `python3 {run_gate_abs} --repo-root . --role verifier coverage`. The --role verifier flag makes run_gate write gates/<n>-verifier.json in the run directory instead of gates/<n>.json. Do not compare anything; verify_independent.py compare performs the comparison."""


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


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cmd_setup(repo_root: str, model: str) -> int:
    """Setup: create worktree, assert .team-ship/ absent, register, print invocation."""
    repo_path = Path(repo_root).resolve()

    # Resolve git top level (supports subdirectory as repo_root)
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        git_top = Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        print(f"ERROR: not a git repository: {repo_path}", file=sys.stderr)
        return 2

    # Walk up from repo_path to find .team-ship/RUN, record directory where found
    current = repo_path
    run_dir = None
    run_id = None
    run_pointer_dir = None
    while current != current.parent:
        marker = current / ".team-ship" / "RUN"
        if marker.is_file():
            try:
                run_id = marker.read_text(encoding="utf-8").strip()
                if run_id:
                    run_dir = state_root() / run_id
                    if run_dir.is_dir():
                        run_pointer_dir = current
                        break
            except Exception:
                pass
        current = current.parent

    if not run_dir or not run_id:
        print(f"ERROR: .team-ship/RUN not present under {repo_path} or its parents", file=sys.stderr)
        return 2

    if not run_dir.is_dir():
        print(f"ERROR: run directory {run_dir} not found under state root {state_root()}", file=sys.stderr)
        return 2

    # Verify run pointer directory belongs to the same git repository
    if run_pointer_dir and os.path.realpath(run_pointer_dir) != os.path.realpath(git_top):
        print(f"ERROR: run pointer at {run_pointer_dir} does not belong to repository {git_top}", file=sys.stderr)
        return 2

    # Get HEAD sha
    try:
        result = subprocess.run(
            ["git", "-C", str(git_top), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        head_sha = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        stderr_line = e.stderr.strip().split('\n')[-1] if e.stderr else "failed to get HEAD"
        print(f"ERROR: {stderr_line}", file=sys.stderr)
        return 2

    # Compute tree digest
    try:
        result = subprocess.run(
            ["git", "-C", str(git_top), "rev-parse", "HEAD^{tree}"],
            capture_output=True, text=True, check=True
        )
        tree_digest = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        stderr_line = e.stderr.strip().split('\n')[-1] if e.stderr else "failed to get tree digest"
        print(f"ERROR: {stderr_line}", file=sys.stderr)
        return 2

    # Prepare worktree path
    verify_wt_dir = run_dir / "verify-wt"
    removed_stale = []

    # Check if target path exists (stale worktree) - remove it
    if verify_wt_dir.exists():
        # Check if it's a registered git worktree
        is_registered = False
        try:
            result = subprocess.run(
                ["git", "-C", str(git_top), "worktree", "list", "--porcelain"],
                capture_output=True, text=True, check=True
            )
            verify_wt_realpath = os.path.realpath(str(verify_wt_dir))
            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue
                # Parse "worktree /path" format
                if line.startswith("worktree "):
                    worktree_path = line[len("worktree "):].strip()
                    if os.path.realpath(worktree_path) == verify_wt_realpath:
                        is_registered = True
                        break
        except Exception:
            pass

        if is_registered:
            # It's a registered worktree, remove it
            try:
                subprocess.run(
                    ["git", "-C", str(git_top), "worktree", "remove", "--force", str(verify_wt_dir)],
                    capture_output=True, check=True
                )
                removed_stale.append("registered worktree")
            except subprocess.CalledProcessError:
                shutil.rmtree(verify_wt_dir, ignore_errors=True)
                removed_stale.append("stale directory (removal failed)")
        else:
            # Not a registered worktree, just a directory
            shutil.rmtree(verify_wt_dir, ignore_errors=True)
            removed_stale.append("stale directory")

        # Prune after removal
        subprocess.run(
            ["git", "-C", str(git_top), "worktree", "prune"],
            capture_output=True, check=False
        )

    # Create fresh worktree at verify-wt/
    try:
        subprocess.run(
            ["git", "-C", str(git_top), "worktree", "add", "--detach", str(verify_wt_dir), "HEAD"],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        stderr_line = e.stderr.strip().split('\n')[-1] if e.stderr else "failed to create worktree"
        print(f"ERROR: {stderr_line}", file=sys.stderr)
        return 2

    # Check for tracked files in .team-ship/ (except RUN which we're about to write)
    team_ship_in_wt = verify_wt_dir / ".team-ship"
    if team_ship_in_wt.exists():
        try:
            result = subprocess.run(
                ["git", "-C", str(git_top), "ls-files", "--", ".team-ship"],
                capture_output=True, text=True, check=True
            )
            tracked_files = [f for f in result.stdout.strip().split('\n') if f and f != ".team-ship/RUN"]
        except Exception:
            tracked_files = []

        if tracked_files:
            reason = ".team-ship/ exists in worktree with tracked files (must be clean)"
            print(f"ERROR: {reason}", file=sys.stderr)
            for tracked_file in tracked_files:
                if tracked_file:
                    print(tracked_file, file=sys.stderr)

            # Clean up the worktree
            try:
                subprocess.run(
                    ["git", "-C", str(git_top), "worktree", "remove", "--force", str(verify_wt_dir)],
                    capture_output=True, check=False
                )
            except Exception:
                pass
            return 1

    # Write .team-ship/RUN pointer in the worktree
    team_ship_in_wt.mkdir(parents=True, exist_ok=True)
    run_pointer = team_ship_in_wt / "RUN"
    run_dir_name = run_dir.name
    run_pointer.write_text(run_dir_name, encoding="utf-8")

    # Register worktree in worktrees.json
    worktrees_file = run_dir / "worktrees.json"
    worktrees = {}
    if worktrees_file.exists():
        try:
            worktrees = json.loads(worktrees_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    worktree_entry = {
        "path": str(verify_wt_dir),
        "head": head_sha,
        "treeDigest": tree_digest
    }
    worktrees["verify-wt"] = worktree_entry

    worktrees_file.write_text(json.dumps(worktrees, indent=2), encoding="utf-8")

    # Append worktree-registered receipt
    run_gate_abs = str(Path(__file__).resolve().parent / "run_gate.py")
    try:
        gate_state.append_receipt(
            run_dir,
            "worktree-registered",
            {
                "path": str(verify_wt_dir),
                "head": head_sha,
                "treeDigest": tree_digest,
                "type": "verify",
                "removed_stale": removed_stale if removed_stale else None,
                "pointer_written": True
            }
        )
    except Exception as e:
        print(f"ERROR: Failed to append receipt: {e}", file=sys.stderr)
        return 2

    # Print path
    print(str(verify_wt_dir))

    # Print pointer_written flag
    print("pointer_written=true")

    # Print exact claude -p invocation with verify_prompt function
    prompt_text = verify_prompt(run_gate_abs)
    invocation = (
        f"cd {shlex.quote(str(verify_wt_dir))} && "
        f"env -u ANTHROPIC_BASE_URL -u ANTHROPIC_AUTH_TOKEN -u ANTHROPIC_MODEL -u ANTHROPIC_SMALL_FAST_MODEL "
        f"claude -p {shlex.quote(prompt_text)} "
        f"--model {shlex.quote(model)} "
        f"--strict-mcp-config "
        f"--mcp-config {shlex.quote(json.dumps({'mcpServers': {}}))} "
        f"--allowedTools Bash,Read,Grep,Glob"
    )
    print(invocation)

    return 0


def cmd_compare(builder_gate: Optional[str], verifier_gate: Optional[str], repo_root: str) -> int:
    """Compare builder and verifier gate results. Arguments default to run_dir/gates/8.json and 8-verifier.json."""
    repo_path = Path(repo_root).resolve()

    # Resolve git top level
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        git_top = Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        print(f"ERROR: not a git repository: {repo_path}", file=sys.stderr)
        return 2

    # Walk up from repo_path to find .team-ship/RUN, record directory where found
    current = repo_path
    run_dir = None
    run_id = None
    run_pointer_dir = None
    while current != current.parent:
        marker = current / ".team-ship" / "RUN"
        if marker.is_file():
            try:
                run_id = marker.read_text(encoding="utf-8").strip()
                if run_id:
                    run_dir = state_root() / run_id
                    if run_dir.is_dir():
                        run_pointer_dir = current
                        break
            except Exception:
                pass
        current = current.parent

    if not run_dir or not run_id:
        print("ERROR: run directory not found", file=sys.stderr)
        return 2

    # Verify run pointer directory belongs to the same git repository
    if run_pointer_dir and os.path.realpath(run_pointer_dir) != os.path.realpath(git_top):
        print(f"ERROR: run pointer at {run_pointer_dir} does not belong to repository {git_top}", file=sys.stderr)
        return 2

    # Default to gates/8.json and gates/8-verifier.json if not provided
    if not builder_gate:
        builder_gate = str(run_dir / "gates" / "8.json")
    if not verifier_gate:
        verifier_gate = str(run_dir / "gates" / "8-verifier.json")

    # Print which files were compared on stderr
    print(f"Comparing {builder_gate} and {verifier_gate}", file=sys.stderr)

    # Get current HEAD
    try:
        result = subprocess.run(
            ["git", "-C", str(git_top), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        head_sha = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        stderr_line = e.stderr.strip().split('\n')[-1] if e.stderr else "failed to get HEAD"
        print(f"ERROR: {stderr_line}", file=sys.stderr)
        return 2

    # Read both gate files
    try:
        builder_data = json.loads(Path(builder_gate).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: Failed to read builder gate {builder_gate}: {e}", file=sys.stderr)
        return 2

    try:
        verifier_data = json.loads(Path(verifier_gate).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: Failed to read verifier gate {verifier_gate}: {e}", file=sys.stderr)
        return 2

    # Check head values exist
    builder_head = builder_data.get("head")
    verifier_head = verifier_data.get("head")

    if builder_head is None:
        print(f"ERROR: gate file {builder_gate} has no head", file=sys.stderr)
        return 2

    if verifier_head is None:
        print(f"ERROR: gate file {verifier_gate} has no head", file=sys.stderr)
        return 2

    # Compare head values first
    if builder_head != verifier_head:
        print(f"ERROR: head mismatch: builder {builder_head} verifier {verifier_head}", file=sys.stderr)
        return 1

    # Extract fields to compare (gates/8.json-shaped)
    builder_exit = builder_data.get("exit")
    verifier_exit = verifier_data.get("exit")

    builder_parsed = builder_data.get("parsed", {})
    verifier_parsed = verifier_data.get("parsed", {})

    builder_passed = builder_parsed.get("passed")
    verifier_passed = verifier_parsed.get("passed")

    builder_skipped = builder_parsed.get("skipped")
    verifier_skipped = verifier_parsed.get("skipped")

    builder_failed = builder_parsed.get("failed")
    verifier_failed = verifier_parsed.get("failed")

    # Compare
    exit_code = 0
    mismatches = []

    if builder_exit != verifier_exit:
        mismatches.append(f"exit: builder={builder_exit}, verifier={verifier_exit}")
        exit_code = 1

    if builder_passed != verifier_passed:
        mismatches.append(f"passed: builder={builder_passed}, verifier={verifier_passed}")
        exit_code = 1

    if builder_skipped != verifier_skipped:
        mismatches.append(f"skipped: builder={builder_skipped}, verifier={verifier_skipped}")
        exit_code = 1

    if builder_failed != verifier_failed:
        mismatches.append(f"failed: builder={builder_failed}, verifier={verifier_failed}")
        exit_code = 1

    # Write comparison result
    comparison = {
        "argv": [sys.executable, __file__, "compare", builder_gate, verifier_gate],
        "cwd": str(repo_path),
        "head": head_sha,
        "exit": exit_code,
        "summary": f"{'PASS' if exit_code == 0 else 'BLOCK'}: compare builder vs verifier gate",
        "builder_exit": builder_exit,
        "verifier_exit": verifier_exit,
        "builder_passed": builder_passed,
        "verifier_passed": verifier_passed,
        "builder_skipped": builder_skipped,
        "verifier_skipped": verifier_skipped,
        "builder_failed": builder_failed,
        "verifier_failed": verifier_failed,
        "mismatches": mismatches
    }

    gates_dir = run_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    gate_file_path = gates_dir / "11.json"

    gate_file_path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    gate_sha256 = _sha256_file(gate_file_path)

    # Append receipt
    try:
        gate_state.append_receipt(
            run_dir,
            "gate-result",
            {
                "gate": "verify-independent-compare",
                "gate_file": "gates/11.json",
                "gate_sha256": gate_sha256,
                "exit": exit_code,
                "summary": comparison["summary"]
            }
        )
    except Exception as e:
        print(f"ERROR: Failed to append receipt: {e}", file=sys.stderr)
        return 2

    if mismatches:
        for mismatch in mismatches:
            print(f"ERROR: {mismatch}", file=sys.stderr)

    return exit_code


def cmd_teardown(repo_root: str) -> int:
    """Teardown: remove worktree and append receipt."""
    repo_path = Path(repo_root).resolve()

    # Resolve git top level
    git_top = None
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        git_top = Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        pass  # Not fatal for teardown

    # Walk up from repo_path to find .team-ship/RUN, record directory where found
    current = repo_path
    run_dir = None
    run_id = None
    run_pointer_dir = None
    while current != current.parent:
        marker = current / ".team-ship" / "RUN"
        if marker.is_file():
            try:
                run_id = marker.read_text(encoding="utf-8").strip()
                if run_id:
                    run_dir = state_root() / run_id
                    if run_dir.is_dir():
                        run_pointer_dir = current
                        break
            except Exception:
                pass
        current = current.parent

    if not run_dir or not run_id:
        print("ERROR: run directory not found", file=sys.stderr)
        return 2

    # Verify run pointer directory belongs to the same git repository (if git_top was resolved)
    if git_top and run_pointer_dir and os.path.realpath(run_pointer_dir) != os.path.realpath(git_top):
        print(f"ERROR: run pointer at {run_pointer_dir} does not belong to repository {git_top}", file=sys.stderr)
        return 2

    # Read worktrees.json to get the worktree path
    worktrees_file = run_dir / "worktrees.json"
    if not worktrees_file.exists():
        print("ERROR: cannot read worktrees.json: No such file or directory", file=sys.stderr)
        return 2

    try:
        worktrees = json.loads(worktrees_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: cannot read {worktrees_file}: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"ERROR: cannot read {worktrees_file}: {e}", file=sys.stderr)
        return 2

    verify_wt_entry = worktrees.get("verify-wt")
    if not verify_wt_entry:
        print("ERROR: verify-wt not found in worktrees.json", file=sys.stderr)
        return 2

    verify_wt_path = Path(verify_wt_entry["path"])

    # Remove the worktree
    if 'git_top' in locals():
        try:
            subprocess.run(
                ["git", "-C", str(git_top), "worktree", "remove", "--force", str(verify_wt_path)],
                capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            # Don't fail on cleanup issues
            pass

    # Append teardown receipt
    try:
        gate_state.append_receipt(
            run_dir,
            "gate-result",
            {
                "gate": "verify-independent-teardown",
                "gate_file": None,
                "gate_sha256": None,
                "exit": 0,
                "summary": "PASS: worktree removed"
            }
        )
    except Exception as e:
        print(f"ERROR: Failed to append receipt: {e}", file=sys.stderr)
        return 2

    return 0


def cmd_self_test() -> int:
    """Run self-tests on all fixtures."""
    fixture_dir = Path(__file__).parent / "fixtures" / "verify_independent"

    # Delete every _build and regenerate fixtures
    if fixture_dir.exists():
        for build_dir in fixture_dir.glob("*/_build"):
            shutil.rmtree(build_dir, ignore_errors=True)

    # Generate fixtures via make_fixtures.py
    make_fixtures_file = fixture_dir / "make_fixtures.py"
    if make_fixtures_file.exists():
        result = subprocess.run(
            [sys.executable, str(make_fixtures_file)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"ERROR: Failed to generate fixtures: {result.stderr}", file=sys.stderr)
            return 2

    # Test cases: (name, subcommand, expected_exit, stderr_contains_list)
    tests = [
        ("clean-worktree-ok", "setup", 0, []),
        ("team-ship-tracked", "setup", 1, [".team-ship/EVIDENCE.md"]),
        ("gate-mismatch", "compare", 1, ["passed"]),
        ("head-mismatch", "compare", 1, ["head mismatch"]),
        ("not-a-git-repo", "setup", 2, ["not a git repository"]),
        ("stale-verify-wt", "setup", 0, []),
        ("subdir-repo-root", "setup", 0, []),
        ("compare-defaults", "compare", 0, ["8-verifier.json"]),
        ("nested-unrelated-repo", "setup", 2, ["does not belong"]),
    ]

    all_pass = True

    for test_name, subcommand, expected_exit, stderr_contains_list in tests:
        fixture_path = fixture_dir / test_name / "_build"

        if not fixture_path.exists():
            if test_name in ("subdir-repo-root", "compare-defaults", "nested-unrelated-repo"):
                # Create these fixtures on the fly from clean-worktree-ok
                base_fixture = fixture_dir / "clean-worktree-ok" / "_build"
                if not base_fixture.exists():
                    print(f"{test_name}: FAIL - base fixture not found", file=sys.stderr)
                    all_pass = False
                    continue
                fixture_path = base_fixture
            else:
                print(f"{test_name}: FIXTURE NOT FOUND", file=sys.stderr)
                all_pass = False
                continue

        # Create temporary TEAM_STATE_ROOT
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_state_root = Path(tmpdir)
            os.environ["TEAM_STATE_ROOT"] = str(temp_state_root)

            # Copy fixture to tmpdir
            isolated_fixture = Path(tmpdir) / "isolated-fixture"
            shutil.copytree(fixture_path, isolated_fixture)
            fixture_copy = isolated_fixture

            # Initialize run state
            try:
                run_id = gate_state.start_run(str(fixture_copy), "verify", [])
            except Exception as e:
                print(f"{test_name}: FAIL - failed to start run: {e}", file=sys.stderr)
                all_pass = False
                continue

            # For stale-verify-wt test, create a verify-wt directory beforehand
            if test_name == "stale-verify-wt":
                run_dir = temp_state_root / run_id
                stale_wt = run_dir / "verify-wt"
                stale_wt.mkdir(parents=True)
                (stale_wt / "stale.txt").write_text("stale")

            # For nested-unrelated-repo test, create a nested git repo
            if test_name == "nested-unrelated-repo":
                nested_dir = fixture_copy / "nested-unrelated"
                nested_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(["git", "init", "-q"], cwd=nested_dir, capture_output=True, check=False)
                subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=nested_dir, capture_output=True, check=False)
                subprocess.run(["git", "config", "user.name", "Test"], cwd=nested_dir, capture_output=True, check=False)
                (nested_dir / "nested.txt").write_text("nested")
                subprocess.run(["git", "add", "nested.txt"], cwd=nested_dir, capture_output=True, check=False)
                subprocess.run(["git", "commit", "-m", "nested"], cwd=nested_dir, capture_output=True, check=False)

            # Run the CLI
            try:
                if subcommand == "setup":
                    if test_name == "subdir-repo-root":
                        # Test with subdirectory
                        subdir = fixture_copy / "sub" / "deeper"
                        subdir.mkdir(parents=True, exist_ok=True)
                        repo_root_arg = str(subdir)
                    elif test_name == "nested-unrelated-repo":
                        # Test with nested unrelated repo
                        repo_root_arg = str(fixture_copy / "nested-unrelated")
                    else:
                        repo_root_arg = str(fixture_copy)

                    result = subprocess.run(
                        [sys.executable, __file__, "setup", "--repo-root", repo_root_arg],
                        capture_output=True, text=True, timeout=30, cwd=str(fixture_copy)
                    )
                elif subcommand == "compare":
                    run_dir = temp_state_root / run_id
                    gates_dir = run_dir / "gates"
                    gates_dir.mkdir(parents=True, exist_ok=True)

                    if test_name == "gate-mismatch":
                        builder_data = {
                            "head": "abc123def456",
                            "exit": 0,
                            "parsed": {"passed": 10, "skipped": 0, "failed": 0}
                        }
                        verifier_data = {
                            "head": "abc123def456",
                            "exit": 1,
                            "parsed": {"passed": 9, "skipped": 1, "failed": 0}
                        }
                        builder_gate_path = gates_dir / "8.json"
                        verifier_gate_path = gates_dir / "8-verifier.json"
                        builder_gate_path.write_text(json.dumps(builder_data))
                        verifier_gate_path.write_text(json.dumps(verifier_data))
                        result = subprocess.run(
                            [sys.executable, __file__, "compare",
                             str(builder_gate_path), str(verifier_gate_path),
                             "--repo-root", str(fixture_copy)],
                            capture_output=True, text=True, timeout=30, cwd=str(fixture_copy)
                        )
                    elif test_name == "head-mismatch":
                        builder_data = {
                            "head": "abc123def456",
                            "exit": 0,
                            "parsed": {"passed": 10, "skipped": 0, "failed": 0}
                        }
                        verifier_data = {
                            "head": "xyz789uvw012",
                            "exit": 0,
                            "parsed": {"passed": 10, "skipped": 0, "failed": 0}
                        }
                        builder_gate_path = gates_dir / "8.json"
                        verifier_gate_path = gates_dir / "8-verifier.json"
                        builder_gate_path.write_text(json.dumps(builder_data))
                        verifier_gate_path.write_text(json.dumps(verifier_data))
                        result = subprocess.run(
                            [sys.executable, __file__, "compare",
                             str(builder_gate_path), str(verifier_gate_path),
                             "--repo-root", str(fixture_copy)],
                            capture_output=True, text=True, timeout=30, cwd=str(fixture_copy)
                        )
                    elif test_name == "compare-defaults":
                        # Write gates/8.json and gates/8-verifier.json with identical data
                        identical_data = {
                            "head": "abc123def456",
                            "exit": 0,
                            "parsed": {"passed": 10, "skipped": 0, "failed": 0}
                        }
                        (gates_dir / "8.json").write_text(json.dumps(identical_data))
                        (gates_dir / "8-verifier.json").write_text(json.dumps(identical_data))
                        # Call compare without positional arguments
                        result = subprocess.run(
                            [sys.executable, __file__, "compare", "--repo-root", str(fixture_copy)],
                            capture_output=True, text=True, timeout=30, cwd=str(fixture_copy)
                        )
                    else:
                        result = subprocess.run(
                            [sys.executable, __file__, "compare", "--repo-root", str(fixture_copy)],
                            capture_output=True, text=True, timeout=30, cwd=str(fixture_copy)
                        )
                else:
                    result = subprocess.run(
                        [sys.executable, __file__, subcommand],
                        capture_output=True, text=True, timeout=30, cwd=str(fixture_copy)
                    )
            except subprocess.TimeoutExpired:
                print(f"{test_name}: FAIL - timeout", file=sys.stderr)
                all_pass = False
                continue
            except Exception as e:
                print(f"{test_name}: FAIL - {e}", file=sys.stderr)
                all_pass = False
                continue

            # Check exit code
            if result.returncode != expected_exit:
                print(f"{test_name}: expected {expected_exit} got {result.returncode} FAIL", file=sys.stderr)
                all_pass = False
                continue

            # Check stderr contains expected strings
            stderr_check = True
            for check_str in stderr_contains_list:
                if check_str not in result.stderr:
                    stderr_check = False
                    break

            if stderr_check:
                status = "OK"
                if stderr_contains_list:
                    stderr_note = f" stderr contains '{stderr_contains_list[0]}'"
                else:
                    stderr_note = ""
                print(f"{test_name}: expected {expected_exit} got {expected_exit} {status}{stderr_note}")
            else:
                print(f"{test_name}: expected {expected_exit} got {expected_exit} FAIL (stderr check failed)", file=sys.stderr)
                print(f"  expected: {stderr_contains_list}", file=sys.stderr)
                print(f"  got: {result.stderr}", file=sys.stderr)
                all_pass = False

            # For setup tests that succeed, clean up verify-wt before checking
            if subcommand == "setup" and result.returncode == 0:
                try:
                    verify_wt_line = None
                    wt_list_result = subprocess.run(
                        ["git", "-C", str(fixture_copy), "worktree", "list", "--porcelain"],
                        capture_output=True, text=True, timeout=10
                    )
                    for line in wt_list_result.stdout.strip().split('\n'):
                        if line.startswith("worktree ") and "verify-wt" in line:
                            verify_wt_line = line
                            break

                    if verify_wt_line:
                        verify_wt_path = verify_wt_line.split()[1]
                        subprocess.run(
                            ["git", "-C", str(fixture_copy), "worktree", "remove", "--force", verify_wt_path],
                            capture_output=True, text=True, timeout=10
                        )
                except Exception:
                    pass

            # Check worktree list for this fixture (skip if not a git repo)
            if test_name != "not-a-git-repo":
                try:
                    result_wt = subprocess.run(
                        ["git", "-C", str(fixture_copy), "worktree", "list", "--porcelain"],
                        capture_output=True, text=True, timeout=10
                    )
                    worktree_lines = [l for l in result_wt.stdout.strip().split('\n') if l.startswith("worktree ")]
                    if len(worktree_lines) == 1:
                        print(f"{test_name}: worktrees=1 OK")
                    else:
                        print(f"{test_name}: FAIL - expected 1 worktree, got {len(worktree_lines)}", file=sys.stderr)
                        all_pass = False
                except Exception as e:
                    print(f"{test_name}: FAIL - worktree list check: {e}", file=sys.stderr)
                    all_pass = False

    return 0 if all_pass else 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="sonnet", help="Claude model to use")
    parser.add_argument("--self-test", action="store_true", help="Run self-tests")

    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # setup subcommand
    setup_parser = subparsers.add_parser("setup", help="Setup worktree")
    setup_parser.add_argument("--repo-root", default=".", help="Repository root")
    setup_parser.add_argument("--model", default="sonnet", help="Claude model to use")

    # compare subcommand
    compare_parser = subparsers.add_parser("compare", help="Compare gate results")
    compare_parser.add_argument("builder_gate", nargs="?", default=None, help="Builder gate JSON file (default: <run_dir>/gates/8.json)")
    compare_parser.add_argument("verifier_gate", nargs="?", default=None, help="Verifier gate JSON file (default: <run_dir>/gates/8-verifier.json)")
    compare_parser.add_argument("--repo-root", default=".", help="Repository root")

    # teardown subcommand
    teardown_parser = subparsers.add_parser("teardown", help="Teardown worktree")
    teardown_parser.add_argument("--repo-root", default=".", help="Repository root")

    args = parser.parse_args()

    if args.self_test:
        return cmd_self_test()

    if args.command == "setup":
        model = args.model if hasattr(args, 'model') else "sonnet"
        return cmd_setup(args.repo_root, model)
    elif args.command == "compare":
        return cmd_compare(args.builder_gate, args.verifier_gate, args.repo_root)
    elif args.command == "teardown":
        return cmd_teardown(args.repo_root)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
