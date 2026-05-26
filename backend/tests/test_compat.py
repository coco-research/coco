"""Tests for app.db.compat — portable SQL helpers.

The SQLite branch is exercised against an in-memory database. The Postgres
branch is exercised only when a ``TEST_PG_URL`` environment variable points
at a reachable instance; otherwise those parametrized cases are skipped.
"""
from __future__ import annotations

import os

import pytest
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    select,
)
from sqlalchemy.engine import Engine

from app.db import compat

# ---------------------------------------------------------------------------
# Engine fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def sqlite_engine() -> Engine:
    """Throwaway in-memory SQLite engine for compat tests."""
    return create_engine("sqlite:///:memory:")


@pytest.fixture(scope="module")
def pg_engine() -> Engine:
    """Optional Postgres engine — skipped when TEST_PG_URL is not set."""
    url = os.environ.get("TEST_PG_URL")
    if not url:
        pytest.skip("TEST_PG_URL not set; skipping Postgres compat tests")
    eng = create_engine(url)
    try:
        with eng.connect() as conn:
            conn.execute(compat.text("SELECT 1"))  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"Postgres unreachable ({exc}); skipping")
    return eng


def _engines(request):
    """Parametrize over available engines; PG is skipped if unavailable."""
    name = request.param
    if name == "sqlite":
        return request.getfixturevalue("sqlite_engine")
    return request.getfixturevalue("pg_engine")


@pytest.fixture
def engine(request) -> Engine:
    return _engines(request)


# ---------------------------------------------------------------------------
# Dialect detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("engine", ["sqlite"], indirect=True)
def test_dialect_detection_sqlite(engine: Engine) -> None:
    assert compat.is_sqlite(engine) is True
    assert compat.is_pg(engine) is False


@pytest.mark.parametrize("engine", ["pg"], indirect=True)
def test_dialect_detection_pg(engine: Engine) -> None:  # pragma: no cover
    assert compat.is_pg(engine) is True
    assert compat.is_sqlite(engine) is False


# ---------------------------------------------------------------------------
# Timestamp helpers — execute and confirm we get a value back
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("engine", ["sqlite", "pg"], indirect=True)
def test_now_executes(engine: Engine) -> None:
    with engine.connect() as conn:
        value = conn.execute(select(compat.now(engine))).scalar_one()
    assert value is not None


@pytest.mark.parametrize("engine", ["sqlite", "pg"], indirect=True)
def test_days_ago_executes(engine: Engine) -> None:
    with engine.connect() as conn:
        past = conn.execute(select(compat.days_ago(7, engine))).scalar_one()
        present = conn.execute(select(compat.now(engine))).scalar_one()
    assert past is not None and present is not None
    # String comparison works for ISO-formatted timestamps in both backends.
    assert str(past) < str(present)


@pytest.mark.parametrize("engine", ["sqlite", "pg"], indirect=True)
def test_today_executes(engine: Engine) -> None:
    with engine.connect() as conn:
        value = conn.execute(select(compat.today(engine))).scalar_one()
    assert value is not None


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("engine", ["sqlite"], indirect=True)
def test_json_extract_sqlite(engine: Engine) -> None:
    meta = MetaData()
    t = Table(
        "items_json",
        meta,
        Column("id", Integer, primary_key=True),
        Column("payload", Text),
    )
    meta.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            t.insert(),
            [{"id": 1, "payload": '{"user": {"name": "alice"}, "n": 7}'}],
        )
        name = conn.execute(
            select(compat.json_extract(t.c.payload, "user.name", engine=engine))
        ).scalar_one()
    assert name == "alice"


# ---------------------------------------------------------------------------
# ILIKE
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("engine", ["sqlite", "pg"], indirect=True)
def test_ilike_case_insensitive(engine: Engine) -> None:
    meta = MetaData()
    t = Table(
        "people_ilike",
        meta,
        Column("id", Integer, primary_key=True),
        Column("name", String(64)),
    )
    meta.create_all(engine)
    try:
        with engine.begin() as conn:
            conn.execute(t.insert(), [{"id": 1, "name": "Alice"}, {"id": 2, "name": "BOB"}])
            rows = (
                conn.execute(select(t.c.id).where(compat.ilike(t.c.name, "%bob%", engine=engine)))
                .scalars()
                .all()
            )
        assert rows == [2]
    finally:
        meta.drop_all(engine)


# ---------------------------------------------------------------------------
# NULLS LAST
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("engine", ["sqlite", "pg"], indirect=True)
def test_nulls_last_ordering(engine: Engine) -> None:
    meta = MetaData()
    t = Table(
        "events_nl",
        meta,
        Column("id", Integer, primary_key=True),
        Column("priority", Integer),
    )
    meta.create_all(engine)
    try:
        with engine.begin() as conn:
            conn.execute(
                t.insert(),
                [
                    {"id": 1, "priority": 2},
                    {"id": 2, "priority": None},
                    {"id": 3, "priority": 1},
                ],
            )
            ordered = (
                conn.execute(select(t.c.id).order_by(*compat.nulls_last(t.c.priority, engine=engine)))
                .scalars()
                .all()
            )
        # Non-nulls come first; the NULL row must be at the end.
        assert ordered[-1] == 2
    finally:
        meta.drop_all(engine)


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("engine", ["sqlite", "pg"], indirect=True)
def test_paginate_applies_limit_offset(engine: Engine) -> None:
    meta = MetaData()
    t = Table(
        "rows_pg",
        meta,
        Column("id", Integer, primary_key=True),
    )
    meta.create_all(engine)
    try:
        with engine.begin() as conn:
            conn.execute(t.insert(), [{"id": i} for i in range(1, 11)])
            stmt = compat.paginate(select(t.c.id).order_by(t.c.id), limit=3, offset=2)
            ids = conn.execute(stmt).scalars().all()
        assert ids == [3, 4, 5]
    finally:
        meta.drop_all(engine)


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("engine", ["sqlite", "pg"], indirect=True)
def test_upsert_insert_then_update(engine: Engine) -> None:
    meta = MetaData()
    t = Table(
        "agents_up",
        meta,
        Column("id", String(32), primary_key=True),
        Column("name", String(64)),
    )
    meta.create_all(engine)
    try:
        with engine.begin() as conn:
            stmt = compat.upsert(
                t,
                {"id": "a1", "name": "first"},
                conflict_columns=["id"],
                update_columns=["name"],
                engine=engine,
            )
            conn.execute(stmt)

            stmt = compat.upsert(
                t,
                {"id": "a1", "name": "second"},
                conflict_columns=["id"],
                update_columns=["name"],
                engine=engine,
            )
            conn.execute(stmt)

            name = conn.execute(select(t.c.name).where(t.c.id == "a1")).scalar_one()
        assert name == "second"
    finally:
        meta.drop_all(engine)
