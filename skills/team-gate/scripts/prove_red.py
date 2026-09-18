#!/usr/bin/env python3
"""TDD red-green proof for Stage 9: every new test is red without the implementation, green with it.

Subcommands:
  enumerate --base <commit> --repo-root <dir>: list every test function added or
             modified between base and HEAD.
  prove --base <commit> --repo-root <dir> [--allow-dirty] [--python <path>]:
             enumerate, then for each runnable test, run it green at HEAD in a
             throwaway detached worktree, revert implementation paths in that
             worktree, and run it again to prove it goes red for the right reason.
  recheck --repo-root <dir>: re-hash every test recorded as PASS in gates/9.json
             at the current HEAD; a changed or removed test is a finding.
  _run-one SYS_PATH_ROOT TEST_FILE QUALNAME: internal, invoked by prove as a
             subprocess to import one test module and call one test function.
  --self-test: regenerate fixtures and assert prove's behavior on each, through
             the CLI subprocess only.

Exit contract: 0 = PASS, 1 = BLOCK, 2 = UNRUNNABLE.

Runner. There is no pytest and no coverage on this machine. Every test function is
run directly, in its own subprocess, through _run-one. A test function that takes
required parameters cannot be run without a fixture-aware runner and is reported
UNRUNNABLE. Fixture-aware execution and coverage attribution are deferred.

Never mutates the caller's worktree. All git writes (checkout, apply, worktree
add/remove/prune) happen either as read-only queries against the repository root
through gr(), or as writes scoped to a throwaway detached worktree through gw(),
which refuses to run against the repository root.
"""

import argparse
import ast
import asyncio
import atexit
import hashlib
import importlib.util
import inspect
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_state


