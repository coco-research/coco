"""Coco Learning System — CLI interface for learning commands.

Usage:
    python -m coco_learning.cli status [--project PROJECT_ID]
    python -m coco_learning.cli evolve --project PROJECT_ID
    python -m coco_learning.cli promote INSTINCT_ID --from-project PROJECT_ID
    python -m coco_learning.cli list [--project PROJECT_ID] [--domain DOMAIN]
    python -m coco_learning.cli delete INSTINCT_ID [--project PROJECT_ID]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from .detector import run_detection_cycle
from .models import Instinct
from .storage import (
    delete_instinct,
    ensure_dirs,
    get_global_dir,
    get_project_dir,
    list_instincts,
    load_instinct,
    save_instinct,
)


def cmd_status(args: argparse.Namespace) -> int:
    """Show learning system status and instinct summary."""
    project_id = args.project
    scopes = []
    if project_id:
        scopes.append(("project", project_id))
    scopes.append(("global", None))

    total = 0
    by_state: dict[str, int] = {}
    by_domain: dict[str, int] = {}

    for scope_name, pid in scopes:
        instincts = list_instincts(pid)
        print(f"\n=== {scope_name.title()} instincts ===")
        if not instincts:
            print("  (none)")
            continue
        for inst in instincts:
            total += 1
            by_state[inst.state] = by_state.get(inst.state, 0) + 1
            by_domain[inst.domain] = by_domain.get(inst.domain, 0) + 1
        print(f"  Count: {len(instincts)}")

    print(f"\nTotal active instincts: {total}")
    if by_state:
        print("By state:", ", ".join(f"{k}={v}" for k, v in sorted(by_state.items())))
    if by_domain:
        print("By domain:", ", ".join(f"{k}={v}" for k, v in sorted(by_domain.items())))

    # Check observations file size if project specified
    if project_id:
        obs_file = get_project_dir(project_id) / "observations.jsonl"
        if obs_file.exists():
            lines = sum(1 for _ in open(obs_file, encoding="utf-8"))
            size_kb = obs_file.stat().st_size / 1024
            print(f"\nObservations: {lines} entries ({size_kb:.1f} KB)")
        else:
            print("\nObservations: no data yet")

    return 0


def cmd_evolve(args: argparse.Namespace) -> int:
    """Run pattern detection cycle on project observations."""
    project_id = args.project
    if not project_id:
        print("Error: --project is required for evolve", file=sys.stderr)
        return 1

    instincts = run_detection_cycle(project_id, auto_save=True)
    if not instincts:
        print("No new patterns detected.")
        return 0

    print(f"Detected/reinforced {len(instincts)} instincts:")
    for inst in instincts:
        marker = "+" if inst.evidence_count <= 5 else "~"
        print(f"  {marker} [{inst.state}] {inst.pattern} "
              f"(confidence={inst.confidence}, evidence={inst.evidence_count})")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    """Promote a project-scoped instinct to global scope."""
    instinct_id = args.instinct_id
    project_id = args.from_project
    if not project_id:
        print("Error: --from-project is required for promote", file=sys.stderr)
        return 1

    inst = load_instinct(instinct_id, project_id)
    if inst is None:
        print(f"Error: instinct '{instinct_id}' not found in project '{project_id}'", file=sys.stderr)
        return 1

    if inst.promoted:
        print(f"Instinct '{instinct_id}' is already promoted.")
        return 0

    distinct_projects = 1  # At minimum the source project
    inst.promoted = True
    inst.updated_at = datetime.now(timezone.utc).isoformat()

    # Save to global
    save_instinct(inst, project_id=None)
    # Update project copy with promoted flag
    save_instinct(inst, project_id=project_id)

    print(f"Promoted '{instinct_id}' to global scope.")
    print(f"  Pattern: {inst.pattern}")
    print(f"  Confidence: {inst.confidence}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List instincts with optional filtering."""
    instincts = list_instincts(args.project)
    if args.domain:
        instincts = [i for i in instincts if i.domain == args.domain]

    if not instincts:
        print("No instincts found.")
        return 0

    for inst in sorted(instincts, key=lambda i: i.confidence, reverse=True):
        promo = " [GLOBAL]" if inst.promoted else ""
        print(f"  {inst.id} | {inst.state:10s} | conf={inst.confidence:.2f} | "
              f"ev={inst.evidence_count:3d} | {inst.domain:12s} | {inst.pattern}{promo}")
    print(f"\n{len(instincts)} instincts listed.")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete an instinct by ID."""
    deleted = delete_instinct(args.instinct_id, args.project)
    if deleted:
        print(f"Deleted instinct '{args.instinct_id}'.")
    else:
        print(f"Instinct '{args.instinct_id}' not found.", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="coco-learning", description="Coco Learning System CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # status
    p_status = sub.add_parser("status", help="Show learning system status")
    p_status.add_argument("--project", default=None, help="Project ID to inspect")

    # evolve
    p_evolve = sub.add_parser("evolve", help="Run pattern detection cycle")
    p_evolve.add_argument("--project", default=None, help="Project ID to scan")

    # promote
    p_promote = sub.add_parser("promote", help="Promote instinct to global")
    p_promote.add_argument("instinct_id", help="Instinct ID to promote")
    p_promote.add_argument("--from-project", required=True, help="Source project ID")

    # list
    p_list = sub.add_parser("list", help="List instincts")
    p_list.add_argument("--project", default=None, help="Project ID filter")
    p_list.add_argument("--domain", default=None, help="Domain filter")

    # delete
    p_delete = sub.add_parser("delete", help="Delete an instinct")
    p_delete.add_argument("instinct_id", help="Instinct ID to delete")
    p_delete.add_argument("--project", default=None, help="Project scope (omit for global)")

    args = parser.parse_args(argv)
    handlers = {
        "status": cmd_status,
        "evolve": cmd_evolve,
        "promote": cmd_promote,
        "list": cmd_list,
        "delete": cmd_delete,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
