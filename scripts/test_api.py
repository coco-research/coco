#!/usr/bin/env python3
"""Deep integration tests for CoCo Platform API."""
import urllib.request
import urllib.error
import json
import sys

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0

def req(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    rq = urllib.request.Request(url, data=data, method=method)
    if data:
        rq.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(rq) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except:
            return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}

def check(desc, method, path, body=None, expect=200):
    global PASS, FAIL
    status, data = req(method, path, body)
    if status == expect:
        print(f"  ✓ {desc} ({method} {path} -> {status})")
        PASS += 1
    else:
        print(f"  ✗ {desc} ({method} {path} -> {status}, expected {expect})")
        print(f"    Response: {json.dumps(data)[:200]}")
        FAIL += 1
    return data

def check_field(desc, data, field, check_fn=None):
    global PASS, FAIL
    val = data.get(field) if isinstance(data, dict) else None
    ok = val is not None if check_fn is None else check_fn(val)
    if ok:
        print(f"  ✓ {desc} -> {str(val)[:80]}")
        PASS += 1
    else:
        print(f"  ✗ {desc} (field '{field}' = {val})")
        FAIL += 1

print("═" * 50)
print("  CoCo Platform — Deep Integration Tests")
print("═" * 50)
print()

# ── Health ──
print("▶ Health")
d = check("Health endpoint", "GET", "/api/health")
check_field("Status is ok", d, "status", lambda v: v == "ok")
check_field("Has version", d, "version")
check_field("Has uptime", d, "uptime_seconds", lambda v: isinstance(v, (int, float)))
check_field("Has databases", d, "databases", lambda v: isinstance(v, dict))
print()

# ── Dashboard ──
print("▶ Dashboard")
d = check("Dashboard endpoint", "GET", "/api/dashboard")
check_field("Has projects", d, "projects", lambda v: isinstance(v, list))
check_field("Has agents", d, "agents", lambda v: isinstance(v, dict))
check_field("Has costs", d, "costs", lambda v: isinstance(v, dict))
check_field("Has health", d, "health", lambda v: isinstance(v, list))
print()

# ── Projects ──
print("▶ Projects")
d = check("Projects list", "GET", "/api/projects")
if isinstance(d, list) and len(d) > 0:
    check_field("First project has name", d[0], "name")
    check_field("First project has id", d[0], "id")
    # Test project detail
    pid = d[0]["id"]
    pd = check("Project detail", "GET", f"/api/projects/{pid}")
else:
    print(f"  ℹ Projects list has {len(d) if isinstance(d, list) else 0} items (ok if KH is empty)")
print()

# ── Agent CRUD ──
print("▶ Agent CRUD")
d = check("Create agent", "POST", "/api/agents", {"name": "test-agent", "model": "haiku", "task_description": "test task"}, expect=201)
sid = d.get("id") if isinstance(d, dict) else None
if sid:
    print(f"  ℹ Created agent: {sid}")
    check("Get agent", "GET", f"/api/agents/{sid}")
    check("Update agent", "PATCH", f"/api/agents/{sid}", {"name": "renamed-agent"})
    d2 = check("Verify rename", "GET", f"/api/agents/{sid}")
    check_field("Name updated", d2, "name", lambda v: v == "renamed-agent")
    check("Get agent logs", "GET", f"/api/agents/{sid}/logs")
    check("Delete agent", "DELETE", f"/api/agents/{sid}")
    check("Deleted agent 404", "GET", f"/api/agents/{sid}", expect=404)
else:
    print(f"  ✗ Could not create agent: {d}")
    FAIL += 1
print()

