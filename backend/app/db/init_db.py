"""Platform DB initialization.

After Sprint 6A: the canonical schema is SA Core metadata in ``app.db.tables``.
This module:

1. Runs backward-compat ALTER TABLE migrations against legacy ``platform.db``
   files (rename ``stations`` -> ``agents``, add new columns, etc.).
2. Calls ``metadata.create_all(engine)`` to create every missing table.
3. Creates the ``todo_identifiers`` compat VIEW (not modelled in SA Core).
4. Seeds default agent_roles, workflow_templates, and bootstraps the nodes
   tree from hub.db on first run.

Raw SQLite DDL was previously ~640 lines in a ``SCHEMA`` constant; that has
been removed -- ``tables.py`` is now the single source of truth.
"""

import json as _json
import sqlite3
import uuid

import structlog
# Historical raw DDL — kept for documentation / emergency rollback only.
# DO NOT execute against platform.db; use `metadata.create_all()` instead.
# tables.py is the single source of truth.

from sqlalchemy import insert, select, text, update

from app.config import HUB_DB_PATH, PLATFORM_DB_PATH
from app.db.engine import engine
from app.db.tables import (
    agent_roles,
    agents,
    metadata,
    nodes,
    workflow_templates,
)

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# Legacy ALTER TABLE migrations
#
# These run BEFORE metadata.create_all() so that pre-existing databases get
# their column shape brought up to current expectations.  New databases skip
# all of these (the tables don't exist yet) and go straight to create_all.
#
# Kept on raw sqlite3 because:
#   * SQLite ALTER TABLE has SQLite-specific quirks (RENAME COLUMN needs 3.25+)
#   * PRAGMA table_info() is the cheapest column-discovery path
#   * These statements are idempotent and only relevant to local SQLite files
# ---------------------------------------------------------------------------

