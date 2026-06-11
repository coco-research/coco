#!/usr/bin/env python3
"""
Generate a team's ROSTER.md from its registry.json — the per-cell roster tables
that /SI-<Team>-Recruit reads as the roster-gap document.

    python3 superintelligence/scripts/build_roster_md.py <team-dir> [<team-dir> ...]
    python3 superintelligence/scripts/build_roster_md.py --all

Idempotent: regenerates the whole file from the registry every run. Teams that
maintain a hand-curated ROSTER.md (engineering, product-design) are skipped by
--all and must be passed explicitly to overwrite.
"""
from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAND_CURATED = {"engineering", "product-design"}


def anchor_for(p: dict) -> str:
    affs = p.get("affiliations_2026") or []
    if affs:
        return str(affs[0])[:90]
    return (p.get("archetype") or "")[:90]


def build(team_dir: str) -> None:
    tdir = ROOT / team_dir
    reg = json.loads((tdir / "registry.json").read_text())
    personas = reg["personas"]
    native = [p for p in personas.values() if not p.get("cross_listed")]
    cross = [p for p in personas.values() if p.get("cross_listed")]
    lines = [
        f"# {reg['team_name']} — Roster",
        "",
        f"**Status:** generated from `registry.json` on {date.today().isoformat()} by `build_roster_md.py` — regenerate, do not hand-edit.",
        f"**Team ID:** `{reg['team_id']}`",
        f"**Native personas:** {len(native)} across {reg.get('cells_count', len(reg.get('cells', {})))} cells."
        + (f" **Cross-listed:** {len(cross)} (no new research)." if cross else ""),
        "**Quality bar:** ≥8 source URLs, ≥3 recent signals, every `public_stance` carries an `evidence_url`. Full English prose.",
        "",
        "---",
        "",
        "## Cells and personas",
        "",
    ]
    for i, (cid, cell) in enumerate(reg.get("cells", {}).items(), 1):
        lines.append(f"### {i}. {cid} ({cell.get('personas_count', len(cell.get('personas', [])))})")
        lines.append(cell.get("description", ""))
        lines.append("")
        lines.append("| Slug | Name | Anchor |")
        lines.append("|---|---|---|")
        for slug in cell.get("personas", []):
            p = personas.get(slug, {})
            name = p.get("real_name") or slug.replace("-", " ").title()
            note = " — *cross-listed*" if p.get("cross_listed") else ""
            lines.append(f"| `{slug}` | {name} | {anchor_for(p)}{note} |")
        lines.append("")
    out = tdir / "ROSTER.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(native)} native + {len(cross)} cross-listed)")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args == ["--all"]:
        args = sorted(
            d.name for d in ROOT.iterdir()
            if (d / "registry.json").exists() and d.name not in HAND_CURATED
        )
    for team in args:
        build(team)


if __name__ == "__main__":
    main()
