"""Human-readable ID generator for todos (e.g. CXR-47).

Uses atomic sequence increments per node to produce unique display IDs.
"""

import structlog
from app.db.connections import get_platform_db

log = structlog.get_logger()


def generate_display_id(node_id: str) -> str | None:
    """Atomically increment the sequence for a node and return PREFIX-N.

    Returns None if the node has no prefix configured.
    """
    with get_platform_db() as db:
        # Get the node's prefix
        row = db.execute(
            "SELECT prefix FROM nodes WHERE id = ?", (node_id,)
        ).fetchone()
        if not row or not row["prefix"]:
            return None

        prefix = row["prefix"]

        # Upsert into id_sequences and atomically get next value
        db.execute(
            "INSERT INTO id_sequences (node_id, next_seq) VALUES (?, 1) "
            "ON CONFLICT(node_id) DO UPDATE SET next_seq = next_seq + 1",
            (node_id,),
        )
        seq_row = db.execute(
            "SELECT next_seq FROM id_sequences WHERE node_id = ?", (node_id,)
        ).fetchone()
        seq = seq_row["next_seq"]

        # The value we just set via upsert is the one to use.
        # On first insert it's 1; on conflict it was incremented.
        # But we need to handle the first-insert case: next_seq is 1 and that's
        # the ID we hand out, then bump to 2 for the next call.
        # Actually the upsert sets next_seq=1 on first insert, then on subsequent
        # calls it increments. So the sequence handed out should be the current value,
        # and we should post-increment for next time.
        # Let's simplify: read, use, then bump.

        db.execute(
            "UPDATE id_sequences SET next_seq = ? WHERE node_id = ?",
            (seq + 1, node_id),
        )
        db.commit()

        return f"{prefix}-{seq}"


def assign_display_id(hub_todo_id: str, node_id: str) -> str | None:
    """Assign a human-readable display ID to a todo and persist the mapping.

    Returns the display_id (e.g. 'CXR-47') or None if the node has no prefix.
    """
    display_id = generate_display_id(node_id)
    if not display_id:
        return None

    # Extract sequence number from display_id
    seq_num = int(display_id.rsplit("-", 1)[1])

    with get_platform_db() as db:
        db.execute(
            "INSERT OR IGNORE INTO todo_identifiers (hub_todo_id, node_id, sequence_num, display_id) "
            "VALUES (?, ?, ?, ?)",
            (hub_todo_id, node_id, seq_num, display_id),
        )
        db.commit()

    log.info("display_id_assigned", hub_todo_id=hub_todo_id, display_id=display_id)
    return display_id


def resolve_display_id(display_id: str) -> str | None:
    """Resolve a human-readable ID (e.g. 'CXR-47') to the hub_todo_id.

    Returns the hub_todo_id or None if not found.
    """
    with get_platform_db() as db:
        row = db.execute(
            "SELECT hub_todo_id FROM todo_identifiers WHERE display_id = ?",
            (display_id.upper(),),
        ).fetchone()
        if row:
            return row["hub_todo_id"]

        # Try case-insensitive match
        row = db.execute(
            "SELECT hub_todo_id FROM todo_identifiers WHERE UPPER(display_id) = UPPER(?)",
            (display_id,),
        ).fetchone()
        return row["hub_todo_id"] if row else None
