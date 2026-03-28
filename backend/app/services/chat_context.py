"""
Build a rich system prompt with full CoCo context for chat sessions.

Aggregates data from brain.json, hub mirrors, platform tables, and queue.json
into a concise system prompt that stays under ~2000 tokens.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select, func, text

from app.config import BRAIN_JSON_PATH, QUEUE_JSON_PATH, CONFIG_JSON_PATH, HUB_DB_PATH
from app.db.session import get_db
from app.db.tables import (
    hub_projects, hub_content, hub_todos, hub_sync_state,
    nodes, agents, governance_log,
)
from app.services.json_store import read_json

log = logging.getLogger(__name__)


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

    try:
        from app.services.collaboration_context import build_knowledge_context
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
