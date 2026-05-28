"""
Build a rich system prompt with full CoCo context for chat sessions.

Aggregates data from brain.json, hub mirrors, platform tables, and queue.json
into a concise system prompt that stays under ~2000 tokens.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    func,
    select,
)

from app.config import BRAIN_JSON_PATH, QUEUE_JSON_PATH, CONFIG_JSON_PATH, HUB_DB_PATH, KNOWLEDGE_DB_PATH

# Media-memory directory — overridable via env var for portability. Defaults to
# the historical ~/.claude/media-memory location used by the Claude Code
# media-memory subsystem. Kept here so chat-context builders can surface
# media-memory availability uniformly across services.
MEDIA_MEMORY_DIR = Path(
    os.environ.get("COCO_MEDIA_MEMORY_DIR")
    or (Path.home() / ".claude" / "media-memory")
).expanduser()
from app.db.session import get_db
from app.services.collaboration_context import build_knowledge_context
from app.db.tables import (
    hub_projects, hub_content, hub_todos, hub_sync_state,
    nodes, agents, governance_log,
)
from app.services.json_store import read_json

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Knowledge DB (read-only) — SA Core table definitions
#
# The knowledge DB lives at KNOWLEDGE_DB_PATH and is owned by the Knowledge
# Engine, not by platform.db. We bind a local read-only SA engine + table
# definitions here so this service can query it via SA Core expressions
# instead of raw SQL. Engines are cached per-path via _knowledge_engine().
# ---------------------------------------------------------------------------

_knowledge_metadata = MetaData()

knowledge_global_entities = Table(
    "global_entities",
    _knowledge_metadata,
    Column("gid", Text, primary_key=True),
    Column("canonical_name", Text, nullable=False),
    Column("type", Text, nullable=False),
    Column("importance_score", Float, nullable=False, server_default="0.0"),
)

knowledge_articles = Table(
    "articles",
    _knowledge_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("gid", Text, nullable=False),
)

knowledge_cross_project_connections = Table(
    "cross_project_connections",
    _knowledge_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_gid", Text, nullable=False),
    Column("target_gid", Text, nullable=False),
)

knowledge_project_entity_links = Table(
    "project_entity_links",
    _knowledge_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("gid", Text, nullable=False),
    Column("project_slug", Text, nullable=False),
)

_knowledge_engine_cache: dict = {}


def _knowledge_engine(db_path):
    """Lazy-create a read-only SA engine for the knowledge DB.

    Cached per-path so repeated calls reuse the same engine.
    """
    key = str(db_path)
    eng = _knowledge_engine_cache.get(key)
    if eng is None:
        eng = create_engine(
            f"sqlite:///file:{db_path}?mode=ro&uri=true",
            connect_args={"uri": True, "timeout": 10},
        )
        _knowledge_engine_cache[key] = eng
    return eng


def build_chat_context(
    project_id: str | None = None,
    node_id: str | None = None,
) -> str:
    sections: list[str] = []

    sections.append(
        "You are CoCo, Rijul's AI assistant. You have access to his "
        "Knowledge Hub, brain, and project data. Be concise and helpful."
    )

    now = datetime.now(timezone.utc)
    sections.append(f"Current date/time: {now.strftime('%Y-%m-%d %H:%M UTC')} ({now.strftime('%A')})")

    brain_section = _build_brain_section()
    if brain_section:
        sections.append(brain_section)

    projects_section = _build_projects_section(project_id)
    if projects_section:
        sections.append(projects_section)

    tree_section = _build_tree_section(node_id)
    if tree_section:
        sections.append(tree_section)

    queue_section = _build_queue_section()
    if queue_section:
        sections.append(queue_section)

    activity_section = _build_activity_section()
    if activity_section:
        sections.append(activity_section)

    agents_section = _build_agents_section()
    if agents_section:
        sections.append(agents_section)

    knowledge_section = _build_knowledge_engine_section(project_id)
    if knowledge_section:
        sections.append(knowledge_section)

    try:
        knowledge_ctx = build_knowledge_context(
            node_id=node_id, project_id=project_id, token_budget=1500
        )
        if knowledge_ctx:
            sections.append(knowledge_ctx)
    except Exception as e:
        log.debug("knowledge_context_injection_skipped: %s", e)

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_knowledge_engine_section(project_id: str | None = None) -> str | None:
    """Query the Knowledge Engine for relevant entities and connections.

    Uses SA Core expressions against a cached read-only engine for the
    knowledge DB (separate from platform.db).
    """
    if not KNOWLEDGE_DB_PATH.exists():
        return None

    try:
        engine = _knowledge_engine(KNOWLEDGE_DB_PATH)
        with engine.connect() as conn:
            parts: list[str] = []

            # Get entity / article / connection counts
            total = conn.execute(
                select(func.count()).select_from(knowledge_global_entities)
            ).scalar() or 0
            article_count = conn.execute(
                select(func.count()).select_from(knowledge_articles)
            ).scalar() or 0
            connection_count = conn.execute(
                select(func.count()).select_from(knowledge_cross_project_connections)
            ).scalar() or 0

            parts.append(
                f"Knowledge Graph: {total} entities, {article_count} articles, "
                f"{connection_count} cross-project connections."
            )

            # Get top entities for this project (if project_id provided)
            ge = knowledge_global_entities
            if project_id:
                pel = knowledge_project_entity_links
                rows = conn.execute(
                    select(ge.c.canonical_name, ge.c.type, ge.c.importance_score)
                    .select_from(ge.join(pel, ge.c.gid == pel.c.gid))
                    .where(pel.c.project_slug == project_id)
                    .order_by(ge.c.importance_score.desc())
                    .limit(5)
                ).fetchall()
                if rows:
                    entity_list = ", ".join(
                        f"{r.canonical_name} ({r.type})" for r in rows
                    )
                    parts.append(f"Key entities for this project: {entity_list}")
            else:
                # Top 5 global entities
                rows = conn.execute(
                    select(ge.c.canonical_name, ge.c.type, ge.c.importance_score)
                    .order_by(ge.c.importance_score.desc())
                    .limit(5)
                ).fetchall()
                if rows:
                    entity_list = ", ".join(
                        f"{r.canonical_name} ({r.type})" for r in rows
                    )
                    parts.append(f"Top entities: {entity_list}")

            return "\n".join(parts) if parts else None
    except Exception as e:
        log.debug("knowledge_engine_section_skipped: %s", e)
        return None


def _build_brain_section() -> str:
    try:
        brain = read_json(BRAIN_JSON_PATH)
        if not brain:
            return ""
    except Exception:
        return ""

    parts: list[str] = ["## Brain"]

    raw_people = brain.get("people", {})
    if isinstance(raw_people, dict):
        people = [{"name": k, **v} if isinstance(v, dict) else {"name": k} for k, v in raw_people.items()]
    elif isinstance(raw_people, list):
        people = raw_people
    else:
        people = []

    if people:
        lines: list[str] = []
        for p in people[:10]:
            name = p.get("name", "unknown")
            role = p.get("role", "")
            priority = p.get("priority", "")
            detail = " | ".join(filter(None, [role, f"pri={priority}" if priority else ""]))
            lines.append(f"- {name}" + (f" ({detail})" if detail else ""))
        parts.append("People:\n" + "\n".join(lines))
        if len(people) > 10:
            parts.append(f"  ...and {len(people) - 10} more")

    rules = brain.get("rules", [])
    if rules:
        parts.append(f"Attention rules: {len(rules)} active")

    stats = brain.get("stats", {})
    if stats:
        stat_items = [f"{k}={v}" for k, v in list(stats.items())[:5]]
        parts.append(f"Stats: {', '.join(stat_items)}")

    return "\n".join(parts) if len(parts) > 1 else ""


def _build_projects_section(focused_project_id: str | None) -> str:
    if not HUB_DB_PATH.exists():
        return ""

    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    hub_projects.c.id,
                    hub_projects.c.name,
                )
                .order_by(hub_projects.c.name)
                .limit(15)
            ).fetchall()

            if not rows:
                return ""

            parts: list[str] = ["## Projects"]
            lines = [f"- {r.name}" for r in rows]
            parts.append("\n".join(lines))

            if focused_project_id:
                detail = _build_focused_project(conn, focused_project_id)
                if detail:
                    parts.append(detail)

            return "\n".join(parts)
    except Exception as e:
        log.debug("projects_section_failed: %s", e)
        return ""


def _build_focused_project(conn, project_id: str) -> str:
    try:
        project = conn.execute(
            select(hub_projects.c.id, hub_projects.c.name)
            .where(hub_projects.c.id == project_id)
        ).fetchone()
        if not project:
            return ""

        parts: list[str] = [f"\nFocused project: {project.name}"]

        recent = conn.execute(
            select(hub_content.c.title, hub_content.c.source, hub_content.c.created_at)
            .where(hub_content.c.source.isnot(None))
            .order_by(hub_content.c.created_at.desc())
            .limit(5)
        ).fetchall()
        if recent:
            parts.append("Recent items:")
            for r in recent:
                parts.append(f"  - [{r.source}] {r.title}")

        return "\n".join(parts)
    except Exception:
        return ""


def _build_tree_section(node_id: str | None) -> str:
    try:
        with get_db() as conn:
            summary = conn.execute(
                select(nodes.c.node_type, func.count().label("cnt"))
                .group_by(nodes.c.node_type)
            ).fetchall()
            if not summary:
                return ""

            type_counts = {r.node_type: r.cnt for r in summary}
            parts: list[str] = [
                "## Org Tree",
                f"Nodes: {', '.join(f'{cnt} {t}s' for t, cnt in type_counts.items())}",
            ]

            if node_id:
                node = conn.execute(
                    select(nodes.c.id, nodes.c.label, nodes.c.node_type, nodes.c.path)
                    .where(nodes.c.id == node_id)
                ).fetchone()
                if node:
                    parts.append(f"Current node: {node.label} ({node.node_type})")
                    children = conn.execute(
                        select(nodes.c.label, nodes.c.node_type)
                        .where(nodes.c.parent_id == node_id)
                        .order_by(nodes.c.sort_order)
                        .limit(10)
                    ).fetchall()
                    if children:
                        parts.append("Children: " + ", ".join(
                            f"{c.label} ({c.node_type})" for c in children
                        ))

            return "\n".join(parts)
    except Exception as e:
        log.debug("tree_section_failed: %s", e)
        return ""


def _build_queue_section() -> str:
    try:
        queue = read_json(QUEUE_JSON_PATH)
        if not queue:
            return ""
    except Exception:
        return ""

    items = queue.get("items", [])
    if not items:
        return ""

    pending = sum(1 for i in items if i.get("status") == "pending")
    drafts = sum(1 for i in items if i.get("status") == "draft")
    urgent = sum(1 for i in items if i.get("priority") == "high" or i.get("urgent"))

    parts: list[str] = [f"## Decision Queue: {len(items)} total"]
    details = []
    if pending:
        details.append(f"{pending} pending")
    if drafts:
        details.append(f"{drafts} drafts")
    if urgent:
        details.append(f"{urgent} urgent")
    if details:
        parts.append(", ".join(details))

    return "\n".join(parts)


def _build_activity_section() -> str:
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    governance_log.c.action,
                    governance_log.c.item_type,
                    governance_log.c.item_id,
                    governance_log.c.decision_by,
                    governance_log.c.created_at,
                )
                .order_by(governance_log.c.created_at.desc())
                .limit(5)
            ).fetchall()
            if not rows:
                return ""

            parts: list[str] = ["## Recent Activity"]
            for r in rows:
                item_ref = f" {r.item_type}" + (f"/{r.item_id}" if r.item_id else "")
                parts.append(f"- {r.action}{item_ref} by {r.decision_by} @ {r.created_at}")

            return "\n".join(parts)
    except Exception as e:
        log.debug("activity_section_failed: %s", e)
        return ""


def _build_agents_section() -> str:
    try:
        with get_db() as conn:
            rows = conn.execute(
                select(
                    agents.c.id, agents.c.name, agents.c.role,
                    agents.c.status, agents.c.task_description, agents.c.node_id,
                )
                .where(agents.c.status.in_(["running", "paused"]))
                .order_by(agents.c.started_at.desc())
                .limit(5)
            ).fetchall()
            if not rows:
                return ""

            parts: list[str] = [f"## Active Agents ({len(rows)})"]
            for r in rows:
                desc = f": {r.task_description[:60]}" if r.task_description else ""
                role = f" [{r.role}]" if r.role and r.role != "custom" else ""
                parts.append(f"- {r.name}{role} ({r.status}){desc}")

            return "\n".join(parts)
    except Exception as e:
        log.debug("agents_section_failed: %s", e)
        return ""
