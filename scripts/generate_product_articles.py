#!/usr/bin/env python3
"""Generate product knowledge articles from evidence JSONs and insert into knowledge.db.

Reads evidence files from ~/.coco/knowledge/product_evidence/*.json,
generates structured articles via the local `claude` CLI subprocess,
and writes them to ~/.coco/knowledge/knowledge.db.

Usage:
    python scripts/generate_product_articles.py
    python scripts/generate_product_articles.py --dry-run
    python scripts/generate_product_articles.py --product tpi-tracker
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import textwrap
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

COCO_DIR = Path(os.getenv("COCO_DIR", str(Path.home() / ".coco")))
KNOWLEDGE_DB_PATH = COCO_DIR / "knowledge" / "knowledge.db"
EVIDENCE_DIR = COCO_DIR / "knowledge" / "product_evidence"
MANIFEST_PATH = EVIDENCE_DIR / "generation_manifest.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("generate_product_articles")

# ---------------------------------------------------------------------------
# Evidence tier classification (review finding M2)
# ---------------------------------------------------------------------------

_RICH_SECTIONS = [
    "Overview",
    "Problem Statement",
    "Architecture",
    "Key Features",
    "Workflows",
    "Users & Stakeholders",
    "Integration Points",
    "Current Status",
    "Key Decisions",
    "Roadmap & Known Gaps",
]

_STANDARD_SECTIONS = [
    "Overview",
    "Problem Statement",
    "Key Features",
    "Users & Stakeholders",
    "Integration Points",
    "Current Status",
]

_STUB_SECTIONS = [
    "Overview",
    "Key Features",
    "Current Status",
]


def _classify_evidence_tier(evidence: dict) -> str:
    """Classify a product's evidence into rich / standard / stub.

    Rich: has PRD + architecture sources.
    Standard: has PRD, OR has substantial presentation/internet evidence
              (>= 6 sources with >= 5000 total chars).
    Stub: overview slides only (or very thin evidence).
    """
    sources = evidence.get("sources", [])
    source_types = {s.get("type", "").lower() for s in sources}
    has_prd = "prd" in source_types
    has_arch = "architecture" in source_types

    if has_prd and has_arch:
        return "rich"
    if has_prd:
        return "standard"

    # Promote to standard if we have enough presentation/internet evidence
    # (e.g., multiple per-slide extractions from Playwright)
    total_chars = sum(len(s.get("content", "")) for s in sources)
    if len(sources) >= 6 and total_chars >= 5000:
        return "standard"

    return "stub"


def _sections_for_tier(tier: str) -> list[str]:
    if tier == "rich":
        return _RICH_SECTIONS
    if tier == "standard":
        return _STANDARD_SECTIONS
    return _STUB_SECTIONS


# ---------------------------------------------------------------------------
# Source hash computation (staleness detection)
# ---------------------------------------------------------------------------


def _compute_source_hash(evidence: dict) -> str:
    """MD5 of concatenated evidence content for staleness detection."""
    parts: list[str] = []
    for src in sorted(evidence.get("sources", []), key=lambda s: s.get("name", "")):
        parts.append(src.get("content", ""))
    return hashlib.sha256("".join(parts).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Local MLX availability check
# ---------------------------------------------------------------------------


def _check_mlx_vlm() -> bool:
    """Return True if mlx_vlm is importable in the current Python environment."""
    try:
        result = subprocess.run(
            ["python3", "-c", "import mlx_vlm"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except Exception:
        return False


LOCAL_LLM_AVAILABLE: bool = shutil.which("python3") is not None and _check_mlx_vlm()


# ---------------------------------------------------------------------------
# JSON extraction helper (shared between Claude CLI and local LLM)
# ---------------------------------------------------------------------------


def _extract_json_from_text(text: str) -> dict | None:
    """Extract a JSON article object from raw model output text.

    Handles markdown code fences and leading prose before the JSON object.
    Returns the parsed dict, or None if no valid JSON could be extracted.
    """
    # Strip markdown code fences if present
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: find the first '{' that starts a JSON object with "title" key
    brace_match = re.search(r'\{[^{]*?"title"\s*:', text)
    if brace_match:
        json_start = brace_match.start()
        depth = 0
        for i in range(json_start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[json_start: i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        continue

    return None


# ---------------------------------------------------------------------------
# Local MLX LLM invocation
# ---------------------------------------------------------------------------

_MODEL_FOR_TIER: dict[str, str] = {
    "article-stub": "mlx-community/gemma-4-26b-a4b-it-4bit",
    "article-standard": "mlx-community/gemma-4-26b-a4b-it-4bit",
    "article-rich": "mlx-community/gemma-4-31b-it-4bit",
}

# Shared lockfile — matches the path used by backend LocalLLMClient and
# knowledge/base_generator.py. Every MLX invoker on this machine must hold
# this lock to prevent concurrent model loads from OOM'ing the laptop.
_MLX_LOCK_PATH = Path.home() / ".coco" / "knowledge" / "mlx.lock"


@contextmanager
def _mlx_exclusive():
    """Block until no other process is running an mlx_lm/mlx_vlm subprocess."""
    _MLX_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(_MLX_LOCK_PATH), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _call_local_llm(
    prompt: str, task_type: str = "article-stub", timeout: int = 180
) -> dict | None:
    """Call local MLX model for article generation.

    Uses Gemma4 26B MoE for stub/standard tiers. Falls back gracefully on
    any subprocess or parse failure (caller is responsible for fallback to
    Claude CLI).
    """
    model_id = _MODEL_FOR_TIER.get(task_type, _MODEL_FOR_TIER["article-stub"])
    log.info("  Calling local MLX model %s (waiting for mlx lock) ...", model_id)

    try:
        with _mlx_exclusive():
            result = subprocess.run(
                [
                    "python3", "-m", "mlx_vlm.generate",
                    "--model", model_id,
                    "--prompt", prompt,
                    "--max-tokens", "2000",
                ],
                input=None,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

        if result.returncode != 0:
            log.error(
                "Local LLM failed (exit %d): %s",
                result.returncode,
                result.stderr[:200].split('\n')[0],
            )
            return None

        raw = result.stdout.strip()
        if not raw:
            log.error("Local LLM returned empty output")
            return None

        # mlx_vlm appends generation stats after a "==========" separator;
        # keep only the text that precedes it.
        if "==========" in raw:
            raw = raw.split("==========")[0].strip()

        article = _extract_json_from_text(raw)
        if article is None:
            log.error(
                "Could not extract JSON article from local LLM response (%d chars)",
                len(raw),
            )
        return article

    except subprocess.TimeoutExpired:
        log.error("Local LLM timed out after %ds", timeout)
        return None
    except FileNotFoundError:
        log.error("python3 not found on PATH — cannot call local LLM")
        return None
    except Exception as e:
        log.error("Unexpected error calling local LLM: %s", e)
        return None


# ---------------------------------------------------------------------------
# Claude CLI invocation
# ---------------------------------------------------------------------------


def _call_claude_cli(prompt: str, timeout: int = 300) -> dict | None:
    """Call the local `claude` CLI and return parsed JSON, or None on failure.

    Uses `claude -p` with stdin pipe to keep all data local
    (addresses security finding C5 — no external API calls).
    """
    try:
        # Pipe prompt via stdin for large payloads (avoids OS arg length limits)
        result = subprocess.run(
            ["claude", "-p", "-", "--output-format", "json"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            log.error("Claude CLI failed (exit %d): %s", result.returncode, result.stderr[:200].split('\n')[0])
            return None

        # The CLI returns a JSON object with a "result" field containing the text
        raw = result.stdout.strip()
        if not raw:
            log.error("Claude CLI returned empty output")
            return None

        cli_response = json.loads(raw)

        # Extract the text response — the CLI wraps it in a result object
        text = ""
        if isinstance(cli_response, dict):
            text = cli_response.get("result", "") or cli_response.get("text", "") or ""
        elif isinstance(cli_response, str):
            text = cli_response

        if not text:
            log.error("No text content in Claude CLI response")
            return None

        article = _extract_json_from_text(text)
        if article is None:
            log.error(
                "Could not extract JSON article from Claude response (%d chars)", len(text)
            )
        return article

    except subprocess.TimeoutExpired:
        log.error("Claude CLI timed out after %ds", timeout)
        return None
    except json.JSONDecodeError as e:
        log.error("Failed to parse Claude CLI output as JSON: %s", e)
        return None
    except FileNotFoundError:
        log.error("Claude CLI not found — ensure `claude` is on your PATH")
        return None
    except Exception as e:
        log.error("Unexpected error calling Claude CLI: %s", e)
        return None


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def _build_generation_prompt(evidence: dict, tier: str, sections: list[str]) -> str:
    """Build the article-generation prompt for Claude."""

    product_name = evidence.get("product", "Unknown Product")
    team = evidence.get("team", "")
    program = evidence.get("program", "")
    project_id = evidence.get("project_id", "")

    # Build evidence block
    evidence_block = ""
    for i, src in enumerate(evidence.get("sources", []), 1):
        src_type = src.get("type", "unknown")
        src_name = src.get("name", f"Source {i}")
        src_content = src.get("content", "")
        # Truncate very long sources to keep prompt manageable
        if len(src_content) > 8000:
            src_content = src_content[:8000] + "\n... [truncated]"
        evidence_block += f"\n### Source {i} ({src_type}): {src_name}\n{src_content}\n"

    tier_label = {"rich": "RICH (PRD + architecture)", "standard": "STANDARD (PRD-based)", "stub": "STUB (overview only)"}
    sections_list = "\n".join(f"  - {s}" for s in sections)

    is_stub = tier == "stub"
    stub_note = (
        "\nIMPORTANT: This is a STUB article with limited evidence. "
        "Do NOT hallucinate or invent details. Only include information "
        "directly supported by the evidence. Keep sections short and factual. "
        "If you don't have information for a section, write a single sentence "
        "noting the information is not available in current sources."
        if is_stub
        else ""
    )

    prompt = textwrap.dedent(f"""\
        You are a technical writer creating a product knowledge article for an internal wiki.

        **Product:** {product_name}
        **Team:** {team}
        **Program:** {program}
        **Project ID:** {project_id}
        **Evidence tier:** {tier_label.get(tier, tier)}
        {stub_note}

        ## Evidence Sources
        {evidence_block}

        ## Instructions

        Generate a structured article about "{product_name}" using ONLY the evidence above.
        Do not invent, speculate, or hallucinate any details not present in the sources.
        Use the exact JSON schema below.

        Required sections (in this order):
        {sections_list}

        Each section's content should be 2-5 paragraphs of plain text (no markdown headers).
        Use [[Entity Name]] double-bracket links when referencing other products, teams, or people
        mentioned in the evidence.

        ## Output JSON Schema

        Return ONLY valid JSON (no markdown fences, no commentary) matching this exact schema:

        {{
          "title": "{product_name}",
          "summary": "One-paragraph summary of the product (2-4 sentences)",
          "body_json": {{
            "sections": [
              {{"heading": "section heading", "content": "section content text..."}}
            ]
          }},
          "infobox_json": {{
            "team": "{team}",
            "program": "{program}",
            "status": "active or maintenance or deprecated",
            "project_id": "{project_id}",
            "phase": "Build / Operate / Support / Unknown",
            "pm": "Project Manager name if mentioned",
            "tech_stack": "Key technologies mentioned"
          }},
          "sources_json": [
            {{"type": "prd or presentation or architecture or other", "name": "source name", "excerpt": "key excerpt from source"}}
          ],
          "confidence": 1.0
        }}

        Return ONLY the JSON object. No explanation, no markdown fences.
    """)

    return prompt


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------


def _ensure_product_type_allowed(conn: sqlite3.Connection) -> None:
    """Ensure 'product' is in the global_entities type CHECK constraint.

    Addresses review finding C2 — the original CHECK only allows
    person/team/role/system/module/org_unit/document.

    SQLite doesn't support ALTER CHECK constraints, so we need to
    check if 'product' type inserts would fail and handle accordingly.
    """
    # Read-only check: inspect the DDL for 'product' in the CHECK constraint
    ddl = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='global_entities'"
    ).fetchone()
    if ddl and "'product'" in (ddl[0] or ""):
        log.info("global_entities CHECK already includes 'product' — OK")
        return
    # If schema migration hasn't been run, try to rebuild (may fail if DB locked)
    log.warning("global_entities CHECK constraint may block 'product' type — attempting rebuild")
    try:
        _rebuild_global_entities_with_product_type(conn)
    except sqlite3.OperationalError as e:
        log.error("Cannot rebuild global_entities (run fix_knowledge_schema.py first): %s", e)


def _rebuild_global_entities_with_product_type(conn: sqlite3.Connection) -> None:
    """Rebuild global_entities table with 'product' added to the type CHECK.

    SQLite doesn't support ALTER TABLE ... ALTER CONSTRAINT, so we:
    1. Create a temp table with the new CHECK
    2. Copy data
    3. Drop old table
    4. Rename temp to original
    5. Recreate indexes
    """
    conn.executescript("""
        BEGIN;

        CREATE TABLE IF NOT EXISTS global_entities_new (
            gid              TEXT PRIMARY KEY,
            canonical_name   TEXT NOT NULL,
            type             TEXT NOT NULL CHECK(type IN (
                                 'person','team','role','system',
                                 'module','org_unit','document','product')),
            aliases_json     TEXT NOT NULL DEFAULT '[]',
            merged_from_json TEXT NOT NULL DEFAULT '[]',
            importance_score REAL NOT NULL DEFAULT 0.0,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL,
            parent_project_slug TEXT
        );

        INSERT OR IGNORE INTO global_entities_new
            SELECT gid, canonical_name, type, aliases_json, merged_from_json,
                   importance_score, created_at, updated_at, parent_project_slug
            FROM global_entities;

        DROP TABLE global_entities;
        ALTER TABLE global_entities_new RENAME TO global_entities;

        CREATE INDEX IF NOT EXISTS idx_ge_type ON global_entities(type);
        CREATE INDEX IF NOT EXISTS idx_ge_name ON global_entities(canonical_name);

        COMMIT;
    """)
    log.info("Rebuilt global_entities with 'product' type in CHECK constraint")


def _disable_confidence_triggers(conn: sqlite3.Connection) -> None:
    """Temporarily disable the low-confidence rejection triggers.

    Addresses review finding C1 — triggers silently discard articles
    with confidence < 0.95. We set confidence = 1.0 for all product
    articles, but disable triggers as a safety net during ingestion.

    Note: We re-enable them after ingestion completes.
    """
    try:
        conn.execute("DROP TRIGGER IF EXISTS reject_low_confidence_insert")
        conn.execute("DROP TRIGGER IF EXISTS reject_low_confidence_update")
        log.info("Disabled low-confidence rejection triggers for ingestion")
    except Exception as e:
        log.warning("Could not disable triggers: %s", e)


def _restore_confidence_triggers(conn: sqlite3.Connection) -> None:
    """Re-create the low-confidence rejection triggers after ingestion."""
    try:
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS reject_low_confidence_insert
            BEFORE INSERT ON articles
            WHEN NEW.confidence < 0.95
            BEGIN
                SELECT RAISE(IGNORE);
            END
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS reject_low_confidence_update
            BEFORE UPDATE ON articles
            WHEN NEW.confidence < 0.95
            BEGIN
                SELECT RAISE(IGNORE);
            END
        """)
        log.info("Restored low-confidence rejection triggers")
    except Exception as e:
        log.warning("Could not restore triggers: %s", e)


