#!/usr/bin/env python3
"""Discover, run, and measure the repository's authoritative test gate.

Subcommands:
  discover: find the repository's authoritative test commands from CI configuration
            (.github/workflows/*.yml, then, only if no workflow line qualifies,
            Makefile targets named check or test, then package.json scripts).
            Selection is by runner shape only, scanning every line of every run:
            block (including every line of a block scalar, not only its first) in
            file order: pytest, python[3] -m pytest, python[3] <path> --self-test,
            npm test, npx vitest|jest, vitest, jest, cargo test, go test, and
            bash|sh <path> where the path's basename matches *test*.sh, smoke*.sh,
            *-smoke.sh, run_fixtures*.sh, or check-*.sh. Every qualifying line across
            every qualifying step is recorded, in file order, as commands: [{argv,
            source, sourceLine}]; the top-level argv/source/sourceLine mirror the
            first command for the existing single-command consumers. There is no
            job-name or step-name fallback, so an install or lint line is never
            selected. Never accepts a free-form command from the caller. Writes
            gates/7-discover.json; exit 2 when zero lines qualify.
  parity:   compares locally installed tool versions against the versions pinned by
            discover. Writes gates/7.json.
  run:      executes every command discover recorded, in order, each with
            subprocess.run and no shell; parses each command's combined stdout and
            stderr for one of two summary shapes: pytest's `N passed`/`N failed`/
            `N skipped`/`N error(s)` count lines, or unittest's `Ran N tests` line
            followed by `OK`, `OK (skipped=S)`, or `FAILED (failures=F, errors=E,
            skipped=S, expected failures=X, unexpected successes=U)`. When both
            shapes appear in the same output (a pytest run may print
            unittest-looking lines from a wrapped runner) the pytest shape wins.
            Every command's summary carries shape: "pytest", "unittest", or "none"
            when neither shape is recognized, in which case only that command's real
            exit is judged. The gate blocks if any command's real exit is non-zero,
            or any pytest- or unittest-shaped summary has failed, skipped, or errors
            above zero, or has no tests collected at all. A missing runner binary is
            exit 2 for the whole gate. Writes gates/8.json with commands: [{argv,
            real_exit, summary}] alongside the existing top-level fields.
  coverage: re-runs the first pytest-shaped discovered command with --cov
            --cov-branch and records the total percentage. If discover found no
            pytest-shaped command at all, writes gates/10.json with status
            NOT_APPLICABLE and exits 2, never attempting to measure a non-pytest
            command's coverage.
  evidence: aggregates the run's gate files into .team-ship/EVIDENCE.json, then asks
            render_evidence.render() for the markdown and writes .team-ship/EVIDENCE.md.

Usage: run_gate.py [--repo-root REPO] [--role ROLE] SUBCOMMAND [--repo-root REPO] [--role ROLE]

Every subcommand accepts --repo-root and --role. Both flags can be given before the subcommand,
after it, or both (if given in both positions with the same value, the second is ignored; if
given in both positions with different values, exit 2 with one stderr line). Default --repo-root
is "." and default --role is "builder". The verifier role writes gates/<n>-verifier.json instead
of gates/<n>.json, so the builder's own gate files are never overwritten by an independent
re-run. evidence in the verifier role is refused, because evidence is assembled from the
builder's gates only.

The run directory comes only from gate_state.find_run(); it is never invented locally.
Every gate file records argv, cwd, head (git rev-parse HEAD of the measured repository),
exit, and a summary, plus its own gate-specific fields. Every gate file and every
artifact under .team-ship/ is written atomically (temp file plus os.replace) and is
followed by its receipt (gate-result or artifact-written) through
gate_state.append_receipt. A write failure, or a receipt-append failure, is exit 2 with
one stderr line; a receipt-append failure after a successful write removes the file
that was just written, so no gate file or artifact is ever left without its receipt.

Exit contract: 0 = the claim is TRUE (PASS), 1 = the claim is FALSE (BLOCK), 2 = the claim
is NOT DECIDED (validator could not run, dependency absent, UNVERIFIED, NOT_APPLICABLE, or
DISABLED). No other exit code exists.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_state


KNOWN_TOOLS = ["pytest", "ruff", "mypy", "node", "npm", "vitest", "jest", "cargo", "go"]
TOOL_VERSION_CMD = {
    "node": ["node", "--version"],
    "npm": ["npm", "--version"],
    "pytest": ["pytest", "--version"],
    "ruff": ["ruff", "--version"],
    "mypy": ["mypy", "--version"],
    "cargo": ["cargo", "--version"],
    "go": ["go", "version"],
    "vitest": ["vitest", "--version"],
    "jest": ["jest", "--version"],
}
GATE_NAME_MAP = {
    "7-discover": "gate-discovery",
    "7": "env-parity",
    "8": "test-execution",
    "10": "coverage",
    "11": "verify-comparison",
}


# ---------------------------------------------------------------------------
# Shared context, gate-file, and receipt helpers
# ---------------------------------------------------------------------------

def _resolve_context(repo_root_arg: str):
    """Resolve (repo_root, run_dir, head) or print one ERROR line and return None."""
    repo_root = Path(repo_root_arg).resolve()
    try:
        run_dir = gate_state.find_run(repo_root)
    except gate_state.RunMarkerUnreadable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return None
    if run_dir is None:
        print(f"ERROR: no active run found under {repo_root}", file=sys.stderr)
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
    except OSError as exc:
        print(f"ERROR: git rev-parse HEAD failed: {exc}", file=sys.stderr)
        return None
    if result.returncode != 0:
        print(f"ERROR: git rev-parse HEAD failed: {result.stderr.strip()}", file=sys.stderr)
        return None
    return repo_root, run_dir, result.stdout.strip()


def _gate_filename(base: str, role: str) -> str:
    return f"{base}-verifier.json" if role == "verifier" else f"{base}.json"


def _atomic_write(path: Path, content_bytes: bytes) -> None:
    """Write content_bytes to path via a same-directory temp file plus os.replace.

    Raises OSError on any failure (mkdir, temp write, or replace); never partially
    writes the destination path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.tmp"
    tmp.write_bytes(content_bytes)
    os.replace(str(tmp), str(path))


def _write_gate_and_receipt(run_dir: Path, base: str, role: str, data: Dict[str, Any],
                             gate_name: str, exit_code: int, summary: str) -> Optional[int]:
    """Write a gate file atomically, then append its gate-result receipt.

    Fails closed: any OSError writing the file, or any exception appending the
    receipt (InvalidReceiptKind, ReceiptFileCorrupt, a locked or unreadable
    receipts.jsonl, an unwritable run directory), is exit 2 with one stderr line.
    If the receipt append fails after the gate file was written, the gate file is
    removed first, so no gate file is ever left without a matching receipt.

    Returns None on success. Returns 2 on failure (the caller returns it directly).
    """
    gates_dir = run_dir / "gates"
    gate_file = gates_dir / _gate_filename(base, role)
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


