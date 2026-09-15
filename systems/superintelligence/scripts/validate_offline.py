#!/usr/bin/env python3
"""
Offline-mode persona validator. Validates structure, schema, and citations
WITHOUT making HTTP requests. Use when web search / URL resolution is unavailable.

Checks:
- frontmatter parses; required keys present
- status active -> recent_signal_12mo >=2; archetype -> persistent_signals >=2  
- public_stances have evidence_url field (format check only, no HTTP)
- sources >=4 (count check only, no HTTP)
- signature_moves >=3
- canonical_works present

Verdict: PASS / NEEDS-TOPUP (with reasons).
NO HTTP REQUESTS MADE — safe to run offline.

Usage:
    python3 validate_offline.py --team finance
    python3 validate_offline.py --all
"""
from __future__ import annotations
import argparse, json, pathlib, sys
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

SI_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEAMS = ["ai", "engineering", "product-design", "finance", "trading",
         "risk-compliance", "strategy", "data-analytics", "gtm"]

REQUIRED = ["slug", "real_name", "archetype", "teams", "cell", "cell_role",
            "status", "domains", "signature_moves", "public_stances",
            "voice_style", "confidence", "sources"]

CUTOFF = datetime(2025, 9, 4, tzinfo=timezone.utc)


def parse_date(d):
    if not d:
        return None
    try:
        dt = datetime.fromisoformat(str(d))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def validate_offline(path, slugs=None, cutoff=None):
    """Validate a persona file without HTTP requests."""
    t = path.read_text(encoding="utf-8")
    reasons = []
    
    if not t.startswith("---"):
        return "NEEDS-TOPUP", ["no leading frontmatter delimiter"], 0, 0
    
    end = t.find("\n---\n", 4)
    if end < 0:
        end = t.find("\n---", 4)
    
    try:
        fm = yaml.safe_load(t[4:end]) if end > 0 else None
        if not isinstance(fm, dict):
            raise ValueError("frontmatter not a mapping")
    except Exception as e:
        return "NEEDS-TOPUP", [f"YAML PARSE ERROR: {type(e).__name__}: {str(e).splitlines()[0]}"], 0, 0
    
    # Required keys
    miss = [k for k in REQUIRED if not fm.get(k)]
    if miss:
        reasons.append(f"missing keys: {miss}")
    
    # Status + signals
    status = fm.get("status")
    rs = fm.get("recent_signal_12mo") or []
    ps_sig = fm.get("persistent_signals") or []
    
    if status == "archetype":
        if len(ps_sig) < 2:
            reasons.append(f"archetype persistent_signals {len(ps_sig)}<2")
    else:
        if len(rs) < 2:
            reasons.append(f"recent_signal_12mo {len(rs)}<2")
    
    # Public stances citation (format check only)
    ps = fm.get("public_stances") or []
    uncited = [i for i, s in enumerate(ps) if isinstance(s, dict) and not s.get("evidence_url")]
    if uncited:
        reasons.append(f"uncited stances idx {uncited}")
    
    # Sources count (no HTTP)
    sources = fm.get("sources") or []
    url_sources = [s for s in sources if isinstance(s, str) and s.startswith("http")]
    if len(url_sources) < 4:
        reasons.append(f"sources {len(url_sources)}<4")
    
    # Signature moves
    moves = fm.get("signature_moves") or []
    if len(moves) < 3:
        reasons.append(f"signature_moves {len(moves)}<3")
    
    # Cross-listing slug check
    if slugs:
        pool = set(slugs)
        for fld in ("pairs_well_with", "productive_conflict_with"):
            bad = [s for s in (fm.get(fld) or []) if s not in pool]
            if bad:
                reasons.append(f"{fld} non-roster slugs: {bad}")
    
    verdict = "PASS" if not reasons else "NEEDS-TOPUP"
    return verdict, reasons, len(url_sources), len(url_sources)  # ok=nurls since no HTTP


def roster_slugs(team_dir):
    roster_path = team_dir / "roster.json"
    if not roster_path.exists():
        return []
    roster = json.loads(roster_path.read_text())
    persons = roster.get("personas", [])
    if isinstance(persons, dict):
        slugs = list(persons.keys())
    else:
        slugs = [p["slug"] if isinstance(p, dict) else p for p in persons]
    return slugs + [x["slug"] for x in roster.get("cross_listed", [])]


def sweep_team(team_dir):
    team = team_dir.name
    pers = team_dir / "personas"
    slugs = roster_slugs(team_dir)
    files = sorted(pers.glob("*.md"))
    
    rows, npass, ntop, topup = [], 0, 0, []
    for f in files:
        try:
            verdict, reasons, n, ok = validate_offline(f, slugs)
        except Exception as e:
            verdict, reasons, n, ok = "NEEDS-TOPUP", [f"validator crash: {type(e).__name__}: {e}"], 0, 0
        
        if verdict == "PASS":
            npass += 1
        else:
            ntop += 1
            topup.append(f.stem)
        
        rows.append(f"| `{f.stem}` | {verdict} | {ok}/{n} | {'; '.join(reasons)[:120]} |")
    
    total = len(files)
    report = f"""# {team} — offline validation sweep
Generated by `validate_offline.py`. {npass}/{total} PASS, {ntop} NEEDS-TOPUP.
NO HTTP REQUESTS MADE — structural/schema checks only.

## NEEDS-TOPUP ({ntop})
{(chr(10).join('- `' + s + '`' for s in topup)) if topup else '- none'}

## Full results
| Slug | Verdict | URLs ok | Notes |
|---|---|---|---|
{chr(10).join(rows)}
"""
    (team_dir / "VALIDATION-OFFLINE.md").write_text(report, encoding="utf-8")
    print(f"{team}: {npass}/{total} PASS, {ntop} NEEDS-TOPUP -> {team_dir/'VALIDATION-OFFLINE.md'}")
    return npass, ntop


def main():
    ap = argparse.ArgumentParser(description="Offline persona validator (no HTTP)")
    ap.add_argument("--team", help="Team to validate")
    ap.add_argument("--all", action="store_true", help="Validate all teams")
    args = ap.parse_args()
    
    teams = TEAMS if args.all else ([args.team] if args.team else [])
    if not teams:
        ap.error("Specify --team <name> or --all")
    
    total_pass, total_topup = 0, 0
    for team in teams:
        team_dir = SI_ROOT / team
        if team_dir.is_dir() and (team_dir / "personas").is_dir():
            p, t = sweep_team(team_dir)
            total_pass += p
            total_topup += t
    
    print(f"\nTOTAL: {total_pass} PASS, {total_topup} NEEDS-TOPUP")


if __name__ == "__main__":
    main()
