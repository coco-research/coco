"""phase-3: brain B0 tables

Port of .planning/v3/brain/REFERENCE-IMPL/migrations/001_initial.sql into
the live Alembic chain. Creates the Brain v3 schema (knowledge graph +
chunked content store + LLM audit + decision queue) on top of the
baseline platform.db.

Tables created (in dependency order):
    relation_types
    brain_sources
    brain_people                 + idx_brain_people_email
    brain_person_aliases         + idx_aliases_canonical, idx_aliases_status
    brain_topics
    brain_documents              + idx_docs_project, idx_docs_ts,
                                   idx_docs_source, idx_docs_status
    brain_chunks                 + idx_chunks_document
    brain_chunks_fts             (FTS5 virtual table, raw SQL)
    brain_chunks_vec             (BLOB-backed; sqlite-vec virtual table
                                  attempted opportunistically, falls back
                                  to plain table if extension absent)
    brain_edges                  + idx_edges_subject, idx_edges_object
    brain_events
    brain_attention_rules
    brain_routing_rules
    brain_decision_queue         + idx_queue_status
    brain_merge_audit
    llm_invocations              + idx_llm_ts, idx_llm_model

Seeds 13 rows into relation_types (controlled predicate vocabulary).

Downgrade drops everything in reverse dependency order.

Revision ID: 140054f726ca
Revises: 001
Create Date: 2026-05-27 14:39:04.701247

"""
from __future__ import annotations

import logging
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "140054f726ca"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


logger = logging.getLogger("alembic.brain_b0")


# ---------------------------------------------------------------------------
# Shared timestamp default — matches REFERENCE-IMPL strftime expression.
# Stored as TEXT (ISO-8601 with ms) so it round-trips identically to the
# raw-SQL reference implementation and to other CoCo Platform tables.
# ---------------------------------------------------------------------------
_TS_DEFAULT = sa.text("(strftime('%Y-%m-%dT%H:%M:%fZ','now'))")


# ---------------------------------------------------------------------------
# Seed data for relation_types — the controlled predicate vocabulary.
# Mirrors the INSERT OR IGNORE block in 001_initial.sql.
# ---------------------------------------------------------------------------
_RELATION_TYPES_SEED: list[tuple[str, str, str, float, str]] = [
    ("owns", "person", "project", 1.0, "Person owns project (user-asserted)"),
    ("participates_in", "person", "project", 0.7, "Person observed participating"),
    ("authored_by", "document", "person", 1.0, "Document authored by person"),
    ("mentions", "document", "person", 0.5, "Document mentions person/topic"),
    ("classified_as", "document", "project", 0.7, "Document classified into project"),
    ("cites", "decision", "document", 1.0, "Decision cites document"),
    ("blocks", "task", "task", 1.0, "Task blocks task"),
    ("owned_by", "task", "person", 1.0, "Task owned by person"),
    ("involves", "event", "person", 0.7, "Event involves person"),
    ("related_to", "topic", "topic", 0.5, "Topic related to topic"),
    ("produces", "source", "document", 1.0, "Source produces document"),
    ("aliased_as", "person", "person", 0.95, "Alias relation (identity resolution)"),
    ("near_dup_of", "document", "document", 0.9, "Near-duplicate of another document"),
]


