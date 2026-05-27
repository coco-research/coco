"""Unified search across all entities for the Cmd+K command palette.

GET /api/search?q=...&types=todos,agents,projects,content,decisions,people&limit=20

Returns a flat list of result rows: [{type, id, human_id, title, snippet, score}].

- `type`: one of todo, agent, project, content, decision, person, task, goal, draft.
- `id`: opaque domain id (matches the detail page route).
- `human_id`: short display id (e.g. CXR-47) where available, else None.
- `title`: primary label shown in the palette.
- `snippet`: short context line (often `status - role`, FTS snippet for content, etc.).
- `score`: relative score for cross-domain ranking. Higher is better.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from typing import Iterable

from fastapi import APIRouter, Query
from sqlalchemy import outerjoin, select, text

from app.config import BRAIN_DB_PATH, BRAIN_JSON_PATH
from app.db.session import get_db
from app.db.tables import (
    agents,
    entity_identifiers,
    goals,
    hub_content,
    hub_drafts,
    hub_projects,
    hub_todos,
    tasks,
    todo_overrides,
)
from app.services.json_store import read_json

log = logging.getLogger(__name__)

router = APIRouter(tags=["Search"])


# All types known to the unified search. Frontend may request a subset via the
# `types` query param (comma-separated). Aliases map plural URL labels to the
# singular result `type` field.
_TYPE_ALIASES: dict[str, str] = {
    "todos": "todo",
    "todo": "todo",
    "agents": "agent",
    "agent": "agent",
    "projects": "project",
    "project": "project",
    "content": "content",
    "decisions": "decision",
    "decision": "decision",
    "people": "person",
    "person": "person",
    "tasks": "task",
    "task": "task",
    "goals": "goal",
    "goal": "goal",
    "drafts": "draft",
    "draft": "draft",
}

# Default set when no `types` filter is supplied.
_DEFAULT_TYPES = {
    "todo", "agent", "project", "content",
    "decision", "person", "task", "goal", "draft",
}


def _parse_types(raw: str | None) -> set[str]:
    if not raw:
        return set(_DEFAULT_TYPES)
    requested: set[str] = set()
    for tok in raw.split(","):
        key = tok.strip().lower()
        if not key:
            continue
        mapped = _TYPE_ALIASES.get(key)
        if mapped:
            requested.add(mapped)
    return requested or set(_DEFAULT_TYPES)


def _truncate(value: str | None, limit: int = 140) -> str:
    if not value:
        return ""
    s = str(value).strip()
    if len(s) <= limit:
        return s
    return s[: limit - 1].rstrip() + "…"


# Per-type base scores: agents/decisions feel higher-signal than raw content rows
# when titles tie. Prefix-match adds +2, exact-match adds +4, FTS rank adds float.
_BASE_SCORE: dict[str, float] = {
    "todo": 6.0,
    "agent": 7.0,
    "task": 5.5,
    "goal": 5.5,
    "project": 6.5,
    "decision": 6.0,
    "person": 6.0,
    "content": 4.0,
    "draft": 4.5,
}


def _title_score(title: str | None, q_lower: str) -> float:
    if not title:
        return 0.0
    t = title.lower()
    if t == q_lower:
        return 4.0
    if t.startswith(q_lower):
        return 2.0
    if q_lower in t:
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# Per-domain search helpers — each appends rows to `out`.
# ---------------------------------------------------------------------------

def _search_todos(conn, pattern: str, q_lower: str, limit: int, out: list[dict]) -> None:
    """Search both hub_todos (mirror) and platform-native todo_overrides."""
    seen: set[str] = set()

    # Hub todos
    try:
        rows = conn.execute(
            select(hub_todos.c.id, hub_todos.c.title, hub_todos.c.status, hub_todos.c.priority)
            .where(hub_todos.c.title.like(pattern))
            .limit(limit)
        ).fetchall()
        display_ids = _fetch_display_ids(conn, "todo", [r.id for r in rows])
        for r in rows:
            seen.add(r.id)
            title = r.title or "(untitled)"
            snippet = f"Status: {r.status or 'open'}"
            if r.priority:
                snippet += f" - {r.priority}"
            out.append({
                "type": "todo",
                "id": r.id,
                "human_id": display_ids.get(r.id),
                "title": title,
                "snippet": snippet,
                "score": _BASE_SCORE["todo"] + _title_score(title, q_lower),
                # Legacy fields the frontend already reads.
                "display_id": display_ids.get(r.id),
                "subtitle": snippet,
                "url": "/todos",
            })
    except Exception as e:
        log.warning("search_hub_todos_failed: %s", e)

    # Platform-native todos (overrides marked is_platform_native=1)
    try:
        j = outerjoin(
            todo_overrides, entity_identifiers,
            (entity_identifiers.c.entity_id == todo_overrides.c.hub_todo_id)
            & (entity_identifiers.c.entity_type == "todo"),
        )
        rows = conn.execute(
            select(
                todo_overrides.c.hub_todo_id,
                todo_overrides.c.title,
                todo_overrides.c.status,
                todo_overrides.c.priority,
                entity_identifiers.c.display_id,
            )
            .select_from(j)
            .where(todo_overrides.c.is_platform_native == 1)
            .where(todo_overrides.c.title.like(pattern))
            .limit(limit)
        ).fetchall()
        for r in rows:
            if r.hub_todo_id in seen:
                continue
            title = r.title or "(untitled)"
            snippet = f"Status: {r.status or 'open'}"
            if r.priority:
                snippet += f" - {r.priority}"
            out.append({
                "type": "todo",
                "id": r.hub_todo_id,
                "human_id": r.display_id,
                "title": title,
                "snippet": snippet,
                "score": _BASE_SCORE["todo"] + _title_score(title, q_lower),
                "display_id": r.display_id,
                "subtitle": snippet,
                "url": "/todos",
            })
    except Exception as e:
        log.warning("search_platform_todos_failed: %s", e)


def _search_agents(conn, pattern: str, q_lower: str, limit: int, out: list[dict]) -> None:
    try:
        j = outerjoin(
            agents, entity_identifiers,
            (entity_identifiers.c.entity_id == agents.c.id)
            & (entity_identifiers.c.entity_type == "agent"),
        )
        rows = conn.execute(
            select(
                agents.c.id, agents.c.name, agents.c.status, agents.c.role,
                entity_identifiers.c.display_id,
            )
            .select_from(j)
            .where(agents.c.name.like(pattern))
            .limit(limit)
        ).fetchall()
        for r in rows:
            parts = [p for p in (r.role, r.status) if p]
            snippet = " - ".join(parts) or "Agent"
            title = r.name or "(unnamed)"
            out.append({
                "type": "agent",
                "id": r.id,
                "human_id": r.display_id,
                "title": title,
                "snippet": snippet,
                "score": _BASE_SCORE["agent"] + _title_score(title, q_lower),
                "display_id": r.display_id,
                "subtitle": snippet,
                "url": f"/agents/{r.id}",
            })
    except Exception as e:
        log.warning("search_agents_failed: %s", e)


def _search_tasks(conn, pattern: str, q_lower: str, limit: int, out: list[dict]) -> None:
    try:
        j = outerjoin(
            tasks, entity_identifiers,
            (entity_identifiers.c.entity_id == tasks.c.id)
            & (entity_identifiers.c.entity_type == "task"),
        )
        rows = conn.execute(
            select(
                tasks.c.id, tasks.c.title, tasks.c.status, tasks.c.priority,
                entity_identifiers.c.display_id,
            )
            .select_from(j)
            .where(tasks.c.title.like(pattern))
            .limit(limit)
        ).fetchall()
        for r in rows:
            parts = [p for p in (r.status, r.priority) if p]
            snippet = " - ".join(parts) or "Task"
            title = r.title or "(untitled)"
            out.append({
                "type": "task",
                "id": r.id,
                "human_id": r.display_id,
                "title": title,
                "snippet": snippet,
                "score": _BASE_SCORE["task"] + _title_score(title, q_lower),
                "display_id": r.display_id,
                "subtitle": snippet,
                "url": "/tasks",
            })
    except Exception as e:
        log.warning("search_tasks_failed: %s", e)


def _search_goals(conn, pattern: str, q_lower: str, limit: int, out: list[dict]) -> None:
    try:
        j = outerjoin(
            goals, entity_identifiers,
            (entity_identifiers.c.entity_id == goals.c.id)
            & (entity_identifiers.c.entity_type == "goal"),
        )
        rows = conn.execute(
            select(
                goals.c.id, goals.c.title, goals.c.status, goals.c.progress_pct,
                entity_identifiers.c.display_id,
            )
            .select_from(j)
            .where(goals.c.title.like(pattern))
            .limit(limit)
        ).fetchall()
        for r in rows:
            snippet = r.status or "active"
            if r.progress_pct is not None:
                snippet += f" - {r.progress_pct}%"
            title = r.title or "(untitled)"
            out.append({
                "type": "goal",
                "id": r.id,
                "human_id": r.display_id,
                "title": title,
                "snippet": snippet,
                "score": _BASE_SCORE["goal"] + _title_score(title, q_lower),
                "display_id": r.display_id,
                "subtitle": snippet,
                "url": "/goals",
            })
    except Exception as e:
        log.warning("search_goals_failed: %s", e)


def _search_projects(conn, pattern: str, q_lower: str, limit: int, out: list[dict]) -> None:
    """Search hub_projects (read-only mirror)."""
    try:
        rows = conn.execute(
            select(
                hub_projects.c.id, hub_projects.c.name,
                hub_projects.c.jira_key, hub_projects.c.confluence_space,
                hub_projects.c.active,
            )
            .where(hub_projects.c.name.like(pattern))
            .where(hub_projects.c.active == 1)
            .limit(limit)
        ).fetchall()
        for r in rows:
            parts = []
            if r.jira_key:
                parts.append(f"Jira: {r.jira_key}")
            if r.confluence_space:
                parts.append(f"Confluence: {r.confluence_space}")
            snippet = " - ".join(parts) or "Project"
            title = r.name or "(unnamed)"
            out.append({
                "type": "project",
                "id": r.id,
                "human_id": r.jira_key or None,
                "title": title,
                "snippet": snippet,
                "score": _BASE_SCORE["project"] + _title_score(title, q_lower),
                "display_id": r.jira_key or None,
                "subtitle": snippet,
                "url": f"/projects/{r.id}",
            })
    except Exception as e:
        log.warning("search_projects_failed: %s", e)


def _search_drafts(conn, pattern: str, q_lower: str, limit: int, out: list[dict]) -> None:
    """Search hub_drafts via content body LIKE — drafts have no titles."""
    try:
        rows = conn.execute(
            select(
                hub_drafts.c.id, hub_drafts.c.content,
                hub_drafts.c.template, hub_drafts.c.status,
            )
            .where(hub_drafts.c.content.like(pattern))
            .limit(limit)
        ).fetchall()
        for r in rows:
            snippet = _truncate(r.content, 120) or (r.template or "Draft")
            title = (r.template or "Draft") + (f" - {r.status}" if r.status else "")
            out.append({
                "type": "draft",
                "id": r.id,
                "human_id": None,
                "title": title,
                "snippet": snippet,
                "score": _BASE_SCORE["draft"] + (1.0 if q_lower in (snippet or "").lower() else 0.0),
                "display_id": None,
                "subtitle": snippet,
                "url": "/drafts",
            })
    except Exception as e:
        log.warning("search_drafts_failed: %s", e)


def _search_content(conn, q: str, pattern: str, q_lower: str, limit: int, out: list[dict]) -> None:
    """Search hub_content via FTS5 if available, fall back to LIKE."""
    fts_used = False
    try:
        conn.execute(text("SELECT 1 FROM hub_content_fts LIMIT 1"))
        # FTS5 is finicky about special characters — quote the user query as a
        # single phrase to avoid syntax errors on tokens like - / : etc.
        safe = _fts_quote(q)
        rows = conn.execute(
            text(
                "SELECT c.id, c.title, c.source, "
                "snippet(hub_content_fts, 1, '', '', '…', 12) AS snip, "
                "rank "
                "FROM hub_content c "
                "JOIN hub_content_fts f ON c.rowid = f.rowid "
                "WHERE hub_content_fts MATCH :q "
                "ORDER BY rank "
                "LIMIT :limit"
            ),
            {"q": safe, "limit": limit},
        ).mappings().all()
        for r in rows:
            title = r["title"] or "(untitled)"
            snippet = _truncate(r["snip"] or "", 160) or (r["source"] or "Content")
            # FTS bm25 rank: more negative = better. Scale to a positive bump.
            try:
                bonus = max(0.0, -float(r["rank"])) / 10.0
            except Exception:
                bonus = 0.0
            out.append({
                "type": "content",
                "id": r["id"],
                "human_id": None,
                "title": title,
                "snippet": snippet,
                "score": _BASE_SCORE["content"] + _title_score(title, q_lower) + bonus,
                "display_id": None,
                "subtitle": snippet,
                "url": f"/knowledge/{r['id']}",
            })
        fts_used = True
    except Exception as e:
        log.debug("search_content_fts_skipped: %s", e)

    if fts_used:
        return

    # LIKE fallback
    try:
        rows = conn.execute(
            select(hub_content.c.id, hub_content.c.title, hub_content.c.source, hub_content.c.body)
            .where((hub_content.c.title.like(pattern)) | (hub_content.c.body.like(pattern)))
            .limit(limit)
        ).fetchall()
        for r in rows:
            title = r.title or "(untitled)"
            snippet = _extract_snippet(r.body, q_lower) or (r.source or "Content")
            out.append({
                "type": "content",
                "id": r.id,
                "human_id": None,
                "title": title,
                "snippet": _truncate(snippet, 160),
                "score": _BASE_SCORE["content"] + _title_score(title, q_lower),
                "display_id": None,
                "subtitle": _truncate(snippet, 160),
                "url": f"/knowledge/{r.id}",
            })
    except Exception as e:
        log.warning("search_content_like_failed: %s", e)


def _fts_quote(q: str) -> str:
    """Escape a user query for FTS5 MATCH.

    Wrapping in double quotes makes the whole input a phrase. Embedded double
    quotes are doubled per the FTS5 spec.
    """
    return '"' + q.replace('"', '""') + '"'


def _extract_snippet(body: str | None, q_lower: str, around: int = 60) -> str:
    if not body:
        return ""
    b = body
    idx = b.lower().find(q_lower)
    if idx < 0:
        return _truncate(b, 160)
    start = max(0, idx - around)
    end = min(len(b), idx + len(q_lower) + around)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(b) else ""
    return (prefix + b[start:end] + suffix).replace("\n", " ")


def _fetch_display_ids(conn, entity_type: str, ids: Iterable[str]) -> dict[str, str]:
    ids = [i for i in ids if i]
    if not ids:
        return {}
    try:
        rows = conn.execute(
            select(entity_identifiers.c.entity_id, entity_identifiers.c.display_id)
            .where(entity_identifiers.c.entity_type == entity_type)
            .where(entity_identifiers.c.entity_id.in_(list(ids)))
        ).fetchall()
        return {r.entity_id: r.display_id for r in rows}
    except Exception as e:
        log.warning("fetch_display_ids_failed: %s", e)
        return {}


# ---------------------------------------------------------------------------
# Brain-sourced search (decisions in project_brain.db, people in brain.json).
# ---------------------------------------------------------------------------

def _brain_db_ro() -> sqlite3.Connection | None:
    """Open the project_brain.db read-only. Returns None if missing."""
    if not BRAIN_DB_PATH.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{BRAIN_DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        log.warning("brain_db_open_failed: %s", e)
        return None


def _search_decisions(q: str, q_lower: str, limit: int, out: list[dict]) -> None:
    conn = _brain_db_ro()
    if conn is None:
        return
    try:
        pattern = f"%{q}%"
        rows = conn.execute(
            "SELECT id, date, decision, context, decided_by "
            "FROM decisions "
            "WHERE project_id = 1 "
            "AND (decision LIKE ? OR context LIKE ? OR decided_by LIKE ?) "
            "ORDER BY date DESC "
            "LIMIT ?",
            (pattern, pattern, pattern, limit),
        ).fetchall()
        for r in rows:
            title = _truncate(r["decision"] or "(decision)", 100)
            parts = []
            if r["decided_by"]:
                parts.append(r["decided_by"])
            if r["date"]:
                parts.append(r["date"])
            snippet = " - ".join(parts) or _truncate(r["context"], 120) or "Decision"
            out.append({
                "type": "decision",
                "id": str(r["id"]),
                "human_id": None,
                "title": title,
                "snippet": snippet,
                "score": _BASE_SCORE["decision"] + _title_score(r["decision"], q_lower),
                "display_id": None,
                "subtitle": snippet,
                "url": "/brain",
            })
    except Exception:
        log.exception("search_decisions_failed")
    finally:
        conn.close()


def _search_people(q_lower: str, limit: int, out: list[dict]) -> None:
    try:
        brain = read_json(BRAIN_JSON_PATH)
    except Exception as e:
        log.warning("search_people_read_brain_failed: %s", e)
        return
    people = brain.get("people") or {}
    if not isinstance(people, dict):
        return
    matched = 0
    for slug, person in people.items():
        if matched >= limit:
            break
        if not isinstance(person, dict):
            continue
        name = person.get("full_name") or slug
        role = person.get("role") or ""
        haystack = f"{slug} {name} {role}".lower()
        if q_lower not in haystack:
            continue
        priority = person.get("priority")
        snippet_parts = []
        if role:
            snippet_parts.append(role)
        if priority:
            snippet_parts.append(f"priority: {priority}")
        snippet = " - ".join(snippet_parts) or "Person"
        out.append({
            "type": "person",
            "id": slug,
            "human_id": None,
            "title": name,
            "snippet": snippet,
            "score": _BASE_SCORE["person"] + _title_score(name, q_lower),
            "display_id": None,
            "subtitle": snippet,
            "url": f"/people?slug={slug}",
        })
        matched += 1


# ---------------------------------------------------------------------------
# Public endpoint
# ---------------------------------------------------------------------------

@router.get("/api/search")
def unified_search(
    q: str = Query(..., min_length=1, max_length=200),
    types: str | None = Query(None, description="Comma-separated subset of types to search"),
    limit: int = Query(20, ge=1, le=100),
):
    """Unified Cmd+K search across todos, agents, projects, content, decisions, people."""
    q_clean = q.strip()
    if not q_clean:
        return []

    q_lower = q_clean.lower()
    pattern = f"%{q_clean}%"
    wanted = _parse_types(types)
    # Per-domain cap so one domain can't crowd the others. Always fetch a bit
    # more than the global limit so cross-domain ranking has something to work
    # with, then trim at the end.
    per = max(5, min(limit, 25))

    results: list[dict] = []

    with get_db() as conn:
        if "todo" in wanted:
            _search_todos(conn, pattern, q_lower, per, results)
        if "agent" in wanted:
            _search_agents(conn, pattern, q_lower, per, results)
        if "task" in wanted:
            _search_tasks(conn, pattern, q_lower, per, results)
        if "goal" in wanted:
            _search_goals(conn, pattern, q_lower, per, results)
        if "project" in wanted:
            _search_projects(conn, pattern, q_lower, per, results)
        if "draft" in wanted:
            _search_drafts(conn, pattern, q_lower, per, results)
        if "content" in wanted:
            _search_content(conn, q_clean, pattern, q_lower, per, results)

    if "decision" in wanted:
        _search_decisions(q_clean, q_lower, per, results)
    if "person" in wanted:
        _search_people(q_lower, per, results)

    # Cross-domain rank: higher score wins, ties broken by shorter title.
    results.sort(key=lambda r: (-float(r.get("score") or 0.0), len(r.get("title") or "")))

    return results[:limit]
