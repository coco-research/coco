"""
Build collaboration context for agents being spawned as part of a team workflow.

Queries project_context, handoffs, and workflows tables to construct a
structured prompt section that orients the agent on shared project state,
pending handoffs, and workflow progress.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, insert, update, text

from app.db.session import get_db
from app.db.tables import (
    nodes, agents, project_context, handoffs, workflows,
    hub_content, hub_todos, todo_overrides, agent_output,
)
from app.config import HUB_DB_PATH, BRAIN_JSON_PATH, CONFIG_JSON_PATH

log = logging.getLogger(__name__)

ROLE_SECTION_MAP: dict[str, str] = {
    "product-manager": "brief",
    "project-manager": "plan",
    "developer": "implementation",
    "user-researcher": "research",
}


def _relative_time(iso_str: str | None) -> str:
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        total_seconds = int(delta.total_seconds())
        if total_seconds < 60:
            return "just now"
        if total_seconds < 3600:
            return f"{total_seconds // 60}m ago"
        if total_seconds < 86400:
            return f"{total_seconds // 3600}h ago"
        return f"{total_seconds // 86400}d ago"
    except Exception:
        return ""


def build_collaboration_prompt(node_id: str, agent_role: str) -> str:
    try:
        with get_db() as conn:
            context_rows = _query_project_context(conn, node_id)
            handoff = _query_pending_handoff(conn, node_id, agent_role)
            workflow = _query_active_workflow(conn, node_id)
            team = _query_team(conn, node_id)
    except Exception as e:
        log.debug("collaboration_context_failed: %s", e)
        return ""

    if not context_rows and not handoff:
        return ""

    sections: list[str] = ["== TEAM COLLABORATION CONTEXT =="]

    if team:
        sections.append("")
        sections.append("Your team members:")
        for member in team:
            role_label = member["role"].replace("-", " ").title() if member["role"] else "Custom"
            sections.append(f"- {role_label}: {member['name']}")

    if context_rows:
        sections.append("")
        sections.append("Shared Project Document:")
        for row in context_rows:
            author = row["author_role"] or "unknown"
            time_ago = _relative_time(row["created_at"])
            label = row["section"] or "note"
            time_str = f" -- {time_ago}" if time_ago else ""
            sections.append(f"[{label.title()} by {author.replace('-', ' ').title()}{time_str}]")
            content = (row["content"] or "")[:800]
            if len(row["content"] or "") > 800:
                content += "\n... (truncated)"
            sections.append(content)
            sections.append("")

    if handoff:
        sections.append("Current Handoff to You:")
        sections.append(f"Title: {handoff['title']}")
        sections.append(f"From: {(handoff['from_role'] or 'unknown').replace('-', ' ').title()}")
        if handoff.get("description"):
            sections.append(f"Description: {handoff['description']}")
        sections.append("")

    if workflow:
        try:
            steps = json.loads(workflow["steps"]) if workflow["steps"] else []
            total = len(steps)
            current = (workflow["current_step"] or 0)
            template = workflow.get("template_name") or "Custom"
            objective = workflow.get("objective") or ""
            sections.append(f"Workflow: {template} -- Step {current + 1}/{total}")
            if objective:
                sections.append(f"Objective: {objective}")
            sections.append("")
        except (json.JSONDecodeError, TypeError):
            pass

    sections.append("INSTRUCTIONS:")
    sections.append("- Read the project context above before starting")
    sections.append("- Your output will be saved and shared with the team")
    sections.append("- Focus on your role's responsibilities")
    sections.append("- Be specific and actionable -- the next team member needs to act on your output")

    return "\n".join(sections)


TOKEN_BUDGET_CHARS = 8000


def build_coco_context(node_id: str) -> str:
    try:
        brain = json.loads(BRAIN_JSON_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        log.debug("brain_json_read_failed: %s", e)
        return ""

    people: dict = brain.get("people", {})
    rules: list = brain.get("attention_rules", [])
    if not people and not rules:
        return ""

    project_id: str | None = None
    try:
        with get_db() as conn:
            row = conn.execute(
                select(nodes.c.hub_project_id).where(nodes.c.id == node_id)
            ).fetchone()
            if row and row.hub_project_id:
                project_id = row.hub_project_id
    except Exception:
        pass

    filtered_people: list[tuple[str, dict]] = []
    for key, person in people.items():
        person_projects = person.get("projects", [])
        if project_id and project_id in person_projects:
            filtered_people.append((key, person))
        elif not project_id:
            if person.get("priority") == "high":
                filtered_people.append((key, person))

    filtered_rules: list[dict] = []
    for rule in rules:
        target = rule.get("target_project")
        if project_id and target == project_id:
            filtered_rules.append(rule)
        elif not project_id:
            if not target:
                filtered_rules.append(rule)

    if not filtered_people and not filtered_rules:
        return ""

    parts: list[str] = ["## Team Context (from CoCo Brain)"]

    if filtered_people:
        parts.append("")
        parts.append("### Key People")
        for key, person in filtered_people:
            name = person.get("full_name", key)
            role = person.get("role", "unknown")
            projects_str = ", ".join(person.get("projects", []))
            topics = ", ".join(person.get("patterns", {}).get("typical_topics", []))
            line = f"- {name} ({role})"
            if topics:
                line += f" -- topics: {topics}"
            parts.append(line)
            if projects_str:
                parts.append(f"  Projects: {projects_str}")

    if filtered_rules:
        parts.append("")
        parts.append("### Attention Rules")
        for rule in filtered_rules:
            reason = rule.get("reason", "")
            action = rule.get("action", "unknown")
            parts.append(f"- {reason} (action: {action})")

    result = "\n".join(parts)
    if len(result) > TOKEN_BUDGET_CHARS:
        result = result[:TOKEN_BUDGET_CHARS] + "\n... (truncated)"

    return result


def build_yolo_constraints(project_id: str | None = None) -> str:
    try:
        config = json.loads(CONFIG_JSON_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        log.debug("config_json_read_failed: %s", e)
        return ""

    if config.get("autonomy_mode") != "yolo":
        return ""

    profile = config.get("yolo_profile", "triage")
    profiles_map = config.get("yolo", {}).get("profiles", {})
    profile_info = profiles_map.get(profile, {})
    profile_description = profile_info.get("description", profile)

    if profile == "triage":
        safe = "read, search, classify, gather information"
        escalate = "create, update, delete, modify any data"
    elif profile == "pm":
        safe = "read, search, classify, create todos, approve drafts, update brain"
        escalate = "delete, modify agents, create Jira tickets, external comms"
    elif profile == "full":
        safe = "read, search, classify, create, update, approve drafts, update brain, update Confluence"
        escalate = "create Jira tickets, external comms, git push, destructive operations"
    else:
        safe = "read, search"
        escalate = "all write operations"

    parts = [
        f"## Autonomy Mode: YOLO ({profile})",
        "",
        "You have elevated permissions for this session. Guidelines:",
        f"- **Safe actions** (do without asking): {safe}",
        f"- **Escalate** (ask before doing): {escalate}",
        "- **Never** (always blocked): delete production data, push to main without review, modify auth/credentials",
        "",
        f"Profile: {profile_description}",
    ]

    return "\n".join(parts)


def build_knowledge_context(
    node_id: str | None = None,
    project_id: str | None = None,
    token_budget: int = 2000,
) -> str:
    char_budget = token_budget * 4
    sections: list[str] = []
    used = 0

    if not project_id and node_id:
        try:
            with get_db() as conn:
                row = conn.execute(
                    select(nodes.c.hub_project_id).where(nodes.c.id == node_id)
                ).fetchone()
                if row and row.hub_project_id:
                    project_id = row.hub_project_id
        except Exception:
            pass

    if not project_id:
        return ""

    try:
        with get_db() as conn:
            # 1. Recent emails
            try:
                emails = conn.execute(
                    select(hub_content.c.title, hub_content.c.summary, hub_content.c.source, hub_content.c.created_at)
                    .where(hub_content.c.source.in_(["email", "outlook"]))
                    .where(hub_content.c.created_at >= text("datetime('now', '-7 days')"))
                    .order_by(hub_content.c.created_at.desc())
                    .limit(5)
                ).fetchall()

                if emails:
                    email_lines = ["Recent emails:"]
                    for e in emails:
                        line = f"- {e.title or 'Untitled'}"
                        if e.summary:
                            line += f": {e.summary[:100]}"
                        email_lines.append(line)
                    block = "\n".join(email_lines)
                    if used + len(block) < char_budget:
                        sections.append(block)
                        used += len(block)
            except Exception:
                pass

            # 2. Recent Jira updates
            try:
                jira_items = conn.execute(
                    select(hub_content.c.title, hub_content.c.summary, hub_content.c.source, hub_content.c.created_at)
                    .where(hub_content.c.source.in_(["jira", "jira_ticket"]))
                    .where(hub_content.c.created_at >= text("datetime('now', '-7 days')"))
                    .order_by(hub_content.c.created_at.desc())
                    .limit(5)
                ).fetchall()

                if jira_items:
                    jira_lines = ["Recent Jira updates:"]
                    for j in jira_items:
                        line = f"- {j.title or 'Untitled'}"
                        if j.summary:
                            line += f": {j.summary[:100]}"
                        jira_lines.append(line)
                    block = "\n".join(jira_lines)
                    if used + len(block) < char_budget:
                        sections.append(block)
                        used += len(block)
            except Exception:
                pass

            # 3. Active action items / todos
            try:
                todos = conn.execute(
                    select(hub_todos.c.title, hub_todos.c.priority, hub_todos.c.due_date, hub_todos.c.status)
                    .where(hub_todos.c.project_id == project_id)
                    .where(hub_todos.c.status == "open")
                    .order_by(hub_todos.c.priority.asc())
                    .limit(5)
                ).fetchall()

                if todos:
                    todo_lines = ["Active action items:"]
                    for t in todos:
                        line = f"- [{t.priority or 'medium'}] {t.title}"
                        if t.due_date:
                            line += f" (due: {t.due_date})"
                        todo_lines.append(line)
                    block = "\n".join(todo_lines)
                    if used + len(block) < char_budget:
                        sections.append(block)
                        used += len(block)
            except Exception:
                pass

            # 4. General recent content
            try:
                recent = conn.execute(
                    select(hub_content.c.title, hub_content.c.source, hub_content.c.created_at)
                    .where(hub_content.c.source.notin_(["email", "outlook", "jira", "jira_ticket"]))
                    .order_by(hub_content.c.created_at.desc())
                    .limit(3)
                ).fetchall()

                if recent:
                    recent_lines = ["Other recent content:"]
                    for r in recent:
                        recent_lines.append(f"- [{r.source or 'unknown'}] {r.title or 'Untitled'}")
                    block = "\n".join(recent_lines)
                    if used + len(block) < char_budget:
                        sections.append(block)
                        used += len(block)
            except Exception:
                pass

    except Exception as e:
        log.debug("build_knowledge_context_failed: %s", e)
        return ""

    if not sections:
        return ""

    header = f"== KNOWLEDGE CONTEXT (project: {project_id}) =="
    return header + "\n\n" + "\n\n".join(sections)


def extract_action_items_from_text(text_content: str) -> list[str]:
    """Extract action items from agent output or content text."""
    items: list[str] = []
    seen: set[str] = set()

    explicit_patterns = [
        r"^TODO:\s*(.+)",
        r"^ACTION:\s*(.+)",
        r"^FOLLOW\s*UP:\s*(.+)",
        r"^-\s*\[\s*\]\s*(.+)",
        r"^NEXT\s*STEP:\s*(.+)",
        r"^ACTION\s*ITEM:\s*(.+)",
        r"^Assigned\s+to\s+\w+:\s*(.+)",
    ]

    imperative_patterns = [
        r"(?:we |I |you |they |he |she )?need(?:s)?\s+to\s+(.{10,})",
        r"(?:we |I |you |they |he |she )?should\s+(.{10,})",
        r"(?:we |I |you |they |he |she )?must\s+(.{10,})",
        r"follow\s+up\s+(?:on|with|about)\s+(.{10,})",
        r"(?:please\s+)?schedule\s+(.{10,})",
        r"(?:please\s+)?send\s+(.{10,})",
        r"(?:please\s+)?prepare\s+(.{10,})",
        r"(?:please\s+)?review\s+(.{10,})",
        r"(?:please\s+)?draft\s+(.{10,})",
        r"(?:please\s+)?set\s+up\s+(.{10,})",
        r"(?:please\s+)?create\s+(.{10,})",
        r"(?:please\s+)?update\s+(.{10,})",
        r"(?:please\s+)?confirm\s+(.{10,})",
        r"(?:please\s+)?coordinate\s+with\s+(.{10,})",
        r"@(\w+)\s+(.{10,})",
    ]

    for line in text_content.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) < 5:
            continue

        for pattern in explicit_patterns:
            m = re.match(pattern, stripped, re.IGNORECASE)
            if m:
                desc = m.group(1).strip().rstrip(".")
                if desc and len(desc) > 3:
                    key = desc.lower()[:50]
                    if key not in seen:
                        seen.add(key)
                        items.append(desc[:200])
                break
        else:
            for pattern in imperative_patterns:
                m = re.search(pattern, stripped, re.IGNORECASE)
                if m:
                    if pattern.startswith(r"@"):
                        owner = m.group(1)
                        desc = f"@{owner}: {m.group(2).strip().rstrip('.')}"
                    else:
                        desc = m.group(1).strip().rstrip(".")
                    for sep in [". ", "; ", " - ", "\t"]:
                        if sep in desc:
                            desc = desc[: desc.index(sep)]
                            break
                    if desc and len(desc) > 5:
                        key = desc.lower()[:50]
                        if key not in seen:
                            seen.add(key)
                            items.append(desc[:200])
                    break

    return items


def extract_due_date(text_content: str) -> str | None:
    text_lower = text_content.lower()

    abs_match = re.search(
        r"(?:by|due|before|until)\s+(\w+\s+\d{1,2}(?:,?\s*\d{4})?)",
        text_lower,
    )
    if abs_match:
        return abs_match.group(1).strip()

    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", text_content)
    if iso_match:
        return iso_match.group(1)

    relative_patterns = {
        r"\bASAP\b": "ASAP",
        r"\bby\s+EOD\b": "end of day",
        r"\bby\s+end\s+of\s+day\b": "end of day",
        r"\bby\s+end\s+of\s+week\b": "end of week",
        r"\bthis\s+week\b": "this week",
        r"\bnext\s+week\b": "next week",
        r"\bby\s+Friday\b": "Friday",
        r"\bby\s+Monday\b": "next Monday",
        r"\bby\s+tomorrow\b": "tomorrow",
        r"\bby\s+tonight\b": "tonight",
    }
    for pattern, label in relative_patterns.items():
        if re.search(pattern, text_content, re.IGNORECASE):
            return label

    return None


def extract_owner(text_content: str) -> str | None:
    m = re.search(r"@(\w+)", text_content)
    if m:
        return m.group(1)

    m = re.search(r"Assigned\s+to\s+(\w+)", text_content, re.IGNORECASE)
    if m:
        return m.group(1)

    m = re.match(r"(\w+)\s+needs?\s+to\b", text_content.strip())
    if m:
        name = m.group(1)
        if name.lower() not in {"we", "i", "you", "they", "he", "she", "it", "someone", "team"}:
            return name

    return None


def create_platform_todos_from_text(
    text_content: str, source_content_id: str | None = None, project_id: str | None = None
) -> list[dict]:
    items = extract_action_items_from_text(text_content)
    if not items:
        return []

    created = []
    try:
        with get_db() as conn:
            for desc in items:
                todo_id = str(uuid.uuid4())
                owner = extract_owner(desc)
                due_hint = extract_due_date(desc)

                conn.execute(
                    text(
                        "INSERT INTO todo_overrides "
                        "(hub_todo_id, title, status, priority, owner, due_date, "
                        "project_id, source_type, source_content_id, "
                        "is_platform_native, created_at) "
                        "VALUES (:id, :title, 'open', 'medium', :owner, :due, "
                        ":project_id, 'extracted', :source_cid, 1, datetime('now'))"
                    ),
                    {
                        "id": todo_id, "title": desc, "owner": owner, "due": due_hint,
                        "project_id": project_id, "source_cid": source_content_id,
                    },
                )
                created.append({
                    "id": todo_id,
                    "title": desc,
                    "owner": owner,
                    "due_hint": due_hint,
                })
    except Exception as e:
        log.warning("create_platform_todos_failed: %s", e)

    return created


def _create_todos_from_agent_output(
    output_text: str, agent_id: str, node_id: str
) -> int:
    project_id = None
    try:
        with get_db() as conn:
            row = conn.execute(
                select(nodes.c.hub_project_id).where(nodes.c.id == node_id)
            ).fetchone()
            if row and row.hub_project_id:
                project_id = row.hub_project_id
    except Exception:
        pass

    source_key = f"agent:{agent_id}"
    created_items = create_platform_todos_from_text(
        output_text, source_content_id=source_key, project_id=project_id
    )
    count = len(created_items)

    if count:
        log.info("agent_todos_created", extra={
            "agent_id": agent_id, "node_id": node_id, "count": count
        })
    return count


def auto_capture_output(agent_id: str, agent_role: str, node_id: str | None) -> None:
    if not node_id:
        return

    try:
        with get_db() as conn:
            output_rows = conn.execute(
                select(agent_output.c.chunk)
                .where(agent_output.c.agent_id == agent_id)
                .order_by(agent_output.c.id.desc())
                .limit(50)
            ).fetchall()

            if not output_rows:
                return

            output_text = "\n".join(r.chunk for r in reversed(output_rows))

            section_name = ROLE_SECTION_MAP.get(agent_role, "output")

            try:
                conn.execute(
                    insert(project_context).values(
                        id=str(uuid.uuid4()), node_id=node_id, section=section_name,
                        content=output_text, author_agent_id=agent_id, author_role=agent_role,
                    )
                )
                log.info("auto_captured_output", extra={
                    "agent_id": agent_id, "node_id": node_id, "section": section_name
                })
            except Exception as e:
                log.debug("project_context_insert_failed: %s", e)

            try:
                _create_todos_from_agent_output(output_text, agent_id, node_id)
            except Exception as e:
                log.warning("agent_todo_extraction_failed: %s", e)

            _advance_workflow(conn, agent_id, agent_role, node_id)

    except Exception as e:
        log.warning("auto_capture_output_failed: %s", e)


# ---------------------------------------------------------------------------
# Internal query helpers
# ---------------------------------------------------------------------------


def _query_project_context(conn, node_id: str) -> list:
    try:
        rows = conn.execute(
            select(
                project_context.c.section,
                project_context.c.content,
                project_context.c.author_role,
                project_context.c.created_at,
            )
            .where(project_context.c.node_id == node_id)
            .order_by(project_context.c.created_at.asc())
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception:
        return []


def _query_pending_handoff(conn, node_id: str, agent_role: str) -> dict | None:
    try:
        row = conn.execute(
            select(
                handoffs.c.title, handoffs.c.from_role, handoffs.c.to_role,
                handoffs.c.description, handoffs.c.status,
            )
            .where(handoffs.c.node_id == node_id)
            .where(handoffs.c.to_role == agent_role)
            .where(handoffs.c.status == "pending")
            .order_by(handoffs.c.created_at.desc())
            .limit(1)
        ).fetchone()
        return dict(row._mapping) if row else None
    except Exception:
        return None


def _query_active_workflow(conn, node_id: str) -> dict | None:
    try:
        row = conn.execute(
            select(
                workflows.c.id, workflows.c.template_name, workflows.c.objective,
                workflows.c.steps, workflows.c.current_step, workflows.c.status,
            )
            .where(workflows.c.node_id == node_id)
            .where(workflows.c.status == "active")
            .limit(1)
        ).fetchone()
        return dict(row._mapping) if row else None
    except Exception:
        return None


def _query_team(conn, node_id: str) -> list:
    try:
        rows = conn.execute(
            select(agents.c.name, agents.c.role, agents.c.status)
            .where(agents.c.node_id == node_id)
            .order_by(agents.c.created_at.asc())
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception:
        return []


def _advance_workflow(conn, agent_id: str, agent_role: str, node_id: str) -> None:
    try:
        workflow = conn.execute(
            select(workflows)
            .where(workflows.c.node_id == node_id)
            .where(workflows.c.status == "active")
            .limit(1)
        ).fetchone()
    except Exception:
        return

    if not workflow:
        return

    try:
        steps = json.loads(workflow.steps) if workflow.steps else []
        current = workflow.current_step or 0
        current_step = steps[current] if current < len(steps) else None

        if not current_step or current_step.get("role") != agent_role:
            return

        conn.execute(
            update(handoffs)
            .where(handoffs.c.node_id == node_id)
            .where(handoffs.c.to_role == agent_role)
            .where(handoffs.c.status == "in_progress")
            .values(status="completed", completed_at=text("datetime('now')"))
        )

        next_step = current + 1
        if next_step < len(steps):
            next_role = steps[next_step]["role"]
            action_label = steps[next_step].get("action", "continue").replace("_", " ").title()
            conn.execute(
                insert(handoffs).values(
                    id=str(uuid.uuid4()),
                    node_id=node_id,
                    workflow_id=workflow.id,
                    from_agent_id=agent_id,
                    from_role=agent_role,
                    to_role=next_role,
                    title=f"{action_label} -- from {agent_role.replace('-', ' ').title()}",
                    status="pending",
                )
            )
            conn.execute(
                update(workflows)
                .where(workflows.c.id == workflow.id)
                .values(current_step=next_step, updated_at=text("datetime('now')"))
            )
        else:
            conn.execute(
                update(workflows)
                .where(workflows.c.id == workflow.id)
                .values(status="completed", updated_at=text("datetime('now')"))
            )

        log.info("workflow_advanced", extra={
            "workflow_id": workflow.id, "from_step": current,
            "next_step": next_step if next_step < len(steps) else "complete"
        })
    except (json.JSONDecodeError, IndexError, KeyError, TypeError) as e:
        log.debug("advance_workflow_failed: %s", e)
    except Exception as e:
        log.warning("advance_workflow_error: %s", e)
