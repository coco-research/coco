"""Coco Learning System — Team feedback to instincts bridge.

Converts structured team review feedback into learning observations
and triggers pattern detection for continuous improvement.

Team roles (from commands/team/roles.md) produce feedback in standardized formats.
This module parses that feedback and feeds it into the learning pipeline.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Optional

from .models import Observation
from .storage import append_observation, ensure_dirs
from .detector import run_detection_cycle


# Mapping of team role names to learning domains
ROLE_DOMAIN_MAP: dict[str, str] = {
    "code-reviewer": "testing",
    "test-guardian": "testing",
    "security-reviewer": "security",
    "refactoring-specialist": "architecture",
    "database-architect": "architecture",
    "ai-engineer": "performance",
    "typescript-pro": "workflow",
    "ui-ux-designer": "workflow",
    "pm-advisor": "workflow",
    "data-specialist": "debugging",
    "mcp-specialist": "devops",
}

# Patterns in feedback text that indicate actionable learning opportunities
FEEDBACK_PATTERNS: list[tuple[str, str, list[str]]] = [
    # (regex, instinct_template, tags)
    (r"(always|never|must|should)\s+(run|execute|check|verify)\s+tests?", 
     "Always run tests after code changes", ["testing", "safety"]),
    (r"(security|vulnerability|injection|xss|csrf)", 
     "Review security implications before merging", ["security", "review"]),
    (r"(performance|slow|latency|bottleneck|optimize)", 
     "Profile before optimizing performance-critical paths", ["performance", "optimization"]),
    (r"(documentation|docs?|comment|readme)", 
     "Update documentation when changing public APIs", ["documentation", "maintenance"]),
    (r"(error handling|try.?catch|exception|graceful)", 
     "Add comprehensive error handling at boundaries", ["debugging", "reliability"]),
    (r"(breaking change|migration|deprecat)", 
     "Plan migration strategy for breaking changes", ["workflow", "compatibility"]),
    (r"(test coverage|coverage.*low|untested)", 
     "Maintain test coverage above 80% for modified code", ["testing", "quality"]),
    (r"(n\+1|query.*efficien|index|database.*slow)", 
     "Check for N+1 queries when modifying data access", ["performance", "database"]),
]


def parse_team_feedback(
    role: str,
    feedback_text: str,
    project_id: str,
    session_id: str = "team-review",
) -> list[Observation]:
    """Parse team review feedback into learning observations.
    
    Args:
        role: Team role name (e.g., "code-reviewer", "test-guardian")
        feedback_text: The review feedback content
        project_id: Target project identifier
        session_id: Session identifier for grouping
        
    Returns:
        List of Observation objects ready for storage
    """
    observations: list[Observation] = []
    timestamp = datetime.now(timezone.utc).isoformat()
    domain = ROLE_DOMAIN_MAP.get(role, "workflow")
    
    # Check each feedback pattern
    for pattern_re, template, tags in FEEDBACK_PATTERNS:
        if re.search(pattern_re, feedback_text, re.IGNORECASE):
            obs = Observation(
                timestamp=timestamp,
                event="TeamFeedback",
                session=session_id,
                tool=f"team:{role}",
                input_summary=template,
                output_summary=f"domain={domain},tags={','.join(tags)}",
                project_id=project_id,
                project_name="",
            )
            observations.append(obs)
    
    return observations


def ingest_team_feedback(
    role: str,
    feedback_text: str,
    project_id: str,
    session_id: str = "team-review",
    auto_evolve: bool = True,
) -> dict:
    """Full pipeline: parse feedback → store observations → optionally evolve.
    
    Args:
        role: Team role name
        feedback_text: Review feedback content  
        project_id: Target project identifier
        session_id: Session identifier
        auto_evolve: Whether to run pattern detection after ingestion
        
    Returns:
        Dict with 'observations_stored', 'instincts_detected', 'instincts' keys
    """
    ensure_dirs(project_id)
    
    # Parse and store observations
    observations = parse_team_feedback(role, feedback_text, project_id, session_id)
    for obs in observations:
        append_observation(obs)
    
    result = {
        "observations_stored": len(observations),
        "instincts_detected": 0,
        "instincts": [],
    }
    
    # Optionally run evolution cycle
    if auto_evolve and observations:
        instincts = run_detection_cycle(project_id, auto_save=True)
        result["instincts_detected"] = len(instincts)
        result["instincts"] = [
            {
                "id": i.id,
                "pattern": i.pattern,
                "confidence": i.confidence,
                "state": i.state,
            }
            for i in instincts
        ]
    
    return result


def get_role_domain(role: str) -> str:
    """Get the learning domain for a team role."""
    return ROLE_DOMAIN_MAP.get(role, "workflow")
