#!/usr/bin/env python3
"""Brain CLI — command-line interface to project_brain.db."""

import argparse
import json
import sys
from pathlib import Path

# Allow running as: python3 brain_cli.py (not just python3 -m brain.brain_cli)
sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------
# Knowledge layer path — add ~/.coco to sys.path so `knowledge` package is
# importable here without requiring it to be installed system-wide.
# All knowledge imports are deferred (inside cmd handlers) to avoid startup
# cost and to tolerate the case where knowledge.db doesn't exist yet.
# ---------------------------------------------------------------------------
_COCO_DIR = Path.home() / ".coco"
if str(_COCO_DIR) not in sys.path:
    sys.path.insert(0, str(_COCO_DIR))

from brain import resolve_db_path
from brain.schema import init_db, get_db, current_version
from brain.operations import (
    create_project, get_project, list_projects,
    create_entity, upsert_entity, find_entities, get_entity, update_entity,
    create_relationship, get_relationships,
    create_task, update_task, list_tasks,
    create_thread, add_thread_item, list_threads,
    create_decision, list_decisions,
    create_event, list_events,
    tag_item, get_tags,
)
from brain.queries import session_context, entity_graph, thread_detail, search_brain
from brain.scanner import scan_summary, update_manifest, diff_manifest, find_knowledge_sources
from brain.memory_bridge import verify_sync, health_check
from brain.exporter import export_claude_local, migrate_feedback_memories, main_export


def out(data):
    print(json.dumps(data, indent=2, default=str))


