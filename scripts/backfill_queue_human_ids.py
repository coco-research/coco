#!/usr/bin/env python3
"""Backfill human_id on every item in ~/.coco/queue.json.

Decisions (queue.json) are not part of platform.db's schema, so the alembic
migration cannot reach them. This one-shot script assigns Linear-style
human IDs (e.g., CXR-47) in monotonic created_at order using the same
id_sequences table that backs todo / agent IDs.

Safe to re-run: skips items that already have a `human_id`.

Usage:
    uv run python scripts/backfill_queue_human_ids.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

COCO_DIR = Path(os.environ.get("COCO_DIR", str(Path.home() / ".coco")))
QUEUE_JSON = COCO_DIR / "queue.json"
PLATFORM_DB = Path(os.environ.get("COCO_PLATFORM_DB", str(COCO_DIR / "platform.db")))

GLOBAL_BUCKET = "__global__"
GLOBAL_PREFIX = "CXR"


def _atomic_write_json(path: Path, data) -> None:
    tmp_fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".queue.", suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _next_seq(cur: sqlite3.Cursor, node_id: str) -> int:
    cur.execute(
        "INSERT INTO id_sequences (node_id, next_seq) VALUES (?, 1) "
        "ON CONFLICT(node_id) DO UPDATE SET next_seq = next_seq + 1",
        (node_id,),
    )
    row = cur.execute(
        "SELECT next_seq FROM id_sequences WHERE node_id = ?", (node_id,)
    ).fetchone()
    return int(row[0])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not QUEUE_JSON.exists():
        print(f"queue.json not found at {QUEUE_JSON}; nothing to do.")
        return 0
    if not PLATFORM_DB.exists():
        print(f"platform.db not found at {PLATFORM_DB}; aborting.", file=sys.stderr)
        return 1

    with QUEUE_JSON.open() as fp:
        data = json.load(fp)

    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        print("queue.json items key is not a list; aborting.", file=sys.stderr)
        return 1

    # Stable sort by created_at so backfill is monotonic.
    items.sort(key=lambda x: x.get("created_at") or "")

    conn = sqlite3.connect(PLATFORM_DB)
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO id_sequences (node_id, next_seq) VALUES (?, 1)",
        (GLOBAL_BUCKET,),
    )

    assigned = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("human_id"):
            continue

        # Resolve a node prefix from project if it maps to a node label.
        project = item.get("project")
        prefix = GLOBAL_PREFIX
        bucket = GLOBAL_BUCKET

        if project:
            row = cur.execute(
                "SELECT id, prefix, label FROM nodes WHERE label = ? OR id = ?",
                (project, project),
            ).fetchone()
            if row:
                bucket = row[0]
                if row[1]:
                    prefix = row[1]
                else:
                    label = (row[2] or "").strip()
                    alpha = "".join(c for c in label if c.isalpha())
                    prefix = (alpha[:3] if len(alpha) >= 3 else (alpha + "XXX")[:3]).upper() or GLOBAL_PREFIX
                    cur.execute(
                        "UPDATE nodes SET prefix = ?, updated_at = datetime('now') WHERE id = ?",
                        (prefix, bucket),
                    )

        seq = _next_seq(cur, bucket)
        human_id = f"{prefix}-{seq}"
        item["human_id"] = human_id

        # Mirror into entity_identifiers so resolve_display_id() finds it.
        cur.execute(
            "INSERT OR IGNORE INTO entity_identifiers "
            "(entity_id, entity_type, node_id, sequence_num, display_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (item.get("id") or human_id, "decision", bucket, seq, human_id),
        )
        assigned += 1

    if args.dry_run:
        print(f"[dry-run] would assign {assigned} human_id(s); rolling back.")
        conn.rollback()
        conn.close()
        return 0

    conn.commit()
    conn.close()

    if isinstance(data, dict):
        data["items"] = items
    else:
        data = items
    _atomic_write_json(QUEUE_JSON, data)
    print(f"Assigned {assigned} human_id(s); queue.json updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
