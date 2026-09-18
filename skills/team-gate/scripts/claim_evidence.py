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

    A claimed field (passed, failed, skipped, errors, tests, coverage) is
    resolved against its cited entry through a fixed search order, because
    run_gate.py's own evidence command nests a gate's real numbers under
    entry.detail rather than at the entry's top level, and a checker that
    only reads the top level reports every real claim as unbacked. The
    order is: (1) the entry's own top level, for hand-built or already-flat
    entries; (2) entry.detail; (3) entry.detail.parsed, run_gate.py's
    parsed test-summary shape; (4) the sum over entry.detail.commands[]
    .summary when every command carries a summary and every summary shares
    the same shape, so a multi-command gate's total is the sum of its
    commands rather than a false miss; and, for coverage specifically, (5)
    entry.detail.coverage or entry.detail.total as a last resort. The first
    path that carries the field wins; a field absent from every path is
    unbacked exactly as before. Every field lookup made while checking a
    numeric claim, a coverage claim, or a lexicon phrase (e.g. "all tests
    pass") goes through this same order. Which path resolved a claim is
    recorded: a contradicted finding carries it under "resolved_via", and a
    claim that resolves cleanly (no finding at all) is logged instead in a
    "resolved" list alongside the findings, so gates/12.json shows not only
    what broke but how everything else was confirmed.

    Any finding is exit 1. Writes gates/12.json in the run directory.

  matrix <plan.md> [--repo-root PATH]
    Extracts requirement identifiers from the plan's "requirements" and
    "must_haves" lists and grades each MET, NOT MET, or UNVERIFIED: exactly
    three grades, since gate exits are only 0, 1 or 2 and every requirement
    lands in one of these three. NOT MET is exit 1; UNVERIFIED alone (no
    NOT MET present) is exit 2. Writes gates/11-matrix.json.

    A requirement item may carry a tests: list of nodeids, in either of two
    accepted shapes: a YAML mapping item ("- id: R1" followed by indented
    "text:" and "tests: [nodeid, ...]" lines) or a scalar item ("R1: <text>
    [tests: nodeid, nodeid]"). A requirement that names tests is graded
    through the tests route: MET when every named test appears in
    gates/9.json with red.class valid-red-assertion or
    valid-red-missing-name and the latest gates/8.json has exit 0 and no
    failures; NOT MET when any named test is classified never-red or
    invalid-red, or gates/8.json records a failure; UNVERIFIED when a named
    test is absent from gates/9.json, or gates/8.json or gates/9.json is
    missing or itself exit 2 (an unrunnable gate can prove nothing, so it
    outranks any single test's classification). UNVERIFIED is checked
    before NOT MET for exactly that reason: a run that could not finish is
    a weaker signal than a run that finished and named a specific failure,
    not a stronger one, so the inconclusive read must not be shadowed by a
    conclusive-looking one built on an incomplete gate.

    A requirement that names no tests falls back to the existing route:
    mapping by a gate's own requirements list or its summary text, so a
    requirement backed either way still gets a real grade. gates/11-matrix
    .json rows record which route decided the grade ("tests", "gates", or
    "none" when neither route maps the requirement) and the tests list the
    requirement named, if any.

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

def _with_total(container: Dict[str, Any]) -> Dict[str, Any]:
    """Return container, or a shallow copy with 'total' synthesized from
    passed+failed+skipped when container carries all three but not 'total'
    itself. Used at every tier _gate_field checks, so a claim of "N tests"
    resolves the same way regardless of which tier carried the counts."""
    if "total" in container or not all(k in container for k in ("passed", "failed", "skipped")):
        return container
    return {**container, "total": container["passed"] + container["failed"] + container["skipped"]}


def _gate_field(gate_data: Dict[str, Any], field: str) -> Tuple[Optional[Any], Optional[str]]:
    """Resolve `field` within one detail-shaped object (a gate file, or an
    EVIDENCE.json entry's detail): its own keys; its 'parsed' dict; or the
    sum over its 'commands[].summary' when every command carries a summary
    and every summary shares the same 'shape'. Returns (value, tier), tier
    in {"self", "parsed", "commands"}, or (None, None) if no tier carries
    the field.
    """
    self_view = _with_total(gate_data)
    if field in self_view:
        return self_view[field], "self"

    parsed = gate_data.get("parsed")
    if isinstance(parsed, dict):
        parsed_view = _with_total(parsed)
        if field in parsed_view:
            return parsed_view[field], "parsed"

    commands = gate_data.get("commands")
    if isinstance(commands, list) and commands:
        summaries = []
        for cmd in commands:
            summary = cmd.get("summary") if isinstance(cmd, dict) else None
            if not isinstance(summary, dict):
                return None, None
            summaries.append(_with_total(summary))
        shapes = {s.get("shape") for s in summaries}
        if len(shapes) == 1 and all(field in s for s in summaries):
            return sum(s[field] for s in summaries), "commands"

    return None, None


_GATE_FIELD_PATH = {"self": "entry.detail", "parsed": "entry.detail.parsed",
                    "commands": "entry.detail.commands[].summary"}


def _entry_field(entry: Dict[str, Any], field: str) -> Tuple[Optional[Any], Optional[str]]:
    """Resolve `field` against a cited EVIDENCE.json entry through a fixed
    search order: (1) the entry's own top level; (2) entry.detail; (3)
    entry.detail.parsed; (4) the sum over entry.detail.commands[].summary
    when every command carries a summary of the same shape; and, for
    coverage, (5) entry.detail.coverage or entry.detail.total. The first
    path that carries the field wins. Returns (value, path); (None, None)
    when the field is absent from every path, which the caller reports as
    unbacked.
    """
    value, tier = _gate_field(entry, field)
    if value is not None:
        return value, "entry" if tier == "self" else f"entry.{tier}"

    detail = entry.get("detail")
    if not isinstance(detail, dict):
        return None, None

    value, tier = _gate_field(detail, field)
    if value is not None:
        return value, _GATE_FIELD_PATH[tier]

    if field == "coverage":
        if "coverage" in detail:
            return detail["coverage"], "entry.detail.coverage"
        if "total" in detail:
            return detail["total"], "entry.detail.total"

    return None, None


def _resolve_single_field(tags: List[str], entries_by_id: Dict[str, Dict[str, Any]],
                          field: str, expected: Any, tolerance: float = 0
                          ) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Resolve a single-field numeric claim against the entries cited on the line.

    Returns (status, info): status in {"ok", "mismatch", "missing"}. "ok"
    and "mismatch" info is {"entry": tag, "path": path}; mismatch also
    carries "actual". "missing" info is None.
    """
    mismatch_info = None
    for tag in tags:
        entry = entries_by_id.get(tag)
        if entry is None:
            continue
        actual, path = _entry_field(entry, field)
        if actual is None:
            continue
        matched = abs(float(actual) - float(expected)) <= tolerance if tolerance else actual == expected
        if matched:
            return "ok", {"entry": tag, "path": path}
        if mismatch_info is None:
            mismatch_info = {"entry": tag, "actual": actual, "path": path}
    if mismatch_info is not None:
        return "mismatch", mismatch_info
    return "missing", None


def _check_requirements(entry: Dict[str, Any], requirements: List[Dict[str, Any]]
                        ) -> Tuple[str, Optional[Tuple[str, Any, Any]], Dict[str, str]]:
    """Check every field/value requirement of a lexicon phrase against one
    entry, resolving each field through _entry_field's search order.

    Returns (status, detail, paths): status in {"ok", "mismatch", "missing"}.
    detail is (field, actual, expected) for mismatch, (field, None, expected)
    for missing. paths maps every field checked before (and including) the
    one that decided the outcome to the path that resolved it.
    """
    paths: Dict[str, str] = {}
    for req in requirements:
        field = req["field"]
        expected = req["value"]
        actual, path = _entry_field(entry, field)
        if actual is None:
            return "missing", (field, None, expected), paths
        paths[field] = path
        if actual != expected:
            return "mismatch", (field, actual, expected), paths
    return "ok", None, paths


def _resolve_phrase(tags: List[str], entries_by_id: Dict[str, Dict[str, Any]],
                    requirements: List[Dict[str, Any]]
                    ) -> Tuple[str, Optional[Tuple[str, Any, Any]], Optional[str], Dict[str, str]]:
    first_missing = None
    first_mismatch = None
    first_mismatch_paths: Dict[str, str] = {}
    for tag in tags:
        entry = entries_by_id.get(tag)
        if entry is None:
            continue
        status, detail, paths = _check_requirements(entry, requirements)
        if status == "ok":
            return "ok", None, tag, paths
        if status == "mismatch" and first_mismatch is None:
            first_mismatch = detail
            first_mismatch_paths = paths
        if status == "missing" and first_missing is None:
            first_missing = detail
    if first_mismatch is not None:
        return "mismatch", first_mismatch, None, first_mismatch_paths
    if first_missing is not None:
        return "missing", first_missing, None, {}
    return "missing", None, None, {}


def _analyze_line(line_no: int, line: str, entries_by_id: Dict[str, Dict[str, Any]],
                  lexicon: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    findings: List[Dict[str, Any]] = []
    resolved: List[Dict[str, Any]] = []
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
        status, info = _resolve_single_field(tags, entries_by_id, field, value)
        if status == "missing":
            findings.append({"line": line_no, "text": text, "type": "unbacked", "claim": claim,
                              "reason": f"cited entry lacks field '{field}'"})
        elif status == "mismatch":
            findings.append({"line": line_no, "text": text, "type": "contradicted", "claim": claim,
                              "reason": f"entry {info['entry']} field '{field}' is {info['actual']!r}, claim says {value}",
                              "resolved_via": info["path"]})
        else:
            resolved.append({"line": line_no, "claim": claim, "entry": info["entry"],
                              "field": field, "path": info["path"]})

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
            status, info = _resolve_single_field(tags, entries_by_id, "coverage", value, tolerance=0.5)
            if status == "missing":
                findings.append({"line": line_no, "text": text, "type": "unbacked", "claim": claim,
                                  "reason": "cited entry lacks field 'coverage'"})
            elif status == "mismatch":
                findings.append({"line": line_no, "text": text, "type": "contradicted", "claim": claim,
                                  "reason": f"entry {info['entry']} field 'coverage' is {info['actual']!r}, claim says {value}",
                                  "resolved_via": info["path"]})
            else:
                resolved.append({"line": line_no, "claim": claim, "entry": info["entry"],
                                  "field": "coverage", "path": info["path"]})

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
            status, detail, matched_tag, paths = _resolve_phrase(tags, entries_by_id, requirements)
            if status == "missing":
                field = detail[0] if detail else "?"
                findings.append({"line": line_no, "text": text, "type": "unbacked", "claim": phrase,
                                  "reason": f"cited entry lacks field '{field}'"})
            elif status == "mismatch":
                field, actual, expected = detail
                findings.append({"line": line_no, "text": text, "type": "contradicted", "claim": phrase,
                                  "reason": f"cited entry field '{field}' is {actual!r}, requires {expected!r}",
                                  "resolved_via": paths.get(field)})
            else:
                resolved.append({"line": line_no, "claim": phrase, "entry": matched_tag, "paths": paths})

    for word in lexicon.get("unbackedWords", []):
        if re.search(r"\b" + re.escape(word) + r"\b", line, re.IGNORECASE) and not tags and not only_unresolved:
            findings.append({"line": line_no, "text": text, "type": "unbacked-word", "claim": word,
                              "reason": f"'{word}' is not a checkable claim; cite an [E<n>] entry or remove it"})

    return findings, resolved


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
    resolved: List[Dict[str, Any]] = []
    for line_no, line in section:
        if not line.strip():
            continue
        line_findings, line_resolved = _analyze_line(line_no, line, entries_by_id, lexicon)
        findings.extend(line_findings)
        resolved.extend(line_resolved)

    condition_cache: Dict[str, Tuple[bool, str]] = {}
    for line_no, line in enumerate(body_lines, start=1):
        if not line.strip():
            continue
        findings.extend(_find_merge_claims(line_no, line, lexicon, condition_cache, root, run_dir))

    exit_code = 1 if findings else 0
    summary = f"{len(findings)} finding(s)" if findings else "no findings"

    gate_data = {
        "argv": sys.argv, "cwd": os.getcwd(), "head": head,
        "exit": exit_code, "summary": summary, "findings": findings, "resolved": resolved,
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
_REQ_SCALAR_ITEM_RE = re.compile(r"^\s*-\s*([A-Za-z][\w.-]*)\s*:\s*(.*)$")
_REQ_MAPPING_ID_RE = re.compile(r"^\s*-\s*id\s*:\s*([A-Za-z][\w.-]*)\s*$")
_REQ_MAPPING_FIELD_RE = re.compile(r"^\s*(text|tests)\s*:\s*(.*)$")
_SCALAR_TESTS_SUFFIX_RE = re.compile(r"^(.*?)\s*\[\s*tests\s*:\s*(.*?)\s*\]\s*$")


def _parse_tests_list(raw: str) -> List[str]:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [t.strip() for t in raw.split(",") if t.strip()]


def _extract_requirements(plan_text: str) -> List[Dict[str, Any]]:
    """Extract requirement identifiers from the plan's "requirements" and
    "must_haves" lists, along with each requirement's tests: list, if any.

    Two item shapes are accepted: a scalar line "- R1: <text>", optionally
    suffixed with "[tests: nodeid, nodeid]"; and a YAML mapping item
    spanning several lines ("- id: R1" followed by more-indented "text:"
    and "tests: [nodeid, ...]" lines). A requirement with no tests: field
    carries an empty tests list, which routes it to the existing
    gates-mapping grade instead of the tests route.
    """
    section = None
    reqs: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None

    def flush() -> None:
        nonlocal current
        if current is not None:
            reqs.append({"id": current["id"], "tests": current["tests"]})
            current = None

    for raw_line in plan_text.splitlines():
        header = _REQ_LIST_HEADER_RE.match(raw_line)
        if header:
            flush()
            section = header.group(1)
            continue
        if section is None:
            continue
        if raw_line.strip() == "":
            continue

        if raw_line.lstrip().startswith("-"):
            flush()
            mapping_id = _REQ_MAPPING_ID_RE.match(raw_line)
            if mapping_id:
                current = {"id": mapping_id.group(1), "tests": []}
                continue
            scalar = _REQ_SCALAR_ITEM_RE.match(raw_line)
            if scalar and (raw_line.startswith(" ") or raw_line.startswith("-")):
                req_id, rest = scalar.group(1), scalar.group(2)
                suffix = _SCALAR_TESTS_SUFFIX_RE.match(rest)
                tests = _parse_tests_list(suffix.group(2)) if suffix else []
                reqs.append({"id": req_id, "tests": tests})
                continue
            if not raw_line.startswith(" "):
                section = None
            continue

        if current is not None:
            field = _REQ_MAPPING_FIELD_RE.match(raw_line)
            if field and field.group(1) == "tests":
                current["tests"] = _parse_tests_list(field.group(2))
                continue
            if field and field.group(1) == "text":
                continue

        if not raw_line.startswith(" ") and raw_line.strip() != "":
            flush()
            section = None

    flush()
    return reqs


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


_VALID_RED_CLASSES = ("valid-red-assertion", "valid-red-missing-name")
_BROKEN_RED_CLASSES = ("never-red", "invalid-red")


def _load_gate_file(gates_dir: Path, name: str) -> Optional[Dict[str, Any]]:
    path = gates_dir / name
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _grade_via_tests(tests: List[str], gates8: Optional[Dict[str, Any]],
                     gates9: Optional[Dict[str, Any]]) -> str:
    """Grade a requirement's named tests against gates/9.json's red-green
    proof and gates/8.json's latest test run.

    UNVERIFIED is checked first: a missing gate file, an unrunnable exit
    (2) on either gate, or a named test absent from gates/9.json all mean
    the proof cannot be read, and an unreadable run is a weaker signal than
    a completed one, never a stronger one, so it must not be shadowed by a
    conclusive-looking NOT MET built on an incomplete gate. NOT MET follows:
    a named test classified never-red or invalid-red, or gates/8.json
    recording a failure. Only when neither holds, and every named test is a
    valid red-green proof with a clean latest run, is the requirement MET.
    """
    if gates8 is None or gates9 is None:
        return "UNVERIFIED"
    if gates8.get("exit") == 2 or gates9.get("exit") == 2:
        return "UNVERIFIED"

    tests_by_nodeid = {t.get("nodeid"): t for t in gates9.get("tests", []) if isinstance(t, dict)}
    classes = []
    for nodeid in tests:
        test = tests_by_nodeid.get(nodeid)
        if test is None:
            return "UNVERIFIED"
        red = test.get("red") or {}
        classes.append(red.get("class"))

    if any(c in _BROKEN_RED_CLASSES for c in classes):
        return "NOT MET"

    failed, _tier = _gate_field(gates8, "failed")
    if failed is not None and failed > 0:
        return "NOT MET"

    if gates8.get("exit") == 0 and all(c in _VALID_RED_CLASSES for c in classes):
        return "MET"

    return "UNVERIFIED"


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

    requirements = _extract_requirements(plan_file.read_text(encoding="utf-8"))
    if not requirements:
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

    gates8 = _load_gate_file(gates_dir, "8.json")
    gates9 = _load_gate_file(gates_dir, "9.json")

    requirements_out = []
    not_met = []
    unverified = []
    for req in requirements:
        req_id = req["id"]
        tests = req.get("tests") or []
        if tests:
            grade = _grade_via_tests(tests, gates8, gates9)
            mapped_names: List[str] = []
            route = "tests"
        else:
            grade, mapped_names = _grade_requirement(req_id, gate_files)
            route = "gates" if mapped_names else "none"
        requirements_out.append({
            "id": req_id, "grade": grade, "gates": mapped_names, "tests": tests, "route": route,
        })
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


def _seed_real_run_gate_evidence(repo_copy: Path) -> Dict[str, Any]:
    """Run run_gate.py's discover, run, and evidence for real against
    repo_copy (already inside an active run via TEAM_STATE_ROOT), and return
    the resulting .team-ship/EVIDENCE.json as a dict. Raises RuntimeError
    naming the failing subcommand and its stderr on any non-zero exit."""
    run_gate_py = Path(__file__).resolve().parent / "run_gate.py"
    for sub in ("discover", "run", "evidence"):
        proc = subprocess.run(
            [sys.executable, str(run_gate_py), "--repo-root", str(repo_copy), sub],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"run_gate.py {sub} exited {proc.returncode}: {proc.stderr}")
    evidence_path = repo_copy / ".team-ship" / "EVIDENCE.json"
    return json.loads(evidence_path.read_text(encoding="utf-8"))


def _prove_red_test_entry(nodeid: str, red_class: str, verdict: str) -> Dict[str, Any]:
    """One gates/9.json test record, in prove_red.py's exact tests[] shape."""
    file_part, qualname = nodeid.split("::", 1)
    return {
        "nodeid": nodeid, "file": file_part, "qualname": qualname,
        "status": "new", "kind": "test", "ast_hash": "0" * 64,
        "green": {"outcome": "pass", "exc_type": None, "message": None},
        "red": {"class": red_class, "exc_type": "AssertionError", "message": "m",
                "last_frame": None, "resolvedTo": None},
        "verdict": verdict,
    }


def _write_prove_red_gate(run_dir: Path, tests: List[Dict[str, Any]]) -> None:
    """Write gates/9.json in prove_red.py's exact shape (gate tdd-redgreen),
    hand-built because prove_red's own classifier fix is a separate task."""
    counts = {
        "tests": len(tests),
        "pass": sum(1 for t in tests if t["verdict"] == "PASS"),
        "block": sum(1 for t in tests if t["verdict"] == "BLOCK"),
        "unverified": 0, "unrunnable": 0,
        "never_red": sum(1 for t in tests if t["red"]["class"] == "never-red"),
        "invalid_red": sum(1 for t in tests if t["red"]["class"] == "invalid-red"),
        "green_fails": 0, "inseparable": 0,
    }
    if counts["block"] > 0:
        exit_code, summary = 1, f"BLOCK: {counts['block']} test(s) failed red-green proof"
    else:
        exit_code, summary = 0, f"PASS: {counts['pass']} test(s) proved red then green"
    gate_obj = {
        "gate": "tdd-redgreen", "argv": ["prove_red.py", "prove"], "cwd": "/repo",
        "head": "0" * 40, "base": {"sha": "0" * 40, "source": "explicit"},
        "env_pins": {"python": sys.executable}, "dirty": False,
        "worktree": "/tmp/wt", "revert": {"diffstat": ""},
        "tests": tests, "counts": counts, "exit": exit_code, "summary": summary,
    }
    gates_dir = run_dir / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    (gates_dir / "9.json").write_text(json.dumps(gate_obj, indent=2, sort_keys=True))


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

    # matrix cases via the old gates-mapping route: (name, build_from,
    # extra_gate_setup, expected_exit, stderr_contains, expected_route for R1)
    matrix_cases = [
        ("requirement-not-met", "requirement-not-met", "not-met", 1, "NOT MET", "gates"),
        ("requirement-unverified", "requirement-unverified", "unverified", 2, "UNVERIFIED", "none"),
        ("matrix-no-tests-no-gates", "requirement-unverified", "unverified", 2, "UNVERIFIED", "none"),
    ]

    for name, build_from, setup, expected_exit, stderr_contains, expected_route in matrix_cases:
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
            matrix_path = gates_dir / "11-matrix.json"
            try:
                row = json.loads(matrix_path.read_text(encoding="utf-8"))["requirements"][0]
            except Exception as e:
                print(f"{name}: FAIL - could not read 11-matrix.json: {e}", file=sys.stderr)
                all_pass = False
                continue
            if row.get("route") != expected_route:
                print(f"{name}: FAIL - route {row.get('route')!r}, expected {expected_route!r}", file=sys.stderr)
                all_pass = False
                continue
            print(f"{name}: expected {expected_exit} got {expected_exit} OK")

    # real-evidence cases: claim_evidence checked against run_gate.py's own
    # real EVIDENCE.json output (discover, run, evidence), not a hand-built
    # fixture, so the field-resolution search order is proven against the
    # actual nesting run_gate.py produces rather than against a schema this
    # file assumed.
    real_repo_build = fixture_dir / "real-run-gate-repo" / "_build"
    if not real_repo_build.is_dir():
        print("real-evidence: FIXTURE NOT FOUND", file=sys.stderr)
        all_pass = False
    else:
        real_evidence_cases = [
            ("real-evidence-backed", "2 passed. [{tag}]", 0, None),
            ("real-evidence-contradicted", "5 passed. [{tag}]", 1, "contradicted"),
        ]
        for name, template, expected_exit, stderr_contains in real_evidence_cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_copy = Path(tmpdir) / "repo"
                shutil.copytree(real_repo_build, repo_copy)
                state_root = Path(tmpdir) / "state"
                state_root.mkdir()
                os.environ["TEAM_STATE_ROOT"] = str(state_root)
                try:
                    gate_state.start_run(str(repo_copy), "test", [])
                    evidence = _seed_real_run_gate_evidence(repo_copy)
                except Exception as e:
                    print(f"{name}: FAIL - {e}", file=sys.stderr)
                    all_pass = False
                    continue

                tag = next((e["id"] for e in evidence.get("entries", [])
                           if e.get("gate") == "test-execution"), None)
                if tag is None:
                    print(f"{name}: FAIL - no test-execution entry in real EVIDENCE.json", file=sys.stderr)
                    all_pass = False
                    continue

                body_path = repo_copy / ".team-ship" / "PR-BODY.md"
                body_path.write_text(
                    "# PR\n\n## Results\n\n- " + template.format(tag=tag) + "\n", encoding="utf-8"
                )
                result = subprocess.run(
                    [sys.executable, __file__, "check", str(body_path), "--repo-root", str(repo_copy)],
                    capture_output=True, text=True, timeout=30,
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
                    all_pass = False
                    continue
                print(f"{name}: expected {expected_exit} got {expected_exit} OK")

    # matrix-tests cases: a requirement's tests: list graded against
    # gates/9.json (hand-built in prove_red.py's exact shape, since its
    # classifier fix is a separate task this file must not depend on) and
    # the real gates/8.json that run_gate.py's own run command wrote.
    good_nodeid = "tests/test_mean.py::TestMean.test_mean"
    other_nodeid = "tests/test_calc.py::TestAdd.test_add"
    plan_scalar_tests = (
        "# Plan\n\n---\nrequirements:\n"
        f"  - R1: mean returns the arithmetic mean [tests: {good_nodeid}]\n---\n"
    )
    plan_yaml_mapping = (
        "# Plan\n\n---\nrequirements:\n"
        "  - id: R1\n"
        "    text: mean returns the arithmetic mean\n"
        f"    tests: [{good_nodeid}]\n---\n"
    )
    matrix_tests_cases = [
        ("matrix-tests-met", plan_scalar_tests,
         [_prove_red_test_entry(good_nodeid, "valid-red-assertion", "PASS")], 0, "tests", "MET"),
        ("matrix-tests-not-met", plan_scalar_tests,
         [_prove_red_test_entry(good_nodeid, "invalid-red", "BLOCK")], 1, "tests", "NOT MET"),
        ("matrix-tests-unverified", plan_scalar_tests,
         [_prove_red_test_entry(other_nodeid, "valid-red-assertion", "PASS")], 2, "tests", "UNVERIFIED"),
        ("matrix-yaml-mapping", plan_yaml_mapping,
         [_prove_red_test_entry(good_nodeid, "valid-red-assertion", "PASS")], 0, "tests", "MET"),
    ]

    if not real_repo_build.is_dir():
        print("matrix-tests: FIXTURE NOT FOUND", file=sys.stderr)
        all_pass = False
    else:
        for name, plan_text, gate9_tests, expected_exit, expected_route, expected_grade in matrix_tests_cases:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_copy = Path(tmpdir) / "repo"
                shutil.copytree(real_repo_build, repo_copy)
                state_root = Path(tmpdir) / "state"
                state_root.mkdir()
                os.environ["TEAM_STATE_ROOT"] = str(state_root)
                try:
                    run_id = gate_state.start_run(str(repo_copy), "test", [])
                    _seed_real_run_gate_evidence(repo_copy)
                except Exception as e:
                    print(f"{name}: FAIL - {e}", file=sys.stderr)
                    all_pass = False
                    continue

                run_dir = state_root / run_id
                _write_prove_red_gate(run_dir, gate9_tests)

                plan_path = repo_copy / ".team-ship" / "PLAN.md"
                plan_path.write_text(plan_text, encoding="utf-8")

                result = subprocess.run(
                    [sys.executable, __file__, "matrix", str(plan_path), "--repo-root", str(repo_copy)],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode != expected_exit:
                    print(f"{name}: expected {expected_exit} got {result.returncode} FAIL", file=sys.stderr)
                    if result.stderr:
                        print(f"  stderr: {result.stderr}", file=sys.stderr)
                    all_pass = False
                    continue

                matrix_path = run_dir / "gates" / "11-matrix.json"
                try:
                    row = json.loads(matrix_path.read_text(encoding="utf-8"))["requirements"][0]
                except Exception as e:
                    print(f"{name}: FAIL - could not read 11-matrix.json: {e}", file=sys.stderr)
                    all_pass = False
                    continue
                if row.get("route") != expected_route or row.get("grade") != expected_grade:
                    print(f"{name}: FAIL - row {row!r}, expected route={expected_route!r} "
                          f"grade={expected_grade!r}", file=sys.stderr)
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
