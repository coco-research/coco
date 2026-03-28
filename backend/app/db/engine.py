"""SQLAlchemy engine singleton for platform.db.

All SA Core queries go through this engine.  The engine is configured
with WAL journal mode, busy_timeout, and foreign keys to match the
existing sqlite3 connection settings in connections.py.
"""

from sqlalchemy import create_engine, event
from app.config import PLATFORM_DB_PATH

_url = f"sqlite:///{PLATFORM_DB_PATH}"

engine = create_engine(
    _url,
    connect_args={"timeout": 10},
    pool_pre_ping=True,
    # SQLite uses NullPool by default in SA, which is fine for us
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, connection_record):
    """Mirror the PRAGMA settings from connections._connect."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
