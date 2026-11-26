#!/usr/bin/env python3
"""Summarize SkillSpector JSON reports by schema; fail closed on severe or malformed output.

Shared by the scan and fixture jobs in .github/workflows/skill-scan.yml.
"""
from __future__ import annotations

import json
import pathlib
import sys

SEVERE = {"high", "critical"}


def _is_num(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_line(v: object) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 1


def _text(v: object) -> str:
    return v.strip() if isinstance(v, str) else ""


def summarize_dir(root: pathlib.Path) -> int:
    problems: list[str] = []
    if not root.is_dir():
        print(f"::error::{root}: report directory not found")
        print("0 report(s) checked, 1 problem(s)")
        return 1

    codes_path = root / "exit-codes.txt"
    lines = [ln for ln in codes_path.read_text(encoding="utf-8").splitlines() if ln.strip()] if codes_path.is_file() else []
    for line in lines:
        code, _, where = line.partition("\t")
        code, where = code.strip(), where.strip() or "<unknown>"
        if code == "1":
            problems.append(f"{where}: skillspector exited 1, so the folder is above the default risk threshold")
        elif code != "0":
            problems.append(f"{where}: unexpected skillspector exit code {code!r}")

    reports = sorted(root.glob("*.json"))
    if not reports:
        problems.append("no report was written for any changed skill folder")
    elif len(reports) != len(lines):
        problems.append(f"{len(lines)} skill folder(s) scanned but {len(reports)} report(s) written")

    for report in reports:
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            problems.append(f"{report.name}: not a readable JSON report ({error})")
            continue
        if not isinstance(data, dict):
            problems.append(f"{report.name}: not a readable JSON report (expected object)")
            continue

        sup = data.get("suppressed")
        if "suppressed" in data and sup is not None and (not isinstance(sup, list) or len(sup) > 0):
            problems.append(f"{report.name}: unexpected suppressed findings")
        sc = data.get("suppressed_count")
        if "suppressed_count" in data and sc is not None and not (isinstance(sc, int) and not isinstance(sc, bool) and sc == 0):
            problems.append(f"{report.name}: unexpected suppressed_count ({sc!r})")

        issues = data.get("issues")
        if not isinstance(issues, list):
            problems.append(f"{report.name}: missing or invalid issues list")
        else:
            for issue in issues:
                if not isinstance(issue, dict):
                    problems.append(f"{report.name}: invalid issue entry")
                    continue
                sev = _text(issue.get("severity")).lower()
                if sev not in SEVERE:
                    continue
                rule_id = _text(issue.get("id")) or "unknown"
                loc = issue.get("location")
                loc_file = _text(loc.get("file")) if isinstance(loc, dict) else ""
                start_line = loc.get("start_line") if isinstance(loc, dict) else None
                if loc_file and _is_line(start_line):
                    exp = issue.get("explanation")
                    first = next((ln.strip() for ln in exp.splitlines() if ln.strip()), "") if isinstance(exp, str) else ""
                    tail = f" {first}" if first else ""
                    problems.append(f"{report.name}: [{sev}] {rule_id} {loc_file}:{start_line}{tail}")
                else:
                    problems.append(f"{report.name}: [{sev}] {rule_id} no file:line")

        ra = data.get("risk_assessment")
        if not isinstance(ra, dict) or not _is_num(ra.get("score")):
            problems.append(f"{report.name}: missing or invalid risk_assessment")
        else:
            ra_sev = _text(ra.get("severity")).lower() or "unknown"
            ra_rec = _text(ra.get("recommendation")) or "unknown"
            summary = f"{report.name}: overall risk score {ra['score']} ({ra_sev}, {ra_rec})"
            print(summary)
            if ra_sev in SEVERE:
                problems.append(summary)

    for problem in problems:
        print(f"::error::{problem}")
    print(f"{len(reports)} report(s) checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("::error::usage: summarize.py <report-dir>")
        sys.exit(1)
    sys.exit(summarize_dir(pathlib.Path(sys.argv[1])))
