"""Folder scanner for brain bootstrap and incremental rescan.

Walks a project folder, builds a manifest of files, detects changes,
and extracts structured knowledge from CLAUDE.local.md, memory files,
and document inventory.
"""

import hashlib
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from .models import now_iso

try:
    from brain.document_reader import read_document, is_readable
except ImportError:
    def read_document(path): return ""
    def is_readable(path): return False

MANIFEST_FILENAME = "_brain_manifest.json"

# Folders to skip during scanning
SKIP_DIRS = {
    ".git", ".claude", "__pycache__", "node_modules",
    "_temp", ".sync", ".planning",
}

# File extensions we care about
DOC_EXTENSIONS = {".html", ".md", ".txt", ".pdf", ".docx", ".xlsx", ".xls", ".pptx"}

# Known knowledge source files (relative to project root)
KNOWLEDGE_SOURCES = {
    "claude_local": "CLAUDE.local.md",
    "claude_md": "CLAUDE.md",
}


def file_hash(path: Path) -> str:
    """Fast hash of file content for change detection."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except (OSError, PermissionError):
        return ""
    return h.hexdigest()


def file_meta(path: Path, project_root: Path) -> dict:
    """Build metadata dict for a single file."""
    stat = path.stat()
    fhash = file_hash(path)
    ext = path.suffix.lower()

    # Generate content preview for entity extraction (used by brain-rescan)
    content_preview = ""
    try:
        if is_readable(str(path)):
            raw = read_document(str(path))
            content_preview = raw[:2000] if raw else ""
        elif ext in {".md", ".txt", ".html"}:
            with open(path, "r", errors="replace") as f:
                content_preview = f.read(2000)
    except Exception:
        content_preview = ""

    return {
        "path": str(path.relative_to(project_root)),
        "abs_path": str(path),
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "hash": fhash,
        "extension": ext,
        "content_preview": content_preview,
    }


# ── Manifest ────────────────────────────────────────────────

def load_manifest(project_root: Path) -> dict:
    """Load existing manifest or return empty structure."""
    manifest_path = project_root / MANIFEST_FILENAME
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"version": 1, "last_scan": None, "files": {}}


def save_manifest(project_root: Path, manifest: dict) -> Path:
    """Write manifest to disk."""
    manifest_path = project_root / MANIFEST_FILENAME
    manifest["last_scan"] = now_iso()
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path


# ── Folder Walking ──────────────────────────────────────────

def walk_project(project_root: Path) -> list[dict]:
    """Walk project folder and return metadata for all relevant files."""
    files = []
    for dirpath, dirnames, filenames in os.walk(project_root):
        # Prune skip dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if fname.startswith("."):
                continue
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if ext in DOC_EXTENSIONS or fname in KNOWLEDGE_SOURCES.values():
                files.append(file_meta(fpath, project_root))
    return sorted(files, key=lambda f: f["path"])


def diff_manifest(project_root: Path) -> dict:
    """Compare current folder state against manifest. Returns categorized changes."""
    old_manifest = load_manifest(project_root)
    current_files = walk_project(project_root)

    old_files = old_manifest.get("files", {})
    current_by_path = {f["path"]: f for f in current_files}
    old_paths = set(old_files.keys())
    current_paths = set(current_by_path.keys())

    new_files = []
    changed_files = []
    removed_files = []
    unchanged_files = []

    for path in current_paths - old_paths:
        new_files.append(current_by_path[path])

    for path in old_paths - current_paths:
        removed_files.append({"path": path, **old_files[path]})

    for path in current_paths & old_paths:
        if current_by_path[path]["hash"] != old_files[path].get("hash"):
            changed_files.append(current_by_path[path])
        else:
            unchanged_files.append(current_by_path[path])

    return {
        "new": new_files,
        "changed": changed_files,
        "removed": removed_files,
        "unchanged": unchanged_files,
        "is_first_scan": old_manifest.get("last_scan") is None,
        "last_scan": old_manifest.get("last_scan"),
        "total_current": len(current_files),
    }


def update_manifest(project_root: Path, files: list[dict]) -> dict:
    """Update manifest with scanned file entries."""
    manifest = load_manifest(project_root)
    for f in files:
        manifest["files"][f["path"]] = {
            "hash": f["hash"],
            "size": f["size"],
            "modified": f["modified"],
            "scanned_at": now_iso(),
        }
    save_manifest(project_root, manifest)
    return manifest


# ── Knowledge Source Detection ──────────────────────────────

def find_knowledge_sources(project_root: Path) -> dict:
    """Find all knowledge-bearing files in the project."""
    sources = {
        "claude_local": None,
        "claude_md": None,
        "memory_dir": None,
        "memory_files": [],
        "docs": [],
        "emails": [],
    }

    # CLAUDE.local.md / CLAUDE.md at project root
    for key, fname in KNOWLEDGE_SOURCES.items():
        candidate = project_root / fname
        if candidate.exists():
            sources[key] = str(candidate)

    # Memory directory (Claude Code's project-specific memory)
    # Located at ~/.claude/projects/<encoded-path>/memory/
    # Encoding: every non-alphanumeric, non-dash char becomes a dash (no collapsing)
    encoded = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in str(project_root))
    memory_dir = Path.home() / ".claude" / "projects" / encoded / "memory"
    if memory_dir.exists():
        sources["memory_dir"] = str(memory_dir)
        for f in memory_dir.glob("*.md"):
            if f.name != "MEMORY.md":
                sources["memory_files"].append(str(f))

    # Docs folder
    docs_dir = project_root / "docs"
    if docs_dir.exists():
        for f in docs_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in DOC_EXTENSIONS:
                sources["docs"].append(str(f))

    # Emails folder
    emails_dir = project_root / "emails"
    if emails_dir.exists():
        for f in emails_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in DOC_EXTENSIONS:
                sources["emails"].append(str(f))

    # Reference docs
    for ref_name in ("Reference Doc", "reference", "refs"):
        ref_dir = project_root / ref_name
        if ref_dir.exists():
            for f in ref_dir.rglob("*"):
                if f.is_file() and f.suffix.lower() in DOC_EXTENSIONS:
                    sources["docs"].append(str(f))

    # Documents: .docx, .pdf, .xlsx, .xls, .pptx files (up to depth 3)
    doc_exts = {".docx", ".pdf", ".xlsx", ".xls", ".pptx"}
    documents = []
    for dirpath, dirnames, filenames in os.walk(project_root):
        # Compute depth relative to project root
        rel = Path(dirpath).relative_to(project_root)
        depth = len(rel.parts) if str(rel) != "." else 0
        if depth >= 3:
            dirnames.clear()
            continue
        # Skip hidden/ignored dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            if fname.startswith("."):
                continue
            fpath = Path(dirpath) / fname
            if fpath.suffix.lower() in doc_exts:
                documents.append(str(fpath))
    sources["documents"] = documents

    return sources


def scan_summary(project_root: Path) -> dict:
    """Full scan report: manifest diff + knowledge sources found."""
    diff = diff_manifest(project_root)
    sources = find_knowledge_sources(project_root)

    return {
        "project_root": str(project_root),
        "manifest_diff": {
            "is_first_scan": diff["is_first_scan"],
            "last_scan": diff["last_scan"],
            "new_files": len(diff["new"]),
            "changed_files": len(diff["changed"]),
            "removed_files": len(diff["removed"]),
            "unchanged_files": len(diff["unchanged"]),
            "total_files": diff["total_current"],
        },
        "files_to_process": [f["path"] for f in diff["new"] + diff["changed"]],
        "knowledge_sources": {
            "claude_local": sources["claude_local"],
            "claude_md": sources["claude_md"],
            "memory_dir": sources["memory_dir"],
            "memory_file_count": len(sources["memory_files"]),
            "memory_files": [Path(f).name for f in sources["memory_files"]],
            "doc_count": len(sources["docs"]),
            "email_count": len(sources["emails"]),
        },
        # Pass full data for CLI/skill consumption
        "_diff": diff,
        "_sources": sources,
    }
