#!/usr/bin/env python3
"""Declare an intended architecture, then check the build against it.

This is the forward counterpart to validate_index.py. The index describes code that
already exists; this describes code a build is about to write, and then checks whether
the build actually wrote it there.

Two modes, and the split is the whole point:

  --declare   Runs BEFORE the build, when the paths do not exist yet. Checks shape only:
              identifiers, symmetry, non-empty declarations, no path escapes. Deliberately
              does NOT check path existence, because nothing has been built.

  --verify    Runs AFTER the build, when the paths should exist. Checks that every path
              the plan declared is now real, and that nothing landed in a path the plan
              declared out of scope.

An earlier analysis rejected forward architecture specs on the grounds that path checking
has to be disabled for them, which removes the only check that matters. That is true if
you check at declaration time. It is false here, because the existence check is deferred
to --verify, after the build, where the paths are expected to exist. The check is not
weakened; it is moved, and moving it turns "describe what exists" into "did you build what
you said you would".

Usage:
    python3 verify_arch_plan.py .team-ship/ARCH-PLAN.json --declare
    python3 verify_arch_plan.py .team-ship/ARCH-PLAN.json --verify --repo-root .

Exit 0 when every check passes, 1 when any fails, 2 when the plan cannot be read.
Violations print one per line to stdout; the summary prints to stderr.
"""

import argparse
import json
import os
import re
import subprocess
import sys

SCHEMA_VERSIONS = {"1.0"}
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BUILD_STATUSES = {"new", "modified", "unchanged"}


def tracked_files(root):
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root,
            capture_output=True, text=True, check=True,
        ).stdout
        return {p for p in out.split("\0") if p}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()