class GateExit(Exception):
    """Raised internally to unwind to a single exit point with one stderr line."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


_GR_ALLOWED_VERBS = {
    "rev-parse", "merge-base", "diff", "ls-files", "status",
    "cat-file", "show", "symbolic-ref", "worktree",
}

_IMPORT_ERROR_RE = re.compile(r"cannot import name '(?P<name>\w+)' from '(?P<mod>[\w.]+)'")
_ATTR_ERROR_RE = re.compile(r"module '(?P<mod>[\w.]+)' has no attribute '(?P<name>\w+)'")


def gr(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    """Run a read-only git command against the measured repository.

    Refuses any verb outside the allowlist before subprocess is called, which is
    what makes it impossible for this function to mutate the caller's worktree.
    worktree is allowed because add, remove, prune and list operate on git
    metadata and the throwaway directory, never on the caller's tracked files.
    """
    if not args or args[0] not in _GR_ALLOWED_VERBS:
        raise ValueError(f"git verb not allowed for gr: {args[0] if args else '<empty>'}")
    return subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, text=True, timeout=60)


def gw(worktree: Path, repo_root: Path, *args: str, input_text: Optional[str] = None) -> subprocess.CompletedProcess:
    """Run a git command against the throwaway worktree. Refuses to run against repo_root."""
    if os.path.realpath(str(worktree)) == os.path.realpath(str(repo_root)):
        raise ValueError("gw refuses to operate on repo_root")
    return subprocess.run(
        ["git", "-C", str(worktree), *args],
        input=input_text, capture_output=True, text=True, timeout=60,
    )


def resolve_base(repo_root: Path, explicit: Optional[str]) -> Tuple[str, str]:
    """Resolve the base commit for diffing. Returns (sha, source).

    Order: the explicit argument; .team-ship/ARCH-PLAN.json declaredAtCommit;
    merge-base against origin/HEAD; HEAD~1 when there is no remote at all.
    Raises GateExit(2, ...) when none resolves.
    """
    if explicit:
        proc = gr(repo_root, "rev-parse", "--verify", f"{explicit}^{{commit}}")
        if proc.returncode != 0:
            raise GateExit(2, f"base {explicit} does not resolve")
        return proc.stdout.strip(), "explicit"

    arch_plan = repo_root / ".team-ship" / "ARCH-PLAN.json"
    if arch_plan.is_file():
        try:
            obj = json.loads(arch_plan.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            obj = {}
        declared = obj.get("declaredAtCommit")
        if declared:
            return declared, "arch-plan"

    sym_proc = gr(repo_root, "symbolic-ref", "-q", "refs/remotes/origin/HEAD")
    if sym_proc.returncode == 0:
        remote_ref = sym_proc.stdout.strip()
        mb_proc = gr(repo_root, "merge-base", "HEAD", remote_ref)
        if mb_proc.returncode == 0:
            return mb_proc.stdout.strip(), "merge-base"

    head_minus_one = gr(repo_root, "rev-parse", "--verify", "-q", "HEAD~1")
    if head_minus_one.returncode == 0:
        return head_minus_one.stdout.strip(), "head-minus-one"

    raise GateExit(2, "base unresolvable")


def changed_paths(repo_root: Path, base: str) -> List[Tuple[str, str, Optional[str]]]:
    """Return (status, path, old_path) tuples for the diff between base and HEAD."""
    proc = gr(repo_root, "diff", "--name-status", "-M", base, "HEAD")
    if proc.returncode != 0:
        raise GateExit(2, f"git diff failed: {proc.stderr.strip()}")
    results: List[Tuple[str, str, Optional[str]]] = []
    for line in proc.stdout.splitlines():
        if not line:
            continue
        fields = line.split("\t")
        status = fields[0][0]
        if status == "R":
            results.append((status, fields[2], fields[1]))
        else:
            results.append((status, fields[1], None))
    return results


def classify_path(path: str) -> str:
    """Classify a repository-relative path as test, support, or implementation."""
    basename = os.path.basename(path)
    segments = path.split("/")
    if basename == "conftest.py" or "fixtures" in segments or not path.endswith(".py"):
        return "support"
    if path.startswith("tests/") or path.startswith("test/"):
        return "test"
    if basename.startswith("test_") or basename.endswith("_test.py"):
        return "test"
    return "implementation"


def test_functions(source: str) -> Dict[str, ast.AST]:
    """Parse source and collect top-level test_* functions and Test*.test_* methods.

    A SyntaxError from ast.parse propagates to the caller.
    """
    tree = ast.parse(source)
    out: Dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            out[node.name] = node
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                    out[f"{node.name}.{item.name}"] = item
    return out


def ast_hash(node: ast.AST) -> str:
    """Hash a function AST, blind to comments, whitespace, and a leading docstring."""
    original_body = node.body
    body = list(original_body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    node.body = body
    try:
        dumped = ast.dump(node, annotate_fields=True, include_attributes=False)
    finally:
        node.body = original_body
    return hashlib.sha256(dumped.encode()).hexdigest()


def _count_params(node: ast.AST) -> int:
    """Count positional parameters of a function node, excluding a leading self."""
    args = node.args
    positional = list(args.posonlyargs) + list(args.args)
    if positional and positional[0].arg == "self":
        positional = positional[1:]
    return len(positional)


def write_gate(run_dir: Path, name: str, obj: Dict[str, Any]) -> Path:
    """Write a gate JSON file and append its gate-result receipt."""
    gates_dir = run_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    gate_path = gates_dir / name
    gate_path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")
    gate_sha256 = hashlib.sha256(gate_path.read_bytes()).hexdigest()
    gate_state.append_receipt(run_dir, "gate-result", {
        "gate": obj["gate"],
        "gate_file": f"gates/{name}",
        "gate_sha256": gate_sha256,
        "exit": obj["exit"],
        "summary": obj["summary"],
    })
    return gate_path


def do_enumerate(repo_root: Path, base: str, head: str,
                  changed: List[Tuple[str, str, Optional[str]]]) -> Dict[str, Any]:
    """Enumerate new or modified test functions between base and HEAD.

    Shared by the enumerate and prove commands. Raises GateExit(1, ...) when a
    changed .py file fails to parse at HEAD, and GateExit(2, ...) when a changed
    file cannot be read at HEAD.
    """
    tests: List[Dict[str, Any]] = []
    support_tests: List[Dict[str, Any]] = []
    implementation_paths: List[str] = []
    support_paths: List[str] = []

    for status, path, old_path in changed:
        if status not in ("A", "M", "R"):
            continue
        if not path.endswith(".py"):
            continue

        head_proc = gr(repo_root, "show", f"{head}:{path}")
        if head_proc.returncode != 0:
            raise GateExit(2, f"cannot read {path} at {head}")
        try:
            head_funcs = test_functions(head_proc.stdout)
        except SyntaxError:
            raise GateExit(1, f"syntax-error-at-head: {path}")

        base_funcs: Dict[str, ast.AST] = {}
        base_parses = False
        if status in ("M", "R"):
            base_path = old_path if old_path else path
            base_proc = gr(repo_root, "show", f"{base}:{base_path}")
            if base_proc.returncode == 0:
                try:
                    base_funcs = test_functions(base_proc.stdout)
                    base_parses = True
                except SyntaxError:
                    base_parses = False

        kind = classify_path(path)
        if kind == "implementation":
            implementation_paths.append(path)
        elif kind == "support":
            support_paths.append(path)

        for qualname, node in head_funcs.items():
            if status == "A":
                test_status = "new"
            elif not base_parses:
                test_status = "modified"
            elif qualname not in base_funcs:
                test_status = "new"
            elif ast_hash(node) == ast_hash(base_funcs[qualname]):
                continue
            else:
                test_status = "modified"

            entry = {
                "nodeid": f"{path}::{qualname}",
                "file": path,
                "qualname": qualname,
                "status": test_status,
                "kind": kind,
                "ast_hash": ast_hash(node),
                "params": _count_params(node),
            }

            if kind == "support":
                support_tests.append(entry)
            else:
                tests.append(entry)

    return {
        "tests": tests,
        "support_tests": support_tests,
        "implementation_paths": implementation_paths,
        "support_paths": support_paths,
    }


def _base_test_fields(t: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the enumeration-derived fields common to every test record."""
    return {
        "nodeid": t["nodeid"],
        "file": t["file"],
        "qualname": t["qualname"],
        "status": t["status"],
        "kind": t["kind"],
        "ast_hash": t["ast_hash"],
    }


