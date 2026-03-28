"""Baseline migration — create all tables and indexes matching init_db.py SCHEMA.

Revision ID: 001
Revises: None
Create Date: 2026-03-28

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# All tables and indexes, matching backend/app/db/init_db.py SCHEMA exactly.
# Uses op.execute() with IF NOT EXISTS so this is safe to run on a database
# that was already bootstrapped by init_db.py.
# ---------------------------------------------------------------------------

TABLES = """
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
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

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

CREATE TABLE IF NOT EXISTS draft_decisions (
    id TEXT PRIMARY KEY,
    hub_draft_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status IN ('approved','rejected')),
    decided_by TEXT DEFAULT 'user',
    decided_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS content_classifications (
    id TEXT PRIMARY KEY,
    hub_content_id TEXT NOT NULL UNIQUE,
    project_id TEXT,
    action TEXT NOT NULL CHECK(action IN ('classify','dismiss')),
    classified_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS project_overrides (
    id TEXT PRIMARY KEY,
    hub_project_id TEXT NOT NULL UNIQUE,
    name TEXT,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

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
"""

INDEXES = [
    # nodes
    "CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_id)",
    "CREATE INDEX IF NOT EXISTS idx_nodes_path ON nodes(path)",
    "CREATE INDEX IF NOT EXISTS idx_nodes_hub ON nodes(hub_project_id)",
    # agent_output
    "CREATE INDEX IF NOT EXISTS idx_agent_output_aid ON agent_output(agent_id)",
    # cost_ledger
    "CREATE INDEX IF NOT EXISTS idx_cost_project ON cost_ledger(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_cost_time ON cost_ledger(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_cost_ledger_agent ON cost_ledger(agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_cost_ledger_node ON cost_ledger(node_id)",
    # governance_log
    "CREATE INDEX IF NOT EXISTS idx_gov_time ON governance_log(created_at)",
    # tasks
    "CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_node ON tasks(node_id)",
    # chat_messages
    "CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)",
    # comments
    "CREATE INDEX IF NOT EXISTS idx_comments_entity ON comments(entity_type, entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id)",
    # project_context
    "CREATE INDEX IF NOT EXISTS idx_pctx_node ON project_context(node_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_context_node ON project_context(node_id)",
    # handoffs
    "CREATE INDEX IF NOT EXISTS idx_handoffs_node ON handoffs(node_id)",
    "CREATE INDEX IF NOT EXISTS idx_handoffs_status ON handoffs(status)",
    # workflows
    "CREATE INDEX IF NOT EXISTS idx_workflows_node ON workflows(node_id)",
    # goals
    "CREATE INDEX IF NOT EXISTS idx_goals_project ON goals(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_goals_parent ON goals(parent_id)",
    "CREATE INDEX IF NOT EXISTS idx_goals_node ON goals(node_id)",
    "CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)",
    # agents
    "CREATE INDEX IF NOT EXISTS idx_agents_node ON agents(node_id)",
    "CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status)",
    # draft_decisions
    "CREATE INDEX IF NOT EXISTS idx_draft_decisions_hub ON draft_decisions(hub_draft_id)",
    # content_classifications
    "CREATE INDEX IF NOT EXISTS idx_content_class_hub ON content_classifications(hub_content_id)",
    # project_overrides
    "CREATE INDEX IF NOT EXISTS idx_project_overrides_hub ON project_overrides(hub_project_id)",
    # todo_overrides
    "CREATE INDEX IF NOT EXISTS idx_todo_overrides_hub ON todo_overrides(hub_todo_id)",
    "CREATE INDEX IF NOT EXISTS idx_todo_overrides_status ON todo_overrides(status)",
    # analysis_jobs
    "CREATE INDEX IF NOT EXISTS idx_analysis_jobs_node ON analysis_jobs(node_id)",
    "CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status ON analysis_jobs(status)",
]

ALL_TABLES = [
    "analysis_jobs",
    "todo_overrides",
    "project_overrides",
    "content_classifications",
    "draft_decisions",
    "goals",
    "templates",
    "workflow_templates",
    "workflows",
    "handoffs",
    "project_context",
    "comments",
    "preferences",
    "chat_messages",
    "chat_sessions",
    "task_documents",
    "tasks",
    "governance_log",
    "budgets",
    "cost_ledger",
    "agent_output",
    "agent_roles",
    "agents",
    "nodes",
]


def upgrade() -> None:
    # Create all tables (IF NOT EXISTS — safe for existing databases)
    op.execute(TABLES)
    # Create all indexes
    for idx_sql in INDEXES:
        op.execute(idx_sql)


def downgrade() -> None:
    # Drop all tables in dependency order (children before parents)
    for table in ALL_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table}")