def _run_legacy_migrations() -> None:
    PLATFORM_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PLATFORM_DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")

    def _tables() -> set:
        return {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}

    def _cols(table: str) -> set:
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}

    try:
        existing = _tables()

        # stations -> agents rename
        if "stations" in existing and "agents" not in existing:
            conn.execute("ALTER TABLE stations RENAME TO agents")
        if "station_output" in existing and "agent_output" not in existing:
            conn.execute("ALTER TABLE station_output RENAME TO agent_output")
            try:
                conn.execute("ALTER TABLE agent_output RENAME COLUMN station_id TO agent_id")
            except Exception as e:
                log.warning("rename_column_skipped", table="agent_output", column="station_id", error=str(e))

        if "cost_ledger" in existing and "station_id" in _cols("cost_ledger") and "agent_id" not in _cols("cost_ledger"):
            try:
                conn.execute("ALTER TABLE cost_ledger RENAME COLUMN station_id TO agent_id")
            except Exception as e:
                log.warning("rename_column_skipped", table="cost_ledger", column="station_id", error=str(e))

        if "tasks" in existing and "station_id" in _cols("tasks") and "agent_id" not in _cols("tasks"):
            try:
                conn.execute("ALTER TABLE tasks RENAME COLUMN station_id TO agent_id")
            except Exception as e:
                log.warning("rename_column_skipped", table="tasks", column="station_id", error=str(e))

        if "agent_output" in existing or "stations" in existing:
            try:
                conn.execute("DROP INDEX IF EXISTS idx_station_output_sid")
            except Exception as e:
                log.warning("drop_index_skipped", index="idx_station_output_sid", error=str(e))

        conn.commit()
    except Exception as e:
        log.warning("migration_failed", error=str(e))

    # todo_identifiers (table) -> entity_identifiers
    try:
        existing = _tables()
        if "todo_identifiers" in existing and "entity_identifiers" not in existing:
            conn.execute(
                "CREATE TABLE entity_identifiers AS "
                "SELECT hub_todo_id AS entity_id, 'todo' AS entity_type, "
                "node_id, sequence_num, display_id FROM todo_identifiers"
            )
            conn.execute("DROP TABLE todo_identifiers")
            conn.commit()
            log.info("migrated_todo_identifiers_to_entity_identifiers")
        elif "todo_identifiers" in existing and "entity_identifiers" in existing:
            conn.execute(
                "INSERT OR IGNORE INTO entity_identifiers "
                "(entity_id, entity_type, node_id, sequence_num, display_id) "
                "SELECT hub_todo_id, 'todo', node_id, sequence_num, display_id "
                "FROM todo_identifiers"
            )
            is_table = conn.execute(
                "SELECT type FROM sqlite_master WHERE name='todo_identifiers' AND type='table'"
            ).fetchone()
            if is_table:
                conn.execute("DROP TABLE todo_identifiers")
            conn.commit()
    except Exception as e:
        log.warning("entity_identifiers_migration_failed", error=str(e))

    # chat_messages.session_id
    try:
        if "chat_messages" in _tables() and "session_id" not in _cols("chat_messages"):
            conn.execute("ALTER TABLE chat_messages ADD COLUMN session_id TEXT")
            conn.commit()
            log.info("migration_chat_session_id_added")
    except Exception as e:
        log.warning("chat_session_migration_failed", error=str(e))

    # content_classifications extra columns (pre-SCHEMA pass)
    try:
        if "content_classifications" in _tables():
            cc_cols = _cols("content_classifications")
            for col, ddl_suffix in [
                ("confidence", " REAL DEFAULT 0.0"),
                ("reasoning", " TEXT"),
                ("auto_classified", " INTEGER DEFAULT 0"),
                ("status", " TEXT DEFAULT 'pending'"),
                ("classified_project_id", " TEXT"),
                ("suggested_project_id", " TEXT"),
                ("created_at", " TEXT"),
            ]:
                if col not in cc_cols:
                    try:
                        conn.execute(f"ALTER TABLE content_classifications ADD COLUMN {col}{ddl_suffix}")
                    except Exception:
                        pass
            conn.commit()
    except Exception as e:
        log.warning("content_classifications_pre_migration_failed", error=str(e))

    # nodes: folder_path, github_repo, jira_key, confluence_space, prefix
    try:
        if "nodes" in _tables():
            cols = _cols("nodes")
            for col in ("folder_path", "github_repo", "jira_key", "confluence_space", "prefix"):
                if col not in cols:
                    try:
                        conn.execute(f"ALTER TABLE nodes ADD COLUMN {col} TEXT")
                    except Exception as e:
                        log.warning("add_column_skipped", table="nodes", column=col, error=str(e))
            conn.commit()
    except Exception as e:
        log.warning("nodes_alter_failed", error=str(e))

    # node_id on agents, goals, tasks, cost_ledger, budgets
    try:
        existing = _tables()
        for table in ("agents", "goals", "tasks", "cost_ledger", "budgets"):
            if table in existing and "node_id" not in _cols(table):
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN node_id TEXT")
                except Exception as e:
                    log.warning("add_column_skipped", table=table, column="node_id", error=str(e))
        conn.commit()
    except Exception as e:
        log.warning("node_id_alter_failed", error=str(e))

    # tasks: delegation columns
    try:
        if "tasks" in _tables():
            task_cols = _cols("tasks")
            for col, default in [
                ("delegated_by", None),
                ("delegated_to", None),
                ("parent_task_id", None),
                ("context_json", "'{}'"),
            ]:
                if col not in task_cols:
                    ddl = f"ALTER TABLE tasks ADD COLUMN {col} TEXT"
                    if default is not None:
                        ddl += f" DEFAULT {default}"
                    try:
                        conn.execute(ddl)
                    except Exception as e:
                        log.warning("add_column_skipped", table="tasks", column=col, error=str(e))
            conn.commit()
    except Exception as e:
        log.warning("tasks_alter_failed", error=str(e))

    # agents: role, reports_to
    try:
        if "agents" in _tables():
            cols = _cols("agents")
            if "role" not in cols:
                try:
                    conn.execute("ALTER TABLE agents ADD COLUMN role TEXT DEFAULT 'custom'")
                except Exception as e:
                    log.warning("add_column_skipped", table="agents", column="role", error=str(e))
            if "reports_to" not in cols:
                try:
                    conn.execute("ALTER TABLE agents ADD COLUMN reports_to TEXT")
                except Exception as e:
                    log.warning("add_column_skipped", table="agents", column="reports_to", error=str(e))
            conn.commit()
    except Exception as e:
        log.warning("agents_alter_failed", error=str(e))

    conn.close()


