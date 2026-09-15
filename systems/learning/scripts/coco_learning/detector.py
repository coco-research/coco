"""Coco Learning System — pattern detector for extracting instincts from observations."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import Instinct, Observation
from .storage import (
    append_observation,
    ensure_dirs,
    get_project_dir,
    list_instincts,
    load_instinct,
    save_instinct,
)


# Simple heuristic patterns that map observation signatures to instinct templates.
# Each entry: (tool_pattern, input_pattern, domain, template, tags)
HEURISTIC_RULES: list[tuple[str, str, str, str, list[str]]] = [
    # Testing patterns
    (r"Bash", r"(npm test|pytest|cargo test|go test|mvn test|gradle test)", "testing",
     "Run tests after modifying code in this project", ["testing", "safety"]),
    (r"Bash", r"(npm run lint|eslint|pylint|ruff check|flake8)", "testing",
     "Run linter before committing changes", ["testing", "quality"]),
    # Security patterns
    (r"(Write|Edit)", r".*(password|secret|token|api_key).*", "security",
     "Never hardcode secrets in source files", ["security", "secrets"]),
    # Git/workflow patterns
    (r"Bash", r"git commit", "workflow",
     "Commit frequently with descriptive messages", ["workflow", "git"]),
    (r"Bash", r"git checkout -b", "workflow",
     "Create feature branches for isolated work", ["workflow", "git"]),
    # Database patterns
    (r"(Write|Edit)", r".*(migration|migrate|ALTER TABLE|CREATE TABLE).*", "architecture",
     "Run migrations after schema changes", ["database", "architecture"]),
    # Debugging patterns
    (r"Bash", r"(console\.log|print\(|logging\.|debugger)", "debugging",
     "Add logging when debugging complex issues", ["debugging", "observability"]),
    # Performance patterns
    (r"(Write|Edit)", r".*(cache|redis|memcached|lru_cache).*", "performance",
     "Consider caching for repeated expensive operations", ["performance", "caching"]),
]


def _generate_instinct_id() -> str:
    """Generate a unique instinct ID."""
    import secrets
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_part = secrets.token_hex(3)
    return f"inst-{date_part}-{rand_part}"


def load_observations(project_id: str, limit: int = 500) -> list[Observation]:
    """Load recent observations from a project's JSONL file."""
    obs_file = get_project_dir(project_id) / "observations.jsonl"
    if not obs_file.exists():
        return []
    observations: list[Observation] = []
    lines = obs_file.read_text(encoding="utf-8").strip().split("\n")
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            observations.append(Observation(
                timestamp=data.get("timestamp", ""),
                event=data.get("event", ""),
                session=data.get("session", ""),
                tool=data.get("tool", ""),
                input_summary=data.get("input_summary", ""),
                output_summary=data.get("output_summary", ""),
                project_id=data.get("project_id", project_id),
                project_name=data.get("project_name", ""),
            ))
        except json.JSONDecodeError:
            continue
    return observations


def detect_patterns(
    project_id: str,
    min_evidence: int = 3,
) -> list[Instinct]:
    """Scan observations and extract candidate instincts using heuristic rules.

    Returns a list of new or reinforced instincts (not yet saved).
    """
    observations = load_observations(project_id)
    if not observations:
        return []

    # Count matches per rule
    rule_hits: dict[int, list[Observation]] = defaultdict(list)
    for obs in observations:
        for idx, (tool_re, input_re, _domain, _template, _tags) in enumerate(HEURISTIC_RULES):
            if re.search(tool_re, obs.tool, re.IGNORECASE) and \
               re.search(input_re, obs.input_summary + " " + obs.output_summary, re.IGNORECASE):
                rule_hits[idx].append(obs)

    candidates: list[Instinct] = []
    existing = {i.pattern: i for i in list_instincts(project_id)}

    for idx, hits in rule_hits.items():
        if len(hits) < min_evidence:
            continue
        _tool_re, _input_re, domain, template, tags = HEURISTIC_RULES[idx]

        if template in existing:
            # Reinforce existing instinct
            inst = existing[template]
            inst.evidence_count += len(hits)
            inst.compute_confidence()
            inst.updated_at = datetime.now(timezone.utc).isoformat()
            candidates.append(inst)
        else:
            # Create new candidate instinct
            first_ts = hits[0].timestamp if hits else datetime.now(timezone.utc).isoformat()
            inst = Instinct(
                id=_generate_instinct_id(),
                pattern=template,
                domain=domain,
                evidence_count=len(hits),
                created_at=first_ts,
                updated_at=datetime.now(timezone.utc).isoformat(),
                source_project=project_id,
                tags=tags,
            )
            inst.compute_confidence()
            candidates.append(inst)

    return candidates


def run_detection_cycle(project_id: str, auto_save: bool = True) -> list[Instinct]:
    """Full detection cycle: scan → detect → optionally save.

    Returns the list of detected/reinforced instincts.
    """
    candidates = detect_patterns(project_id)
    if auto_save and candidates:
        ensure_dirs(project_id)
        for inst in candidates:
            save_instinct(inst, project_id)
    return candidates
