"""
Folder scanning service for the Analyze Folder pipeline.

Recursively walks a folder, collects file metadata, reads text content,
and builds summaries. Uses only Python stdlib for file operations.
"""

from __future__ import annotations

import mimetypes
import os
import stat
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Extensions considered analyzable by default
DEFAULT_EXTENSIONS: set[str] = {
    ".md", ".txt", ".pdf", ".docx", ".csv", ".json", ".yaml", ".yml",
    ".html", ".py", ".ts", ".js", ".jsx", ".tsx", ".sql", ".sh", ".toml",
    ".cfg", ".ini", ".xml", ".rst", ".adoc", ".log",
}

# Directories to always skip
SKIP_DIRS: set[str] = {
    ".git", ".venv", ".env", "venv", "node_modules", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".tox", ".eggs", "dist", "build",
    ".next", ".nuxt", ".svelte-kit", "target", ".DS_Store",
}

# Extensions known to be binary (not readable as text)
BINARY_EXTENSIONS: set[str] = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".ico", ".webp",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    ".sqlite", ".db", ".hxd",
}


def _human_size(size_bytes: int) -> str:
    """Return a human-readable file size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def scan_folder(
    folder_path: str,
    extensions: list[str] | None = None,
    max_files: int = 100,
) -> list[dict]:
    """Recursively walk a folder and return file metadata.

    Returns a list of dicts sorted by modified_at descending:
        { "path": str, "name": str, "ext": str, "size_bytes": int, "modified_at": str }
    """
    root = os.path.expanduser(folder_path)
    if not os.path.isdir(root):
        return []

    allowed_exts: set[str] | None = None
    if extensions:
        allowed_exts = {e if e.startswith(".") else f".{e}" for e in extensions}

    files: list[dict] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden and excluded directories (modify in-place to prune walk)
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in SKIP_DIRS
        ]

        for fname in filenames:
            if fname.startswith("."):
                continue

            ext = os.path.splitext(fname)[1].lower()

            # Filter by extension
            if allowed_exts and ext not in allowed_exts:
                continue
            if not allowed_exts and ext and ext not in DEFAULT_EXTENSIONS:
                continue

            full_path = os.path.join(dirpath, fname)
            try:
                st = os.stat(full_path)
            except OSError:
                continue

            mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)

            files.append({
                "path": full_path,
                "name": fname,
                "ext": ext,
                "size_bytes": st.st_size,
                "modified_at": mtime.isoformat(),
            })

            if len(files) >= max_files * 3:
                # Early break if we have way more than needed; we'll sort and trim later
                break

    # Sort by modified_at descending, then trim
    files.sort(key=lambda f: f["modified_at"], reverse=True)
    return files[:max_files]


def read_file_content(path: str, max_chars: int = 50_000) -> str:
    """Read a file and return its text content, truncated to max_chars.

    For binary files, returns a summary string instead.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext in BINARY_EXTENSIONS:
        try:
            size = os.path.getsize(path)
            mime = mimetypes.guess_type(path)[0] or ext.upper().lstrip(".")
            return f"[Binary file: {_human_size(size)} {mime}]"
        except OSError:
            return "[Binary file: unable to read]"

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars + 100)
        if len(content) > max_chars:
            content = content[:max_chars] + "\n... (truncated)"
        return content
    except (OSError, UnicodeDecodeError):
        try:
            size = os.path.getsize(path)
            return f"[Unreadable file: {_human_size(size)}]"
        except OSError:
            return "[Unreadable file]"


def build_folder_summary(folder_path: str) -> str:
    """Return a markdown summary of a folder: file counts by type, total size, etc."""
    root = os.path.expanduser(folder_path)
    if not os.path.isdir(root):
        return f"Folder not found: {folder_path}"

    ext_counts: dict[str, int] = defaultdict(int)
    ext_sizes: dict[str, int] = defaultdict(int)
    total_files = 0
    total_size = 0
    recent_files: list[tuple[str, float]] = []  # (name, mtime)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in SKIP_DIRS
        ]

        for fname in filenames:
            if fname.startswith("."):
                continue
            full_path = os.path.join(dirpath, fname)
            try:
                st = os.stat(full_path)
            except OSError:
                continue

            ext = os.path.splitext(fname)[1].lower() or "(no ext)"
            ext_counts[ext] += 1
            ext_sizes[ext] += st.st_size
            total_files += 1
            total_size += st.st_size
            recent_files.append((os.path.relpath(full_path, root), st.st_mtime))

    # Sort recent files
    recent_files.sort(key=lambda x: x[1], reverse=True)

    lines: list[str] = [
        f"# Folder Summary: {os.path.basename(root)}",
        f"**Path:** `{root}`",
        f"**Total files:** {total_files}",
        f"**Total size:** {_human_size(total_size)}",
        "",
        "## Files by Type",
    ]

    # Sort by count descending
    for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- `{ext}`: {count} files ({_human_size(ext_sizes[ext])})")

    if recent_files:
        lines.append("")
        lines.append("## Recently Modified")
        for name, mtime in recent_files[:10]:
            dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            lines.append(f"- `{name}` -- {dt.strftime('%Y-%m-%d %H:%M')}")

    return "\n".join(lines)
