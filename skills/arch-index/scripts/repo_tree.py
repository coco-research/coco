#!/usr/bin/env python3
"""Produce a token-cheap, filtered file tree for architecture generation.

The pruning happens here, in code, rather than by asking a model to ignore noise.
That is the correct division of labour: a denylist is deterministic and free, and a
model instructed to "please disregard node_modules" still pays for the tokens.

Three behaviours matter and each exists because of a specific upstream failure.

Adaptive depth. Upstream capped directory depth at a fixed four levels, which makes
any monorepo layout invisible below its package directories. Here the depth is chosen
by measuring: the deepest level whose file count still fits the budget wins.

Truncation is a hard warning. Upstream captured a truncation flag and then never read
it in any caller, so a large repository silently yielded a partial tree that the
reconciliation prompt treated as authoritative and deleted real components from. Here
truncation prints a warning to stderr and sets `truncated` in the output, and the
skill refuses to run drift reconciliation against a truncated tree.

Real secrets are dropped, examples are kept. A `.env` file is excluded; `.env.example`
and its variants are kept, because the example is architecturally informative about
which services the system talks to and the real file is a credential.

Usage:
    python3 repo_tree.py --repo-root .
    python3 repo_tree.py --repo-root . --budget 1200 --max-depth 8
    python3 repo_tree.py --repo-root . --stats      # counts only, no tree

Output is JSON on stdout: {"root", "depth", "budget", "files", "dirs",
"truncated", "tree"}. The tree uses single-character keys — "d" for
subdirectories, "f" for files — to keep the serialisation small.
"""

import argparse
import json
import os
import sys

DENY_DIRS = {
    ".git", ".hg", ".svn",
    "node_modules", "bower_components", "jspm_packages",
    ".next", ".nuxt", ".svelte-kit", ".astro", ".docusaurus",
    "dist", "build", "out", "target", "bin_", "obj",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    ".venv", "venv", "env", ".env.d", "site-packages",
    ".idea", ".vscode", ".vs", ".fleet",
    ".cache", ".parcel-cache", ".turbo", ".yarn", ".pnpm-store",
    "coverage", "htmlcov", ".nyc_output",
    "vendor", "Pods", "Carthage", ".gradle", ".terraform",
    ".DS_Store", ".sass-cache", "tmp", "temp", ".tmp",
}

DENY_SUFFIXES = (".egg-info", ".dist-info", ".framework", ".xcworkspace")

DENY_FILE_EXT = {
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".class", ".o", ".a",
    ".log", ".lock", ".map", ".min.js", ".min.css",
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".mp4", ".mov", ".webm", ".mp3", ".wav", ".woff", ".woff2", ".ttf",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".pdf",
}

DENY_FILE_NAMES = {".DS_Store", "Thumbs.db", "package-lock.json",
                   "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
                   "Cargo.lock", "composer.lock", "uv.lock"}

ENV_KEEP_MARKERS = (".example", ".sample", ".template", ".dist", ".defaults")


def is_denied_dir(name):
    if name in DENY_DIRS:
        return True
    return any(name.endswith(s) for s in DENY_SUFFIXES)


def is_denied_file(name):
    if name in DENY_FILE_NAMES:
        return True
    # A real .env is a credential and is dropped; .env.example is informative.
    if name == ".env" or (name.startswith(".env")
                          and not any(m in name for m in ENV_KEEP_MARKERS)):
        return True
    lower = name.lower()
    return any(lower.endswith(e) for e in DENY_FILE_EXT)


def walk(root, max_depth):
    """Return (tree, file_count, dir_count) honouring max_depth.

    Depth 1 means the immediate children of the root.
    """
    file_count = 0
    dir_count = 0

    def rec(path, depth):
        nonlocal file_count, dir_count
        node = {}
        try:
            entries = sorted(os.scandir(path), key=lambda e: e.name)
        except (PermissionError, FileNotFoundError, OSError):
            return node
        files, dirs = [], {}
        for e in entries:
            try:
                if e.is_dir(follow_symlinks=False):
                    if is_denied_dir(e.name):
                        continue
                    if depth < max_depth:
                        dir_count += 1
                        dirs[e.name] = rec(e.path, depth + 1)
                    else:
                        # At the depth limit the directory is named but not entered.
                        dir_count += 1
                        dirs[e.name] = {"…": 1}
                elif e.is_file(follow_symlinks=False):
                    if is_denied_file(e.name):
                        continue
                    files.append(e.name)
                    file_count += 1
            except OSError:
                continue
        if files:
            node["f"] = files
        if dirs:
            node["d"] = dirs
        return node

    tree = rec(root, 1)
    return tree, file_count, dir_count


def choose_depth(root, budget, max_depth):
    """Pick the deepest level whose file count fits the budget.

    Returns (depth, tree, files, dirs, truncated). When even depth 1 exceeds the
    budget, depth 1 is returned with truncated set, because there is no shallower
    view available.
    """
    best = None
    for d in range(1, max_depth + 1):
        tree, files, dirs = walk(root, d)
        if files <= budget:
            best = (d, tree, files, dirs, False)
        else:
            if best is None:
                return (d, tree, files, dirs, True)
            break
    if best is None:
        tree, files, dirs = walk(root, 1)
        return (1, tree, files, dirs, True)
    return best


def main():
    ap = argparse.ArgumentParser(
        description="Emit a filtered, depth-adaptive file tree as compact JSON."
    )
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--budget", type=int, default=1200,
                    help="target maximum file count (default: 1200)")
    ap.add_argument("--max-depth", type=int, default=8,
                    help="ceiling on directory depth (default: 8)")
    ap.add_argument("--stats", action="store_true",
                    help="print counts only, omit the tree")
    args = ap.parse_args()

    root = os.path.abspath(args.repo_root)
    if not os.path.isdir(root):
        print(f"repo root is not a directory: {root}", file=sys.stderr)
        return 2

    depth, tree, files, dirs, truncated = choose_depth(
        root, args.budget, args.max_depth
    )

    if truncated:
        print(
            f"WARNING: tree is TRUNCATED. {files} files exceed the budget of "
            f"{args.budget} even at depth 1. The resulting view is partial. Do NOT "
            f"use it for drift reconciliation: deletion-first reconciliation treats "
            f"the tree as the source of truth and would delete components whose code "
            f"is merely unseen.",
            file=sys.stderr,
        )

    out = {
        "root": root,
        "depth": depth,
        "budget": args.budget,
        "maxDepth": args.max_depth,
        "files": files,
        "dirs": dirs,
        "truncated": truncated,
    }
    if not args.stats:
        out["tree"] = tree

    json.dump(out, sys.stdout, separators=(",", ":"), sort_keys=True)
    sys.stdout.write("\n")
    print(
        f"depth={depth} files={files} dirs={dirs} truncated={truncated}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
