"""Brain Exporter — generates a slim CLAUDE.local.md auto-section from brain DB.

Public API:
    export_claude_local(db_path, project_slug, output_path) -> bool
    migrate_feedback_memories(memory_dir) -> list[str]
"""

import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path


# ── Sentinels ────────────────────────────────────────────────────────────────

SENTINEL_START = "<!-- AUTO-GENERATED: brain-export -->"
SENTINEL_END   = "<!-- END AUTO-GENERATED -->"

# Approximate chars-per-token for budget enforcement
CHARS_PER_TOKEN = 4
TOKEN_BUDGET     = 1200
CHAR_BUDGET      = TOKEN_BUDGET * CHARS_PER_TOKEN  # 4 800


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_date(iso_str: str | None) -> str:
    """Return YYYY-MM-DD from an ISO timestamp string (or '' if None/invalid)."""
    if not iso_str:
        return ""
    try:
        return iso_str[:10]
    except Exception:
        return ""


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


# ── MemPalace L0 ─────────────────────────────────────────────────────────────

def _mempalace_identity() -> str | None:
    """Return the contents of ~/.mempalace/identity.txt or None."""
    identity_path = Path.home() / ".mempalace" / "identity.txt"
    if identity_path.exists():
        try:
            return identity_path.read_text(encoding="utf-8").strip()
        except OSError:
            pass
    return None


# ── Section builders ──────────────────────────────────────────────────────────

