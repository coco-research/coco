"""Utilities for node-tree (materialized path) queries."""

from __future__ import annotations

import sqlite3


def get_subtree_node_ids(db: sqlite3.Connection, node_id: str) -> list[str]:
    """Get all node IDs in the subtree rooted at *node_id* (inclusive).

    Uses the materialized ``path`` column on the ``nodes`` table.
    If the node is not found, falls back to returning ``[node_id]`` so callers
    can still filter safely.
    """
    row = db.execute("SELECT path FROM nodes WHERE id = ?", (node_id,)).fetchone()
    if not row:
        return [node_id]
    path = row["path"] if isinstance(row, sqlite3.Row) else row[0]
    rows = db.execute(
        "SELECT id FROM nodes WHERE path LIKE ? || '%'", (path,)
    ).fetchall()
    return [r["id"] if isinstance(r, sqlite3.Row) else r[0] for r in rows]


def build_node_id_filter(
    db: sqlite3.Connection,
    node_id: str | None,
    subtree: bool,
    column: str = "node_id",
) -> tuple[str, list[str]]:
    """Return a SQL fragment and params list for node-based filtering.

    Returns (sql_fragment, params) where *sql_fragment* is either empty or a
    clause like ``"node_id IN (?, ?, ?)"`` (without WHERE/AND prefix) so
    callers can integrate it into their own condition lists.
    """
    if not node_id:
        return ("", [])

    if subtree:
        ids = get_subtree_node_ids(db, node_id)
        placeholders = ", ".join("?" for _ in ids)
        return (f"{column} IN ({placeholders})", ids)

    return (f"{column} = ?", [node_id])