# ---------------------------------------------------------------------------
# Compat VIEW + non-Table objects (executed via SA engine after create_all)
# ---------------------------------------------------------------------------

_COMPAT_OBJECTS = [
    # Backward compat view so old code referencing todo_identifiers still works
    "CREATE VIEW IF NOT EXISTS todo_identifiers AS "
    "SELECT entity_id AS hub_todo_id, node_id, sequence_num, display_id "
    "FROM entity_identifiers WHERE entity_type = 'todo'",
]


def _create_compat_objects() -> None:
    """Create views/triggers that SA Core ``Table`` can't model directly."""
    with engine.begin() as conn:
        for stmt in _COMPAT_OBJECTS:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                log.warning("compat_object_skipped", stmt=stmt[:60], error=str(e))


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------

def init_platform_db() -> None:
    """Initialize platform.db: migrate legacy schema, create tables, seed data."""
    # 1. Bring legacy SQLite files up to current column shape.
    _run_legacy_migrations()

    # 2. Create any missing tables from SA Core metadata (single source of truth).
    metadata.create_all(engine, checkfirst=True)

    # 3. Create views / other objects SA Core doesn't manage.
    _create_compat_objects()

    # 4. Seed default reference data.
    _seed_agent_roles()
    _seed_workflow_templates()
    _seed_nodes()
    _backfill_agents_for_nodes()


# Spec alias for smoke-test invocation paths.
init_database = init_platform_db


# ---------------------------------------------------------------------------
# Seed: nodes (root + hub.db projects on first run)
# ---------------------------------------------------------------------------

def _seed_nodes() -> None:
    """Seed the nodes table with hub.db projects if empty."""
    try:
        with engine.begin() as conn:
            count = conn.execute(select(nodes.c.id).limit(1)).first()
            if count is not None:
                return

            conn.execute(insert(nodes).values(
                id="root",
                parent_id=None,
                hub_project_id=None,
                label="My Portfolio",
                node_type="group",
                sort_order=0,
                path="/root",
                depth=0,
                created_at=text("datetime('now')"),
                updated_at=text("datetime('now')"),
            ))

            if not HUB_DB_PATH.exists():
                log.warning("hub_db_not_found", path=str(HUB_DB_PATH))
                return

            hub_conn = sqlite3.connect(f"file:{HUB_DB_PATH}?mode=ro", uri=True, timeout=10)
            hub_conn.row_factory = sqlite3.Row
            try:
                rows = hub_conn.execute(
                    "SELECT id, name FROM projects ORDER BY name"
                ).fetchall()
                for idx, row in enumerate(rows):
                    node_id = str(uuid.uuid4())
                    conn.execute(insert(nodes).values(
                        id=node_id,
                        parent_id="root",
                        hub_project_id=row["id"],
                        label=row["name"],
                        node_type="team",
                        sort_order=idx,
                        path=f"/root/{node_id}",
                        depth=1,
                        created_at=text("datetime('now')"),
                        updated_at=text("datetime('now')"),
                    ))
                log.info("nodes_seeded", count=len(rows))
            finally:
                hub_conn.close()
    except Exception as e:
        log.error("seed_nodes_failed", error=str(e))


# ---------------------------------------------------------------------------
# Seed: agent_roles
# ---------------------------------------------------------------------------

