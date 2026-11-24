#!/usr/bin/env python3
# ponytail: 13 near-copies of this generator; upgrade path is one shared generator taking the team as an argument.
"""
Build <team>/registry.json from the persona frontmatter and <team>/roster.json.

roster.json is the source for the team id, name, description and the cells (id -> description);
personas/*.md is the source for everything per persona. Re-run after editing either. Idempotent:
generated_at keeps its date until something else in the file changes.

    python3 superintelligence/<team>/scripts/build_registry.py
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

TEAM_DIR = Path(__file__).resolve().parents[1]  # superintelligence/<team>
TEAM = TEAM_DIR.name
PERSONAS_DIR = TEAM_DIR / "personas"
REGISTRY_PATH = TEAM_DIR / "registry.json"
ROSTER = json.loads((TEAM_DIR / "roster.json").read_text(encoding="utf-8"))
KNOWN_CELLS = OrderedDict(ROSTER["cells"])  # id -> description


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name}: no leading frontmatter delimiter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path.name}: no closing frontmatter delimiter")
    return yaml.safe_load(text[4:end])


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
        text = json.dumps(registry, indent=2)
        if text == old:
            break
    REGISTRY_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    if not PERSONAS_DIR.exists():
        sys.exit(f"Personas directory missing: {PERSONAS_DIR}")
    files = sorted(PERSONAS_DIR.glob("*.md"))
    if not files:
        sys.exit("No persona files found.")
    personas = OrderedDict()
    cells = {c: [] for c in KNOWN_CELLS}
    for path in files:
        try:
            fm = parse_frontmatter(path)
        except Exception as exc:
            print(f"WARN: skipping {path.name}: {exc}", file=sys.stderr)
            continue
        if fm.get("status") == "held":  # held out until it can be sourced: not in the registry, so not in ROSTER/SKILL/cells
            continue
        slug, cell = fm["slug"], fm.get("cell")
        if cell in cells:
            cells[cell].append(slug)
        else:
            print(f"WARN: {slug} unknown cell '{cell}'", file=sys.stderr)
        personas[slug] = {"slug": slug, "real_name": fm.get("real_name", ""), "cell": cell,
                          "file_path": f"superintelligence/{TEAM}/personas/{path.name}"}
    registry = OrderedDict([
        ("schema_version", "1.0"), ("generated_at", None),
        ("team_id", ROSTER["team_id"]), ("team_name", ROSTER["team_name"]),
        ("description", ROSTER["description"]),
        ("personas_count", len(personas)), ("cells_count", len(cells)),
        ("cells", {cid: {"id": cid, "description": KNOWN_CELLS[cid], "personas_count": len(slugs),
                         "personas": slugs, "file_path": f"superintelligence/{TEAM}/cells/{cid}.md"}
                   for cid, slugs in cells.items()}),
        ("personas", personas),
    ])
    write_registry(registry)
    print(f"Wrote {REGISTRY_PATH} ({len(personas)} personas, {len(cells)} cells).")
    for cid, slugs in cells.items():
        if not slugs:
            print(f"WARN: cell {cid} empty", file=sys.stderr)


if __name__ == "__main__":
    main()