def changed_since(root, commit):
    """Files changed between commit and HEAD, or None when unavailable."""
    if not commit:
        return None
    try:
        subprocess.run(["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                       cwd=root, capture_output=True, check=True)
        out = subprocess.run(["git", "diff", "--name-only", f"{commit}..HEAD"],
                             cwd=root, capture_output=True, text=True, check=True).stdout
        return [p for p in out.splitlines() if p]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def component_paths(c):
    block = c.get("intendedPaths") or {}
    return list(block.get("directories") or []), list(block.get("files") or [])


def resolves(root, path, as_dir, tracked):
    full = os.path.join(root, path)
    if as_dir and os.path.isdir(full):
        return True
    if not as_dir and os.path.isfile(full):
        return True
    prefix = path.rstrip("/") + "/"
    if as_dir and any(f.startswith(prefix) for f in tracked):
        return True
    return path in tracked


def under(path, prefix):
    return path == prefix or path.startswith(prefix.rstrip("/") + "/")


def check_shape(plan):
    """Checks valid at declaration time, before anything is built."""
    v = []
    comps = plan.get("components")
    if not isinstance(comps, list) or not comps:
        v.append("SHAPE 1 components present: <root>: `components` is missing or empty")
        return v

    if plan.get("schemaVersion") not in SCHEMA_VERSIONS:
        v.append(f"SHAPE 2 schemaVersion known: <root>: "
                 f"{plan.get('schemaVersion')!r} is not one of {sorted(SCHEMA_VERSIONS)}")

    ids, seen = [], set()
    for c in comps:
        cid = c.get("id", "")
        ids.append(cid)
        if not KEBAB.match(str(cid)):
            v.append(f"SHAPE 3 ids kebab-case: {cid!r}: id is not kebab-case")
        if cid in seen:
            v.append(f"SHAPE 3 ids unique: {cid!r}: id is duplicated")
        seen.add(cid)

    for c in comps:
        cid = c.get("id")
        st = c.get("status")
        if st not in BUILD_STATUSES:
            v.append(f"SHAPE 4 status valid: {cid!r}: status {st!r} is not one of "
                     f"{sorted(BUILD_STATUSES)}")
        dirs, files = component_paths(c)
        if not dirs and not files:
            v.append(f"SHAPE 5 intendedPaths declared: {cid!r}: declares no directories "
                     f"and no files, so nothing about it can ever be verified")
        if not str((c.get("intendedPaths") or {}).get("rationale", "")).strip():
            v.append(f"SHAPE 6 rationale non-empty: {cid!r}: intendedPaths.rationale is empty")
        if not str(c.get("title", "")).strip():
            v.append(f"SHAPE 7 title non-empty: {cid!r}: title is empty")
        # A declared path must be repo-relative. An absolute path or one escaping the
        # repository can never be verified and may point anywhere on the machine.
        for p in dirs + files:
            if os.path.isabs(p) or p.startswith("~"):
                v.append(f"SHAPE 8 paths repo-relative: {cid!r}: {p!r} is absolute")
            if ".." in p.split("/"):
                v.append(f"SHAPE 8 paths repo-relative: {cid!r}: {p!r} escapes the repository")

    by_id = {c.get("id"): c for c in comps}
    for c in comps:
        src = c.get("id")
        for dst in c.get("connections") or []:
            if dst not in by_id:
                v.append(f"SHAPE 9 connections resolve: {src!r}: connects to {dst!r}, "
                         f"which is not a declared component")
            elif src not in (by_id[dst].get("connections") or []):
                v.append(f"SHAPE 9 connections bidirectional: {src!r}: connects to "
                         f"{dst!r} but {dst!r} does not connect back")

    # Overlap between a component's paths and the out-of-scope list is a contradiction
    # that would make the plan unsatisfiable, so it is caught before the build starts.
    oos = plan.get("outOfScope") or []
    for c in comps:
        dirs, files = component_paths(c)
        for p in dirs + files:
            for o in oos:
                if under(p, o) or under(o, p):
                    v.append(f"SHAPE 10 scope not self-contradictory: {c.get('id')!r}: "
                             f"declares {p!r} while outOfScope lists {o!r}")
    return v


def check_built(plan, root):
    """Checks valid only after the build, when declared paths should exist."""
    v = []
    tracked = tracked_files(root)
    comps = plan.get("components") or []
    built = missing = 0

    for c in comps:
        cid = c.get("id")
        if c.get("status") == "unchanged":
            continue
        dirs, files = component_paths(c)
        for p, as_dir in [(d, True) for d in dirs] + [(f, False) for f in files]:
            if resolves(root, p, as_dir, tracked):
                built += 1
            else:
                missing += 1
                v.append(f"BUILT 1 declared path exists: {cid!r}: {p!r} was declared "
                         f"(status={c.get('status')}) but does not exist after the build")

    oos = plan.get("outOfScope") or []
    changed = changed_since(root, plan.get("declaredAtCommit"))
    violations = 0
    if changed is None:
        v.append("BUILT 2 out-of-scope respected: <root>: cannot compare against "
                 "declaredAtCommit, so out-of-scope enforcement is UNVERIFIED rather "
                 "than clean")
    else:
        for f in changed:
            for o in oos:
                if under(f, o):
                    violations += 1
                    v.append(f"BUILT 2 out-of-scope respected: <root>: {f!r} was changed "
                             f"but falls under declared out-of-scope path {o!r}")
                    break

    return v, {"built": built, "missing": missing,
               "changed": len(changed) if changed is not None else None,
               "oosViolations": violations}


def main():
    ap = argparse.ArgumentParser(
        description="Declare an intended architecture, then verify the build against it."
    )
    ap.add_argument("plan")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--declare", action="store_true",
                   help="pre-build shape checks only; does not check path existence")
    g.add_argument("--verify", action="store_true",
                   help="post-build checks; declared paths must now exist")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    try:
        with open(args.plan) as fh:
            plan = json.load(fh)
    except FileNotFoundError:
        print(f"PLAN 0 readable: <root>: plan not found at {args.plan}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"PLAN 0 readable: <root>: plan is not valid JSON: {exc}")
        return 2

    root = os.path.abspath(args.repo_root)
    violations = check_shape(plan)
    stats = None

    # Shape failures are reported alone. Running existence checks against a malformed
    # plan produces noise that hides the real problem.
    if args.verify and not violations:
        more, stats = check_built(plan, root)
        violations += more

    for line in violations:
        print(line)

    if not args.quiet:
        w = sys.stderr
        mode = "declare" if args.declare else "verify"
        print(f"\nplan:  {args.plan}", file=w)
        print(f"mode:  {mode}", file=w)
        print(f"components: {len(plan.get('components') or [])}", file=w)
        if stats:
            print(f"declared paths built: {stats['built']} | missing: {stats['missing']}",
                  file=w)
            ch = "unavailable" if stats["changed"] is None else stats["changed"]
            print(f"files changed since declaration: {ch} | "
                  f"out-of-scope violations: {stats['oosViolations']}", file=w)
        if args.declare:
            print("note: path existence is NOT checked in declare mode; that is what "
                  "--verify does after the build", file=w)
        print(f"violations: {len(violations)}", file=w)

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
