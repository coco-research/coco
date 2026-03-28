from pathlib import Path
import os

COCO_DIR = Path(os.getenv("COCO_DIR", str(Path.home() / ".coco")))
HUB_DIR = Path(os.getenv("HUB_DIR", str(Path.home() / ".hub")))

HUB_DB_PATH = HUB_DIR / "hub.db"
PLATFORM_DB_PATH = COCO_DIR / "platform.db"
BRAIN_JSON_PATH = COCO_DIR / "brain.json"
QUEUE_JSON_PATH = COCO_DIR / "queue.json"
CONFIG_JSON_PATH = COCO_DIR / "config.json"
EVENTS_JSONL_PATH = COCO_DIR / "events.jsonl"
SESSIONS_DIR = COCO_DIR / "sessions"
LOGS_DIR = COCO_DIR / "logs"

PLATFORM_PORT = int(os.getenv("PLATFORM_PORT", "8000"))
MAX_CONCURRENT_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", "3"))
AGENT_TIMEOUT_MINUTES = int(os.getenv("AGENT_TIMEOUT_MINUTES", "30"))
CHAT_TIMEOUT_MINUTES = int(os.getenv("CHAT_TIMEOUT_MINUTES", "5"))
