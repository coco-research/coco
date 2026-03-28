import sqlite3
from contextlib import contextmanager
from pathlib import Path
from app.config import HUB_DB_PATH, PLATFORM_DB_PATH

def _connect(path: Path, read_only: bool = False) -> sqlite3.Connection:
    uri = f"file:{path}{'?mode=ro' if read_only else ''}"
    conn = sqlite3.connect(uri, uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def get_hub_db():
    conn = _connect(HUB_DB_PATH, read_only=True)
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_platform_db():
    conn = _connect(PLATFORM_DB_PATH, read_only=False)
    try:
        yield conn
    finally:
        conn.close()
