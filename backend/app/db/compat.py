"""Dialect-aware database compatibility helpers.

Provides functions that emit the correct SQL for both SQLite and
PostgreSQL so that query code stays dialect-agnostic.

Usage::

    from app.db.compat import now, days_ago, upsert

    stmt = select(agents).where(agents.c.created_at >= days_ago(7))
    stmt = upsert(agents, {...}, conflict_columns=["id"], update_columns=["name"])
"""

from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import Column, Table, func, text
from sqlalchemy.dialects import postgresql, sqlite

from app.db.engine import engine

# ---------------------------------------------------------------------------
# Dialect detection
# ---------------------------------------------------------------------------

_IS_SQLITE: bool = engine.url.get_backend_name() == "sqlite"


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------


def now():
    """Current UTC timestamp expression.

    SQLite  -> datetime('now')
    PG      -> now()
    """
    if _IS_SQLITE:
        return func.datetime("now")
    return func.now()


def days_ago(n: int):
    """Timestamp N days before the current moment.

    SQLite  -> datetime('now', '-N days')
    PG      -> now() - INTERVAL 'N days'
    """
    if _IS_SQLITE:
        return func.datetime("now", f"-{n} days")
    return func.now() - text(f"INTERVAL '{n} days'")


def today():
    """Current date (no time component).

    SQLite  -> date('now')
    PG      -> current_date
    """
    if _IS_SQLITE:
        return func.date("now")
    return func.current_date()


def date_trunc_day(col: Column):
    """Truncate a timestamp column to date granularity for GROUP BY.

    SQLite  -> date(col)
    PG      -> date_trunc('day', col)
    """
    if _IS_SQLITE:
        return func.date(col)
    return func.date_trunc("day", col)


# ---------------------------------------------------------------------------
# Upsert helper
# ---------------------------------------------------------------------------


def upsert(
    table: Table,
    values: dict[str, Any],
    conflict_columns: Sequence[str],
    update_columns: Sequence[str],
):
    """Build a dialect-aware INSERT ... ON CONFLICT DO UPDATE statement.

    Parameters
    ----------
    table:
        SA Table object to insert into.
    values:
        Column-name -> value mapping for the INSERT.
    conflict_columns:
        Columns that form the uniqueness constraint (e.g. ``["id"]``).
    update_columns:
        Columns to SET on conflict (taken from the excluded/inserted row).

    Returns
    -------
    An executable insert statement with ``on_conflict_do_update`` applied.
    """
    if _IS_SQLITE:
        stmt = sqlite.insert(table).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns,
            set_={col: stmt.excluded[col] for col in update_columns},
        )
    else:
        stmt = postgresql.insert(table).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns,
            set_={col: stmt.excluded[col] for col in update_columns},
        )
    return stmt