def _build_last_session(conn: sqlite3.Connection, project_id: int) -> str:
    lines = []

    event = conn.execute(
        "SELECT title, date FROM events WHERE project_id=? ORDER BY date DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    if event:
        lines.append(f"- {event['title']} ({_short_date(event['date'])})")

    decision = conn.execute(
        "SELECT decision, date FROM decisions WHERE project_id=? ORDER BY date DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    if decision:
        text = _truncate(decision["decision"], 100)
        lines.append(f"- {text} ({_short_date(decision['date'])})")

    if not lines:
        return ""
    return "## Last Session\n" + "\n".join(lines) + "\n"


def _build_key_people(conn: sqlite3.Connection, project_id: int) -> str:
    rows = conn.execute(
        "SELECT name, metadata_json FROM entities "
        "WHERE project_id=? AND type='person' "
        "ORDER BY created_at DESC LIMIT 8",
        (project_id,),
    ).fetchall()
    if not rows:
        return ""

    lines = [
        "## Key People",
        "| Name | Role | Email |",
        "|------|------|-------|",
    ]
    for row in rows:
        meta = {}
        try:
            meta = json.loads(row["metadata_json"] or "{}")
        except (json.JSONDecodeError, TypeError):
            pass
        role  = meta.get("role", meta.get("title", ""))
        email = meta.get("email", "")
        lines.append(f"| {row['name']} | {role} | {email} |")
    return "\n".join(lines) + "\n"


def _build_key_systems(conn: sqlite3.Connection, project_id: int) -> str:
    rows = conn.execute(
        "SELECT name, metadata_json FROM entities "
        "WHERE project_id=? AND type IN ('system', 'module') "
        "ORDER BY created_at DESC LIMIT 8",
        (project_id,),
    ).fetchall()
    if not rows:
        return ""

    lines = ["## Key Systems"]
    for row in rows:
        meta = {}
        try:
            meta = json.loads(row["metadata_json"] or "{}")
        except (json.JSONDecodeError, TypeError):
            pass
        desc = meta.get("description", meta.get("desc", ""))
        if desc:
            lines.append(f"- **{row['name']}** — {_truncate(desc, 120)}")
        else:
            lines.append(f"- **{row['name']}**")
    return "\n".join(lines) + "\n"


def _build_recent_decisions(conn: sqlite3.Connection, project_id: int) -> str:
    rows = conn.execute(
        "SELECT date, decision FROM decisions "
        "WHERE project_id=? ORDER BY date DESC LIMIT 4",
        (project_id,),
    ).fetchall()
    if not rows:
        return ""

    lines = ["## Recent Decisions"]
    for row in rows:
        text = _truncate(row["decision"], 120)
        lines.append(f"- [{_short_date(row['date'])}] {text}")
    return "\n".join(lines) + "\n"


def _build_project_status(conn: sqlite3.Connection, project_id: int,
                           db_path: Path) -> str:
    stats = conn.execute(
        "SELECT "
        "(SELECT COUNT(*) FROM entities   WHERE project_id=?) as entities, "
        "(SELECT COUNT(*) FROM decisions  WHERE project_id=?) as decisions, "
        "(SELECT COUNT(*) FROM events     WHERE project_id=?) as events",
        (project_id, project_id, project_id),
    ).fetchone()

    # Last-modified date of the DB file itself as proxy for "last brain sync"
    try:
        mtime = os.path.getmtime(str(db_path))
        sync_date = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
    except OSError:
        sync_date = "unknown"

    lines = [
        "## Project Status",
        f"- Entities: {stats['entities']} | Decisions: {stats['decisions']} | Events: {stats['events']}",
        f"- Last brain sync: {sync_date}",
        "- Query: `/coco brain` or `/brain context {slug}` for full context",
    ]
    return "\n".join(lines) + "\n"


# ── Core auto-section generator ───────────────────────────────────────────────

def _generate_auto_section(db_path: Path, project_slug: str) -> str:
    """Build the complete AUTO-GENERATED block as a string."""

    # Minimal section if DB is missing or empty
    if not db_path.exists():
        return (
            f"{SENTINEL_START}\n"
            f"<!-- Generated: {_iso_now()} | Brain DB: not found -->\n\n"
            "*(No brain DB found — run `/brain init` to initialize)*\n\n"
            f"{SENTINEL_END}\n"
        )

    try:
        conn = _get_db(db_path)
    except Exception:
        return (
            f"{SENTINEL_START}\n"
            f"<!-- Generated: {_iso_now()} | Brain DB: error opening -->\n\n"
            "*(Could not open brain DB)*\n\n"
            f"{SENTINEL_END}\n"
        )

    try:
        # Entity and MemPalace drawer counts for the header comment
        total_entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]

        mempalace_drawers = 0
        palace_dir = Path.home() / ".mempalace" / "palace"
        if palace_dir.exists():
            try:
                mempalace_drawers = sum(1 for _ in palace_dir.iterdir())
            except OSError:
                pass

        proj_row = conn.execute(
            "SELECT * FROM projects WHERE slug=?", (project_slug,)
        ).fetchone()

        if not proj_row:
            # Project slug not in DB — minimal stub
            conn.close()
            return (
                f"{SENTINEL_START}\n"
                f"<!-- Generated: {_iso_now()} | Brain DB: {total_entities} entities "
                f"| MemPalace: {mempalace_drawers} drawers -->\n\n"
                f"*(Project slug `{project_slug}` not found in brain DB)*\n\n"
                f"{SENTINEL_END}\n"
            )

        project_id = proj_row["id"]

        # --- MemPalace identity (L0) ---
        identity = _mempalace_identity()
        identity_block = ""
        if identity:
            identity_block = f"## Project Identity\n{identity}\n\n"

        # --- Build body sections ---
        sections = []
        for builder in (
            _build_last_session,
            _build_key_people,
            _build_key_systems,
            _build_recent_decisions,
        ):
            section = builder(conn, project_id)
            if section:
                sections.append(section)

        status_section = _build_project_status(conn, project_id, db_path)
        sections.append(status_section)

        conn.close()

        body = "\n".join(sections)
        full = (
            f"{SENTINEL_START}\n"
            f"<!-- Generated: {_iso_now()} | Brain DB: {total_entities} entities "
            f"| MemPalace: {mempalace_drawers} drawers -->\n\n"
            + identity_block
            + body
            + f"\n{SENTINEL_END}\n"
        )

        # --- Token budget enforcement ---
        if len(full) > CHAR_BUDGET:
            # Trim from body (keep header comment + sentinels intact)
            header_end = full.index("\n\n", len(SENTINEL_START)) + 2
            header = full[:header_end]
            footer = f"\n{SENTINEL_END}\n"
            allowed = CHAR_BUDGET - len(header) - len(footer) - 50
            trimmed_body = _truncate(body, allowed)
            full = header + trimmed_body + footer

        return full

    except Exception as exc:
        try:
            conn.close()
        except Exception:
            pass
        return (
            f"{SENTINEL_START}\n"
            f"<!-- Generated: {_iso_now()} | Brain DB: error — {exc} -->\n\n"
            "*(Export error — see above)*\n\n"
            f"{SENTINEL_END}\n"
        )


# ── File parser ───────────────────────────────────────────────────────────────

def _parse_sections(existing: str) -> tuple[str, str]:
    """
    Split existing CLAUDE.local.md into (protected, behavior_rules).

    'protected'      — everything ABOVE the START sentinel
    'behavior_rules' — everything BELOW the END sentinel

    If no sentinels found, the entire content is treated as protected
    and behavior_rules is empty string.
    """
    start_idx = existing.find(SENTINEL_START)
    end_idx   = existing.find(SENTINEL_END)

    if start_idx == -1 or end_idx == -1:
        # No sentinels — whole file is protected
        return existing, ""

    protected      = existing[:start_idx]
    behavior_rules = existing[end_idx + len(SENTINEL_END):]
    return protected, behavior_rules


# ── Public API ────────────────────────────────────────────────────────────────

def export_claude_local(db_path: Path, project_slug: str, output_path: Path) -> bool:
    """
    Generate / refresh the AUTO-GENERATED section in CLAUDE.local.md.

    Preserves:
      - Everything above <!-- AUTO-GENERATED: brain-export -->
      - Everything below <!-- END AUTO-GENERATED -->
      - If no sentinels present, appends auto section at end (safe first run)

    Returns True on success, False on error.
    """
    # 1. Read existing file (if any)
    existing = ""
    if output_path.exists():
        try:
            existing = output_path.read_text(encoding="utf-8")
        except OSError:
            existing = ""

    # 2. Split into protected / behavior sections
    protected, behavior_rules = _parse_sections(existing)

    # 3. Generate the new auto section
    auto_section = _generate_auto_section(db_path, project_slug)

    # 4. Reassemble
    # Ensure protected ends with a blank line separator
    if protected and not protected.endswith("\n\n"):
        protected = protected.rstrip("\n") + "\n\n"

    # Ensure behavior_rules starts clean (strip leading blank lines)
    behavior_rules = behavior_rules.lstrip("\n")

    content = protected + auto_section
    if behavior_rules:
        content += "\n" + behavior_rules

    # 5. Atomic write (tmp file + rename)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(output_path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                fh.write(content)
            os.replace(tmp_path, str(output_path))
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception:
        return False

    return True


def migrate_feedback_memories(memory_dir: Path) -> list[str]:
    """
    Scan memory_dir for markdown files with `type: feedback` YAML frontmatter.
    Extract the rule body (everything after the closing ---) and return as a
    list of strings suitable for manual inclusion in the behavior rules section.
    """
    rules: list[str] = []
    if not memory_dir.is_dir():
        return rules

    for md_file in sorted(memory_dir.glob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        if not text.startswith("---"):
            continue

        # Find closing ---
        second_fence = text.find("\n---", 3)
        if second_fence == -1:
            continue

        frontmatter = text[3:second_fence].strip()
        body = text[second_fence + 4:].strip()

        # Check for type: feedback
        if "type: feedback" not in frontmatter:
            continue

        if body:
            # Use filename (without ext) as a header hint
            name = md_file.stem.replace("_", " ").title()
            rules.append(f"### {name}\n{body}")

    return rules


# ── CLI entry point (used by brain_cli.py) ───────────────────────────────────

def main_export(db_path_str: str | None, project_slug: str,
                output_path_str: str | None) -> None:
    """Thin wrapper called from brain_cli cmd_export."""
    from brain import resolve_db_path  # local import to avoid circular at module level

    db_path = resolve_db_path(db_path_str)
    if output_path_str:
        output_path = Path(output_path_str)
    else:
        # Default: CLAUDE.local.md in the same directory as the brain DB
        output_path = db_path.parent / "CLAUDE.local.md"

    ok = export_claude_local(db_path, project_slug, output_path)
    if ok:
        # Quick stats for CLI feedback
        try:
            content = output_path.read_text(encoding="utf-8")
            char_count = len(content)
            token_est  = char_count // CHARS_PER_TOKEN
            # Count sentinel-delimited auto section
            start_idx = content.find(SENTINEL_START)
            end_idx   = content.find(SENTINEL_END)
            auto_chars = (end_idx - start_idx + len(SENTINEL_END)) if start_idx != -1 else 0
            auto_tokens = auto_chars // CHARS_PER_TOKEN

            import json as _json
            print(_json.dumps({
                "status": "ok",
                "output": str(output_path),
                "project_slug": project_slug,
                "total_chars": char_count,
                "total_tokens_est": token_est,
                "auto_section_chars": auto_chars,
                "auto_section_tokens_est": auto_tokens,
                "within_budget": auto_tokens <= TOKEN_BUDGET,
            }, indent=2))
        except OSError:
            import json as _json
            print(_json.dumps({"status": "ok", "output": str(output_path)}))
    else:
        import json as _json
        import sys
        print(_json.dumps({"status": "error", "output": str(output_path)}), file=sys.stderr)
        sys.exit(1)
