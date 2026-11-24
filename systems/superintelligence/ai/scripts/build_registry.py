#!/usr/bin/env python3
# ponytail: 13 near-copies of this generator; upgrade path is one shared generator taking the team as an argument.
"""
Build superintelligenceTeam/registry.json from persona file frontmatter.

Reads every superintelligenceTeam/personas/*.md, extracts the YAML frontmatter,
and emits a machine-readable registry consumed by:
  - superintelligenceTeam/SKILL.md (entry point)
  - .claude/commands/superintelligenceTeam*.md (slash commands)
  - future cross-team routing

Re-run this script after editing any persona file. Idempotent.

Usage:
    python3 superintelligenceTeam/scripts/build_registry.py
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

# Script lives at superintelligence/ai/scripts/build_registry.py
AI_DIR = Path(__file__).resolve().parents[1] # -> superintelligence/ai
REPO_ROOT = AI_DIR.parents[1] # -> coco-platform
PERSONAS_DIR = AI_DIR / "personas"
REGISTRY_PATH = AI_DIR / "registry.json"

KNOWN_CELLS_AI_SI = OrderedDict([
    ("frontier-labs-research", "Frontier foundation models, compute scaling, pretraining economics, and capability strategy."),
    ("applied-ai-leadership", "Language-model assistants, chatbots, document QA, semantic vector search, RAG, and citation grounding."),
    ("model-architects", "Transformer architectures, model compression, quantization, knowledge distillation, pruning, tokenization, fine-tuning, and prompting."),
    ("reasoning-rl-agents", "Post-training, RLHF, preference optimization, reward modeling, reasoning, tool calling, and agentic workflows."),
    ("alignment-interp-safety", "Safety alignment, mechanistic interpretability, prompt-injection defense, hallucination detection, and evaluation benchmarks."),
    ("theory-science", "Deep learning theory, dense representations, semantic similarity, uncertainty calibration, and natural language processing."),
    ("multimodal-embodied", "Multimodal vision-language models, image and video diffusion, world models, speech, and robotics."),
    ("systems-kernels-serving", "Distributed training, GPU kernels, edge and on-device inference, batching, and low-latency model serving."),
])

KNOWN_TEAMS = OrderedDict([
    ("ai-super-intelligence", "AI Super Intelligence Team — frontier AI research, models, alignment, and systems."),
    ("cloud-super-intelligence", "Cloud Super Intelligence Team — AWS, GCP, Azure, infrastructure (future)."),
    ("finance-super-intelligence", "Finance Super Intelligence Team — FP&A, accounting, finance ops (future)."),
    ("coding-super-intelligence", "Coding Super Intelligence Team — software engineering practice (future)."),
    ("design-super-intelligence", "Design Super Intelligence Team — UX, design systems, visual design (future)."),
    ("product-super-intelligence", "Product Super Intelligence Team — PM craft, product strategy (future)."),
])


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name}: no leading frontmatter delimiter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"{path.name}: no closing frontmatter delimiter")
    return yaml.safe_load(text[4:end])


def length_of(field):
    if field is None:
        return 0
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
        text = json.dumps(registry, indent=2) + "\n"
        if text == old:
            break
    REGISTRY_PATH.write_text(text, encoding="utf-8")


def build_persona_index(persona_files: list[Path]) -> tuple[dict, dict]:
    """Returns (personas_by_slug, cells_to_slugs)."""
    personas = OrderedDict()
    cells: dict[str, list[str]] = {c: [] for c in KNOWN_CELLS_AI_SI}
    for path in sorted(persona_files):
        try:
            fm = parse_frontmatter(path)
        except Exception as exc:
            print(f"WARN: skipping {path.name}: {exc}", file=sys.stderr)
            continue
        if fm.get("status") == "held":  # held out until it can be sourced: not in the registry, so not in ROSTER/SKILL/cells
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
            "cell": cell,
            "cell_letter": fm.get("cell_letter"),
            "cell_role": fm.get("cell_role"),
            "status": fm.get("status"),
            "affiliations_2026": fm.get("affiliations_2026", []),
            "domains": fm.get("domains", []),
            "pairs_well_with": fm.get("pairs_well_with", []),
            "productive_conflict_with": fm.get("productive_conflict_with", []),
            "v2_panel_attribution_count": length_of(fm.get("v2_panel_attribution")),
            "sources_count": length_of(fm.get("sources")),
            "recent_signal_12mo_count": length_of(fm.get("recent_signal_12mo")),
            "persistent_signals_count": length_of(fm.get("persistent_signals")),
            "public_stances_count": length_of(fm.get("public_stances")),
            "confidence": fm.get("confidence"),
            "last_verified": str(fm.get("last_verified", "")),
            "voice_style_excerpt": (fm.get("voice_style", "") or "").strip().splitlines()[0][:160]
            if fm.get("voice_style") else "",
            "file_path": f"superintelligence/ai/personas/{path.name}",
            "research_dir": f"superintelligenceTeam/research/{slug}/",
        }
    return personas, cells


def build_cells_section(cells: dict[str, list[str]]) -> OrderedDict:
    out = OrderedDict()
    for cell_id, slugs in cells.items():
        out[cell_id] = {
            "id": cell_id,
            "description": KNOWN_CELLS_AI_SI[cell_id],
            "personas_count": len(slugs),
            "personas": slugs,
            "file_path": f"superintelligenceTeam/cells/{cell_id}.md",
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
        ("team_id", "ai-super-intelligence"),
        ("team_name", "AI Super Intelligence Team"),
        (
            "description",
            "Large and small language models, chatbots, AI assistants, transformers, dense "
            "embeddings, semantic vector search, retrieval-augmented generation (RAG), grounding "
            "and citation checks, hallucination detection, fine-tuning versus prompting, model "
            "compression, quantization, distillation, tool calling, RLHF and preference "
            "alignment, prompt-injection defense, evaluation benchmarks, multimodal models, and "
            "inference serving.",
        ),
        ("personas_count", len(personas)),
        ("cells_count", len(cells_to_slugs)),
        ("cells", build_cells_section(cells_to_slugs)),
        ("personas", personas),
        ("known_teams", KNOWN_TEAMS),
        (
            "lineage",
            {
                "founding_v2_panel": {
                    "date": "2026-05-26",
                    "note": (
                        "Earlier 5-cell × 4-persona panel synthesized the founding Memory v2 "
                        "architecture. Personas with `v2_panel_attribution` entries draw on "
                        "that material; cell_letter A-E preserves cross-team back-compat."
                    ),
                    "source_artifacts": [
                        "internal synthesis (not publicly citable)",
                        "internal synthesis (not publicly citable)",
                        "internal synthesis (not publicly citable)",
                        "internal synthesis (not publicly citable)",
                        "internal synthesis (not publicly citable)",
                    ],
                },
            },
        ),
    ])

    write_registry(registry)
    print(f"Wrote {REGISTRY_PATH} ({len(personas)} personas, {len(cells_to_slugs)} cells).")

    # Sanity checks
    for cell_id, slugs in cells_to_slugs.items():
        if not slugs:
            print(f"WARN: cell {cell_id} is empty", file=sys.stderr)
    panel_count = sum(1 for p in personas.values() if p["v2_panel_attribution_count"] > 0)
    print(f" founding v2 panel-attributed personas: {panel_count}")


if __name__ == "__main__":
    main()