def _zero_counts() -> Dict[str, int]:
    """Zeroed counts dict matching the gates/9.json counts schema."""
    return {
        "tests": 0, "pass": 0, "block": 0, "unverified": 0, "unrunnable": 0,
        "never_red": 0, "invalid_red": 0, "green_fails": 0, "inseparable": 0,
    }


def _remove_empty_parents(wt: Path, start: Path) -> None:
    """Remove now-empty parent directories up to the worktree root."""
    current = start
    while current != wt and current.is_dir() and not any(current.iterdir()):
        current.rmdir()
        current = current.parent


def _reap_stale_worktrees(repo_root: Path, run_dir: Path) -> None:
    """Remove red-* worktrees under run_dir/worktrees older than two hours."""
    worktrees_dir = run_dir / "worktrees"
    if worktrees_dir.is_dir():
        cutoff = time.time() - 2 * 3600
        for entry in worktrees_dir.iterdir():
            if entry.is_dir() and entry.name.startswith("red-") and entry.stat().st_mtime < cutoff:
                gr(repo_root, "worktree", "remove", "--force", str(entry))
                shutil.rmtree(entry, ignore_errors=True)
    gr(repo_root, "worktree", "prune")


def _run_one_subprocess(python: str, wt: Path, file: str, qualname: str) -> Dict[str, Any]:
    """Invoke _run-one in a subprocess. A missing or unparseable JSON result is UNRUNNABLE.

    Runs with PYTHONDONTWRITEBYTECODE=1 so the green run at HEAD never leaves a
    __pycache__ entry that the red run, moments later against reverted source of
    the same size, could read back as a stale, mtime-coincident cache hit.
    """
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        proc = subprocess.run(
            [python, __file__, "_run-one", str(wt), str(wt / file), qualname],
            capture_output=True, text=True, timeout=120, env=env,
        )
    except subprocess.TimeoutExpired:
        return {"outcome": "unrunnable", "phase": "call", "message": "runner timed out"}
    try:
        return json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        return {"outcome": "unrunnable", "phase": "call", "message": "runner produced no parseable JSON"}


def _relative_to_worktree(file_path: str, wt: Path) -> Optional[str]:
    """Return file_path relative to the worktree, or None if it falls outside it."""
    try:
        return str(Path(file_path).resolve().relative_to(wt.resolve()))
    except ValueError:
        return None


def classify_red(result: Dict[str, Any], wt: Path, added_impl: Set[str], modified_impl: Set[str],
                  repo_root: Path, base: str) -> Dict[str, Any]:
    """Classify one red-phase _run-one result into never-red, valid-red, or invalid-red.

    For an AssertionError, attribution walks the recorded frames from the last one
    backwards, skipping any frame whose file resolves outside the worktree (the
    standard library, site-packages, a pytest plugin's assertion rewrite hook), and
    stops at the first frame that resolves under it. That frame decides the class: a
    test-path frame is valid-red-assertion, an implementation-path frame is
    invalid-red. No frame under the worktree at all is invalid-red naming the last
    frame's file, as before this attribution walk existed.
    """
    outcome = result.get("outcome")
    exc_type = result.get("exc_type")
    message = (result.get("message") or "")[:2000]
    frames = result.get("frames") or []
    last_frame = frames[-1] if frames else None

    red: Dict[str, Any] = {
        "class": None, "exc_type": exc_type, "message": message,
        "last_frame": last_frame, "attribution_frame": None, "resolvedTo": None,
    }

    if outcome == "pass":
        red["class"] = "never-red"
        return red

    if outcome == "unrunnable":
        red["class"] = "unrunnable"
        return red

    if outcome == "fail" and exc_type == "AssertionError":
        attribution_frame = None
        rel = None
        for frame in reversed(frames):
            candidate = _relative_to_worktree(frame["file"], wt)
            if candidate is not None:
                attribution_frame = frame
                rel = candidate
                break
        red["attribution_frame"] = attribution_frame
        if rel is not None and classify_path(rel) in ("test", "support"):
            red["class"] = "valid-red-assertion"
        elif rel is not None:
            red["class"] = "invalid-red"
            red["message"] = f"assertion raised inside implementation path {rel}"
        else:
            red["class"] = "invalid-red"
            outside_file = last_frame["file"] if last_frame else "<no frames recorded>"
            red["message"] = f"no frame under the worktree; last frame {outside_file}"
        return red

    if exc_type == "ModuleNotFoundError":
        mod = result.get("missing_name")
        resolved = None
        if mod:
            for candidate in (mod.replace(".", "/") + ".py", mod.replace(".", "/") + "/__init__.py"):
                if candidate in added_impl:
                    resolved = candidate
                    break
        if resolved:
            red["class"] = "valid-red-missing-name"
            red["resolvedTo"] = resolved
        else:
            red["class"] = "invalid-red"
            red["message"] = f"missing module {mod} is not added by this change"
        return red

    if exc_type in ("ImportError", "AttributeError"):
        pattern = _IMPORT_ERROR_RE if exc_type == "ImportError" else _ATTR_ERROR_RE
        m = pattern.search(message)
        resolved = None
        if m:
            name, mod = m.group("name"), m.group("mod")
            path = mod.replace(".", "/") + ".py"
            if path in added_impl or path in modified_impl:
                diff_proc = gr(repo_root, "diff", "-U0", base, "HEAD", "--", path)
                added_pattern = re.compile(
                    rf"^\+\s*(async\s+def|def|class)\s+{re.escape(name)}\b|^\+\s*{re.escape(name)}\s*=",
                    re.MULTILINE,
                )
                if diff_proc.returncode == 0 and added_pattern.search(diff_proc.stdout):
                    resolved = f"{path}::{name}"
        if resolved:
            red["class"] = "valid-red-missing-name"
            red["resolvedTo"] = resolved
        else:
            red["class"] = "invalid-red"
        return red

    red["class"] = "invalid-red"
    red["message"] = f"{exc_type}: {message[:200]}"
    return red


