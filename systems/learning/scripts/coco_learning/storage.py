"""Coco Learning System — file-based storage for instincts and observations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import yaml

from .models import Instinct, Observation


def _base_dir() -> Path:
    return Path(os.environ.get("COCO_LEARNING_DIR", Path.home() / ".coco" / "learning"))


def get_project_dir(project_id: str) -> Path:
    return _base_dir() / "projects" / project_id


def get_global_dir() -> Path:
    return _base_dir() / "global"


def ensure_dirs(project_id: Optional[str] = None) -> None:
    """Create required directory structure."""
    g = get_global_dir() / "instincts"
    g.mkdir(parents=True, exist_ok=True)
    if project_id:
        p = get_project_dir(project_id) / "instincts"
        p.mkdir(parents=True, exist_ok=True)


def save_instinct(instinct: Instinct, project_id: Optional[str] = None) -> Path:
    """Persist an instinct to YAML. If project_id is None, saves to global."""
    ensure_dirs(project_id)
    if project_id:
        base = get_project_dir(project_id) / "instincts"
    else:
        base = get_global_dir() / "instincts"
    path = base / f"{instinct.id}.yaml"
    data = {
        "id": instinct.id,
        "pattern": instinct.pattern,
        "domain": instinct.domain,
        "confidence": instinct.confidence,
        "evidence_count": instinct.evidence_count,
        "created_at": instinct.created_at,
        "updated_at": instinct.updated_at,
        "source_project": instinct.source_project,
        "promoted": instinct.promoted,
        "superseded_by": instinct.superseded_by,
        "tags": instinct.tags,
    }
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")
    return path


def load_instinct(instinct_id: str, project_id: Optional[str] = None) -> Optional[Instinct]:
    """Load an instinct from YAML. Returns None if not found."""
    if project_id:
        path = get_project_dir(project_id) / "instincts" / f"{instinct_id}.yaml"
    else:
        path = get_global_dir() / "instincts" / f"{instinct_id}.yaml"
    if not path.exists():
        # Try global fallback when project_id was specified
        if project_id:
            path = get_global_dir() / "instincts" / f"{instinct_id}.yaml"
            if not path.exists():
                return None
        else:
            return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Instinct(
        id=data["id"],
        pattern=data["pattern"],
        domain=data["domain"],
        confidence=float(data.get("confidence", 0.3)),
        evidence_count=int(data.get("evidence_count", 0)),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
        source_project=data.get("source_project", ""),
        promoted=bool(data.get("promoted", False)),
        superseded_by=data.get("superseded_by"),
        tags=data.get("tags", []),
    )


def list_instincts(project_id: Optional[str] = None, include_superseded: bool = False) -> list[Instinct]:
    """List all instincts in a scope (project or global)."""
    results: list[Instinct] = []
    dirs = []
    if project_id:
        dirs.append(get_project_dir(project_id) / "instincts")
    dirs.append(get_global_dir() / "instincts")
    for d in dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.yaml")):
            inst = load_instinct(f.stem, project_id=None if d == get_global_dir() / "instincts" else project_id)
            if inst is None:
                continue
            if not include_superseded and inst.superseded_by:
                continue
            results.append(inst)
    return results


def delete_instinct(instinct_id: str, project_id: Optional[str] = None) -> bool:
    """Delete an instinct YAML file. Returns True if deleted."""
    if project_id:
        path = get_project_dir(project_id) / "instincts" / f"{instinct_id}.yaml"
    else:
        path = get_global_dir() / "instincts" / f"{instinct_id}.yaml"
    if path.exists():
        path.unlink()
        return True
    return False


def append_observation(obs: Observation) -> Path:
    """Append an observation as a JSON line to the project's observations.jsonl."""
    ensure_dirs(obs.project_id)
    obs_dir = get_project_dir(obs.project_id)
    obs_file = obs_dir / "observations.jsonl"
    line = json.dumps({
        "timestamp": obs.timestamp,
        "event": obs.event,
        "session": obs.session,
        "tool": obs.tool,
        "input_summary": obs.input_summary,
        "output_summary": obs.output_summary,
        "project_id": obs.project_id,
        "project_name": obs.project_name,
    }, ensure_ascii=False) + "\n"
    with open(obs_file, "a", encoding="utf-8") as f:
        f.write(line)
    return obs_file
