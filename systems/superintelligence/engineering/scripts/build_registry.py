#!/usr/bin/env python3
"""
Build superintelligence/engineering/registry.json from persona file frontmatter.

Reads every superintelligence/engineering/personas/*.md, extracts the YAML
frontmatter, and emits the machine-readable registry consumed by the
/SI-Eng-* slash commands and the orchestrator.

Re-run after editing any Engineering persona file. Idempotent.

Usage:
    python3 superintelligence/engineering/scripts/build_registry.py
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

# Script lives at superintelligence/engineering/scripts/build_registry.py
ENG_DIR = Path(__file__).resolve().parents[1]          # -> superintelligence/engineering
PERSONAS_DIR = ENG_DIR / "personas"
REGISTRY_PATH = ENG_DIR / "registry.json"

KNOWN_CELLS_ENG_SI = OrderedDict([
    ("cloud-architecture", "Cloud Architecture — cloud-scale system design, infra primitives, build-vs-managed lens."),
    ("reliability-sre-obs", "Reliability, SRE, and Observability — SRE practice, incident response, resilience."),
    ("data-and-storage", "Data and Storage — databases, distributed data, consistency, distributed-systems theory."),
    ("security", "Security — security architecture, cryptography, vuln research, disclosure policy."),
    ("finops-cost", "FinOps and Cost — cloud cost engineering and FinOps practice."),
    ("languages-runtimes", "Languages and Runtimes — language design, type systems, compilers, runtimes."),
    ("systems-programming", "Systems Programming — low-level, OS, performance, systems craft."),
    ("web-and-frontend", "Web and Frontend — frontend frameworks, web platform, UI engineering."),
    ("architecture-testing-craft", "Architecture, Testing, and Craft — software architecture, DDD, testing discipline."),
    ("devops-platform", "DevOps and Platform Engineering — DevOps movement, internal developer platforms."),
    ("ai-assisted-coding", "AI-Assisted Coding — agentic dev tools, codegen, the AI-coding frontier."),
])

KNOWN_TEAMS = OrderedDict([
    ("ai-super-intelligence", "AI Super Intelligence Team — frontier AI research, models, alignment, and systems."),
    ("engineering-super-intelligence", "Engineering Super Intelligence Team — cloud, data, languages, systems, web, security, DevOps."),
    ("product-super-intelligence", "Product Super Intelligence Team — PM craft, product strategy (future)."),
    ("design-super-intelligence", "Design Super Intelligence Team — UX, design systems, visual design (future)."),
    ("finance-super-intelligence", "Finance Super Intelligence Team — FP&A, accounting, finance ops (future)."),
    ("compliance-super-intelligence", "Compliance Super Intelligence Team — governance, risk, regulatory (future)."),
])

# AI personas cross-listed into Engineering (home_team stays ai; no file here).
CROSS_LISTED_FROM_AI = [
    "andrej-karpathy", "sasha-rush", "tri-dao", "bryan-catanzaro", "andrew-feldman",
    "albert-gu", "horace-he", "woosuk-kwon", "tim-dettmers",
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
    if isinstance(field, list):
        return len(field)
    return 0


def build_persona_index(persona_files: list[Path]) -> tuple[dict, dict]:
    """Returns (personas_by_slug, cells_to_slugs)."""
    personas = OrderedDict()
    cells: dict[str, list[str]] = {c: [] for c in KNOWN_CELLS_ENG_SI}
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
            "home_team": fm.get("home_team", "engineering"),
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
            "file_path": f"superintelligence/engineering/personas/{path.name}",
            "research_dir": f"superintelligence/engineering/research/{slug}/",
        }
    return personas, cells


def build_cells_section(cells: dict[str, list[str]]) -> OrderedDict:
    out = OrderedDict()
    for cell_id, slugs in cells.items():
        out[cell_id] = {
            "id": cell_id,
            "description": KNOWN_CELLS_ENG_SI[cell_id],
            "personas_count": len(slugs),
            "personas": slugs,
            "file_path": f"superintelligence/engineering/cells/{cell_id}.md",
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
        ("team_id", "engineering-super-intelligence"),
        ("team_name", "Engineering Super Intelligence Team"),
        (
            "description",
            "Rijul's software-engineering brain trust. Named personas across 11 cells covering "
            "cloud architecture, reliability/SRE/observability, data and storage, security, "
            "FinOps, languages and runtimes, systems programming, web and frontend, "
            "architecture/testing/craft, DevOps/platform, and AI-assisted coding. Reusable as a "
            "decision-making partner — invoked by /SI-Eng slash commands.",
        ),
        ("personas_count", len(personas)),
        ("cells_count", len(cells_to_slugs)),
        ("cells", build_cells_section(cells_to_slugs)),
        ("personas", personas),
        ("cross_listed_from_ai", CROSS_LISTED_FROM_AI),
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
