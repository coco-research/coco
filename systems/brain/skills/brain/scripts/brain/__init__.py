"""Project Brain — SQLite knowledge tracker for project folders."""

from pathlib import Path

VERSION = "0.1.0"
SCHEMA_VERSION = 6
DB_FILENAME = "project_brain.db"


def resolve_db_path(explicit_path: str | None = None) -> Path:
    """Resolve the brain DB path. Walks up from cwd if not given explicitly."""
    if explicit_path:
        return Path(explicit_path)
    # Walk up from cwd looking for an existing DB
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / DB_FILENAME
        if candidate.exists():
            return candidate
        # Stop at home directory
        if parent == Path.home():
            break
    # Default: create in cwd
    return current / DB_FILENAME
