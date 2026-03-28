"""get_db() context manager -- the single entry point for SA Core queries.

Usage::

    from app.db.session import get_db

    with get_db() as conn:
        conn.execute(insert(agents).values(id=id, name=name))
        # auto-commits on successful exit, auto-rolls-back on exception
"""

from contextlib import contextmanager
from sqlalchemy import Connection
from app.db.engine import engine


@contextmanager
def get_db() -> Connection:
    """Yield a SA Connection inside a transaction.

    * On normal exit the transaction is **committed**.
    * On exception the transaction is **rolled back** and the exception
      re-raised.
    """
    with engine.connect() as conn:
        with conn.begin():
            yield conn
