"""
Build a rich system prompt with full CoCo context for chat sessions.

Aggregates data from brain.json, hub.db, platform.db, and queue.json
into a concise system prompt that stays under ~2000 tokens.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.config import BRAIN_JSON_PATH, QUEUE_JSON_PATH, CONFIG_JSON_PATH, HUB_DB_PATH
from app.db.connections import get_hub_db, get_platform_db
from app.services.json_store import read_json

log = logging.getLogger(__name__)


def build_chat_context(
    project_id: str | None = None,
    node_id: str | None = None,
) -> str:
    """Build a system prompt with full CoCo context for chat.

    Assembles identity, date, brain, projects, tree, queue, recent activity,
    and active agents into a structured prompt. Keeps output concise.
    """
    sections: list[str] = []

    # 1. Identity
    sections.append(
        "You are CoCo, Rijul's AI assistant. You have access to his "
        "Knowledge Hub, brain, and project data. Be concise and helpful."
    )

    # 2. Current date/time
    now = datetime.now(timezone.utc)
    sections.append(f"Current date/time: {now.strftime('%Y-%m-%d %H:%M UTC')} ({now.strftime('%A')})")

    # 3. Brain context
    brain_section = _build_brain_section()
    if brain_section:
        sections.append(brain_section)

    # 4. Projects overview
    projects_section = _build_projects_section(project_id)
    if projects_section:
        sections.append(projects_section)

    # 5. Tree context (org hierarchy)
    tree_section = _build_tree_section(node_id)
    if tree_section:
        sections.append(tree_section)

    # 6. Queue summary
    queue_section = _build_queue_section()
    if queue_section:
        sections.append(queue_section)

    # 7. Recent activity
    activity_section = _build_activity_section()
    if activity_section:
        sections.append(activity_section)

    # 8. Active agents
    agents_section = _build_agents_section()
    if agents_section:
        sections.append(agents_section)

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _build_brain_section() -> str:
    """Brain context from brain.json: people, rules, stats."""
    try:
        brain = read_json(BRAIN_JSON_PATH)
        if not brain:
            return ""
    except Exception:
        return ""

    parts: list[str] = ["## Brain"]

    # People summary — people can be a dict keyed by name or a list of dicts
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

    # Attention rules summary
    rules = brain.get("rules", [])
    if rules:
        parts.append(f"Attention rules: {len(rules)} active")

    # Stats
    stats = brain.get("stats", {})
    if stats:
        stat_items = [f"{k}={v}" for k, v in list(stats.items())[:5]]
        parts.append(f"Stats: {', '.join(stat_items)}")

    return "\n".join(parts) if len(parts) > 1 else ""


def _build_projects_section(focused_project_id: str | None) -> str:
    """Projects overview from hub.db, with detail for the focused project."""
    if not HUB_DB_PATH.exists():
        return ""

    try:
        with get_hub_db() as db:
            # All projects with item counts
            rows = db.execute(
                "SELECT p.id, p.name, COUNT(c.id) AS item_count "
                "FROM projects p "
                "LEFT JOIN content c ON c.project_id = p.id "
                "GROUP BY p.id, p.name "
                "ORDER BY item_count DESC "
                "LIMIT 15"
            ).fetchall()

            if not rows:
                return ""

            parts: list[str] = ["## Projects"]
            lines = [f"- {r['name']} ({r['item_count']} items)" for r in rows]
            parts.append("\n".join(lines))

            # Focused project detail
            if focused_project_id:
                detail = _build_focused_project(db, focused_project_id)
                if detail:
                    parts.append(detail)

            return "\n".join(parts)
    except Exception as e:
        log.debug("projects_section_failed: %s", e)
        return ""


def _build_focused_project(db, project_id: str) -> str:
    """Detailed context for a specific focused project."""
    try:
        project = db.execute(
            "SELECT id, name FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if not project:
            return ""

        parts: list[str] = [f"\nFocused project: {project['name']}"]

        # Recent content items
        recent = db.execute(
            "SELECT title, content_type, created_at "
            "FROM content "
            "WHERE project_id = ? "
            "ORDER BY created_at DESC "
            "LIMIT 5",
            (project_id,),
        ).fetchall()
        if recent:
            parts.append("Recent items:")
            for r in recent:
                parts.append(f"  - [{r['content_type']}] {r['title']}")

        return "\n".join(parts)
    except Exception:
        return ""


def _build_tree_section(node_id: str | None) -> str:
    """Org hierarchy from the nodes table in platform.db."""
    try:
        with get_platform_db() as db:
            # Top-level summary: count groups and teams
            summary = db.execute(
                "SELECT node_type, COUNT(*) AS cnt FROM nodes GROUP BY node_type"
            ).fetchall()
            if not summary:
                return ""

            type_counts = {r["node_type"]: r["cnt"] for r in summary}
            parts: list[str] = [
                "## Org Tree",
                f"Nodes: {', '.join(f'{cnt} {t}s' for t, cnt in type_counts.items())}",
            ]

            # If node_id provided, show that subtree
            if node_id:
                node = db.execute(
                    "SELECT id, label, node_type, path FROM nodes WHERE id = ?",
                    (node_id,),
                ).fetchone()
                if node:
                    parts.append(f"Current node: {node['label']} ({node['node_type']})")
                    # Children
                    children = db.execute(
                        "SELECT label, node_type FROM nodes "
                        "WHERE parent_id = ? ORDER BY sort_order LIMIT 10",
                        (node_id,),
                    ).fetchall()
                    if children:
                        parts.append("Children: " + ", ".join(
                            f"{c['label']} ({c['node_type']})" for c in children
                        ))

            return "\n".join(parts)
    except Exception as e:
        log.debug("tree_section_failed: %s", e)
        return ""


def _build_queue_section() -> str:
    """Queue summary from queue.json."""
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
    """Last 5 governance actions from platform.db."""
    try:
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT action, item_type, item_id, decision_by, created_at "
                "FROM governance_log "
                "ORDER BY created_at DESC "
                "LIMIT 5"
            ).fetchall()
            if not rows:
                return ""

            parts: list[str] = ["## Recent Activity"]
            for r in rows:
                item_ref = f" {r['item_type']}" + (f"/{r['item_id']}" if r["item_id"] else "")
                parts.append(f"- {r['action']}{item_ref} by {r['decision_by']} @ {r['created_at']}")

            return "\n".join(parts)
    except Exception as e:
        log.debug("activity_section_failed: %s", e)
        return ""


def _build_agents_section() -> str:
    """List running/active agents from platform.db."""
    try:
        with get_platform_db() as db:
            rows = db.execute(
                "SELECT id, name, role, status, task_description, node_id "
                "FROM agents "
                "WHERE status IN ('running', 'paused') "
                "ORDER BY started_at DESC "
                "LIMIT 5"
            ).fetchall()
            if not rows:
                return ""

            parts: list[str] = [f"## Active Agents ({len(rows)})"]
            for r in rows:
                desc = f": {r['task_description'][:60]}" if r["task_description"] else ""
                role = f" [{r['role']}]" if r["role"] and r["role"] != "custom" else ""
                parts.append(f"- {r['name']}{role} ({r['status']}){desc}")

            return "\n".join(parts)
    except Exception as e:
        log.debug("agents_section_failed: %s", e)
        return ""