def _is_sqlite() -> bool:
    """True when running against a SQLite backend (FTS5 / vec gating)."""
    return op.get_bind().dialect.name == "sqlite"


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # relation_types — controlled predicate vocabulary
    # -----------------------------------------------------------------------
    op.create_table(
        "relation_types",
        sa.Column("predicate", sa.Text, primary_key=True),
        sa.Column("subject_type", sa.Text, nullable=False),
        sa.Column("object_type", sa.Text, nullable=False),
        sa.Column(
            "default_conf",
            sa.Float,
            nullable=False,
            server_default=sa.text("1.0"),
        ),
        sa.Column("description", sa.Text),
        sa.CheckConstraint(
            "default_conf BETWEEN 0.0 AND 1.0",
            name="ck_relation_types_default_conf",
        ),
    )

    # -----------------------------------------------------------------------
    # brain_sources — provenance entity per producer
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_sources",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("config", sa.Text),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.CheckConstraint(
            "kind IN ('outlook','slack','confluence','jira','voice',"
            "'screenshot','manual','gmail')",
            name="ck_brain_sources_kind",
        ),
    )

    # -----------------------------------------------------------------------
    # brain_people — canonical person registry
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_people",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("canonical_name", sa.Text, nullable=False),
        sa.Column("primary_email", sa.Text),
        sa.Column("role", sa.Text),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.Column("updated_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
    )
    op.create_index("idx_brain_people_email", "brain_people", ["primary_email"])

    # -----------------------------------------------------------------------
    # brain_person_aliases — identity resolution
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_person_aliases",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "canonical_id",
            sa.Text,
            sa.ForeignKey("brain_people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("alias_value", sa.Text, nullable=False),
        sa.Column("alias_type", sa.Text, nullable=False),
        sa.Column(
            "confidence",
            sa.Float,
            nullable=False,
            server_default=sa.text("1.0"),
        ),
        sa.Column("source", sa.Text),
        sa.Column(
            "status",
            sa.Text,
            nullable=False,
            server_default=sa.text("'auto'"),
        ),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.CheckConstraint(
            "alias_type IN ('email','slack','name_string',"
            "'voice_transcription','jira_handle')",
            name="ck_aliases_alias_type",
        ),
        sa.CheckConstraint(
            "confidence BETWEEN 0.0 AND 1.0",
            name="ck_aliases_confidence",
        ),
        sa.CheckConstraint(
            "status IN ('auto','confirmed','rejected','pending')",
            name="ck_aliases_status",
        ),
        sa.UniqueConstraint("alias_value", "alias_type", name="uq_aliases_value_type"),
    )
    op.create_index("idx_aliases_canonical", "brain_person_aliases", ["canonical_id"])
    op.create_index("idx_aliases_status", "brain_person_aliases", ["status"])

    # -----------------------------------------------------------------------
    # brain_topics — TF-IDF + LLM derived concepts
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_topics",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("label", sa.Text, nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column(
            "frequency",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
    )

    # -----------------------------------------------------------------------
    # brain_documents — unified content metadata
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_documents",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "source_id",
            sa.Text,
            sa.ForeignKey("brain_sources.id", ondelete="SET NULL"),
        ),
        sa.Column("source_external_id", sa.Text, nullable=False),
        sa.Column("source_hash", sa.Text, nullable=False, unique=True),
        sa.Column("content_type", sa.Text, nullable=False),
        sa.Column("title", sa.Text),
        sa.Column("project_id", sa.Text),  # soft FK to hub.db.projects.id
        sa.Column("raw_text", sa.Text),
        sa.Column("metadata", sa.Text, key="metadata_json"),
        sa.Column("classification_method", sa.Text),
        sa.Column("classification_confidence", sa.Float),
        sa.Column("timestamp", sa.Text, nullable=False),
        sa.Column("ingested_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.Column(
            "status",
            sa.Text,
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.CheckConstraint(
            "content_type IN ('email','voice_memo','doc','link','image','message')",
            name="ck_docs_content_type",
        ),
        sa.CheckConstraint(
            "classification_method IS NULL OR classification_method IN "
            "('rule','centroid','llm','manual')",
            name="ck_docs_classification_method",
        ),
        sa.CheckConstraint(
            "classification_confidence IS NULL OR "
            "classification_confidence BETWEEN 0.0 AND 1.0",
            name="ck_docs_classification_confidence",
        ),
        sa.CheckConstraint(
            "status IN ('active','deleted','archived')",
            name="ck_docs_status",
        ),
    )
    op.create_index("idx_docs_project", "brain_documents", ["project_id"])
    op.create_index("idx_docs_ts", "brain_documents", ["timestamp"])
    op.create_index("idx_docs_source", "brain_documents", ["source_id"])
    op.create_index("idx_docs_status", "brain_documents", ["status"])

    # -----------------------------------------------------------------------
    # brain_chunks — chunked text + metadata
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_chunks",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "document_id",
            sa.Text,
            sa.ForeignKey("brain_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("char_start", sa.Integer, nullable=False),
        sa.Column("char_end", sa.Integer, nullable=False),
        sa.Column("embedding_model", sa.Text, nullable=False),
        sa.Column("embedding_dim", sa.Integer, nullable=False),
        sa.Column("embedding_version", sa.Text, nullable=False),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_chunks_doc_idx"),
    )
    op.create_index("idx_chunks_document", "brain_chunks", ["document_id"])

    # -----------------------------------------------------------------------
    # brain_chunks_fts — FTS5 external-content virtual table.
    # Only emit on SQLite; on any other dialect we skip (the rest of the
    # brain stack treats search as a SQLite-only optimisation).
    # -----------------------------------------------------------------------
    if _is_sqlite():
        op.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS brain_chunks_fts USING fts5(
                text,
                content='brain_chunks',
                content_rowid='rowid',
                tokenize='unicode61'
            )
            """
        )
    else:
        logger.warning(
            "Skipping brain_chunks_fts: FTS5 virtual table is SQLite-only "
            "(dialect=%s)",
            op.get_bind().dialect.name,
        )

    # -----------------------------------------------------------------------
    # brain_chunks_vec — vector storage.
    #
    # Reference implementation models this as a plain table with a BLOB +
    # dim column. Production deployment layers a sqlite-vec vec0 virtual
    # table on top. We attempt the sqlite-vec virtual-table flavour first
    # (best path for prod) and fall back to the plain-table schema if the
    # extension isn't loaded — that way migration succeeds on bare SQLite
    # builds (CI runners, dev laptops without sqlite-vec installed).
    # -----------------------------------------------------------------------
    vec_dim = 512  # matches design doc §1.1 (sqlite-vec virtual table, 512-d float)
    vec_virtual_ok = False
    if _is_sqlite():
        try:
            op.execute(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS brain_chunks_vec USING vec0("
                f"chunk_id TEXT PRIMARY KEY, "
                f"embedding float[{vec_dim}]"
                f")"
            )
            vec_virtual_ok = True
        except Exception as exc:  # noqa: BLE001 — extension absent or build mismatch
            logger.warning(
                "sqlite-vec vec0 virtual table unavailable (%s); "
                "falling back to BLOB-backed brain_chunks_vec table",
                exc,
            )

    if not vec_virtual_ok:
        op.create_table(
            "brain_chunks_vec",
            sa.Column(
                "chunk_id",
                sa.Text,
                sa.ForeignKey("brain_chunks.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("embedding", sa.LargeBinary, nullable=False),
            sa.Column("dim", sa.Integer, nullable=False),
        )

    # -----------------------------------------------------------------------
    # brain_edges — subject -> predicate -> object
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_edges",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("subject_id", sa.Text, nullable=False),
        sa.Column("subject_type", sa.Text, nullable=False),
        sa.Column(
            "predicate",
            sa.Text,
            sa.ForeignKey("relation_types.predicate"),
            nullable=False,
        ),
        sa.Column("object_id", sa.Text, nullable=False),
        sa.Column("object_type", sa.Text, nullable=False),
        sa.Column(
            "confidence",
            sa.Float,
            nullable=False,
            server_default=sa.text("1.0"),
        ),
        sa.Column("evidence_id", sa.Text),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.CheckConstraint(
            "confidence BETWEEN 0.0 AND 1.0",
            name="ck_edges_confidence",
        ),
        sa.UniqueConstraint(
            "subject_id",
            "predicate",
            "object_id",
            name="uq_edges_triple",
        ),
    )
    op.create_index(
        "idx_edges_subject", "brain_edges", ["subject_id", "predicate"]
    )
    op.create_index(
        "idx_edges_object", "brain_edges", ["object_id", "predicate"]
    )

    # -----------------------------------------------------------------------
    # brain_events — time-anchored happenings (Brain v3 namespace).
    #
    # NOTE: platform.db already has a generic `events` table (baseline 001).
    # The brain table is `brain_events`, distinct namespace, no clash.
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_events",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("starts_at", sa.Text, nullable=False),
        sa.Column("ends_at", sa.Text),
        sa.Column("metadata", sa.Text, key="metadata_json"),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
    )

    # -----------------------------------------------------------------------
    # brain_attention_rules — replaces brain.json["rules"]
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_attention_rules",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column(
            "person_id",
            sa.Text,
            sa.ForeignKey("brain_people.id", ondelete="CASCADE"),
        ),
        sa.Column("project_id", sa.Text),
        sa.Column("pattern", sa.Text, nullable=False),
        sa.Column(
            "score_delta",
            sa.Float,
            nullable=False,
            server_default=sa.text("0.0"),
        ),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
    )

    # -----------------------------------------------------------------------
    # brain_routing_rules — replaces brain.json["routing"]
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_routing_rules",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("pattern", sa.Text, nullable=False),
        sa.Column("target_project_id", sa.Text, nullable=False),
        sa.Column(
            "priority",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "enabled",
            sa.Integer,
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.CheckConstraint("enabled IN (0,1)", name="ck_routing_enabled"),
    )

    # -----------------------------------------------------------------------
    # brain_decision_queue — replaces queue.json
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_decision_queue",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("payload", sa.Text, nullable=False),
        sa.Column(
            "status",
            sa.Text,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("created_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.Column("resolved_at", sa.Text),
        sa.CheckConstraint(
            "kind IN ('classification','merge_candidate','draft_approval','custom')",
            name="ck_queue_kind",
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected','expired')",
            name="ck_queue_status",
        ),
    )
    op.create_index(
        "idx_queue_status",
        "brain_decision_queue",
        ["status", "created_at"],
    )

    # -----------------------------------------------------------------------
    # brain_merge_audit — forever log of entity merges
    # -----------------------------------------------------------------------
    op.create_table(
        "brain_merge_audit",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("canonical_id", sa.Text, nullable=False),
        sa.Column("merged_alias_id", sa.Text, nullable=False),
        sa.Column("method", sa.Text, nullable=False),
        sa.Column("similarity", sa.Float),
        sa.Column("secondary_signal", sa.Text),
        sa.Column("merged_at", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.Column("undone_at", sa.Text),
        sa.Column(
            "undo_re_resolved_count",
            sa.Integer,
            server_default=sa.text("0"),
        ),
        sa.CheckConstraint(
            "method IN ('auto','user_confirmed','rule')",
            name="ck_merge_method",
        ),
    )

    # -----------------------------------------------------------------------
    # llm_invocations — every LLM call audited
    # -----------------------------------------------------------------------
    op.create_table(
        "llm_invocations",
        sa.Column("id", sa.Text, primary_key=True),
        sa.Column("model", sa.Text, nullable=False),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False),
        sa.Column("output_tokens", sa.Integer, nullable=False),
        sa.Column(
            "cost_usd",
            sa.Float,
            nullable=False,
            server_default=sa.text("0.0"),
        ),
        sa.Column(
            "fallback_used",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("result_hash", sa.Text),
        sa.Column("ts", sa.Text, nullable=False, server_default=_TS_DEFAULT),
        sa.CheckConstraint(
            "purpose IN ('classify','article','embed','rerank','chat','other')",
            name="ck_llm_purpose",
        ),
        sa.CheckConstraint(
            "fallback_used IN (0,1)",
            name="ck_llm_fallback",
        ),
    )
    op.create_index("idx_llm_ts", "llm_invocations", ["ts"])
    op.create_index("idx_llm_model", "llm_invocations", ["model"])

    # -----------------------------------------------------------------------
    # Seed: controlled predicate vocabulary.
    # Bulk-insert via op.bulk_insert against a lightweight column spec — we
    # don't re-declare the full relation_types table here, just enough for
    # the INSERT.
    # -----------------------------------------------------------------------
    seed_table = sa.table(
        "relation_types",
        sa.column("predicate", sa.Text),
        sa.column("subject_type", sa.Text),
        sa.column("object_type", sa.Text),
        sa.column("default_conf", sa.Float),
        sa.column("description", sa.Text),
    )
    op.bulk_insert(
        seed_table,
        [
            {
                "predicate": predicate,
                "subject_type": subject,
                "object_type": obj,
                "default_conf": conf,
                "description": desc,
            }
            for predicate, subject, obj, conf, desc in _RELATION_TYPES_SEED
        ],
    )


def downgrade() -> None:
    # Drop in reverse dependency order. Indexes attached to a table go away
    # with op.drop_table(); we drop the standalone virtual tables explicitly.

    op.drop_index("idx_llm_model", table_name="llm_invocations")
    op.drop_index("idx_llm_ts", table_name="llm_invocations")
    op.drop_table("llm_invocations")

    op.drop_table("brain_merge_audit")

    op.drop_index("idx_queue_status", table_name="brain_decision_queue")
    op.drop_table("brain_decision_queue")

    op.drop_table("brain_routing_rules")
    op.drop_table("brain_attention_rules")
    op.drop_table("brain_events")

    op.drop_index("idx_edges_object", table_name="brain_edges")
    op.drop_index("idx_edges_subject", table_name="brain_edges")
    op.drop_table("brain_edges")

    # brain_chunks_vec may be either a vec0 virtual table or a plain table —
    # DROP TABLE handles both flavours on SQLite. Gate on dialect so non-
    # SQLite backends only see the plain-table form.
    if _is_sqlite():
        op.execute("DROP TABLE IF EXISTS brain_chunks_vec")
        op.execute("DROP TABLE IF EXISTS brain_chunks_fts")
    else:
        op.drop_table("brain_chunks_vec")

    op.drop_index("idx_chunks_document", table_name="brain_chunks")
    op.drop_table("brain_chunks")

    op.drop_index("idx_docs_status", table_name="brain_documents")
    op.drop_index("idx_docs_source", table_name="brain_documents")
    op.drop_index("idx_docs_ts", table_name="brain_documents")
    op.drop_index("idx_docs_project", table_name="brain_documents")
    op.drop_table("brain_documents")

    op.drop_table("brain_topics")

    op.drop_index("idx_aliases_status", table_name="brain_person_aliases")
    op.drop_index("idx_aliases_canonical", table_name="brain_person_aliases")
    op.drop_table("brain_person_aliases")

    op.drop_index("idx_brain_people_email", table_name="brain_people")
    op.drop_table("brain_people")

    op.drop_table("brain_sources")
    op.drop_table("relation_types")
