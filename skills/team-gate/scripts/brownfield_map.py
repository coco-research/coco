#!/usr/bin/env python3
"""Build a Stage 1 brownfield map from a ripwire scan, with a receipt.

Contract, the same as every gate script: stdlib only; sys.path.insert then
import gate_state; the run comes from gate_state.find_run, absence exit 2.
Exit 0 when the map is written. Exit 2 when the binary is absent, the
repository or run is unreadable, --repo-root resolves to a different
repository than the one the found run belongs to, or ripwire exits
non-zero. Exit 1 never happens: a map is not a pass or fail judgement, so
this script has no notion of a failing map.

--repo-root may be any subdirectory of the run's own repository:
gate_state.find_run walks up from it to find .team-ship/RUN, and every
path this script resolves from then on, including the repository root
passed to git and to ripwire, uses run.json's own repo_root, never the
raw --repo-root argument. If the git repository containing --repo-root
(its "git rev-parse --show-toplevel") is not that same repo_root, the
argument is inside an unrelated repository nested under (or beside) the
one the run belongs to, and the script exits 2 before writing or
appending anything.

Invocation: brownfield_map.py --repo-root <dir> [--for "<task in words>"]
[--binary <path>]. The binary is resolved from --binary, else the
environment variable RIPWIRE_BIN, else "ripwire" on PATH, else
~/.local/bin/ripwire; whichever candidate resolves first is recorded.
ripwire is run once, as "<binary> <repo> --json" when no task is given, or
"<binary> <repo> --json --for=<task>" when one is. No shell, cwd at the
repository root, a 300-second timeout, and the proxy variables HTTP_PROXY,
HTTPS_PROXY, ALL_PROXY (and their lower-case forms) removed from the
environment before the call.

Two artifacts are written under the repository's .team-ship directory:
BROWNFIELD-MAP.md and brownfield-map.json, each atomically (temp file plus
os.replace), each followed by its own artifact-written receipt carrying the
file's path and sha256.

One more file is written under the run directory's own gates subdirectory:
handoff-1-map.json, carrying argv, cwd, head, exit, summary,
ripwire_version, binary, elapsed_seconds, languages and symbols, followed
by a gate-result receipt naming that file's sha256.

brownfield-map.json is ripwire's own parsed JSON, unchanged, plus one added
"meta" key. BROWNFIELD-MAP.md is rendered deterministically from that same
JSON with exactly five headings: Summary, Entry points, Impact, Tests,
Limits. No wall-clock timestamp appears in the rendered file; the run id
and HEAD identify it instead.

Greenfield repositories (a single commit and fewer than three tracked
files) still get a map; the Summary states that plainly rather than
treating a near-empty scan as an error.

ripwire's own JSON does not carry a per-file churn number outside of
--hotspots, and --hotspots refuses --json (confirmed against the installed
0.6.1 binary; see the README beside this script's fixtures). Without a
task, the Impact section therefore ranks files by the same call-graph
importance score the map already carries, and says so, rather than
mislabeling that score as churn.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_state


PROXY_VARS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy")

EXT_LANG = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".rb": "Ruby",
    ".php": "PHP", ".phtml": "PHP", ".lua": "Lua",
    ".ex": "Elixir", ".exs": "Elixir", ".dart": "Dart", ".kt": "Kotlin",
    ".sh": "Bash", ".bash": "Bash", ".swift": "Swift", ".cs": "C#",
    ".c": "C", ".h": "C", ".cpp": "C++", ".cc": "C++", ".hpp": "C++", ".hh": "C++",
    ".m": "Objective-C", ".mm": "Objective-C++",
    ".cu": "CUDA", ".cuh": "CUDA", ".metal": "Metal", ".gd": "GDScript",
    ".json": "JSON", ".toml": "TOML", ".yml": "YAML", ".yaml": "YAML",
    ".md": "Markdown", ".markdown": "Markdown",
}

LIMITS = [
    'Multi-file localization is the weakest measured result: "the tool finds one '
    'gold file far more often than it finds all of them" (ripwire README, section '
    '14, Known limits).',
    'The call graph is name-based and unsound by construction: "no pointer '
    'aliasing, no indirect calls," so any count that depends on it is a floor, '
    'never a total (ripwire README, "The quality panel," the --nonlocal-state '
    'feature row).',
    'Churn, ownership and co-change need real git history: "a shallow clone '
    'reports every file as one commit" (ripwire README, section 14, Known limits).',
]


# ---------------------------------------------------------------------------
# Binary resolution and the ripwire subprocess call
# ---------------------------------------------------------------------------

def _resolve_binary(binary_arg: Optional[str]) -> Tuple[Optional[str], Optional[str], List[str]]:
    """Resolve the ripwire binary. Returns (path, source, tried_descriptions).

    Tries, in order: --binary, RIPWIRE_BIN, "ripwire" on PATH,
    ~/.local/bin/ripwire. Returns the first candidate that exists and is
    executable. path is None when none qualified; tried_descriptions names
    every candidate that was checked, for the caller's error message.
    """
    checks = [
        ("--binary", binary_arg, "not given"),
        ("RIPWIRE_BIN", os.environ.get("RIPWIRE_BIN"), "not set"),
        ("PATH", shutil.which("ripwire"), "not found"),
        ("~/.local/bin/ripwire", str(Path.home() / ".local" / "bin" / "ripwire"), "not found"),
    ]

    tried: List[str] = []
    for label, candidate, absent_word in checks:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate, label, tried
        if candidate:
            tried.append(f"{label} ({candidate}, not found)")
        else:
            tried.append(f"{label} ({absent_word})")
    return None, None, tried


def _stripped_env() -> Dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in PROXY_VARS}


def _ripwire_version(binary: str, env: Dict[str, str]) -> str:
    try:
        result = subprocess.run([binary, "--version"], capture_output=True, text=True,
                                 timeout=10, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    text = ((result.stdout or "") + (result.stderr or "")).strip()
    return text.splitlines()[0] if text else "unknown"


def _run_ripwire_scan(binary: str, repo_root: Path, task: Optional[str],
                       env: Dict[str, str]) -> Tuple[Optional[Dict[str, Any]], List[str], float, Optional[str]]:
    """Run the one authoritative scan. Returns (data, argv, elapsed_seconds, error)."""
    argv = [binary, str(repo_root), "--json"]
    if task:
        argv.append(f"--for={task}")

    start = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=str(repo_root), capture_output=True, text=True,
                                 timeout=300, env=env)
    except FileNotFoundError as exc:
        return None, argv, time.monotonic() - start, f"ripwire binary not executable: {exc}"
    except subprocess.TimeoutExpired:
        return None, argv, time.monotonic() - start, "ripwire timed out after 300 seconds"
    elapsed = time.monotonic() - start

    if result.returncode != 0:
        stderr_lines = [ln for ln in (result.stderr or "").splitlines() if ln.strip()]
        reason = stderr_lines[-1] if stderr_lines else f"ripwire exited {result.returncode}"
        return None, argv, elapsed, f"ripwire failed: {reason}"

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, argv, elapsed, f"ripwire produced invalid JSON: {exc}"

    if not isinstance(data, dict):
        return None, argv, elapsed, "ripwire produced a JSON value that is not an object"

    return data, argv, elapsed, None


# ---------------------------------------------------------------------------
# Repository facts (independent of ripwire, used only for greenfield)
# ---------------------------------------------------------------------------

def _repo_facts(repo_root: Path) -> Tuple[Optional[int], Optional[int]]:
    """Return (commit_count, tracked_file_count), either None if git could not answer."""
    commit_count = None
    try:
        result = subprocess.run(["git", "-C", str(repo_root), "rev-list", "--count", "HEAD"],
                                 capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            commit_count = int(result.stdout.strip())
    except (OSError, ValueError):
        commit_count = None

    file_count = None
    try:
        result = subprocess.run(["git", "-C", str(repo_root), "ls-files"],
                                 capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            file_count = len([ln for ln in result.stdout.splitlines() if ln.strip()])
    except OSError:
        file_count = None

    return commit_count, file_count


# ---------------------------------------------------------------------------
# Shaping the JSON into what the Markdown needs
# ---------------------------------------------------------------------------

def _collect_paths(data: Dict[str, Any]) -> List[str]:
    paths: List[str] = []
    for entry in data.get("r") or []:
        p = entry.get("p")
        if p:
            paths.append(p)
    for entry in data.get("sigs") or []:
        p = entry.get("p")
        if p:
            paths.append(p)
    tail = data.get("tail") or {}
    for f in tail.get("files") or []:
        p = f.get("p") if isinstance(f, dict) else f
        if p:
            paths.append(p)
    return paths


def _languages(data: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for p in _collect_paths(data):
        ext = Path(p).suffix.lower()
        lang = EXT_LANG.get(ext, ext.lstrip(".") or "unknown")
        counts[lang] = counts.get(lang, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def _entry_points(data: Dict[str, Any], task: Optional[str], limit: int = 10) -> List[Dict[str, Any]]:
    if task:
        sigs = sorted(data.get("sigs") or [], key=lambda s: s.get("r") or 0)
        return [{"name": s.get("n"), "path": s.get("p"), "line": s.get("l")} for s in sigs[:limit]]

    pooled: List[Dict[str, Any]] = []
    for file_entry in data.get("r") or []:
        p = file_entry.get("p")
        for s in file_entry.get("s") or []:
            pooled.append({"name": s.get("n"), "path": p, "line": None, "k": s.get("k") or 0})
    pooled.sort(key=lambda e: -e["k"])
    return pooled[:limit]


def _impact_with_task(data: Dict[str, Any], limit: int = 10) -> "Dict[str, List[Dict[str, Any]]]":
    sigs = sorted(data.get("sigs") or [], key=lambda s: s.get("r") or 0)
    by_file: Dict[str, List[Dict[str, Any]]] = {}
    for s in sigs[:limit]:
        by_file.setdefault(s.get("p"), []).append(s)
    return by_file


def _impact_without_task(data: Dict[str, Any], limit: int = 5) -> List[Tuple[str, float]]:
    scores: Dict[str, float] = {}
    for file_entry in data.get("r") or []:
        p = file_entry.get("p")
        if not p:
            continue
        total = sum((s.get("k") or 0) for s in file_entry.get("s") or [])
        scores[p] = max(scores.get(p, 0.0), total)
    return sorted(scores.items(), key=lambda kv: -kv[1])[:limit]


def _test_files(data: Dict[str, Any], task: Optional[str]) -> List[str]:
    paths = set()
    if task:
        for s in data.get("sigs") or []:
            if s.get("layer") == "test" and s.get("p"):
                paths.add(s["p"])
    else:
        for file_entry in data.get("r") or []:
            if file_entry.get("layer") == "test" and file_entry.get("p"):
                paths.add(file_entry["p"])
    return sorted(paths)


def render_markdown(data: Dict[str, Any], meta: Dict[str, Any], task: Optional[str]) -> str:
    lines: List[str] = []
    lines.append("# Brownfield map")
    lines.append("")
    lines.append(f"Run {meta['run_id']}, HEAD {meta['head']}.")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Task: {task}" if task else "- Task: none given; showing the default ranked map.")
    if meta["greenfield"]:
        lines.append(f"- Repository: greenfield ({meta['repo_commit_count']} commit, "
                      f"{meta['repo_file_count']} tracked file(s))")
    lang_str = ", ".join(f"{name} ({count})" for name, count in meta["languages"].items())
    lines.append(f"- Languages: {lang_str or 'none identified'}")
    lines.append(f"- Files: {meta['map_file_count']}")
    lines.append(f"- Symbols: {meta['map_symbol_count']}")
    lines.append("")

    lines.append("## Entry points")
    lines.append("")
    entries = _entry_points(data, task)
    if entries:
        for e in entries:
            if e.get("line") is not None:
                lines.append(f"- **{e['name']}** - {e['path']}:{e['line']}")
            else:
                lines.append(f"- **{e['name']}** - {e['path']}")
    else:
        lines.append("- none identified")
    lines.append("")

    lines.append("## Impact")
    lines.append("")
    if task:
        by_file = _impact_with_task(data)
        if by_file:
            for path, syms in by_file.items():
                names = ", ".join(s.get("n") or "" for s in syms)
                lines.append(f"- {path}: {names}")
        else:
            lines.append("- none identified")
    else:
        ranked_files = _impact_without_task(data)
        if ranked_files:
            lines.append("- ripwire's default map carries no per-file churn number; the files "
                          "below are ranked by call-graph importance instead.")
            for path, _score in ranked_files:
                lines.append(f"- {path}")
        else:
            lines.append("- none identified")
    lines.append("")

    lines.append("## Tests")
    lines.append("")
    tests = _test_files(data, task)
    if tests:
        for t in tests:
            lines.append(f"- {t}")
    else:
        lines.append("- none identified")
    lines.append("")

    lines.append("## Limits")
    lines.append("")
    for item in LIMITS:
        lines.append(f"- {item}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Atomic write and receipt helpers (same house pattern as run_gate.py)
# ---------------------------------------------------------------------------

def _atomic_write(path: Path, content_bytes: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.tmp"
    tmp.write_bytes(content_bytes)
    os.replace(str(tmp), str(path))


def _write_artifact_and_receipt(run_dir: Path, path: Path, rel_path: str,
                                 content_bytes: bytes) -> Optional[int]:
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


def _write_gate_and_receipt(run_dir: Path, filename: str, data: Dict[str, Any],
                             gate_name: str, exit_code: int, summary: str) -> Optional[int]:
    gate_file = run_dir / "gates" / filename
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


# ---------------------------------------------------------------------------
# The map command
# ---------------------------------------------------------------------------

def _resolve_context(repo_root_arg: str):
    """Resolve (repo_root, run_dir, head) or print one ERROR line and return None.

    repo_root_arg may be any subdirectory of a repository that has an active
    run: gate_state.find_run() walks up from it to the same .team-ship/RUN
    pointer, so a run started against the repository root is found from any
    of its subdirectories. Before anything is written, the git repository
    containing the argument (its "rev-parse --show-toplevel") is checked
    against run.json's own repo_root. If they differ, the argument is
    inside a different repository than the one the found run belongs to
    (for example a nested, unrelated repository below the run's root) and
    nothing is written or appended. When they agree, repo_root_arg's own
    subdirectory is discarded: every path from here on, including the
    returned repo_root, is run.json's own repo_root, never the raw
    argument. A relative repo_root is resolved against the run directory,
    the same rule as gate_state.verify_chain, never against the process cwd.
    """
    repo_root_input = Path(repo_root_arg).resolve()
    try:
        run_dir = gate_state.find_run(repo_root_input)
    except gate_state.RunMarkerUnreadable as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return None
    if run_dir is None:
        print(f"ERROR: no active run found under {repo_root_input}", file=sys.stderr)
        return None

    run_json_path = run_dir / "run.json"
    try:
        run_obj = json.loads(run_json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: run.json unreadable: {exc}", file=sys.stderr)
        return None

    recorded_root_str = run_obj.get("repo_root")
    if not recorded_root_str:
        print(f"ERROR: run.json missing repo_root: {run_json_path}", file=sys.stderr)
        return None
    try:
        recorded_root = gate_state.resolve_recorded_repo_root(run_dir, recorded_root_str)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return None

    try:
        toplevel_result = subprocess.run(
            ["git", "-C", str(repo_root_input), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
    except OSError as exc:
        print(f"ERROR: repository unreadable: git rev-parse --show-toplevel failed: {exc}",
              file=sys.stderr)
        return None
    if toplevel_result.returncode != 0:
        print(f"ERROR: repository unreadable: git rev-parse --show-toplevel failed: "
              f"{toplevel_result.stderr.strip()}", file=sys.stderr)
        return None
    toplevel = Path(toplevel_result.stdout.strip()).resolve()

    if toplevel != recorded_root:
        print(f"ERROR: repo-root mismatch: --repo-root {repo_root_input} is inside "
              f"repository {toplevel}, run {run_dir.name} belongs to {recorded_root}",
              file=sys.stderr)
        return None

    repo_root = recorded_root

    try:
        head_result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
    except OSError as exc:
        print(f"ERROR: repository unreadable: git rev-parse HEAD failed: {exc}", file=sys.stderr)
        return None
    if head_result.returncode != 0:
        print(f"ERROR: repository unreadable: git rev-parse HEAD failed: "
              f"{head_result.stderr.strip()}", file=sys.stderr)
        return None
    return repo_root, run_dir, head_result.stdout.strip()


def cmd_map(repo_root_arg: str, task: Optional[str], binary_arg: Optional[str]) -> int:
    ctx = _resolve_context(repo_root_arg)
    if ctx is None:
        return 2
    repo_root, run_dir, head = ctx

    binary, _source, tried = _resolve_binary(binary_arg)
    if binary is None:
        print(f"ERROR: ripwire binary not found; searched {', '.join(tried)}", file=sys.stderr)
        return 2

    env = _stripped_env()
    version = _ripwire_version(binary, env)

    data, argv, elapsed, error = _run_ripwire_scan(binary, repo_root, task, env)
    if error is not None:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    repo_commit_count, repo_file_count = _repo_facts(repo_root)
    greenfield = (repo_commit_count is not None and repo_commit_count <= 1
                  and repo_file_count is not None and repo_file_count < 3)

    map_file_count = data.get("corpus") if task else data.get("files")
    map_symbol_count = data.get("kept", len(data.get("sigs") or [])) if task else data.get("symbols")
    languages = _languages(data)

    meta = {
        "run_id": run_dir.name,
        "head": head,
        "task": task,
        "binary": binary,
        "ripwire_version": version,
        "elapsed_seconds": round(elapsed, 3),
        "repo_commit_count": repo_commit_count,
        "repo_file_count": repo_file_count,
        "greenfield": greenfield,
        "map_file_count": map_file_count,
        "map_symbol_count": map_symbol_count,
        "languages": languages,
    }

    output_json = dict(data)
    output_json["meta"] = meta
    json_bytes = (json.dumps(output_json, indent=2, sort_keys=True) + "\n").encode("utf-8")

    md_text = render_markdown(data, meta, task)
    md_bytes = md_text.encode("utf-8")

    team_ship_dir = repo_root / ".team-ship"
    rc = _write_artifact_and_receipt(run_dir, team_ship_dir / "brownfield-map.json",
                                      ".team-ship/brownfield-map.json", json_bytes)
    if rc is not None:
        return rc
    rc = _write_artifact_and_receipt(run_dir, team_ship_dir / "BROWNFIELD-MAP.md",
                                      ".team-ship/BROWNFIELD-MAP.md", md_bytes)
    if rc is not None:
        return rc

    summary = f"map written: {map_file_count} file(s), {map_symbol_count} symbol(s)"
    if task:
        summary += f" for task {task!r}"
    gate_data = {
        "argv": argv, "cwd": str(repo_root), "head": head, "exit": 0, "summary": summary,
        "ripwire_version": version, "binary": binary, "elapsed_seconds": round(elapsed, 3),
        "languages": languages, "symbols": map_symbol_count,
    }
    rc = _write_gate_and_receipt(run_dir, "handoff-1-map.json", gate_data, "brownfield-map",
                                  0, summary)
    if rc is not None:
        return rc

    print(summary)
    return 0


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _isolated_copy(build_dir: Path, name: str, start_run: bool = True) -> Tuple[Path, Dict[str, str]]:
    tmp_root = Path(tempfile.mkdtemp(prefix=f"brownfield_map_{name}_"))
    copy_path = tmp_root / name
    shutil.copytree(build_dir / name, copy_path)
    state_root = tmp_root / "state"
    state_root.mkdir()
    env = os.environ.copy()
    env["TEAM_STATE_ROOT"] = str(state_root)
    os.environ["TEAM_STATE_ROOT"] = str(state_root)
    if start_run:
        gate_state.start_run(str(copy_path), "test", [])
    return copy_path, env


def _invoke(copy_path: Path, env: Dict[str, str], *args: str,
            repo_root: Optional[Path] = None) -> subprocess.CompletedProcess:
    target = repo_root if repo_root is not None else copy_path
    rest = ["--repo-root", str(target)] + list(args)
    return subprocess.run([sys.executable, __file__] + rest,
                           cwd=str(copy_path), env=env, capture_output=True, text=True, timeout=60)


def _make_stub_dir() -> Path:
    stub_src = Path(__file__).resolve().parent / "fixtures" / "brownfield_map" / "stub-ripwire"
    stub_dir = Path(tempfile.mkdtemp(prefix="brownfield_map_stub_"))
    stub_dst = stub_dir / "ripwire"
    shutil.copy(str(stub_src), str(stub_dst))
    os.chmod(stub_dst, 0o755)
    return stub_dir


def _with_stub_on_path(env: Dict[str, str], stub_dir: Path) -> Dict[str, str]:
    merged = dict(env)
    merged["PATH"] = f"{stub_dir}{os.pathsep}{merged.get('PATH', '')}"
    merged.pop("RIPWIRE_BIN", None)
    return merged


def _with_no_binary_env(env: Dict[str, str]) -> Dict[str, str]:
    merged = dict(env)
    merged["PATH"] = f"{os.sep}usr{os.sep}bin{os.pathsep}{os.sep}bin"
    fake_home = Path(tempfile.mkdtemp(prefix="brownfield_map_fakehome_"))
    merged["HOME"] = str(fake_home)
    merged.pop("RIPWIRE_BIN", None)
    return merged


def cmd_self_test() -> int:
    fixtures_dir = Path(__file__).resolve().parent / "fixtures" / "brownfield_map"
    build_dir = fixtures_dir / "_build"
    make_fixtures = fixtures_dir / "make_fixtures.py"

    result = subprocess.run([sys.executable, str(make_fixtures)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"make_fixtures.py failed: {result.stderr}", file=sys.stderr)
        return 2

    stub_dir = _make_stub_dir()
    all_ok = True

    # map-written: exit 0, both artifacts present, receipts appended, headings present,
    # verify-chain 0.
    copy_path, env = _isolated_copy(build_dir, "map-written")
    proc = _invoke(copy_path, _with_stub_on_path(env, stub_dir))
    ok = proc.returncode == 0
    json_path = copy_path / ".team-ship" / "brownfield-map.json"
    md_path = copy_path / ".team-ship" / "BROWNFIELD-MAP.md"
    artifacts_ok = json_path.is_file() and md_path.is_file()
    ok = ok and artifacts_ok
    headings_ok = False
    if md_path.is_file():
        md_text = md_path.read_text()
        headings_ok = all(h in md_text for h in
                           ("## Summary", "## Entry points", "## Impact", "## Tests", "## Limits"))
    ok = ok and headings_ok
    verify_ok = False
    if ok:
        verify_proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "gate_state.py"), "verify-chain"],
            cwd=str(copy_path), env=env, capture_output=True, text=True, timeout=30)
        verify_ok = verify_proc.returncode == 0
    ok = ok and verify_ok
    all_ok = all_ok and ok
    print(f"map-written: expected 0 got {proc.returncode} artifacts={artifacts_ok} "
          f"headings={headings_ok} verify-chain={verify_ok} {'OK' if ok else 'FAIL'}")

    # map-with-task: exit 0, the task appears in Summary, Impact is non-empty.
    copy_path, env = _isolated_copy(build_dir, "map-written")
    task_text = "fix the add helper"
    proc = _invoke(copy_path, _with_stub_on_path(env, stub_dir), "--for", task_text)
    ok = proc.returncode == 0
    task_in_summary = False
    impact_nonempty = False
    if ok:
        md_text = (copy_path / ".team-ship" / "BROWNFIELD-MAP.md").read_text()
        task_in_summary = task_text in md_text
        impact_section = (md_text.split("## Impact", 1)[-1].split("## Tests", 1)[0]
                           if "## Impact" in md_text else "")
        impact_nonempty = impact_section.strip() != "" and "none identified" not in impact_section
    ok = ok and task_in_summary and impact_nonempty
    all_ok = all_ok and ok
    print(f"map-with-task: expected 0 got {proc.returncode} task_in_summary={task_in_summary} "
          f"impact_nonempty={impact_nonempty} {'OK' if ok else 'FAIL'}")

    # binary-absent: PATH without ripwire and no RIPWIRE_BIN; exit 2 naming what was searched.
    copy_path, env = _isolated_copy(build_dir, "map-written")
    proc = _invoke(copy_path, _with_no_binary_env(env))
    named = (proc.returncode == 2 and "RIPWIRE_BIN" in proc.stderr and "PATH" in proc.stderr
             and "~/.local/bin/ripwire" in proc.stderr)
    ok = named
    all_ok = all_ok and ok
    print(f"binary-absent: expected 2 got {proc.returncode} searched-named={named} {'OK' if ok else 'FAIL'}")

    # ripwire-fails: stub exits 3; exit 2 with the stub's stderr line.
    copy_path, env = _isolated_copy(build_dir, "map-written")
    fail_env = _with_stub_on_path(env, stub_dir)
    fail_env["RIPWIRE_STUB_FAIL"] = "1"
    proc = _invoke(copy_path, fail_env)
    ok = proc.returncode == 2 and "stub forced failure" in proc.stderr
    all_ok = all_ok and ok
    print(f"ripwire-fails: expected 2 got {proc.returncode} stderr_names_stub="
          f"{'stub forced failure' in proc.stderr} {'OK' if ok else 'FAIL'}")

    # no-run: exit 2.
    copy_path, env = _isolated_copy(build_dir, "map-written", start_run=False)
    proc = _invoke(copy_path, _with_stub_on_path(env, stub_dir))
    ok = proc.returncode == 2
    all_ok = all_ok and ok
    print(f"no-run: expected 2 got {proc.returncode} {'OK' if ok else 'FAIL'}")

    # greenfield: single-commit repository; exit 0, Summary says greenfield.
    copy_path, env = _isolated_copy(build_dir, "greenfield")
    proc = _invoke(copy_path, _with_stub_on_path(env, stub_dir))
    ok = proc.returncode == 0
    greenfield_stated = False
    if ok:
        md_path = copy_path / ".team-ship" / "BROWNFIELD-MAP.md"
        greenfield_stated = md_path.is_file() and "greenfield" in md_path.read_text()
    ok = ok and greenfield_stated
    all_ok = all_ok and ok
    print(f"greenfield: expected 0 got {proc.returncode} greenfield_stated={greenfield_stated} "
          f"{'OK' if ok else 'FAIL'}")

    # repo-root-mismatch: --repo-root inside a nested, unrelated git repository
    # under a repository that has an active run. find_run() walks up and finds
    # the outer run; the toplevel check must catch the mismatch before anything
    # is written, and the outer run's own chain must stay verifiable afterward.
    copy_path, env = _isolated_copy(build_dir, "repo-root-mismatch")
    outer_run_dir = gate_state.find_run(copy_path)
    gate_state.append_receipt(outer_run_dir, "run-started", {"command": "test", "flags": []})
    nested_path = copy_path / "nested-unrelated"
    proc = _invoke(copy_path, _with_stub_on_path(env, stub_dir), repo_root=nested_path)
    nested_resolved = str(nested_path.resolve())
    outer_resolved = str(copy_path.resolve())
    named = (proc.returncode == 2 and "repo-root mismatch" in proc.stderr
             and nested_resolved in proc.stderr and outer_resolved in proc.stderr)
    nested_clean = not (nested_path / ".team-ship").exists()
    outer_ts = copy_path / ".team-ship"
    outer_only_run = outer_ts.is_dir() and sorted(p.name for p in outer_ts.iterdir()) == ["RUN"]
    verify_proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "gate_state.py"), "verify-chain"],
        cwd=str(copy_path), env=env, capture_output=True, text=True, timeout=30)
    verify_ok = verify_proc.returncode == 0
    ok = proc.returncode == 2 and named and nested_clean and outer_only_run and verify_ok
    all_ok = all_ok and ok
    print(f"repo-root-mismatch: expected 2 got {proc.returncode} named={named} "
          f"nested-clean={nested_clean} outer-only-run={outer_only_run} verify-chain={verify_ok} "
          f"{'OK' if ok else 'FAIL'}")

    # repo-root-subdir: --repo-root pointing at a subdirectory of the run's own
    # repository. The recorded root wins, so the artifacts land under the
    # repository root, never under the subdirectory.
    copy_path, env = _isolated_copy(build_dir, "map-written")
    subdir = copy_path / "src"
    proc = _invoke(copy_path, _with_stub_on_path(env, stub_dir), repo_root=subdir)
    ok = proc.returncode == 0
    artifacts_at_root = ((copy_path / ".team-ship" / "brownfield-map.json").is_file()
                         and (copy_path / ".team-ship" / "BROWNFIELD-MAP.md").is_file())
    not_under_subdir = not (subdir / ".team-ship").exists()
    ok = ok and artifacts_at_root and not_under_subdir
    all_ok = all_ok and ok
    print(f"repo-root-subdir: expected 0 got {proc.returncode} artifacts_at_root={artifacts_at_root} "
          f"not_under_subdir={not_under_subdir} {'OK' if ok else 'FAIL'}")

    # relative-repo-root: run.json records a single path segment relative
    # to the run directory. Path.resolve() with no base uses the process
    # cwd and misses the repository; joining with the run directory
    # matches gate_state.verify_chain and writes the map. The follow-up
    # invoke rewrites repo_root to "." which verify_chain refuses as
    # malformed, so this script must refuse it the same way.
    copy_path, env = _isolated_copy(build_dir, "map-written")
    run_dir = gate_state.find_run(copy_path)
    run_json_path = run_dir / "run.json"
    run_obj = json.loads(run_json_path.read_text(encoding="utf-8"))
    link = run_dir / "linked-repo"
    link.symlink_to(copy_path.resolve())
    run_obj["repo_root"] = "linked-repo"
    run_json_path.write_text(json.dumps(run_obj, indent=2), encoding="utf-8")
    foreign_cwd = Path(tempfile.mkdtemp(prefix="brownfield_map_cwd_"))
    stub_env = _with_stub_on_path(env, stub_dir)
    proc = subprocess.run(
        [sys.executable, __file__, "--repo-root", str(copy_path)],
        cwd=str(foreign_cwd), env=stub_env, capture_output=True, text=True, timeout=60)
    artifacts_ok = ((copy_path / ".team-ship" / "brownfield-map.json").is_file()
                    and (copy_path / ".team-ship" / "BROWNFIELD-MAP.md").is_file())
    named = "map written" in proc.stdout
    ok = proc.returncode == 0 and artifacts_ok and named
    run_obj["repo_root"] = "."
    run_json_path.write_text(json.dumps(run_obj, indent=2), encoding="utf-8")
    refuse = subprocess.run(
        [sys.executable, __file__, "--repo-root", str(copy_path)],
        cwd=str(copy_path), env=stub_env, capture_output=True, text=True, timeout=60)
    refuse_ok = refuse.returncode == 2 and "run.json repo_root malformed" in refuse.stderr
    ok = ok and refuse_ok
    all_ok = all_ok and ok
    print(f"relative-repo-root: expected 0 got {proc.returncode} artifacts={artifacts_ok} "
          f"stdout_map_written={named} refuse_exit={refuse.returncode} "
          f"refuse_malformed={'run.json repo_root malformed' in refuse.stderr} "
          f"{'OK' if ok else 'FAIL'}")

    # real-binary: the one permitted skip, when no real binary is on this machine.
    real_binary, _real_source, _tried = _resolve_binary(None)
    if real_binary is None:
        print("real-binary: skipped, no binary")
    else:
        copy_path, env = _isolated_copy(build_dir, "map-written")
        real_env = dict(env)
        real_env["RIPWIRE_BIN"] = real_binary
        proc = _invoke(copy_path, real_env)
        ok = proc.returncode == 0
        all_ok = all_ok and ok
        print(f"real-binary: expected 0 got {proc.returncode} {'OK' if ok else 'FAIL'}")

    shutil.rmtree(stub_dir, ignore_errors=True)
    return 0 if all_ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--for", dest="task", default=None, help="the task, in words")
    parser.add_argument("--binary", default=None, help="path to the ripwire binary")
    parser.add_argument("--self-test", action="store_true", help="run self-test on fixtures")
    args = parser.parse_args()

    if args.self_test:
        return cmd_self_test()

    return cmd_map(args.repo_root, args.task, args.binary)


if __name__ == "__main__":
    sys.exit(main())
