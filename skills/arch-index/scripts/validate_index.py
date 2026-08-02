#!/usr/bin/env python3
"""Validate .arch/index.json against the architecture index contract.

Twelve checks. Standard library only. Exit 0 when every check passes, exit 1 when
any check fails. Every violation prints one line to stdout naming the check, the
component it belongs to, and the offending value. The per-check summary table and
the path counters print to stderr, so a caller can count violations with `wc -l`
without the summary polluting the count.

This script is the gate. `team:architecture.md` describes the protocol in prose,
but every imperative in that document maps to a numbered check here — if a rule is
not implemented below, it is not enforced, and the prose must not claim otherwise.

Usage:
    python3 validate_index.py .arch/index.json --repo-root .
    python3 validate_index.py .arch/index.json --repo-root . --quiet

Upstream credit: the exact-path-matching guard implemented here as checks 5 and 6
comes from devildev by lak7 (Apache-2.0), which specified it in prose at
prompts/ReverseArchitecture.ts and never implemented it. See the Attribution
section of ../SKILL.md.
"""

import argparse
import json
import os
import re
import subprocess
import sys

SCHEMA_VERSIONS = {"1.0"}
MIN_COMPONENTS = 3
MAX_COMPONENTS = 8
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Check 10 — a component must describe what exists, not what someone hopes will
# exist. The index is reverse-only; a wishful title means a component was invented
# rather than observed.
WISHFUL = [
    "recommended", "proposed", "planned", "future", "should",
    "todo", "tbd", "suggested", "potential", "ideal", "missing",
    "desired", "target-state", "to-be", "wanted", "eventual",
]

# Check 11 — pure-infrastructure and pure-presentation titles are not components.
# They describe files rather than business capability. Deliberately excludes words
# like "cache" and "queue", which can legitimately be part of a capability name.
INFRA_ONLY = [
    "static assets", "config files", "configuration files", "build system",
    "ci/cd", "ci cd", "cicd", "logging", "monitoring", "observability",
    "dockerfile", "environment variables", "env vars", "linting",
    "package manifest", "dependencies", "node_modules", "gitignore",
    "boilerplate", "scaffolding", "misc", "miscellaneous", "utils", "utilities",
]


