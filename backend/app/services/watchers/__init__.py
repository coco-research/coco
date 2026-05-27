"""Cross-platform file watchers + dead-letter queue.

Phase 10 — Crons + Watchers per `.planning/v3/backend/DESIGN.md` §8.

Components:
- `file_watcher.FileWatcherService` — uses watchdog to monitor HxStore,
  attachment cache, and project sync directories. Emits ingest requests
  to the Phase 5 ingest router.
- `dead_letter.DeadLetterQueue` — persistent retry-with-backoff for failed
  ingest tasks (and any other background job that opts in).

Both are intended to be driven by the in-proc APScheduler started during
FastAPI lifespan; they do not own their own threads outside of watchdog's
internal observer.
"""

from app.services.watchers.dead_letter import DeadLetterQueue, DLQEntry
from app.services.watchers.file_watcher import (
    FileWatcherService,
    IngestRequest,
    WatchSpec,
)

__all__ = [
    "DeadLetterQueue",
    "DLQEntry",
    "FileWatcherService",
    "IngestRequest",
    "WatchSpec",
]