DEFAULT_AGENT_ROLES = [
    (
        "chief-of-staff",
        "Chief of Staff",
        "opus",
        "You are the Chief of Staff — the orchestrator of this project's agent team. "
        "Your job is to read the full project context, decide which agent to delegate tasks to, "
        "coordinate handoffs between team members, and maintain the project narrative. "
        "Focus on: delegation, prioritization, context synthesis, team coordination. "
        "You see the big picture and ensure nothing falls through the cracks.",
        0,
    ),
    (
        "product-manager",
        "Product Manager",
        "opus",
        "You are a Product Manager agent. Your job is to understand stakeholder needs, "
        "write requirements, prioritize features, create PRDs, and ensure the product "
        "delivers value. Focus on: user stories, acceptance criteria, stakeholder "
        "communication, roadmap planning.",
        1,
    ),
    (
        "project-manager",
        "Project Manager",
        "sonnet",
        "You are a Project Manager agent. Your job is to track timelines, manage "
        "dependencies, flag risks, maintain status reports, and keep the team on track. "
        "Focus on: RAID logs, status updates, milestone tracking, blocker escalation.",
        2,
    ),
    (
        "technical-architect",
        "Technical Architect",
        "opus",
        "You are a Technical Architect agent. Your job is to review technical decisions, "
        "create architecture documents, evaluate trade-offs, and ensure technical quality. "
        "Focus on: system design, API design, data modeling, technology selection, "
        "scalability, and maintainability. You review before the Developer builds.",
        3,
    ),
    (
        "developer",
        "Developer",
        "opus",
        "You are a Developer agent. Your job is to implement features, write code, "
        "debug issues, and maintain code quality. Focus on: clean code, testing, "
        "implementation, technical documentation. Follow the Technical Architect's designs.",
        4,
    ),
    (
        "qa-reviewer",
        "QA Reviewer",
        "opus",
        "You are a QA Reviewer agent. Your job is to review outputs of every other agent — "
        "code, documents, plans, communications. You are the quality gate. "
        "Focus on: correctness, completeness, consistency, security, edge cases. "
        "Flag issues before they reach stakeholders. Be thorough but constructive.",
        5,
    ),
    (
        "user-researcher",
        "User Researcher",
        "sonnet",
        "You are a User Researcher agent. Your job is to understand user needs, "
        "synthesize feedback, conduct analysis, and provide UX recommendations. Focus "
        "on: user interviews, feedback themes, usability findings, research reports.",
        6,
    ),
    (
        "communications-specialist",
        "Communications Specialist",
        "sonnet",
        "You are a Communications Specialist agent. Your job is to draft stakeholder updates, "
        "email replies, meeting summaries, and announcements. You know the right tone, "
        "formatting, and audience for each piece. Focus on: clarity, professionalism, "
        "professional communication standards, concise executive summaries.",
        7,
    ),
    (
        "data-analyst",
        "Data Analyst",
        "sonnet",
        "You are a Data Analyst agent. Your job is to analyze costs, track metrics, "
        "generate trend reports, and surface anomalies. Turn raw data into actionable insights. "
        "Focus on: cost analysis, velocity tracking, budget forecasting, dashboard metrics.",
        8,
    ),
    (
        "scribe",
        "Scribe",
        "sonnet",
        "You are a Scribe agent. Your job is to process meeting recordings into structured notes, "
        "extract action items, link decisions to projects, and maintain the knowledge trail. "
        "Focus on: accurate transcription, action item extraction, decision logging, "
        "connecting meeting outcomes to project goals.",
        9,
    ),
]


def _seed_agent_roles() -> None:
    """Seed default agent roles — upsert missing roles."""
    try:
        with engine.begin() as conn:
            existing = {r[0] for r in conn.execute(select(agent_roles.c.slug)).fetchall()}
            added = 0
            for slug, name, model, prompt, sort_order in DEFAULT_AGENT_ROLES:
                if slug not in existing:
                    conn.execute(insert(agent_roles).values(
                        slug=slug,
                        name=name,
                        default_model=model,
                        default_system_prompt=prompt,
                        sort_order=sort_order,
                    ))
                    added += 1
        if added > 0:
            log.info("agent_roles_seeded", added=added, total=len(DEFAULT_AGENT_ROLES))
    except Exception as e:
        log.error("seed_agent_roles_failed", error=str(e))


