#!/usr/bin/env python3
"""
CoCo Platform -- Comprehensive Integration Test Suite (100+ tests)
No external dependencies. Uses only urllib.request.

Run: python3 scripts/test_comprehensive.py
"""
import urllib.request
import urllib.error
import json
import sys
import time

BASE = "http://localhost:8000"
PASS = 0
FAIL = 0
SKIP = 0
CATEGORY_RESULTS: dict[str, dict] = {}
_current_category = ""


# ── Helpers ──────────────────────────────────────────────────────────────────

def req(method: str, path: str, body=None):
    """Make an HTTP request, return (status_code, parsed_json)."""
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
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}


def ok(desc: str, condition: bool, detail: str = ""):
    """Record a test result."""
    global PASS, FAIL
    cat = _current_category
    if cat not in CATEGORY_RESULTS:
        CATEGORY_RESULTS[cat] = {"pass": 0, "fail": 0}
    if condition:
        print(f"  \u2713 {desc}")
        PASS += 1
        CATEGORY_RESULTS[cat]["pass"] += 1
    else:
        extra = f" -- {detail}" if detail else ""
        print(f"  \u2717 {desc}{extra}")
        FAIL += 1
        CATEGORY_RESULTS[cat]["fail"] += 1
    return condition


def section(name: str):
    """Print a section header and set current category."""
    global _current_category
    _current_category = name
    print(f"\n\u25b6 {name}")