def cmd_enumerate(args: argparse.Namespace) -> int:
    """List every new or modified test function between base and HEAD."""
    repo_root = Path(args.repo_root).resolve()
    try:
        run_dir = gate_state.find_run(repo_root)
        if not run_dir:
            raise GateExit(2, "run directory not found")

        head_proc = gr(repo_root, "rev-parse", "HEAD")
        if head_proc.returncode != 0:
            raise GateExit(2, "cannot resolve HEAD")
        head = head_proc.stdout.strip()

        base, base_source = resolve_base(repo_root, args.base)
        changed = changed_paths(repo_root, base)
        enum_result = do_enumerate(repo_root, base, head, changed)

        runnable = [t for t in enum_result["tests"] if t["kind"] != "implementation"]
        inseparable = [t for t in enum_result["tests"] if t["kind"] == "implementation"]

        gate_obj: Dict[str, Any] = {
            "gate": "tdd-enumerate",
            "argv": sys.argv,
            "cwd": os.getcwd(),
            "head": head,
            "base": {"sha": base, "source": base_source},
            "env_pins": {"python": sys.executable},
            "tests": enum_result["tests"],
            "support_tests": enum_result["support_tests"],
            "implementation_paths": enum_result["implementation_paths"],
            "support_paths": enum_result["support_paths"],
        }

        if not enum_result["tests"]:
            gate_obj["exit"] = 2
            gate_obj["summary"] = "NOT_APPLICABLE: no new or modified tests"
            verdict_word = "NOT_APPLICABLE"
        elif not runnable:
            gate_obj["exit"] = 2
            gate_obj["summary"] = "UNVERIFIED: every test is inseparable"
            verdict_word = "UNVERIFIED"
        else:
            gate_obj["exit"] = 0
            gate_obj["summary"] = f"PASS: {len(runnable)} runnable test(s) found"
            verdict_word = "PASS"

        write_gate(run_dir, "9-tests.json", gate_obj)

        for t in enum_result["tests"]:
            print(f"{t['nodeid']} {t['status']} {t['kind']}")

        print(f"verdict={verdict_word} tests={len(enum_result['tests'])} inseparable={len(inseparable)}", file=sys.stderr)
        return gate_obj["exit"]

    except GateExit as exc:
        print(exc.message, file=sys.stderr)
        return exc.code


