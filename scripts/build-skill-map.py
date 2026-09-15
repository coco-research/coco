#!/usr/bin/env python3
"""Generate docs/skill-map.json — portable discovery index (no new runtime).

Projects from existing SSoTs:
  docs/asset-counts.json
  skills/ (SKILL.md frontmatter)
  commands/ (shipped markdown)
  systems/superintelligence/scripts/build_meta_commands.py VERBS (SI-* family)

Do not invent Maker/other ids: only emit skills that exist on disk.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip().strip('"').strip("'")
        if v.lower() in ("true", "false"):
            meta[k.strip()] = v.lower() == "true"
        else:
            meta[k.strip()] = v
    return meta


def collect_skills() -> list[dict]:
    out = []
    for skill_md in sorted(ROOT.joinpath("skills").glob("*/SKILL.md")):
        meta = _frontmatter(skill_md.read_text(encoding="utf-8"))
        sid = meta.get("name") or skill_md.parent.name
        out.append(
            {
                "kind": "skill",
                "id": sid,
                "path": str(skill_md.relative_to(ROOT)),
                "description": meta.get("description", ""),
                "domain": meta.get("domain", ""),
                "required": bool(meta.get("required", False))
                or sid in ("karpathy-guidelines", "maker-mdap"),
                "tags": [t for t in [meta.get("domain", ""), meta.get("baseline", "")] if t],
            }
        )
    # Bundle skills under systems/*/skills/*/SKILL.md
    for skill_md in sorted(ROOT.joinpath("systems").glob("*/skills/*/SKILL.md")):
        meta = _frontmatter(skill_md.read_text(encoding="utf-8"))
        sid = meta.get("name") or skill_md.parent.name
        bundle = skill_md.relative_to(ROOT).parts[1]
        out.append(
            {
                "kind": "skill",
                "id": sid,
                "path": str(skill_md.relative_to(ROOT)),
                "description": meta.get("description", ""),
                "domain": meta.get("domain", "") or f"bundle:{bundle}",
                "required": False,
                "tags": [f"bundle:{bundle}"],
            }
        )
    return out


def collect_commands() -> list[dict]:
    out = []
    commands = ROOT / "commands"
    for md in sorted(commands.rglob("*.md")):
        if md.name in ("INDEX.md", "README.md"):
            continue
        rel = md.relative_to(commands)
        parts = rel.parts
        if len(parts) == 1:
            continue
        ns, name = parts[0], parts[1].removesuffix(".md")
        if name == "_index":
            slash = f"/{ns}"
            cid = ns
        else:
            slash = f"/{ns}:{name}"
            cid = f"{ns}:{name}"
        body = md.read_text(encoding="utf-8", errors="replace")
        # first non-empty line as description hint
        desc = ""
        for line in body.splitlines():
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("---"):
                desc = s[:200]
                break
        out.append(
            {
                "kind": "command",
                "id": cid,
                "slash": slash,
                "path": str(md.relative_to(ROOT)),
                "description": desc,
                "required": False,
                "tags": [ns],
            }
        )
    return out


def collect_si_verbs() -> list[dict]:
    gen = ROOT / "systems/superintelligence/scripts/build_meta_commands.py"
    verbs = {}
    if gen.exists():
        text = gen.read_text(encoding="utf-8")
        m = re.search(r"VERBS\s*=\s*\{([^}]+)\}", text, re.S)
        if m:
            for title, desc in re.findall(
                r"'([A-Za-z0-9-]+)'\s*:\s*\(\s*'([^']+)'", m.group(1)
            ):
                verbs[title] = desc
    # Fallback locked list if parse fails
    if not verbs:
        verbs = {
            "Analyse": "multi-team analysis",
            "Decide": "cross-team decision matrix",
            "Review": "multi-team critique",
            "Plan": "phased plan synthesis",
            "Design": "architecture/feature design",
            "Debug": "multi-lens diagnosis",
            "Vote": "yes/no per persona",
            "Tradeoff": "side-by-side A-vs-B",
        }
    out = [
        {
            "kind": "si_verb",
            "id": f"SI-{title}",
            "slash": f"/SI-{title}",
            "path": None,
            "description": desc,
            "required": False,
            "tags": ["si", "generated"],
        }
        for title, desc in sorted(verbs.items())
    ]
    out.insert(
        0,
        {
            "kind": "si_verb",
            "id": "SI-Orchestrate",
            "slash": "/SI-Orchestrate",
            "path": None,
            "description": "cross-team selection + approval gate (verbs call this)",
            "required": False,
            "tags": ["si", "generated"],
        },
    )
    return out


def main() -> None:
    counts_path = ROOT / "docs" / "asset-counts.json"
    counts = json.loads(counts_path.read_text(encoding="utf-8"))
    skills = collect_skills()
    commands = collect_commands()
    si_verbs = collect_si_verbs()
    doc = {
        "schema": 1,
        "source": {
            "asset_counts": "docs/asset-counts.json",
            "builder": "scripts/build-skill-map.py",
        },
        "totals": {
            "skills": counts.get("skills", {}).get("total"),
            "commands_customer_facing": counts.get("commands", {}).get(
                "customer_facing"
            ),
            "commands_shipped": counts.get("commands", {}).get("shipped"),
            "commands_generated_si": counts.get("commands", {}).get("generated_si"),
        },
        "required_baseline": [
            e["id"] for e in skills if e.get("required")
        ],
        "entries": skills + commands + si_verbs,
    }
    # JSON is the machine form (no PyYAML required). A one-line pointer MD sits beside it.
    out = ROOT / "docs" / "skill-map.json"
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ptr = ROOT / "docs" / "skill-map.md"
    ptr.write_text(
        "\n".join(
            [
                "# Skill map",
                "",
                "Generated by `python3 scripts/build-skill-map.py`. Do not hand-edit.",
                "",
                f"- Machine index: [`skill-map.json`](skill-map.json) ({len(doc['entries'])} entries)",
                f"- Totals from [`asset-counts.json`](asset-counts.json): skills={doc['totals'].get('skills')}, commands_customer_facing={doc['totals'].get('commands_customer_facing')}",
                f"- Required baseline: {', '.join(doc['required_baseline']) or '(none)'}",
                "",
                "Discovery: use the `skill-map` skill (ranks entries locally; no new runtime).",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {out.relative_to(ROOT)} ({len(doc['entries'])} entries)")
    print("required_baseline:", doc["required_baseline"])
    print("totals:", doc["totals"])


if __name__ == "__main__":
    main()
