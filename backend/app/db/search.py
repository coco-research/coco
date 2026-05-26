"""Full-text search abstraction over hub_content mirror table.

SQLite: uses FTS5 on hub_content_fts virtual table (falls back to LIKE).
PostgreSQL: tsvector (future — falls back to LIKE for now).

This module is intentionally written against SA Core + the platform engine
exposed via ``app.db.session.get_db`` so that all platform.db access goes
through a single, consistent abstraction.  FTS5 MATCH is a SQLite-specific
operator; we therefore keep it as a wrapped ``text("col MATCH :q")`` clause
fed into ``select(...).where(...)`` rather than emitting raw SQL strings.
"""

import time

import structlog
from sqlalchemy import Column, func, literal_column, select, table, text

from app.db.compat import _IS_SQLITE
from app.db.session import get_db
from app.db.tables import hub_content

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# Lightweight Core handle for the FTS5 virtual table.
#
# The FTS5 virtual ``hub_content_fts`` table is created by raw DDL in init_db
# and is SQLite-only, so it is not part of the canonical ``metadata`` in
# ``tables.py``.  We declare a minimal SA Core ``table()`` here purely so we
# can join against it from a ``select(...)`` statement; the FTS5 ``MATCH``
# operator itself stays wrapped in ``text("hub_content_fts MATCH :q")``.
#
# NOTE (PG path): the PostgreSQL equivalent is ``to_tsvector(col) @@
# plainto_tsquery(:q)`` over a GIN-indexed tsvector column.  Wiring that up
# is a future task — see ``_tsvector_search`` below.
# ---------------------------------------------------------------------------

_hub_content_fts = table(
    "hub_content_fts",
    Column("rowid"),
)


def search_content(
    query: str,
    limit: int = 50,
    offset: int = 0,
    source_filter: str | None = None,
) -> dict:
    """Search hub_content using FTS5 (preferred) or LIKE (fallback).

    Returns ``{"items": [dict, ...], "total": int}``.
    """
    with get_db() as conn:
        if _IS_SQLITE:
            result = _fts5_search(conn, query, limit, offset, source_filter)
            if result is not None:
                return result
        else:
            result = _tsvector_search(conn, query, limit, offset, source_filter)
            if result is not None:
                return result

        # Reached LIKE fallback path — log for observability (slow path / missing FTS index)
        like_start = time.perf_counter()
        result = _like_search(conn, query, limit, offset, source_filter)
        like_ms = round((time.perf_counter() - like_start) * 1000, 2)
        log.warning(
            "fts5_fallback",
            query=query,
            reason="fts5_unavailable_or_failed",
            duration_ms=like_ms,
            backend="sqlite" if _IS_SQLITE else "postgres",
            source_filter=source_filter,
        )
        return result


def _fts5_search(
    conn,
    query: str,
    limit: int,
    offset: int,
    source_filter: str | None,
) -> dict | None:
    """Try FTS5 search (SQLite only). Returns None if the virtual table doesn't exist."""
    start = time.perf_counter()
    # Verify FTS5 table exists.  We probe via a SA Core select against the
    # virtual table; if it's missing SQLite raises OperationalError.
    try:
        conn.execute(select(_hub_content_fts.c.rowid).limit(1))
    except Exception as e:
        ms = round((time.perf_counter() - start) * 1000, 2)
        log.warning(
            "fts5_fallback",
            query=query,
            reason=f"missing_table:{e.__class__.__name__}",
            duration_ms=ms,
            stage="probe",
        )
        return None

    try:
        # FTS5 MATCH is a SQLite-only operator with no SA expression-level
        # representation, so we wrap it in ``text(...)`` and feed that into
        # ``select(...).where(...)`` — the rest of the query stays Core.
        #
        # PG equivalent (future task): replace with
        #   select(...).where(func.to_tsvector(...).op("@@")(func.plainto_tsquery(bindparam("q"))))
        match_clause = text("hub_content_fts MATCH :q")

        # Join hub_content c -> hub_content_fts f on rowid.  hub_content.id
        # is a TEXT primary key in the mirror; FTS5 indexes by integer rowid,
        # so we use the implicit ``rowid`` column on both sides.
        c_rowid = literal_column("c.rowid")
        f_rowid = literal_column("f.rowid")

        c = hub_content.alias("c")
        f = _hub_content_fts.alias("f")

        join_clause = c.join(f, c_rowid == f_rowid)

        where = match_clause
        params: dict = {"q": query}
        if source_filter:
            where = where & (c.c.source == source_filter)

        # --- total ---
        total_stmt = (
            select(func.count())
            .select_from(join_clause)
            .where(where)
        )
        total = conn.execute(total_stmt, params).scalar_one()

        # --- page ---
        # FTS5 exposes a hidden ``rank`` column on the virtual table; we
        # order by it ascending (lower = more relevant in FTS5's bm25).
        rank_col = literal_column("rank")
        rows_stmt = (
            select(c, rank_col)
            .select_from(join_clause)
            .where(where)
            .order_by(rank_col)
            .limit(limit)
            .offset(offset)
        )
        rows = conn.execute(rows_stmt, params).mappings().all()

        return {
            "items": [dict(r) for r in rows],
            "total": total,
        }
    except Exception as e:
        # FTS5 query syntax error (e.g. special chars) — fall back.
        ms = round((time.perf_counter() - start) * 1000, 2)
        log.warning(
            "fts5_fallback",
            query=query,
            reason=e.__class__.__name__,
            duration_ms=ms,
            stage="query",
        )
        return None


def _tsvector_search(
    conn,
    query: str,
    limit: int,
    offset: int,
    source_filter: str | None,
) -> dict | None:
    """PostgreSQL tsvector search stub.

    TODO: Implement proper tsvector search with ``to_tsvector`` /
    ``plainto_tsquery`` (or ``websearch_to_tsquery``), ``ts_rank`` for
    ordering, and a GIN index on ``hub_content``.  For now returns ``None``
    so the caller falls through to the LIKE path.
    """
    return None


def _like_search(
    conn,
    query: str,
    limit: int,
    offset: int,
    source_filter: str | None,
) -> dict:
    """Fallback LIKE search on hub_content using SA Core."""
    c = hub_content.c
    pattern = f"%{query}%"

    # Use actual DB column names via the table object.
    # hub_content.c.body maps to raw_text, hub_content.c.summary maps to processed_text
    where = (c.title.like(pattern)) | (c.body.like(pattern)) | (c.summary.like(pattern))

    if source_filter:
        where = where & (c.source == source_filter)

    total = conn.execute(
        select(func.count()).select_from(hub_content).where(where)
    ).scalar_one()

    rows = conn.execute(
        select(hub_content)
        .where(where)
        .order_by(hub_content.c.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).mappings().all()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
    }
