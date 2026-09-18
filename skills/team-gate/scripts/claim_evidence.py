#!/usr/bin/env python3
"""Check quantitative claims in a PR body against EVIDENCE.json, and grade a
plan's requirements against the run's gate files.

Exit contract: 0 = pass, 1 = block, 2 = unrunnable (repository, run, lexicon,
or a required input file cannot be read).

Subcommands:
  check <pr-body.md> [--repo-root PATH]
    Every sentence (one non-blank line) inside the Results or Evidence
    section must carry an [E<n>] tag naming an entry in EVIDENCE.json, every
    quantitative claim's number or qualifier must match the cited entry, and
    every unbacked-claim word from the lexicon must carry a citation. Every
    sentence of the whole PR body is also scanned for the lexicon's
    mergeClaims phrases ("merged", "shipped", "ci green", and their
    variants); each is a merge-claim finding unless its named condition
    (ancestor-of-main, ci-mirror-pass, pr-opened) holds, checked at most
    once per run. This is independent of the [E<n>] citation checks above.
    Matching is fail closed: a conditional or future-tense sentence such
    as "once this is merged, the cron picks it up" is a finding by
    design; the cost is a reword, the benefit is that a merge masquerade
    cannot pass. Fenced text is scanned like plain text, as the
    forbidden-token precedent in check_artifacts does.
    Any finding is exit 1. Writes gates/12.json in the run directory.

  matrix <plan.md> [--repo-root PATH]
    Extracts requirement identifiers from the plan's "requirements" and
    "must_haves" lists, maps each to the gate files that name it, and grades
    MET, NOT MET, or UNVERIFIED: exactly three grades, since gate exits are
    only 0, 1 or 2 and every requirement lands in one of these three. NOT MET
    is exit 1; UNVERIFIED alone (no NOT MET present) is exit 2. Writes
    gates/11-matrix.json.

Tags and claims inside fenced code blocks in the PR body are checked exactly
like plain text: "check" does no Markdown-aware fence parsing, and a fence is
not stripped or skipped before line analysis. A claim wrapped in three
backticks is exactly as capable of misleading a reader as one outside a
fence, so exempting fenced text would hand an easy way to hide an unbacked
or contradicted claim from this checker. This mirrors check_artifacts.py's
own ruling that a forbidden token counts wherever it appears, fenced or not;
only a required heading is void inside a fence, because a heading is a
document-structure claim that a fence removes from the structure.
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


LEXICON_PATH = Path(__file__).resolve().parent.parent / "references" / "claim-lexicon.json"

NUMERIC_CLAIM_RE = re.compile(r"\b(\d[\d,]*)\s+(passed|failed|skipped|tests?)\b", re.IGNORECASE)
COVERAGE_RE_1 = re.compile(r"coverage\s+(?:is|of|at)?\s*(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
COVERAGE_RE_2 = re.compile(r"(\d+(?:\.\d+)?)\s*%\s+coverage", re.IGNORECASE)

QUALIFIER_FIELD = {
    "passed": "passed",
    "failed": "failed",
    "skipped": "skipped",
    "test": "total",
    "tests": "total",
}

_ONES = [
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen",
]
_TENS = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_COMPOUNDS = [f"{t}-{o}" for t in _TENS for o in _ONES[:9]]
_NUMBER_WORDS = _ONES + _TENS + _COMPOUNDS + ["hundred", "thousand"]
NUMBER_WORD_RE = re.compile(
    r"\b(" + "|".join(sorted((re.escape(w) for w in _NUMBER_WORDS), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

SECTION_HEADING_RE = re.compile(r"^\s*#+\s*(results?|evidence)\s*$", re.IGNORECASE)
HEADING_RE = re.compile(r"^\s*#+\s")
TAG_RE = re.compile(r"\[E(\d+)\]")


def _git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"not a git repository: {repo_root}")
    return result.stdout.strip()


def _load_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"{label} not found at {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise RuntimeError(f"{label} is not valid JSON: {path}: {e}")


def _check_duplicate_ids(evidence: Dict[str, Any]) -> None:
    """Raise if two entries in EVIDENCE.json share an id (silent last-wins otherwise)."""
    seen = set()
    for entry in evidence.get("entries", []):
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id")
        if entry_id is None:
            continue
        if entry_id in seen:
            raise RuntimeError(f"EVIDENCE.json malformed: duplicate id {entry_id}")
        seen.add(entry_id)


def _write_gate_file(run_dir: Path, name: str, data: Dict[str, Any]) -> Tuple[Path, str]:
    gates_dir = run_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    gate_path = gates_dir / name
    payload = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
    gate_path.write_bytes(payload)
    sha256 = hashlib.sha256(payload).hexdigest()
    return gate_path, sha256


def _record_gate_result(run_dir: Path, gate: str, name: str, exit_code: int, summary: str) -> None:
    gate_path = run_dir / "gates" / name
    sha256 = hashlib.sha256(gate_path.read_bytes()).hexdigest()
    gate_state.append_receipt(
        run_dir, "gate-result",
        {"gate": gate, "gate_file": f"gates/{name}", "gate_sha256": sha256,
         "exit": exit_code, "summary": summary}
    )


# --- claim resolution helpers -------------------------------------------------

def _entry_field(entry: Dict[str, Any], field: str) -> Optional[Any]:
    if field == "total":
        if "total" in entry:
            return entry["total"]
        if all(k in entry for k in ("passed", "failed", "skipped")):
            return entry["passed"] + entry["failed"] + entry["skipped"]
        return None
    return entry.get(field)


def _resolve_single_field(tags: List[str], entries_by_id: Dict[str, Dict[str, Any]],
                          field: str, expected: Any, tolerance: float = 0) -> Tuple[str, Any]:
    """Resolve a single-field numeric claim against the entries cited on the line.

    Returns (status, detail): status in {"ok", "mismatch", "missing"}.
    "mismatch" detail is (entry_id, actual). "missing" detail is None.
    """
    mismatch_detail = None
    for tag in tags:
        entry = entries_by_id.get(tag)
        if entry is None:
            continue
        actual = _entry_field(entry, field)
        if actual is None:
            continue
        if tolerance:
            if abs(float(actual) - float(expected)) <= tolerance:
                return "ok", None
        else:
            if actual == expected:
                return "ok", None
        if mismatch_detail is None:
            mismatch_detail = (tag, actual)
    if mismatch_detail is not None:
        return "mismatch", mismatch_detail
    return "missing", None


def _check_requirements(entry: Dict[str, Any], requirements: List[Dict[str, Any]]) -> Tuple[str, Optional[Tuple[str, Any, Any]]]:
    """Check every field/value requirement of a lexicon phrase against one entry.

    Returns (status, detail): status in {"ok", "mismatch", "missing"}.
    detail is (field, actual, expected) for mismatch, (field, None, expected) for missing.
    """
    for req in requirements:
        field = req["field"]
        expected = req["value"]
        if field not in entry:
            return "missing", (field, None, expected)
        if entry[field] != expected:
            return "mismatch", (field, entry[field], expected)
    return "ok", None


def _resolve_phrase(tags: List[str], entries_by_id: Dict[str, Dict[str, Any]],
                    requirements: List[Dict[str, Any]]) -> Tuple[str, Optional[Tuple[str, Any, Any]]]:
    first_missing = None
    first_mismatch = None
    for tag in tags:
        entry = entries_by_id.get(tag)
        if entry is None:
            continue
        status, detail = _check_requirements(entry, requirements)
        if status == "ok":
            return "ok", None
        if status == "mismatch" and first_mismatch is None:
            first_mismatch = detail
        if status == "missing" and first_missing is None:
            first_missing = detail
    if first_mismatch is not None:
        return "mismatch", first_mismatch
    if first_missing is not None:
        return "missing", first_missing
    return "missing", None


def _analyze_line(line_no: int, line: str, entries_by_id: Dict[str, Dict[str, Any]],
                  lexicon: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    text = line.strip()

    tags_all = [f"E{d}" for d in TAG_RE.findall(line)]
    seen_tags: List[str] = []
    for t in tags_all:
        if t not in seen_tags:
            seen_tags.append(t)
    tags = [t for t in seen_tags if t in entries_by_id]
    unresolved_tags = [t for t in seen_tags if t not in entries_by_id]

    for t in unresolved_tags:
        findings.append({"line": line_no, "text": text, "type": "unresolved-tag", "claim": t,
                          "reason": f"cites {t} which names no entry"})

    # A line whose only citation(s) are unresolved has already been reported
    # above as unresolved-tag; do not also report its claims as uncited or
    # unbacked, which would name the wrong problem.
    only_unresolved = bool(tags_all) and not tags

    for m in NUMBER_WORD_RE.finditer(line):
        findings.append({
            "line": line_no, "text": text, "type": "unverifiable", "claim": m.group(0),
            "reason": "number words are not machine-checkable; use digits",
        })

    for m in NUMERIC_CLAIM_RE.finditer(line):
        if only_unresolved:
            continue
        raw_num, qualifier = m.group(1), m.group(2).lower()
        value = int(raw_num.replace(",", ""))
        field = QUALIFIER_FIELD[qualifier]
        claim = m.group(0)
        if not tags:
            findings.append({"line": line_no, "text": text, "type": "uncited", "claim": claim,
                              "reason": "quantitative claim has no [E<n>] citation"})
            continue
        status, detail = _resolve_single_field(tags, entries_by_id, field, value)
        if status == "missing":
            findings.append({"line": line_no, "text": text, "type": "unbacked", "claim": claim,
                              "reason": f"cited entry lacks field '{field}'"})
        elif status == "mismatch":
            entry_id, actual = detail
            findings.append({"line": line_no, "text": text, "type": "contradicted", "claim": claim,
                              "reason": f"entry {entry_id} field '{field}' is {actual!r}, claim says {value}"})

    for pattern in (COVERAGE_RE_1, COVERAGE_RE_2):
        for m in pattern.finditer(line):
            if only_unresolved:
                continue
            value = float(m.group(1))
            claim = m.group(0)
            if not tags:
                findings.append({"line": line_no, "text": text, "type": "uncited", "claim": claim,
                                  "reason": "quantitative claim has no [E<n>] citation"})
                continue
            status, detail = _resolve_single_field(tags, entries_by_id, "coverage", value, tolerance=0.5)
            if status == "missing":
                findings.append({"line": line_no, "text": text, "type": "unbacked", "claim": claim,
                                  "reason": "cited entry lacks field 'coverage'"})
            elif status == "mismatch":
                entry_id, actual = detail
                findings.append({"line": line_no, "text": text, "type": "contradicted", "claim": claim,
                                  "reason": f"entry {entry_id} field 'coverage' is {actual!r}, claim says {value}"})

    phrase_spans: List[Any] = []
    phrase_items = sorted(lexicon.get("phrases", {}).items(), key=lambda kv: -len(kv[0]))
    for phrase, requirements in phrase_items:
        match = re.search(r"\b" + re.escape(phrase) + r"\b", line, re.IGNORECASE)
        if match:
            span = match.span()
            if any(span[0] >= s[0] and span[1] <= s[1] for s in phrase_spans):
                continue  # already covered by a longer phrase match on this line
            phrase_spans.append(span)
            if only_unresolved:
                continue
            if not tags:
                findings.append({"line": line_no, "text": text, "type": "uncited", "claim": phrase,
                                  "reason": "quantitative claim has no [E<n>] citation"})
                continue
            status, detail = _resolve_phrase(tags, entries_by_id, requirements)
            if status == "missing":
                field = detail[0] if detail else "?"
                findings.append({"line": line_no, "text": text, "type": "unbacked", "claim": phrase,
                                  "reason": f"cited entry lacks field '{field}'"})
            elif status == "mismatch":
                field, actual, expected = detail
                findings.append({"line": line_no, "text": text, "type": "contradicted", "claim": phrase,
                                  "reason": f"cited entry field '{field}' is {actual!r}, requires {expected!r}"})

    for word in lexicon.get("unbackedWords", []):
        if re.search(r"\b" + re.escape(word) + r"\b", line, re.IGNORECASE) and not tags and not only_unresolved:
            findings.append({"line": line_no, "text": text, "type": "unbacked-word", "claim": word,
                              "reason": f"'{word}' is not a checkable claim; cite an [E<n>] entry or remove it"})

    return findings


def _extract_section(lines: List[str]) -> Optional[List[Tuple[int, str]]]:
    """Return (line_no, text) pairs for the body of the Results/Evidence section."""
    start = None
    for i, line in enumerate(lines):
        if SECTION_HEADING_RE.match(line):
            start = i + 1
            break
    if start is None:
        return None
    section = []
    for i in range(start, len(lines)):
        if HEADING_RE.match(lines[i]):
            break
        section.append((i + 1, lines[i]))
    return section


# --- merge-claim conditions ---------------------------------------------------

def _condition_ancestor_of_main(root: Path, run_dir: Path) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", "HEAD", "origin/main"],
            capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False, "git merge-base --is-ancestor timed out after 10s"
    except OSError as e:
        return False, f"git is not available: {e}"
    if result.returncode == 0:
        return True, "HEAD is an ancestor of origin/main"
    if result.returncode == 1:
        return False, "HEAD is not an ancestor of origin/main"
    return False, f"git merge-base --is-ancestor exited {result.returncode}: {result.stderr.strip()}"


def _condition_ci_mirror_pass(root: Path, run_dir: Path) -> Tuple[bool, str]:
    gate_path = run_dir / "gates" / "14.json"
    if not gate_path.is_file():
        return False, "gates/14.json not found"
    try:
        data = json.loads(gate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return False, f"gates/14.json unreadable: {e}"
    for row in data.get("stages", []):
        if isinstance(row, dict) and row.get("stage") == 13:
            if row.get("exit") == 0 and row.get("head_ok") is True:
                return True, "gates/14.json stage 13 exit 0, head_ok true"
            return False, f"gates/14.json stage 13 exit {row.get('exit')!r}, head_ok {row.get('head_ok')!r}"
    return False, "gates/14.json has no stage 13 row"


def _condition_pr_opened(root: Path, run_dir: Path) -> Tuple[bool, str]:
    receipts_file = run_dir / "receipts.jsonl"
    if not receipts_file.is_file():
        return False, "receipts.jsonl not found"
    try:
        raw = receipts_file.read_text(encoding="utf-8")
    except OSError as e:
        return False, f"receipts.jsonl unreadable: {e}"
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("kind") == "pr-opened":
            return True, "receipts.jsonl carries a pr-opened receipt"
    return False, "receipts.jsonl carries no pr-opened receipt"


_MERGE_CONDITIONS = {
    "ancestor-of-main": _condition_ancestor_of_main,
    "ci-mirror-pass": _condition_ci_mirror_pass,
    "pr-opened": _condition_pr_opened,
}


def _find_merge_claims(line_no: int, line: str, lexicon: Dict[str, Any],
                       condition_cache: Dict[str, Tuple[bool, str]],
                       root: Path, run_dir: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    text = line.strip()
    spans: List[Tuple[int, int]] = []
    items = sorted(lexicon.get("mergeClaims", {}).items(), key=lambda kv: -len(kv[0]))
    for phrase, condition in items:
        match = re.search(r"\b" + re.escape(phrase) + r"\b", line, re.IGNORECASE)
        if not match:
            continue
        span = match.span()
        if any(span[0] >= s[0] and span[1] <= s[1] for s in spans):
            continue  # already covered by a longer phrase match on this line
        spans.append(span)
        if condition not in condition_cache:
            condition_fn = _MERGE_CONDITIONS.get(condition)
            condition_cache[condition] = (
                (False, f"unknown condition {condition!r}") if condition_fn is None
                else condition_fn(root, run_dir)
            )
        holds, measured = condition_cache[condition]
        if holds:
            continue
        findings.append({
            "line": line_no, "text": text, "type": "merge-claim", "claim": phrase,
            "condition": condition, "measured": measured,
            "reason": f"claims {phrase!r} but {condition} does not hold: {measured}",
        })
    return findings


def cmd_check(repo_root: str, pr_body_path: str) -> int:
    root = Path(repo_root).resolve()

    try:
        head = _git_head(root)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    run_dir = gate_state.find_run(root)
    if run_dir is None:
        print(f"ERROR: no active run found under {root}", file=sys.stderr)
        return 2

    try:
        lexicon = _load_json(LEXICON_PATH, "claim-lexicon.json")
        evidence = _load_json(root / ".team-ship" / "EVIDENCE.json", "EVIDENCE.json")
        _check_duplicate_ids(evidence)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    body_path = Path(pr_body_path)
    if not body_path.is_file():
        print(f"ERROR: PR body not found at {body_path}", file=sys.stderr)
        return 2
    body_text = body_path.read_text(encoding="utf-8")
    body_lines = body_text.splitlines()

    section = _extract_section(body_lines)
    if section is None:
        print(f"ERROR: no Results or Evidence section found in {body_path}", file=sys.stderr)
        return 2

    entries_by_id = {
        e.get("id"): e for e in evidence.get("entries", []) if isinstance(e, dict) and e.get("id")
    }

    findings: List[Dict[str, Any]] = []
    for line_no, line in section:
        if not line.strip():
            continue
        findings.extend(_analyze_line(line_no, line, entries_by_id, lexicon))

    condition_cache: Dict[str, Tuple[bool, str]] = {}
    for line_no, line in enumerate(body_lines, start=1):
        if not line.strip():
            continue
        findings.extend(_find_merge_claims(line_no, line, lexicon, condition_cache, root, run_dir))

    exit_code = 1 if findings else 0
    summary = f"{len(findings)} finding(s)" if findings else "no findings"

    gate_data = {
        "argv": sys.argv, "cwd": os.getcwd(), "head": head,
        "exit": exit_code, "summary": summary, "findings": findings,
    }
    _, gate_sha256 = _write_gate_file(run_dir, "12.json", gate_data)
    try:
        _record_gate_result(run_dir, "claim-evidence", "12.json", exit_code, summary)
    except Exception as e:
        print(f"ERROR: failed to record gate-result receipt: {e}", file=sys.stderr)
        return 2

    for f in findings:
        print(f"{f['type']}: line {f['line']}: {f['claim']!r} {f['reason']}", file=sys.stderr)

    return exit_code


# --- matrix --------------------------------------------------------------------

_REQ_LIST_HEADER_RE = re.compile(r"^\s*(requirements|must_haves)\s*:\s*$")
_REQ_ITEM_RE = re.compile(r"^\s*-\s*([A-Za-z][\w.-]*)\s*:\s*(.*)$")


def _extract_requirements(plan_text: str) -> List[str]:
    section = None
    ids: List[str] = []
    for raw_line in plan_text.splitlines():
        header = _REQ_LIST_HEADER_RE.match(raw_line)
        if header:
            section = header.group(1)
            continue
        if section is None:
            continue
        if raw_line.strip() == "":
            continue
        item = _REQ_ITEM_RE.match(raw_line)
        if item and (raw_line.startswith(" ") or raw_line.startswith("-")):
            ids.append(item.group(1))
            continue
        if not raw_line.startswith(" ") and raw_line.strip() != "":
            section = None
    return ids


def _grade_requirement(req_id: str, gate_files: List[Tuple[str, Dict[str, Any]]]) -> Tuple[str, List[str]]:
    mapped = []
    for name, data in gate_files:
        req_list = data.get("requirements", [])
        summary = str(data.get("summary", ""))
        if (isinstance(req_list, list) and req_id in req_list) or req_id in summary:
            mapped.append((name, data.get("exit")))
    if not mapped:
        return "UNVERIFIED", []
    names = [name for name, _ in mapped]
    exits = [e for _, e in mapped]
    if any(e == 2 for e in exits):
        return "UNVERIFIED", names
    if any(e == 1 for e in exits):
        return "NOT MET", names
    # Every remaining exit is 0: gate exits are only 0, 1 or 2, and both 1 and 2
    # were excluded above, so this is the only grade left. The matrix has
    # exactly three grades: MET, NOT MET, UNVERIFIED.
    return "MET", names


def cmd_matrix(repo_root: str, plan_path: str) -> int:
    root = Path(repo_root).resolve()

    try:
        head = _git_head(root)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    run_dir = gate_state.find_run(root)
    if run_dir is None:
        print(f"ERROR: no active run found under {root}", file=sys.stderr)
        return 2

    plan_file = Path(plan_path)
    if not plan_file.is_file():
        print(f"ERROR: plan not found at {plan_file}", file=sys.stderr)
        return 2

    req_ids = _extract_requirements(plan_file.read_text(encoding="utf-8"))
    if not req_ids:
        print(f"ERROR: no requirements or must_haves found in {plan_file}", file=sys.stderr)
        return 2

    gates_dir = run_dir / "gates"
    gate_files: List[Tuple[str, Dict[str, Any]]] = []
    if gates_dir.is_dir():
        for gate_path in sorted(gates_dir.glob("*.json")):
            if gate_path.name == "11-matrix.json":
                continue
            try:
                gate_files.append((gate_path.name, json.loads(gate_path.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError):
                continue

    requirements_out = []
    not_met = []
    unverified = []
    for req_id in req_ids:
        grade, mapped_names = _grade_requirement(req_id, gate_files)
        requirements_out.append({"id": req_id, "grade": grade, "gates": mapped_names})
        if grade == "NOT MET":
            not_met.append(req_id)
        elif grade == "UNVERIFIED":
            unverified.append(req_id)

    if not_met:
        exit_code = 1
    elif unverified:
        exit_code = 2
    else:
        exit_code = 0

    met_count = sum(1 for r in requirements_out if r["grade"] == "MET")
    summary = (
        f"{len(requirements_out)} requirement(s): {met_count} met, "
        f"{len(not_met)} not met, {len(unverified)} unverified"
    )

    gate_data = {
        "argv": sys.argv, "cwd": os.getcwd(), "head": head,
        "exit": exit_code, "summary": summary, "requirements": requirements_out,
    }
    _, gate_sha256 = _write_gate_file(run_dir, "11-matrix.json", gate_data)
    try:
        _record_gate_result(run_dir, "requirements-matrix", "11-matrix.json", exit_code, summary)
    except Exception as e:
        print(f"ERROR: failed to record gate-result receipt: {e}", file=sys.stderr)
        return 2

    for req_id in not_met:
        print(f"NOT MET: {req_id}", file=sys.stderr)
    for req_id in unverified:
        print(f"UNVERIFIED: {req_id}", file=sys.stderr)

    return exit_code


# --- self-test -----------------------------------------------------------------

def _self_test_fixture_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures" / "claim_evidence"


def _ensure_fixtures() -> int:
    fixture_dir = _self_test_fixture_dir()
    make_fixtures = fixture_dir / "make_fixtures.py"
    if not make_fixtures.is_file():
        print(f"ERROR: make_fixtures.py not found at {make_fixtures}", file=sys.stderr)
        return 2
    result = subprocess.run([sys.executable, str(make_fixtures)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: make_fixtures.py failed: {result.stderr}", file=sys.stderr)
        return 2
    return 0


def _seed_pr_opened_receipt(run_dir: Path) -> None:
    gate_state.append_receipt(run_dir, "pr-opened", {"url": "https://github.com/example/repo/pull/1"})


def cmd_self_test() -> int:
    rc = _ensure_fixtures()
    if rc != 0:
        return rc

    fixture_dir = _self_test_fixture_dir()
    all_pass = True

    # check cases: (name, build_from, pr_body_filename, expected_exit, stderr_contains[, setup_fn(run_dir)])
    check_cases = [
        ("all-claims-backed", "all-claims-backed", "PR-BODY.md", 0, None),
        ("number-mismatch", "number-mismatch", "PR-BODY.md", 1, "contradicted"),
        ("unbacked-adjective", "unbacked-adjective", "PR-BODY.md", 1, "unbacked-word"),
        ("uncited-claim", "uncited-claim", "PR-BODY.md", 1, "uncited"),
        ("number-words", "number-words", "PR-BODY.md", 1, "unverifiable"),
        ("two-claims-one-tag", "two-claims-one-tag", "PR-BODY.md", 1, "coverage"),
        ("duplicate-evidence-id", "duplicate-evidence-id", "PR-BODY.md", 2, "duplicate id"),
        ("unresolved-tag", "unresolved-tag", "PR-BODY.md", 1, "unresolved-tag"),
        ("no-failures-phrase", "no-failures-phrase", "PR-BODY.md", 0, None),
        ("no-failures-phrase-contradicted", "no-failures-phrase", "PR-BODY-2.md", 1, "contradicted"),
        ("merged-not-ancestor", "merged-not-ancestor", "PR-BODY.md", 1, "merge-claim"),
        ("merged-ancestor", "merged-ancestor", "PR-BODY.md", 0, None),
        ("ci-green-without-stage-13", "ci-green-without-stage-13", "PR-BODY.md", 1, "merge-claim"),
        ("shipped-without-pr", "shipped-without-pr", "PR-BODY.md", 1, "merge-claim"),
        ("shipped-with-pr-receipt", "shipped-with-pr-receipt", "PR-BODY.md", 0, None, _seed_pr_opened_receipt),
    ]

    for case in check_cases:
        name, build_from, body_name, expected_exit, stderr_contains = case[:5]
        setup_fn = case[5] if len(case) > 5 else None
        build_dir = fixture_dir / build_from / "_build"
        if not build_dir.is_dir():
            print(f"{name}: FIXTURE NOT FOUND", file=sys.stderr)
            all_pass = False
            continue
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_copy = Path(tmpdir) / "repo"
            shutil.copytree(build_dir, repo_copy)
            state_root = Path(tmpdir) / "state"
            state_root.mkdir()
            os.environ["TEAM_STATE_ROOT"] = str(state_root)
            try:
                run_id = gate_state.start_run(str(repo_copy), "test", [])
            except Exception as e:
                print(f"{name}: FAIL - could not start run: {e}", file=sys.stderr)
                all_pass = False
                continue
            if setup_fn is not None:
                setup_fn(state_root / run_id)

            body_path = repo_copy / ".team-ship" / body_name
            result = subprocess.run([sys.executable, __file__, "check", str(body_path), "--repo-root", str(repo_copy)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != expected_exit:
                print(f"{name}: expected {expected_exit} got {result.returncode} FAIL", file=sys.stderr)
                if result.stderr:
                    print(f"  stderr: {result.stderr}", file=sys.stderr)
                all_pass = False
                continue
            if stderr_contains and stderr_contains not in result.stderr:
                print(
                    f"{name}: expected {expected_exit} got {expected_exit} FAIL "
                    f"(stderr missing {stderr_contains!r})", file=sys.stderr
                )
                print(f"  got: {result.stderr}", file=sys.stderr)
                all_pass = False
                continue
            print(f"{name}: expected {expected_exit} got {expected_exit} OK")

    # matrix cases: (name, extra_gate_setup, expected_exit, stderr_contains)
    matrix_cases = [
        ("requirement-not-met", "not-met", 1, "NOT MET"),
        ("requirement-unverified", "unverified", 2, "UNVERIFIED"),
    ]

    for name, setup, expected_exit, stderr_contains in matrix_cases:
        build_dir = fixture_dir / name / "_build"
        if not build_dir.is_dir():
            print(f"{name}: FIXTURE NOT FOUND", file=sys.stderr)
            all_pass = False
            continue
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_copy = Path(tmpdir) / "repo"
            shutil.copytree(build_dir, repo_copy)
            state_root = Path(tmpdir) / "state"
            state_root.mkdir()
            os.environ["TEAM_STATE_ROOT"] = str(state_root)
            try:
                run_id = gate_state.start_run(str(repo_copy), "test", [])
            except Exception as e:
                print(f"{name}: FAIL - could not start run: {e}", file=sys.stderr)
                all_pass = False
                continue

            run_dir = state_root / run_id
            gates_dir = run_dir / "gates"
            gates_dir.mkdir(parents=True, exist_ok=True)
            # M1 is always mapped and green, so only R1 varies with the condition
            # under test.
            (gates_dir / "7.json").write_text(json.dumps(
                {"requirements": ["M1"], "exit": 0, "summary": "ruff clean"}
            ))
            if setup == "not-met":
                (gates_dir / "8.json").write_text(json.dumps(
                    {"requirements": ["R1"], "exit": 1, "summary": "tests failed"}
                ))
            # "unverified": no gate file maps R1 at all.

            plan_path = repo_copy / ".team-ship" / "PLAN.md"
            result = subprocess.run([sys.executable, __file__, "matrix", str(plan_path), "--repo-root", str(repo_copy)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != expected_exit:
                print(f"{name}: expected {expected_exit} got {result.returncode} FAIL", file=sys.stderr)
                if result.stderr:
                    print(f"  stderr: {result.stderr}", file=sys.stderr)
                all_pass = False
                continue
            if stderr_contains and stderr_contains not in result.stderr:
                print(
                    f"{name}: expected {expected_exit} got {expected_exit} FAIL "
                    f"(stderr missing {stderr_contains!r})", file=sys.stderr
                )
                print(f"  got: {result.stderr}", file=sys.stderr)
                all_pass = False
                continue
            print(f"{name}: expected {expected_exit} got {expected_exit} OK")

    return 0 if all_pass else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="Run self-tests")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("pr_body")
    check_parser.add_argument("--repo-root", default=".")

    matrix_parser = subparsers.add_parser("matrix")
    matrix_parser.add_argument("plan")
    matrix_parser.add_argument("--repo-root", default=".")

    args = parser.parse_args()

    if args.self_test:
        return cmd_self_test()

    try:
        if args.command == "check":
            return cmd_check(args.repo_root, args.pr_body)
        if args.command == "matrix":
            return cmd_matrix(args.repo_root, args.plan)
        parser.print_help()
        return 2
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
