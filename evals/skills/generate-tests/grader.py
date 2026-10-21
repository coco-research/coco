"""Grade a generated unittest module by how many mutants it kills.

Model-written test code runs only when the environment variable
COCO_SKILL_EXEC_UNTRUSTED=1, and then only inside macOS sandbox-exec, with no
network and writes confined to the temp directory. Elsewhere (Linux included)
there is no sandbox that confines writes, so the grader scores 0 with a note
instead of running the code.

ponytail: the 30s timeout, the minimal child environment and the temp-dir cwd
are kept. Ceiling: macOS only, and reads are not restricted. Upgrade path: a
container sandbox, which would also enable Linux.
"""
import functools
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_FENCE = re.compile(r"```([^\n`]*)\r?\n(.*?)```", re.DOTALL)
_TIMEOUT = 30

UNTRUSTED_ENV = "COCO_SKILL_EXEC_UNTRUSTED"
NOT_RUN_NOTE = "untrusted test code not run: set COCO_SKILL_EXEC_UNTRUSTED=1 (sandboxed)"
NO_SANDBOX_NOTE = "no write-confining sandbox here (macOS sandbox-exec only); untrusted test code not run"


def extract_tests(output):
    """First ```python or bare ``` fence whose body contains 'unittest'."""
    if not isinstance(output, str):
        return None
    for match in _FENCE.finditer(output):
        lang = match.group(1).strip().lower()
        body = match.group(2)
        if lang in ("", "python") and "unittest" in body:
            return body
    return None


def _child_env():
    return {
        "PATH": os.environ.get("PATH", os.defpath),
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _untrusted_exec_allowed():
    return os.environ.get(UNTRUSTED_ENV) == "1"


def _probe_works(cmd):
    """True only when cmd actually starts and exits 0 on this host."""
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


@functools.lru_cache(maxsize=None)
def _sandbox_exec_works():
    """True only when sandbox-exec can start a trivially allowed process."""
    return _probe_works(
        ["sandbox-exec", "-p", "(version 1)(allow default)", "true"]
    )


def sandbox_cmd(tmp):
    """Command that runs model-written tests under an OS sandbox.

    macOS uses sandbox-exec with no network and writes limited to the temp
    directory and /dev/null. Returns None anywhere else: Linux's unprivileged
    `unshare -rn` blocks the network but not file writes, so it is not used.
    """
    base = ["python3", "-E", "-s", "-B", "-m", "unittest", "-q", "test_skill"]  # -B: -E ignores PYTHONDONTWRITEBYTECODE
    if shutil.which("sandbox-exec") and _sandbox_exec_works():
        path = os.path.realpath(tmp).replace("\\", "\\\\").replace('"', '\\"')
        profile = (
            "(version 1)"
            "(allow default)"
            "(deny network*)"
            "(deny file-write*)"
            '(allow file-write* (subpath "' + path + '") (literal "/dev/null"))'
        )
        return ["sandbox-exec", "-p", profile] + base
    return None


def _purge_bytecode(directory):
    root = Path(directory)
    # Untrusted tests may leave odd entries here (a dir or a file named __pycache__): never crash on them.
    for cache in list(root.rglob("__pycache__")):
        if cache.is_dir() and not cache.is_symlink():
            shutil.rmtree(cache, ignore_errors=True)
        else:
            try:
                cache.unlink()
            except OSError:
                pass
    for pyc in root.glob("*.pyc"):
        try:
            pyc.unlink()
        except OSError:
            pass


def _run_in_sandbox(test_src, directory, impl_src=None):
    """Write the sources into directory and run the tests under the sandbox.

    Returns the finished process, or None when no sandbox is available or the
    run times out. This is the raw runner; the env gate lives in the callers.
    """
    directory = Path(directory)
    _purge_bytecode(directory)
    if impl_src is not None:
        (directory / "impl.py").write_text(impl_src)
    (directory / "test_skill.py").write_text(test_src)
    cmd = sandbox_cmd(directory)
    if cmd is None:
        return None
    try:
        return subprocess.run(
            cmd,
            cwd=directory,
            env=_child_env(),
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):  # timeout, or the spawn itself failed
        return None


def tests_pass(impl_src, test_src, directory=None):
    """True when the extracted tests exit 0 against impl_src, sandboxed."""

    return run_outcome(impl_src, test_src, directory) == "pass"


def run_outcome(impl_src, test_src, directory=None):
    """"pass", "fail", or "error" (not allowed, no sandbox, timeout, or the run never started)."""

    def run(directory):
        if not _untrusted_exec_allowed():
            return "error"
        result = _run_in_sandbox(test_src, directory, impl_src)
        if result is None:
            return "error"
        return "pass" if result.returncode == 0 else "fail"

    if directory is not None:
        return run(directory)
    with tempfile.TemporaryDirectory() as tmp:
        return run(tmp)


def grade(item, output):
    test_src = extract_tests(output)
    if test_src is None:
        return {"score": 0.0, "notes": ["no unittest code block"]}
    if not item["mutants"]:
        return {"score": 0.0, "notes": ["item has no mutants"]}
    if not _untrusted_exec_allowed():
        return {"score": 0.0, "notes": [NOT_RUN_NOTE]}
    if sandbox_cmd(tempfile.gettempdir()) is None:
        return {"score": 0.0, "notes": [NO_SANDBOX_NOTE]}
    # Each run gets a fresh directory: a file the untrusted tests leave behind
    # (a shadowing unittest.py, say) must not carry into the next run.
    first = run_outcome(item["impl"], test_src)
    if first == "error":
        return {"score": 0.0, "notes": ["tests did not finish on the correct function (timeout or run error)"]}
    if first == "fail":
        return {"score": 0.0, "notes": ["tests fail on the correct function"]}
    notes = []
    killed = 0
    for index, mutant in enumerate(item["mutants"], start=1):
        outcome = run_outcome(mutant, test_src)
        if outcome == "fail":
            killed += 1
        elif outcome == "pass":
            notes.append(f"mutant {index} survived")
        else:  # a hang or a failed start is not a kill
            notes.append(f"mutant {index}: run did not finish, not counted as caught")
    return {"score": killed / len(item["mutants"]), "notes": notes}
