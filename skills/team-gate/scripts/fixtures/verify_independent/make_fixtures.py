#!/usr/bin/env python3
"""Generate test fixtures for verify_independent.py."""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


def make_clean_worktree_ok(output_root: Path) -> None:
    """Fixture: clean worktree with no .team-ship/ tracked (exit 0)."""
    fixture_dir = output_root / "clean-worktree-ok"
    fixture_dir.mkdir(exist_ok=True)

    build_dir = fixture_dir / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    # Set git environment for deterministic commits
    git_env = os.environ.copy()
    fixed_ts = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
    git_env.update({
        "GIT_AUTHOR_DATE": fixed_ts,
        "GIT_COMMITTER_DATE": fixed_ts,
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    })

    # Initialize a minimal git repo with one commit
    subprocess.run(["git", "init"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=build_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=build_dir, capture_output=True, check=True)

    # Create a file and commit
    (build_dir / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=build_dir, capture_output=True, check=True, env=git_env)

    # Create .team-ship directory but do NOT track it (ensure .gitignore exists)
    (build_dir / ".gitignore").write_text(".team-ship/\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "commit", "-m", "Add gitignore"], cwd=build_dir, capture_output=True, check=True, env=git_env)

    # Create the test metadata
    metadata = {
        "name": "clean-worktree-ok",
        "expected_exit": 0,
        "description": "Clean worktree with .team-ship/ gitignored"
    }
    (fixture_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


def make_team_ship_tracked(output_root: Path) -> None:
    """Fixture: .team-ship/ tracked in git (exit 1)."""
    fixture_dir = output_root / "team-ship-tracked"
    fixture_dir.mkdir(exist_ok=True)

    build_dir = fixture_dir / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    # Set git environment for deterministic commits
    git_env = os.environ.copy()
    fixed_ts = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
    git_env.update({
        "GIT_AUTHOR_DATE": fixed_ts,
        "GIT_COMMITTER_DATE": fixed_ts,
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    })

    # Initialize a minimal git repo with one commit
    subprocess.run(["git", "init"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=build_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=build_dir, capture_output=True, check=True)

    # Create .team-ship/ and track it
    team_ship_dir = build_dir / ".team-ship"
    team_ship_dir.mkdir()
    (team_ship_dir / "EVIDENCE.md").write_text("# Evidence\n")

    subprocess.run(["git", "add", ".team-ship"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "commit", "-m", "Add team-ship (TRACKED)"], cwd=build_dir, capture_output=True, check=True, env=git_env)

    # Create the test metadata
    metadata = {
        "name": "team-ship-tracked",
        "expected_exit": 1,
        "description": ".team-ship/ is tracked in git, cannot achieve independence",
        "tracked_files": [".team-ship/EVIDENCE.md"]
    }
    (fixture_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


def make_gate_mismatch(output_root: Path) -> None:
    """Fixture: gate result mismatch between builder and verifier (exit 1)."""
    fixture_dir = output_root / "gate-mismatch"
    fixture_dir.mkdir(exist_ok=True)

    build_dir = fixture_dir / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    # Set git environment for deterministic commits
    git_env = os.environ.copy()
    fixed_ts = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
    git_env.update({
        "GIT_AUTHOR_DATE": fixed_ts,
        "GIT_COMMITTER_DATE": fixed_ts,
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    })

    # Initialize a minimal git repo
    subprocess.run(["git", "init"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=build_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=build_dir, capture_output=True, check=True)

    (build_dir / "README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "README.md"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=build_dir, capture_output=True, check=True, env=git_env)

    metadata = {
        "name": "gate-mismatch",
        "expected_exit": 1,
        "description": "Builder passed=10/skipped=0, verifier passed=9/skipped=1"
    }
    (fixture_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


def make_head_mismatch(output_root: Path) -> None:
    """Fixture: gate results with different head SHAs (exit 1)."""
    fixture_dir = output_root / "head-mismatch"
    fixture_dir.mkdir(exist_ok=True)

    build_dir = fixture_dir / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    # Set git environment for deterministic commits
    git_env = os.environ.copy()
    fixed_ts = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
    git_env.update({
        "GIT_AUTHOR_DATE": fixed_ts,
        "GIT_COMMITTER_DATE": fixed_ts,
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    })

    # Initialize a minimal git repo
    subprocess.run(["git", "init"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=build_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=build_dir, capture_output=True, check=True)

    (build_dir / "README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "README.md"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=build_dir, capture_output=True, check=True, env=git_env)

    metadata = {
        "name": "head-mismatch",
        "expected_exit": 1,
        "description": "Builder and verifier gate files have different HEAD SHAs"
    }
    (fixture_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


def make_not_a_git_repo(output_root: Path) -> None:
    """Fixture: not a git repository (exit 2)."""
    fixture_dir = output_root / "not-a-git-repo"
    fixture_dir.mkdir(exist_ok=True)

    build_dir = fixture_dir / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    # Just a plain directory with no git
    (build_dir / "README.md").write_text("# Not a git repo\n")

    metadata = {
        "name": "not-a-git-repo",
        "expected_exit": 2,
        "description": "Directory is not a git repository"
    }
    (fixture_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


def make_stale_verify_wt(output_root: Path) -> None:
    """Fixture: stale verify-wt directory already exists (exit 0)."""
    fixture_dir = output_root / "stale-verify-wt"
    fixture_dir.mkdir(exist_ok=True)

    build_dir = fixture_dir / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    # Set git environment for deterministic commits
    git_env = os.environ.copy()
    fixed_ts = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
    git_env.update({
        "GIT_AUTHOR_DATE": fixed_ts,
        "GIT_COMMITTER_DATE": fixed_ts,
        "GIT_AUTHOR_NAME": "Test User",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test User",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    })

    # Initialize a minimal git repo
    subprocess.run(["git", "init"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=build_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=build_dir, capture_output=True, check=True)

    (build_dir / "README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "README.md"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=build_dir, capture_output=True, check=True, env=git_env)

    # Create a gitignore for .team-ship
    (build_dir / ".gitignore").write_text(".team-ship/\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=build_dir, capture_output=True, check=True, env=git_env)
    subprocess.run(["git", "commit", "-m", "Add gitignore"], cwd=build_dir, capture_output=True, check=True, env=git_env)

    metadata = {
        "name": "stale-verify-wt",
        "expected_exit": 0,
        "description": "Stale verify-wt directory exists and is removed before creating fresh one"
    }
    (fixture_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


def main() -> None:
    """Generate all fixtures."""
    parser = argparse.ArgumentParser(description="Generate test fixtures")
    parser.add_argument("--out", type=Path, default=None, help="Output root directory")
    args = parser.parse_args()

    if args.out:
        output_root = Path(args.out).resolve()
    else:
        output_root = Path(__file__).resolve().parent

    make_clean_worktree_ok(output_root)
    make_team_ship_tracked(output_root)
    make_gate_mismatch(output_root)
    make_head_mismatch(output_root)
    make_not_a_git_repo(output_root)
    make_stale_verify_wt(output_root)
    print("Fixtures generated successfully")


if __name__ == "__main__":
    main()