# ── Task CRUD + Atomic Checkout ──
print("▶ Task CRUD + Atomic Checkout")
d = check("Create task", "POST", "/api/tasks", {"title": "Test checkout", "priority": "high"}, expect=201)
tid = d.get("id") if isinstance(d, dict) else None
if tid:
    print(f"  ℹ Created task: {tid}")
    check("Get task", "GET", f"/api/tasks/{tid}")
    check("Checkout task", "POST", f"/api/tasks/{tid}/checkout", {"checked_out_by": "station-a"})
    check("Double checkout → 409", "POST", f"/api/tasks/{tid}/checkout", {"checked_out_by": "station-b"}, expect=409)
    check("Release task", "POST", f"/api/tasks/{tid}/release")
    check("Re-checkout after release", "POST", f"/api/tasks/{tid}/checkout", {"checked_out_by": "station-b"})
    check("Release again", "POST", f"/api/tasks/{tid}/release")
    check("Update task", "PATCH", f"/api/tasks/{tid}", {"status": "done", "priority": "low"})
    d2 = check("Verify update", "GET", f"/api/tasks/{tid}")
    check_field("Status is done", d2, "status", lambda v: v == "done")
    check_field("Priority is low", d2, "priority", lambda v: v == "low")
else:
    print(f"  ✗ Could not create task: {d}")
    FAIL += 1
print()

# ── Content ──
print("▶ Content")
d = check("Content list", "GET", "/api/content?limit=5")
check_field("Has items array", d, "items", lambda v: isinstance(v, list))
check_field("Has total count", d, "total", lambda v: isinstance(v, int))
check("Content with search", "GET", "/api/content?q=test&limit=5")
check("Content filter source", "GET", "/api/content?source=email&limit=5")
print()

# ── Brain / Queue / Config ──
print("▶ Brain & Config")
d = check("Brain", "GET", "/api/brain")
check_field("Brain has people", d, "people", lambda v: isinstance(v, dict))
check_field("Brain has stats", d, "stats", lambda v: isinstance(v, dict))
check("People", "GET", "/api/brain/people")
check("Rules", "GET", "/api/brain/rules")
d = check("Queue", "GET", "/api/queue")
check_field("Queue has items", d, "items", lambda v: isinstance(v, list))
check("Config", "GET", "/api/config")
print()

# ── Costs ──
print("▶ Costs")
d = check("Cost summary", "GET", "/api/costs/summary")
check_field("Has total_usd", d, "total_usd", lambda v: isinstance(v, (int, float)))
check_field("Has by_model", d, "by_model", lambda v: isinstance(v, dict))
check("Cost events", "GET", "/api/costs/events?limit=5")
check("Budgets list", "GET", "/api/budgets")
check("Create budget", "POST", "/api/budgets", {"project_id": "test-proj", "monthly_cap_usd": 50.0}, expect=201)
print()

# ── Sessions ──
print("▶ Sessions")
d = check("Sessions list", "GET", "/api/sessions")
if isinstance(d, list):
    print(f"  ℹ {len(d)} sessions found")
print()

# ── Settings ──
print("▶ Settings")
check("Get settings", "GET", "/api/settings")
check("Patch settings", "PATCH", "/api/settings", {"_test": "value"})
print()

# ── Todos ──
print("▶ Todos")
check("Todos list", "GET", "/api/todos")
print()

# ── Drafts ──
print("▶ Drafts")
check("Drafts list", "GET", "/api/drafts")
print()

# ── Activity ──
print("▶ Activity")
check("Activity list", "GET", "/api/activity")
print()

# ── Agent Roles ──
print("▶ Agent Roles")
d = check("Agent roles list", "GET", "/api/agent-roles")
if isinstance(d, list):
    print(f"  ℹ {len(d)} agent roles found")
    if len(d) >= 4:
        print(f"  ✓ Has at least 4 default roles")
        PASS += 1
    else:
        print(f"  ✗ Expected at least 4 default roles, got {len(d)}")
        FAIL += 1
    # Check first role has expected fields
    if len(d) > 0:
        check_field("Role has slug", d[0], "slug")
        check_field("Role has name", d[0], "name")
d2 = check("Recruit agent", "POST", "/api/agents/recruit", {"node_id": "root", "role_slug": "developer"}, expect=201)
print()

# ── Chat ──
print("▶ Chat")
# POST /api/chat may return 501/503 if claude CLI not available, 200 if it is,
# or 0 if SSE stream closes immediately (connection refused / claude not installed)
status, _ = req("POST", "/api/chat", {"message": "hello"})
if status in (200, 501, 503, 0):
    print(f"  ✓ Chat POST returns {status} (expected 200, 501, 503, or 0)")
    PASS += 1