def _write_artifact_and_receipt(run_dir: Path, path: Path, rel_path: str,
                                 content_bytes: bytes) -> Optional[int]:
    """Write an artifact atomically under .team-ship/, then append its receipt.

    Same fail-closed contract as _write_gate_and_receipt: a write failure or a
    receipt-append failure is exit 2 with one stderr line, and a receipt-append
    failure removes the artifact just written.
    """
    try:
        _atomic_write(path, content_bytes)
    except OSError as exc:
        print(f"ERROR: cannot write {path}: {exc}", file=sys.stderr)
        return 2

    try:
        gate_state.append_receipt(run_dir, "artifact-written", {
            "path": rel_path,
            "sha256": hashlib.sha256(content_bytes).hexdigest(),
            "lines": content_bytes.decode("utf-8", errors="replace").count("\n"),
        })
    except Exception as exc:
        try:
            path.unlink()
        except OSError:
            pass
        print(f"ERROR: cannot append receipt: {exc}", file=sys.stderr)
        return 2

    return None


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------

def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _extract_run_lines(text: str, source: str) -> List[Dict[str, Any]]:
    """Line-oriented extraction of every `run:` command line in a workflow's jobs.

    Not a YAML parser. For a single-line `run: cmd` (list-item or nested-key form)
    this yields one line. For a block scalar (`run: |`, `run: >`, and their `-`
    variants) this yields every body line of the block, indentation greater than
    the `run:` key's own line, not only the first, each with its own file line
    number. Job and step names are not tracked: selection is by runner shape only.
    """
    result: List[Dict[str, Any]] = []
    lines = text.splitlines()
    in_jobs = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue

        m_run_item = re.match(r'^\s*-\s*run:\s*(.+?)\s*$', line)
        m_run = m_run_item or re.match(r'^\s*run:\s*(.+?)\s*$', line)
        if not m_run:
            continue

        value = m_run.group(1)
        indent = len(line) - len(line.lstrip(" "))
        if value in ("|", ">", "|-", ">-"):
            for j in range(i + 1, len(lines)):
                nxt = lines[j]
                if nxt.strip() == "":
                    continue
                if len(nxt) - len(nxt.lstrip(" ")) <= indent:
                    break
                result.append({"text": nxt.strip(), "source": source, "sourceLine": j + 1})
        else:
            result.append({"text": _strip_quotes(value), "source": source, "sourceLine": i + 1})

    return result


BASH_TEST_SCRIPT_PATTERNS = ("*test*.sh", "smoke*.sh", "*-smoke.sh", "run_fixtures*.sh", "check-*.sh")


def _bash_script_qualifies(path_str: str) -> bool:
    basename = os.path.basename(path_str)
    return any(fnmatch.fnmatch(basename, pattern) for pattern in BASH_TEST_SCRIPT_PATTERNS)


def _is_pytest_command(argv: List[str]) -> bool:
    if not argv:
        return False
    if argv[0] == "pytest":
        return True
    if argv[0] in ("python", "python3"):
        for i in range(1, len(argv) - 1):
            if argv[i] == "-m" and argv[i + 1] == "pytest":
                return True
    return False


def _is_test_argv(argv: List[str]) -> bool:
    if not argv:
        return False
    head = argv[0]
    if _is_pytest_command(argv):
        return True
    if head in ("python", "python3") and "--self-test" in argv[1:]:
        return True
    if head == "npm" and "test" in argv[1:]:
        return True
    if head == "npx" and ("vitest" in argv[1:] or "jest" in argv[1:]):
        return True
    if head in ("vitest", "jest"):
        return True
    if head == "cargo" and "test" in argv[1:]:
        return True
    if head == "go" and "test" in argv[1:]:
        return True
    if head in ("bash", "sh") and len(argv) >= 2 and _bash_script_qualifies(argv[1]):
        return True
    return False


SHELL_OPERATOR_TOKENS = {"||", "&&", ";", "|", ">", "<"}


def _has_unquoted_dollar(text: str) -> bool:
    """True if text contains a `$` outside a single-quoted span.

    Single quotes suppress shell expansion entirely, so a `$` inside them is
    genuinely literal. Everything else (bare, or inside double quotes, where a
    real shell would still expand it) is "unquoted" for this purpose, because
    subprocess.run with no shell never expands anything.
    """
    in_single = False
    for ch in text:
        if ch == "'":
            in_single = not in_single
        elif ch == "$" and not in_single:
            return True
    return False


def _shell_unsafe_reason(text: str, argv: List[str]) -> Optional[str]:
    """None if argv/text can be run by subprocess.run with no shell; else a reason."""
    if any(token in SHELL_OPERATOR_TOKENS for token in argv):
        return "shell operator or variable; cannot run without a shell"
    if _has_unquoted_dollar(text):
        return "shell operator or variable; cannot run without a shell"
    return None


def _select_test_lines(lines: List[Dict[str, Any]]) -> tuple:
    """Select every line, in file order, whose argv is a known test runner.

    Returns (chosen, skipped). A line that qualifies as a runner but cannot be
    reproduced without a shell (a shell operator token, or an unquoted `$`) is
    moved to skipped rather than chosen.
    """
    chosen: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    for entry in lines:
        try:
            argv = shlex.split(entry["text"])
        except ValueError:
            continue
        if not argv or not _is_test_argv(argv):
            continue
        reason = _shell_unsafe_reason(entry["text"], argv)
        if reason:
            skipped.append({"line": entry["sourceLine"], "text": entry["text"], "reason": reason})
            continue
        candidate = dict(entry)
        candidate["argv"] = argv
        chosen.append(candidate)
    return chosen, skipped


def _select_from_makefile(repo_root: Path) -> Optional[Dict[str, Any]]:
    makefile = repo_root / "Makefile"
    if not makefile.is_file():
        return None
    try:
        lines = makefile.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for i, line in enumerate(lines):
        if re.match(r'^(check|test):', line) and i + 1 < len(lines):
            body = lines[i + 1]
            if body.startswith("\t"):
                cmd = body[1:].strip()
                if not cmd:
                    continue
                try:
                    argv = shlex.split(cmd)
                except ValueError:
                    continue
                if argv and _is_test_argv(argv):
                    return {"run": cmd, "argv": argv, "source": "Makefile", "sourceLine": i + 2}
    return None


