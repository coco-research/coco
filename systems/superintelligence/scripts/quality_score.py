#!/usr/bin/env python3
"""
Tier 1 automated structural quality scorer for SI personas.
Scores each persona 0-100 based on schema compliance, recency, and citation integrity.
No external API calls — pure local validation.

Usage:
    python3 quality_score.py --team ai
    python3 quality_score.py --all
    python3 quality_score.py --team finance --slug cathie-wood
"""
from __future__ import annotations
import argparse, json, os, pathlib, re, sys
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

SI_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEAMS = ["ai", "engineering", "product-design", "finance", "trading",
         "risk-compliance", "strategy", "data-analytics", "gtm",
         "legal-ip", "healthcare-life-sciences", "education-edtech", "climate-energy"]

REQUIRED_FIELDS = [
    "slug", "real_name", "archetype", "teams", "cell", "cell_role",
    "status", "domains", "signature_moves", "public_stances",
    "voice_style", "confidence", "sources"
]

CUTOFF = datetime(2025, 9, 4, tzinfo=timezone.utc)  # 12 months before Sep 2026


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


def score_persona(fm: dict) -> dict:
    """Score a single persona's frontmatter. Returns {score, checks, warnings}."""
    checks = {}
    warnings = []
    total_weight = 0
    earned = 0

    # 1. Required fields present (weight: 15)
    w = 15
    total_weight += w
    missing = [k for k in REQUIRED_FIELDS if not fm.get(k)]
    if not missing:
        earned += w
        checks["required_fields"] = {"pass": True, "score": w, "weight": w}
    else:
        partial = w * max(0, (len(REQUIRED_FIELDS) - len(missing))) / len(REQUIRED_FIELDS)
        earned += partial
        checks["required_fields"] = {"pass": False, "score": round(partial, 1), "weight": w, "missing": missing}

    # 2. Valid team_ids (weight: 10)
    w = 10
    total_weight += w
    teams = fm.get("teams", [])
    valid_teams = {f"{t}-super-intelligence" for t in TEAMS}
    if isinstance(teams, list) and all(t in valid_teams for t in teams):
        earned += w
        checks["valid_teams"] = {"pass": True, "score": w, "weight": w}
    else:
        bad = [t for t in (teams or []) if t not in valid_teams]
        checks["valid_teams"] = {"pass": False, "score": 0, "weight": w, "invalid": bad}

    # 3. affiliations_2026 non-empty (weight: 10)
    w = 10
    total_weight += w
    affils = fm.get("affiliations_2026", [])
    if affils and len(affils) > 0:
        earned += w
        checks["affiliations"] = {"pass": True, "score": w, "weight": w, "count": len(affils)}
    else:
        checks["affiliations"] = {"pass": False, "score": 0, "weight": w}

    # 4. recent_signal_12mo >= 3 if active (weight: 15)
    w = 15
    total_weight += w
    status = fm.get("status", "unknown")
    recent = fm.get("recent_signal_12mo") or []
    persistent = fm.get("persistent_signals") or []
    if status == "archetype":
        if len(persistent) >= 3:
            earned += w
            checks["signals"] = {"pass": True, "score": w, "weight": w, "type": "persistent", "count": len(persistent)}
        else:
            partial = w * min(len(persistent), 3) / 3
            earned += partial
            checks["signals"] = {"pass": False, "score": round(partial, 1), "weight": w, "type": "persistent", "count": len(persistent)}
    else:
        current_signals = []
        for sig in recent:
            d = parse_date(sig.get("date") if isinstance(sig, dict) else None)
            if d and d >= CUTOFF:
                current_signals.append(d)
        if len(current_signals) >= 3:
            earned += w
            checks["signals"] = {"pass": True, "score": w, "weight": w, "type": "recent", "count": len(current_signals)}
        elif len(recent) >= 3:
            # Has signals but they're stale
            partial = w * 0.5
            earned += partial
            warnings.append(f"has {len(recent)} signals but {len(recent)-len(current_signals)} are stale")
            checks["signals"] = {"pass": False, "score": round(partial, 1), "weight": w, "type": "recent_stale", "count": len(current_signals), "total": len(recent)}
        else:
            checks["signals"] = {"pass": False, "score": 0, "weight": w, "type": "recent", "count": len(recent)}

    # 5. canonical_works >= 5 (weight: 10)
    w = 10
    total_weight += w
    works = fm.get("canonical_works") or []
    if len(works) >= 5:
        earned += w
        checks["canonical_works"] = {"pass": True, "score": w, "weight": w, "count": len(works)}
    else:
        partial = w * min(len(works), 5) / 5
        earned += partial
        checks["canonical_works"] = {"pass": False, "score": round(partial, 1), "weight": w, "count": len(works)}

    # 6. signature_moves >= 5 (weight: 10)
    w = 10
    total_weight += w
    moves = fm.get("signature_moves") or []
    if len(moves) >= 5:
        earned += w
        checks["signature_moves"] = {"pass": True, "score": w, "weight": w, "count": len(moves)}
    else:
        partial = w * min(len(moves), 5) / 5
        earned += partial
        checks["signature_moves"] = {"pass": False, "score": round(partial, 1), "weight": w, "count": len(moves)}

    # 7. public_stances all have evidence_url (weight: 15)
    w = 15
    total_weight += w
    stances = fm.get("public_stances") or []
    if not stances:
        checks["stances_cited"] = {"pass": False, "score": 0, "weight": w, "note": "no stances"}
    else:
        cited = sum(1 for s in stances if isinstance(s, dict) and s.get("evidence_url"))
        uncited = len(stances) - cited
        if uncited == 0:
            earned += w
            checks["stances_cited"] = {"pass": True, "score": w, "weight": w, "cited": cited, "total": len(stances)}
        else:
            partial = w * cited / len(stances)
            earned += partial
            checks["stances_cited"] = {"pass": False, "score": round(partial, 1), "weight": w, "cited": cited, "uncited": uncited, "total": len(stances)}

    # 8. sources >= 4 with valid URLs (weight: 15)
    w = 15
    total_weight += w
    sources = fm.get("sources") or []
    url_sources = [s for s in sources if isinstance(s, str) and s.startswith("http")]
    if len(url_sources) >= 4:
        earned += w
        checks["sources"] = {"pass": True, "score": w, "weight": w, "count": len(url_sources)}
    else:
        partial = w * min(len(url_sources), 4) / 4
        earned += partial
        checks["sources"] = {"pass": False, "score": round(partial, 1), "weight": w, "count": len(url_sources)}

    final_score = round(earned, 1)
    return {"score": final_score, "max": total_weight, "checks": checks, "warnings": warnings}


