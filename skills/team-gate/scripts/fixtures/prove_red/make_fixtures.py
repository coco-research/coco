#!/usr/bin/env python3
"""Generate prove_red fixtures deterministically.

Each fixture is a git repository at <name>/_build/repo with exactly two commits,
a base commit and a HEAD commit. <name>/_build/BASE_SHA holds the base commit
SHA. Every git call in this generator runs with a fixed author and committer
identity and date (from TEAM_FIXED_TS, default 2026-01-01T00:00:00Z), so two
generations produce identical commit SHAs; the only variance under diff -r
between generations is .git/index and .git/logs. --out redirects the fixtures
root; the default anchors on this file's own directory. An existing _build is
removed before a fixture is regenerated.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

FIXTURES_DIR = Path(__file__).resolve().parent


def _git_env(fixed_ts: str) -> Dict[str, str]:
    """Environment for a deterministic git call: fixed author and committer identity and date."""
    env = os.environ.copy()
    env.update({
        "GIT_AUTHOR_NAME": "fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_AUTHOR_DATE": fixed_ts,
        "GIT_COMMITTER_NAME": "fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_DATE": fixed_ts,
    })
    return env


def _git(repo: Path, env: Dict[str, str], *args: str) -> subprocess.CompletedProcess:
    """Run git against repo with the deterministic environment. Raises on failure."""
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")
    return result


def _init_repo(root: Path, name: str, env: Dict[str, str]) -> Path:
    """Remove any existing _build and create a fresh _build/repo for a fixture."""
    build_dir = root / name / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    repo = build_dir / "repo"
    repo.mkdir(parents=True)
    _git(repo, env, "init", "-q", "--initial-branch=main")
    _git(repo, env, "config", "commit.gpgsign", "false")
    return repo


def _write_files(repo: Path, files: Dict[str, str]) -> None:
    """Write files relative to repo, creating parent directories as needed."""
    for rel, content in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _commit(repo: Path, env: Dict[str, str], message: str) -> str:
    """Stage everything and commit with the deterministic identity; return the new HEAD SHA."""
    _git(repo, env, "add", "-A")
    _git(repo, env, "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
    return _git(repo, env, "rev-parse", "HEAD").stdout.strip()


def _write_base_sha(root: Path, name: str, sha: str) -> None:
    """Record the base commit SHA for a fixture."""
    (root / name / "_build" / "BASE_SHA").write_text(sha, encoding="utf-8")


def fixture_proper_red_green(root: Path, env: Dict[str, str]) -> None:
    """Base has the bug (subtracts); HEAD fixes it and adds the test that catches it."""
    name = "proper-red-green"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a - b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_new_module_import_red(root: Path, env: Dict[str, str]) -> None:
    """Base has only a placeholder test file; HEAD adds the module the test imports."""
    name = "new-module-import-red"
    repo = _init_repo(root, name, env)
    _write_files(repo, {"tests/test_calc.py": "# placeholder\n"})
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "def test_add():\n    from src.calc import add\n    assert add(2, 3) == 5\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_new_symbol_in_existing_module(root: Path, env: Dict[str, str]) -> None:
    """Base has a module missing the symbol under test; HEAD adds the symbol to that module."""
    name = "new-symbol-in-existing-module"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/math.py": "def subtract(a, b):\n    return a - b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/math.py": "def subtract(a, b):\n    return a - b\n\n\ndef add(a, b):\n    return a + b\n",
        "tests/test_math.py": "def test_add():\n    from src.math import add\n    assert add(2, 3) == 5\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_assertion_in_helper(root: Path, env: Dict[str, str]) -> None:
    """Same bug and fix as proper-red-green, but the assertion lives in a helper the test calls."""
    name = "assertion-in-helper"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a - b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": (
            "from src.calc import add\n\n\n"
            "def check(actual, expected):\n    assert actual == expected\n\n\n"
            "def test_add():\n    check(add(2, 3), 5)\n"
        ),
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_unittest_valid_red(root: Path, env: Dict[str, str]) -> None:
    """Same bug and fix as proper-red-green, but the new test is a unittest.TestCase whose
    red-phase failure is an AssertionError raised from inside the standard library's
    unittest/case.py, never from the test file itself."""
    name = "unittest-valid-red"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def mean(values):\n    return sum(values) / (len(values) + 1)\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def mean(values):\n    return sum(values) / len(values)\n",
        "tests/test_calc.py": (
            "import unittest\n\n"
            "from src.calc import mean\n\n\n"
            "class TestMean(unittest.TestCase):\n"
            "    def test_mean(self):\n"
            "        self.assertEqual(mean([2, 4]), 3)\n"
        ),
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_helper_outside_worktree(root: Path, env: Dict[str, str]) -> None:
    """Same bug and fix as proper-red-green, but the assertion lives in a helper module
    that sits outside the worktree entirely, reachable only through an external
    sys.path entry the self-test supplies via PYTHONPATH."""
    name = "helper-outside-worktree"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a - b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": (
            "from assert_helper import check_equal\n\n"
            "from src.calc import add\n\n\n"
            "def test_add():\n    check_equal(add(2, 3), 5)\n"
        ),
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)
    external_dir = root / name / "_build" / "external_helpers"
    external_dir.mkdir(parents=True, exist_ok=True)
    (external_dir / "assert_helper.py").write_text(
        "def check_equal(actual, expected):\n    assert actual == expected\n",
        encoding="utf-8",
    )


def fixture_unittest_invalid_red(root: Path, env: Dict[str, str]) -> None:
    """A unittest.TestCase test whose red-phase failure is an AssertionError raised by a
    plain assert statement inside the implementation module itself, not by the test."""
    name = "unittest-invalid-red"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": (
            "def double(n):\n"
            "    result = n + n + 1\n"
            "    assert result % 2 == 0, \"double must be even\"\n"
            "    return result\n"
        ),
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": (
            "def double(n):\n"
            "    result = n + n\n"
            "    assert result % 2 == 0, \"double must be even\"\n"
            "    return result\n"
        ),
        "tests/test_calc.py": (
            "import unittest\n\n"
            "from src.calc import double\n\n\n"
            "class TestDouble(unittest.TestCase):\n"
            "    def test_double(self):\n"
            "        self.assertEqual(double(3), 6)\n"
        ),
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_never_red(root: Path, env: Dict[str, str]) -> None:
    """Base already has a passing implementation and test; HEAD only adds an unrelated test.

    HEAD also touches an unrelated, unimported module (src/util.py) so the diff
    carries an implementation path and stays on the ordinary red-green proof
    rather than stub mode; add() itself, the function under test, never
    changes, which is the case this fixture exists to cover.
    """
    name = "never-red"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "src/util.py": "def double(n):\n    return n * 2\n",
        "tests/test_calc.py": "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/util.py": "def double(n):\n    return n * 2\n\n\ndef triple(n):\n    return n * 3\n",
        "tests/test_calc.py": (
            "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n"
            "\n\ndef test_add_negatives():\n    assert add(-2, 3) == 1\n"
        ),
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_wrong_reason_syntax_error(root: Path, env: Dict[str, str]) -> None:
    """Base has a syntax error in the implementation (missing colon); HEAD fixes it and adds the test."""
    name = "wrong-reason-syntax-error"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b)\n    return a + b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_weakened_after_red(root: Path, env: Dict[str, str]) -> None:
    """Same as proper-red-green, plus a weakened test file for the self-test to commit after proving."""
    name = "weakened-after-red"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a - b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)
    weakened = root / name / "_build" / "weakened_test_calc.py"
    weakened.write_text(
        "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) in (5, 6)\n",
        encoding="utf-8",
    )


def fixture_inseparable_same_file(root: Path, env: Dict[str, str]) -> None:
    """The test and the implementation it exercises live in the same non-test file."""
    name = "inseparable-same-file"
    repo = _init_repo(root, name, env)
    _write_files(repo, {"app.py": "# empty\n"})
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "app.py": "def add(a, b):\n    return a + b\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_mixed_valid_and_inseparable(root: Path, env: Dict[str, str]) -> None:
    """proper-red-green's valid change plus inseparable-same-file's app.py change in one HEAD commit."""
    name = "mixed-valid-and-inseparable"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a - b\n",
        "app.py": "# empty\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        "app.py": "def add(a, b):\n    return a + b\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_not_applicable_no_new_tests(root: Path, env: Dict[str, str]) -> None:
    """Base as proper-red-green; HEAD changes only the implementation, no test."""
    name = "not-applicable-no-new-tests"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a - b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_dirty_tree(root: Path, env: Dict[str, str]) -> None:
    """proper-red-green fully committed, then an uncommitted edit is left on top."""
    name = "dirty-tree"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a - b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)
    calc = repo / "src" / "calc.py"
    calc.write_text(calc.read_text(encoding="utf-8") + "# dirty\n", encoding="utf-8")


def fixture_unrunnable_parametrised(root: Path, env: Dict[str, str]) -> None:
    """proper-red-green's test written with a required parameter the runner cannot supply."""
    name = "unrunnable-parametrised"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a - b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from src.calc import add\n\n\ndef test_add(value):\n    assert add(value, 3) == value + 3\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_tests_only_exercises(root: Path, env: Dict[str, str]) -> None:
    """Existing module unchanged at base and HEAD; HEAD adds a unittest test that calls it."""
    name = "tests-only-exercises"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a + b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "tests/test_calc.py": (
            "import unittest\n\n"
            "from src.calc import add\n\n\n"
            "class TestAdd(unittest.TestCase):\n"
            "    def test_add(self):\n"
            "        self.assertEqual(add(2, 3), 5)\n"
        ),
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_tests_only_no_import(root: Path, env: Dict[str, str]) -> None:
    """HEAD adds a test that asserts on a literal and imports nothing from the worktree."""
    name = "tests-only-no-import"
    repo = _init_repo(root, name, env)
    _write_files(repo, {"README.md": "placeholder\n"})
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "tests/test_trivial.py": "def test_trivial():\n    assert 1 == 1\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_tests_only_still_passes(root: Path, env: Dict[str, str]) -> None:
    """HEAD adds a test that imports the module but asserts only on its own constant."""
    name = "tests-only-still-passes"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a + b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "tests/test_calc2.py": (
            "from src.calc import add\n\n"
            "EXPECTED = 5\n\n\n"
            "def test_add():\n    assert EXPECTED == 5\n"
        ),
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_tests_only_relative_import(root: Path, env: Dict[str, str]) -> None:
    """HEAD adds a test in a package that reaches its implementation via a relative import."""
    name = "tests-only-relative-import"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "pkg/__init__.py": "",
        "pkg/calc.py": "def add(a, b):\n    return a + b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "pkg/test_calc.py": (
            "from .calc import add\n\n\n"
            "def test_add():\n    assert add(2, 3) == 5\n"
        ),
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


