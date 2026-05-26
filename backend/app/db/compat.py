"""Dialect-aware database compatibility helpers.

Provides functions that emit the correct SQL for both SQLite and PostgreSQL
so query code stays dialect-agnostic. Used to replace raw ``text()`` calls
scattered across routers/services.

Most helpers accept an optional ``engine`` argument; when omitted they fall
back to the process-wide platform engine from :mod:`app.db.engine`. This lets
the helpers work against ``hub.db`` (read-only) or test engines without
touching their callers.

Usage::

    from app.db.compat import now, days_ago, upsert, json_extract, ilike

    stmt = select(agents).where(agents.c.created_at >= days_ago(7))
    stmt = upsert(agents, {...}, conflict_columns=["id"], update_columns=["name"])
    stmt = select(t).where(ilike(t.c.name, "%foo%"))
    stmt = select(json_extract(t.c.meta, "user.name").label("user_name"))
"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence, Union

from sqlalchemy import Column, Table, cast, func, text
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.engine import Engine
from sqlalchemy.sql import ColumnElement, Select
from sqlalchemy.types import String

from app.db.engine import engine as _default_engine

# ---------------------------------------------------------------------------
# Dialect detection
# ---------------------------------------------------------------------------


def _resolve(engine: Optional[Engine]) -> Engine:
    """Return ``engine`` if provided, else the platform default engine."""
    return engine if engine is not None else _default_engine


def is_sqlite(engine: Optional[Engine] = None) -> bool:
    """Return True if ``engine`` (or the default engine) targets SQLite."""
    return _resolve(engine).url.get_backend_name() == "sqlite"


def is_pg(engine: Optional[Engine] = None) -> bool:
    """Return True if ``engine`` (or the default engine) targets PostgreSQL."""
    name = _resolve(engine).url.get_backend_name()
    return name in ("postgresql", "postgres")


# Module-level constant kept for backwards compatibility with helpers below.
_IS_SQLITE: bool = is_sqlite()


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------


def now(engine: Optional[Engine] = None):
    """Current UTC timestamp expression.

    SQLite  -> ``datetime('now')``
    Postgres-> ``now()``
    """
    if is_sqlite(engine):
        return func.datetime("now")
    return func.now()


def current_timestamp(engine: Optional[Engine] = None):
    """Alias for :func:`now` — matches the SQL standard keyword."""
    return now(engine)


def days_ago(n: int, engine: Optional[Engine] = None):
    """Timestamp ``n`` days before the current moment.

    SQLite  -> ``datetime('now', '-N days')``
    Postgres-> ``now() - INTERVAL 'N days'``
    """
    if is_sqlite(engine):
        return func.datetime("now", f"-{n} days")
    return func.now() - text(f"INTERVAL '{n} days'")


def today(engine: Optional[Engine] = None):
    """Current date (no time component).

    SQLite  -> ``date('now')``
    Postgres-> ``current_date``
    """
    if is_sqlite(engine):
        return func.date("now")
    return func.current_date()


def date_trunc_day(col: Union[Column, ColumnElement], engine: Optional[Engine] = None):
    """Truncate a timestamp column to date granularity for ``GROUP BY``.

    SQLite  -> ``date(col)``
    Postgres-> ``date_trunc('day', col)``
    """
    if is_sqlite(engine):
        return func.date(col)
    return func.date_trunc("day", col)


def start_of_month(engine: Optional[Engine] = None):
    """First moment of the current month.

    SQLite  -> ``date('now', 'start of month')``
    Postgres-> ``date_trunc('month', now())``
    """
    if is_sqlite(engine):
        return func.date("now", "start of month")
    return func.date_trunc("month", func.now())


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def json_extract(
    col: Union[Column, ColumnElement],
    path: str,
    *,
    as_text: bool = True,
    engine: Optional[Engine] = None,
) -> ColumnElement:
    """Portable JSON field extraction.

    ``path`` is a dotted accessor (``"user.name"`` or ``"items[0].id"``).
    The function rewrites it to each dialect's native syntax.

    SQLite  -> ``json_extract(col, '$.user.name')``
    Postgres-> ``col #>> '{user,name}'`` (text) or ``col #> '{user,name}'`` (json)

    Parameters
    ----------
    col:
        JSON / JSONB column or expression.
    path:
        Dotted access path. Numeric segments and ``[N]`` indices work too.
    as_text:
        When True (default) return the value as TEXT. When False, return the
        nested JSON value (Postgres) or the raw ``json_extract`` result
        (SQLite — which already returns the underlying type).
    """
    if is_sqlite(engine):
        json_path = "$." + path.replace("[", ".").replace("]", "")
        # Strip accidental double-dots from ``foo[0]`` -> ``foo.0`` transform.
        json_path = json_path.replace("..", ".")
        return func.json_extract(col, json_path)

    # Postgres: split path into segments understood by ``#>``/``#>>``.
    segments: list[str] = []
    for part in path.replace("]", "").split("."):
        for seg in part.split("["):
            if seg:
                segments.append(seg)
    pg_path = "{" + ",".join(segments) + "}"
    op = "#>>" if as_text else "#>"
    # ``op_text`` ensures the operator is rendered literally rather than as a
    # bound parameter.
    return col.op(op)(text(f"'{pg_path}'"))


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------


def ilike(
    col: Union[Column, ColumnElement],
    pattern: str,
    engine: Optional[Engine] = None,
) -> ColumnElement:
    """Case-insensitive ``LIKE``.

    SQLite's ``LIKE`` is case-insensitive for ASCII by default (with the stock
    build) but **not** for Unicode. To behave consistently we lower-case both
    sides on SQLite. On Postgres we use the native ``ILIKE`` operator.
    """
    if is_sqlite(engine):
        return func.lower(cast(col, String)).like(pattern.lower())
    return col.ilike(pattern)


# ---------------------------------------------------------------------------
# Ordering helpers
# ---------------------------------------------------------------------------


def nulls_last(col: Union[Column, ColumnElement], engine: Optional[Engine] = None):
    """``ORDER BY col NULLS LAST`` — portable.

    SQLite (<3.30 lacks NULLS LAST) -> ``CASE WHEN col IS NULL THEN 1 ELSE 0 END, col``
    Postgres                        -> ``col NULLS LAST``

    The SQLite branch returns a *tuple* of expressions; spread it into
    ``order_by`` with ``*``::

        stmt = stmt.order_by(*nulls_last(t.c.updated_at))

    On Postgres a single expression is returned; spreading still works because
    Python unpacks a 1-tuple.
    """
    if is_sqlite(engine):
        from sqlalchemy import case

        null_first = case((col.is_(None), 1), else_=0)
        return (null_first, col)
    return (col.nulls_last(),)


def nulls_first(col: Union[Column, ColumnElement], engine: Optional[Engine] = None):
    """``ORDER BY col NULLS FIRST`` — portable. See :func:`nulls_last`."""
    if is_sqlite(engine):
        from sqlalchemy import case

        null_first = case((col.is_(None), 0), else_=1)
        return (null_first, col)
    return (col.nulls_first(),)


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------


def paginate(
    stmt: Select,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Select:
    """Apply ``LIMIT`` / ``OFFSET`` to a Select in a dialect-neutral way.

    SQLAlchemy already emits portable SQL for ``stmt.limit().offset()``; this
    helper exists purely to centralize None-handling so callers don't pepper
    routers with conditionals.
    """
    if limit is not None:
        stmt = stmt.limit(limit)
    if offset is not None:
        stmt = stmt.offset(offset)
    return stmt


# ---------------------------------------------------------------------------
# Upsert helper
# ---------------------------------------------------------------------------


def upsert(
    table: Table,
    values: dict[str, Any],
    conflict_columns: Sequence[str],
    update_columns: Sequence[str],
    engine: Optional[Engine] = None,
):
    """Build a dialect-aware ``INSERT ... ON CONFLICT DO UPDATE`` statement.

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
    engine:
        Optional engine override for dialect detection.

    Returns
    -------
    An executable insert statement with ``on_conflict_do_update`` applied.
    """
    if is_sqlite(engine):
        stmt = sqlite.insert(table).values(**values)
    else:
        stmt = postgresql.insert(table).values(**values)
    return stmt.on_conflict_do_update(
        index_elements=list(conflict_columns),
        set_={col: stmt.excluded[col] for col in update_columns},
    )


__all__ = [
    "is_sqlite",
    "is_pg",
    "now",
    "current_timestamp",
    "days_ago",
    "today",
    "date_trunc_day",
    "start_of_month",
    "json_extract",
    "ilike",
    "nulls_last",
    "nulls_first",
    "paginate",
    "upsert",
]