def cmd_prove(args: argparse.Namespace) -> int:
    """Prove that every enumerated test is red at base and green at HEAD, in a throwaway worktree."""
    repo_root = Path(args.repo_root).resolve()
    python = args.python if args.python else sys.executable

    try:
        run_dir = gate_state.find_run(repo_root)
        if not run_dir:
            raise GateExit(2, "run directory not found")

        head_proc = gr(repo_root, "rev-parse", "HEAD")
        if head_proc.returncode != 0:
            raise GateExit(2, "cannot resolve HEAD")
        head = head_proc.stdout.strip()

        base, base_source = resolve_base(repo_root, args.base)

        dirty_proc = gr(repo_root, "status", "--porcelain", "--untracked-files=no")
        dirty = bool(dirty_proc.stdout.strip())
        patch_text: Optional[str] = None
        if dirty:
            if not args.allow_dirty:
                raise GateExit(2, "working tree is dirty; commit first or pass --allow-dirty")
            patch_text = gr(repo_root, "diff", "HEAD", "--binary").stdout

        changed = changed_paths(repo_root, base)
        enum_result = do_enumerate(repo_root, base, head, changed)

        runnable = [t for t in enum_result["tests"] if t["kind"] != "implementation"]
        inseparable = [t for t in enum_result["tests"] if t["kind"] == "implementation"]

        gate_obj: Dict[str, Any] = {
            "gate": "tdd-redgreen",
            "argv": sys.argv,
            "cwd": os.getcwd(),
            "head": head,
            "base": {"sha": base, "source": base_source},
            "env_pins": {"python": python},
            "dirty": dirty,
        }

        if not enum_result["tests"]:
            counts = _zero_counts()
            gate_obj.update({
                "worktree": None, "revert": None, "tests": [],
                "counts": counts, "exit": 2,
                "summary": "NOT_APPLICABLE: no new or modified tests",
            })
            write_gate(run_dir, "9.json", gate_obj)
            print(
                "verdict=NOT_APPLICABLE tests=0 red_ok=0 never_red=0 invalid_red=0 "
                "green_fails=0 inseparable=0 unrunnable=0",
                file=sys.stderr,
            )
            return 2

        if not runnable:
            counts = _zero_counts()
            counts["tests"] = len(enum_result["tests"])
            counts["inseparable"] = len(inseparable)
            counts["unverified"] = len(inseparable)
            gate_obj.update({
                "worktree": None, "revert": None,
                "tests": [
                    {**_base_test_fields(t), "green": None, "red": None, "verdict": "UNVERIFIED"}
                    for t in inseparable
                ],
                "counts": counts, "exit": 2,
                "summary": "UNVERIFIED: every test is inseparable",
            })
            write_gate(run_dir, "9.json", gate_obj)
            print(
                f"verdict=UNVERIFIED tests={counts['tests']} red_ok=0 never_red=0 invalid_red=0 "
                f"green_fails=0 inseparable={counts['inseparable']} unrunnable=0",
                file=sys.stderr,
            )
            return 2

        added_impl = {p for (s, p, _o) in changed if s == "A" and classify_path(p) == "implementation"}
        modified_impl = {p for (s, p, _o) in changed if s in ("M", "R") and classify_path(p) == "implementation"}

        _reap_stale_worktrees(repo_root, run_dir)

        wt = run_dir / "worktrees" / f"red-{head[:8]}-{os.getpid()}"
        add_proc = gr(repo_root, "worktree", "add", "--detach", str(wt), head)
        if add_proc.returncode != 0:
            raise GateExit(2, f"cannot create worktree: {add_proc.stderr.strip()}")

        gate_state.append_receipt(run_dir, "worktree-registered", {
            "path": str(wt), "head": head, "type": "red-proof",
        })

        teardown_state = {"done": False}

        def teardown_once() -> None:
            if teardown_state["done"]:
                return
            teardown_state["done"] = True
            gr(repo_root, "worktree", "remove", "--force", str(wt))
            shutil.rmtree(wt, ignore_errors=True)
            gr(repo_root, "worktree", "prune")

        def _signal_handler(signum: int, _frame: Any) -> None:
            teardown_once()
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)

        atexit.register(teardown_once)
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        try:
            if dirty and patch_text:
                apply_proc = gw(wt, repo_root, "apply", "--binary", input_text=patch_text)
                if apply_proc.returncode != 0:
                    raise GateExit(2, f"cannot apply dirty patch: {apply_proc.stderr.strip()}")

            green_info: Dict[str, Dict[str, Any]] = {}
            for t in runnable:
                r = _run_one_subprocess(python, wt, t["file"], t["qualname"])
                green_info[t["nodeid"]] = {
                    "outcome": r.get("outcome"),
                    "exc_type": r.get("exc_type"),
                    "message": r.get("message"),
                }

            for status, path, old_path in changed:
                if classify_path(path) != "implementation":
                    continue
                if status == "A":
                    target = wt / path
                    if target.exists():
                        target.unlink()
                        _remove_empty_parents(wt, target.parent)
                elif status == "M":
                    gw(wt, repo_root, "checkout", base, "--", path)
                elif status == "R":
                    target = wt / path
                    if target.exists():
                        target.unlink()
                        _remove_empty_parents(wt, target.parent)
                    gw(wt, repo_root, "checkout", base, "--", old_path)
                elif status == "D":
                    gw(wt, repo_root, "checkout", base, "--", path)

            revert_status = gw(wt, repo_root, "status", "--porcelain")
            revert_info = {"diffstat": revert_status.stdout}

            counts = _zero_counts()
            counts["tests"] = len(enum_result["tests"])
            counts["inseparable"] = len(inseparable)
            counts["unverified"] = len(inseparable)

            tests_output: List[Dict[str, Any]] = [
                {**_base_test_fields(t), "green": None, "red": None, "verdict": "UNVERIFIED"}
                for t in inseparable
            ]

            for t in runnable:
                nodeid = t["nodeid"]
                r = _run_one_subprocess(python, wt, t["file"], t["qualname"])
                red = classify_red(r, wt, added_impl, modified_impl, repo_root, base)
                g = green_info[nodeid]

                if g.get("outcome") == "unrunnable" or red["class"] == "unrunnable":
                    verdict = "UNRUNNABLE"
                    counts["unrunnable"] += 1
                else:
                    is_never_red = red["class"] == "never-red"
                    is_invalid_red = red["class"] == "invalid-red"
                    is_green_fail = g.get("outcome") != "pass"
                    if is_never_red:
                        counts["never_red"] += 1
                    if is_invalid_red:
                        counts["invalid_red"] += 1
                    if is_green_fail:
                        counts["green_fails"] += 1
                    if is_never_red or is_invalid_red or is_green_fail:
                        verdict = "BLOCK"
                        counts["block"] += 1
                    else:
                        verdict = "PASS"
                        counts["pass"] += 1

                tests_output.append({**_base_test_fields(t), "green": g, "red": red, "verdict": verdict})

            if counts["unrunnable"] > 0:
                exit_code = 2
                summary = f"UNRUNNABLE: {counts['unrunnable']} test(s) could not be run"
                verdict_word = "UNRUNNABLE"
            elif counts["block"] > 0:
                exit_code = 1
                summary = f"BLOCK: {counts['block']} test(s) failed red-green proof"
                verdict_word = "BLOCK"
            else:
                exit_code = 0
                summary = f"PASS: {counts['pass']} test(s) proved red then green"
                verdict_word = "PASS"

            gate_obj.update({
                "worktree": str(wt), "revert": revert_info, "tests": tests_output,
                "counts": counts, "exit": exit_code, "summary": summary,
            })
            write_gate(run_dir, "9.json", gate_obj)

            for t in tests_output:
                if t["verdict"] in ("BLOCK", "UNRUNNABLE"):
                    red = t.get("red") or {}
                    cls = red.get("class") or ("unrunnable" if t["verdict"] == "UNRUNNABLE" else "block")
                    reason = red.get("message") or (t.get("green") or {}).get("message") or ""
                    print(f"{t['nodeid']}: {cls}: {reason}")

            print(
                f"verdict={verdict_word} tests={counts['tests']} red_ok={counts['pass']} "
                f"never_red={counts['never_red']} invalid_red={counts['invalid_red']} "
                f"green_fails={counts['green_fails']} inseparable={counts['inseparable']} "
                f"unrunnable={counts['unrunnable']}",
                file=sys.stderr,
            )
            return exit_code
        finally:
            teardown_once()

    except GateExit as exc:
        print(exc.message, file=sys.stderr)
        return exc.code