def fixture_mixed_diff_uses_red_green(root: Path, env: Dict[str, str]) -> None:
    """An implementation fix plus a new test in the same HEAD commit keeps red-green mode."""
    name = "mixed-diff-uses-red-green"
    repo = _init_repo(root, name, env)
    _write_files(repo, {
        "src/__init__.py": "",
        "src/calc.py": "def add(a, b):\n    return a - b\n",
    })
    base_sha = _commit(repo, env, "base")
    _write_files(repo, {
        "src/calc.py": "def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": "from src.calc import add\n\n\ndef test_add():\n    assert add(2, 3) == 5\n",
    })
    _commit(repo, env, "head")
    _write_base_sha(root, name, base_sha)


_GENERATORS = [
    fixture_proper_red_green,
    fixture_new_module_import_red,
    fixture_new_symbol_in_existing_module,
    fixture_assertion_in_helper,
    fixture_unittest_valid_red,
    fixture_helper_outside_worktree,
    fixture_unittest_invalid_red,
    fixture_never_red,
    fixture_wrong_reason_syntax_error,
    fixture_weakened_after_red,
    fixture_inseparable_same_file,
    fixture_mixed_valid_and_inseparable,
    fixture_not_applicable_no_new_tests,
    fixture_dirty_tree,
    fixture_unrunnable_parametrised,
    fixture_tests_only_exercises,
    fixture_tests_only_no_import,
    fixture_tests_only_still_passes,
    fixture_tests_only_relative_import,
    fixture_mixed_diff_uses_red_green,
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None, help="alternative fixtures root")
    args = parser.parse_args()

    root = Path(args.out).resolve() if args.out else FIXTURES_DIR
    fixed_ts = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
    env = _git_env(fixed_ts)

    try:
        for generator in _GENERATORS:
            generator(root, env)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
