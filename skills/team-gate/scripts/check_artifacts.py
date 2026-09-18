#!/usr/bin/env python3
"""Validate artifacts at handoff transitions and the approval gate.

Exit contract: 0 = pass, 1 = block (a required artifact is missing, trivial, or
escapes .team-ship/), 2 = unrunnable (no run, unknown stage, manifest or repo
unreadable).

Subcommands:
  stage-inputs <n>: every input artifact the manifest requires for stage n
                    exists under .team-ship/, resolves without escaping it,
                    and is non-trivial (minLines, requiredHeadings,
                    forbidTokens). Writes gates/handoff-<n>.json.
  stage-output <n> <path>: validates one just-written output artifact of
                    stage n with the same function, then appends an
                    artifact-written receipt (path, sha256, lines, stage).
                    Writes no gate file of its own.
  approval-ready: the approval gate's input artifacts (research brief,
                    architecture options, plan, ARCH-PLAN.json, review
                    findings) all exist and are non-trivial. Writes
                    gates/handoff-approval.json.

The run directory comes only from gate_state.find_run(); its absence is
exit 2. Every gate file records argv, cwd, head (git rev-parse HEAD of the
measured repository), exit, summary, and violations, then a gate-result
receipt is appended naming the gate file and its sha256. A receipt append
failure is exit 2 and is never swallowed. Gate files never land under
.team-ship/; they are written only under run_dir/gates/.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_state

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "references" / "ship-manifest.json"

_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(\S.*)$")


def load_manifest() -> Optional[Dict[str, Any]]:
    """Load ship-manifest.json from its fixed location next to this skill."""
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def get_head(repo_root: Path) -> Optional[str]:
    """Return git rev-parse HEAD for repo_root, or None if it cannot be resolved."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    head = result.stdout.strip()
    return head or None


def resolve_under_team_ship(repo_root: Path, rel_path: str) -> Tuple[Optional[Path], Optional[str]]:
    """Resolve rel_path against repo_root, requiring the result stay under .team-ship/.

    Returns (resolved_path, None) on success, (None, reason) when the path is
    absolute, cannot be resolved, or resolves outside .team-ship/ (including
    via a symlink).
    """
    if os.path.isabs(rel_path):
        return None, f"{rel_path}: escapes .team-ship (absolute path)"

    team_ship_base = (repo_root / ".team-ship").resolve()
    candidate = repo_root / rel_path
    try:
        resolved = candidate.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        return None, f"{rel_path}: cannot be resolved ({exc})"

    try:
        resolved.relative_to(team_ship_base)
    except ValueError:
        return None, f"{rel_path}: escapes .team-ship (resolves to {resolved})"

    return resolved, None