def err(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def cmd_init(args):
    db_path = resolve_db_path(args.db)
    conn = init_db(db_path)
    ver = current_version(conn)
    conn.close()
    out({"status": "ok", "db_path": str(db_path), "schema_version": ver})


def cmd_info(args):
    db_path = resolve_db_path(args.db)
    if not db_path.exists():
        err(f"No brain DB at {db_path}. Run 'init' first.")
    conn = get_db(db_path)
    ver = current_version(conn)
    tables = {}
    for t in ["projects", "entities", "relationships", "tasks", "threads",
              "decisions", "events", "changelog", "tags", "taggables"]:
        row = conn.execute(f"SELECT COUNT(*) as c FROM {t}").fetchone()
        tables[t] = row["c"]
    conn.close()
    out({"db_path": str(db_path), "schema_version": ver, "counts": tables})


def cmd_add_project(args):
    conn = get_db(resolve_db_path(args.db))
    result = create_project(conn, args.name, args.slug, args.desc or "")
    conn.close()
    out(result)


def cmd_projects(args):
    conn = get_db(resolve_db_path(args.db))
    out(list_projects(conn))
    conn.close()


def cmd_add_entity(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    meta = {}
    if args.meta:
        for kv in args.meta:
            k, v = kv.split("=", 1)
            meta[k] = v
    result = upsert_entity(conn, proj["id"], args.type, args.name,
                           args.external_id, meta or None)
    conn.close()
    out(result)


def cmd_entities(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    results = find_entities(conn, proj["id"], args.type, args.search)
    conn.close()
    out(results)


def cmd_add_rel(args):
    conn = get_db(resolve_db_path(args.db))
    result = create_relationship(conn, args.source, args.target, args.rel_type,
                                 args.context, getattr(args, "from", None), args.to)
    conn.close()
    out(result)


def cmd_rels(args):
    conn = get_db(resolve_db_path(args.db))
    results = get_relationships(conn, args.entity_id, args.direction)
    conn.close()
    out(results)


def cmd_add_task(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    result = create_task(conn, proj["id"], args.title, args.owner,
                         args.priority, args.due, args.notes)
    conn.close()
    out(result)


def cmd_update_task(args):
    conn = get_db(resolve_db_path(args.db))
    kwargs = {}
    if args.status:
        kwargs["status"] = args.status
    if args.notes:
        kwargs["notes"] = args.notes
    if args.owner:
        kwargs["owner_entity_id"] = args.owner
    result = update_task(conn, args.task_id, **kwargs)
    conn.close()
    out(result)


def cmd_tasks(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    results = list_tasks(conn, proj["id"], args.status)
    conn.close()
    out(results)


def cmd_add_thread(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    result = create_thread(conn, proj["id"], args.title, args.category)
    conn.close()
    out(result)


def cmd_threads(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    results = list_threads(conn, proj["id"], args.status)
    conn.close()
    out(results)


def cmd_link_thread(args):
    conn = get_db(resolve_db_path(args.db))
    result = add_thread_item(conn, args.thread_id, args.item_type, args.item_id)
    conn.close()
    out(result)


def cmd_add_decision(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    result = create_decision(conn, proj["id"], args.date, args.decision,
                             args.context, args.decided_by, args.impact, args.thread_id)
    conn.close()
    out(result)


def cmd_decisions(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    results = list_decisions(conn, proj["id"], args.limit)
    conn.close()
    out(results)


def cmd_add_event(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    participants = args.participants.split(",") if args.participants else []
    result = create_event(conn, proj["id"], args.date, args.type, args.title,
                          args.summary, args.source, participants)
    conn.close()
    out(result)


def cmd_events(args):
    conn = get_db(resolve_db_path(args.db))
    proj = get_project(conn, args.project)
    if not proj:
        err(f"Project '{args.project}' not found")
    results = list_events(conn, proj["id"], args.type, args.limit)
    conn.close()
    out(results)


def cmd_context(args):
    conn = get_db(resolve_db_path(args.db))
    if args.search:
        result = search_brain(conn, args.search, args.project)
    else:
        result = session_context(conn, args.project)
    conn.close()
    out(result)


def cmd_graph(args):
    conn = get_db(resolve_db_path(args.db))
    result = entity_graph(conn, args.entity_id)
    conn.close()
    out(result)


def cmd_thread_detail(args):
    conn = get_db(resolve_db_path(args.db))
    result = thread_detail(conn, args.thread_id)
    conn.close()
    out(result)


def cmd_verify(args):
    db_path = resolve_db_path(args.db)
    result = verify_sync(db_path, args.project_slug)
    status = "PASS" if result.get("ok") else "FAIL"
    print(f"[{status}] project={args.project_slug}  "
          f"expected={result['expected']}  actual={result['actual']}  "
          f"missing={result['missing']}  extra={result['extra']}")
    if result.get("missing_ids"):
        print("Missing drawer IDs (first 5):")
        for mid in result["missing_ids"]:
            print(f"  {mid}")
    out(result)


def cmd_health(args):
    db_path = resolve_db_path(args.db)
    report = health_check(db_path, args.project_slug)

    print(f"\n=== Brain Health Report: {args.project_slug} ===\n")

    db = report["brain_db"]
    print(f"Brain DB:   exists={db['exists']}  "
          f"entities={db['entities']}  decisions={db['decisions']}  events={db['events']}")

    mp = report["mempalace"]
    print(f"MemPalace:  available={mp['available']}  "
          f"total_drawers={mp['total_drawers']}  project_drawers={mp['project_drawers']}")

    bj = report["brain_json"]
    print(f"Brain JSON: exists={bj['exists']}  "
          f"people={bj['people_count']}  last_sync={bj['last_sync'] or 'never'}")

    ss = report["sync_status"]
    sync_label = "PASS" if ss.get("ok") else "FAIL"
    print(f"Sync:       [{sync_label}]  "
          f"expected={ss.get('expected', 0)}  actual={ss.get('actual', 0)}  "
          f"missing={ss.get('missing', 0)}  extra={ss.get('extra', 0)}")

    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  - {rec}")

    print()
    out(report)


def cmd_export(args):
    """Generate / refresh CLAUDE.local.md auto-section from brain DB."""
    main_export(args.db, args.project_slug, getattr(args, "output", None))


def cmd_scan(args):
    from pathlib import Path
    project_root = Path(args.root) if args.root else Path.cwd()
    if not project_root.is_dir():
        err(f"Not a directory: {project_root}")
    result = scan_summary(project_root)
    out(result)


def cmd_scan_update(args):
    """Mark scanned files in manifest after brain writes are done."""
    from pathlib import Path
    project_root = Path(args.root) if args.root else Path.cwd()
    diff = diff_manifest(project_root)
    processed = diff["new"] + diff["changed"]
    manifest = update_manifest(project_root, processed)
    out({"status": "ok", "files_updated": len(processed), "last_scan": manifest["last_scan"]})


def cmd_wiki(args):
    """Show a knowledge article by entity name or GID.

    Usage:
        brain wiki --name "Alice Example"
        brain wiki --gid 6ba7b810-...
        brain wiki --project my-project          # list all articles for project
    """
    try:
        from knowledge.search import get_article, search as _search
    except ImportError as exc:
        err(f"Knowledge layer not available: {exc}. Run 'wiki-generate' first.")

    gid = getattr(args, "gid", None)
    name = getattr(args, "name", None)
    project = getattr(args, "project", None)

    # List mode: no name or gid given — show all articles for a project
    if not gid and not name:
        if not project:
            err("Provide --name, --gid, or --project to list articles.")
        try:
            from knowledge.schema import get_knowledge_db
            conn = get_knowledge_db()
            rows = conn.execute("""
                SELECT a.gid, a.title, a.summary, a.confidence, a.generated_at
                FROM articles a
                INNER JOIN (
                    SELECT gid, MAX(version) AS v FROM articles GROUP BY gid
                ) latest ON a.gid = latest.gid AND a.version = latest.v
                JOIN global_entities ge ON ge.gid = a.gid
                ORDER BY a.title
            """).fetchall()
            conn.close()
            filtered = []
            for row in rows:
                # Filter by project via infobox_json if we can; else include all
                filtered.append({
                    "gid": row["gid"],
                    "title": row["title"],
                    "summary": (row["summary"] or "")[:120],
                    "confidence": row["confidence"],
                    "generated_at": row["generated_at"],
                })
            out({"project": project, "articles": filtered, "count": len(filtered)})
        except Exception as exc:
            err(f"Failed to list articles: {exc}")
        return

    # Fetch single article
    article = get_article(gid=gid, name=name)
    if not article:
        identifier = gid or name
        err(f"No article found for '{identifier}'. Run 'wiki-generate' to create one.")

    # If markdown file exists, print it; otherwise print structured JSON summary
    md = article.get("markdown")
    if md:
        print(md)
    else:
        out({
            "gid": article.get("gid"),
            "title": article.get("title"),
            "summary": article.get("summary"),
            "confidence": article.get("confidence"),
            "generated_at": article.get("generated_at"),
            "version": article.get("version"),
            "infobox": article.get("infobox", {}),
            "body_text": (article.get("body_text") or "")[:2000],
            "note": "No markdown file found — article exists in DB only.",
        })


def cmd_wiki_search(args):
    """Search the knowledge base with unified FTS5 + semantic search.

    Usage:
        brain wiki-search "Alice Example"
        brain wiki-search "vendor onboarding process" --project my-project
        brain wiki-search "VendorPortal" --limit 5
    """
    try:
        from knowledge.search import search as knowledge_search
    except ImportError as exc:
        err(f"Knowledge layer not available: {exc}. Run 'wiki-generate' first.")

    project = getattr(args, "project", None)
    limit = getattr(args, "limit", 10)

    results = knowledge_search(args.query, project=project, limit=limit)

    if not results:
        print(f"No results for '{args.query}'")
        if project:
            print(f"  (filtered to project: {project})")
        return

    # Human-readable table to stdout
    print(f"\nKnowledge search: '{args.query}'")
    if project:
        print(f"  Project filter:   {project}")
    print(f"  Results:          {len(results)}\n")
    fmt = "{:<36}  {:<40}  {:>6}  {:<10}  {:<8}"
    header = fmt.format("GID (short)", "Title", "Conf", "Generated", "Source")
    print(header)
    print("-" * len(header))
    for r in results:
        gid_short = (r.get("gid") or "")[:36]
        title = (r.get("title") or "")[:40]
        conf = f"{r.get('confidence', 0):.2f}" if r.get("confidence") is not None else "n/a"
        gen = (r.get("generated_at") or "")[:10]
        source = r.get("source", "")[:8]
        print(fmt.format(gid_short, title, conf, gen, source))

    print()
    # Also emit JSON for programmatic callers that parse stdout
    out(results)


def cmd_wiki_generate(args):
    """Generate or refresh knowledge articles.

    Usage:
        brain wiki-generate --project my-project
        brain wiki-generate --project my-project --entity "Alice Example"
        brain wiki-generate --project my-project --force
        brain wiki-generate --all
    """
    try:
        from knowledge.engine import KnowledgeEngine
    except ImportError as exc:
        err(f"Knowledge engine not available: {exc}. Check ~/.coco/knowledge/engine.py exists.")

    project_slug = getattr(args, "project_slug", None)
    entity_name = getattr(args, "entity_name", None)
    force = getattr(args, "force", False)
    all_projects = getattr(args, "all_projects", False)

    if not project_slug and not all_projects:
        err("Provide --project <slug> or --all to generate articles for all registered projects.")

    try:
        engine = KnowledgeEngine()
    except Exception as exc:
        err(f"Failed to initialize KnowledgeEngine: {exc}")

    try:
        if entity_name and project_slug:
            # Single-entity generation
            registered = engine.load_registered_projects()
            target = next((p for p in registered if p["slug"] == project_slug), None)
            if not target:
                err(f"Project '{project_slug}' not registered. "
                    f"Run: brain wiki-register --slug {project_slug} --db <path>")
            all_evidence = engine.harvest_evidence(target["db_path"], project_slug, since=None)
            # Filter to matching entity
            entity_evidence = [
                e for e in all_evidence
                if entity_name.lower() in e.get("entity_name", "").lower()
            ]
            if not entity_evidence:
                err(f"Entity '{entity_name}' not found in project '{project_slug}'.")
            generated = 0
            skipped = 0
            for ev in entity_evidence:
                result = engine.generate_for_entity(ev, force=force)
                if result:
                    generated += 1
                    print(f"  Generated: {result.get('title')} (confidence={result.get('confidence', 0):.2f})")
                else:
                    skipped += 1
            out({"status": "ok", "generated": generated, "skipped": skipped,
                 "entity_filter": entity_name, "project": project_slug})
        else:
            # Full project / all-projects generation
            summary = engine.generate_articles(
                project_slug=project_slug if not all_projects else None,
                force=force,
            )
            out({"status": "ok", **summary})
    except Exception as exc:
        err(f"Generation failed: {exc}")


def build_parser():
    p = argparse.ArgumentParser(prog="brain", description="Project Brain CLI")
    p.add_argument("--db", help="Explicit path to project_brain.db")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize brain DB in current directory")
    sub.add_parser("info", help="Show DB info and table counts")

    ap = sub.add_parser("add-project", help="Create a project")
    ap.add_argument("name")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--desc")

    sub.add_parser("projects", help="List projects")

    ae = sub.add_parser("add-entity", help="Add/upsert an entity")
    ae.add_argument("project", help="Project slug")
    ae.add_argument("type", choices=["person", "team", "role", "system", "module", "org_unit", "document"])
    ae.add_argument("name")
    ae.add_argument("--external-id")
    ae.add_argument("--meta", nargs="*", help="key=value pairs")

    le = sub.add_parser("entities", help="List entities")
    le.add_argument("project")
    le.add_argument("--type")
    le.add_argument("--search")

    ar = sub.add_parser("add-rel", help="Add a relationship")
    ar.add_argument("source", type=int)
    ar.add_argument("target", type=int)
    ar.add_argument("rel_type")
    ar.add_argument("--context")
    ar.add_argument("--from", dest="valid_from")
    ar.add_argument("--to")

    lr = sub.add_parser("rels", help="Show relationships")
    lr.add_argument("entity_id", type=int)
    lr.add_argument("--direction", default="both", choices=["both", "outgoing", "incoming"])

    at = sub.add_parser("add-task", help="Add a task")
    at.add_argument("project")
    at.add_argument("title")
    at.add_argument("--owner", type=int)
    at.add_argument("--priority", type=int, default=3)
    at.add_argument("--due")
    at.add_argument("--notes")

    ut = sub.add_parser("update-task", help="Update a task")
    ut.add_argument("task_id", type=int)
    ut.add_argument("--status")
    ut.add_argument("--notes")
    ut.add_argument("--owner", type=int)

    lt = sub.add_parser("tasks", help="List tasks")
    lt.add_argument("project")
    lt.add_argument("--status")

    ath = sub.add_parser("add-thread", help="Create a thread")
    ath.add_argument("project")
    ath.add_argument("title")
    ath.add_argument("--category", choices=["feature", "incident", "request", "decision", "research"])

    lth = sub.add_parser("threads", help="List threads")
    lth.add_argument("project")
    lth.add_argument("--status")

    lnk = sub.add_parser("link-thread", help="Link item to thread")
    lnk.add_argument("thread_id", type=int)
    lnk.add_argument("item_type")
    lnk.add_argument("item_id", type=int)

    ad = sub.add_parser("add-decision", help="Record a decision")
    ad.add_argument("project")
    ad.add_argument("date")
    ad.add_argument("decision")
    ad.add_argument("--context")
    ad.add_argument("--decided-by")
    ad.add_argument("--impact")
    ad.add_argument("--thread-id", type=int)

    ld = sub.add_parser("decisions", help="List decisions")
    ld.add_argument("project")
    ld.add_argument("--limit", type=int, default=20)

    aev = sub.add_parser("add-event", help="Record an event")
    aev.add_argument("project")
    aev.add_argument("date")
    aev.add_argument("type", choices=["meeting", "email", "call", "milestone", "deploy"])
    aev.add_argument("title")
    aev.add_argument("--summary")
    aev.add_argument("--source")
    aev.add_argument("--participants")

    lev = sub.add_parser("events", help="List events")
    lev.add_argument("project")
    lev.add_argument("--type")
    lev.add_argument("--limit", type=int, default=20)

    ctx = sub.add_parser("context", help="CoCo context dump")
    ctx.add_argument("project")
    ctx.add_argument("--search")

    gr = sub.add_parser("graph", help="Entity relationship graph")
    gr.add_argument("entity_id", type=int)

    td = sub.add_parser("thread-detail", help="Full thread with items")
    td.add_argument("thread_id", type=int)

    sc = sub.add_parser("scan", help="Scan project folder for knowledge sources and changes")
    sc.add_argument("--root", help="Project root directory (default: cwd)")

    scu = sub.add_parser("scan-update", help="Update manifest after brain writes complete")
    scu.add_argument("--root", help="Project root directory (default: cwd)")

    vfy = sub.add_parser("verify", help="Check brain DB records have matching MemPalace drawers")
    vfy.add_argument("project_slug", help="Project slug to verify")

    hlt = sub.add_parser("health", help="Full health report: brain DB, MemPalace, brain.json, and sync status")
    hlt.add_argument("project_slug", help="Project slug to report on")

    exp = sub.add_parser("export", help="Generate/refresh AUTO-GENERATED section in CLAUDE.local.md")
    exp.add_argument("project_slug", help="Project slug to export context for")
    exp.add_argument("--output", help="Output path for CLAUDE.local.md (default: same dir as brain DB)")

    # ── Knowledge / Wiki subcommands ──────────────────────────────────────────
    wk = sub.add_parser("wiki", help="Show knowledge article for an entity")
    wk.add_argument("--name", help="Entity canonical name to look up")
    wk.add_argument("--gid", help="Entity GID (UUID) to look up directly")
    wk.add_argument("--project", help="Project slug — if neither --name nor --gid, lists all articles for project")

    ws = sub.add_parser("wiki-search", help="Search knowledge articles (FTS5 + semantic)")
    ws.add_argument("query", help="Search query — proper names use exact FTS5, conceptual queries use semantic")
    ws.add_argument("--project", help="Filter results to a specific project slug")
    ws.add_argument("--limit", type=int, default=10, help="Max results to return (default: 10)")

    wg = sub.add_parser("wiki-generate", help="Generate or refresh knowledge articles")
    wg.add_argument("--project", dest="project_slug", help="Project slug to generate articles for")
    wg.add_argument("--entity", dest="entity_name", help="Entity name to generate a single article for")
    wg.add_argument("--force", action="store_true", help="Regenerate even if article is unchanged")
    wg.add_argument("--all", action="store_true", dest="all_projects",
                    help="Generate articles for all registered projects")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "init": cmd_init, "info": cmd_info,
        "add-project": cmd_add_project, "projects": cmd_projects,
        "add-entity": cmd_add_entity, "entities": cmd_entities,
        "add-rel": cmd_add_rel, "rels": cmd_rels,
        "add-task": cmd_add_task, "update-task": cmd_update_task, "tasks": cmd_tasks,
        "add-thread": cmd_add_thread, "threads": cmd_threads, "link-thread": cmd_link_thread,
        "add-decision": cmd_add_decision, "decisions": cmd_decisions,
        "add-event": cmd_add_event, "events": cmd_events,
        "context": cmd_context, "graph": cmd_graph, "thread-detail": cmd_thread_detail,
        "scan": cmd_scan, "scan-update": cmd_scan_update,
        "verify": cmd_verify, "health": cmd_health,
        "export": cmd_export,
        "wiki": cmd_wiki, "wiki-search": cmd_wiki_search, "wiki-generate": cmd_wiki_generate,
    }
    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        err(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
