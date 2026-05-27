"""SA Core authoritative schema for platform.db.

This module is the SINGLE source of truth for platform.db DDL.  It mirrors
(and supersedes) the historical raw `SCHEMA` and `_MIRROR_DDL` strings.

`init_db.init_platform_db()` uses `metadata.create_all(engine)` to materialise
the schema.  Alembic autogenerate can compare a target database against this
metadata to produce migration scripts, making the schema portable from SQLite
to PostgreSQL.

Conventions:
- All TEXT columns use SA `Text` (SQLite TEXT == PG TEXT).
- All `datetime('now')` defaults are expressed as `text("(datetime('now'))")`
  which SQLite honours natively and which Alembic preserves verbatim.  On
  PostgreSQL the equivalent default (`now()`) should be substituted via an
  Alembic op when migrating.
- `CHECK` constraints are expressed as `CheckConstraint(...)` so they round-
  trip through Alembic autogenerate.
- Named indexes are attached via `Index(...)` so they survive create_all and
  are visible to autogenerate.
- The `tables.py` module continues to host SA Core table descriptors used by
  routers/services for query building.  Where those drift from this module,
  this module wins for DDL purposes.
"""

from sqlalchemy import (
    REAL,
    CheckConstraint,
    Column,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    text,
)

# Alias REAL as `Float` locally so the file reads naturally while emitting
# SQLite's native REAL type (and Postgres's REAL).  Using `sqlalchemy.Float`
# would emit `FLOAT` on SQLite which has the same REAL affinity but differs
# textually from the legacy DDL.
Float = REAL

metadata = MetaData()


def _ts_now():
    """Server-side default expression for `datetime('now')` (SQLite syntax).

    Kept verbatim from the legacy DDL.  On Postgres this becomes a no-op text
    default; Alembic migrations should override with `func.now()` when porting.
    """
    return text("(datetime('now'))")


# ---------------------------------------------------------------------------
# Nodes / tree
# ---------------------------------------------------------------------------