else:
    print(f"  ✗ Chat POST returns {status} (expected 200, 501, 503, or 0)")
    FAIL += 1
check("Chat history", "GET", "/api/chat/history")
check("Clear chat history", "DELETE", "/api/chat/history")
# Verify history is empty after clear
d = check("Chat history after clear", "GET", "/api/chat/history")
if isinstance(d, list) and len(d) == 0:
    print(f"  ✓ Chat history is empty after clear")
    PASS += 1
elif isinstance(d, list):
    print(f"  ✗ Chat history still has {len(d)} messages after clear")
    FAIL += 1
print()

# ── Tree CRUD ──
print("▶ Tree CRUD")
d = check("Tree root", "GET", "/api/tree")
root_id = None
if isinstance(d, dict):
    check_field("Has id (root node)", d, "id")
    root_id = d.get("id")
elif isinstance(d, list) and len(d) > 0:
    check_field("First node has id", d[0], "id")
    root_id = d[0].get("id")

child_id = None
if root_id:
    child = check("Create child node", "POST", "/api/tree", {"parent_id": root_id, "label": "Test Child", "node_type": "team"}, expect=201)
    child_id = child.get("id") if isinstance(child, dict) else None

if child_id:
    print(f"  ℹ Created tree node: {child_id}")
    d2 = check("Get tree node", "GET", f"/api/tree/{child_id}")
    check_field("Node has label", d2, "label")
    check("Rename tree node", "PATCH", f"/api/tree/{child_id}", {"label": "Renamed Child"})
    d3 = check("Verify rename", "GET", f"/api/tree/{child_id}")
    check_field("Label updated", d3, "label", lambda v: v == "Renamed Child")
    # Move node (may not have another parent; try moving to root again)
    check("Move tree node", "POST", f"/api/tree/{child_id}/move", {"new_parent_id": root_id})
    check("Delete tree node", "DELETE", f"/api/tree/{child_id}")
else:
    print("  ℹ Skipped tree CRUD (no root node to create children under)")

check("Unplaced items", "GET", "/api/tree/unplaced")
print()

# ── Teams (alias for Projects) ──
print("▶ Teams")
teams = check("Teams list", "GET", "/api/teams")
projects = check("Projects list (compare)", "GET", "/api/projects")
if isinstance(teams, list) and isinstance(projects, list):
    if len(teams) == len(projects):
        print(f"  ✓ Teams and Projects return same count ({len(teams)})")
        PASS += 1
    else:
        print(f"  ✗ Teams ({len(teams)}) != Projects ({len(projects)}) count mismatch")
        FAIL += 1
print()

# ── Collaboration ──
print("▶ Collaboration")
# Workflow templates
d = check("List workflow templates", "GET", "/api/workflow-templates")
if isinstance(d, list):
    has_fd = any(t.get("name") == "Feature Development" for t in d)
    if has_fd:
        print(f"  ✓ Has Feature Development template")
        PASS += 1
    else:
        print(f"  ✗ Missing Feature Development template")
        FAIL += 1

# Project context
check("Create context section", "POST", "/api/nodes/root/context",
      {"section": "brief", "title": "Test Brief", "content": "This is a test brief", "author_role": "product-manager"}, expect=201)
check("List context", "GET", "/api/nodes/root/context")

# Start workflow
check("Start workflow", "POST", "/api/nodes/root/workflows",
      {"template_id": "feature-development", "objective": "Test workflow"}, expect=201)
check("Get active workflow", "GET", "/api/nodes/root/workflows/active")

# Handoffs
check("List handoffs", "GET", "/api/nodes/root/handoffs")
print()

# ── Error Handling ──
print("▶ Error Handling")
check("Unknown agent → 404", "GET", "/api/agents/nonexistent-id", expect=404)
check("Unknown task → 404", "GET", "/api/tasks/nonexistent-id", expect=404)
print()

# ── Summary ──
print("═" * 50)
print(f"  Results: {PASS} passed, {FAIL} failed")
print("═" * 50)
sys.exit(1 if FAIL > 0 else 0)
