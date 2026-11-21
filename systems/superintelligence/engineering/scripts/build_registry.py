#!/usr/bin/env python3
# ponytail: 13 near-copies of this generator; upgrade path is one shared generator taking the team as an argument.
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
ENG_DIR = Path(__file__).resolve().parents[1] # -> superintelligence/engineering
PERSONAS_DIR = ENG_DIR / "personas"
REGISTRY_PATH = ENG_DIR / "registry.json"

KNOWN_CELLS_ENG_SI = OrderedDict([
    ("cloud-architecture", "Distributed systems, monolith versus services, queues, retries, backpressure, and cloud infrastructure."),
    ("reliability-sre-obs", "Site reliability engineering, SLOs, distributed request tracing, observability stacks, chaos testing, and incident response."),
    ("data-and-storage", "Database internals, zero-downtime schema migrations, query latency, transactions, distributed locks, and network partitions."),
    ("security", "Application security, cryptography, authentication, vulnerability research, and threat modeling."),
    ("finops-cost", "Cloud cost engineering, compute utilization, infrastructure spend, and FinOps."),
    ("languages-runtimes", "Programming languages, type systems, compiler optimizations, numerical semantics, and runtime internals."),
    ("systems-programming", "Operating systems, server concurrency, async I/O, worker processes, memory leaks, profiling, and low-level performance."),
    ("web-and-frontend", "Frontend engineering, browser rendering, CSS frameworks, web standards, and build tooling."),
    ("architecture-testing-craft", "Software modularity, API boundaries, distributed fault testing, refactoring, and engineering craft."),
    ("devops-platform", "CI/CD pipelines, containers, Kubernetes, progressive delivery, deployment rollbacks, and developer platforms."),
    ("ai-assisted-coding", "Code editors, automated refactoring, and developer productivity tooling."),
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


def write_registry(registry: OrderedDict) -> None:
    """Write registry.json; generated_at keeps its committed date unless something else changed."""
    old = REGISTRY_PATH.read_text(encoding="utf-8") if REGISTRY_PATH.exists() else ""
    stamps = [date.today().isoformat()]
    try:
        stamps.insert(0, json.loads(old)["generated_at"])
    except (ValueError, KeyError, TypeError):
        pass
    for stamp in stamps:
        registry["generated_at"] = stamp
        text = json.dumps(registry, indent=2, ensure_ascii=False) + "\n"
        if text == old:
            break
    REGISTRY_PATH.write_text(text, encoding="utf-8")


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
            "Software engineering, backend systems architecture, monolith versus microservices, "
            "zero-downtime schema evolution and database migrations, distributed locks and "
            "network partitions, concurrency models, queues and retries, backend latency, memory "
            "leaks in daemon workers, compiler optimizations, distributed request tracing, "
            "container rollbacks, cloud security, and systems craft.",
        ),
        ("personas_count", len(personas)),
        ("cells_count", len(cells_to_slugs)),
        ("cells", build_cells_section(cells_to_slugs)),
        ("personas", personas),
        ("cross_listed_from_ai", CROSS_LISTED_FROM_AI),
        ("known_teams", KNOWN_TEAMS),
    ])

    write_registry(registry)
    print(f"Wrote {REGISTRY_PATH} ({len(personas)} personas, {len(cells_to_slugs)} cells).")

    for cell_id, slugs in cells_to_slugs.items():
        if not slugs:
            print(f"WARN: cell {cell_id} is empty", file=sys.stderr)


if __name__ == "__main__":
    main()
