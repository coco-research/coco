#!/usr/bin/env python3
"""Scan a tree for private employer patterns. `python3 scripts/employer-scan.py [DIR]`.

The patterns live outside the repo, in ~/.config/coco-private/employer-patterns.txt
(one case-insensitive literal per line; blank lines and '#' comments are skipped).
The scan fails CLOSED: a missing, unreadable or empty patterns file exits 2.
A patterns file whose mode is not 600 is used, with a warning.

The allowlist (`--allowlist`, default next to this script) exempts single lines,
matched by repo-relative path and sha256 of the exact original line. A missing
allowlist exempts nothing; a malformed entry exits 2.

A hit prints only `pattern N at file:line`, never the pattern text.
Exit 0 clean, 1 on any hit, 2 when the scan cannot run.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import stat
import sys
from collections import Counter
from pathlib import Path

DEFAULT = Path("~/.config/coco-private/employer-patterns.txt")
ALLOWLIST = Path(__file__).resolve().parent / "employer-scan-allowlist.txt"
ENTRY = re.compile(r"([0-9a-f]{64})  (\S.*)")


def load(path: Path) -> list[str]:
    """Patterns, lowercased. Raises OSError or ValueError when the scan must not run."""
    mode = stat.S_IMODE(os.stat(path).st_mode)
    if mode != 0o600:
        print(f"employer-scan: warning: {path} has mode {mode:o}, expected 600", file=sys.stderr)
    with open(path, encoding="utf-8") as handle:
        lines = [line.strip() for line in handle]
    found = [line.lower() for line in lines if line and not line.startswith("#")]
    if not found:
        raise ValueError("no patterns")
    return found


def load_allowlist(path: Path) -> Counter:
    """(path, sha256) -> count. A missing file exempts nothing; a bad line raises ValueError."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return Counter()
    allowed: Counter = Counter()
    for n, line in enumerate(text.splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        match = ENTRY.fullmatch(line)
        if not match:
            raise ValueError(f"bad allowlist line {n}")
        allowed[(match.group(2), match.group(1))] += 1
    return allowed


def files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != ".git")
        for name in sorted(filenames):
            yield Path(dirpath) / name


def scan(root: Path, patterns: list[str], allowed: Counter) -> tuple[list[str], int]:
    hits = []
    skipped = 0
    for path in files(root):
        rel = path.relative_to(root)
        for n, pattern in enumerate(patterns, 1):
            if pattern in str(rel).lower():
                hits.append(f"pattern {n} at {rel}:0")
        try:
            original = path.read_bytes().decode("utf-8", errors="ignore")
        except OSError:
            hits.append(f"unreadable at {rel}:0")
            continue
        for lineno, line in enumerate(original.splitlines(), 1):
            found = [
                f"pattern {n} at {rel}:{lineno}"
                for n, pattern in enumerate(patterns, 1)
                if pattern in line.lower()
            ]
            if not found:
                continue
            key = (rel.as_posix(), hashlib.sha256(line.encode("utf-8")).hexdigest())
            if allowed[key] > 0:
                allowed[key] -= 1
                skipped += 1
            else:
                hits.extend(found)
    return hits, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--patterns", default=str(DEFAULT), help=argparse.SUPPRESS)
    parser.add_argument("--allowlist", default=str(ALLOWLIST))
    args = parser.parse_args(argv)
    path = Path(args.patterns).expanduser()
    try:
        patterns = load(path)
    except (OSError, ValueError, UnicodeDecodeError):
        print(f"employer-scan: FAIL (closed): patterns file missing, unreadable or empty: {path}", file=sys.stderr)
        return 2
    try:
        allowed = load_allowlist(Path(args.allowlist).expanduser())
    except ValueError as exc:
        print(f"employer-scan: FAIL (closed): {exc}", file=sys.stderr)
        return 2
    except (OSError, UnicodeDecodeError):
        print(f"employer-scan: FAIL (closed): allowlist unreadable: {args.allowlist}", file=sys.stderr)
        return 2
    hits, skipped = scan(Path(args.root).resolve(), patterns, allowed)
    for hit in hits:
        print(hit)
    print(
        f"employer-scan: {len(hits)} hit(s) for {len(patterns)} pattern(s), "
        f"{skipped} allowlisted line(s) skipped",
        file=sys.stderr,
    )
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
