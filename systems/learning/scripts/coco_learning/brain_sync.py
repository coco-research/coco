"""Coco Learning System — Brain DB decisions sync.

Syncs high-confidence instincts to the Brain DB as decisions,
creating a durable record of learned behaviors in the project knowledge graph.

Brain DB schema reference: systems/brain/skills/brain/scripts/brain/schema.py
Decision fields: id, title, content, status, created_at, tags
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


# Default Brain DB path relative to project root
DEFAULT_BRAIN_DB_REL = ".brain/brain.db"


def _find_brain_db(project_root: Optional[str] = None) -> Optional[Path]:
    """Locate the Brain DB SQLite file for a project."""
    if project_root:
        db_path = Path(project_root) / DEFAULT_BRAIN_DB_REL
        if db_path.exists():
            return db_path
    
    # Try current working directory
    cwd_db = Path.cwd() / DEFAULT_BRAIN_DB_REL
    if cwd_db.exists():
        return cwd_db
    
    # Check environment override
    env_db = os.environ.get("COCO_BRAIN_DB")
    if env_db and Path(env_db).exists():
        return Path(env_db)
    
    return None


def instinct_to_decision(instinct: Instinct) -> dict:
    """Convert an Instinct to a Brain DB decision record."""
    return {
        "title": f"[{instinct.domain}] {instinct.pattern}",
        "content": (
            f"Learned behavior from {instinct.evidence_count} observations.\n"
            f"Confidence: {instinct.confidence:.2f} ({instinct.state})\n"
            f"Source project: {instinct.source_project}\n"
            f"Tags: {', '.join(instinct.tags)}"
        ),
        "status": "accepted" if instinct.confidence >= 0.7 else "proposed",
        "tags": json.dumps(["coco-learning", instinct.domain] + instinct.tags),
    }


def sync_instincts_to_brain(
    project_id: Optional[str] = None,
    min_confidence: float = 0.5,
    project_root: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """Sync eligible instincts to Brain DB as decisions.
    
    Args:
        project_id: Project scope for instincts (None = global only)
        min_confidence: Minimum confidence threshold for sync
        project_root: Path to project root for Brain DB lookup
        dry_run: If True, report what would be synced without writing
        
    Returns:
        Dict with 'synced', 'skipped', 'errors', 'decisions' keys
    """
    result = {
        "synced": 0,
        "skipped": 0,
        "errors": [],
        "decisions": [],
    }
    
    # Find Brain DB
    db_path = _find_brain_db(project_root)
    if db_path is None:
        result["errors"].append("Brain DB not found; skipping sync")
        return result
    
    # Load eligible instincts
    instincts = list_instincts(project_id)
    eligible = [i for i in instincts if i.confidence >= min_confidence and not i.superseded_by]
    
    if not eligible:
        return result
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Ensure decisions table exists (idempotent)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                status TEXT DEFAULT 'proposed',
                created_at TEXT,
                tags TEXT
            )
        """)
        
        for instinct in eligible:
            decision = instinct_to_decision(instinct)
            
            # Check if already synced (by title match)
            cursor.execute(
                "SELECT id FROM decisions WHERE title = ? AND tags LIKE '%coco-learning%'",
                (decision["title"],)
            )
            existing = cursor.fetchone()
            
            if existing:
                result["skipped"] += 1
                continue
            
            if dry_run:
                result["decisions"].append(decision)
                result["synced"] += 1
            else:
                cursor.execute(
                    "INSERT INTO decisions (title, content, status, created_at, tags) VALUES (?, ?, ?, ?, ?)",
                    (
                        decision["title"],
                        decision["content"],
                        decision["status"],
                        datetime.now(timezone.utc).isoformat(),
                        decision["tags"],
                    )
                )
                result["synced"] += 1
                result["decisions"].append(decision)
        
        conn.commit()
        conn.close()
        
    except sqlite3.Error as e:
        result["errors"].append(f"Database error: {e}")
    
    return result


def get_sync_status(project_root: Optional[str] = None) -> dict:
    """Get current sync status between instincts and Brain DB."""
    result = {
        "brain_db_found": False,
        "total_decisions": 0,
        "learning_decisions": 0,
        "eligible_instincts": 0,
    }
    
    db_path = _find_brain_db(project_root)
    if db_path is None:
        return result
    
    result["brain_db_found"] = True
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if decisions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='decisions'"
        )
        if not cursor.fetchone():
            conn.close()
            return result
        
        cursor.execute("SELECT COUNT(*) FROM decisions")
        result["total_decisions"] = cursor.fetchone()[0]
        
        cursor.execute(
            "SELECT COUNT(*) FROM decisions WHERE tags LIKE '%coco-learning%'"
        )
        result["learning_decisions"] = cursor.fetchone()[0]
        
        conn.close()
    except sqlite3.Error:
        pass
    
    return result