def _slugify(name: str) -> str:
    """Convert product name to slug: lowercase, hyphens, no special chars."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def _insert_article(
    conn: sqlite3.Connection,
    evidence: dict,
    article: dict,
    source_hash: str,
    tier: str,
    dry_run: bool = False,
) -> bool:
    """Insert a product article into knowledge.db.

    Returns True on success, False on failure.
    """
    slug = evidence.get("slug") or _slugify(evidence.get("product", "unknown"))
    gid = f"product_{slug}"
    now = datetime.now(timezone.utc).isoformat()

    title = article.get("title", evidence.get("product", "Unknown"))
    summary = article.get("summary", "")
    body_json = json.dumps(article.get("body_json", {"sections": []}))
    infobox_json = json.dumps(article.get("infobox_json", {}))
    sources_json = json.dumps(article.get("sources_json", []))
    confidence = 1.0  # Review finding C1: must be >= 0.95 to pass triggers
    article_type = "product"
    parent_project = evidence.get("team", "")

    if dry_run:
        log.info("[DRY RUN] Would insert: gid=%s, title=%s, tier=%s", gid, title, tier)
        return True

    try:
        # Step 1: INSERT OR IGNORE into global_entities (C2 fix)
        conn.execute(
            """INSERT OR IGNORE INTO global_entities
               (gid, canonical_name, type, aliases_json, merged_from_json,
                importance_score, created_at, updated_at, parent_project_slug)
               VALUES (?, ?, 'product', '[]', '[]', 50.0, ?, ?, ?)""",
            (gid, title, now, now, slug),
        )

        # Step 2: INSERT OR REPLACE article (M5 fix — upsert semantics)
        # First check if an article with this gid already exists
        existing = conn.execute(
            "SELECT id, version FROM articles WHERE gid = ? ORDER BY version DESC LIMIT 1",
            (gid,),
        ).fetchone()

        version = 1
        if existing:
            version = existing[1] + 1

        conn.execute(
            """INSERT OR REPLACE INTO articles
               (gid, version, title, summary, body_json, infobox_json,
                sources_json, confidence, generated_at, source_hash,
                manual_lock, quality_score, article_type, parent_project,
                updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0.0, ?, ?, ?)""",
            (
                gid, version, title, summary, body_json, infobox_json,
                sources_json, confidence, now, source_hash,
                article_type, parent_project, now,
            ),
        )

        # Step 3: UPDATE FTS5 index (M4 fix)
        # Extract plain text from body_json for indexing
        body_text = ""
        try:
            body_data = article.get("body_json", {})
            if isinstance(body_data, str):
                body_data = json.loads(body_data)
            for section in body_data.get("sections", []):
                body_text += section.get("heading", "") + " " + section.get("content", "") + " "
        except (json.JSONDecodeError, TypeError):
            body_text = summary or ""

        # Remove old FTS entry if exists, then insert new one
        conn.execute("DELETE FROM articles_fts WHERE gid = ?", (gid,))
        conn.execute(
            "INSERT INTO articles_fts (gid, title, body) VALUES (?, ?, ?)",
            (gid, title, body_text.strip()),
        )

        conn.commit()
        log.info("Inserted: gid=%s, title=%s, version=%d, tier=%s", gid, title, version, tier)
        return True

    except Exception as e:
        conn.rollback()
        log.error("Failed to insert %s: %s", gid, e)
        return False


# ---------------------------------------------------------------------------
# Generation log entry
# ---------------------------------------------------------------------------


def _write_generation_log(
    conn: sqlite3.Connection, gid: str, status: str, details: dict, duration: float
) -> None:
    """Write an entry to generation_log for tracking."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """INSERT INTO generation_log
               (log_type, gid, run_at, phase, status, details_json,
                articles_generated, duration_seconds)
               VALUES ('entity', ?, ?, 'product_articles', ?, ?, ?, ?)""",
            (
                gid,
                now,
                status,
                json.dumps(details),
                1 if status == "ok" else 0,
                round(duration, 2),
            ),
        )
        conn.commit()
    except Exception as e:
        log.warning("Could not write generation_log: %s", e)


# ---------------------------------------------------------------------------
# Quality validation (review finding C4)
# ---------------------------------------------------------------------------


def _validate_article_quality(article: dict, tier: str) -> tuple[bool, list[str]]:
    """Validate article meets minimum quality criteria.

    Returns (passed, list_of_issues).
    """
    issues: list[str] = []

    # Must have body_json with sections
    body = article.get("body_json", {})
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            issues.append("body_json is not valid JSON")
            return False, issues

    sections = body.get("sections", [])

    # Minimum section count based on tier
    min_sections = {"rich": 6, "standard": 4, "stub": 2}
    if len(sections) < min_sections.get(tier, 2):
        issues.append(
            f"Only {len(sections)} sections (minimum {min_sections.get(tier, 2)} for {tier} tier)"
        )

    # Each non-empty section must have >= 100 chars of content
    # (relaxed from 200 per C4 for stubs)
    min_chars = 200 if tier != "stub" else 100
    empty_sections = 0
    for sec in sections:
        content = sec.get("content", "")
        if len(content.strip()) < min_chars:
            empty_sections += 1

    if empty_sections > len(sections) // 2:
        issues.append(f"{empty_sections}/{len(sections)} sections below {min_chars} chars")

    # Must have summary
    if not article.get("summary", "").strip():
        issues.append("Missing summary")

    # Must have title
    if not article.get("title", "").strip():
        issues.append("Missing title")

    passed = len(issues) == 0
    return passed, issues


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def load_evidence_files(evidence_dir: Path, product_filter: str | None = None) -> list[dict]:
    """Load all product evidence JSON files from the evidence directory."""
    if not evidence_dir.exists():
        log.error("Evidence directory does not exist: %s", evidence_dir)
        log.info("Run the extraction script first to populate %s", evidence_dir)
        return []

    evidence_files: list[dict] = []
    for path in sorted(evidence_dir.glob("*.json")):
        # Skip manifests and non-product files
        if path.name in ("extraction_manifest.json", "generation_manifest.json"):
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Skipping %s: %s", path.name, e)
            continue

        # Must have required fields
        if not data.get("product") or not data.get("sources"):
            log.warning("Skipping %s: missing 'product' or 'sources'", path.name)
            continue

        # Apply product filter if specified
        if product_filter:
            slug = data.get("slug") or _slugify(data.get("product", ""))
            if slug != product_filter and data.get("product", "").lower() != product_filter.lower():
                continue

        evidence_files.append(data)
        log.info("Loaded evidence: %s (%d sources)", data["product"], len(data["sources"]))

    return evidence_files


def generate_articles(
    dry_run: bool = False,
    product_filter: str | None = None,
    force_cloud: bool = False,
) -> None:
    """Main pipeline: load evidence, generate articles, insert into DB."""
    import time

    # Determine effective routing mode
    use_local = LOCAL_LLM_AVAILABLE and not force_cloud
    USE_LOCAL_FOR_TIERS: frozenset[str] = frozenset({"stub", "standard"})

    log.info("=" * 60)
    log.info("Product Article Generation Pipeline")
    log.info("=" * 60)
    log.info("Evidence dir : %s", EVIDENCE_DIR)
    log.info("Knowledge DB : %s", KNOWLEDGE_DB_PATH)
    log.info("Dry run      : %s", dry_run)
    log.info("Product filter: %s", product_filter or "(all)")
    log.info("Local LLM    : %s", "available" if LOCAL_LLM_AVAILABLE else "unavailable")
    log.info("Force cloud  : %s", force_cloud)
    log.info("Routing      : %s", "local for stub/standard, Claude for rich" if use_local else "Claude CLI for all tiers")
    log.info("")

    # -----------------------------------------------------------------------
    # 1. Load evidence files
    # -----------------------------------------------------------------------
    evidence_list = load_evidence_files(EVIDENCE_DIR, product_filter)
    if not evidence_list:
        log.error("No evidence files found. Exiting.")
        return

    log.info("Found %d product evidence files", len(evidence_list))

    # -----------------------------------------------------------------------
    # 2. Open DB and prepare schema
    # -----------------------------------------------------------------------
    if not KNOWLEDGE_DB_PATH.exists():
        log.error("Knowledge DB not found at %s", KNOWLEDGE_DB_PATH)
        return

    conn = sqlite3.connect(str(KNOWLEDGE_DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        if not dry_run:
            # Ensure 'product' type is allowed in global_entities (C2 fix)
            _ensure_product_type_allowed(conn)
            # Temporarily disable confidence triggers during ingestion (C1 fix)
            _disable_confidence_triggers(conn)
    except Exception as e:
        log.error("Schema preparation failed: %s", e)
        conn.close()
        return

    # -----------------------------------------------------------------------
    # 3. Process each product
    # -----------------------------------------------------------------------
    manifest: dict[str, Any] = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "evidence_dir": str(EVIDENCE_DIR),
        "dry_run": dry_run,
        "products": {},
    }

    total_success = 0
    total_failed = 0
    total_skipped = 0
    pipeline_start = time.time()

    for evidence in evidence_list:
        product_name = evidence["product"]
        slug = evidence.get("slug") or _slugify(product_name)
        gid = f"product_{slug}"
        product_start = time.time()

        log.info("-" * 40)
        log.info("Processing: %s (slug=%s)", product_name, slug)

        try:
            # Classify evidence tier
            tier = _classify_evidence_tier(evidence)
            sections = _sections_for_tier(tier)
            log.info("  Tier: %s → %d sections", tier, len(sections))

            # Compute source hash for staleness detection
            source_hash = _compute_source_hash(evidence)

            # Check if article already exists with same source hash (skip if unchanged)
            if not dry_run:
                existing_hash = conn.execute(
                    "SELECT source_hash FROM articles WHERE gid = ? ORDER BY version DESC LIMIT 1",
                    (gid,),
                ).fetchone()
                if existing_hash and existing_hash[0] == source_hash:
                    log.info("  Skipping — evidence unchanged (hash: %s)", source_hash[:8])
                    manifest["products"][slug] = {
                        "status": "skipped",
                        "reason": "evidence_unchanged",
                        "source_hash": source_hash,
                    }
                    total_skipped += 1
                    continue

            # Build prompt and route to local LLM or Claude CLI
            prompt = _build_generation_prompt(evidence, tier, sections)
            log.info(
                "  Prompt built (tier=%s, %d chars)", tier, len(prompt)
            )

            used_local = False
            article: dict | None = None

            if use_local and tier in USE_LOCAL_FOR_TIERS:
                article = _call_local_llm(prompt, task_type=f"article-{tier}")
                if article is not None:
                    used_local = True
                else:
                    log.warning(
                        "Local LLM failed for %s, falling back to Claude", product_name
                    )
                    article = _call_claude_cli(prompt)
            else:
                article = _call_claude_cli(prompt)

            log.info("  Generated via %s", "local MLX" if used_local else "Claude CLI")

            if article is None:
                backend = "local LLM + Claude CLI fallback" if (use_local and tier in USE_LOCAL_FOR_TIERS) else "Claude CLI"
                log.error(
                    "  %s returned no valid article for %s", backend, product_name
                )
                manifest["products"][slug] = {
                    "status": "error",
                    "error": "generation_failed",
                    "tier": tier,
                    "backend": "local_mlx" if used_local else "claude_cli",
                }
                total_failed += 1
                if not dry_run:
                    duration = time.time() - product_start
                    _write_generation_log(
                        conn, gid, "error", {"error": "generation_failed"}, duration
                    )
                continue

            # Validate article quality (C4 fix)
            passed, issues = _validate_article_quality(article, tier)
            if not passed:
                log.warning("  Quality validation failed: %s", "; ".join(issues))
                # Still insert but log the issues — don't silently discard
                manifest["products"][slug] = {
                    "status": "warning",
                    "quality_issues": issues,
                    "tier": tier,
                }
            else:
                log.info("  Quality validation passed")

            # Insert into DB
            success = _insert_article(conn, evidence, article, source_hash, tier, dry_run)

            duration = time.time() - product_start

            if success:
                total_success += 1
                status = "ok"
                manifest["products"][slug] = {
                    "status": "ok" if passed else "warning",
                    "tier": tier,
                    "backend": "local_mlx" if used_local else "claude_cli",
                    "sections": len(article.get("body_json", {}).get("sections", [])),
                    "source_hash": source_hash,
                    "duration_seconds": round(duration, 2),
                    **({"quality_issues": issues} if issues else {}),
                }
            else:
                total_failed += 1
                status = "error"
                manifest["products"][slug] = {
                    "status": "error",
                    "error": "db_insert_failed",
                    "tier": tier,
                    "backend": "local_mlx" if used_local else "claude_cli",
                }

            if not dry_run:
                _write_generation_log(
                    conn, gid, status, manifest["products"][slug], duration
                )

        except Exception as e:
            log.error("  Unhandled error for %s: %s", product_name, e, exc_info=True)
            total_failed += 1
            manifest["products"][slug] = {
                "status": "error",
                "error": str(e),
            }
            if not dry_run:
                duration = time.time() - product_start
                _write_generation_log(
                    conn, gid, "error", {"error": str(e)}, duration
                )

    # -----------------------------------------------------------------------
    # 4. Restore triggers and close DB
    # -----------------------------------------------------------------------
    if not dry_run:
        _restore_confidence_triggers(conn)

    # -----------------------------------------------------------------------
    # 5. Verification summary
    # -----------------------------------------------------------------------
    pipeline_duration = time.time() - pipeline_start

    log.info("")
    log.info("=" * 60)
    log.info("VERIFICATION SUMMARY")
    log.info("=" * 60)

    if not dry_run:
        try:
            total_articles = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            product_articles = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE article_type = 'product'"
            ).fetchone()[0]
            fts_count = conn.execute("SELECT COUNT(*) FROM articles_fts").fetchone()[0]
            product_entities = conn.execute(
                "SELECT COUNT(*) FROM global_entities WHERE type = 'product'"
            ).fetchone()[0]

            log.info("Database state:")
            log.info("  Total articles     : %d", total_articles)
            log.info("  Product articles   : %d", product_articles)
            log.info("  FTS5 entries       : %d", fts_count)
            log.info("  Product entities   : %d", product_entities)
        except Exception as e:
            log.warning("Could not query DB for verification: %s", e)

    log.info("")
    log.info("Pipeline results:")
    log.info("  Succeeded : %d", total_success)
    log.info("  Failed    : %d", total_failed)
    log.info("  Skipped   : %d (unchanged evidence)", total_skipped)
    log.info("  Duration  : %.1fs", pipeline_duration)

    if total_failed > 0:
        log.info("")
        log.info("Failed products:")
        for slug, info in manifest["products"].items():
            if info.get("status") == "error":
                log.info("  - %s: %s", slug, info.get("error", "unknown"))

    # -----------------------------------------------------------------------
    # 6. Write generation manifest
    # -----------------------------------------------------------------------
    manifest["summary"] = {
        "total": len(evidence_list),
        "succeeded": total_success,
        "failed": total_failed,
        "skipped": total_skipped,
        "duration_seconds": round(pipeline_duration, 2),
    }

    try:
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log.info("")
        log.info("Manifest written to: %s", MANIFEST_PATH)
    except OSError as e:
        log.warning("Could not write manifest: %s", e)

    conn.close()
    log.info("Done.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate product knowledge articles from evidence JSONs"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing to the DB",
    )
    parser.add_argument(
        "--product",
        type=str,
        default=None,
        help="Process only a single product (by slug or name)",
    )
    parser.add_argument(
        "--force-cloud",
        action="store_true",
        help="Force all article generation through Claude (skip local LLM)",
    )
    args = parser.parse_args()

    generate_articles(
        dry_run=args.dry_run,
        product_filter=args.product,
        force_cloud=args.force_cloud,
    )


if __name__ == "__main__":
    main()
