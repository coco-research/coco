"""SA Core table definitions for platform.db.

These mirror the DDL in init_db.py.  They are used for typed SA Core
queries (select / insert / update / delete) across routers and services.

NOTE: The canonical schema is still the raw DDL in init_db.SCHEMA.
These Table objects must stay in sync with it.  When adding new tables
or columns, update BOTH places.
"""

from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
)

metadata = MetaData()

# ---------------------------------------------------------------------------
# Nodes / tree
# ---------------------------------------------------------------------------

nodes = Table(
    "nodes",
    metadata,
    Column("id", Text, primary_key=True),
    Column("parent_id", Text),
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
    Column("metadata", Text, key="metadata_json", server_default="{}"),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

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
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

agent_roles = Table(
    "agent_roles",
    metadata,
    Column("slug", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("default_system_prompt", Text),
    Column("default_model", Text, server_default="sonnet"),
    Column("sort_order", Integer, server_default="0"),
)

agent_sessions = Table(
    "agent_sessions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("agent_id", Text, nullable=False),
    Column("conversation_id", Text),
    Column("model", Text),
    Column("status", Text, nullable=False, server_default="active"),
    Column("message_count", Integer, nullable=False, server_default="0"),
    Column("total_input_tokens", Integer, nullable=False, server_default="0"),
    Column("total_output_tokens", Integer, nullable=False, server_default="0"),
    Column("checkpoint_data", Text, server_default="{}"),
    Column("messages_json", Text, server_default="[]"),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

agent_output = Table(
    "agent_output",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("agent_id", Text, nullable=False),
    Column("stream", Text, nullable=False),
    Column("chunk", Text, nullable=False),
    Column("timestamp", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

cost_ledger = Table(
    "cost_ledger",
    metadata,
    Column("id", Text, primary_key=True),
    Column("agent_id", Text),
    Column("node_id", Text),
    Column("project_id", Text),
    Column("model", Text, nullable=False),
    Column("input_tokens", Integer, nullable=False, server_default="0"),
    Column("output_tokens", Integer, nullable=False, server_default="0"),
    Column("cost_usd", Float, nullable=False, server_default="0.0"),
    Column("source", Text, nullable=False, server_default="agent"),
    Column("created_at", Text, nullable=False),
)

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
    Column("created_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

tasks = Table(
    "tasks",
    metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("agent_id", Text),
    Column("node_id", Text),
    Column("project_id", Text),
    Column("status", Text, nullable=False, server_default="open"),
    Column("priority", Text, server_default="medium"),
    Column("checked_out_by", Text),
    Column("checked_out_at", Text),
    Column("delegated_by", Text),
    Column("delegated_to", Text),
    Column("parent_task_id", Text),
    Column("context_json", Text, server_default="{}"),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

task_documents = Table(
    "task_documents",
    metadata,
    Column("id", Text, primary_key=True),
    Column("task_id", Text, nullable=False),
    Column("key", Text, nullable=False),
    Column("body", Text, nullable=False, server_default=""),
    Column("revision", Integer, nullable=False, server_default="1"),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

task_board = Table(
    "task_board",
    metadata,
    Column("id", Text, primary_key=True),
    Column("node_id", Text, nullable=False),
    Column("name", Text, nullable=False, server_default="Shared Board"),
    Column("agent_ids", Text, nullable=False, server_default="[]"),
    Column("created_at", Text, nullable=False),
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
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

chat_messages = Table(
    "chat_messages",
    metadata,
    Column("id", Text, primary_key=True),
    Column("session_id", Text),
    Column("role", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("model", Text),
    Column("tokens_used", Integer),
    Column("created_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

preferences = Table(
    "preferences",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

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
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Collaboration: project_context, handoffs, workflows
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
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

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
    Column("created_at", Text, nullable=False),
    Column("accepted_at", Text),
    Column("completed_at", Text),
)

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
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

workflow_templates = Table(
    "workflow_templates",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("steps", Text, nullable=False),
    Column("created_at", Text, nullable=False),
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
    Column("parent_id", Text),
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("status", Text, nullable=False, server_default="active"),
    Column("progress_pct", Integer, server_default="0"),
    Column("owner", Text),
    Column("target_date", Text),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Decisions / Classifications
# ---------------------------------------------------------------------------

draft_decisions = Table(
    "draft_decisions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("hub_draft_id", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("decided_by", Text, server_default="user"),
    Column("decided_at", Text, nullable=False),
)

content_classifications = Table(
    "content_classifications",
    metadata,
    Column("id", Text, primary_key=True),
    Column("hub_content_id", Text, nullable=False),
    Column("project_id", Text),
    Column("classified_project_id", Text),
    Column("suggested_project_id", Text),
    Column("action", Text, server_default="classify"),
    Column("confidence", Float, server_default="0.0"),
    Column("reasoning", Text),
    Column("auto_classified", Integer, server_default="0"),
    Column("status", Text, server_default="pending"),
    Column("classified_at", Text, nullable=False),
    Column("created_at", Text),
)

project_overrides = Table(
    "project_overrides",
    metadata,
    Column("id", Text, primary_key=True),
    Column("hub_project_id", Text, nullable=False),
    Column("name", Text),
    Column("description", Text),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# ID sequences / entity identifiers
# ---------------------------------------------------------------------------

id_sequences = Table(
    "id_sequences",
    metadata,
    Column("node_id", Text, primary_key=True),
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
)

# ---------------------------------------------------------------------------
# Todo overrides / dependencies
# ---------------------------------------------------------------------------

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
    Column("created_at", Text),
    Column("updated_at", Text),
)

todo_dependencies = Table(
    "todo_dependencies",
    metadata,
    Column("id", Text, primary_key=True),
    Column("todo_id", Text, nullable=False),
    Column("depends_on", Text, nullable=False),
    Column("dep_type", Text, nullable=False, server_default="blocked_by"),
    Column("created_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Analysis jobs
# ---------------------------------------------------------------------------

analysis_jobs = Table(
    "analysis_jobs",
    metadata,
    Column("id", Text, primary_key=True),
    Column("node_id", Text, nullable=False),
    Column("folder_path", Text, nullable=False),
    Column("analysis_type", Text, server_default="full"),
    Column("status", Text, server_default="pending"),
    Column("file_count", Integer, server_default="0"),
    Column("agent_ids", Text, server_default="[]"),
    Column("results_summary", Text),
    Column("created_at", Text, nullable=False),
    Column("completed_at", Text),
)

# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

events = Table(
    "events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", Text, nullable=False),
    Column("data_json", Text, nullable=False),
    Column("created_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Triggers
# ---------------------------------------------------------------------------

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
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

trigger_log = Table(
    "trigger_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("trigger_id", Text, nullable=False),
    Column("fired_at", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("result", Text),
    Column("error", Text),
)

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
    Column("created_at", Text, nullable=False),
)

self_improve_improvements = Table(
    "self_improve_improvements",
    metadata,
    Column("id", Text, primary_key=True),
    Column("cycle_id", Text, nullable=False),
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
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

self_improve_preferences = Table(
    "self_improve_preferences",
    metadata,
    Column("key", Text, primary_key=True),
    Column("value", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

self_improve_agents = Table(
    "self_improve_agents",
    metadata,
    Column("id", Text, primary_key=True),
    Column("cycle_id", Text, nullable=False),
    Column("improvement_id", Text),
    Column("agent_id", Text, nullable=False),
    Column("role", Text, nullable=False),
    Column("status", Text, nullable=False, server_default="pending"),
    Column("started_at", Text),
    Column("completed_at", Text),
    Column("output_summary", Text),
    Column("created_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Agent Replays
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
    Column("created_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Inbox
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
    Column("created_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------

inbox_read_state = Table(
    "inbox_read_state",
    metadata,
    Column("item_key", Text, primary_key=True),
    Column("read_state", Text, nullable=False, server_default="unread"),
    Column("updated_at", Text, nullable=False),
)

inbox_notifications = Table(
    "inbox_notifications",
    metadata,
    Column("id", Text, primary_key=True),
    Column("item_type", Text, nullable=False),
    Column("item_key", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("body", Text),
    Column("metadata_json", Text, server_default="{}"),
    Column("created_at", Text, nullable=False),
)

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
    Column("created_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Verification gates
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

verification_results = Table(
    "verification_results",
    metadata,
    Column("id", Text, primary_key=True),
    Column("gate", Text, nullable=False),
    Column("verdict", Text, nullable=False),
    Column("checks_json", Text),
    Column("summary", Text),
    Column("node_id", Text),
    Column("entity_type", Text),
    Column("entity_id", Text),
    Column("retry_count", Integer, server_default="0"),
    Column("budget_spent_usd", Float, server_default="0.0"),
    Column("run_at", Text, nullable=False),
    Column("duration_ms", Integer, server_default="0"),
)

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

templates = Table(
    "templates",
    metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text),
    Column("template_json", Text, nullable=False),
    Column("created_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Hub mirror tables (populated by hub_sync service from hub.db)
# ---------------------------------------------------------------------------

hub_todos = Table(
    "hub_todos", metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text),
    Column("description", Text),
    Column("project_id", Text),
    Column("owner", Text),
    Column("due_date", Text),
    Column("priority", Text),
    Column("status", Text),
    Column("source_type", Text),
    Column("source_content_id", Text),
    Column("jira_key", Text),
    Column("created_at", Text),
    Column("completed_at", Text),
    Column("tags", Text),
)

hub_content = Table(
    "hub_content", metadata,
    Column("id", Text, primary_key=True),
    Column("source", Text),
    Column("source_id", Text),
    Column("source_path", Text),
    Column("content_type", Text),
    Column("title", Text),
    Column("raw_text", Text, key="body"),        # alias: routers use .c.body
    Column("processed_text", Text, key="summary"),  # alias: routers use .c.summary
    Column("metadata", Text),
    Column("status", Text),
    Column("relevance_score", Float),
    Column("created_at", Text),
    Column("updated_at", Text),
    Column("ingested_at", Text),
    Column("processed_at", Text),
)

hub_projects = Table(
    "hub_projects", metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text),
    Column("jira_key", Text),
    Column("confluence_space", Text),
    Column("folder_path", Text),
    Column("created_at", Text),
    Column("updated_at", Text),
    Column("metadata_json", Text, server_default="{}"),
    Column("active", Integer, server_default="1"),
)

hub_sync_state = Table(
    "hub_sync_state", metadata,
    Column("source_name", Text, primary_key=True, key="source"),  # alias
    Column("last_success", Text, key="last_sync"),  # alias
    Column("last_failure", Text),
    Column("items_synced", Integer, key="item_count"),  # alias
    Column("error_message", Text, key="message"),  # alias
    Column("status", Text),
)

hub_project_content = Table(
    "hub_project_content", metadata,
    Column("project_id", Text, nullable=False),
    Column("content_id", Text, nullable=False),
    Column("confidence", Float),
    Column("method", Text),
    Column("classified_at", Text),
    UniqueConstraint("project_id", "content_id"),
)

hub_api_costs = Table(
    "hub_api_costs", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", Text, key="created_at"),  # alias
    Column("model", Text),
    Column("feature", Text),
    Column("input_tokens", Integer),
    Column("output_tokens", Integer),
    Column("cache_read_tokens", Integer),
    Column("cache_write_tokens", Integer),
    Column("cost_usd", Float),
    Column("content_id", Text),
)

hub_drafts = Table(
    "hub_drafts", metadata,
    Column("id", Text, primary_key=True),
    Column("project_id", Text),
    Column("source_content_id", Text),
    Column("target_template", Text, key="template"),  # alias
    Column("target_section", Text, key="section"),  # alias
    Column("content", Text),
    Column("format", Text),
    Column("status", Text),
    Column("created_at", Text),
    Column("reviewed_at", Text),
)

# ---------------------------------------------------------------------------
# Hub sync watermark (tracks sync progress)
# ---------------------------------------------------------------------------

staged_actions = Table(
    "staged_actions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("content_id", Text, nullable=False),
    Column("action_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text),
    Column("assignee", Text),
    Column("due_date", Text),
    Column("priority", Text, default="medium"),
    Column("source_quote", Text),
    Column("confidence", Float, default=0.0),
    Column("status", Text, default="staged"),
    Column("created_todo_id", Text),
    Column("created_at", Text),
)

hub_sync_watermark = Table(
    "hub_sync_watermark", metadata,
    Column("table_name", Text, primary_key=True),
    Column("last_synced_at", Text),
    Column("last_rowid", Integer),
    Column("row_count", Integer),
)

# ---------------------------------------------------------------------------
# Extracted entities & insights (Cross-Source Insight Engine)
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
    Column("created_at", Text, nullable=False),
)

insights = Table(
    "insights",
    metadata,
    Column("id", Text, primary_key=True),
    Column("insight_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("confidence", Float, default=0.5),
    Column("entity_ids", Text, default="[]"),
    Column("content_ids", Text, default="[]"),
    Column("sources", Text, default="[]"),
    Column("status", Text, default="new"),
    Column("created_at", Text),
)

# ---------------------------------------------------------------------------
# Audit log (Phase 11 — security/governance)
# ---------------------------------------------------------------------------

audit_log = Table(
    "audit_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("action", Text, nullable=False),
    Column("actor", Text, nullable=False, server_default="user"),
    Column("payload_hash", Text),
    Column("occurred_at", Text, nullable=False),
    Column("ip", Text),
)

# ---------------------------------------------------------------------------
# Attention tracking
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
    Column("viewed_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# project_brain.db — separate read-only DB (NOT platform.db)
#
# These tables live in a distinct MetaData so they do not conflict with
# platform.db tables of the same name (e.g. tasks, events).  They are
# consumed by routers/brain.py through its own SA Core engine.
# ---------------------------------------------------------------------------

brain_metadata = MetaData()

brain_decisions = Table(
    "decisions",
    brain_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", Integer, nullable=False),
    Column("thread_id", Integer),
    Column("date", Text, nullable=False),
    Column("decision", Text, nullable=False),
    Column("context", Text),
    Column("decided_by", Text),
    Column("impact", Text),
)

brain_events = Table(
    "events",
    brain_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", Integer, nullable=False),
    Column("date", Text, nullable=False),
    Column("type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text),
    Column("source", Text),
    Column("participants_json", Text, server_default="[]"),
)

brain_tasks = Table(
    "tasks",
    brain_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", Integer, nullable=False),
    Column("title", Text, nullable=False),
    Column("status", Text, nullable=False, server_default="open"),
    Column("owner_entity_id", Integer),
    Column("priority", Integer, server_default="3"),
    Column("due_date", Text),
    Column("blocked_by_task_id", Integer),
    Column("notes", Text),
    Column("created_at", Text, nullable=False),
    Column("completed_at", Text),
)

brain_entities = Table(
    "entities",
    brain_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", Integer, nullable=False),
    Column("type", Text, nullable=False),
    Column("name", Text, nullable=False),
    Column("external_id", Text),
    Column("metadata_json", Text, server_default="{}"),
    Column("created_at", Text, nullable=False),
    Column("updated_at", Text, nullable=False),
)

# ---------------------------------------------------------------------------
# Idempotency (Phase 2 Foundation Hardening) — see .planning/v3/backend/DESIGN.md §7
# ---------------------------------------------------------------------------

idempotency_keys = Table(
    "idempotency_keys",
    metadata,
    Column("key", Text, nullable=False),
    Column("route", Text, nullable=False),
    Column("request_hash", Text, nullable=False),
    Column("response_status", Integer, nullable=False),
    Column("response_body", Text, nullable=False),
    Column("created_at", Text, nullable=False),
    UniqueConstraint("key", "route", name="uq_idempotency_keys_key_route"),
)

# ---------------------------------------------------------------------------
# Dead-letter queue (Phase 10 — watchers + crons)
# ---------------------------------------------------------------------------
# Background jobs and file-watcher-triggered ingest tasks that fail are
# enqueued here for bounded retry. After max retries, rows are marked
# `archived` and surfaced to the operator via the admin DLQ endpoint.

dead_letter_queue = Table(
    "dead_letter_queue",
    metadata,
    Column("id", Text, primary_key=True),
    Column("source_task", Text, nullable=False),
    Column("payload_json", Text, nullable=False, server_default="{}"),
    Column("error", Text, nullable=False, server_default=""),
    Column("retry_count", Integer, nullable=False, server_default="0"),
    Column("status", Text, nullable=False, server_default="pending"),
    Column("created_at", Text, nullable=False),
    Column("next_retry_at", Text),
    Column("last_attempt_at", Text),
)

# ---------------------------------------------------------------------------
# Brain merge log (Phase 11 — Brain B4 graph ops)
# ---------------------------------------------------------------------------
# Append-only audit + undo buffer for entity_resolver merges. Distinct from
# `brain_merge_audit` (B0): `brain_merge_audit` is the forever record of
# *what* merged; `brain_merge_log` carries the *operational* metadata —
# who performed the merge, until when it's reversible, and when (if ever)
# it was undone. The graph_ops admin endpoints read from here.

brain_merge_log = Table(
    "brain_merge_log",
    metadata,
    Column("id", Text, primary_key=True),
    Column("merged_from", Text, nullable=False),
    Column("merged_into", Text, nullable=False),
    Column("performed_at", Text, nullable=False),
    Column("performed_by", Text),
    Column("reversible_until", Text),
    Column("undone_at", Text),
)
