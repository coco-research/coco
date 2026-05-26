"""Human-readable ID generator for entities (e.g. CXR-47).

Supports todos, agents, tasks, decisions, and any future entity types.
Uses atomic sequence increments per node to produce unique display IDs.
Auto-generates a prefix from the node label if none is configured.

Entities without a node land in the "__global__" bucket with prefix "CXR".

The generated ID is stored in two places (kept consistent):
  - entity_identifiers (legacy join table; used for resolution)
  - <table>.human_id (direct column on todo_overrides / agents)
"""

import re
import structlog
from app.db.session import get_db

log = structlog.get_logger()


# Sentinel for entities (agents, decisions, todos) that have no real node.
GLOBAL_BUCKET_NODE_ID = "__global__"
GLOBAL_PREFIX = "CXR"

# entity_type -> (table, id_column) for column-level writeback.
_HUMAN_ID_TABLES: dict[str, tuple[str, str]] = {
    "todo": ("todo_overrides", "hub_todo_id"),
    "agent": ("agents", "id"),
}


def _auto_prefix(label: str) -> str:
    """Generate a 3-char uppercase prefix from a node label."""
    alpha = re.sub(r"[^A-Za-z]", "", label)
    if len(alpha) >= 3:
        return alpha[:3].upper()
    return (alpha + "XXX")[:3].upper()


def _get_or_create_prefix(conn, node_id: str) -> str | None:
    """Get the node's prefix, auto-generating one if absent.

    Returns the global "CXR" prefix when node_id is the global bucket sentinel.
    """
    if node_id == GLOBAL_BUCKET_NODE_ID:
        return GLOBAL_PREFIX

    row = conn.exec_driver_sql(
        "SELECT prefix, label FROM nodes WHERE id = ?", (node_id,)
    ).fetchone()
    if not row:
        return None

    rm = row._mapping
    prefix = rm["prefix"]
    if prefix:
        return prefix

    label = rm["label"] or ""
    if not label:
        return None

    prefix = _auto_prefix(label)

    conn.exec_driver_sql(
        "UPDATE nodes SET prefix = ?, updated_at = datetime('now') WHERE id = ?",
        (prefix, node_id),
    )
    return prefix


def generate_display_id(node_id: str | None, entity_type: str = "todo", entity_id: str | None = None) -> str | None:
    """Atomically increment the sequence for a node and return PREFIX-N.

    Pass node_id=None (or the GLOBAL_BUCKET_NODE_ID sentinel) for entities
    without an associated node — they will be minted under the global "CXR"
    namespace.
    """
    bucket = node_id or GLOBAL_BUCKET_NODE_ID

    with get_db() as conn:
        prefix = _get_or_create_prefix(conn, bucket)
        if not prefix:
            return None

        conn.exec_driver_sql(
            "INSERT INTO id_sequences (node_id, next_seq) VALUES (?, 1) "
            "ON CONFLICT(node_id) DO UPDATE SET next_seq = next_seq + 1",
            (bucket,),
        )
        seq_row = conn.exec_driver_sql(
            "SELECT next_seq FROM id_sequences WHERE node_id = ?", (bucket,)
        ).fetchone()
        seq = seq_row[0]

        display_id = f"{prefix}-{seq}"

        if entity_id:
            conn.exec_driver_sql(
                "INSERT OR IGNORE INTO entity_identifiers "
                "(entity_id, entity_type, node_id, sequence_num, display_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (entity_id, entity_type, bucket, seq, display_id),
            )

            # Best-effort writeback to the table's human_id column.
            target = _HUMAN_ID_TABLES.get(entity_type)
            if target:
                table, id_col = target
                try:
                    conn.exec_driver_sql(
                        f"UPDATE {table} SET human_id = ? "
                        f"WHERE {id_col} = ? AND human_id IS NULL",
                        (display_id, entity_id),
                    )
                except Exception as e:
                    log.warning("human_id_writeback_failed", entity_type=entity_type, error=str(e))

        return display_id


def assign_display_id(entity_id: str, node_id: str | None, entity_type: str = "todo") -> str | None:
    """Assign a human-readable display ID to an entity and persist the mapping."""
    display_id = generate_display_id(node_id, entity_type=entity_type, entity_id=entity_id)
    if display_id:
        log.info("display_id_assigned", entity_id=entity_id, entity_type=entity_type, display_id=display_id)
    return display_id


def resolve_display_id(display_id: str) -> dict | None:
    """Resolve a human-readable ID (e.g. 'CXR-47') to entity details."""
    with get_db() as conn:
        row = conn.exec_driver_sql(
            "SELECT entity_id, entity_type, node_id, display_id FROM entity_identifiers WHERE display_id = ?",
            (display_id.upper(),),
        ).fetchone()
        if row:
            return dict(row._mapping)

        row = conn.exec_driver_sql(
            "SELECT entity_id, entity_type, node_id, display_id FROM entity_identifiers WHERE UPPER(display_id) = UPPER(?)",
            (display_id,),
        ).fetchone()
        return dict(row._mapping) if row else None
