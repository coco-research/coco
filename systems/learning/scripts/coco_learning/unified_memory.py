"""Coco Unified Memory — Cross-Agent Context Vault.

Provides a shared context vault that all agents can read from and write to.
Bridges Learning System instincts with Brain DB decisions and makes both
available as structured context during agent execution.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import Instinct
from .storage import list_instincts


DEFAULT_VAULT_DB_REL = ".coco/memory/vault.db"


def _vault_db_path(project_root: Optional[str] = None) -> Path:
    """Resolve the vault DB path."""
    env = os.environ.get("COCO_VAULT_DB")
    if env:
        return Path(env)
    base = Path(project_root) if project_root else Path.home()
    return base / DEFAULT_VAULT_DB_REL


def init_vault(project_root: Optional[str] = None) -> Path:
    """Create or verify the vault DB schema. Returns the DB path."""
    db_path = _vault_db_path(project_root)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS context_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            domain TEXT,
            content TEXT NOT NULL,
            relevance_score REAL DEFAULT 0.0,
            project_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            tags TEXT DEFAULT '[]'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            agent_role TEXT,
            entry_ids TEXT,
            accessed_at TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_context_project
        ON context_entries(project_id, domain)
    """)
    conn.commit()
    conn.close()
    return db_path


def upsert_entry(
    source: str,
    source_id: str,
    domain: str,
    content: str,
    project_id: str,
    relevance_score: float = 0.5,
    tags: Optional[list[str]] = None,
    project_root: Optional[str] = None,
) -> int:
    """Insert or update a context entry. Returns the entry ID."""
    db_path = init_vault(project_root)
    now = datetime.now(timezone.utc).isoformat()
    tags_json = json.dumps(tags or [])

    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute(
        "SELECT id FROM context_entries WHERE source=? AND source_id=?",
        (source, source_id),
    )
    row = c.fetchone()
    if row:
        entry_id = row[0]
        c.execute(
            """UPDATE context_entries
               SET domain=?, content=?, relevance_score=?, project_id=?,
                   updated_at=?, tags=?
               WHERE id=?""",
            (domain, content, relevance_score, project_id, now, tags_json, entry_id),
        )
    else:
        c.execute(
            """INSERT INTO context_entries
               (source, source_id, domain, content, relevance_score,
                project_id, created_at, updated_at, tags)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source, source_id, domain, content, relevance_score,
             project_id, now, now, tags_json),
        )
        entry_id = c.lastrowid
    conn.commit()
    conn.close()
    return entry_id


def resolve_context(
    project_id: str,
    role: str = "",
    task_description: str = "",
    limit: int = 10,
    project_root: Optional[str] = None,
    session_id: str = "",
) -> list[dict]:
    """Resolve relevant context entries for an agent invocation.

    Returns a list of dicts with keys: id, source, domain, content, score, tags.
    """
    db_path = _vault_db_path(project_root)
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        """SELECT id, source, source_id, domain, content, relevance_score, tags
           FROM context_entries
           WHERE project_id = ?
           ORDER BY relevance_score DESC, updated_at DESC
           LIMIT ?""",
        (project_id, limit),
    )
    rows = c.fetchall()
    conn.close()

    results = []
    entry_ids = []
    for r in rows:
        entry = {
            "id": r["id"],
            "source": r["source"],
            "source_id": r["source_id"],
            "domain": r["domain"],
            "content": r["content"],
            "score": r["relevance_score"],
            "tags": json.loads(r["tags"]) if r["tags"] else [],
        }
        results.append(entry)
        entry_ids.append(str(r["id"]))

    # Log access if session provided
    if session_id and entry_ids:
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO access_log (session_id, agent_role, entry_ids, accessed_at) VALUES (?, ?, ?, ?)",
            (session_id, role, json.dumps(entry_ids), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()

    return results


def sync_all_sources(
    project_id: str,
    project_root: Optional[str] = None,
) -> dict:
    """Sync instincts and brain decisions into the unified vault.

    Returns counts of synced entries per source.
    """
    stats = {"instincts": 0, "decisions": 0}

    # Sync instincts
    instincts = list_instincts(project_id)
    for inst in instincts:
        if inst.superseded_by:
            continue
        content = f"{inst.pattern} (confidence={inst.confidence:.2f}, evidence={inst.evidence_count})"
        upsert_entry(
            source="instinct",
            source_id=inst.id,
            domain=inst.domain,
            content=content,
            project_id=project_id,
            relevance_score=inst.confidence,
            tags=["coco-learning"] + inst.tags,
            project_root=project_root,
        )
        stats["instincts"] += 1

    # Sync brain decisions if DB exists
    brain_db_candidates = [
        Path(project_root or "") / ".brain" / "brain.db",
        Path(os.environ.get("COCO_BRAIN_DB", "")),
    ]
    brain_db = next((p for p in brain_db_candidates if p.exists()), None)
    if brain_db:
        try:
            conn = sqlite3.connect(str(brain_db))
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='decisions'"
            )
            if c.fetchone():
                c.execute("SELECT * FROM decisions WHERE tags LIKE '%coco-learning%'")
                for row in c.fetchall():
                    upsert_entry(
                        source="decision",
                        source_id=str(row["id"]),
                        domain="workflow",
                        content=f"{row['title']}: {row['content']}",
                        project_id=project_id,
                        relevance_score=0.6 if row["status"] == "accepted" else 0.4,
                        tags=json.loads(row["tags"]) if row["tags"] else ["coco-learning"],
                        project_root=project_root,
                    )
                    stats["decisions"] += 1
            conn.close()
        except sqlite3.Error:
            pass

    return stats


def format_context_block(entries: list[dict]) -> str:
    """Render resolved context entries into a prompt-friendly block."""
    if not entries:
        return ""
    lines = ["<unified_memory>"]
    for e in entries:
        tags_str = ", ".join(e["tags"]) if e["tags"] else ""
        lines.append(f"- [{e['source']}:{e['domain']}] {e['content']}")
        if tags_str:
            lines.append(f"  tags: {tags_str}")
    lines.append("</unified_memory>")
    return "\n".join(lines)
