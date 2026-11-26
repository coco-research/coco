#!/usr/bin/env python3
"""Local tests for .github/skill-scan/summarize.py (stdlib only, no framework)."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[1]
SUMMARIZE = REPO / ".github" / "skill-scan" / "summarize.py"
FIXTURES = REPO / "tests" / "fixtures" / "skillspector"
REAL_M0_SKILL = REPO / "systems" / "m0" / "skills" / "m0"

_spec = importlib.util.spec_from_file_location("skill_scan_summarize", SUMMARIZE)
assert _spec and _spec.loader
summarize_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(summarize_mod)


def run_case(
    report_text: str,
    exit_code: int = 0,
    skill_dir: str = "skills/sample",
    include_report_col: bool = False,
    allow_suppressed: list[str] | None = None,
) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        row = f"{exit_code}\t{skill_dir}\tsample.json\n" if include_report_col else f"{exit_code}\t{skill_dir}\n"
        (d / "exit-codes.txt").write_text(row, encoding="utf-8")
        (d / "sample.json").write_text(report_text, encoding="utf-8")
        cmd = [sys.executable, str(SUMMARIZE), str(d)]
        for allow in allow_suppressed or []:
            cmd.extend(["--allow-suppressed", allow])
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return proc.returncode, proc.stdout + proc.stderr


def tt3_suppressed(**overrides: object) -> dict:
    entry: dict = {
        "id": "TT3",
        "severity": "critical",
        "location": {"file": "scripts/m0_mcp.py", "start_line": 16},
        "suppressed": True,
        "suppression_reason": "Known loopback M0 bridge.",
    }
    entry.update(overrides)
    return entry


VALID_BRIDGE = (FIXTURES / "waiver_a" / "scripts" / "m0_mcp.py").read_text(encoding="utf-8")


def check_src(bridge_src: str, siblings: dict[str, str] | None = None) -> list[str]:
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        scripts = root / "scripts"
        scripts.mkdir()
        (scripts / "m0_mcp.py").write_text(bridge_src, encoding="utf-8")
        for rel, body in (siblings or {}).items():
            p = scripts / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        return summarize_mod.check_bridge(root)


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

    # 11. corrupt non-list suppressed fails closed
    for bad_sup in ("bad", {"id": "TT3"}, 1):
        rc, out = run_case(json.dumps(clean(suppressed=bad_sup, suppressed_count=0)), 0)
        assert rc == 1 and "unexpected suppressed" in out, out
    print("PASS 11: corrupt non-list suppressed fails closed")

    # 12. suppression gating via --allow-suppressed
    waiver_a = str(FIXTURES / "waiver_a")
    rep_ok = json.dumps(clean(suppressed=[tt3_suppressed()], suppressed_count=1))
    # 2-column exit-codes.txt cannot map report -> skill dir
    rc, out = run_case(rep_ok, 0, skill_dir=waiver_a, include_report_col=False, allow_suppressed=[waiver_a])
    assert rc == 1 and "unexpected suppressed" in out, out
    # disallowed dir
    rc, out = run_case(rep_ok, 0, skill_dir=str(FIXTURES / "waiver_g"), include_report_col=True, allow_suppressed=[waiver_a])
    assert rc == 1 and "unexpected suppressed" in out, out
    # allowed dir + valid TT3 passes and prints suppressed line
    rc, out = run_case(rep_ok, 0, skill_dir=waiver_a, include_report_col=True, allow_suppressed=[waiver_a])
    assert rc == 0 and "sample.json: suppressed 1: TT3 scripts/m0_mcp.py:16" in out, out
    # real systems/m0/skills/m0 passes too
    rc, out = run_case(rep_ok, 0, skill_dir=str(REAL_M0_SKILL), include_report_col=True, allow_suppressed=[str(REAL_M0_SKILL)])
    assert rc == 0 and "sample.json: suppressed 1: TT3 scripts/m0_mcp.py:16" in out, out
    # >1 suppressed entry fails
    rep_two = json.dumps(clean(suppressed=[tt3_suppressed(), tt3_suppressed()], suppressed_count=2))
    rc, out = run_case(rep_two, 0, skill_dir=waiver_a, include_report_col=True, allow_suppressed=[waiver_a])
    assert rc == 1 and "expected exactly 1 suppressed" in out, out
    # malformed suppressed entries fail
    bad_entries = [
        tt3_suppressed(id="R9"),
        tt3_suppressed(location={"file": "scripts/other.py", "start_line": 16}),
        tt3_suppressed(location={"file": "scripts/m0_mcp.py", "start_line": True}),
        tt3_suppressed(suppressed=False),
        tt3_suppressed(suppression_reason=""),
        tt3_suppressed(severity="bogus"),
    ]
    for entry in bad_entries:
        rc, out = run_case(json.dumps(clean(suppressed=[entry], suppressed_count=1)), 0, skill_dir=waiver_a, include_report_col=True, allow_suppressed=[waiver_a])
        assert rc == 1, f"expected fail for {entry}: {out}"
    # valid suppressed TT3 + non-TT3 high issue still fails
    rep_plus = json.dumps(clean(
        suppressed=[tt3_suppressed()],
        suppressed_count=1,
        issues=[{"id": "R9", "severity": "critical", "location": {"file": "scripts/m0_mcp.py", "start_line": 9}}],
    ))
    rc, out = run_case(rep_plus, 0, skill_dir=waiver_a, include_report_col=True, allow_suppressed=[waiver_a])
    assert rc == 1 and "[critical] R9 scripts/m0_mcp.py:9" in out, out
    print("PASS 12: --allow-suppressed gating enforces single TT3 bridge waiver")

    # 13. check_bridge AST rules on scripts/m0_mcp.py (env allowlist, dynamic access, outbound sinks, transport selector)
    assert check_src(VALID_BRIDGE) == []
    bad_bridges = [
        ("C10 cred", VALID_BRIDGE + '\nX = os.environ.get("M0_API_TOKEN", "")\n'),
        ("C10 other", VALID_BRIDGE + '\nX = os.environ.get("HOME", "")\n'),
        ("S1 copy", VALID_BRIDGE + "\nX = os.environ.copy()\n"),
        ("S1 dict", VALID_BRIDGE + "\nX = dict(os.environ)\n"),
        ("S1 sub", VALID_BRIDGE + '\nX = os.environ["M0_BASE_URL"]\n'),
        ("S1 from os", "from os import environ\n" + VALID_BRIDGE),
        ("S1 getattr", VALID_BRIDGE + '\nX = getattr(os, "environ")\n'),
        ("S1 __import__", VALID_BRIDGE + '\nX = __import__("http.client")\n'),
        ("S1 importlib", "import importlib\n" + VALID_BRIDGE + '\nX = importlib.import_module("os")\n'),
        ("S1 vars", VALID_BRIDGE + "\nX = vars(os)\n"),
        ("S1 globals", VALID_BRIDGE + "\nX = globals()\n"),
        ("S1 non-lit", VALID_BRIDGE + '\nK = "M0_BASE_URL"\nX = os.environ.get(K)\n'),
        ("S1 alias os", VALID_BRIDGE.replace("import os", "import os as _os")),
        ("C3 http.client", "import http.client\n" + VALID_BRIDGE),
        ("C3 socket", "import socket\n" + VALID_BRIDGE),
        ("C3 subprocess", "import subprocess\n" + VALID_BRIDGE),
        ("C3 build_opener", VALID_BRIDGE + "\nX = urllib.request.build_opener()\n"),
        ("C3 zero urlopen", VALID_BRIDGE.replace("with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:\n        return resp.read()", "return b''")),
        ("C3 two urlopen", VALID_BRIDGE + "\ndef extra(r):\n    return urllib.request.urlopen(r)\n"),
        ("C9 alias", VALID_BRIDGE + "\nT2 = TRANSPORT\n"),
        ("C9 fstring", VALID_BRIDGE + '\nMSG = f"{TRANSPORT}"\n'),
        ("C9 upper", VALID_BRIDGE.replace(".strip().lower()", ".upper()")),
        ("C9 local", VALID_BRIDGE.replace('TRANSPORT = os.environ.get("M0_MCP_TRANSPORT", "auto").strip().lower()\n', "").replace('if TRANSPORT == "direct":', 'TRANSPORT = os.environ.get("M0_MCP_TRANSPORT", "auto").strip().lower()\n    if TRANSPORT == "direct":')),
    ]
    for label, src in bad_bridges:
        errs = check_src(src)
        assert errs, f"bridge case {label} unexpectedly passed"
    print(f"PASS 13: check_bridge rejected all {len(bad_bridges)} invalid bridge variants")

    # 14. check_bridge AST rules on sibling scripts/*.py (Q2 C1-C3)
    assert check_src(VALID_BRIDGE, {"helper.py": 'import os\nPORT = os.environ.get("M0_PORT", "8787")\n'}) == []
    assert check_src(VALID_BRIDGE, {"m0_server.py": "import http.server\nS = http.server.HTTPServer\n"}) == []
    bad_siblings = [
        ("C1 get cred", {"helper.py": 'import os\nX = os.environ.get("API_KEY", "")\n'}),
        ("C1 getenv cred", {"helper.py": 'import os\nX = os.getenv("DB_PASSWORD")\n'}),
        ("C1 sub cred", {"helper.py": 'import os\nX = os.environ["AUTH_SECRET"]\n'}),
        ("C1 setdefault cred", {"helper.py": 'import os\nX = os.environ.setdefault("X_CRED", "")\n'}),
        ("C2 socket", {"helper.py": "import socket\n"}),
        ("C2 urllib.request", {"helper.py": "import urllib.request\n"}),
        ("C2 from urllib", {"helper.py": "from urllib import request\n"}),
        ("C2 alias urllib", {"helper.py": "import urllib as u\n"}),
        ("C2 http.server non-server", {"helper.py": "import http.server\n"}),
        ("C2 nested m0_server", {"sub/m0_server.py": "import http.server\n"}),
        ("C2 os.system", {"helper.py": 'import os\nos.system("id")\n'}),
        ("C2 os.popen", {"helper.py": 'import os\nos.popen("id")\n'}),
        ("C3 non-lit get", {"helper.py": 'import os\nK = "X"\nV = os.environ.get(K)\n'}),
        ("C3 non-lit sub", {"helper.py": 'import os\nK = "X"\nV = os.environ[K]\n'}),
        ("C3 dict(environ)", {"helper.py": "import os\nE = dict(os.environ)\n"}),
        ("C3 environ.copy", {"helper.py": "import os\nE = os.environ.copy()\n"}),
        ("C3 unpack environ", {"helper.py": "import os\nE = {**os.environ}\n"}),
        ("C3 importlib", {"helper.py": "import importlib\n"}),
        ("C3 __import__", {"helper.py": '__import__("os")\n'}),
        ("C3 exec", {"helper.py": 'exec("pass")\n'}),
        ("C3 eval", {"helper.py": 'eval("1")\n'}),
    ]
    for label, sibs in bad_siblings:
        errs = check_src(VALID_BRIDGE, sibs)
        assert errs, f"sibling case {label} unexpectedly passed"
    print(f"PASS 14: check_bridge rejected all {len(bad_siblings)} invalid sibling variants")

    # 15. real systems/m0/skills/m0 + fixtures a..k + runtime-assembled m0_server pass
    assert summarize_mod.check_bridge(REAL_M0_SKILL) == [], summarize_mod.check_bridge(REAL_M0_SKILL)
    assert summarize_mod.check_bridge(FIXTURES / "waiver_a") == []
    with tempfile.TemporaryDirectory() as td:
        srv = pathlib.Path(td) / "m0_server_skill"
        shutil.copytree(FIXTURES / "waiver_a", srv)
        src_srv = REAL_M0_SKILL / "scripts" / "m0_server.py"
        dst_srv = srv / "scripts" / "m0_server.py"
        shutil.copyfile(src_srv, dst_srv)
        assert src_srv.read_bytes() == dst_srv.read_bytes()
        assert summarize_mod.check_bridge(srv) == []
    for name in ("waiver_b", "waiver_c", "waiver_d", "waiver_e", "waiver_f", "waiver_h", "waiver_i", "waiver_j", "waiver_k"):
        errs = summarize_mod.check_bridge(FIXTURES / name)
        assert errs, f"fixture {name} unexpectedly passed check_bridge"
    print("PASS 15: real m0 skill, waiver_a, runtime m0_server pass; invalid fixtures fail")

    print("check-skill-scan-summarize: all 15 cases passed")


if __name__ == "__main__":
    main()
