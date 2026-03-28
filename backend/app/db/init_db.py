import sqlite3
import uuid
import structlog
from app.config import PLATFORM_DB_PATH, HUB_DB_PATH

log = structlog.get_logger()

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    parent_id TEXT REFERENCES nodes(id),
    hub_project_id TEXT,
    label TEXT NOT NULL,
    node_type TEXT NOT NULL DEFAULT 'group',
    sort_order INTEGER NOT NULL DEFAULT 0,
    path TEXT NOT NULL DEFAULT '',
    depth INTEGER NOT NULL DEFAULT 0,
    icon TEXT,
    color TEXT,
    folder_path TEXT,
    github_repo TEXT,
    jira_key TEXT,
    confluence_space TEXT,
    prefix TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_nodes_path ON nodes(path);
CREATE INDEX IF NOT EXISTS idx_nodes_hub ON nodes(hub_project_id);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    node_id TEXT,
    project_id TEXT,
    model TEXT NOT NULL DEFAULT 'sonnet',
    role TEXT DEFAULT 'custom',
    status TEXT NOT NULL DEFAULT 'idle' CHECK(status IN ('idle','running','paused','completed','failed','killed')),
    task_description TEXT,
    system_prompt TEXT,
    working_directory TEXT,
    pid INTEGER,
    started_at TEXT,
    stopped_at TEXT,
    last_heartbeat TEXT,
    exit_code INTEGER,
    config TEXT DEFAULT '{}',
    reports_to TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_roles (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    default_system_prompt TEXT,
    default_model TEXT DEFAULT 'sonnet',
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS agent_output (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL REFERENCES agents(id),
    stream TEXT NOT NULL CHECK(stream IN ('stdout','stderr')),
    chunk TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_agent_output_aid ON agent_output(agent_id);

CREATE TABLE IF NOT EXISTS cost_ledger (
    id TEXT PRIMARY KEY,
    agent_id TEXT REFERENCES agents(id),
    node_id TEXT,
    project_id TEXT,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    source TEXT NOT NULL DEFAULT 'agent' CHECK(source IN ('agent','chat','think','kh_pipeline')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cost_project ON cost_ledger(project_id);
CREATE INDEX IF NOT EXISTS idx_cost_time ON cost_ledger(created_at);

CREATE TABLE IF NOT EXISTS budgets (
    project_id TEXT PRIMARY KEY,
    node_id TEXT,
    daily_cap_usd REAL,
    weekly_cap_usd REAL,
    monthly_cap_usd REAL,
    alert_threshold_pct REAL DEFAULT 0.8
);

CREATE TABLE IF NOT EXISTS governance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    item_type TEXT NOT NULL,
    item_id TEXT,
    autonomy_mode TEXT,
    confidence REAL,
    decision_by TEXT DEFAULT 'user',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_gov_time ON governance_log(created_at);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    agent_id TEXT REFERENCES agents(id),
    node_id TEXT,
    project_id TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','checked_out','in_progress','review','done','cancelled')),
    priority TEXT DEFAULT 'medium' CHECK(priority IN ('high','medium','low')),
    checked_out_by TEXT,
    checked_out_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS task_documents (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    key TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    revision INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(task_id, key)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT,
    model TEXT DEFAULT 'sonnet',
    message_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES chat_sessions(id),
    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
    content TEXT NOT NULL,
    model TEXT,
    tokens_used INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

CREATE TABLE IF NOT EXISTS preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    parent_id TEXT,
    author TEXT NOT NULL DEFAULT 'user',
    body TEXT NOT NULL,
    mentions TEXT DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_comments_entity ON comments(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id);

CREATE TABLE IF NOT EXISTS project_context (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    section TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    author_agent_id TEXT,
    author_role TEXT,
    version INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_pctx_node ON project_context(node_id);

CREATE TABLE IF NOT EXISTS handoffs (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    workflow_id TEXT,
    from_agent_id TEXT NOT NULL,
    from_role TEXT,
    to_role TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','in_progress','completed','rejected','skipped')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    accepted_at TEXT,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_handoffs_node ON handoffs(node_id);
CREATE INDEX IF NOT EXISTS idx_handoffs_status ON handoffs(status);

CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    template_name TEXT NOT NULL,
    objective TEXT,
    steps TEXT NOT NULL,
    current_step INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed','paused','cancelled')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_workflows_node ON workflows(node_id);

CREATE TABLE IF NOT EXISTS workflow_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    steps TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    template_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    node_id TEXT,
    parent_id TEXT REFERENCES goals(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    progress_pct INTEGER DEFAULT 0,
    owner TEXT,
    target_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_goals_project ON goals(project_id);
CREATE INDEX IF NOT EXISTS idx_goals_parent ON goals(parent_id);

CREATE TABLE IF NOT EXISTS draft_decisions (
    id TEXT PRIMARY KEY,
    hub_draft_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status IN ('approved','rejected')),
    decided_by TEXT DEFAULT 'user',
    decided_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_draft_decisions_hub ON draft_decisions(hub_draft_id);

CREATE TABLE IF NOT EXISTS content_classifications (
    id TEXT PRIMARY KEY,
    hub_content_id TEXT NOT NULL UNIQUE,
    project_id TEXT,
    action TEXT NOT NULL CHECK(action IN ('classify','dismiss')),
    classified_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_content_class_hub ON content_classifications(hub_content_id);

CREATE TABLE IF NOT EXISTS project_overrides (
    id TEXT PRIMARY KEY,
    hub_project_id TEXT NOT NULL UNIQUE,
    name TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_project_overrides_hub ON project_overrides(hub_project_id);

CREATE TABLE IF NOT EXISTS id_sequences (
    node_id TEXT PRIMARY KEY REFERENCES nodes(id),
    next_seq INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS todo_identifiers (
    hub_todo_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    sequence_num INTEGER NOT NULL,
    display_id TEXT NOT NULL,
    UNIQUE(node_id, sequence_num)
);
CREATE INDEX IF NOT EXISTS idx_todo_ident_display ON todo_identifiers(display_id);

CREATE TABLE IF NOT EXISTS todo_dependencies (
    id TEXT PRIMARY KEY,
    todo_id TEXT NOT NULL,
    depends_on TEXT NOT NULL,
    dep_type TEXT NOT NULL DEFAULT 'blocked_by',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(todo_id, depends_on)
);
CREATE INDEX IF NOT EXISTS idx_todo_deps_todo ON todo_dependencies(todo_id);
CREATE INDEX IF NOT EXISTS idx_todo_deps_dep ON todo_dependencies(depends_on);

CREATE TABLE IF NOT EXISTS todo_overrides (
    hub_todo_id TEXT PRIMARY KEY,
    title TEXT,
    status TEXT,
    priority TEXT,
    owner TEXT,
    due_date TEXT,
    project_id TEXT,
    node_id TEXT,
    source_type TEXT,
    source_content_id TEXT,
    is_platform_native INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_todo_overrides_hub ON todo_overrides(hub_todo_id);
CREATE INDEX IF NOT EXISTS idx_todo_overrides_status ON todo_overrides(status);

CREATE TABLE IF NOT EXISTS analysis_jobs (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    folder_path TEXT NOT NULL,
    analysis_type TEXT DEFAULT 'full',
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','running','completed','failed','cancelled')),
    file_count INTEGER DEFAULT 0,
    agent_ids TEXT DEFAULT '[]',
    results_summary TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(id)
);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_node ON analysis_jobs(node_id);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status ON analysis_jobs(status);

CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_node ON tasks(node_id);
CREATE INDEX IF NOT EXISTS idx_agents_node ON agents(node_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_cost_ledger_agent ON cost_ledger(agent_id);
CREATE INDEX IF NOT EXISTS idx_cost_ledger_node ON cost_ledger(node_id);
CREATE INDEX IF NOT EXISTS idx_goals_node ON goals(node_id);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_handoffs_node ON handoffs(node_id);
CREATE INDEX IF NOT EXISTS idx_workflows_node ON workflows(node_id);
CREATE INDEX IF NOT EXISTS idx_project_context_node ON project_context(node_id);
"""

MIGRATION = """
-- Rename old tables if they exist (backward compatibility)
-- SQLite doesn't support IF EXISTS on ALTER TABLE, so we use a workaround
"""

def init_platform_db():
    PLATFORM_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PLATFORM_DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")

    # Backward compatibility: rename old tables if they exist
    try:
        existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        if "stations" in existing and "agents" not in existing:
            conn.execute("ALTER TABLE stations RENAME TO agents")
        if "station_output" in existing and "agent_output" not in existing:
            conn.execute("ALTER TABLE station_output RENAME TO agent_output")
            # Rename station_id column to agent_id in agent_output
            # SQLite 3.25+ supports RENAME COLUMN
            try:
                conn.execute("ALTER TABLE agent_output RENAME COLUMN station_id TO agent_id")
            except Exception as e:
                log.warning("rename_column_skipped", table="agent_output", column="station_id", error=str(e))

        # Rename station_id column in cost_ledger if it exists
        if "cost_ledger" in existing:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(cost_ledger)").fetchall()}
            if "station_id" in cols and "agent_id" not in cols:
                try:
                    conn.execute("ALTER TABLE cost_ledger RENAME COLUMN station_id TO agent_id")
                except Exception as e:
                    log.warning("rename_column_skipped", table="cost_ledger", column="station_id", error=str(e))

        # Rename station_id column in tasks if it exists
        if "tasks" in existing:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(tasks)").fetchall()}
            if "station_id" in cols and "agent_id" not in cols:
                try:
                    conn.execute("ALTER TABLE tasks RENAME COLUMN station_id TO agent_id")
                except Exception as e:
                    log.warning("rename_column_skipped", table="tasks", column="station_id", error=str(e))

        # Drop old index and recreate with new name
        if "agent_output" in existing or "stations" in existing:
            try:
                conn.execute("DROP INDEX IF EXISTS idx_station_output_sid")
            except Exception as e:
                log.warning("drop_index_skipped", index="idx_station_output_sid", error=str(e))

        conn.commit()
    except Exception as e:
        log.warning("migration_failed", error=str(e))

    # Add session_id to chat_messages before running SCHEMA (which creates an index on it)
    try:
        existing_tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "chat_messages" in existing_tables:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(chat_messages)").fetchall()}
            if "session_id" not in cols:
                conn.execute("ALTER TABLE chat_messages ADD COLUMN session_id TEXT")
                conn.commit()
                log.info("migration_chat_session_id_added")
    except Exception as e:
        log.warning("chat_session_migration_failed", error=str(e))

    conn.executescript(SCHEMA)

    # Add new columns to existing tables
    existing_tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    # nodes: folder_path, github_repo, jira_key, confluence_space
    if "nodes" in existing_tables:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(nodes)").fetchall()}
        for col in ("folder_path", "github_repo", "jira_key", "confluence_space", "prefix"):
            if col not in cols:
                try:
                    conn.execute(f"ALTER TABLE nodes ADD COLUMN {col} TEXT")
                except Exception as e:
                    log.warning("add_column_skipped", table="nodes", column=col, error=str(e))

    # node_id on agents, goals, tasks, cost_ledger, budgets
    for table in ("agents", "goals", "tasks", "cost_ledger", "budgets"):
        if table in existing_tables:
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            if "node_id" not in cols:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN node_id TEXT")
                except Exception as e:
                    log.warning("add_column_skipped", table=table, column="node_id", error=str(e))

    # chat_messages: add session_id column if missing
    if "chat_messages" in existing_tables:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(chat_messages)").fetchall()}
        if "session_id" not in cols:
            try:
                conn.execute("ALTER TABLE chat_messages ADD COLUMN session_id TEXT REFERENCES chat_sessions(id)")
            except Exception as e:
                log.warning("add_column_skipped", table="chat_messages", column="session_id", error=str(e))

    # Add role column to agents if missing
    if "agents" in existing_tables:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(agents)").fetchall()}
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

    # Ensure all indexes exist on existing databases (idempotent)
    _runtime_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_node ON tasks(node_id)",
        "CREATE INDEX IF NOT EXISTS idx_agents_node ON agents(node_id)",
        "CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)",
        "CREATE INDEX IF NOT EXISTS idx_cost_ledger_agent ON cost_ledger(agent_id)",
        "CREATE INDEX IF NOT EXISTS idx_cost_ledger_node ON cost_ledger(node_id)",
        "CREATE INDEX IF NOT EXISTS idx_goals_node ON goals(node_id)",
        "CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)",
        "CREATE INDEX IF NOT EXISTS idx_comments_entity ON comments(entity_type, entity_id)",
        "CREATE INDEX IF NOT EXISTS idx_handoffs_node ON handoffs(node_id)",
        "CREATE INDEX IF NOT EXISTS idx_workflows_node ON workflows(node_id)",
        "CREATE INDEX IF NOT EXISTS idx_project_context_node ON project_context(node_id)",
    ]
    for idx_sql in _runtime_indexes:
        try:
            conn.execute(idx_sql)
        except Exception as e:
            log.warning("create_index_skipped", sql=idx_sql, error=str(e))
    conn.commit()

    # Seed default agent roles if the table is empty
    _seed_agent_roles(conn)

    # Seed default workflow templates
    _seed_workflow_templates(conn)

    conn.close()
    _seed_nodes()
    _backfill_agents_for_nodes()


def _backfill_agents_for_nodes():
    """Create missing agent roles for any team/project nodes."""
    conn = sqlite3.connect(str(PLATFORM_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        nodes = conn.execute(
            "SELECT id, label, node_type FROM nodes WHERE node_type IN ('team', 'project')"
        ).fetchall()

        roles = conn.execute(
            "SELECT slug, name, default_model, default_system_prompt FROM agent_roles ORDER BY sort_order"
        ).fetchall()

        if not nodes or not roles:
            return

        count = 0
        for node in nodes:
            # Get existing role slugs for this node
            existing_roles = {r[0] for r in conn.execute(
                "SELECT role FROM agents WHERE node_id = ?", (node["id"],)
            ).fetchall()}

            for role in roles:
                if role["slug"] not in existing_roles:
                    agent_id = str(uuid.uuid4())
                    conn.execute(
                        "INSERT INTO agents (id, name, node_id, model, role, system_prompt, status) "
                        "VALUES (?, ?, ?, ?, ?, ?, 'idle')",
                        (agent_id, role["name"], node["id"], role["default_model"],
                         role["slug"], role["default_system_prompt"]),
                    )
                    count += 1

            # Set hierarchy for this node's agents
            _set_agent_hierarchy(conn, node["id"])

        conn.commit()
        if count > 0:
            log.info("backfill_agents_done", agents_created=count, nodes_checked=len(nodes))
    except Exception as e:
        log.warning("backfill_agents_failed", error=str(e))
    finally:
        conn.close()


# Hierarchy: role -> reports_to role slug (None = root)
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


def _set_agent_hierarchy(conn, node_id: str):
    """Set reports_to for all agents in a node based on role hierarchy."""
    agents = conn.execute(
        "SELECT id, role FROM agents WHERE node_id = ?", (node_id,)
    ).fetchall()

    # Build role -> agent_id lookup
    role_to_id = {a["role"]: a["id"] for a in agents}

    for agent in agents:
        role = agent["role"]
        parent_role = _AGENT_HIERARCHY.get(role)

        if parent_role is None:
            # Root agent (chief-of-staff) or unknown role — no parent
            reports_to = None
        else:
            # Try the designated parent; fall back to chief-of-staff
            reports_to = role_to_id.get(parent_role) or role_to_id.get("chief-of-staff")

        conn.execute(
            "UPDATE agents SET reports_to = ? WHERE id = ?",
            (reports_to, agent["id"]),
        )


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
        "McKinsey communication standards, concise executive summaries.",
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


def _seed_agent_roles(conn):
    """Seed default agent roles — upsert missing roles."""
    try:
        existing = {r[0] for r in conn.execute("SELECT slug FROM agent_roles").fetchall()}
        added = 0
        for slug, name, model, prompt, sort_order in DEFAULT_AGENT_ROLES:
            if slug not in existing:
                conn.execute(
                    "INSERT INTO agent_roles (slug, name, default_model, default_system_prompt, sort_order) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (slug, name, model, prompt, sort_order),
                )
                added += 1
        if added > 0:
            conn.commit()
            log.info("agent_roles_seeded", added=added, total=len(DEFAULT_AGENT_ROLES))
    except Exception as e:
        log.error("seed_agent_roles_failed", error=str(e))


import json as _json

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


def _seed_workflow_templates(conn):
    """Seed/update default workflow templates — upsert."""
    try:
        existing = {r[0] for r in conn.execute("SELECT id FROM workflow_templates").fetchall()}
        added = 0
        updated = 0
        for template_id, name, description, steps in DEFAULT_WORKFLOW_TEMPLATES:
            if template_id in existing:
                conn.execute(
                    "UPDATE workflow_templates SET name=?, description=?, steps=? WHERE id=?",
                    (name, description, steps, template_id),
                )
                updated += 1
            else:
                conn.execute(
                    "INSERT INTO workflow_templates (id, name, description, steps) VALUES (?, ?, ?, ?)",
                    (template_id, name, description, steps),
                )
                added += 1
        conn.commit()
        if added or updated:
            log.info("workflow_templates_seeded", added=added, updated=updated)
    except Exception as e:
        log.error("seed_workflow_templates_failed", error=str(e))


def _seed_nodes():
    """Seed the nodes table with hub.db projects if empty."""
    conn = sqlite3.connect(str(PLATFORM_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        if count > 0:
            return

        # Create root node
        conn.execute(
            "INSERT INTO nodes (id, parent_id, hub_project_id, label, node_type, sort_order, path, depth) "
            "VALUES (?, NULL, NULL, ?, ?, 0, ?, 0)",
            ("root", "My Portfolio", "group", "/root"),
        )

        # Read projects from hub.db
        if not HUB_DB_PATH.exists():
            log.warning("hub_db_not_found", path=str(HUB_DB_PATH))
            conn.commit()
            return

        hub_conn = sqlite3.connect(f"file:{HUB_DB_PATH}?mode=ro", uri=True, timeout=10)
        hub_conn.row_factory = sqlite3.Row
        try:
            rows = hub_conn.execute("SELECT id, name FROM projects ORDER BY name").fetchall()
            for idx, row in enumerate(rows):
                node_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO nodes (id, parent_id, hub_project_id, label, node_type, sort_order, path, depth) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (node_id, "root", row["id"], row["name"], "team", idx, f"/root/{node_id}", 1),
                )
            log.info("nodes_seeded", count=len(rows))
        finally:
            hub_conn.close()

        conn.commit()
    except Exception as e:
        log.error("seed_nodes_failed", error=str(e))
    finally:
        conn.close()
