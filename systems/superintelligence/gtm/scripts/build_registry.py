#!/usr/bin/env python3
"""
Team-generic registry builder. Drop into superintelligence/<team>/scripts/ and run.
Resolves the team from its own location (parents[1]), reads roster.json for the cell
list + team metadata, and builds <team>/registry.json from persona frontmatter.

Cross-listed personas (roster.json["cross_listed"]) are referenced by slug into their
cell with home_team + file_path pointing at the home team — no file is copied.

    python3 superintelligence/<team>/scripts/build_registry.py

Idempotent. Behavior for Finance is preserved because it reads the same cells/meta.
"""
from __future__ import annotations
import json, sys
from collections import OrderedDict
from datetime import date
from pathlib import Path
try:
    import yaml
except ImportError:
    sys.exit("PyYAML not available. Install with: pip install --break-system-packages pyyaml")

TEAM_DIR = Path(__file__).resolve().parents[1]      # superintelligence/<team>
TEAM = TEAM_DIR.name
PERSONAS_DIR = TEAM_DIR / "personas"
REGISTRY_PATH = TEAM_DIR / "registry.json"
ROSTER = json.loads((TEAM_DIR / "roster.json").read_text())

KNOWN_CELLS = OrderedDict(ROSTER["cells"])          # id -> description
TEAM_ID = ROSTER["team_id"]
TEAM_NAME = ROSTER["team_name"]
DESCRIPTION = ROSTER.get(
    "description",
    f"{TEAM_NAME}. Named real-world personas across {len(KNOWN_CELLS)} cells. "
    "Built local-first (LM Studio) and validator-gated. Illustrative composites; see DISCLAIMER.md.",
)

KNOWN_TEAMS = OrderedDict([
    ("ai-super-intelligence", "AI Super Intelligence Team."),
    ("engineering-super-intelligence", "Engineering Super Intelligence Team."),
    ("product-design-super-intelligence", "Product & Design Super Intelligence Team."),
    ("finance-super-intelligence", "Finance Super Intelligence Team."),
    ("trading-super-intelligence", "Trading Super Intelligence Team."),
    ("risk-compliance-super-intelligence", "Risk & Compliance (GRC) Super Intelligence Team."),
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
            "teams": fm.get("teams", []), "home_team": fm.get("home_team", TEAM_ID),
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
            "file_path": f"superintelligence/{TEAM}/personas/{path.name}",
            "research_dir": f"superintelligence/{TEAM}/research/{slug}/",
            "build_method": "local-llm",
        }

    # cross-listed personas: reference by slug into their cell, point file at home team
    HOME_DIR = {
        "ai-super-intelligence": "ai", "engineering-super-intelligence": "engineering",
        "product-design-super-intelligence": "product-design", "finance-super-intelligence": "finance",
        "trading-super-intelligence": "trading", "risk-compliance-super-intelligence": "risk-compliance",
    }
    cross = ROSTER.get("cross_listed", [])
    for x in cross:
        slug = x["slug"]; cell = x.get("cell"); home = x.get("home_team", "")
        hdir = HOME_DIR.get(home, home.replace("-super-intelligence", ""))
        if cell in cells and slug not in cells[cell]:
            cells[cell].append(slug)
        personas.setdefault(slug, {
            "slug": slug, "cell": cell, "home_team": home, "cross_listed": True,
            "file_path": f"superintelligence/{hdir}/personas/{slug}.md",
            "build_method": "cross-listed-reference",
        })

    cells_section = OrderedDict()
    for cid, slugs in cells.items():
        cells_section[cid] = {"id": cid, "description": KNOWN_CELLS[cid],
                              "personas_count": len(slugs), "personas": slugs,
                              "file_path": f"superintelligence/{TEAM}/cells/{cid}.md"}
    registry = OrderedDict([
        ("schema_version", "1.0"), ("generated_at", date.today().isoformat()),
        ("team_id", TEAM_ID), ("team_name", TEAM_NAME),
        ("description", DESCRIPTION),
        ("native_personas_count", len([p for p in personas.values() if not p.get("cross_listed")])),
        ("cross_listed_count", len(cross)),
        ("personas_count", len(personas)), ("cells_count", len(cells)),
        ("cells", cells_section), ("personas", personas),
        ("known_teams", KNOWN_TEAMS),
    ])
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {REGISTRY_PATH} ({len(personas)} personas [{registry['native_personas_count']} native + "
          f"{len(cross)} cross-listed], {len(cells)} cells).")
    for cid, slugs in cells.items():
        if not slugs:
            print(f"WARN: cell {cid} empty", file=sys.stderr)


if __name__ == "__main__":
    main()
