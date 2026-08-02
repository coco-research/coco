#!/usr/bin/env python3
"""Detect structural drift between .arch/index.json and the current working tree.

Entirely deterministic. Makes no model calls, reads no prompts, and reaches no
judgement. It answers three mechanical questions and writes them to
.arch/DRIFT.json:

  1. For each component, do its primary paths still resolve? The verdict follows the
     deletion-first rule: NONE surviving means REMOVE the component, SOME surviving
     means PRUNE the dead paths, ALL surviving means KEEP.
  2. Which files were added since the pin that no component claims?
  3. How large is the diff, and does that make a full rebuild cheaper than an
     incremental patch?

The `gate` field is computed here and never by a model:

  NONE          every verdict is KEEP and nothing unclaimed was added
  FULL_REBUILD  more than 300 files or 50,000 lines changed since the pin
  INCREMENTAL   anything else

Upstream threw an error at the change-magnitude threshold. Inverting it into a
full-rebuild escalation is a deliberate modification: a large diff is a normal event
and the correct response is to rebuild the index, not to refuse to look.

Usage:
    python3 arch_drift.py --repo-root .
    python3 arch_drift.py --repo-root . --index .arch/index.json --out .arch/DRIFT.json
    python3 arch_drift.py --repo-root . --stdout      # print, do not write

Exit codes: 0 when the scan completed (whatever it found), 2 when the scan could not
run at all. A scan that cannot run must never be interpreted as NO DRIFT.
"""

import argparse
import json
import os
import subprocess
import sys

FILES_THRESHOLD = 300
LINES_THRESHOLD = 50_000


def git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True
    ).stdout


def tracked_files(root):
    out = git(root, "ls-files", "-z")
    return {p for p in out.split("\0") if p}


def path_resolves(root, path, tracked):
    """A path resolves when git tracks it, or when it exists on disk.

    Directory claims are matched by prefix, because `git ls-files` lists files only.
    """
    full = os.path.join(root, path)
    if os.path.isdir(full):
        return True
    if os.path.isfile(full):
        return True
    prefix = path.rstrip("/") + "/"
    if any(f.startswith(prefix) for f in tracked):
        return True
    return path in tracked


def claimed_paths(index):
    """Every path any component claims, in any tier."""
    out = []
    for c in index.get("components") or []:
        own = c.get("codeOwnership") or {}
        for tier in ("primary", "shared"):
            block = own.get(tier) or {}
            out.extend(block.get("directories") or [])
            out.extend(block.get("files") or [])
    return out


def is_claimed(path, claims):
    for c in claims:
        if path == c:
            return True
        if path.startswith(c.rstrip("/") + "/"):
            return True
    return False


def main():
    ap = argparse.ArgumentParser(
        description="Deterministic structural drift scan against the pinned index."
    )
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--index", default=None, help="default: <repo-root>/.arch/index.json")
    ap.add_argument("--pin-file", default=None,
                    help="default: <repo-root>/.arch/pinned-commit")
    ap.add_argument("--out", default=None,
                    help="default: <repo-root>/.arch/DRIFT.json")
    ap.add_argument("--stdout", action="store_true",
                    help="print the result instead of writing it")
    args = ap.parse_args()

    root = os.path.abspath(args.repo_root)
    index_path = args.index or os.path.join(root, ".arch", "index.json")
    pin_path = args.pin_file or os.path.join(root, ".arch", "pinned-commit")
    out_path = args.out or os.path.join(root, ".arch", "DRIFT.json")

    try:
        with open(index_path) as fh:
            index = json.load(fh)
    except FileNotFoundError:
        print(f"cannot scan: index not found at {index_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"cannot scan: index is not valid JSON: {exc}", file=sys.stderr)
        return 2

    if index.get("ecosystem", {}).get("treeTruncated"):
        print(
            "cannot scan: the index was built from a TRUNCATED file tree. "
            "Deletion-first reconciliation treats the tree as the source of truth, "
            "so reconciling against a partial view would delete components whose "
            "code is merely unseen. Rebuild the index with a larger budget first.",
            file=sys.stderr,
        )
        return 2

    pin = index.get("pinnedCommit")
    if os.path.isfile(pin_path):
        with open(pin_path) as fh:
            file_pin = fh.read().strip()
        if file_pin:
            pin = file_pin

    try:
        head = git(root, "rev-parse", "HEAD").strip()
        tracked = tracked_files(root)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"cannot scan: git is unavailable or this is not a repository: {exc}",
              file=sys.stderr)
        return 2

    files_changed, lines_changed, added = 0, 0, []
    pin_valid = False
    if pin:
        try:
            git(root, "cat-file", "-e", f"{pin}^{{commit}}")
            pin_valid = True
        except subprocess.CalledProcessError:
            print(f"WARNING: pinned commit {pin} is not present in this repository; "
                  f"diff magnitude cannot be measured and the gate falls back to a "
                  f"path-existence scan only.", file=sys.stderr)

    if pin_valid and pin != head:
        name_status = git(root, "diff", "--name-status", f"{pin}..HEAD")
        for line in name_status.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            files_changed += 1
            if parts[0].startswith("A"):
                added.append(parts[-1])
        numstat = git(root, "diff", "--numstat", f"{pin}..HEAD")
        for line in numstat.splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            for n in parts[:2]:
                if n.isdigit():
                    lines_changed += int(n)

    claims = claimed_paths(index)
    components = []
    for c in index.get("components") or []:
        primary = (c.get("codeOwnership") or {}).get("primary") or {}
        paths = list(primary.get("directories") or []) + list(primary.get("files") or [])
        surviving = [p for p in paths if path_resolves(root, p, tracked)]
        dead = [p for p in paths if p not in surviving]
        if not paths:
            verdict = "REMOVE"
        elif not surviving:
            verdict = "REMOVE"
        elif dead:
            verdict = "PRUNE"
        else:
            verdict = "KEEP"
        components.append({
            "id": c.get("id"),
            "verdict": verdict,
            "survivingPaths": surviving,
            "deadPaths": dead,
        })

    unclaimed_added = [p for p in added if not is_claimed(p, claims)]
    unclaimed_top = sorted({p.split("/")[0] for p in unclaimed_added if "/" in p})

    if files_changed > FILES_THRESHOLD or lines_changed > LINES_THRESHOLD:
        gate = "FULL_REBUILD"
    elif all(c["verdict"] == "KEEP" for c in components) and not unclaimed_added:
        gate = "NONE"
    else:
        gate = "INCREMENTAL"

    result = {
        "pin": pin,
        "head": head,
        "pinValid": pin_valid,
        "filesChanged": files_changed,
        "linesChanged": lines_changed,
        "gate": gate,
        "components": components,
        "unclaimedAdded": unclaimed_added,
        "unclaimedTopLevelDirs": unclaimed_top,
        "scopeLimit": ("Structural drift only. Semantic drift inside an "
                       "already-claimed path is not detected by this scan."),
    }

    text = json.dumps(result, indent=2, sort_keys=False)
    if args.stdout:
        print(text)
    else:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as fh:
            fh.write(text + "\n")
        print(f"wrote {out_path}", file=sys.stderr)

    removes = [c["id"] for c in components if c["verdict"] == "REMOVE"]
    prunes = [c["id"] for c in components if c["verdict"] == "PRUNE"]
    print(f"gate={gate} filesChanged={files_changed} linesChanged={lines_changed} "
          f"REMOVE={removes or '-'} PRUNE={prunes or '-'} "
          f"unclaimedAdded={len(unclaimed_added)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