def tracked_files(root):
    """Return the set of git-tracked paths, or None when git is unavailable."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return {p for p in out.split("\0") if p}


class PathResolver:
    """Resolves a claimed path against the repository.

    A path resolves when git tracks it (for a directory, when git tracks anything
    beneath it) or when it exists on disk. The second condition is a deliberate
    hole for generated or gitignored directories that are genuinely part of the
    running system; those are counted and reported as `untracked-but-present`
    rather than failed, so the hole stays visible.
    """

    def __init__(self, root, tracked):
        self.root = root
        self.tracked = tracked
        self.verified = 0
        self.missing = 0
        self.untracked_but_present = 0

    def _is_tracked(self, path, as_dir):
        if self.tracked is None:
            return False
        if not as_dir:
            return path in self.tracked
        prefix = path.rstrip("/") + "/"
        return any(f.startswith(prefix) for f in self.tracked)

    def resolve(self, path, as_dir):
        full = os.path.join(self.root, path)
        on_disk = os.path.isdir(full) if as_dir else os.path.isfile(full)
        in_git = self._is_tracked(path, as_dir)
        if in_git:
            self.verified += 1
            return True
        if on_disk:
            self.verified += 1
            self.untracked_but_present += 1
            return True
        self.missing += 1
        return False


def load(path):
    try:
        with open(path) as fh:
            return json.load(fh), None
    except FileNotFoundError:
        return None, f"index not found: {path}"
    except json.JSONDecodeError as exc:
        return None, f"index is not valid JSON: {exc}"


def validate(index, resolver):
    """Run all twelve checks. Returns (violations, results).

    `violations` is a list of one-line strings. `results` is a list of
    (number, name, passed, detail) tuples for the summary table.
    """
    violations = []
    results = []

    def record(num, name, bad, detail):
        results.append((num, name, not bad, detail))

    components = index.get("components")
    if not isinstance(components, list):
        violations.append(
            "CHECK 2 component count in 3..8: <root>: `components` is missing or not a list"
        )
        record(2, "component count in 3..8", True, "components missing")
        return violations, results

    # 1 — schemaVersion known
    ver = index.get("schemaVersion")
    bad = ver not in SCHEMA_VERSIONS
    if bad:
        violations.append(
            f"CHECK 1 schemaVersion known: <root>: {ver!r} is not one of "
            f"{sorted(SCHEMA_VERSIONS)}"
        )
    record(1, "schemaVersion known", bad, str(ver))

    # 2 — component count within the ladder
    n = len(components)
    bad = not (MIN_COMPONENTS <= n <= MAX_COMPONENTS)
    if bad:
        violations.append(
            f"CHECK 2 component count in 3..8: <root>: found {n} components, "
            f"expected {MIN_COMPONENTS}..{MAX_COMPONENTS}"
        )
    record(2, "component count in 3..8", bad, str(n))

    # 3 — ids unique and kebab-case
    ids, dupes, malformed = [], [], []
    for c in components:
        cid = c.get("id", "")
        ids.append(cid)
        if not KEBAB.match(str(cid)):
            malformed.append(cid)
    seen = set()
    for cid in ids:
        if cid in seen:
            dupes.append(cid)
        seen.add(cid)
    for cid in malformed:
        violations.append(
            f"CHECK 3 ids unique, kebab-case: {cid!r}: id is not kebab-case"
        )
    for cid in dupes:
        violations.append(
            f"CHECK 3 ids unique, kebab-case: {cid!r}: id is duplicated"
        )
    record(3, "ids unique, kebab-case", bool(malformed or dupes),
           f"{len(set(ids))} unique of {len(ids)}")

    # 4 — every component declares at least one primary path
    no_primary = []
    for c in components:
        primary = (c.get("codeOwnership") or {}).get("primary") or {}
        if not (primary.get("directories") or primary.get("files")):
            no_primary.append(c.get("id"))
            violations.append(
                f"CHECK 4 every component has primary paths: {c.get('id')!r}: "
                f"codeOwnership.primary declares no directories and no files"
            )
    record(4, "every component has primary paths", bool(no_primary),
           f"{len(components) - len(no_primary)}/{len(components)}")

    # 5 and 6 — every claimed path resolves on disk
    tier_bad = {"primary": False, "shared": False}
    tier_counts = {"primary": [0, 0], "shared": [0, 0]}
    for tier, num in (("primary", 5), ("shared", 6)):
        for c in components:
            block = (c.get("codeOwnership") or {}).get(tier) or {}
            for kind, as_dir in (("directories", True), ("files", False)):
                for p in block.get(kind) or []:
                    tier_counts[tier][1] += 1
                    if resolver.resolve(p, as_dir):
                        tier_counts[tier][0] += 1
                    else:
                        tier_bad[tier] = True
                        violations.append(
                            f"CHECK {num} every {tier} path resolves on disk: "
                            f"{c.get('id')!r}: {p!r} does not exist"
                        )
        record(num, f"every {tier} path resolves on disk", tier_bad[tier],
               f"{tier_counts[tier][0]}/{tier_counts[tier][1]} verified")

    # 7 — no orphan components
    id_set = set(ids)
    orphans = []
    for c in components:
        if len(components) > 1 and not (c.get("connections") or []):
            orphans.append(c.get("id"))
            violations.append(
                f"CHECK 7 no orphan components: {c.get('id')!r}: declares no "
                f"connections, so it is unreachable in the component graph"
            )
    record(7, "no orphan components", bool(orphans),
           f"{len(components) - len(orphans)}/{len(components)} connected")

    # 8 — connections are bidirectional and point at real components
    by_id = {c.get("id"): c for c in components}
    asym, dangling = [], []
    for c in components:
        src = c.get("id")
        for dst in c.get("connections") or []:
            if dst not in id_set:
                dangling.append((src, dst))
                violations.append(
                    f"CHECK 8 connections bidirectional: {src!r}: connects to "
                    f"{dst!r}, which is not a component id"
                )
                continue
            back = by_id[dst].get("connections") or []
            if src not in back:
                asym.append((src, dst))
                violations.append(
                    f"CHECK 8 connections bidirectional: {src!r}: connects to "
                    f"{dst!r} but {dst!r} does not connect back to {src!r}"
                )
    edges = sum(len(c.get("connections") or []) for c in components) // 2
    record(8, "connections bidirectional", bool(asym or dangling),
           f"{edges} edges symmetric")

    # 9 — connectionLabels keys resolve to real edges
    labels = index.get("connectionLabels") or {}
    bad_labels = []
    real_edges = set()
    for c in components:
        for dst in c.get("connections") or []:
            real_edges.add(frozenset((c.get("id"), dst)))
    for key in labels:
        if "-to-" not in key:
            bad_labels.append(key)
            violations.append(
                f"CHECK 9 connectionLabels keys resolve to real edges: <root>: "
                f"{key!r} is not of the form <id>-to-<id>"
            )
            continue
        a, b = key.split("-to-", 1)
        if frozenset((a, b)) not in real_edges:
            bad_labels.append(key)
            violations.append(
                f"CHECK 9 connectionLabels keys resolve to real edges: <root>: "
                f"{key!r} names an edge that does not exist between {a!r} and {b!r}"
            )
    record(9, "connectionLabels keys resolve to real edges", bool(bad_labels),
           f"{len(labels) - len(bad_labels)}/{len(labels)}")

    # 10 — no wishful or aspirational titles
    wishful_hits = []
    for c in components:
        title = str(c.get("title", ""))
        low = title.lower()
        for word in WISHFUL:
            if re.search(rf"\b{re.escape(word)}\b", low):
                wishful_hits.append((c.get("id"), title, word))
                violations.append(
                    f"CHECK 10 no negative or wishful titles: {c.get('id')!r}: "
                    f"title {title!r} contains {word!r}; the index is reverse-only "
                    f"and must describe what exists"
                )
                break
    record(10, "no negative or wishful titles", bool(wishful_hits),
           f"{len(wishful_hits)} matches")

    # 11 — no pure-infrastructure titles
    infra_hits = []
    for c in components:
        low = str(c.get("title", "")).lower()
        for phrase in INFRA_ONLY:
            if phrase in low:
                infra_hits.append((c.get("id"), phrase))
                violations.append(
                    f"CHECK 11 no pure-infrastructure titles: {c.get('id')!r}: "
                    f"title contains {phrase!r}, which names files rather than a "
                    f"business capability"
                )
                break
    record(11, "no pure-infrastructure titles", bool(infra_hits),
           f"{len(infra_hits)} matches")

    # 12 — every rationale is non-empty
    empty_rationale, total_blocks = [], 0
    for c in components:
        own = c.get("codeOwnership") or {}
        for tier in ("primary", "shared"):
            block = own.get(tier)
            if not block:
                continue
            total_blocks += 1
            if not str(block.get("rationale", "")).strip():
                empty_rationale.append((c.get("id"), tier))
                violations.append(
                    f"CHECK 12 every rationale non-empty: {c.get('id')!r}: "
                    f"codeOwnership.{tier}.rationale is empty"
                )
    record(12, "every rationale non-empty", bool(empty_rationale),
           f"{total_blocks - len(empty_rationale)}/{total_blocks}")

    return violations, results


def main():
    ap = argparse.ArgumentParser(
        description="Validate an architecture index against the contract."
    )
    ap.add_argument("index", help="path to .arch/index.json")
    ap.add_argument("--repo-root", default=".", help="repository root (default: .)")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress the summary table on stderr")
    args = ap.parse_args()

    index, err = load(args.index)
    if err:
        # A validator that cannot read its input is a BLOCK, never a pass.
        print(f"CHECK 0 index readable: <root>: {err}")
        return 1

    root = os.path.abspath(args.repo_root)
    resolver = PathResolver(root, tracked_files(root))
    violations, results = validate(index, resolver)

    for line in violations:
        print(line)

    if not args.quiet:
        w = sys.stderr
        print(f"\nindex:     {args.index}", file=w)
        print(f"repo root: {root}", file=w)
        if resolver.tracked is None:
            print("git:       UNAVAILABLE — path checks fell back to on-disk "
                  "existence only", file=w)
        print("", file=w)
        print("| # | Check | Result | Detail |", file=w)
        print("|---|-------|--------|--------|", file=w)
        for num, name, ok, detail in sorted(results):
            print(f"| {num} | {name} | {'PASS' if ok else 'FAIL'} | {detail} |",
                  file=w)
        print("", file=w)
        print(f"paths verified: {resolver.verified} | "
              f"paths missing: {resolver.missing} | "
              f"untracked-but-present: {resolver.untracked_but_present}", file=w)
        print(f"violations: {len(violations)}", file=w)

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
