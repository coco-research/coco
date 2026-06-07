#!/usr/bin/env python3
"""
Queue-3 mechanical activation (threshold-gated). For each freshly-built team:
  1. read <team>/VALIDATION.md -> PASS rate
  2. if rate >= THRESHOLD: flip superintelligence/registry.json built=true + counts,
     then regenerate that team's /SI-<Short>-* commands via build_commands.py --team <Short>
  3. else: HOLD (leave built=false, no commands) -> needs top-up first

Does NOT do: persona top-up (verify-gate, Claude-only), SKILL.md prose, git commit.
Writes superintelligence/ACTIVATION-REPORT.md.

    python3 superintelligence/scripts/activate_teams.py            # all 6
    THRESHOLD=0.6 python3 .../activate_teams.py                    # override gate
"""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]                 # superintelligence/
META = ROOT / "registry.json"
BUILD_CMDS = ROOT / "ai" / "scripts" / "build_commands.py"
THRESHOLD = float(os.environ.get("THRESHOLD", "0.70"))

# (meta-registry key / dir name, build_commands TEAMS short)
TEAMS = [
    ("finance", "Fin"),
    ("trading", "Trade"),
    ("risk-compliance", "GRC"),
    ("strategy", "Strat"),
    ("data-analytics", "Data"),
    ("gtm", "GTM"),
]


def pass_rate(team_dir: Path):
    vp = team_dir / "VALIDATION.md"
    if not vp.exists():
        return None
    m = re.search(r"(\d+)\s*/\s*(\d+)\s+PASS", vp.read_text())
    if not m:
        return None
    npass, total = int(m.group(1)), int(m.group(2))
    return npass, total, (npass / total if total else 0.0)


def main():
    meta = json.loads(META.read_text())
    report = ["# Super Intelligence — activation report (queue-3)",
              f"\nThreshold: PASS-rate >= {THRESHOLD:.0%}. ACTIVATED = registry built=true + /SI-* commands generated.\n",
              "| Team | PASS | rate | action |", "|---|---|---|---|"]
    activated, held = [], []
    for dirname, short in TEAMS:
        tdir = ROOT / dirname
        pr = pass_rate(tdir)
        if pr is None:
            report.append(f"| {dirname} | — | — | SKIP (no VALIDATION.md) |")
            held.append(dirname)
            continue
        npass, total, rate = pr
        if rate >= THRESHOLD:
            # flip meta-registry + counts from the team's own registry.json
            treg_path = tdir / "registry.json"
            if treg_path.exists():
                treg = json.loads(treg_path.read_text())
                if dirname in meta["teams"]:
                    meta["teams"][dirname]["built"] = True
                    meta["teams"][dirname]["personas"] = treg.get("native_personas_count",
                                                                  treg.get("personas_count", npass))
                    meta["teams"][dirname]["cells"] = treg.get("cells_count",
                                                               meta["teams"][dirname].get("cells", 0))
                    meta["teams"][dirname].pop("status", None)
            # regenerate commands
            r = subprocess.run([sys.executable, str(BUILD_CMDS), "--team", short],
                               capture_output=True, text=True)
            ok = r.returncode == 0
            report.append(f"| {dirname} | {npass}/{total} | {rate:.0%} | "
                          f"{'ACTIVATED' if ok else 'FLIP-OK / CMD-FAIL: ' + r.stderr.strip()[:60]} |")
            activated.append(dirname)
        else:
            report.append(f"| {dirname} | {npass}/{total} | {rate:.0%} | HELD (< threshold) — top-up first |")
            held.append(dirname)

    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    report += ["",
               f"**Activated ({len(activated)}):** {', '.join(activated) or 'none'}",
               f"**Held ({len(held)}):** {', '.join(held) or 'none'}",
               "",
               "## Still manual (NOT done here)",
               "- Persona top-up of every NEEDS-TOPUP (see each team's VALIDATION.md) — verify-gate, Claude-only.",
               "- SKILL.md prose per activated team.",
               "- git commit + push.",
               "- Re-run this script after top-up to activate any HELD teams."]
    (ROOT / "ACTIVATION-REPORT.md").write_text("\n".join(report) + "\n")
    print(f"activation done: {len(activated)} activated, {len(held)} held. "
          f"See {ROOT/'ACTIVATION-REPORT.md'}")


if __name__ == "__main__":
    main()