def strip_fenced_blocks(text: str) -> str:
    """Return text with lines inside ``` or ~~~ fenced blocks removed."""
    out = []
    in_fence = False
    for line in text.split("\n"):
        if line.strip().startswith("```") or line.strip().startswith("~~~"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def has_required_heading(text: str, needle: str) -> bool:
    """True when a heading line outside a fenced block contains needle (case-insensitive)."""
    needle_lower = needle.strip().lower()
    for line in strip_fenced_blocks(text).split("\n"):
        match = _HEADING_RE.match(line)
        if match and needle_lower in match.group(1).lower():
            return True
    return False


def has_forbidden_token(text: str, token: str) -> bool:
    """True when token appears as a whole word anywhere in text, case-insensitive,
    including inside fenced blocks. "TODOs" and "mastodon" do not match "TODO";
    "TODO:" and "(TODO)" do.
    """
    pattern = r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def count_non_trivial_lines(text: str) -> int:
    """Count non-blank lines that are not themselves a heading line."""
    count = 0
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            count += 1
    return count


def validate_artifact(repo_root: Path, entry: Dict[str, Any]) -> Tuple[bool, List[str], Optional[Path]]:
    """Validate one manifest artifact entry. Returns (ok, violations, resolved_path)."""
    rel_path = entry["path"]
    violations: List[str] = []

    resolved, escape_reason = resolve_under_team_ship(repo_root, rel_path)
    if escape_reason:
        return False, [escape_reason], None

    if not resolved.is_file():
        return False, [f"{rel_path}: does not exist"], None

    try:
        text = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return False, [f"{rel_path}: cannot be read ({exc})"], None

    min_lines = entry.get("minLines", 0)
    max_lines = entry.get("maxLines")
    required_headings = entry.get("requiredHeadings", [])
    forbid_tokens = entry.get("forbidTokens", [])

    n = count_non_trivial_lines(text)
    if n < min_lines:
        violations.append(f"{rel_path}: too few non-blank non-heading lines ({n} < {min_lines})")
    if max_lines is not None and n > max_lines:
        violations.append(f"{rel_path}: too many non-blank non-heading lines ({n} > {max_lines})")

    for heading in required_headings:
        if not has_required_heading(text, heading):
            violations.append(f"{rel_path}: missing required heading '{heading}'")

    for token in forbid_tokens:
        if has_forbidden_token(text, token):
            violations.append(f"{rel_path}: forbidden token '{token}' present")

    return (len(violations) == 0), violations, resolved


def write_gate_and_receipt(run_dir: Path, gate_name: str, gate_rel: str, gate_data: Dict[str, Any]) -> bool:
    """Write the gate JSON, then append a gate-result receipt. False on any failure."""
    try:
        gates_dir = run_dir / "gates"
        gates_dir.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(gate_data, indent=2) + "\n"
        gate_path = run_dir / gate_rel
        gate_path.write_text(payload, encoding="utf-8")
        gate_sha256 = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        gate_state.append_receipt(run_dir, "gate-result", {
            "gate": gate_name,
            "gate_file": gate_rel,
            "gate_sha256": gate_sha256,
            "exit": gate_data["exit"],
            "summary": gate_data["summary"],
        })
        return True
    except Exception as exc:
        print(f"ERROR: failed to write gate or append receipt: {exc}", file=sys.stderr)
        return False


def run_handoff_gate(repo_root: Path, stage_key: str, gate_name: str, gate_rel: str) -> int:
    """Shared implementation for stage-inputs and approval-ready."""
    manifest = load_manifest()
    if manifest is None:
        print(f"ERROR: cannot read manifest: {MANIFEST_PATH}", file=sys.stderr)
        return 2

    stages = manifest.get("stages", {})
    if stage_key not in stages:
        print(f"ERROR: unknown stage: {stage_key}", file=sys.stderr)
        return 2

    try:
        run_dir = gate_state.find_run(repo_root)
    except gate_state.RunMarkerUnreadable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if run_dir is None:
        print(f"ERROR: no active run (.team-ship/RUN not found under {repo_root})", file=sys.stderr)
        return 2

    head = get_head(repo_root)
    if head is None:
        print(f"ERROR: cannot resolve git HEAD for {repo_root}", file=sys.stderr)
        return 2

    violations: List[str] = []
    for entry in stages[stage_key].get("inputs", []):
        _, entry_violations, _ = validate_artifact(repo_root, entry)
        violations.extend(entry_violations)

    exit_code = 0 if not violations else 1
    summary = "PASS: all inputs valid" if exit_code == 0 else f"BLOCK: {len(violations)} violation(s)"

    gate_data = {
        "argv": list(sys.argv),
        "cwd": str(repo_root),
        "head": head,
        "exit": exit_code,
        "summary": summary,
        "violations": violations,
    }

    if not write_gate_and_receipt(run_dir, gate_name, gate_rel, gate_data):
        return 2

    for violation in violations:
        print(f"ERROR: {violation}", file=sys.stderr)

    return exit_code


def cmd_stage_inputs(repo_root: Path, stage: str) -> int:
    return run_handoff_gate(repo_root, stage, f"handoff-{stage}", f"gates/handoff-{stage}.json")


def cmd_approval_ready(repo_root: Path) -> int:
    return run_handoff_gate(repo_root, "approval", "handoff-approval", "gates/handoff-approval.json")


def to_repo_relative(repo_root: Path, path_arg: str) -> Optional[str]:
    """Compute a repo-root-relative posix path string from a CLI argument, lexically.

    A relative path_arg is interpreted as relative to repo_root, matching how every
    artifact path in the manifest is itself written (repo-root-relative). This never
    resolves symlinks: containment against a symlink escape is checked later, by
    validate_artifact, after the argument has been matched to a declared manifest
    entry by name. Returns None when the argument does not lexically stay under
    repo_root (an absolute path outside it, or a literal ".." that walks out of it).
    """
    if os.path.isabs(path_arg):
        combined = os.path.normpath(path_arg)
    else:
        combined = os.path.normpath(str(repo_root / path_arg))
    repo_root_str = os.path.normpath(str(repo_root))
    if combined == repo_root_str:
        rel = ""
    elif combined.startswith(repo_root_str + os.sep):
        rel = combined[len(repo_root_str) + 1:]
    else:
        return None
    return rel.replace(os.sep, "/")


def cmd_stage_output(repo_root: Path, stage: str, path_arg: str) -> int:
    manifest = load_manifest()
    if manifest is None:
        print(f"ERROR: cannot read manifest: {MANIFEST_PATH}", file=sys.stderr)
        return 2

    stages = manifest.get("stages", {})
    if stage not in stages:
        print(f"ERROR: unknown stage: {stage}", file=sys.stderr)
        return 2

    try:
        run_dir = gate_state.find_run(repo_root)
    except gate_state.RunMarkerUnreadable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if run_dir is None:
        print(f"ERROR: no active run (.team-ship/RUN not found under {repo_root})", file=sys.stderr)
        return 2

    if get_head(repo_root) is None:
        print(f"ERROR: cannot resolve git HEAD for {repo_root}", file=sys.stderr)
        return 2

    rel_path = to_repo_relative(repo_root, path_arg)
    outputs = stages[stage].get("outputs", [])
    matching_entry = next((entry for entry in outputs if entry["path"] == rel_path), None)
    if matching_entry is None:
        print(f"ERROR: {path_arg!r} is not a declared output of stage {stage}", file=sys.stderr)
        return 2

    ok, violations, resolved = validate_artifact(repo_root, matching_entry)
    if not ok:
        for violation in violations:
            print(f"ERROR: {violation}", file=sys.stderr)
        return 1

    sha256 = hashlib.sha256(resolved.read_bytes()).hexdigest()
    lines = count_non_trivial_lines(resolved.read_text(encoding="utf-8"))

    try:
        gate_state.append_receipt(run_dir, "artifact-written", {
            "path": matching_entry["path"],
            "sha256": sha256,
            "lines": lines,
            "stage": stage,
        })
    except Exception as exc:
        print(f"ERROR: failed to append receipt: {exc}", file=sys.stderr)
        return 2

    return 0


def run_self_test() -> int:
    """Regenerate fixtures, then run the CLI against a temporary copy of every fixture.

    Every case runs on a copy of _build/<name> made under a fresh tempfile directory,
    with TEAM_STATE_ROOT and --repo-root pointed at that copy, so no run ever writes
    into _build itself: repeated self-test runs leave the in-tree fixtures untouched.
    """
    fixtures_dir = Path(__file__).parent / "fixtures" / "check_artifacts"
    build_dir = fixtures_dir / "_build"

    result = subprocess.run(
        [sys.executable, str(fixtures_dir / "make_fixtures.py")],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"make_fixtures.py failed: {result.stderr}", file=sys.stderr)
        return 2

    # (name, argv-after-script, expected_exit, expected_stderr_substring)
    cases = [
        ("complete-stage", ["stage-inputs", "2"], 0, None),
        ("missing-input", ["stage-inputs", "2"], 1, "does not exist"),
        ("trivial-artifact-too-short", ["stage-inputs", "2"], 1, "too few"),
        ("forbidden-token", ["stage-inputs", "2"], 1, "forbidden token"),
        ("missing-heading", ["stage-inputs", "3"], 1, "missing required heading"),
        ("no-run", ["stage-inputs", "1"], 2, "no active run"),
        ("forbidden-token-in-fence", ["stage-inputs", "2"], 1, "forbidden token"),
        ("forbidden-token-substring-ok", ["stage-inputs", "2"], 0, None),
        ("heading-only-in-fence", ["stage-inputs", "3"], 1, "missing required heading"),
        ("symlink-escape", ["stage-inputs", "2"], 1, "escapes .team-ship"),
        ("unknown-stage", ["stage-inputs", "99"], 2, "unknown stage"),
        ("adversarial-filler-no-heading", ["stage-inputs", "3"], 1, "missing required heading"),
        ("stage-output-ok", ["stage-output", "3", ".team-ship/PLAN.md"], 0, None),
        ("stage-output-undeclared", ["stage-output", "3", ".team-ship/NOPE.md"], 2, "not a declared output"),
        ("stage-output-symlink-escape", ["stage-output", "3", ".team-ship/PLAN.md"], 1, "escapes .team-ship"),
        ("approval-ready-ok", ["approval-ready"], 0, None),
        ("approval-missing", ["approval-ready"], 1, "does not exist"),
        ("map-missing", ["stage-inputs", "2"], 1, "BROWNFIELD-MAP.md"),
    ]

    all_pass = True
    for name, argv, expected_exit, expected_stderr in cases:
        with tempfile.TemporaryDirectory(prefix="check_artifacts_selftest_") as tmp:
            copy_dir = Path(tmp) / name
            shutil.copytree(build_dir / name, copy_dir, symlinks=True)
            fixture_repo = copy_dir / "repo"
            fixture_runs = copy_dir / "runs"
            env = dict(os.environ, TEAM_STATE_ROOT=str(fixture_runs))
            result = subprocess.run([sys.executable, __file__] + argv + ["--repo-root", str(fixture_repo)], capture_output=True, text=True, env=env)

            exit_ok = result.returncode == expected_exit
            stderr_ok = expected_stderr is None or expected_stderr in result.stderr
            status = "OK" if (exit_ok and stderr_ok) else "FAIL"
            if not (exit_ok and stderr_ok):
                all_pass = False

            if expected_stderr is not None:
                print(f"{name}: expected {expected_exit} got {result.returncode} stderr contains {expected_stderr!r} {status}")
            else:
                print(f"{name}: expected {expected_exit} got {result.returncode} {status}")

            if status == "FAIL" and result.stderr:
                print(f"  stderr: {result.stderr.strip()}", file=sys.stderr)

    return 0 if all_pass else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="Run self-tests")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    inputs_parser = subparsers.add_parser("stage-inputs", help="Validate inputs for a stage")
    inputs_parser.add_argument("stage", help="Stage number")
    inputs_parser.add_argument("--repo-root", default=".", help="Repository root")

    output_parser = subparsers.add_parser("stage-output", help="Validate and record a just-written artifact")
    output_parser.add_argument("stage", help="Stage number")
    output_parser.add_argument("path", help="Path to the artifact")
    output_parser.add_argument("--repo-root", default=".", help="Repository root")

    approval_parser = subparsers.add_parser("approval-ready", help="Validate the approval gate's inputs")
    approval_parser.add_argument("--repo-root", default=".", help="Repository root")

    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if args.command == "stage-inputs":
        return cmd_stage_inputs(Path(args.repo_root).resolve(), args.stage)
    elif args.command == "stage-output":
        return cmd_stage_output(Path(args.repo_root).resolve(), args.stage, args.path)
    elif args.command == "approval-ready":
        return cmd_approval_ready(Path(args.repo_root).resolve())
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