def cmd_recheck(args: argparse.Namespace) -> int:
    """Re-hash every PASS test recorded in gates/9.json at the current HEAD."""
    repo_root = Path(args.repo_root).resolve()
    try:
        run_dir = gate_state.find_run(repo_root)
        if not run_dir:
            raise GateExit(2, "run directory not found")

        gate9 = run_dir / "gates" / "9.json"
        if not gate9.is_file():
            raise GateExit(2, "gates/9.json not found")

        try:
            proved = json.loads(gate9.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise GateExit(2, f"gates/9.json unreadable: {exc}")

        head_proc = gr(repo_root, "rev-parse", "HEAD")
        if head_proc.returncode != 0:
            raise GateExit(2, "cannot resolve HEAD")
        head_now = head_proc.stdout.strip()

        findings: List[str] = []
        rechecked = 0
        changed_count = 0
        removed_count = 0

        for t in proved.get("tests", []):
            if t.get("verdict") != "PASS":
                continue
            rechecked += 1
            file = t["file"]
            qualname = t["qualname"]

            src_proc = gr(repo_root, "show", f"{head_now}:{file}")
            if src_proc.returncode != 0:
                findings.append(f"test removed: {t['nodeid']}")
                removed_count += 1
                continue

            try:
                funcs = test_functions(src_proc.stdout)
            except SyntaxError:
                findings.append(f"syntax error at HEAD: {file}")
                continue

            if qualname not in funcs:
                findings.append(f"test removed: {t['nodeid']}")
                removed_count += 1
                continue

            new_hash = ast_hash(funcs[qualname])
            if new_hash != t.get("ast_hash"):
                findings.append(f"hash changed: {t['nodeid']} recorded {t['ast_hash'][:12]} now {new_hash[:12]}")
                changed_count += 1

        exit_code = 1 if findings else 0
        summary = f"{'BLOCK' if exit_code else 'PASS'}: {len(findings)} finding(s)"

        gate_obj = {
            "gate": "tdd-recheck",
            "argv": sys.argv,
            "cwd": os.getcwd(),
            "head": head_now,
            "base": proved.get("base"),
            "env_pins": proved.get("env_pins", {}),
            "proved_at_head": proved.get("head"),
            "findings": findings,
            "tests": proved.get("tests", []),
            "exit": exit_code,
            "summary": summary,
        }
        write_gate(run_dir, "9-recheck.json", gate_obj)

        for finding in findings:
            print(finding)

        print(
            f"verdict={'BLOCK' if exit_code else 'PASS'} rechecked={rechecked} "
            f"changed={changed_count} removed={removed_count}",
            file=sys.stderr,
        )
        return exit_code

    except GateExit as exc:
        print(exc.message, file=sys.stderr)
        return exc.code


def cmd_run_one(sys_path_root: str, test_file: str, qualname: str) -> int:
    """Internal: import test_file, resolve qualname, call it, print one JSON result line."""
    root = Path(sys_path_root)
    tf = Path(test_file)
    sys.path.insert(0, str(root))
    sys.path.insert(1, str(tf.parent))
    os.chdir(str(root))

    try:
        rel = tf.resolve().relative_to(root.resolve())
    except ValueError:
        rel = tf
    modname = str(rel).replace(os.sep, ".")
    if modname.endswith(".py"):
        modname = modname[:-3]

    phase = "import"
    try:
        spec = importlib.util.spec_from_file_location(modname, str(tf))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[modname] = mod
        spec.loader.exec_module(mod)

        phase = "lookup"
        if "." in qualname:
            class_name, method_name = qualname.split(".", 1)
            cls = getattr(mod, class_name)
            instance = cls()
            func = getattr(instance, method_name)
        else:
            func = getattr(mod, qualname)

        sig = inspect.signature(func)
        required = [
            p for p in sig.parameters.values()
            if p.default is inspect.Parameter.empty
            and p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        if required:
            print(json.dumps({
                "outcome": "unrunnable",
                "phase": "lookup",
                "message": f"test requires {len(required)} parameters; fixture-aware runner not available",
            }))
            return 0

        phase = "call"
        if inspect.iscoroutinefunction(func):
            asyncio.run(func())
        else:
            func()
        print(json.dumps({"outcome": "pass", "phase": "call"}))
        return 0

    except BaseException as exc:
        this_file = os.path.abspath(__file__)
        frames = [
            {"file": f.filename, "line": f.lineno, "func": f.name}
            for f in traceback.extract_tb(exc.__traceback__)
            if os.path.abspath(f.filename) != this_file
        ]
        print(json.dumps({
            "outcome": "fail" if isinstance(exc, AssertionError) else "error",
            "phase": phase,
            "exc_type": type(exc).__name__,
            "exc_module": type(exc).__module__,
            "message": str(exc)[:2000],
            "missing_name": getattr(exc, "name", None),
            "frames": frames,
        }))
        return 0


_FIXTURE_EXPECTATIONS: List[Tuple[str, int, List[str]]] = [
    ("proper-red-green", 0, ["red_ok=1"]),
    ("new-module-import-red", 0, []),
    ("new-symbol-in-existing-module", 0, []),
    ("assertion-in-helper", 0, []),
    ("unittest-valid-red", 0, ["red_ok=1"]),
    ("helper-outside-worktree", 0, ["red_ok=1"]),
    ("unittest-invalid-red", 1, ["invalid_red=1"]),
    ("never-red", 1, ["never_red=1"]),
    ("wrong-reason-syntax-error", 1, ["invalid_red=1"]),
    ("weakened-after-red", 0, []),
    ("inseparable-same-file", 2, ["inseparable=1"]),
    ("mixed-valid-and-inseparable", 0, ["red_ok=1", "inseparable=1"]),
    ("not-applicable-no-new-tests", 2, ["NOT_APPLICABLE"]),
    ("dirty-tree", 2, ["dirty"]),
    ("unrunnable-parametrised", 2, ["unrunnable=1"]),
]

_NO_GATE_FIXTURES = {"dirty-tree"}


def cmd_self_test() -> int:
    """Regenerate fixtures and assert prove's behavior on each, through the CLI subprocess only."""
    fixtures_dir = Path(__file__).resolve().parent / "fixtures" / "prove_red"
    make_fixtures = fixtures_dir / "make_fixtures.py"

    for build_dir in fixtures_dir.glob("*/_build"):
        shutil.rmtree(build_dir, ignore_errors=True)

    fixed_ts = os.environ.get("TEAM_FIXED_TS", "2026-01-01T00:00:00Z")
    gen_env = os.environ.copy()
    gen_env["TEAM_FIXED_TS"] = fixed_ts
    gen_proc = subprocess.run([sys.executable, str(make_fixtures)], capture_output=True, text=True, timeout=120, env=gen_env)
    if gen_proc.returncode != 0:
        print(f"make_fixtures.py failed: {gen_proc.stderr.strip()}", file=sys.stderr)
        return 2

    gate_state_path = Path(__file__).resolve().parent / "gate_state.py"
    lines: List[str] = []
    all_ok = True

    for name, expected_exit, expected_substrings in _FIXTURE_EXPECTATIONS:
        build_dir = fixtures_dir / name / "_build"
        base_sha_file = build_dir / "BASE_SHA"

        if not base_sha_file.is_file():
            lines.append(f"{name}: FAIL fixture not generated")
            all_ok = False
            continue

        base = base_sha_file.read_text(encoding="utf-8").strip()

        # Every fixture runs on a temporary copy of _build/repo, never on the
        # checked-in fixture itself, so a self-test run (including fixture 7's
        # weaken commit) never modifies anything under fixtures/prove_red.
        with tempfile.TemporaryDirectory() as tmp_root:
            tmp_root_path = Path(tmp_root)
            repo = tmp_root_path / "repo"
            shutil.copytree(build_dir / "repo", repo)
            state_root_dir = tmp_root_path / "state"
            state_root_dir.mkdir()

            child_env = os.environ.copy()
            child_env["TEAM_STATE_ROOT"] = str(state_root_dir)
            os.environ["TEAM_STATE_ROOT"] = str(state_root_dir)

            if name == "helper-outside-worktree":
                # The fixture's test imports a helper that lives outside the worktree
                # entirely, reachable only through this externally supplied sys.path
                # entry; it is never copied into the temporary repo.
                external_dir = str(build_dir / "external_helpers")
                existing_pp = child_env.get("PYTHONPATH")
                child_env["PYTHONPATH"] = (
                    external_dir if not existing_pp else external_dir + os.pathsep + existing_pp
                )

            try:
                run_id = gate_state.start_run(str(repo), "fix", [])
            except Exception as exc:
                lines.append(f"{name}: FAIL start_run raised {exc}")
                all_ok = False
                continue

            run_dir = state_root_dir / run_id

            proc = subprocess.run([sys.executable, __file__, "prove", "--base", base, "--repo-root", str(repo)], capture_output=True, text=True, timeout=300, env=child_env)

            exit_ok = proc.returncode == expected_exit
            stderr_ok = all(s in proc.stderr for s in expected_substrings)

            wt_proc = subprocess.run(["git", "-C", str(repo), "worktree", "list", "--porcelain"], capture_output=True, text=True, timeout=30)
            worktree_lines = [l for l in wt_proc.stdout.splitlines() if l.startswith("worktree ")]
            worktrees_ok = len(worktree_lines) == 1

            gate_path = run_dir / "gates" / "9.json"
            if name in _NO_GATE_FIXTURES:
                gate_ok = not gate_path.exists()
            else:
                gate_ok = gate_path.is_file()

            chain_ok = True
            if gate_ok and name not in _NO_GATE_FIXTURES:
                chain_proc = subprocess.run([sys.executable, str(gate_state_path), "verify-chain"], cwd=str(repo), env=child_env, capture_output=True, text=True, timeout=30)
                chain_ok = chain_proc.returncode == 0

            status = "OK" if (exit_ok and stderr_ok and worktrees_ok and gate_ok and chain_ok) else "FAIL"
            if status == "FAIL":
                all_ok = False

            sub_desc = " ".join(f"stderr contains '{s}'" for s in expected_substrings)
            lines.append(
                f"{name}: expected {expected_exit} got {proc.returncode} {sub_desc} "
                f"worktrees={1 if worktrees_ok else 0} chain={0 if chain_ok else 1} {status}"
            )

            if name == "weakened-after-red" and status == "OK":
                weakened_src = build_dir / "weakened_test_calc.py"
                target = repo / "tests" / "test_calc.py"
                target.write_text(weakened_src.read_text(encoding="utf-8"), encoding="utf-8")

                git_env = os.environ.copy()
                git_env.update({
                    "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                    "GIT_AUTHOR_DATE": fixed_ts,
                    "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
                    "GIT_COMMITTER_DATE": fixed_ts,
                })
                subprocess.run(["git", "-C", str(repo), "add", "tests/test_calc.py"], capture_output=True, env=git_env, timeout=30)
                subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", "commit", "-q", "-m", "weaken assertion"], capture_output=True, env=git_env, timeout=30)

                recheck_proc = subprocess.run([sys.executable, __file__, "recheck", "--repo-root", str(repo)], capture_output=True, text=True, timeout=60, env=child_env)
                recheck_ok = recheck_proc.returncode == 1 and "hash changed" in recheck_proc.stdout
                recheck_status = "OK" if recheck_ok else "FAIL"
                if not recheck_ok:
                    all_ok = False
                lines.append(f"{name}-recheck: expected 1 got {recheck_proc.returncode} stdout contains 'hash changed' {recheck_status}")

    for line in lines:
        print(line)

    return 0 if all_ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="regenerate fixtures and assert behavior on each")
    sub = parser.add_subparsers(dest="command")

    p_enum = sub.add_parser("enumerate")
    p_enum.add_argument("--base")
    p_enum.add_argument("--repo-root", default=".")

    p_prove = sub.add_parser("prove")
    p_prove.add_argument("--base")
    p_prove.add_argument("--repo-root", default=".")
    p_prove.add_argument("--allow-dirty", action="store_true")
    p_prove.add_argument("--python", default=None)

    p_recheck = sub.add_parser("recheck")
    p_recheck.add_argument("--repo-root", default=".")

    p_run_one = sub.add_parser("_run-one")
    p_run_one.add_argument("sys_path_root")
    p_run_one.add_argument("test_file")
    p_run_one.add_argument("qualname")

    args = parser.parse_args()

    if args.self_test:
        return cmd_self_test()

    if args.command == "enumerate":
        return cmd_enumerate(args)
    if args.command == "prove":
        return cmd_prove(args)
    if args.command == "recheck":
        return cmd_recheck(args)
    if args.command == "_run-one":
        return cmd_run_one(args.sys_path_root, args.test_file, args.qualname)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