nodes = Table(
    "nodes",
    metadata,
    Column("id", Text, primary_key=True),
    Column("parent_id", Text),  # REFERENCES nodes(id) — self-FK kept implicit
    Column("hub_project_id", Text),
    Column("label", Text, nullable=False),
    Column("node_type", Text, nullable=False, server_default="group"),
    Column("sort_order", Integer, nullable=False, server_default="0"),
    Column("path", Text, nullable=False, server_default=""),
    Column("depth", Integer, nullable=False, server_default="0"),
    Column("icon", Text),
    Column("color", Text),
    Column("folder_path", Text),
    Column("github_repo", Text),
    Column("jira_key", Text),
    Column("confluence_space", Text),
    Column("prefix", Text),
    Column("metadata", Text, server_default="{}"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_nodes_parent", nodes.c.parent_id)
Index("idx_nodes_path", nodes.c.path)
Index("idx_nodes_hub", nodes.c.hub_project_id)

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------

agents = Table(
    "agents",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("node_id", Text),
    Column("project_id", Text),
    Column("model", Text, nullable=False, server_default="sonnet"),
    Column("role", Text, server_default="custom"),
    Column("status", Text, nullable=False, server_default="idle"),
    Column("task_description", Text),
    Column("system_prompt", Text),
    Column("working_directory", Text),
    Column("pid", Integer),
    Column("started_at", Text),
    Column("stopped_at", Text),
    Column("last_heartbeat", Text),
    Column("exit_code", Integer),
    Column("config", Text, server_default="{}"),
    Column("reports_to", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "status IN ('idle','running','paused','completed','failed','killed')",
        name="ck_agents_status",
    ),
)
Index("idx_agents_node", agents.c.node_id)
Index("idx_agents_status", agents.c.status)

agent_roles = Table(
    "agent_roles",
    metadata,
    Column("slug", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("default_system_prompt", Text),
    Column("default_model", Text, server_default="sonnet"),
    Column("sort_order", Integer, server_default="0"),
)

agent_output = Table(
    "agent_output",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("agent_id", Text, nullable=False),  # REFERENCES agents(id)
    Column("stream", Text, nullable=False),
    Column("chunk", Text, nullable=False),
    Column("timestamp", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint("stream IN ('stdout','stderr')", name="ck_agent_output_stream"),
)
Index("idx_agent_output_aid", agent_output.c.agent_id)

agent_sessions = Table(
    "agent_sessions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("agent_id", Text, nullable=False),  # REFERENCES agents(id)
    Column("conversation_id", Text),
    Column("model", Text),
    Column("status", Text, nullable=False, server_default="active"),
    Column("message_count", Integer, nullable=False, server_default="0"),
    Column("total_input_tokens", Integer, nullable=False, server_default="0"),
    Column("total_output_tokens", Integer, nullable=False, server_default="0"),
    Column("checkpoint_data", Text, server_default="{}"),
    Column("messages_json", Text, server_default="[]"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "status IN ('active','paused','completed','failed')",
        name="ck_agent_sessions_status",
    ),
)

# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

cost_ledger = Table(
    "cost_ledger",
    metadata,
    Column("id", Text, primary_key=True),
    Column("agent_id", Text),  # REFERENCES agents(id)
    Column("node_id", Text),
    Column("project_id", Text),
    Column("model", Text, nullable=False),
    Column("input_tokens", Integer, nullable=False, server_default="0"),
    Column("output_tokens", Integer, nullable=False, server_default="0"),
    Column("cost_usd", Float, nullable=False, server_default="0.0"),
    Column("source", Text, nullable=False, server_default="agent"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "source IN ('agent','chat','think','kh_pipeline')",
        name="ck_cost_ledger_source",
    ),
)
Index("idx_cost_project", cost_ledger.c.project_id)
Index("idx_cost_time", cost_ledger.c.created_at)
Index("idx_cost_ledger_agent", cost_ledger.c.agent_id)
Index("idx_cost_ledger_node", cost_ledger.c.node_id)

budgets = Table(
    "budgets",
    metadata,
    Column("project_id", Text, primary_key=True),
    Column("node_id", Text),
    Column("daily_cap_usd", Float),
    Column("weekly_cap_usd", Float),
    Column("monthly_cap_usd", Float),
    Column("alert_threshold_pct", Float, server_default="0.8"),
)

# ---------------------------------------------------------------------------
# Governance
# ---------------------------------------------------------------------------

governance_log = Table(
    "governance_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("action", Text, nullable=False),
    Column("item_type", Text, nullable=False),
    Column("item_id", Text),
    Column("autonomy_mode", Text),
    Column("confidence", Float),
    Column("decision_by", Text, server_default="user"),
    Column("notes", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_gov_time", governance_log.c.created_at)

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

tasks = Table(
    "tasks",
    metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("agent_id", Text),  # REFERENCES agents(id)
    Column("node_id", Text),
    Column("project_id", Text),
    Column("status", Text, nullable=False, server_default="open"),
    Column("priority", Text, server_default="medium"),
    Column("checked_out_by", Text),
    Column("checked_out_at", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "status IN ('open','checked_out','in_progress','review','done','cancelled')",
        name="ck_tasks_status",
    ),
    CheckConstraint(
        "priority IN ('high','medium','low')",
        name="ck_tasks_priority",
    ),
)
Index("idx_tasks_project", tasks.c.project_id)
Index("idx_tasks_status", tasks.c.status)
Index("idx_tasks_node", tasks.c.node_id)

task_documents = Table(
    "task_documents",
    metadata,
    Column("id", Text, primary_key=True),
    Column("task_id", Text, nullable=False),  # REFERENCES tasks(id)
    Column("key", Text, nullable=False),
    Column("body", Text, nullable=False, server_default=""),
    Column("revision", Integer, nullable=False, server_default="1"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
    UniqueConstraint("task_id", "key", name="uq_task_documents_task_key"),
)

task_board = Table(
    "task_board",
    metadata,
    Column("id", Text, primary_key=True),
    Column("node_id", Text, nullable=False),
    Column("name", Text, nullable=False, server_default="Shared Board"),
    Column("agent_ids", Text, nullable=False, server_default="[]"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)

# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

chat_sessions = Table(
    "chat_sessions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text),
    Column("model", Text, server_default="sonnet"),
    Column("message_count", Integer, server_default="0"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
)

chat_messages = Table(
    "chat_messages",
    metadata,
    Column("id", Text, primary_key=True),
    Column("session_id", Text),  # REFERENCES chat_sessions(id)
    Column("role", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("model", Text),
    Column("tokens_used", Integer),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "role IN ('user','assistant','system')",
        name="ck_chat_messages_role",
    ),
)
Index("idx_chat_messages_session", chat_messages.c.session_id)

# ---------------------------------------------------------------------------
# Preferences / Comments
# ---------------------------------------------------------------------------

preferences = Table(
    "preferences",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", Text, nullable=False),
)

comments = Table(
    "comments",
    metadata,
    Column("id", Text, primary_key=True),
    Column("entity_type", Text, nullable=False),
    Column("entity_id", Text, nullable=False),
    Column("parent_id", Text),
    Column("author", Text, nullable=False, server_default="user"),
    Column("body", Text, nullable=False),
    Column("mentions", Text, server_default="[]"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_comments_entity", comments.c.entity_type, comments.c.entity_id)
Index("idx_comments_parent", comments.c.parent_id)

# ---------------------------------------------------------------------------
# Project context / Handoffs / Workflows
# ---------------------------------------------------------------------------

project_context = Table(
    "project_context",
    metadata,
    Column("id", Text, primary_key=True),
    Column("node_id", Text, nullable=False),
    Column("section", Text, nullable=False),
    Column("title", Text),
    Column("content", Text, nullable=False),
    Column("author_agent_id", Text),
    Column("author_role", Text),
    Column("version", Integer, server_default="1"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_pctx_node", project_context.c.node_id)
Index("idx_project_context_node", project_context.c.node_id)

handoffs = Table(
    "handoffs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("node_id", Text, nullable=False),
    Column("workflow_id", Text),
    Column("from_agent_id", Text, nullable=False),
    Column("from_role", Text),
    Column("to_role", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("status", Text, nullable=False, server_default="pending"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("accepted_at", Text),
    Column("completed_at", Text),
    CheckConstraint(
        "status IN ('pending','in_progress','completed','rejected','skipped')",
        name="ck_handoffs_status",
    ),
)
Index("idx_handoffs_node", handoffs.c.node_id)
Index("idx_handoffs_status", handoffs.c.status)

workflows = Table(
    "workflows",
    metadata,
    Column("id", Text, primary_key=True),
    Column("node_id", Text, nullable=False),
    Column("template_name", Text, nullable=False),
    Column("objective", Text),
    Column("steps", Text, nullable=False),
    Column("current_step", Integer, server_default="0"),
    Column("status", Text, nullable=False, server_default="active"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "status IN ('active','completed','paused','cancelled')",
        name="ck_workflows_status",
    ),
)
Index("idx_workflows_node", workflows.c.node_id)

workflow_templates = Table(
    "workflow_templates",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("steps", Text, nullable=False),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)

templates = Table(
    "templates",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("template_json", Text, nullable=False),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)

# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------

goals = Table(
    "goals",
    metadata,
    Column("id", Text, primary_key=True),
    Column("project_id", Text),
    Column("node_id", Text),
    Column("parent_id", Text),  # REFERENCES goals(id) — self-FK
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("status", Text, nullable=False, server_default="active"),
    Column("progress_pct", Integer, server_default="0"),
    Column("owner", Text),
    Column("target_date", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_goals_project", goals.c.project_id)
Index("idx_goals_parent", goals.c.parent_id)
Index("idx_goals_node", goals.c.node_id)
Index("idx_goals_status", goals.c.status)

# ---------------------------------------------------------------------------
# Decisions / Classifications
# ---------------------------------------------------------------------------

draft_decisions = Table(
    "draft_decisions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("hub_draft_id", Text, nullable=False, unique=True),
    Column("status", Text, nullable=False),
    Column("decided_by", Text, server_default="user"),
    Column("decided_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "status IN ('approved','rejected')",
        name="ck_draft_decisions_status",
    ),
)
Index("idx_draft_decisions_hub", draft_decisions.c.hub_draft_id)

content_classifications = Table(
    "content_classifications",
    metadata,
    Column("id", Text, primary_key=True),
    Column("hub_content_id", Text, nullable=False, unique=True),
    Column("project_id", Text),
    Column("classified_project_id", Text),
    Column("suggested_project_id", Text),
    Column("action", Text, server_default="classify"),
    Column("confidence", Float, server_default="0.0"),
    Column("reasoning", Text),
    Column("auto_classified", Integer, server_default="0"),
    Column("status", Text, server_default="pending"),
    Column("classified_at", Text, nullable=False, server_default=_ts_now()),
    Column("created_at", Text, server_default=_ts_now()),
    CheckConstraint(
        "action IN ('classify','dismiss')",
        name="ck_content_classifications_action",
    ),
)
Index("idx_content_class_hub", content_classifications.c.hub_content_id)
Index("idx_content_class_status", content_classifications.c.status)

project_overrides = Table(
    "project_overrides",
    metadata,
    Column("id", Text, primary_key=True),
    Column("hub_project_id", Text, nullable=False, unique=True),
    Column("name", Text),
    Column("description", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_project_overrides_hub", project_overrides.c.hub_project_id)

# ---------------------------------------------------------------------------
# ID sequences / Entity identifiers
# ---------------------------------------------------------------------------

id_sequences = Table(
    "id_sequences",
    metadata,
    Column("node_id", Text, primary_key=True),  # REFERENCES nodes(id)
    Column("next_seq", Integer, nullable=False, server_default="1"),
)

entity_identifiers = Table(
    "entity_identifiers",
    metadata,
    Column("entity_id", Text, primary_key=True),
    Column("entity_type", Text, nullable=False),
    Column("node_id", Text, nullable=False),
    Column("sequence_num", Integer, nullable=False),
    Column("display_id", Text, nullable=False),
    UniqueConstraint("node_id", "sequence_num", name="uq_entity_identifiers_node_seq"),
)
Index("idx_entity_ident_display", entity_identifiers.c.display_id)
Index("idx_entity_ident_type", entity_identifiers.c.entity_type)

# ---------------------------------------------------------------------------
# Todo dependencies / overrides
# ---------------------------------------------------------------------------

todo_dependencies = Table(
    "todo_dependencies",
    metadata,
    Column("id", Text, primary_key=True),
    Column("todo_id", Text, nullable=False),
    Column("depends_on", Text, nullable=False),
    Column("dep_type", Text, nullable=False, server_default="blocked_by"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    UniqueConstraint("todo_id", "depends_on", name="uq_todo_dependencies_pair"),
    CheckConstraint(
        "dep_type IN ('blocked_by', 'related_to')",
        name="ck_todo_dependencies_dep_type",
    ),
)
Index("idx_todo_deps_todo", todo_dependencies.c.todo_id)
Index("idx_todo_deps_dep", todo_dependencies.c.depends_on)

todo_overrides = Table(
    "todo_overrides",
    metadata,
    Column("hub_todo_id", Text, primary_key=True),
    Column("title", Text),
    Column("status", Text),
    Column("priority", Text),
    Column("owner", Text),
    Column("due_date", Text),
    Column("project_id", Text),
    Column("node_id", Text),
    Column("source_type", Text),
    Column("source_content_id", Text),
    Column("is_platform_native", Integer, server_default="0"),
    Column("created_at", Text, server_default=_ts_now()),
    Column("updated_at", Text, server_default=_ts_now()),
)
Index("idx_todo_overrides_hub", todo_overrides.c.hub_todo_id)
Index("idx_todo_overrides_status", todo_overrides.c.status)

# ---------------------------------------------------------------------------
# Analysis jobs
# ---------------------------------------------------------------------------

analysis_jobs = Table(
    "analysis_jobs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("node_id", Text, nullable=False),  # FK nodes(id)
    Column("folder_path", Text, nullable=False),
    Column("analysis_type", Text, server_default="full"),
    Column("status", Text, server_default="pending"),
    Column("file_count", Integer, server_default="0"),
    Column("agent_ids", Text, server_default="[]"),
    Column("results_summary", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("completed_at", Text),
    CheckConstraint(
        "status IN ('pending','running','completed','failed','cancelled')",
        name="ck_analysis_jobs_status",
    ),
)
Index("idx_analysis_jobs_node", analysis_jobs.c.node_id)
Index("idx_analysis_jobs_status", analysis_jobs.c.status)

# ---------------------------------------------------------------------------
# Events / Triggers
# ---------------------------------------------------------------------------

events = Table(
    "events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", Text, nullable=False),
    Column("data_json", Text, nullable=False),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_events_type", events.c.event_type)
Index("idx_events_created", events.c.created_at)

triggers = Table(
    "triggers",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("trigger_type", Text, nullable=False),
    Column("enabled", Integer, nullable=False, server_default="1"),
    Column("config", Text, nullable=False, server_default="{}"),
    Column("action_type", Text, nullable=False),
    Column("action_config", Text, nullable=False, server_default="{}"),
    Column("node_id", Text),
    Column("last_fired_at", Text),
    Column("fire_count", Integer, server_default="0"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "trigger_type IN ('cron', 'webhook', 'file_watch')",
        name="ck_triggers_trigger_type",
    ),
    CheckConstraint(
        "action_type IN ('spawn_agent', 'run_command', 'create_todo', 'notify', 'podcast_generate')",
        name="ck_triggers_action_type",
    ),
)

trigger_log = Table(
    "trigger_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("trigger_id", Text, nullable=False),  # REFERENCES triggers(id)
    Column("fired_at", Text, nullable=False, server_default=_ts_now()),
    Column("status", Text, nullable=False),
    Column("result", Text),
    Column("error", Text),
    CheckConstraint(
        "status IN ('success', 'failed', 'skipped')",
        name="ck_trigger_log_status",
    ),
)
Index("idx_trigger_log_trigger", trigger_log.c.trigger_id)

# ---------------------------------------------------------------------------
# Self-improve
# ---------------------------------------------------------------------------

self_improve_cycles = Table(
    "self_improve_cycles",
    metadata,
    Column("id", Text, primary_key=True),
    Column("status", Text, nullable=False, server_default="idle"),
    Column("budget_usd", Float, nullable=False, server_default="5.0"),
    Column("spent_usd", Float, nullable=False, server_default="0.0"),
    Column("max_improvements", Integer, nullable=False, server_default="5"),
    Column("focus_areas", Text),
    Column("started_at", Text),
    Column("completed_at", Text),
    Column("error", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)

self_improve_improvements = Table(
    "self_improve_improvements",
    metadata,
    Column("id", Text, primary_key=True),
    Column("cycle_id", Text, nullable=False),  # REFERENCES self_improve_cycles(id)
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False, server_default=""),
    Column("priority", Integer, nullable=False, server_default="0"),
    Column("category", Text, nullable=False, server_default="refactor"),
    Column("status", Text, nullable=False, server_default="proposed"),
    Column("worktree_path", Text),
    Column("branch_name", Text),
    Column("diff_summary", Text),
    Column("diff_stat", Text),
    Column("test_results", Text),
    Column("review_notes", Text),
    Column("security_scan", Text),
    Column("pr_description", Text),
    Column("changelog_entry", Text),
    Column("agent_id", Text),
    Column("human_comment", Text),
    Column("reject_reason", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_si_improvements_cycle", self_improve_improvements.c.cycle_id)

self_improve_agents = Table(
    "self_improve_agents",
    metadata,
    Column("id", Text, primary_key=True),
    Column("cycle_id", Text, nullable=False),  # REFERENCES self_improve_cycles(id)
    Column("improvement_id", Text),  # REFERENCES self_improve_improvements(id)
    Column("agent_id", Text, nullable=False),
    Column("role", Text, nullable=False),
    Column("status", Text, nullable=False, server_default="pending"),
    Column("started_at", Text),
    Column("completed_at", Text),
    Column("output_summary", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_si_agents_cycle", self_improve_agents.c.cycle_id)
Index("idx_si_agents_agent", self_improve_agents.c.agent_id)

self_improve_preferences = Table(
    "self_improve_preferences",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", Text, nullable=False),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
)

# ---------------------------------------------------------------------------
# Podcasts
# ---------------------------------------------------------------------------

podcasts = Table(
    "podcasts",
    metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text, nullable=False),
    Column("script", Text),
    Column("audio_path", Text),
    Column("duration", Float),
    Column("voice", Text, server_default="af_heart"),
    Column("status", Text, server_default="pending"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "status IN ('pending','generating','ready','failed')",
        name="ck_podcasts_status",
    ),
)
Index("idx_podcasts_created", podcasts.c.created_at)

# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------

inbox_read_state = Table(
    "inbox_read_state",
    metadata,
    Column("item_key", Text, primary_key=True),
    Column("read_state", Text, nullable=False, server_default="unread"),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "read_state IN ('unread', 'seen', 'dismissed')",
        name="ck_inbox_read_state_read_state",
    ),
)

inbox_notifications = Table(
    "inbox_notifications",
    metadata,
    Column("id", Text, primary_key=True),
    Column("item_type", Text, nullable=False),
    Column("item_key", Text, nullable=False, unique=True),
    Column("title", Text, nullable=False),
    Column("body", Text),
    Column("metadata_json", Text, server_default="{}"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_inbox_notif_type", inbox_notifications.c.item_type)
Index("idx_inbox_notif_created", inbox_notifications.c.created_at)

# ---------------------------------------------------------------------------
# Jarvis sessions
# ---------------------------------------------------------------------------

jarvis_sessions = Table(
    "jarvis_sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("command", Text, nullable=False),
    Column("response_summary", Text),
    Column("cards_json", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_jarvis_sessions_created", jarvis_sessions.c.created_at)

# ---------------------------------------------------------------------------
# Verification gates / results
# ---------------------------------------------------------------------------

verification_gates = Table(
    "verification_gates",
    metadata,
    Column("id", Text, primary_key=True),
    Column("gate", Text, nullable=False),
    Column("verdict", Text, nullable=False),
    Column("checks_json", Text),
    Column("summary", Text),
    Column("node_id", Text),
    Column("entity_type", Text),
    Column("entity_id", Text),
    Column("run_at", Text, nullable=False),
    Column("duration_ms", Integer, server_default="0"),
)
Index("idx_vg_entity", verification_gates.c.entity_type, verification_gates.c.entity_id)
Index("idx_vg_node", verification_gates.c.node_id)

verification_results = Table(
    "verification_results",
    metadata,
    Column("id", Text, primary_key=True),
    Column("gate_name", Text, nullable=False),
    Column("entity_type", Text, nullable=False),
    Column("entity_id", Text, nullable=False),
    Column("passed", Integer, nullable=False),
    Column("score", Float, server_default="0.0"),
    Column("issues", Text, server_default="[]"),
    Column("verifier_results", Text),
    Column("retry_count", Integer, server_default="0"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_vr_gate", verification_results.c.gate_name)
Index(
    "idx_vr_entity",
    verification_results.c.entity_type,
    verification_results.c.entity_id,
)

# ---------------------------------------------------------------------------
# Extracted entities / Insights / Staged actions (Sprint 6)
# ---------------------------------------------------------------------------

extracted_entities = Table(
    "extracted_entities",
    metadata,
    Column("id", Text, primary_key=True),
    Column("content_id", Text, nullable=False),
    Column("entity_type", Text, nullable=False),
    Column("value", Text, nullable=False),
    Column("confidence", Float, nullable=False, server_default="0.5"),
    Column("source_mode", Text, nullable=False, server_default="regex"),
    Column("context_snippet", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "entity_type IN ('person','project','date','decision','action_item','topic')",
        name="ck_extracted_entities_type",
    ),
    CheckConstraint(
        "source_mode IN ('regex','llm')",
        name="ck_extracted_entities_source_mode",
    ),
)
Index("idx_ee_content", extracted_entities.c.content_id)
Index("idx_ee_type", extracted_entities.c.entity_type)
Index("idx_ee_value", extracted_entities.c.value)

insights = Table(
    "insights",
    metadata,
    Column("id", Text, primary_key=True),
    Column("insight_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("confidence", Float, nullable=False, server_default="0.5"),
    Column("status", Text, nullable=False, server_default="new"),
    Column("entity_ids", Text, nullable=False, server_default="[]"),
    Column("content_ids", Text, nullable=False, server_default="[]"),
    Column("metadata_json", Text, server_default="{}"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "insight_type IN ('cross_reference','pattern','contradiction')",
        name="ck_insights_type",
    ),
    CheckConstraint(
        "status IN ('new','seen','actioned','dismissed')",
        name="ck_insights_status",
    ),
)
Index("idx_insights_type", insights.c.insight_type)
Index("idx_insights_status", insights.c.status)

staged_actions = Table(
    "staged_actions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("content_id", Text, nullable=False),
    Column("action_type", Text, nullable=False, server_default="todo"),
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("assignee", Text),
    Column("due_date", Text),
    Column("priority", Text, server_default="medium"),
    Column("source_quote", Text),
    Column("confidence", Float, server_default="0.0"),
    Column("extraction_mode", Text, server_default="regex"),
    Column("status", Text, nullable=False, server_default="staged"),
    Column("result_id", Text),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
    Column("updated_at", Text, nullable=False, server_default=_ts_now()),
    CheckConstraint(
        "action_type IN ('todo', 'decision', 'follow_up')",
        name="ck_staged_actions_action_type",
    ),
    CheckConstraint(
        "extraction_mode IN ('regex', 'llm')",
        name="ck_staged_actions_extraction_mode",
    ),
    CheckConstraint(
        "status IN ('staged', 'approved', 'rejected')",
        name="ck_staged_actions_status",
    ),
)
Index("idx_staged_actions_content", staged_actions.c.content_id)
Index("idx_staged_actions_status", staged_actions.c.status)

# ---------------------------------------------------------------------------
# Agent Replays (Sprint 7)
# ---------------------------------------------------------------------------

agent_replays = Table(
    "agent_replays",
    metadata,
    Column("id", Text, primary_key=True),
    Column("agent_id", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("duration", Float),
    Column("event_count", Integer),
    Column("cost", Float),
    Column("files_changed", Integer),
    Column("share_token", Text, unique=True),
    Column("html_path", Text),
    Column("replay_schema_version", Text, server_default="1"),
    Column("created_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_agent_replays_agent", agent_replays.c.agent_id)
Index("idx_agent_replays_share", agent_replays.c.share_token)

# ---------------------------------------------------------------------------
# Attention tracking (Wave 4.3)
# ---------------------------------------------------------------------------

attention_scores = Table(
    "attention_scores",
    metadata,
    Column("project_slug", Text, primary_key=True),
    Column("score", Float, server_default="0"),
    Column("view_count", Integer, server_default="0"),
    Column("last_viewed_at", Text),
    Column("updated_at", Text),
)

attention_events = Table(
    "attention_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_slug", Text, nullable=False),
    Column("source", Text, nullable=False, server_default="content"),
    Column("viewed_at", Text, nullable=False, server_default=_ts_now()),
)
Index("idx_attention_events_slug", attention_events.c.project_slug)
Index("idx_attention_events_viewed", attention_events.c.viewed_at)

# ---------------------------------------------------------------------------
# Hub mirror tables (populated by hub_sync service from hub.db)
# These are the canonical DDL — previously defined in
# `app.services.hub_sync._MIRROR_DDL`.  We keep the legacy DDL string in
# hub_sync for runtime idempotency, but `create_all()` here owns the schema.
# ---------------------------------------------------------------------------

hub_todos = Table(
    "hub_todos",
    metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("project_id", Text),
    Column("owner", Text),
    Column("due_date", Text),
    Column("priority", Text),
    Column("status", Text),
    Column("source_type", Text),
    Column("source_content_id", Text),
    Column("jira_key", Text),
    Column("created_at", Text, nullable=False),
    Column("completed_at", Text),
    Column("tags", Text),
)

hub_content = Table(
    "hub_content",
    metadata,
    Column("id", Text, primary_key=True),
    Column("source", Text, nullable=False),
    Column("source_id", Text),
    Column("source_path", Text),
    Column("content_type", Text),
    Column("title", Text),
    Column("raw_text", Text),
    Column("processed_text", Text),
    Column("metadata", Text, server_default="{}"),
    Column("status", Text, nullable=False, server_default="ingested"),
    Column("relevance_score", Float),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
    Column("ingested_at", Text, nullable=False),
    Column("processed_at", Text),
)
Index("idx_hub_content_source", hub_content.c.source)
Index("idx_hub_content_status", hub_content.c.status)

hub_projects = Table(
    "hub_projects",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("jira_key", Text),
    Column("confluence_space", Text),
    Column("folder_path", Text),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text),
    Column("metadata_json", Text, server_default="{}"),
    Column("active", Integer, nullable=False, server_default="1"),
)

hub_sync_state = Table(
    "hub_sync_state",
    metadata,
    Column("source_name", Text, primary_key=True),
    Column("last_success", Text),
    Column("last_failure", Text),
    Column("items_synced", Integer, server_default="0"),
    Column("error_message", Text),
    Column("status", Text, server_default="unknown"),
)

hub_project_content = Table(
    "hub_project_content",
    metadata,
    Column("project_id", Text, primary_key=True, nullable=False),
    Column("content_id", Text, primary_key=True, nullable=False),
    Column("confidence", Float, server_default="0.0"),
    Column("method", Text, server_default=""),
    Column("classified_at", Text),
)

hub_api_costs = Table(
    "hub_api_costs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("timestamp", Text, nullable=False),
    Column("model", Text, nullable=False),
    Column("feature", Text, nullable=False),
    Column("input_tokens", Integer, nullable=False),
    Column("output_tokens", Integer, nullable=False),
    Column("cache_read_tokens", Integer, server_default="0"),
    Column("cache_write_tokens", Integer, server_default="0"),
    Column("cost_usd", Float, nullable=False),
    Column("content_id", Text),
)

hub_drafts = Table(
    "hub_drafts",
    metadata,
    Column("id", Text, primary_key=True),
    Column("project_id", Text, nullable=False),
    Column("source_content_id", Text, nullable=False),
    Column("target_template", Text, nullable=False),
    Column("target_section", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("format", Text, nullable=False, server_default="bullet"),
    Column("status", Text, nullable=False, server_default="pending"),
    Column("created_at", Text, nullable=False),
    Column("reviewed_at", Text),
)

hub_sync_watermark = Table(
    "hub_sync_watermark",
    metadata,
    Column("table_name", Text, primary_key=True),
    Column("last_synced_at", Text, nullable=False),
    Column("last_rowid", Integer, nullable=False, server_default="0"),
    Column("row_count", Integer, nullable=False, server_default="0"),
)


__all__ = [
    "metadata",
    # platform tables
    "nodes",
    "agents",
    "agent_roles",
    "agent_output",
    "agent_sessions",
    "cost_ledger",
    "budgets",
    "governance_log",
    "tasks",
    "task_documents",
    "task_board",
    "chat_sessions",
    "chat_messages",
    "preferences",
    "comments",
    "project_context",
    "handoffs",
    "workflows",
    "workflow_templates",
    "templates",
    "goals",
    "draft_decisions",
    "content_classifications",
    "project_overrides",
    "id_sequences",
    "entity_identifiers",
    "todo_dependencies",
    "todo_overrides",
    "analysis_jobs",
    "events",
    "triggers",
    "trigger_log",
    "self_improve_cycles",
    "self_improve_improvements",
    "self_improve_agents",
    "self_improve_preferences",
    "podcasts",
    "inbox_read_state",
    "inbox_notifications",
    "jarvis_sessions",
    "verification_gates",
    "verification_results",
    "extracted_entities",
    "insights",
    "staged_actions",
    "agent_replays",
    "attention_scores",
    "attention_events",
    # hub mirror tables
    "hub_todos",
    "hub_content",
    "hub_projects",
    "hub_sync_state",
    "hub_project_content",
    "hub_api_costs",
    "hub_drafts",
    "hub_sync_watermark",
]
