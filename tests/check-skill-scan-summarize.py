#!/usr/bin/env python3
"""Local tests for .github/skill-scan/summarize.py (stdlib only, no framework)."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

SUMMARIZE = pathlib.Path(__file__).resolve().parents[1] / ".github" / "skill-scan" / "summarize.py"


def run_case(report_text: str, exit_code: int = 0) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / "exit-codes.txt").write_text(f"{exit_code}\tskills/sample\n", encoding="utf-8")
        (d / "sample.json").write_text(report_text, encoding="utf-8")
        proc = subprocess.run([sys.executable, str(SUMMARIZE), str(d)], capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout + proc.stderr


def clean(**overrides: object) -> dict:
    base: dict = {
        "issues": [],
        "risk_assessment": {"score": 10, "severity": "low", "recommendation": "approve"},
        "suppressed_count": 0,
        "suppressed": [],
    }
    base.update(overrides)
    return base


def main() -> None:
    # 1. clean -> 0
    rc, out = run_case(json.dumps(clean()), 0)
    assert rc == 0 and "overall risk score 10 (low, approve)" in out and "1 report(s) checked, 0 problem(s)" in out, out
    print("PASS 1: clean report exits 0")

    # 2. one critical TT3 with location -> 1, line contains TT3 scripts/x.py:205
    rep2 = clean(
        issues=[{"id": "TT3", "severity": "critical", "location": {"file": "scripts/x.py", "start_line": 205},
                 "explanation": "Env var flows to urlopen.\nSecond line omitted.", "evidence": "must not print"}],
        risk_assessment={"score": 75, "severity": "critical", "recommendation": "block"},
    )
    rc, out = run_case(json.dumps(rep2), 1)
    assert rc == 1 and "::error::sample.json: [critical] TT3 scripts/x.py:205 Env var flows to urlopen." in out, out
    assert "Second line omitted" not in out and "must not print" not in out, out
    print("PASS 2: critical TT3 with location prints rule id, file:line, and first explanation line")

    # 3. corrupt JSON -> 1
    rc, out = run_case("{not valid json", 0)
    assert rc == 1 and "::error::sample.json: not a readable JSON report" in out, out
    print("PASS 3: corrupt JSON fails closed")

    # 4. no issues key -> 1
    rep4 = clean()
    del rep4["issues"]
    rc, out = run_case(json.dumps(rep4), 0)
    assert rc == 1 and "::error::sample.json: missing or invalid issues list" in out, out
    print("PASS 4: missing issues key fails closed")

    # 5. high issue with no location (and bool start_line) -> 1, prints no file:line
    rc, out = run_case(json.dumps(clean(issues=[{"id": "R9", "severity": "high", "explanation": "No loc."}])), 0)
    assert rc == 1 and "::error::sample.json: [high] R9 no file:line" in out, out
    rc_b, out_b = run_case(json.dumps(clean(issues=[{"id": "R9", "severity": "high", "location": {"file": "SKILL.md", "start_line": True}}])), 0)
    assert rc_b == 1 and "no file:line" in out_b, out_b
    print("PASS 5: high issue without valid location fails closed with no file:line")

    # 6. non-empty suppressed (and non-zero suppressed_count) -> 1
    rc, out = run_case(json.dumps(clean(suppressed=[{"id": "TT3"}], suppressed_count=1)), 0)
    assert rc == 1 and "unexpected suppressed" in out, out
    rc_b, out_b = run_case(json.dumps(clean(suppressed=[], suppressed_count=2)), 0)
    assert rc_b == 1 and "unexpected suppressed_count" in out_b, out_b
    print("PASS 6: non-empty suppressed and non-zero suppressed_count fail closed")

    # 7. exit-codes 1 with a clean report -> 1
    rc, out = run_case(json.dumps(clean()), 1)
    assert rc == 1 and "skillspector exited 1" in out, out
    print("PASS 7: exit-codes 1 with clean report fails closed")

    # 8. risk severity critical with empty issues -> 1
    rep8 = clean(issues=[], risk_assessment={"score": 80, "severity": "critical", "recommendation": "block"})
    rc, out = run_case(json.dumps(rep8), 0)
    assert rc == 1 and "::error::sample.json: overall risk score 80 (critical, block)" in out, out
    print("PASS 8: critical risk_assessment with empty issues fails closed")

    # 9. newline, %, CR, and control chars in scanned fields are escaped once
    rep9 = clean(
        issues=[{
            "id": "R9",
            "severity": "high",
            "location": {"file": "x\n::warning::y", "start_line": 12},
            "explanation": "100% bad\x07line",
        }]
    )
    rc, out = run_case(json.dumps(rep9), 0)
    assert rc == 1, f"case 9 expected rc 1, got {rc}: {out}"
    assert not any(ln.startswith("::warning::") for ln in out.splitlines()), out
    assert "x%0A::warning::y:12 100%25 bad?line" in out, out
    rep9b = clean(issues=[{"id": "R9", "severity": "high", "location": {"file": "a%b\r\x7fc", "start_line": 3}}])
    rc_b, out_b = run_case(json.dumps(rep9b), 0)
    assert rc_b == 1 and "a%25b%0D?c:3" in out_b, out_b
    print("PASS 9: workflow command injection chars escaped once at print time")

    # 10. unknown severity in issue or risk_assessment -> 1
    rc, out = run_case(json.dumps(clean(issues=[{"id": "X1", "severity": "bogus"}])), 0)
    assert rc == 1 and "::error::sample.json: [bogus] X1 unknown severity" in out, out
    rep10b = clean(risk_assessment={"score": 10, "severity": "bogus", "recommendation": "review"})
    rc_b, out_b = run_case(json.dumps(rep10b), 0)
    assert rc_b == 1 and "::error::sample.json: [bogus] risk_assessment unknown severity" in out_b, out_b
    print("PASS 10: unknown severity in issue or risk_assessment fails closed")

    print("check-skill-scan-summarize: all 10 cases passed")


if __name__ == "__main__":
    main()