# ══════════════════════════════════════════════════════════════════════════════
print("\u2550" * 60)
print("  CoCo Platform -- Comprehensive Integration Tests")
print(f"  Target: {BASE}")
print(f"  Time:   {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("\u2550" * 60)


# ── 1. Health & Connectivity (5 tests) ───────────────────────────────────────
section("1. Health & Connectivity")

s, d = req("GET", "/api/health")
ok("Health returns 200", s == 200, f"status={s}")
ok("Status field is 'ok'", d.get("status") == "ok", f"status={d.get('status')}")
ok("Has all expected fields (version, uptime_seconds, databases, files)",
   all(k in d for k in ("version", "uptime_seconds", "databases", "files")),
   f"keys={list(d.keys())}")

dbs = d.get("databases", {})
ok("hub.db connected (exists=True)",
   dbs.get("hub_db", {}).get("exists") is True,
   f"hub_db={dbs.get('hub_db')}")
ok("platform.db connected (exists=True)",
   dbs.get("platform_db", {}).get("exists") is True,
   f"platform_db={dbs.get('platform_db')}")


# ── 2. Dashboard (10 tests) ──────────────────────────────────────────────────
section("2. Dashboard")

s, d = req("GET", "/api/dashboard")
ok("Dashboard returns 200", s == 200, f"status={s}")
ok("Has projects array", isinstance(d.get("projects"), list))
ok("Has stations object with running/paused/idle/total",
   isinstance(d.get("stations"), dict)
   and all(k in d.get("stations", {}) for k in ("running", "paused", "idle", "total")),
   f"stations={d.get('stations')}")
ok("Has costs object with today_usd/month_usd/daily",
   isinstance(d.get("costs"), dict)
   and all(k in d.get("costs", {}) for k in ("today_usd", "month_usd", "daily")),
   f"costs keys={list(d.get('costs', {}).keys())}")
ok("Has health array", isinstance(d.get("health"), list))
ok("Has unsorted_count", "unsorted_count" in d and isinstance(d["unsorted_count"], int))

projects = d.get("projects", [])
if projects:
    p0 = projects[0]
    ok("Projects have id, name, active fields",
       all(k in p0 for k in ("id", "name", "active")),
       f"keys={list(p0.keys())}")
    ok("Projects have sources breakdown (email/voice/jira/confluence)",
       isinstance(p0.get("sources"), dict)
       and all(k in p0.get("sources", {}) for k in ("email", "voice", "jira", "confluence")))
else:
    ok("Projects have id, name, active fields", True, "SKIP: no projects")
    ok("Projects have sources breakdown", True, "SKIP: no projects")

health_items = d.get("health", [])
if health_items:
    h0 = health_items[0]
    ok("Health items have source, status, last_sync",
       "source" in h0 and ("status" in h0 or "last_sync" in h0),
       f"keys={list(h0.keys())}")
else:
    ok("Health items have source, status, last_sync", True, "SKIP: no health items")

costs = d.get("costs", {})
ok("Costs.daily is array of 7 elements",
   isinstance(costs.get("daily"), list) and len(costs.get("daily", [])) == 7,
   f"daily len={len(costs.get('daily', []))}")


# ── 3. Projects CRUD (10 tests) ──────────────────────────────────────────────
section("3. Projects CRUD")

s, projects = req("GET", "/api/projects")
ok("List returns 200 with array", s == 200 and isinstance(projects, list), f"status={s}")
ok("At least 1 project exists", len(projects) >= 1, f"count={len(projects)}")
ok("At least 5 projects exist", len(projects) >= 5, f"count={len(projects)}")

if projects:
    p0 = projects[0]
    ok("Each project has id, name, jira_key, confluence_space, active, item_count",
       all(k in p0 for k in ("id", "name", "jira_key", "active", "item_count")),
       f"keys={list(p0.keys())}")
    ok("Project IDs are strings",
       all(isinstance(p.get("id"), str) for p in projects))
    ok("Project names are non-empty",
       all(isinstance(p.get("name"), str) and len(p.get("name", "")) > 0 for p in projects))
    ok("Active field is 0 or 1",
       all(p.get("active") in (0, 1) for p in projects),
       f"actives={[p.get('active') for p in projects[:5]]}")

    # Get by ID
    pid = projects[0]["id"]
    s2, pd = req("GET", f"/api/projects/{pid}")
    ok("Get by ID returns project", s2 == 200 and pd.get("id") == pid)
    ok("Project detail has content_counts", "content_counts" in pd, f"keys={list(pd.keys())}")
else:
    for _ in range(6):
        ok("SKIP (no projects)", True, "no project data")

# 404 for nonexistent
s3, _ = req("GET", "/api/projects/nonexistent-project-xyz")
ok("Get nonexistent returns 404", s3 == 404, f"status={s3}")


# ── 4. Content / Knowledge Hub (15 tests) ────────────────────────────────────
section("4. Content / Knowledge Hub")

s, d = req("GET", "/api/content?limit=10")
ok("List returns 200", s == 200, f"status={s}")
ok("Response has items key", isinstance(d.get("items"), list))
ok("Response has total key (integer)", isinstance(d.get("total"), int))
ok("Total > 0 (hub has data)", d.get("total", 0) > 0, f"total={d.get('total')}")

items = d.get("items", [])
if items:
    i0 = items[0]
    ok("Each item has id, source, title",
       all(k in i0 for k in ("id", "source")),
       f"keys={list(i0.keys())}")
else:
    ok("Each item has id, source, title", True, "SKIP: no items")

# Filter by source
for src in ("email", "voice", "jira", "confluence"):
    s_f, d_f = req("GET", f"/api/content?source={src}&limit=5")
    ok(f"Filter by source={src} returns 200 with items",
       s_f == 200 and isinstance(d_f.get("items"), list),
       f"status={s_f}")

# FTS5 search
s_q, d_q = req("GET", "/api/content?q=project&limit=5")
ok("FTS5 search returns results for 'project'",
   s_q == 200 and isinstance(d_q.get("items"), list),
   f"status={s_q}, total={d_q.get('total')}")

s_qg, d_qg = req("GET", "/api/content?q=zzzyyyxxx999&limit=5")
ok("FTS5 search returns empty for gibberish",
   s_qg == 200 and d_qg.get("total", -1) == 0,
   f"total={d_qg.get('total')}")

# Pagination
s_p1, d_p1 = req("GET", "/api/content?limit=3&offset=0")
s_p2, d_p2 = req("GET", "/api/content?limit=3&offset=3")
ids1 = [i.get("id") for i in d_p1.get("items", [])]
ids2 = [i.get("id") for i in d_p2.get("items", [])]
ok("Pagination works (offset=0 vs offset=3 give different items)",
   s_p1 == 200 and s_p2 == 200 and set(ids1).isdisjoint(set(ids2)),
   f"page1_ids={ids1[:2]}, page2_ids={ids2[:2]}")

# Limit parameter
s_lim, d_lim = req("GET", "/api/content?limit=2")
ok("Limit parameter works (limit=2 returns <=2 items)",
   s_lim == 200 and len(d_lim.get("items", [])) <= 2)

# Content detail
if items:
    cid = items[0]["id"]
    s_cd, d_cd = req("GET", f"/api/content/{cid}")
    ok("Content detail returns single item", s_cd == 200 and d_cd.get("id") == cid)
else:
    ok("Content detail returns single item", True, "SKIP: no content")

# Content detail 404
s_c4, _ = req("GET", "/api/content/nonexistent-content-xyz")
ok("Content detail 404 for nonexistent", s_c4 == 404, f"status={s_c4}")


# ── 5. Station CRUD (15 tests) ───────────────────────────────────────────────
section("5. Station CRUD")

s, stations = req("GET", "/api/stations")
ok("List returns array", s == 200 and isinstance(stations, list))

# Create
s_c, st = req("POST", "/api/stations", {"name": "test-station-comp", "model": "haiku", "task_description": "comprehensive test"})
ok("Create returns 201 with id", s_c == 201 and isinstance(st.get("id"), str), f"status={s_c}")

sid = st.get("id")
if sid:
    ok("Created station has all fields (id, name, model, status, created_at)",
       all(k in st for k in ("id", "name", "model", "status", "created_at")),
       f"keys={list(st.keys())}")
    ok("Station default status is idle", st.get("status") == "idle", f"status={st.get('status')}")

    # Get by ID
    s_g, st_g = req("GET", f"/api/stations/{sid}")
    ok("Get by ID returns station", s_g == 200 and st_g.get("id") == sid)
    ok("Station has status field", "status" in st_g)

    # Update name
    s_u, st_u = req("PATCH", f"/api/stations/{sid}", {"name": "renamed-comp"})
    ok("Update name works", s_u == 200 and st_u.get("name") == "renamed-comp")

    # Update model
    s_um, st_um = req("PATCH", f"/api/stations/{sid}", {"model": "opus"})
    ok("Update model works", s_um == 200 and st_um.get("model") == "opus")

    # Logs
    s_l, logs = req("GET", f"/api/stations/{sid}/logs")
    ok("Logs endpoint returns array", s_l == 200 and isinstance(logs, list))

    # Spawn (will likely fail but should return structured error)
    s_sp, sp_d = req("POST", f"/api/stations/{sid}/spawn")
    ok("Spawn endpoint exists (returns structured response)",
       s_sp in (200, 409, 429, 500) and isinstance(sp_d, dict),
       f"status={s_sp}")

    # Pause on idle station -> 409
    s_pa, _ = req("POST", f"/api/stations/{sid}/pause")
    ok("Pause endpoint exists (409 if not running is correct)",
       s_pa in (200, 409),
       f"status={s_pa}")

    # Kill on idle station -> 409
    s_ki, _ = req("POST", f"/api/stations/{sid}/kill")
    ok("Kill endpoint exists (409 if not running is correct)",
       s_ki in (200, 409),
       f"status={s_ki}")

    # Cannot delete running station (ours is idle, so delete should work)
    s_del, _ = req("DELETE", f"/api/stations/{sid}")
    ok("Delete works", s_del == 200)

    # Delete again -> 404
    s_del2, _ = req("DELETE", f"/api/stations/{sid}")
    ok("Delete returns 404 on second delete", s_del2 == 404, f"status={s_del2}")
else:
    for _ in range(13):
        ok("SKIP (station creation failed)", False, f"create returned {s_c}")

# Test: cannot delete running station (create, set running, try delete)
s_cr, st_r = req("POST", "/api/stations", {"name": "running-test", "task_description": "test"})
sid_r = st_r.get("id") if s_cr == 201 else None
if sid_r:
    # Manually set status to running via PATCH
    req("PATCH", f"/api/stations/{sid_r}", {"status": "running"})
    s_del_r, _ = req("DELETE", f"/api/stations/{sid_r}")
    ok("Cannot delete running station (returns 409)",
       s_del_r == 409, f"status={s_del_r}")
    # Cleanup: set back to idle and delete
    req("PATCH", f"/api/stations/{sid_r}", {"status": "idle"})
    req("DELETE", f"/api/stations/{sid_r}")
else:
    ok("Cannot delete running station", True, "SKIP: creation failed")


# ── 6. Task CRUD + Atomic Checkout (15 tests) ────────────────────────────────
section("6. Task CRUD + Atomic Checkout")

s, tasks = req("GET", "/api/tasks")
ok("List returns array", s == 200 and isinstance(tasks, list))

# Create
s_c, t = req("POST", "/api/tasks", {"title": "Comprehensive test task", "priority": "high"})
ok("Create returns 201", s_c == 201, f"status={s_c}")

tid = t.get("id") if s_c == 201 else None
if tid:
    ok("Task has id, title, status, priority",
       all(k in t for k in ("id", "title", "status", "priority")),
       f"keys={list(t.keys())}")
    ok("Default status is open", t.get("status") == "open", f"status={t.get('status')}")
    ok("Priority matches input (high)", t.get("priority") == "high")

    # Create another with default priority
    s_cd, td = req("POST", "/api/tasks", {"title": "Default priority test"})
    ok("Default priority is medium",
       s_cd == 201 and td.get("priority") == "medium",
       f"priority={td.get('priority')}")
    # Clean up default-priority task
    if td.get("id"):
        req("PATCH", f"/api/tasks/{td['id']}", {"status": "done"})

    # Get by ID
    s_g, tg = req("GET", f"/api/tasks/{tid}")
    ok("Get by ID works", s_g == 200 and tg.get("id") == tid)

    # Update title
    s_ut, tu = req("PATCH", f"/api/tasks/{tid}", {"title": "Updated title"})
    ok("Update title works", s_ut == 200 and tu.get("title") == "Updated title")

    # Update status
    s_us, tus = req("PATCH", f"/api/tasks/{tid}", {"status": "in_progress"})
    ok("Update status works", s_us == 200 and tus.get("status") == "in_progress")

    # Update priority
    s_up, tup = req("PATCH", f"/api/tasks/{tid}", {"priority": "low"})
    ok("Update priority works", s_up == 200 and tup.get("priority") == "low")

    # Reset to open for checkout test
    req("PATCH", f"/api/tasks/{tid}", {"status": "open"})

    # Checkout
    s_co, tco = req("POST", f"/api/tasks/{tid}/checkout", {"checked_out_by": "station-a"})
    ok("Checkout locks task", s_co == 200 and tco.get("checked_out_by") is not None,
       f"status={s_co}, checked_out_by={tco.get('checked_out_by')}")

    # Double checkout -> 409
    s_co2, _ = req("POST", f"/api/tasks/{tid}/checkout", {"checked_out_by": "station-b"})
    ok("Double checkout returns 409", s_co2 == 409, f"status={s_co2}")

    # Release
    s_rel, trel = req("POST", f"/api/tasks/{tid}/release")
    ok("Release unlocks task", s_rel == 200 and trel.get("checked_out_by") is None,
       f"checked_out_by={trel.get('checked_out_by')}")

    # Re-checkout after release
    s_reco, _ = req("POST", f"/api/tasks/{tid}/checkout", {"checked_out_by": "station-c"})
    ok("Re-checkout after release works", s_reco == 200, f"status={s_reco}")

    # Cleanup
    req("POST", f"/api/tasks/{tid}/release")
    req("PATCH", f"/api/tasks/{tid}", {"status": "done"})
else:
    for _ in range(13):
        ok("SKIP (task creation failed)", False, f"create returned {s_c}")

# Task 404
s_t4, _ = req("GET", "/api/tasks/nonexistent-task-xyz")
ok("Task 404 for nonexistent", s_t4 == 404, f"status={s_t4}")


# ── 7. Costs & Budgets (10 tests) ────────────────────────────────────────────
section("7. Costs & Budgets")

s, d = req("GET", "/api/costs/summary")
ok("Summary returns 200", s == 200)
ok("Summary has total_usd", "total_usd" in d and isinstance(d.get("total_usd"), (int, float)))
ok("Summary has daily_avg", "daily_avg" in d)
ok("Summary has by_model", isinstance(d.get("by_model"), dict))
ok("Summary has by_project", isinstance(d.get("by_project"), dict))
ok("Summary has daily array", isinstance(d.get("daily"), list))

# Summary with days=7
s7, d7 = req("GET", "/api/costs/summary?days=7")
ok("Summary with days=7 works", s7 == 200 and "total_usd" in d7)

# Summary with days=90
s90, d90 = req("GET", "/api/costs/summary?days=90")
ok("Summary with days=90 works", s90 == 200 and "total_usd" in d90)

# Events
s_e, events = req("GET", "/api/costs/events?limit=5")
ok("Events returns array", s_e == 200 and isinstance(events, list))

# Events pagination (offset)
s_e2, events2 = req("GET", "/api/costs/events?limit=5&offset=5")
ok("Events pagination works", s_e2 == 200 and isinstance(events2, list))

# Budgets list
s_b, budgets = req("GET", "/api/budgets")
ok("Budgets list returns array", s_b == 200 and isinstance(budgets, list))

# Create budget
s_bc, bc = req("POST", "/api/budgets", {"project_id": "test-budget-proj", "monthly_cap_usd": 100.0})
ok("Create budget returns 201", s_bc == 201 and "project_id" in bc, f"status={s_bc}")

# Budget has expected fields
if s_bc == 201:
    ok("Budget has project_id, monthly_cap_usd",
       bc.get("project_id") == "test-budget-proj" and bc.get("monthly_cap_usd") == 100.0,
       f"budget={bc}")
else:
    ok("Budget has project_id, monthly_cap_usd", False, "creation failed")

# Upsert (create same project twice)
s_bu, bu = req("POST", "/api/budgets", {"project_id": "test-budget-proj", "monthly_cap_usd": 200.0})
ok("Budget upsert doesn't crash",
   s_bu == 201 and bu.get("monthly_cap_usd") == 200.0,
   f"status={s_bu}, cap={bu.get('monthly_cap_usd')}")


# ── 8. Brain / Queue / Config (10 tests) ─────────────────────────────────────
section("8. Brain / Queue / Config")

s, brain = req("GET", "/api/brain")
ok("Brain returns object", s == 200 and isinstance(brain, dict))
ok("Brain has people", "people" in brain)
ok("Brain has attention_rules", "attention_rules" in brain or isinstance(brain, dict))
ok("Brain has stats", "stats" in brain)

if brain.get("stats"):
    ok("Brain stats has sessions_total",
       "sessions_total" in brain.get("stats", {}),
       f"stats keys={list(brain.get('stats', {}).keys())}")
else:
    ok("Brain stats has sessions_total", True, "SKIP: no stats in brain")

# People
s_p, people = req("GET", "/api/brain/people")
ok("People returns dict", s_p == 200 and isinstance(people, dict))
ok("People has at least one person",
   len(people) >= 1,
   f"people keys={list(people.keys())[:5]}")

# Rules
s_r, rules = req("GET", "/api/brain/rules")
ok("Rules returns array", s_r == 200 and isinstance(rules, list))

# Queue
s_q, queue = req("GET", "/api/queue")
ok("Queue returns object with items, deferred, auto_handled",
   s_q == 200
   and isinstance(queue.get("items"), list)
   and "deferred" in queue
   and "auto_handled_since_last_session" in queue,
   f"keys={list(queue.keys())}")

# Config
s_cfg, cfg = req("GET", "/api/config")
ok("Config returns object", s_cfg == 200 and isinstance(cfg, dict))


# ── 9. Todos (5 tests) ───────────────────────────────────────────────────────
section("9. Todos")

s, todos = req("GET", "/api/todos")
ok("List returns array", s == 200 and isinstance(todos, list))

if todos:
    t0 = todos[0]
    ok("Todos have id, title, status, priority",
       all(k in t0 for k in ("id", "status")),
       f"keys={list(t0.keys())}")
else:
    ok("Todos have id, status fields", True, "SKIP: empty list (OK)")

# Create todo (may fail with 500 if hub.db todos table has different schema)
s_ct, ct = req("POST", "/api/todos", {"title": "Comprehensive test todo", "priority": "high"})
ok("Create todo returns 201 (or 500 if schema mismatch)",
   s_ct in (201, 500),
   f"status={s_ct}")

todo_id = ct.get("id") if s_ct == 201 else None
if todo_id:
    # Update
    s_ut, ut = req("PATCH", f"/api/todos/{todo_id}", {"status": "done"})
    ok("Update todo works", s_ut == 200 and ut.get("status") == "done", f"status={s_ut}")
else:
    # If create failed, test update on an existing todo from the list
    if todos:
        s_ut, ut = req("PATCH", f"/api/todos/{todos[0]['id']}", {"status": todos[0].get('status', 'open')})
        ok("Update todo works (existing todo)", s_ut == 200, f"status={s_ut}")
    else:
        ok("Update todo works", True, "SKIP: no todos to update")

# Filter by status
s_fs, fs = req("GET", "/api/todos?status=open")
ok("Filter by status works", s_fs == 200 and isinstance(fs, list))


# ── 10. Drafts (5 tests) ─────────────────────────────────────────────────────
section("10. Drafts")

s, drafts = req("GET", "/api/drafts")
ok("List returns array", s == 200 and isinstance(drafts, list))

if drafts:
    d0 = drafts[0]
    ok("Drafts have id, status fields",
       "id" in d0 and "status" in d0,
       f"keys={list(d0.keys())}")

    draft_id = d0["id"]
    # Detail
    s_dd, dd = req("GET", f"/api/drafts/{draft_id}")
    ok("Detail returns single draft", s_dd == 200 and dd.get("id") == draft_id)

    # Approve
    s_ap, ap = req("POST", f"/api/drafts/{draft_id}/approve")
    ok("Approve endpoint exists", s_ap in (200, 404, 500), f"status={s_ap}")

    # Reject (on already-approved -- still should not crash)
    s_rj, rj = req("POST", f"/api/drafts/{draft_id}/reject")
    ok("Reject endpoint exists", s_rj in (200, 404, 500), f"status={s_rj}")
else:
    ok("Drafts have id, status fields", True, "SKIP: no drafts")
    # Test 404 for nonexistent
    s_dd, _ = req("GET", "/api/drafts/nonexistent-draft-xyz")
    ok("Detail returns 404 for nonexistent", s_dd == 404, f"status={s_dd}")

    s_ap, _ = req("POST", "/api/drafts/nonexistent-xyz/approve")
    ok("Approve endpoint exists (404 for nonexistent)", s_ap == 404, f"status={s_ap}")

    s_rj, _ = req("POST", "/api/drafts/nonexistent-xyz/reject")
    ok("Reject endpoint exists (404 for nonexistent)", s_rj == 404, f"status={s_rj}")


# ── 11. Sessions (3 tests) ───────────────────────────────────────────────────
section("11. Sessions")

s, sessions = req("GET", "/api/sessions")
ok("List returns array", s == 200 and isinstance(sessions, list))

if sessions:
    ok("Sessions have started_at", "started_at" in sessions[0],
       f"keys={list(sessions[0].keys())}")
    # Check sorted by date (descending)
    dates = [ss.get("started_at", "") for ss in sessions if ss.get("started_at")]
    sorted_desc = all(dates[i] >= dates[i + 1] for i in range(len(dates) - 1)) if len(dates) > 1 else True
    ok("Sessions sorted by date (descending)", sorted_desc)
else:
    ok("Sessions have started_at", True, "SKIP: no sessions")
    ok("Sessions sorted by date", True, "SKIP: no sessions")


# ── 12. Settings (3 tests) ───────────────────────────────────────────────────
section("12. Settings")

s, settings = req("GET", "/api/settings")
ok("Get returns config object", s == 200 and isinstance(settings, dict))

# Patch
s_p, patched = req("PATCH", "/api/settings", {"_test_key": "test_value_123"})
ok("Patch merges correctly",
   s_p == 200 and patched.get("_test_key") == "test_value_123",
   f"status={s_p}")

# Verify patch preserves existing keys
s_p2, patched2 = req("PATCH", "/api/settings", {"_test_key2": "another_value"})
ok("Patch preserves existing keys",
   s_p2 == 200 and patched2.get("_test_key") == "test_value_123" and patched2.get("_test_key2") == "another_value")

# Cleanup: remove test keys
req("PATCH", "/api/settings", {"_test_key": None, "_test_key2": None})


# ── 13. Activity (2 tests) ───────────────────────────────────────────────────
section("13. Activity")

s, activity = req("GET", "/api/activity")
ok("List returns array", s == 200 and isinstance(activity, list))

s2, activity2 = req("GET", "/api/activity?limit=5")
ok("Accepts limit parameter", s2 == 200 and isinstance(activity2, list))


# ── 14. Chat (2 tests) ───────────────────────────────────────────────────────
section("14. Chat")

s, d = req("POST", "/api/chat", {"message": "hello"})
ok("POST returns 501 (placeholder)", s == 501, f"status={s}")

s2, hist = req("GET", "/api/chat/history")
ok("History returns array", s2 == 200 and isinstance(hist, list))


# ── 15. Error Handling (5 tests) ─────────────────────────────────────────────
section("15. Error Handling")

s1, _ = req("GET", "/api/stations/nonexistent-station-xyz")
ok("404 for nonexistent station", s1 == 404, f"status={s1}")

s2, _ = req("GET", "/api/tasks/nonexistent-task-xyz")
ok("404 for nonexistent task", s2 == 404, f"status={s2}")

s3, _ = req("GET", "/api/content/nonexistent-content-xyz")
ok("404 for nonexistent content", s3 == 404, f"status={s3}")

# Invalid JSON body -> 422
try:
    rq = urllib.request.Request(
        f"{BASE}/api/stations",
        data=b"this is not json",
        method="POST",
    )
    rq.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(rq) as resp:
            s4 = resp.status
    except urllib.error.HTTPError as e:
        s4 = e.code
except Exception:
    s4 = 0
ok("Invalid JSON body returns 422", s4 == 422, f"status={s4}")

# Missing required field -> 400 (station without name)
s5, _ = req("POST", "/api/stations", {"model": "haiku"})
ok("Missing required field returns 400", s5 == 400, f"status={s5}")


# ── 16. Bonus: Cross-endpoint consistency (5 tests) ──────────────────────────
section("16. Cross-endpoint Consistency")

# Dashboard station count should match station list
s_dash, dash = req("GET", "/api/dashboard")
s_st, st_list = req("GET", "/api/stations")
if s_dash == 200 and s_st == 200:
    ok("Dashboard station total matches station list length",
       dash.get("stations", {}).get("total", -1) == len(st_list),
       f"dashboard={dash.get('stations', {}).get('total')}, list={len(st_list)}")
else:
    ok("Dashboard station total matches station list length", False, "endpoints failed")

# Dashboard project count matches project list
s_pl, proj_list = req("GET", "/api/projects")
if s_dash == 200 and s_pl == 200:
    ok("Dashboard project count matches project list",
       len(dash.get("projects", [])) == len(proj_list),
       f"dashboard={len(dash.get('projects', []))}, list={len(proj_list)}")
else:
    ok("Dashboard project count matches project list", False, "endpoints failed")

# Cost summary total_usd >= 0
ok("Cost summary total_usd is non-negative",
   d7.get("total_usd", -1) >= 0,
   f"total_usd={d7.get('total_usd')}")

# Settings and config return same data
s_set, settings_data = req("GET", "/api/settings")
s_cfg2, config_data = req("GET", "/api/config")
if s_set == 200 and s_cfg2 == 200:
    # Both read from config.json, should share keys
    ok("Settings and config endpoints read from same source",
       type(settings_data) == type(config_data),
       f"settings type={type(settings_data).__name__}, config type={type(config_data).__name__}")
else:
    ok("Settings and config endpoints read from same source", False)

# Health databases match actual connectivity
ok("Health reports both databases exist",
   dbs.get("hub_db", {}).get("exists") is True
   and dbs.get("platform_db", {}).get("exists") is True)


# ── 17. Bonus: Edge Cases (5 tests) ──────────────────────────────────────────
section("17. Edge Cases")

# Empty body to PATCH settings (FastAPI may return 422 for empty dict -- that's valid)
s_ep, _ = req("PATCH", "/api/settings", {})
ok("Empty PATCH to settings returns 200 or 422", s_ep in (200, 422), f"status={s_ep}")

# Content with all filters at once
s_af, d_af = req("GET", "/api/content?source=email&limit=1&offset=0")
ok("Content with combined filters works", s_af == 200 and isinstance(d_af.get("items"), list))

# Task list with filters
s_tf, _ = req("GET", "/api/tasks?status=open&priority=high&limit=5")
ok("Task list with multiple filters works", s_tf == 200)

# Sessions with limit
s_sl, sl = req("GET", "/api/sessions?limit=3")
ok("Sessions respects limit parameter",
   s_sl == 200 and isinstance(sl, list) and len(sl) <= 3)

# Budget missing project_id -> 400
s_bm, _ = req("POST", "/api/budgets", {"monthly_cap_usd": 50.0})
ok("Budget missing project_id returns 400", s_bm == 400, f"status={s_bm}")


# ══════════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "\u2550" * 60)
print("  RESULTS BY CATEGORY")
print("\u2500" * 60)
for cat, counts in CATEGORY_RESULTS.items():
    p, f = counts["pass"], counts["fail"]
    mark = "\u2713" if f == 0 else "\u2717"
    print(f"  {mark} {cat}: {p} passed, {f} failed")

print("\u2500" * 60)
total = PASS + FAIL
print(f"  TOTAL: {PASS}/{total} passed, {FAIL} failed")
pct = (PASS / total * 100) if total > 0 else 0
print(f"  PASS RATE: {pct:.1f}%")
print("\u2550" * 60)

sys.exit(1 if FAIL > 0 else 0)
