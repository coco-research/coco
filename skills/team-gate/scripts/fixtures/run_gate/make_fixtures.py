#!/usr/bin/env python3
"""Generate deterministic fixture repositories for run_gate.py's --self-test.

Anchors on its own file location, accepts --out for an alternative root, and pins
GIT_AUTHOR_DATE, GIT_COMMITTER_DATE, and a fixed author/committer identity from
TEAM_FIXED_TS so two generations are byte-identical (except .git/index and
.git/logs, which is the accepted variance under diff -r).

Fixtures (see README.md for why five of them ship a stub bin/pytest):
  all-pass            run: passed only, exit 0
  one-fail            run: one failure, exit 1
  one-skip            run: one skip, exit 0 from the stub, exit 1 from run_gate.py
  parity-mismatch     parity: ruff pinned in pyproject.toml but not installed locally
  no-ci-config        discover: no .github/workflows, no Makefile, no package.json
  lint-and-test       discover: a lint step and a test step; pytest must be chosen
  runner-absent       run: PATH restricted at self-test time so pytest cannot be found
  multiline-run-block      discover: a `run: |` block whose first line is `set -e`;
                           the pytest line further down the block must be chosen
  only-install-steps       discover: every run: block is pip install or echo; exit 2
  no-tests-ran             run: the stub prints "no tests ran"; run_gate.py must block
  multi-command-step       discover/run: one step, two commands (bash + python3
                           --self-test), both exit 0; discover records both, run
                           executes both
  multi-command-one-fails  same two commands; the second exits 3; run must name it
  coverage-not-applicable  discover finds only a bash test script, no pytest command;
                           coverage must be NOT_APPLICABLE
  shell-operator-line      discover: a step with `bash tests/check-x.sh || true` and a
                           plain `pytest -q`; the first is skipped, the second chosen
  shell-operator-only      discover: only the `|| true` line; zero commands, exit 2
  unittest-all-pass        run: a `bash scripts/test.sh` runner prints unittest's
                            `Ran 3 tests` + `OK`; summary shape unittest, passed 3
  unittest-one-fail        run: `Ran 2 tests` + `FAILED (failures=1)`, exit 1
  unittest-skip            run: `Ran 2 tests` + `OK (skipped=1)`, exit 1 (blocked)
  unittest-zero            run: `Ran 0 tests` + `OK`; blocked as no tests collected
  pytest-wins              run: the same script prints both shapes; pytest's own
                            `2 passed` line must win, shape pytest, passed 2
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

FIXED_NAME = "Team Gate Fixtures"
FIXED_EMAIL = "team-gate-fixtures@example.invalid"

STUB_HEADER = (
    "#!/usr/bin/env python3\n"
    "import sys\n"
    "if \"--version\" in sys.argv:\n"
    "    print(\"pytest 7.4.4\")\n"
    "    sys.exit(0)\n"
)
STUB_ALL_PASS = STUB_HEADER + "print(\"2 passed in 0.01s\")\nsys.exit(0)\n"
STUB_ONE_FAIL = STUB_HEADER + "print(\"1 failed, 1 passed in 0.01s\")\nsys.exit(1)\n"
STUB_ONE_SKIP = STUB_HEADER + "print(\"1 passed, 1 skipped in 0.01s\")\nsys.exit(0)\n"
STUB_PARITY = STUB_HEADER + "print(\"1 passed in 0.01s\")\nsys.exit(0)\n"
STUB_NO_TESTS_RAN = STUB_HEADER + "print(\"no tests ran in 0.01s\")\nsys.exit(0)\n"


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


def _init_git_repo(path: Path, ts: str) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", FIXED_NAME], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", FIXED_EMAIL], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=str(path), check=True,
                    capture_output=True, env=_git_env(ts))


def _write_workflow(repo: Path, run_cmd: str, lint_cmd: str = None) -> None:
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    steps = ["      - uses: actions/checkout@v4"]
    if lint_cmd:
        steps.append("      - name: Lint")
        steps.append(f"        run: {lint_cmd}")
    steps.append("      - name: Test")
    steps.append(f"        run: {run_cmd}")
    content = "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n"
    content += "\n".join(steps) + "\n"
    (workflows / "ci.yml").write_text(content)


def _write_stub_pytest(repo: Path, body: str) -> None:
    bin_dir = repo / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub = bin_dir / "pytest"
    stub.write_text(body)
    os.chmod(stub, 0o755)


def _make_all_pass(out_dir: Path, ts: str) -> None:
    repo = out_dir / "all-pass"
    _reset_dir(repo)
    (repo / "test_example.py").write_text(
        "def test_one():\n    assert True\n\n\ndef test_two():\n    assert 1 + 1 == 2\n"
    )
    _write_workflow(repo, "pytest -q")
    _write_stub_pytest(repo, STUB_ALL_PASS)
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    _init_git_repo(repo, ts)


def _make_one_fail(out_dir: Path, ts: str) -> None:
    repo = out_dir / "one-fail"
    _reset_dir(repo)
    (repo / "test_example.py").write_text(
        "def test_pass():\n    assert True\n\n\ndef test_fail():\n    assert False\n"
    )
    _write_workflow(repo, "pytest -q")
    _write_stub_pytest(repo, STUB_ONE_FAIL)
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    _init_git_repo(repo, ts)


def _make_one_skip(out_dir: Path, ts: str) -> None:
    repo = out_dir / "one-skip"
    _reset_dir(repo)
    (repo / "test_example.py").write_text(
        "import pytest\n\n\ndef test_pass():\n    assert True\n\n\n"
        "@pytest.mark.skip(reason=\"not ready\")\ndef test_skip():\n    assert False\n"
    )
    _write_workflow(repo, "pytest -q")
    _write_stub_pytest(repo, STUB_ONE_SKIP)
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    _init_git_repo(repo, ts)


def _make_parity_mismatch(out_dir: Path, ts: str) -> None:
    repo = out_dir / "parity-mismatch"
    _reset_dir(repo)
    (repo / "test_example.py").write_text("def test_pass():\n    assert True\n")
    _write_workflow(repo, "pytest -q")
    _write_stub_pytest(repo, STUB_PARITY)
    (repo / "pyproject.toml").write_text('[project]\ndependencies = ["ruff==0.7.0"]\n')
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    _init_git_repo(repo, ts)


def _make_no_ci_config(out_dir: Path, ts: str) -> None:
    repo = out_dir / "no-ci-config"
    _reset_dir(repo)
    (repo / "README.md").write_text("no CI configuration on purpose\n")
    _init_git_repo(repo, ts)


def _make_lint_and_test(out_dir: Path, ts: str) -> None:
    repo = out_dir / "lint-and-test"
    _reset_dir(repo)
    (repo / "test_example.py").write_text("def test_pass():\n    assert True\n")
    _write_workflow(repo, "pytest -q", lint_cmd="ruff check .")
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    _init_git_repo(repo, ts)


def _make_runner_absent(out_dir: Path, ts: str) -> None:
    repo = out_dir / "runner-absent"
    _reset_dir(repo)
    (repo / "test_example.py").write_text("def test_pass():\n    assert True\n")
    _write_workflow(repo, "pytest -q")
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    _init_git_repo(repo, ts)


def _make_multiline_run_block(out_dir: Path, ts: str) -> None:
    repo = out_dir / "multiline-run-block"
    _reset_dir(repo)
    (repo / "test_example.py").write_text("def test_pass():\n    assert True\n")
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / "ci.yml").write_text(
        "name: CI\n"
        "on: [push]\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - name: Test\n"
        "        run: |\n"
        "          set -e\n"
        "          pip install -e .\n"
        "          pytest -q\n"
    )
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    _init_git_repo(repo, ts)


def _make_only_install_steps(out_dir: Path, ts: str) -> None:
    repo = out_dir / "only-install-steps"
    _reset_dir(repo)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / "ci.yml").write_text(
        "name: CI\n"
        "on: [push]\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - name: Install\n"
        "        run: |\n"
        "          pip install -e .\n"
        "          echo installed\n"
        "      - name: Announce\n"
        "        run: echo done\n"
    )
    _init_git_repo(repo, ts)


def _make_no_tests_ran(out_dir: Path, ts: str) -> None:
    repo = out_dir / "no-tests-ran"
    _reset_dir(repo)
    _write_workflow(repo, "pytest -q")
    _write_stub_pytest(repo, STUB_NO_TESTS_RAN)
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    _init_git_repo(repo, ts)


def _write_workflow_multi(repo: Path, run_lines: list) -> None:
    """Write a single-step workflow whose `run: |` block has one command per line."""
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"          {line}" for line in run_lines)
    content = (
        "name: CI\n"
        "on: [push]\n"
        "jobs:\n"
        "  test:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - name: Standalone suites\n"
        "        run: |\n"
        f"{body}\n"
    )
    (workflows / "ci.yml").write_text(content)


def _make_multi_command_step(out_dir: Path, ts: str) -> None:
    repo = out_dir / "multi-command-step"
    _reset_dir(repo)
    _write_workflow_multi(repo, ["bash tests/smoke.sh", "python3 check.py --self-test"])
    (repo / "tests").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "smoke.sh").write_text("#!/bin/sh\necho smoke ok\nexit 0\n")
    (repo / "check.py").write_text("print(\"self-test ok\")\n")
    _init_git_repo(repo, ts)


def _make_multi_command_one_fails(out_dir: Path, ts: str) -> None:
    repo = out_dir / "multi-command-one-fails"
    _reset_dir(repo)
    _write_workflow_multi(repo, ["bash tests/smoke.sh", "python3 check.py --self-test"])
    (repo / "tests").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "smoke.sh").write_text("#!/bin/sh\necho smoke ok\nexit 0\n")
    (repo / "check.py").write_text("import sys\nprint(\"self-test failing\")\nsys.exit(3)\n")
    _init_git_repo(repo, ts)


def _make_coverage_not_applicable(out_dir: Path, ts: str) -> None:
    repo = out_dir / "coverage-not-applicable"
    _reset_dir(repo)
    _write_workflow_multi(repo, ["bash tests/smoke.sh"])
    (repo / "tests").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "smoke.sh").write_text("#!/bin/sh\necho smoke ok\nexit 0\n")
    _init_git_repo(repo, ts)


def _make_shell_operator_line(out_dir: Path, ts: str) -> None:
    repo = out_dir / "shell-operator-line"
    _reset_dir(repo)
    (repo / "test_example.py").write_text("def test_pass():\n    assert True\n")
    _write_workflow_multi(repo, ["bash tests/check-x.sh || true", "pytest -q"])
    (repo / "tests").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "check-x.sh").write_text("#!/bin/sh\nexit 1\n")
    _write_stub_pytest(repo, STUB_ALL_PASS)
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    _init_git_repo(repo, ts)


def _make_shell_operator_only(out_dir: Path, ts: str) -> None:
    repo = out_dir / "shell-operator-only"
    _reset_dir(repo)
    _write_workflow_multi(repo, ["bash tests/check-x.sh || true"])
    (repo / "tests").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "check-x.sh").write_text("#!/bin/sh\nexit 1\n")
    _init_git_repo(repo, ts)


def _write_test_script(repo: Path, body: str) -> None:
    scripts_dir = repo / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script = scripts_dir / "test.sh"
    script.write_text(body)
    os.chmod(script, 0o755)


def _make_unittest_all_pass(out_dir: Path, ts: str) -> None:
    repo = out_dir / "unittest-all-pass"
    _reset_dir(repo)
    _write_workflow(repo, "bash scripts/test.sh")
    _write_test_script(repo, "#!/bin/bash\necho \"Ran 3 tests in 0.001s\"\necho\necho OK\nexit 0\n")
    _init_git_repo(repo, ts)


def _make_unittest_one_fail(out_dir: Path, ts: str) -> None:
    repo = out_dir / "unittest-one-fail"
    _reset_dir(repo)
    _write_workflow(repo, "bash scripts/test.sh")
    _write_test_script(
        repo,
        "#!/bin/bash\necho \"Ran 2 tests in 0.001s\"\necho\necho \"FAILED (failures=1)\"\nexit 1\n",
    )
    _init_git_repo(repo, ts)


def _make_unittest_skip(out_dir: Path, ts: str) -> None:
    repo = out_dir / "unittest-skip"
    _reset_dir(repo)
    _write_workflow(repo, "bash scripts/test.sh")
    _write_test_script(
        repo,
        "#!/bin/bash\necho \"Ran 2 tests in 0.001s\"\necho\necho \"OK (skipped=1)\"\nexit 0\n",
    )
    _init_git_repo(repo, ts)


def _make_unittest_zero(out_dir: Path, ts: str) -> None:
    repo = out_dir / "unittest-zero"
    _reset_dir(repo)
    _write_workflow(repo, "bash scripts/test.sh")
    _write_test_script(repo, "#!/bin/bash\necho \"Ran 0 tests in 0.000s\"\necho\necho OK\nexit 0\n")
    _init_git_repo(repo, ts)


def _make_pytest_wins(out_dir: Path, ts: str) -> None:
    repo = out_dir / "pytest-wins"
    _reset_dir(repo)
    _write_workflow(repo, "bash scripts/test.sh")
    _write_test_script(
        repo,
        "#!/bin/bash\necho \"Ran 3 tests in 0.001s\"\necho\necho OK\necho \"2 passed in 0.01s\"\nexit 0\n",
    )
    _init_git_repo(repo, ts)


def generate_fixtures(out_dir: Path) -> None:
    ts = os.environ.get("TEAM_FIXED_TS", "2026-09-17T14:22:03+00:00")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    _make_all_pass(out_dir, ts)
    _make_one_fail(out_dir, ts)
    _make_one_skip(out_dir, ts)
    _make_parity_mismatch(out_dir, ts)
    _make_no_ci_config(out_dir, ts)
    _make_lint_and_test(out_dir, ts)
    _make_runner_absent(out_dir, ts)
    _make_multiline_run_block(out_dir, ts)
    _make_only_install_steps(out_dir, ts)
    _make_no_tests_ran(out_dir, ts)
    _make_multi_command_step(out_dir, ts)
    _make_multi_command_one_fails(out_dir, ts)
    _make_coverage_not_applicable(out_dir, ts)
    _make_shell_operator_line(out_dir, ts)
    _make_shell_operator_only(out_dir, ts)
    _make_unittest_all_pass(out_dir, ts)
    _make_unittest_one_fail(out_dir, ts)
    _make_unittest_skip(out_dir, ts)
    _make_unittest_zero(out_dir, ts)
    _make_pytest_wins(out_dir, ts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate fixtures for run_gate.py.")
    parser.add_argument("--out", default=None, help="output directory (default: _build next to this file)")
    args = parser.parse_args()
    out_dir = Path(args.out).resolve() if args.out else Path(__file__).resolve().parent / "_build"
    generate_fixtures(out_dir)
    print(f"wrote fixtures to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
