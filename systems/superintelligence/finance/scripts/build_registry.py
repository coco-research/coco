#!/usr/bin/env python3
"""
Build superintelligence/finance/registry.json from persona frontmatter.
Re-run after editing any Finance persona file. Idempotent.

    python3 superintelligence/finance/scripts/build_registry.py
"""
from __future__ import annotations
import json, sys
from collections import OrderedDict
from datetime import date
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.exit("PyYAML not available. Install with: pip install pyyaml")

FIN_DIR = Path(__file__).resolve().parents[1]
PERSONAS_DIR = FIN_DIR / "personas"
REGISTRY_PATH = FIN_DIR / "registry.json"

KNOWN_CELLS = OrderedDict([
    ("valuation-corporate-finance", "Valuation, corporate finance, intrinsic value, capital structure."),
    ("investing-capital-allocation", "Value / discretionary investing and capital allocation."),
    ("accounting-fpa-reporting", "Forensic accounting, financial reporting, and FP&A practice."),
    ("macro-economics", "Macro economists and policy / markets framing."),
    ("fintech-payments", "Fintech, payments, banking-as-a-service, fintech investing."),
    ("behavioral-decision-science", "Behavioral finance and decision-making under uncertainty."),
    ("capital-markets-ma-private", "IPOs, M&A, private equity / VC finance, distress and restructuring."),
])

KNOWN_TEAMS = OrderedDict([
    ("ai-super-intelligence", "AI Super Intelligence Team."),
    ("engineering-super-intelligence", "Engineering Super Intelligence Team."),
    ("product-design-super-intelligence", "Product & Design Super Intelligence Team."),
    ("finance-super-intelligence", "Finance Super Intelligence Team."),
    ("trading-super-intelligence", "Trading Super Intelligence Team (future)."),
    ("compliance-super-intelligence", "Compliance Super Intelligence Team (future)."),
])


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name}: no leading frontmatter delimiter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path.name}: no closing frontmatter delimiter")
    return yaml.safe_load(text[4:end])


def length_of(f):
    return len(f) if isinstance(f, list) else 0


def main() -> None:
    if not PERSONAS_DIR.exists():
        sys.exit(f"Personas directory missing: {PERSONAS_DIR}")
    files = list(PERSONAS_DIR.glob("*.md"))
    if not files:
        sys.exit("No persona files found.")
    personas = OrderedDict()
    cells = {c: [] for c in KNOWN_CELLS}
    for path in sorted(files):
        try:
            fm = parse_frontmatter(path)
        except Exception as exc:
            print(f"WARN: skipping {path.name}: {exc}", file=sys.stderr)
            continue
        slug = fm["slug"]; cell = fm.get("cell")
        if cell in cells:
            cells[cell].append(slug)
        else:
            print(f"WARN: {slug} unknown cell '{cell}'", file=sys.stderr)
        personas[slug] = {
            "slug": slug, "real_name": fm.get("real_name", ""), "archetype": fm.get("archetype", ""),
            "teams": fm.get("teams", []), "home_team": fm.get("home_team", "finance-super-intelligence"),
            "cell": cell, "cell_role": fm.get("cell_role"), "status": fm.get("status"),
            "affiliations_2026": fm.get("affiliations_2026", []), "domains": fm.get("domains", []),
            "pairs_well_with": fm.get("pairs_well_with", []),
            "productive_conflict_with": fm.get("productive_conflict_with", []),
            "sources_count": length_of(fm.get("sources")),
            "recent_signal_12mo_count": length_of(fm.get("recent_signal_12mo")),
            "persistent_signals_count": length_of(fm.get("persistent_signals")),
            "public_stances_count": length_of(fm.get("public_stances")),
            "confidence": fm.get("confidence"), "last_verified": str(fm.get("last_verified", "")),
            "voice_style_excerpt": (fm.get("voice_style", "") or "").strip().splitlines()[0][:160]
            if fm.get("voice_style") else "",
            "file_path": f"superintelligence/finance/personas/{path.name}",
            "research_dir": f"superintelligence/finance/research/{slug}/",
            "build_method": "local-llm",
        }
    cells_section = OrderedDict()
    for cid, slugs in cells.items():
        cells_section[cid] = {"id": cid, "description": KNOWN_CELLS[cid],
                              "personas_count": len(slugs), "personas": slugs,
                              "file_path": f"superintelligence/finance/cells/{cid}.md"}
    registry = OrderedDict([
        ("schema_version", "1.0"), ("generated_at", date.today().isoformat()),
        ("team_id", "finance-super-intelligence"), ("team_name", "Finance Super Intelligence Team"),
        ("description", "Rijul's finance brain trust and decision partner. Named personas across 7 cells: "
                        "valuation/corporate finance, investing, accounting/FP&A, macro, fintech, behavioral, "
                        "and capital markets/M&A/private. Markets/quant/derivatives are reserved for the Trading "
                        "team. Built local-first (LM Studio) and validator-gated. Invoked by /SI-Fin commands."),
        ("personas_count", len(personas)), ("cells_count", len(cells)),
        ("cells", cells_section), ("personas", personas),
        ("known_teams", KNOWN_TEAMS),
    ])
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {REGISTRY_PATH} ({len(personas)} personas, {len(cells)} cells).")
    for cid, slugs in cells.items():
        if not slugs:
            print(f"WARN: cell {cid} empty", file=sys.stderr)


if __name__ == "__main__":
    main()