def score_team(team: str, slug_filter: str | None = None) -> list[dict]:
    personas_dir = SI_ROOT / team / "personas"
    if not personas_dir.is_dir():
        return []
    results = []
    files = sorted(personas_dir.glob("*.md"))
    for f in files:
        slug = f.stem
        if slug_filter and slug != slug_filter:
            continue
        text = f.read_text()
        if not text.startswith("---"):
            results.append({"slug": slug, "score": 0, "error": "no frontmatter"})
            continue
        end = text.find("\n---\n", 4)
        if end < 0:
            end = text.find("\n---", 4)
        try:
            fm = yaml.safe_load(text[4:end]) if end > 0 else None
            if not isinstance(fm, dict):
                results.append({"slug": slug, "score": 0, "error": "frontmatter not a mapping"})
                continue
        except Exception as e:
            results.append({"slug": slug, "score": 0, "error": f"YAML parse: {e}"})
            continue
        result = score_persona(fm)
        result["slug"] = slug
        result["team"] = team
        results.append(result)
    return results


def main():
    ap = argparse.ArgumentParser(description="Tier 1 structural quality scorer for SI personas")
    ap.add_argument("--team", help="Team to score (or --all)")
    ap.add_argument("--all", action="store_true", help="Score all teams")
    ap.add_argument("--slug", help="Score only this slug within the team")
    ap.add_argument("--json", action="store_true", help="Output JSON instead of table")
    ap.add_argument("--threshold", type=int, default=70, help="Pass threshold (default: 70)")
    args = ap.parse_args()

    teams = TEAMS if args.all else ([args.team] if args.team else [])
    if not teams:
        ap.error("Specify --team <name> or --all")

    all_results = []
    for team in teams:
        all_results.extend(score_team(team, args.slug))

    if args.json:
        print(json.dumps(all_results, indent=2, default=str))
        return

    # Table output
    pass_count = sum(1 for r in all_results if r.get("score", 0) >= args.threshold)
    fail_count = len(all_results) - pass_count
    avg_score = sum(r.get("score", 0) for r in all_results) / len(all_results) if all_results else 0

    print(f"Quality Score Report | Teams: {', '.join(teams)} | Threshold: {args.threshold}")
    print(f"Total: {len(all_results)} | Pass: {pass_count} | Fail: {fail_count} | Avg: {avg_score:.1f}")
    print()
    print(f"{'Slug':<30} {'Score':>6} {'Status':>8}  Issues")
    print("-" * 90)
    for r in sorted(all_results, key=lambda x: x.get("score", 0)):
        slug = r.get("slug", "?")
        score = r.get("score", 0)
        status = "PASS" if score >= args.threshold else "FAIL"
        issues = []
        if "error" in r:
            issues.append(r["error"])
        else:
            for check_name, check in r.get("checks", {}).items():
                if not check.get("pass", True):
                    detail = check.get("missing") or check.get("invalid") or check.get("uncited") or check.get("count", "?")
                    issues.append(f"{check_name}:{detail}")
            issues.extend(r.get("warnings", []))
        print(f"{slug:<30} {score:>6.1f} {status:>8}  {'; '.join(issues[:3])}")

    # Write dashboard file
    dashboard_path = SI_ROOT / "QUALITY-DASHBOARD.md"
    lines = [f"# Quality Dashboard\n\nGenerated: {datetime.now(timezone.utc).isoformat()}\n"]
    lines.append(f"| Team | Personas | Avg Score | Pass | Fail |")
    lines.append("|------|----------|-----------|------|------|")
    for team in teams:
        team_results = [r for r in all_results if r.get("team") == team]
        if not team_results:
            continue
        t_avg = sum(r.get("score", 0) for r in team_results) / len(team_results)
        t_pass = sum(1 for r in team_results if r.get("score", 0) >= args.threshold)
        t_fail = len(team_results) - t_pass
        lines.append(f"| {team} | {len(team_results)} | {t_avg:.1f} | {t_pass} | {t_fail} |")
    lines.append("")
    dashboard_path.write_text("\n".join(lines))
    print(f"\nDashboard written to {dashboard_path}")


if __name__ == "__main__":
    main()