def _select_from_package_json(repo_root: Path) -> Optional[Dict[str, Any]]:
    pkg_file = repo_root / "package.json"
    if not pkg_file.is_file():
        return None
    try:
        pkg = json.loads(pkg_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    scripts = pkg.get("scripts") or {}
    for key in ("test", "check"):
        cmd = scripts.get(key)
        if not cmd:
            continue
        try:
            argv = shlex.split(cmd)
        except ValueError:
            continue
        if argv and _is_test_argv(argv):
            return {"run": cmd, "argv": argv, "source": "package.json", "sourceLine": 0}
    return None


def _extract_pins(repo_root: Path, workflow_texts: List[str]) -> Dict[str, str]:
    pins: Dict[str, str] = {}
    combined = "\n".join(workflow_texts)

    for tool in KNOWN_TOOLS:
        match = re.search(rf'\b{re.escape(tool)}==([\w.\-]+)', combined)
        if match:
            pins[tool] = match.group(1)
    node_match = re.search(r'node-version:\s*["\']?([\w.]+)', combined)
    if node_match and "node" not in pins:
        pins["node"] = node_match.group(1)

    pyproject = repo_root / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        for tool in KNOWN_TOOLS:
            if tool in pins:
                continue
            match = re.search(rf'"{re.escape(tool)}\s*==\s*([\w.\-]+)"', text)
            if not match:
                match = re.search(rf'^{re.escape(tool)}\s*=\s*"==?\s*([\w.\-]+)"', text, re.MULTILINE)
            if match:
                pins[tool] = match.group(1)

    package_json = repo_root / "package.json"
    if package_json.is_file():
        try:
            pkg = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pkg = {}
        deps: Dict[str, Any] = {}
        deps.update(pkg.get("dependencies") or {})
        deps.update(pkg.get("devDependencies") or {})
        for tool in KNOWN_TOOLS:
            if tool in pins:
                continue
            if tool in deps:
                pins[tool] = re.sub(r'^[\^~=]+', '', str(deps[tool]))

    return pins


def cmd_discover(repo_root_arg: str, role: str) -> int:
    ctx = _resolve_context(repo_root_arg)
    if ctx is None:
        return 2
    repo_root, run_dir, head = ctx

    workflow_texts: List[str] = []
    run_lines: List[Dict[str, Any]] = []
    workflows_dir = repo_root / ".github" / "workflows"
    if workflows_dir.is_dir():
        workflow_files = sorted(workflows_dir.glob("*.yml")) + sorted(workflows_dir.glob("*.yaml"))
        for wf in workflow_files:
            try:
                text = wf.read_text(encoding="utf-8")
            except OSError:
                continue
            workflow_texts.append(text)
            try:
                rel = str(wf.relative_to(repo_root))
            except ValueError:
                rel = str(wf)
            run_lines.extend(_extract_run_lines(text, rel))

    chosen, skipped = _select_test_lines(run_lines)
    if not chosen:
        fallback = _select_from_makefile(repo_root)
        if fallback is None:
            fallback = _select_from_package_json(repo_root)
        if fallback is not None:
            reason = _shell_unsafe_reason(fallback["run"], fallback["argv"])
            if reason:
                skipped.append({"line": fallback["sourceLine"], "text": fallback["run"], "reason": reason})
            else:
                chosen = [fallback]

    pins = _extract_pins(repo_root, workflow_texts)

    if not chosen:
        summary = skipped[0]["reason"] if skipped else "no qualifying test command found in CI configuration"
        data = {
            "argv": None, "cwd": str(repo_root), "head": head, "exit": 2,
            "summary": summary, "source": None, "sourceLine": None, "pins": pins,
            "commands": [], "skipped": skipped,
        }
        override = _write_gate_and_receipt(run_dir, "7-discover", role, data, "gate-discovery", 2, summary)
        if override is not None:
            return override
        print(f"ERROR: {summary}", file=sys.stderr)
        return 2

    commands = [{"argv": c["argv"], "source": c["source"], "sourceLine": c["sourceLine"]} for c in chosen]
    first = commands[0]
    summary = (f"discovered {len(commands)} command(s); first {' '.join(first['argv'])!r} "
               f"from {first['source']}:{first['sourceLine']}")
    data = {
        "argv": first["argv"], "cwd": str(repo_root), "head": head, "exit": 0,
        "summary": summary, "source": first["source"], "sourceLine": first["sourceLine"],
        "pins": pins, "commands": commands, "skipped": skipped,
    }
    override = _write_gate_and_receipt(run_dir, "7-discover", role, data, "gate-discovery", 0, summary)
    if override is not None:
        return override
    print(summary)
    return 0


# ---------------------------------------------------------------------------
# parity
# ---------------------------------------------------------------------------

def _local_tool_version(tool: str) -> Optional[str]:
    cmd = TOOL_VERSION_CMD.get(tool, [tool, "--version"])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = ((result.stdout or "") + (result.stderr or "")).strip()
    if not text:
        return None
    return text.splitlines()[0]


def _read_discover(run_dir: Path, role: str, head: str) -> Optional[Dict[str, Any]]:
    """Read the discover gate file and bind it to the current commit.

    A discover file recorded at a different HEAD than the one measured now is
    stale evidence: the commands it names may no longer exist, or new ones may
    have appeared. Returns None (exit 2) rather than let a stale discovery pass
    silently into run, parity, or coverage.
    """
    discover_file = run_dir / "gates" / _gate_filename("7-discover", role)
    if not discover_file.is_file():
        print("ERROR: discover file missing; run discover first", file=sys.stderr)
        return None
    try:
        data = json.loads(discover_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read discover file: {exc}", file=sys.stderr)
        return None
    discover_head = data.get("head")
    if discover_head != head:
        print(f"ERROR: discover was recorded at {discover_head} but HEAD is {head}; run discover again",
              file=sys.stderr)
        return None
    return data


def cmd_parity(repo_root_arg: str, role: str) -> int:
    ctx = _resolve_context(repo_root_arg)
    if ctx is None:
        return 2
    repo_root, run_dir, head = ctx

    discover_data = _read_discover(run_dir, role, head)
    if discover_data is None:
        return 2

    argv = discover_data.get("argv") or []
    pins = discover_data.get("pins") or {}
    tools = set(pins.keys()) | {t for t in KNOWN_TOOLS if t in argv}

    toolchain: Dict[str, Any] = {}
    mismatched: List[str] = []
    for tool in sorted(tools):
        local_version = _local_tool_version(tool)
        pinned_version = pins.get(tool)
        if local_version is None:
            toolchain[tool] = {"local": None, "ci": pinned_version, "match": False}
            mismatched.append(tool)
        elif pinned_version and pinned_version not in local_version:
            toolchain[tool] = {"local": local_version, "ci": pinned_version, "match": False}
            mismatched.append(tool)
        else:
            toolchain[tool] = {"local": local_version, "ci": pinned_version, "match": True}

    final_exit = 1 if mismatched else 0
    summary = f"parity mismatch: {', '.join(mismatched)}" if mismatched else f"parity OK for {len(tools)} tool(s)"
    data = {
        "argv": argv, "cwd": str(repo_root), "head": head, "exit": final_exit,
        "summary": summary, "toolchain": toolchain,
    }
    override = _write_gate_and_receipt(run_dir, "7", role, data, "env-parity", final_exit, summary)
    if override is not None:
        return override
    if mismatched:
        print(f"ERROR: {summary}", file=sys.stderr)
    return final_exit


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------

_PYTEST_PATTERNS = {
    "passed": r'(\d+)\s+passed',
    "failed": r'(\d+)\s+failed',
    "skipped": r'(\d+)\s+skipped',
    "errors": r'(\d+)\s+error',
}


def _parse_pytest_summary(output: str) -> Dict[str, int]:
    def _count(pattern: str) -> int:
        match = re.search(pattern, output)
        return int(match.group(1)) if match else 0

    return {key: _count(pattern) for key, pattern in _PYTEST_PATTERNS.items()}


def _pytest_summary_present(output: str) -> bool:
    """True when output contains at least one pytest-shaped `N <word>` count line."""
    return any(re.search(pattern, output) for pattern in _PYTEST_PATTERNS.values())


def _parse_unittest_summary(output: str) -> Optional[Dict[str, int]]:
    """Parse unittest's `Ran N tests` / `OK` / `FAILED (...)` summary shape.

    Returns None when no `Ran N tests?` line is present (this output is not
    unittest-shaped). Otherwise: a following `OK` line gives passed = total,
    failed = 0, skipped = 0; a following `OK (skipped=S)` line gives
    skipped = S and passed = total - S; a following `FAILED (...)` line carries
    comma-separated `failures=F, errors=E, skipped=S, expected failures=X,
    unexpected successes=U` (any subset, defaulting missing keys to 0), and then
    failed = F + E + U, skipped = S, passed = total - failed - skipped - X.
    """
    ran_match = re.search(r'^Ran (\d+) tests?\b', output, re.MULTILINE)
    if not ran_match:
        return None
    total = int(ran_match.group(1))
    rest = output[ran_match.end():]

    failed_match = re.search(r'^FAILED \((.*)\)\s*$', rest, re.MULTILINE)
    if failed_match:
        counts: Dict[str, int] = {}
        for part in failed_match.group(1).split(","):
            key, sep, value = part.strip().partition("=")
            if sep and value.strip().isdigit():
                counts[key.strip()] = int(value.strip())
        failures = counts.get("failures", 0)
        errors = counts.get("errors", 0)
        skipped = counts.get("skipped", 0)
        expected_failures = counts.get("expected failures", 0)
        unexpected_successes = counts.get("unexpected successes", 0)
        failed = failures + errors + unexpected_successes
        passed = total - failed - skipped - expected_failures
        return {"passed": passed, "failed": failed, "skipped": skipped, "errors": errors}

    ok_match = re.search(r'^OK(?:\s+\(skipped=(\d+)\))?\s*$', rest, re.MULTILINE)
    if ok_match:
        skipped = int(ok_match.group(1)) if ok_match.group(1) else 0
        return {"passed": total - skipped, "failed": 0, "skipped": skipped, "errors": 0}

    return None


def _parse_test_summary(output: str) -> Dict[str, Any]:
    """Parse combined stdout+stderr into a shape-tagged test summary.

    Recognizes pytest's `N passed`/`N failed`/`N skipped`/`N error(s)` count-line
    shape and unittest's `Ran N tests` + `OK`/`FAILED (...)` shape. When both shapes
    are present in the same output (a pytest run may print unittest-looking lines
    from a wrapped runner) the pytest shape wins. Returns a dict with passed,
    failed, skipped, errors, and shape: "pytest", "unittest", or "none" when
    neither shape is recognized.
    """
    if _pytest_summary_present(output):
        parsed = _parse_pytest_summary(output)
        parsed["shape"] = "pytest"
        return parsed

    unittest_parsed = _parse_unittest_summary(output)
    if unittest_parsed is not None:
        unittest_parsed["shape"] = "unittest"
        return unittest_parsed

    return {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "shape": "none"}


def _commands_from_discover(discover_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return discover's commands list, falling back to its single top-level argv."""
    commands = discover_data.get("commands")
    if commands:
        return commands
    argv = discover_data.get("argv")
    if argv:
        return [{"argv": argv, "source": discover_data.get("source"),
                 "sourceLine": discover_data.get("sourceLine")}]
    return []


def cmd_run(repo_root_arg: str, role: str) -> int:
    ctx = _resolve_context(repo_root_arg)
    if ctx is None:
        return 2
    repo_root, run_dir, head = ctx

    discover_data = _read_discover(run_dir, role, head)
    if discover_data is None:
        return 2

    commands = _commands_from_discover(discover_data)
    if not commands:
        print("ERROR: discover file has no argv", file=sys.stderr)
        return 2

    results: List[Dict[str, Any]] = []
    for command in commands:
        argv = command["argv"]
        try:
            result = subprocess.run(argv, cwd=str(repo_root), capture_output=True, text=True, timeout=600)
        except FileNotFoundError:
            summary = f"runner not found: {argv[0]}"
            results.append({"argv": argv, "real_exit": None, "summary": None})
            data = {
                "argv": commands[0]["argv"], "cwd": str(repo_root), "head": head, "exit": 2,
                "summary": summary, "commands": results,
            }
            override = _write_gate_and_receipt(run_dir, "8", role, data, "test-execution", 2, summary)
            if override is not None:
                return override
            print(f"ERROR: {summary}", file=sys.stderr)
            return 2
        except OSError as exc:
            print(f"ERROR: cannot execute {argv[0]}: {exc}", file=sys.stderr)
            return 2

        real_exit = result.returncode
        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        parsed = _parse_test_summary(combined)
        if parsed["shape"] == "none" and _is_pytest_command(argv):
            # A pytest-invoked command whose output matched neither summary shape
            # (e.g. "no tests ran") is still a pytest result: all-zero counts, which
            # blocks below as "no tests collected" rather than being ignored.
            parsed = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0, "shape": "pytest"}
        no_tests_collected = (parsed["shape"] != "none" and parsed["passed"] == 0
                               and parsed["failed"] == 0 and parsed["skipped"] == 0
                               and parsed["errors"] == 0)
        command_summary = dict(parsed)
        command_summary["no_tests_collected"] = no_tests_collected
        results.append({"argv": argv, "real_exit": real_exit, "summary": command_summary})

    reasons: List[str] = []
    for entry in results:
        argv_text = " ".join(entry["argv"])
        summary = entry["summary"]
        if summary is not None:
            if summary["no_tests_collected"]:
                reasons.append(f"{argv_text}: no tests collected")
                continue
            if summary["failed"] > 0 or summary["skipped"] > 0 or summary["errors"] > 0:
                reasons.append(f"{argv_text}: {summary['passed']} passed, {summary['skipped']} skipped, "
                                f"{summary['failed']} failed, {summary['errors']} errors")
                continue
        if entry["real_exit"] != 0:
            reasons.append(f"{argv_text} exited {entry['real_exit']}")

    final_exit = 1 if reasons else 0
    summary_text = "; ".join(reasons) if reasons else f"{len(results)} command(s) passed"
    first_summary = results[0]["summary"] if results else None

    data = {
        "argv": commands[0]["argv"], "cwd": str(repo_root), "head": head, "exit": final_exit,
        "summary": summary_text, "parsed": first_summary,
        "real_exit": results[0]["real_exit"] if results else None,
        "commands": results,
    }
    override = _write_gate_and_receipt(run_dir, "8", role, data, "test-execution", final_exit, summary_text)
    if override is not None:
        return override
    if final_exit != 0:
        print(f"ERROR: {summary_text}", file=sys.stderr)
    return final_exit


# ---------------------------------------------------------------------------
# coverage
# ---------------------------------------------------------------------------

def cmd_coverage(repo_root_arg: str, role: str) -> int:
    ctx = _resolve_context(repo_root_arg)
    if ctx is None:
        return 2
    repo_root, run_dir, head = ctx

    discover_data = _read_discover(run_dir, role, head)
    if discover_data is None:
        return 2

    commands = _commands_from_discover(discover_data)
    pytest_argv = None
    for command in commands:
        if _is_pytest_command(command.get("argv") or []):
            pytest_argv = command["argv"]
            break

    if pytest_argv is None:
        reason = "no pytest command among the discovered commands"
        summary = f"NOT_APPLICABLE: {reason}"
        data = {"argv": None, "cwd": str(repo_root), "head": head, "exit": 2,
                "summary": summary, "status": "NOT_APPLICABLE", "reason": reason}
        override = _write_gate_and_receipt(run_dir, "10", role, data, "coverage", 2, summary)
        if override is not None:
            return override
        print(f"ERROR: {summary}", file=sys.stderr)
        return 2

    cov_argv = pytest_argv + ["--cov", "--cov-branch"]
    try:
        result = subprocess.run(cov_argv, cwd=str(repo_root), capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        print(f"ERROR: runner not found: {cov_argv[0]}", file=sys.stderr)
        return 2

    combined = (result.stdout or "") + "\n" + (result.stderr or "")

    if "unrecognized arguments: --cov" in combined or "No module named 'pytest_cov'" in combined:
        reason = "coverage plugin unavailable"
        summary = f"UNVERIFIED: {reason}"
        data = {"argv": cov_argv, "cwd": str(repo_root), "head": head, "exit": 1,
                "summary": summary, "status": "UNVERIFIED", "reason": reason}
        override = _write_gate_and_receipt(run_dir, "10", role, data, "coverage", 1, summary)
        if override is not None:
            return override
        print(f"ERROR: {summary}", file=sys.stderr)
        return 1

    match = re.search(r'^TOTAL\b.*?(\d+)%', combined, re.MULTILINE)
    if not match:
        reason = "no coverage total line found"
        summary = f"UNVERIFIED: {reason}"
        data = {"argv": cov_argv, "cwd": str(repo_root), "head": head, "exit": 1,
                "summary": summary, "status": "UNVERIFIED", "reason": reason}
        override = _write_gate_and_receipt(run_dir, "10", role, data, "coverage", 1, summary)
        if override is not None:
            return override
        print(f"ERROR: {summary}", file=sys.stderr)
        return 1

    pct = int(match.group(1))
    summary = f"coverage {pct}%"
    data = {"argv": cov_argv, "cwd": str(repo_root), "head": head, "exit": 0,
            "summary": summary, "status": "MEASURED", "pct": pct}
    override = _write_gate_and_receipt(run_dir, "10", role, data, "coverage", 0, summary)
    if override is not None:
        return override
    return 0


# ---------------------------------------------------------------------------
# evidence
# ---------------------------------------------------------------------------

def cmd_evidence(repo_root_arg: str, role: str) -> int:
    if role == "verifier":
        print("ERROR: evidence is assembled from the builder's gates only", file=sys.stderr)
        return 2

    ctx = _resolve_context(repo_root_arg)
    if ctx is None:
        return 2
    repo_root, run_dir, head = ctx

    gates_dir = run_dir / "gates"
    if not gates_dir.is_dir():
        print("ERROR: no gates directory found; run discover/parity/run/coverage first", file=sys.stderr)
        return 2

    entries: List[Dict[str, Any]] = []
    for gate_file in sorted(gates_dir.glob("*.json")):
        if gate_file.name.endswith("-verifier.json"):
            continue
        try:
            data = json.loads(gate_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        base = gate_file.stem
        exit_code = data.get("exit")
        if exit_code == 0:
            verdict = "PASS"
        elif exit_code == 1:
            verdict = "BLOCK"
        else:
            verdict = "UNVERIFIED"
        detail = {k: v for k, v in data.items() if k not in ("argv", "cwd", "head", "exit", "summary")}
        entries.append({
            "id": f"E{len(entries) + 1}",
            "gate": GATE_NAME_MAP.get(base, base),
            "verdict": verdict,
            "exit": exit_code,
            "head": data.get("head"),
            "command": {"argv": data.get("argv"), "cwd": data.get("cwd")},
            "summary": data.get("summary"),
            "detail": detail,
        })

    if not entries:
        print("ERROR: no gate files found; run discover/parity/run/coverage first", file=sys.stderr)
        return 2

    run_id = None
    run_json = run_dir / "run.json"
    if run_json.is_file():
        try:
            run_id = json.loads(run_json.read_text(encoding="utf-8")).get("run_id")
        except (OSError, json.JSONDecodeError):
            run_id = None

    evidence_dict = {"schemaVersion": "1.0", "head": head, "runId": run_id, "entries": entries}
    evidence_json_bytes = (json.dumps(evidence_dict, indent=2, sort_keys=True) + "\n").encode("utf-8")

    team_ship_dir = repo_root / ".team-ship"
    override = _write_artifact_and_receipt(run_dir, team_ship_dir / "EVIDENCE.json",
                                            ".team-ship/EVIDENCE.json", evidence_json_bytes)
    if override is not None:
        return override

    try:
        import render_evidence
    except ImportError as exc:
        print(f"ERROR: render_evidence import failed: {exc}", file=sys.stderr)
        return 2

    render_fn = getattr(render_evidence, "render", None)
    if render_fn is None:
        print("ERROR: render_evidence.render is not defined", file=sys.stderr)
        return 2

    try:
        md_text = render_fn(evidence_dict)
    except Exception as exc:
        print(f"ERROR: render_evidence.render raised: {exc}", file=sys.stderr)
        return 2

    if not isinstance(md_text, str):
        print("ERROR: render_evidence.render did not return a string", file=sys.stderr)
        return 2

    evidence_md_bytes = md_text.encode("utf-8")
    override = _write_artifact_and_receipt(run_dir, team_ship_dir / "EVIDENCE.md",
                                            ".team-ship/EVIDENCE.md", evidence_md_bytes)
    if override is not None:
        return override
    return 0


# ---------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------

def _isolated_fixture_copy(build_dir: Path, name: str):
    tmp_root = Path(tempfile.mkdtemp(prefix=f"run_gate_{name}_"))
    copy_path = tmp_root / name
    shutil.copytree(build_dir / name, copy_path)
    state_root = tmp_root / "state"
    state_root.mkdir()
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(state_root)
    os.environ["TEAM_STATE_ROOT"] = str(state_root)
    gate_state.start_run(str(copy_path), "test", [])
    return copy_path, env


def _invoke(copy_path: Path, env: Dict[str, str], *args: str):
    rest = ["--repo-root", str(copy_path)] + list(args)
    return subprocess.run([sys.executable, __file__] + rest,
                           cwd=str(copy_path), env=env, capture_output=True, text=True, timeout=60)


def _with_stub_on_path(env: Dict[str, str], copy_path: Path) -> Dict[str, str]:
    merged = dict(env)
    merged["PATH"] = f"{copy_path / 'bin'}{os.pathsep}{merged.get('PATH', '')}"
    return merged


def _with_restricted_path(env: Dict[str, str]) -> Dict[str, str]:
    merged = dict(env)
    merged["PATH"] = f"{os.sep}usr{os.sep}bin{os.pathsep}{os.sep}bin"
    return merged


def cmd_self_test() -> int:
    fixtures_dir = Path(__file__).resolve().parent / "fixtures" / "run_gate"
    build_dir = fixtures_dir / "_build"
    make_fixtures = fixtures_dir / "make_fixtures.py"

    if not build_dir.is_dir():
        result = subprocess.run([sys.executable, str(make_fixtures)], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"make_fixtures.py failed: {result.stderr}", file=sys.stderr)
            return 2

    all_ok = True

    # no-ci-config: discover -> 2
    copy_path, env = _isolated_fixture_copy(build_dir, "no-ci-config")
    proc = _invoke(copy_path, env, "discover")
    ok = proc.returncode == 2
    all_ok = all_ok and ok
    print(f"no-ci-config: expected 2 got {proc.returncode} {'OK' if ok else 'FAIL'}")

    # lint-and-test: discover -> 0, gates/7-discover.json argv[0] is pytest, never ruff
    copy_path, env = _isolated_fixture_copy(build_dir, "lint-and-test")
    proc = _invoke(copy_path, env, "discover")
    ok = proc.returncode == 0
    if ok:
        run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
        gate_path = run_dir / "gates" / "7-discover.json"
        ok = gate_path.is_file()
        if ok:
            argv0 = json.loads(gate_path.read_text()).get("argv", [None])[0]
            ok = argv0 == "pytest"
    all_ok = all_ok and ok
    print(f"lint-and-test: expected 0 got {proc.returncode} argv[0]=pytest {'OK' if ok else 'FAIL'}")

    # all-pass: discover then run -> 0
    copy_path, env = _isolated_fixture_copy(build_dir, "all-pass")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, _with_stub_on_path(env, copy_path), "run")
    ok = proc.returncode == 0
    all_ok = all_ok and ok
    print(f"all-pass: expected 0 got {proc.returncode} {'OK' if ok else 'FAIL'}")

    # one-fail: discover then run -> 1, stderr contains "failed"
    copy_path, env = _isolated_fixture_copy(build_dir, "one-fail")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, _with_stub_on_path(env, copy_path), "run")
    ok = proc.returncode == 1 and "failed" in proc.stderr
    all_ok = all_ok and ok
    print(f"one-fail: expected 1 got {proc.returncode} stderr contains 'failed' {'OK' if ok else 'FAIL'}")

    # one-skip: discover then run -> 1, stderr contains "skipped"
    copy_path, env = _isolated_fixture_copy(build_dir, "one-skip")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, _with_stub_on_path(env, copy_path), "run")
    ok = proc.returncode == 1 and "skipped" in proc.stderr
    all_ok = all_ok and ok
    print(f"one-skip: expected 1 got {proc.returncode} stderr contains 'skipped' {'OK' if ok else 'FAIL'}")

    # unittest-all-pass: discover then run -> 0, summary shape unittest, passed 3
    copy_path, env = _isolated_fixture_copy(build_dir, "unittest-all-pass")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, env, "run")
    ok = proc.returncode == 0
    shape = passed = None
    if ok:
        run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
        gate_path = run_dir / "gates" / "8.json"
        ok = gate_path.is_file()
        if ok:
            data = json.loads(gate_path.read_text())
            summary = (data.get("commands") or [{}])[0].get("summary") or {}
            shape = summary.get("shape")
            passed = summary.get("passed")
            ok = shape == "unittest" and passed == 3
    all_ok = all_ok and ok
    print(f"unittest-all-pass: expected 0 got {proc.returncode} shape={shape} passed={passed} "
          f"{'OK' if ok else 'FAIL'}")

    # unittest-one-fail: discover then run -> 1, stderr contains "failed"
    copy_path, env = _isolated_fixture_copy(build_dir, "unittest-one-fail")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, env, "run")
    ok = proc.returncode == 1 and "failed" in proc.stderr
    all_ok = all_ok and ok
    print(f"unittest-one-fail: expected 1 got {proc.returncode} stderr contains 'failed' {'OK' if ok else 'FAIL'}")

    # unittest-skip: discover then run -> 1, stderr contains "skipped"
    copy_path, env = _isolated_fixture_copy(build_dir, "unittest-skip")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, env, "run")
    ok = proc.returncode == 1 and "skipped" in proc.stderr
    all_ok = all_ok and ok
    print(f"unittest-skip: expected 1 got {proc.returncode} stderr contains 'skipped' {'OK' if ok else 'FAIL'}")

    # unittest-zero: discover then run -> 1, stderr contains "no tests collected"
    copy_path, env = _isolated_fixture_copy(build_dir, "unittest-zero")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, env, "run")
    ok = proc.returncode == 1 and "no tests collected" in proc.stderr
    all_ok = all_ok and ok
    print(f"unittest-zero: expected 1 got {proc.returncode} stderr contains 'no tests collected' "
          f"{'OK' if ok else 'FAIL'}")

    # pytest-wins: discover then run -> 0, summary shape pytest, passed 2 (pytest shape
    # wins over the unittest-looking lines the same script also prints)
    copy_path, env = _isolated_fixture_copy(build_dir, "pytest-wins")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, env, "run")
    ok = proc.returncode == 0
    shape = passed = None
    if ok:
        run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
        gate_path = run_dir / "gates" / "8.json"
        ok = gate_path.is_file()
        if ok:
            data = json.loads(gate_path.read_text())
            summary = (data.get("commands") or [{}])[0].get("summary") or {}
            shape = summary.get("shape")
            passed = summary.get("passed")
            ok = shape == "pytest" and passed == 2
    all_ok = all_ok and ok
    print(f"pytest-wins: expected 0 got {proc.returncode} shape={shape} passed={passed} {'OK' if ok else 'FAIL'}")

    # parity-mismatch: discover then parity -> 1, stderr contains "ruff"
    copy_path, env = _isolated_fixture_copy(build_dir, "parity-mismatch")
    _invoke(copy_path, _with_stub_on_path(env, copy_path), "discover")
    proc = _invoke(copy_path, _with_stub_on_path(env, copy_path), "parity")
    ok = proc.returncode == 1 and "ruff" in proc.stderr
    all_ok = all_ok and ok
    print(f"parity-mismatch: expected 1 got {proc.returncode} stderr contains 'ruff' {'OK' if ok else 'FAIL'}")

    # runner-absent: discover then run with PATH restricted -> 2
    copy_path, env = _isolated_fixture_copy(build_dir, "runner-absent")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, _with_restricted_path(env), "run")
    ok = proc.returncode == 2
    all_ok = all_ok and ok
    print(f"runner-absent: expected 2 got {proc.returncode} {'OK' if ok else 'FAIL'}")

    # multiline-run-block: a `run: |` block whose first line is `set -e`; discover must
    # scan every line of the block and select the pytest line, not the first line.
    copy_path, env = _isolated_fixture_copy(build_dir, "multiline-run-block")
    proc = _invoke(copy_path, env, "discover")
    ok = proc.returncode == 0
    if ok:
        run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
        gate_path = run_dir / "gates" / "7-discover.json"
        ok = gate_path.is_file()
        if ok:
            argv0 = json.loads(gate_path.read_text()).get("argv", [None])[0]
            ok = argv0 == "pytest"
    all_ok = all_ok and ok
    print(f"multiline-run-block: expected 0 got {proc.returncode} argv[0]=pytest {'OK' if ok else 'FAIL'}")

    # only-install-steps: every run: block is pip install or echo; no runner line
    # anywhere, so discover must exit 2, never select an install line.
    copy_path, env = _isolated_fixture_copy(build_dir, "only-install-steps")
    proc = _invoke(copy_path, env, "discover")
    ok = proc.returncode == 2
    all_ok = all_ok and ok
    print(f"only-install-steps: expected 2 got {proc.returncode} {'OK' if ok else 'FAIL'}")

    # no-tests-ran: the stub prints "no tests ran in 0.01s" and exits 0; run_gate.py
    # must never treat zero-everything as a pass.
    copy_path, env = _isolated_fixture_copy(build_dir, "no-tests-ran")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, _with_stub_on_path(env, copy_path), "run")
    ok = proc.returncode == 1 and "no tests collected" in proc.stderr
    all_ok = all_ok and ok
    print(f"no-tests-ran: expected 1 got {proc.returncode} stderr contains 'no tests collected' {'OK' if ok else 'FAIL'}")

    # unwritable-run-dir: chmod 000 the run directory itself; discover must fail closed
    # with exit 2 and exactly one stderr line, never a traceback.
    copy_path, env = _isolated_fixture_copy(build_dir, "all-pass")
    run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
    os.chmod(run_dir, 0o000)
    try:
        proc = _invoke(copy_path, env, "discover")
    finally:
        os.chmod(run_dir, 0o755)
    stderr_lines = [ln for ln in proc.stderr.splitlines() if ln.strip()]
    ok = proc.returncode == 2 and len(stderr_lines) == 1
    all_ok = all_ok and ok
    print(f"unwritable-run-dir: expected 2 got {proc.returncode} stderr_lines={len(stderr_lines)} {'OK' if ok else 'FAIL'}")

    # receipts-unwritable: the gate file itself is writable, but receipts.jsonl is not;
    # discover must fail closed with exit 2, one stderr line, and roll back the gate
    # file it had just written so no gate file exists without its receipt.
    copy_path, env = _isolated_fixture_copy(build_dir, "all-pass")
    run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
    receipts_file = run_dir / "receipts.jsonl"
    receipts_file.write_text("")
    os.chmod(receipts_file, 0o000)
    try:
        proc = _invoke(copy_path, env, "discover")
    finally:
        os.chmod(receipts_file, 0o644)
    stderr_lines = [ln for ln in proc.stderr.splitlines() if ln.strip()]
    gate_path = run_dir / "gates" / "7-discover.json"
    ok = proc.returncode == 2 and len(stderr_lines) == 1 and not gate_path.exists()
    all_ok = all_ok and ok
    print(f"receipts-unwritable: expected 2 got {proc.returncode} stderr_lines={len(stderr_lines)} "
          f"gate_rolled_back={not gate_path.exists()} {'OK' if ok else 'FAIL'}")

    # evidence: run_gate.py evidence is the only writer of EVIDENCE.json, so this must
    # be a real end-to-end check, not merely described.
    copy_path, env = _isolated_fixture_copy(build_dir, "all-pass")
    _invoke(copy_path, env, "discover")
    _invoke(copy_path, _with_stub_on_path(env, copy_path), "run")
    proc = _invoke(copy_path, env, "evidence")
    ok = proc.returncode == 0
    all_ok = all_ok and ok
    if ok:
        print("evidence: expected 0 got 0 OK")
    else:
        print(f"evidence: expected 0 got {proc.returncode} FAIL ({proc.stderr.strip()})")

    # evidence-runid: EVIDENCE.json must carry the run's own run_id from run.json, so
    # render_evidence.py can print it. Reuses the run just created above.
    runid_ok = False
    if proc.returncode == 0:
        run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
        run_json = run_dir / "run.json"
        evidence_json = copy_path / ".team-ship" / "EVIDENCE.json"
        if run_json.is_file() and evidence_json.is_file():
            expected_run_id = json.loads(run_json.read_text()).get("run_id")
            actual_run_id = json.loads(evidence_json.read_text()).get("runId")
            runid_ok = expected_run_id is not None and expected_run_id == actual_run_id
    all_ok = all_ok and runid_ok
    print(f"evidence-runid: expected match got {'match' if runid_ok else 'mismatch'} {'OK' if runid_ok else 'FAIL'}")

    # multi-command-step: one step, two commands (bash + python3 --self-test), both
    # exit 0; discover must record both, run must execute both.
    copy_path, env = _isolated_fixture_copy(build_dir, "multi-command-step")
    proc_discover = _invoke(copy_path, env, "discover")
    run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
    discover_commands = 0
    if proc_discover.returncode == 0:
        gate_path = run_dir / "gates" / "7-discover.json"
        if gate_path.is_file():
            discover_commands = len(json.loads(gate_path.read_text()).get("commands", []))
    proc_run = _invoke(copy_path, env, "run")
    run_commands = 0
    if proc_run.returncode == 0:
        gate_path = run_dir / "gates" / "8.json"
        if gate_path.is_file():
            run_commands = len(json.loads(gate_path.read_text()).get("commands", []))
    ok = (proc_discover.returncode == 0 and discover_commands == 2
          and proc_run.returncode == 0 and run_commands == 2)
    all_ok = all_ok and ok
    print(f"multi-command-step: expected 0/0 got {proc_discover.returncode}/{proc_run.returncode} "
          f"discover_commands={discover_commands} run_commands={run_commands} {'OK' if ok else 'FAIL'}")

    # multi-command-one-fails: same two commands, but the second exits 3; run must
    # name the failing argv.
    copy_path, env = _isolated_fixture_copy(build_dir, "multi-command-one-fails")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, env, "run")
    ok = proc.returncode == 1 and "check.py" in proc.stderr
    all_ok = all_ok and ok
    print(f"multi-command-one-fails: expected 1 got {proc.returncode} stderr names failing argv {'OK' if ok else 'FAIL'}")

    # coverage-not-applicable: discover finds only a bash test script, no pytest
    # command; coverage must be NOT_APPLICABLE, exit 2, never 0 and never a plain 1.
    copy_path, env = _isolated_fixture_copy(build_dir, "coverage-not-applicable")
    _invoke(copy_path, env, "discover")
    proc = _invoke(copy_path, env, "coverage")
    ok = proc.returncode == 2 and "NOT_APPLICABLE" in proc.stderr
    all_ok = all_ok and ok
    print(f"coverage-not-applicable: expected 2 got {proc.returncode} stderr contains 'NOT_APPLICABLE' "
          f"{'OK' if ok else 'FAIL'}")

    # shell-operator-line: a step with `bash tests/check-x.sh || true` and a plain
    # `pytest -q`; the first is unrunnable without a shell and must be skipped, the
    # second must be chosen. discover 0 with one command and one skipped entry.
    copy_path, env = _isolated_fixture_copy(build_dir, "shell-operator-line")
    proc = _invoke(copy_path, env, "discover")
    ok = proc.returncode == 0
    if ok:
        run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
        gate_path = run_dir / "gates" / "7-discover.json"
        ok = gate_path.is_file()
        if ok:
            data = json.loads(gate_path.read_text())
            ok = len(data.get("commands", [])) == 1 and len(data.get("skipped", [])) == 1
    all_ok = all_ok and ok
    print(f"shell-operator-line: expected 0 got {proc.returncode} commands=1 skipped=1 {'OK' if ok else 'FAIL'}")

    # shell-operator-only: only the `|| true` line; zero commands survive, exit 2.
    copy_path, env = _isolated_fixture_copy(build_dir, "shell-operator-only")
    proc = _invoke(copy_path, env, "discover")
    ok = proc.returncode == 2
    all_ok = all_ok and ok
    print(f"shell-operator-only: expected 2 got {proc.returncode} {'OK' if ok else 'FAIL'}")

    # stale-discover-head: discover, then a new commit in the fixture repo changes
    # HEAD, then run must refuse the stale discovery, exit 2, naming both SHAs.
    copy_path, env = _isolated_fixture_copy(build_dir, "all-pass")
    _invoke(copy_path, env, "discover")
    run_dir = next(Path(env["TEAM_STATE_ROOT"]).glob("*"))
    old_gate_path = run_dir / "gates" / "7-discover.json"
    old_head = json.loads(old_gate_path.read_text()).get("head") if old_gate_path.is_file() else None
    (copy_path / "NEWFILE.txt").write_text("stale head test\n")
    subprocess.run(["git", "add", "-A"], cwd=str(copy_path), capture_output=True, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "stale"], cwd=str(copy_path), capture_output=True, check=True)
    new_head_proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(copy_path),
                                    capture_output=True, text=True, check=True)
    new_head = new_head_proc.stdout.strip()
    proc = _invoke(copy_path, _with_stub_on_path(env, copy_path), "run")
    ok = (proc.returncode == 2 and old_head is not None
          and old_head in proc.stderr and new_head in proc.stderr)
    all_ok = all_ok and ok
    print(f"stale-discover-head: expected 2 got {proc.returncode} old_sha_in_stderr="
          f"{old_head in proc.stderr if old_head else False} new_sha_in_stderr={new_head in proc.stderr} "
          f"{'OK' if ok else 'FAIL'}")

    return 0 if all_ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--role", choices=["builder", "verifier"], default="builder",
                         help="builder writes gates/<n>.json, verifier writes gates/<n>-verifier.json")
    parser.add_argument("--self-test", action="store_true", help="run self-test on fixtures")
    subparsers = parser.add_subparsers(dest="subcommand")
    for subparser_name in ["discover", "parity", "run", "coverage", "evidence"]:
        subparser = subparsers.add_parser(subparser_name)
        subparser.add_argument("--repo-root", default=None, dest="sub_repo_root",
                               help="repository root (overrides parent --repo-root)")
        subparser.add_argument("--role", choices=["builder", "verifier"], default=None, dest="sub_role",
                               help="builder|verifier (overrides parent --role)")

    args = parser.parse_args()

    if args.self_test:
        return cmd_self_test()

    dispatch = {
        "discover": cmd_discover,
        "parity": cmd_parity,
        "run": cmd_run,
        "coverage": cmd_coverage,
        "evidence": cmd_evidence,
    }
    if not args.subcommand:
        parser.print_help()
        return 2

    # Resolve --repo-root: prefer subparser value, then parent value, then default
    repo_root_from_parent = args.repo_root
    repo_root_from_sub = getattr(args, "sub_repo_root", None)
    if repo_root_from_parent != "." and repo_root_from_sub is not None and repo_root_from_parent != repo_root_from_sub:
        sys.stderr.write(f"--repo-root given twice with different values\n")
        return 2
    final_repo_root = repo_root_from_sub if repo_root_from_sub is not None else repo_root_from_parent

    # Resolve --role: prefer subparser value, then parent value, then default
    role_from_parent = args.role
    role_from_sub = getattr(args, "sub_role", None)
    if role_from_parent != "builder" and role_from_sub is not None and role_from_parent != role_from_sub:
        sys.stderr.write(f"--role given twice with different values\n")
        return 2
    final_role = role_from_sub if role_from_sub is not None else role_from_parent

    return dispatch[args.subcommand](final_repo_root, final_role)


if __name__ == "__main__":
    sys.exit(main())
