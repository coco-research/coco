#!/usr/bin/env python3
"""
Build superintelligence/product-design/registry.json from persona frontmatter.
Re-run after editing any Product & Design persona file. Idempotent.

Usage:
    python3 superintelligence/product-design/scripts/build_registry.py
"""
from __future__ import annotations

import json
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not available. Install with: pip install pyyaml")

PD_DIR = Path(__file__).resolve().parents[1]            # -> superintelligence/product-design
PERSONAS_DIR = PD_DIR / "personas"
REGISTRY_PATH = PD_DIR / "registry.json"

KNOWN_CELLS_PD_SI = OrderedDict([
    ("product-strategy", "Product Strategy — product vision, strategy, positioning, business model."),
    ("product-discovery-research", "Product Discovery and Research — continuous discovery, JTBD, user research, lean."),
    ("growth-metrics", "Growth and Metrics — growth loops, metrics, experimentation, PLG, analytics."),
    ("design-foundations-usability", "Design Foundations and Usability — HCI, usability, interaction design, accessibility."),
    ("design-leadership-craft", "Design Leadership and Craft — design leadership, visual/industrial craft, culture."),
    ("ux-content-research", "UX, Content, and Research — content strategy, content design, information architecture."),
    ("design-systems-interaction", "Design Systems and Interaction — design systems, component architecture, patterns."),
    ("sprints-behavior-bridge", "Sprints, Behavior, and Bridge — product×design: sprints, behavioral design, ethics."),
])

KNOWN_TEAMS = OrderedDict([
    ("ai-super-intelligence", "AI Super Intelligence Team."),
    ("engineering-super-intelligence", "Engineering Super Intelligence Team."),
    ("product-design-super-intelligence", "Product & Design Super Intelligence Team."),
    ("finance-super-intelligence", "Finance Super Intelligence Team (future)."),
    ("compliance-super-intelligence", "Compliance Super Intelligence Team (future)."),
])

# Personas whose home team is elsewhere but who are cross-listed into Product & Design.
CROSS_LISTED = [
    {"slug": "adam-wathan", "home_team": "engineering-super-intelligence",
     "file_path": "superintelligence/engineering/personas/adam-wathan.md",
     "cell": "design-systems-interaction"},
]


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name}: no leading frontmatter delimiter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path.name}: no closing frontmatter delimiter")
    return yaml.safe_load(text[4:end])


def length_of(field):
    return len(field) if isinstance(field, list) else 0


def build_persona_index(persona_files):
    personas = OrderedDict()
    cells = {c: [] for c in KNOWN_CELLS_PD_SI}
    for path in sorted(persona_files):
        try:
            fm = parse_frontmatter(path)
        except Exception as exc:
            print(f"WARN: skipping {path.name}: {exc}", file=sys.stderr)
            continue
        slug = fm["slug"]
        cell = fm.get("cell")
        if cell not in cells:
            print(f"WARN: {slug} has unknown cell '{cell}'", file=sys.stderr)
        else:
            cells[cell].append(slug)
        personas[slug] = {
            "slug": slug,
            "real_name": fm.get("real_name", ""),
            "archetype": fm.get("archetype", ""),
            "teams": fm.get("teams", []),
            "home_team": fm.get("home_team", "product-design-super-intelligence"),
            "cell": cell,
            "cell_role": fm.get("cell_role"),
            "status": fm.get("status"),
            "affiliations_2026": fm.get("affiliations_2026", []),
            "domains": fm.get("domains", []),
            "pairs_well_with": fm.get("pairs_well_with", []),
            "productive_conflict_with": fm.get("productive_conflict_with", []),
            "sources_count": length_of(fm.get("sources")),
            "recent_signal_12mo_count": length_of(fm.get("recent_signal_12mo")),
            "persistent_signals_count": length_of(fm.get("persistent_signals")),
            "public_stances_count": length_of(fm.get("public_stances")),
            "confidence": fm.get("confidence"),
            "last_verified": str(fm.get("last_verified", "")),
            "voice_style_excerpt": (fm.get("voice_style", "") or "").strip().splitlines()[0][:160]
            if fm.get("voice_style") else "",
            "file_path": f"superintelligence/product-design/personas/{path.name}",
            "research_dir": f"superintelligence/product-design/research/{slug}/",
        }
    return personas, cells


def build_cells_section(cells):
    out = OrderedDict()
    for cell_id, slugs in cells.items():
        # append cross-listed personas that belong to this cell
        xl = [x["slug"] for x in CROSS_LISTED if x["cell"] == cell_id]
        out[cell_id] = {
            "id": cell_id,
            "description": KNOWN_CELLS_PD_SI[cell_id],
            "personas_count": len(slugs),
            "personas": slugs,
            "cross_listed": xl,
            "file_path": f"superintelligence/product-design/cells/{cell_id}.md",
        }
    return out


def main() -> None:
    if not PERSONAS_DIR.exists():
        sys.exit(f"Personas directory missing: {PERSONAS_DIR}")
    persona_files = list(PERSONAS_DIR.glob("*.md"))
    if not persona_files:
        sys.exit("No persona files found.")

    personas, cells_to_slugs = build_persona_index(persona_files)

    registry = OrderedDict([
        ("schema_version", "1.0"),
        ("generated_at", date.today().isoformat()),
        ("team_id", "product-design-super-intelligence"),
        ("team_name", "Product & Design Super Intelligence Team"),
        (
            "description",
            "Rijul's product + design brain trust and decision partner. Named personas across 8 "
            "cells spanning product strategy, discovery/research, growth/metrics, design "
            "foundations/usability, design leadership/craft, UX/content, design systems, and a "
            "product×design bridge. One merged team that convenes both lenses; pure-discipline "
            "input via /SI-PD-Huddle or --cells. Invoked by /SI-PD slash commands.",
        ),
        ("personas_count", len(personas)),
        ("cells_count", len(cells_to_slugs)),
        ("cells", build_cells_section(cells_to_slugs)),
        ("personas", personas),
        ("cross_listed", CROSS_LISTED),
        ("known_teams", KNOWN_TEAMS),
    ])

    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {REGISTRY_PATH} ({len(personas)} personas, {len(cells_to_slugs)} cells).")
    for cell_id, slugs in cells_to_slugs.items():
        if not slugs:
            print(f"WARN: cell {cell_id} is empty", file=sys.stderr)


if __name__ == "__main__":
    main()
