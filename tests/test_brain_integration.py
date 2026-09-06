"""Integration tests for Brain DB operations — covers CRUD, relationships, threads, decisions, events, tags, changelog."""
import sqlite3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'systems', 'brain', 'skills', 'brain', 'scripts'))
from brain.operations import (
    create_project, get_project, list_projects,
    create_entity, upsert_entity, get_entity, find_entities, update_entity,
    create_relationship, get_relationships,
    create_task, update_task, list_tasks,
    create_thread, add_thread_item, list_threads,
    create_decision, list_decisions,
    create_event, list_events,
    ensure_tag, tag_item, get_tags,
)
from brain.schema import SCHEMA_V1


def get_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_V1)
    return conn


# ── Project Tests ──────────────────────────────────────────

def test_create_and_get_project():
    conn = get_conn()
    proj = create_project(conn, "Test Project", "test-proj", description="A test")
    assert proj["name"] == "Test Project"
    assert proj["slug"] == "test-proj"
    fetched = get_project(conn, "test-proj")
    assert fetched is not None
    assert fetched["id"] == proj["id"]
    print("PASS: create_and_get_project")


def test_list_projects():
    conn = get_conn()
    create_project(conn, "Alpha", "alpha")
    create_project(conn, "Beta", "beta")
    projects = list_projects(conn)
    assert len(projects) == 2
    names = [p["name"] for p in projects]
    assert "Alpha" in names and "Beta" in names
    print("PASS: list_projects")


def test_get_nonexistent_project():
    conn = get_conn()
    result = get_project(conn, "does-not-exist")
    assert result is None
    print("PASS: get_nonexistent_project")


# ── Entity Tests ───────────────────────────────────────────

def test_create_and_find_entities():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    create_entity(conn, proj["id"], "person", "Alice")
    create_entity(conn, proj["id"], "person", "Bob")
    create_entity(conn, proj["id"], "team", "Engineering")
    people = find_entities(conn, proj["id"], etype="person")
    assert len(people) == 2
    all_entities = find_entities(conn, proj["id"])
    assert len(all_entities) == 3
    print("PASS: create_and_find_entities")


def test_upsert_entity_creates_then_updates():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    e1 = upsert_entity(conn, proj["id"], "person", "Alice", external_id="ext-1")
    assert e1["name"] == "Alice"
    e2 = upsert_entity(conn, proj["id"], "person", "Alice Updated", external_id="ext-1")
    assert e2["id"] == e1["id"]
    assert e2["name"] == "Alice Updated"
    print("PASS: upsert_entity_creates_then_updates")


def test_find_entities_name_like():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    create_entity(conn, proj["id"], "person", "Alice Smith")
    create_entity(conn, proj["id"], "person", "Bob Jones")
    results = find_entities(conn, proj["id"], name_like="Alice")
    assert len(results) == 1
    assert results[0]["name"] == "Alice Smith"
    print("PASS: find_entities_name_like")


# ── Relationship Tests ─────────────────────────────────────

def test_create_and_get_relationships():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    alice = create_entity(conn, proj["id"], "person", "Alice")
    eng = create_entity(conn, proj["id"], "team", "Engineering")
    rel = create_relationship(conn, alice["id"], eng["id"], "member_of")
    assert rel["source_id"] == alice["id"]
    assert rel["target_id"] == eng["id"]
    rels = get_relationships(conn, alice["id"], direction="outgoing")
    assert len(rels) == 1
    assert rels[0]["target_name"] == "Engineering"
    print("PASS: create_and_get_relationships")


def test_relationship_idempotent():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    a = create_entity(conn, proj["id"], "person", "A")
    b = create_entity(conn, proj["id"], "person", "B")
    r1 = create_relationship(conn, a["id"], b["id"], "member_of")
    r2 = create_relationship(conn, a["id"], b["id"], "member_of")
    assert r1["id"] == r2["id"]
    print("PASS: relationship_idempotent")


# ── Task Tests ─────────────────────────────────────────────

def test_task_lifecycle():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    task = create_task(conn, proj["id"], "Build feature", priority=1)
    assert task["status"] == "open"
    updated = update_task(conn, task["id"], status="in_progress")
    assert updated["status"] == "in_progress"
    done = update_task(conn, task["id"], status="done")
    assert done["completed_at"] is not None
    open_tasks = list_tasks(conn, proj["id"], status="open")
    assert len(open_tasks) == 0
    print("PASS: task_lifecycle")


def test_task_blocked_by():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    t1 = create_task(conn, proj["id"], "Task 1")
    t2 = create_task(conn, proj["id"], "Task 2")
    update_task(conn, t2["id"], blocked_by_task_id=t1["id"])
    fetched = list_tasks(conn, proj["id"])
    t2_fetched = [t for t in fetched if t["id"] == t2["id"]][0]
    assert t2_fetched["blocked_by_task_id"] == t1["id"]
    print("PASS: task_blocked_by")


# ── Thread Tests ───────────────────────────────────────────

def test_thread_with_items():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    thread = create_thread(conn, proj["id"], "Access Request", category="request")
    task = create_task(conn, proj["id"], "Configure access")
    decision = create_decision(conn, proj["id"], "2026-09-06", "Use SSO")
    add_thread_item(conn, thread["id"], "task", task["id"])
    add_thread_item(conn, thread["id"], "decision", decision["id"])
    threads = list_threads(conn, proj["id"])
    assert len(threads) == 1
    assert threads[0]["category"] == "request"
    print("PASS: thread_with_items")


# ── Decision & Event Tests ─────────────────────────────────

def test_decisions_and_events():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    d = create_decision(conn, proj["id"], "2026-09-06", "Use PostgreSQL", decided_by="Alice")
    assert d["decision"] == "Use PostgreSQL"
    decisions = list_decisions(conn, proj["id"])
    assert len(decisions) == 1

    e = create_event(conn, proj["id"], "2026-09-06", "meeting", "Kickoff",
                     summary="Initial planning", participants=["Alice", "Bob"])
    assert e["title"] == "Kickoff"
    events = list_events(conn, proj["id"])
    assert len(events) == 1
    print("PASS: decisions_and_events")


# ── Tag Tests ──────────────────────────────────────────────

def test_tags():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    entity = create_entity(conn, proj["id"], "person", "Alice")
    tag_item(conn, "entity", entity["id"], "vip")
    tag_item(conn, "entity", entity["id"], "engineering")
    tag_item(conn, "entity", entity["id"], "vip")  # idempotent
    tags = get_tags(conn, "entity", entity["id"])
    assert set(tags) == {"vip", "engineering"}
    print("PASS: tags")


if __name__ == "__main__":
    test_create_and_get_project()
    test_list_projects()
    test_get_nonexistent_project()
    test_create_and_find_entities()
    test_upsert_entity_creates_then_updates()
    test_find_entities_name_like()
    test_create_and_get_relationships()
    test_relationship_idempotent()
    test_task_lifecycle()
    test_task_blocked_by()
    test_thread_with_items()
    test_decisions_and_events()
    test_tags()
    print("\nAll 13 integration tests passed")
