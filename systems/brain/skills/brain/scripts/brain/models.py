"""Dataclasses and enums for all brain domain objects."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import json
import sqlite3


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EntityType(str, Enum):
    PERSON = "person"
    TEAM = "team"
    ROLE = "role"
    SYSTEM = "system"
    MODULE = "module"
    ORG_UNIT = "org_unit"
    DOCUMENT = "document"


class RelType(str, Enum):
    MEMBER_OF = "member_of"
    OWNS = "owns"
    ADMINISTERS = "administers"
    REPORTS_TO = "reports_to"
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"
    SCOPED_TO = "scoped_to"
    CREATED_BY = "created_by"


class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    WAITING = "waiting"
    DONE = "done"
    CANCELLED = "cancelled"


class ThreadCategory(str, Enum):
    FEATURE = "feature"
    INCIDENT = "incident"
    REQUEST = "request"
    DECISION = "decision"
    RESEARCH = "research"


class EventType(str, Enum):
    MEETING = "meeting"
    EMAIL = "email"
    CALL = "call"
    MILESTONE = "milestone"
    DEPLOY = "deploy"


def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


@dataclass
class Project:
    id: int = 0
    name: str = ""
    slug: str = ""
    status: str = "active"
    description: str = ""
    created_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Entity:
    id: int = 0
    project_id: int = 0
    type: str = ""
    name: str = ""
    external_id: str | None = None
    metadata_json: str = "{}"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @property
    def metadata(self) -> dict:
        return json.loads(self.metadata_json) if self.metadata_json else {}

    def to_dict(self) -> dict:
        d = asdict(self)
        d["metadata"] = self.metadata
        return d


@dataclass
class Relationship:
    id: int = 0
    source_id: int = 0
    target_id: int = 0
    rel_type: str = ""
    context: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None


@dataclass
class Task:
    id: int = 0
    project_id: int = 0
    title: str = ""
    status: str = "open"
    owner_entity_id: int | None = None
    priority: int = 3
    due_date: str | None = None
    blocked_by_task_id: int | None = None
    notes: str | None = None
    created_at: str = field(default_factory=now_iso)
    completed_at: str | None = None


@dataclass
class Thread:
    id: int = 0
    project_id: int = 0
    title: str = ""
    status: str = "open"
    category: str | None = None
    created_at: str = field(default_factory=now_iso)


@dataclass
class Decision:
    id: int = 0
    project_id: int = 0
    thread_id: int | None = None
    date: str = ""
    decision: str = ""
    context: str | None = None
    decided_by: str | None = None
    impact: str | None = None


@dataclass
class Event:
    id: int = 0
    project_id: int = 0
    date: str = ""
    type: str = ""
    title: str = ""
    summary: str | None = None
    source: str | None = None
    participants_json: str = "[]"

    @property
    def participants(self) -> list:
        return json.loads(self.participants_json) if self.participants_json else []