# ---------------------------------------------------------------------------
# Seed: workflow_templates
# ---------------------------------------------------------------------------

DEFAULT_WORKFLOW_TEMPLATES = [
    (
        "feature-development",
        "Feature Development",
        "End-to-end feature development with architecture review and QA",
        _json.dumps([
            {"role": "chief-of-staff", "action": "delegate", "section": "brief"},
            {"role": "product-manager", "action": "write_brief", "section": "brief"},
            {"role": "technical-architect", "action": "review_architecture", "section": "plan"},
            {"role": "project-manager", "action": "create_plan", "section": "plan"},
            {"role": "developer", "action": "implement", "section": "implementation"},
            {"role": "qa-reviewer", "action": "review_quality", "section": "review"},
            {"role": "user-researcher", "action": "review_ux", "section": "review"},
            {"role": "communications-specialist", "action": "draft_announcement", "section": "decision"},
            {"role": "chief-of-staff", "action": "accept", "section": "decision"},
        ]),
    ),
    (
        "bug-investigation",
        "Bug Investigation",
        "Investigate, architect fix, implement, and QA verify",
        _json.dumps([
            {"role": "chief-of-staff", "action": "delegate", "section": "brief"},
            {"role": "developer", "action": "investigate", "section": "investigation"},
            {"role": "technical-architect", "action": "design_fix", "section": "plan"},
            {"role": "developer", "action": "fix", "section": "implementation"},
            {"role": "qa-reviewer", "action": "verify_fix", "section": "review"},
            {"role": "project-manager", "action": "close_out", "section": "decision"},
        ]),
    ),
    (
        "research-spike",
        "Research Spike",
        "Research, analyze data, synthesize, and prototype",
        _json.dumps([
            {"role": "chief-of-staff", "action": "delegate", "section": "brief"},
            {"role": "user-researcher", "action": "research", "section": "research"},
            {"role": "data-analyst", "action": "analyze_data", "section": "research"},
            {"role": "product-manager", "action": "synthesize", "section": "brief"},
            {"role": "technical-architect", "action": "design_prototype", "section": "plan"},
            {"role": "developer", "action": "prototype", "section": "implementation"},
        ]),
    ),
    (
        "stakeholder-update",
        "Stakeholder Update",
        "Draft, review, and send stakeholder communication",
        _json.dumps([
            {"role": "chief-of-staff", "action": "delegate", "section": "brief"},
            {"role": "product-manager", "action": "draft_content", "section": "brief"},
            {"role": "communications-specialist", "action": "polish_and_format", "section": "brief"},
            {"role": "qa-reviewer", "action": "review_accuracy", "section": "review"},
            {"role": "chief-of-staff", "action": "approve_send", "section": "decision"},
        ]),
    ),
    (
        "meeting-processing",
        "Meeting Processing",
        "Process meeting recording into notes, actions, and updates",
        _json.dumps([
            {"role": "scribe", "action": "transcribe_and_extract", "section": "brief"},
            {"role": "product-manager", "action": "review_actions", "section": "review"},
            {"role": "project-manager", "action": "update_tracker", "section": "plan"},
            {"role": "communications-specialist", "action": "draft_summary", "section": "decision"},
        ]),
    ),
    (
        "architecture-review",
        "Architecture Review",
        "Review technical architecture with quality gate",
        _json.dumps([
            {"role": "developer", "action": "present_design", "section": "brief"},
            {"role": "technical-architect", "action": "review_architecture", "section": "review"},
            {"role": "qa-reviewer", "action": "review_quality", "section": "review"},
            {"role": "product-manager", "action": "approve_direction", "section": "decision"},
        ]),
    ),
    (
        "cost-analysis",
        "Cost Analysis",
        "Analyze costs, generate report, and recommend actions",
        _json.dumps([
            {"role": "data-analyst", "action": "gather_metrics", "section": "research"},
            {"role": "data-analyst", "action": "analyze_trends", "section": "brief"},
            {"role": "product-manager", "action": "review_findings", "section": "review"},
            {"role": "communications-specialist", "action": "format_report", "section": "decision"},
        ]),
    ),
]


