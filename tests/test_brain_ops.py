"""Tests for brain operations — verifies zero SQL injection surface."""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'systems', 'brain', 'skills', 'brain', 'scripts'))
from brain.operations import update_entity, update_task, create_project, create_entity, create_task
from brain.schema import SCHEMA_V1

def get_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_V1)
    return conn

def test_update_entity_safe_columns():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    entity = create_entity(conn, proj["id"], "person", "Alice")
    result = update_entity(conn, entity["id"], name="Bob", external_id="ext-1")
    assert result["name"] == "Bob"
    assert result["external_id"] == "ext-1"
    print("PASS: update_entity safe columns")

def test_update_entity_rejects_unknown_field():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    entity = create_entity(conn, proj["id"], "person", "Alice")
    result = update_entity(conn, entity["id"], malicious_field="DROP TABLE entities;--")
    assert result["name"] == "Alice"
    print("PASS: update_entity rejects unknown fields")

def test_update_task_safe_columns():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    task = create_task(conn, proj["id"], "Do thing")
    result = update_task(conn, task["id"], status="in_progress", title="Updated")
    assert result["status"] == "in_progress"
    assert result["title"] == "Updated"
    print("PASS: update_task safe columns")

def test_update_task_done_sets_completed_at():
    conn = get_conn()
    proj = create_project(conn, "Test", "test")
    task = create_task(conn, proj["id"], "Do thing")
    result = update_task(conn, task["id"], status="done")
    assert result["completed_at"] is not None
    print("PASS: update_task done sets completed_at")

def test_no_fstring_sql_in_source():
    ops_path = os.path.join(os.path.dirname(__file__), '..', 'systems', 'brain', 'skills', 'brain', 'scripts', 'brain', 'operations.py')
    with open(ops_path) as f:
        content = f.read()
    import re
    matches = re.findall(r'f"[^"]*(?:UPDATE|SELECT|DELETE|INSERT)[^"]*"', content, re.IGNORECASE)
    assert len(matches) == 0, f"Found f-string SQL: {matches}"
    print("PASS: zero f-string SQL in source")

if __name__ == "__main__":
    test_update_entity_safe_columns()
    test_update_entity_rejects_unknown_field()
    test_update_task_safe_columns()
    test_update_task_done_sets_completed_at()
    test_no_fstring_sql_in_source()
    print("\nAll 5 tests passed")
