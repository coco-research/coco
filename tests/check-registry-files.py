#!/usr/bin/env python3
"""Verify every Super Intelligence team registry agrees with persona files on disk.

Checks all 13 departments under systems/superintelligence/:
  1. every registry persona's file_path exists under systems/;
  2. every <dept>/personas/*.md is the file_path of an entry in its own registry;
  3. every cell's personas list is a subset of that registry's personas;
  4. personas_count equals the list length, for the registry and for each cell.

Run from repo root: python3 tests/check-registry-files.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ROOT / "systems"
BOARD = SYSTEMS / "superintelligence"


def _safe_under_systems(rel: str) -> Path | None:
    if not isinstance(rel, str) or not rel or rel.startswith("/"):
        return None
    p = Path(rel)
    if ".." in p.parts:
        return None
    target = (SYSTEMS / p).resolve()
    try:
        target.relative_to(SYSTEMS.resolve())
    except ValueError:
        return None
    return target


def main() -> int:
    meta = json.loads((BOARD / "registry.json").read_text(encoding="utf-8"))
    depts = sorted(set(meta.get("teams", {}).keys()) | {p.parent.name for p in BOARD.glob("*/registry.json")})
    fails: list[str] = []
    checked_entries = 0
    checked_files = 0

    for dept in depts:
        reg_path = BOARD / dept / "registry.json"
        if not reg_path.is_file():
            fails.append(f"{dept}: missing-registry: superintelligence/{dept}/registry.json")
            continue
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        personas = reg.get("personas")
        cells = reg.get("cells")
        if not isinstance(personas, dict) or not isinstance(cells, dict):
            fails.append(f"{dept}: invalid-registry: superintelligence/{dept}/registry.json")
            continue

        reg_count = reg.get("personas_count")
        if reg_count != len(personas):
            fails.append(f"{dept}: count-mismatch: registry ({reg_count} != {len(personas)})")

        registered_paths: set[str] = set()
        for slug, entry in sorted(personas.items()):
            checked_entries += 1
            fp = entry.get("file_path") if isinstance(entry, dict) else None
            target = _safe_under_systems(fp) if isinstance(fp, str) else None
            if target is None or not target.is_file():
                fails.append(f"{dept}: missing-file: {slug} ({fp})")
            else:
                registered_paths.add(fp)

        personas_dir = BOARD / dept / "personas"
        for md in sorted(personas_dir.glob("*.md")):
            checked_files += 1
            rel_fp = f"superintelligence/{dept}/personas/{md.name}"
            if rel_fp not in registered_paths:
                fails.append(f"{dept}: unregistered-file: {rel_fp}")

        for cid, cell in sorted(cells.items()):
            plist = cell.get("personas") if isinstance(cell, dict) else None
            ccount = cell.get("personas_count") if isinstance(cell, dict) else None
            if not isinstance(plist, list):
                fails.append(f"{dept}: invalid-cell: {cid}")
                continue
            if ccount != len(plist):
                fails.append(f"{dept}: count-mismatch: {cid} ({ccount} != {len(plist)})")
            for slug in plist:
                if slug not in personas:
                    fails.append(f"{dept}: unknown-cell-persona: {cid}/{slug}")

    if fails:
        for line in fails:
            print(line)
        return 1

    print(
        f"PASS: {len(depts)} departments, {checked_entries} registry entries, "
        f"{checked_files} persona files agree"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