def _seed_workflow_templates() -> None:
    """Seed/update default workflow templates — upsert."""
    try:
        added = 0
        updated = 0
        with engine.begin() as conn:
            existing = {r[0] for r in conn.execute(select(workflow_templates.c.id)).fetchall()}
            for template_id, name, description, steps in DEFAULT_WORKFLOW_TEMPLATES:
                if template_id in existing:
                    conn.execute(
                        update(workflow_templates)
                        .where(workflow_templates.c.id == template_id)
                        .values(name=name, description=description, steps=steps)
                    )
                    updated += 1
                else:
                    conn.execute(insert(workflow_templates).values(
                        id=template_id,
                        name=name,
                        description=description,
                        steps=steps,
                        created_at=text("datetime('now')"),
                    ))
                    added += 1
        if added or updated:
            log.info("workflow_templates_seeded", added=added, updated=updated)
    except Exception as e:
        log.error("seed_workflow_templates_failed", error=str(e))


# ---------------------------------------------------------------------------
# Backfill agents for every team / project node
# ---------------------------------------------------------------------------

# role -> reports_to role slug (None = root)
_AGENT_HIERARCHY = {
    "chief-of-staff": None,
    "product-manager": "chief-of-staff",
    "project-manager": "chief-of-staff",
    "technical-architect": "chief-of-staff",
    "developer": "technical-architect",
    "qa-reviewer": "chief-of-staff",
    "user-researcher": "product-manager",
    "communications-specialist": "chief-of-staff",
    "data-analyst": "product-manager",
    "scribe": "project-manager",
}


def _backfill_agents_for_nodes() -> None:
    """Create missing agent roles for any team/project nodes."""
    try:
        with engine.begin() as conn:
            node_rows = conn.execute(
                select(nodes.c.id, nodes.c.label, nodes.c.node_type)
                .where(nodes.c.node_type.in_(("team", "project")))
            ).fetchall()

            role_rows = conn.execute(
                select(
                    agent_roles.c.slug,
                    agent_roles.c.name,
                    agent_roles.c.default_model,
                    agent_roles.c.default_system_prompt,
                ).order_by(agent_roles.c.sort_order)
            ).fetchall()

            if not node_rows or not role_rows:
                return

            count = 0
            for node in node_rows:
                node_id = node[0]
                existing_roles = {
                    r[0] for r in conn.execute(
                        select(agents.c.role).where(agents.c.node_id == node_id)
                    ).fetchall()
                }
                for role in role_rows:
                    slug = role[0]
                    if slug in existing_roles:
                        continue
                    agent_id = str(uuid.uuid4())
                    conn.execute(insert(agents).values(
                        id=agent_id,
                        name=role[1],
                        node_id=node_id,
                        model=role[2],
                        role=slug,
                        system_prompt=role[3],
                        status="idle",
                        created_at=text("datetime('now')"),
                        updated_at=text("datetime('now')"),
                    ))
                    count += 1

                _set_agent_hierarchy(conn, node_id)

            if count > 0:
                log.info("backfill_agents_done", agents_created=count, nodes_checked=len(node_rows))
    except Exception as e:
        log.warning("backfill_agents_failed", error=str(e))


def _set_agent_hierarchy(conn, node_id: str) -> None:
    """Set reports_to for all agents in a node based on role hierarchy."""
    agent_rows = conn.execute(
        select(agents.c.id, agents.c.role).where(agents.c.node_id == node_id)
    ).fetchall()

    role_to_id = {row[1]: row[0] for row in agent_rows}

    for row in agent_rows:
        agent_id, role = row[0], row[1]
        parent_role = _AGENT_HIERARCHY.get(role)
        if parent_role is None:
            reports_to = None
        else:
            reports_to = role_to_id.get(parent_role) or role_to_id.get("chief-of-staff")
        conn.execute(
            update(agents).where(agents.c.id == agent_id).values(reports_to=reports_to)
        )
