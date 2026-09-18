#!/usr/bin/env python3
"""Generate deterministic fixture repositories for brownfield_map.py's --self-test.

Anchors on its own file location, accepts --out for an alternative root, and pins
GIT_AUTHOR_DATE, GIT_COMMITTER_DATE, and a fixed author/committer identity from
TEAM_FIXED_TS so two generations are byte-identical (except .git/index and
.git/logs, which is the accepted variance under diff -r).

Fixtures:
  map-written   a small, two-commit repository with a helper, a caller and a
                test. Used directly for the map-written and map-with-task
                self-test cases, and reused (with the environment varied
                instead of the repository) for binary-absent, ripwire-fails
                and no-run.
  greenfield    a single-commit repository with one tracked file.
  repo-root-mismatch
                an outer, single-commit repository (the one the self-test
                starts a run against) containing "nested-unrelated", its
                own single-commit git repository with no .team-ship of its
                own. Used by the self-test to prove that pointing
                --repo-root at the nested repository is caught and refused
                before anything is written, even though find_run() walks
                up from it and finds the outer run.

The stub ripwire binary that stands in for the real one does not read these
repositories at all; it prints a fixed, redacted JSON document regardless of
which directory it is pointed at (see stub-ripwire and the README beside
this file). Greenfield detection in brownfield_map.py is computed from git
directly, never from the stub's canned output, which is why the greenfield
fixture only needs one real commit and one real tracked file to exercise it.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

FIXED_NAME = "Team Gate Fixtures"
FIXED_EMAIL = "team-gate-fixtures@example.invalid"


def _git_env(ts: str) -> dict:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = FIXED_NAME
    env["GIT_AUTHOR_EMAIL"] = FIXED_EMAIL
    env["GIT_COMMITTER_NAME"] = FIXED_NAME
    env["GIT_COMMITTER_EMAIL"] = FIXED_EMAIL
    env["GIT_AUTHOR_DATE"] = ts
    env["GIT_COMMITTER_DATE"] = ts
    return env


def _reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def _commit(path: Path, message: str, ts: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=str(path), check=True,
                    capture_output=True, env=_git_env(ts))


def _init_git_repo(path: Path, ts: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", FIXED_NAME], cwd=str(path), check=True,
                    capture_output=True)
    subprocess.run(["git", "config", "user.email", FIXED_EMAIL], cwd=str(path), check=True,
                    capture_output=True)
    _commit(path, "fixture", ts)


def _make_map_written(out_dir: Path, ts: str) -> None:
    repo = out_dir / "map-written"
    _reset_dir(repo)
    (repo / "src").mkdir()
    (repo / "src" / "util.py").write_text(
        "def add(a, b):\n    return a + b\n\n\ndef used_by_helper(x):\n    return add(x, 1)\n"
    )
    (repo / "src" / "main.py").write_text(
        "from src.util import used_by_helper\n\n\n"
        "def helper(x):\n    return used_by_helper(x)\n\n\n"
        "def main():\n    print(helper(5))\n"
    )
    (repo / ".gitignore").write_text("__pycache__/\n")
    _init_git_repo(repo, ts)
    (repo / "tests").mkdir()
    (repo / "tests" / "test_util.py").write_text(
        "from src.util import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n"
    )
    _commit(repo, "add test", ts)


def _make_greenfield(out_dir: Path, ts: str) -> None:
    repo = out_dir / "greenfield"
    _reset_dir(repo)
    (repo / "app.py").write_text("def main():\n    print(\"hello\")\n")
    _init_git_repo(repo, ts)


def _make_repo_root_mismatch(out_dir: Path, ts: str) -> None:
    outer = out_dir / "repo-root-mismatch"
    _reset_dir(outer)
    (outer / "app.py").write_text("def main():\n    print(\"outer\")\n")
    _init_git_repo(outer, ts)

    nested = outer / "nested-unrelated"
    nested.mkdir()
    (nested / "lib.py").write_text("def helper():\n    return 1\n")
    _init_git_repo(nested, ts)


def generate_fixtures(out_dir: Path) -> None:
    ts = os.environ.get("TEAM_FIXED_TS", "2026-09-17T14:22:03+00:00")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    _make_map_written(out_dir, ts)
    _make_greenfield(out_dir, ts)
    _make_repo_root_mismatch(out_dir, ts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate fixtures for brownfield_map.py.")
    parser.add_argument("--out", default=None, help="output directory (default: _build next to this file)")
    args = parser.parse_args()
    out_dir = Path(args.out).resolve() if args.out else Path(__file__).resolve().parent / "_build"
    generate_fixtures(out_dir)
    print(f"wrote fixtures to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
