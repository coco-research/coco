"""Coco Learning System — data models for instincts and observations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


VALID_DOMAINS = frozenset({
    "testing", "security", "architecture", "workflow",
    "debugging", "performance", "documentation", "devops",
})

INSTINCT_ID_RE = re.compile(r"^inst-\d{8}-[a-z0-9]{6}$")


@dataclass
class Observation:
    """A single captured tool-use event from a session."""

    timestamp: str
    event: str
    session: str
    tool: str
    input_summary: str = ""
    output_summary: str = ""
    project_id: str = ""
    project_name: str = ""

    def validate(self) -> None:
        if not self.timestamp:
            raise ValueError("Observation missing timestamp")
        if not self.event:
            raise ValueError("Observation missing event type")
        if not self.tool:
            raise ValueError("Observation missing tool name")
        if not self.project_id:
            raise ValueError("Observation missing project_id")


@dataclass
class Instinct:
    """An atomic learned behavior extracted from observations."""

    id: str
    pattern: str
    domain: str
    confidence: float = 0.3
    evidence_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    source_project: str = ""
    promoted: bool = False
    superseded_by: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not INSTINCT_ID_RE.match(self.id):
            raise ValueError(f"Invalid instinct id format: {self.id}")
        if not self.pattern:
            raise ValueError("Instinct missing pattern")
        if self.domain not in VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain '{self.domain}'; must be one of {sorted(VALID_DOMAINS)}"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence {self.confidence} out of range [0, 1]")
        if self.evidence_count < 0:
            raise ValueError("evidence_count cannot be negative")

    def compute_confidence(self) -> float:
        """Recompute confidence from evidence count using the schema algorithm."""
        raw = 0.3 + (self.evidence_count * 0.05)
        self.confidence = round(min(0.9, raw), 4)
        return self.confidence

    @property
    def state(self) -> str:
        if self.superseded_by:
            return "superseded"
        if self.confidence >= 0.7:
            return "strong"
        if self.confidence >= 0.5:
            return "active"
        return "candidate"

    def is_promotion_eligible(self, distinct_projects: int = 0) -> bool:
        """Check whether this instinct qualifies for global promotion."""
        return (
            self.confidence >= 0.7
            and self.evidence_count >= 10
            and distinct_projects >= 2
            and not self.promoted
            and self.superseded_by is None
        )
