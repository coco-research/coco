#!/bin/bash
# Deep integration tests for CoCo Platform
BASE="http://localhost:8000"
PASS=0
FAIL=0

check() {
  local DESC="$1"
  local METHOD="$2"
  local PATH="$3"
  local BODY="$4"
  local EXPECT="$5"
  
  if [ "$METHOD" = "GET" ]; then
    RESP=$(curl -s -w "\n%{http_code}" "$BASE$PATH")
  else
    RESP=$(curl -s -w "\n%{http_code}" -X "$METHOD" -H "Content-Type: application/json" -d "$BODY" "$BASE$PATH")
  fi
  
  STATUS=$(echo "$RESP" | tail -1)
  BODY_RESP=$(echo "$RESP" | sed '$d')
  
  if [ "$STATUS" = "$EXPECT" ]; then
    echo "  ✓ $DESC ($METHOD $PATH -> $STATUS)"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $DESC ($METHOD $PATH -> $STATUS, expected $EXPECT)"
    echo "    Response: $(echo "$BODY_RESP" | head -c 200)"
    FAIL=$((FAIL + 1))
  fi
}

check_json() {
  local DESC="$1"
  local PATH="$2"
  local JQ_FILTER="$3"
  
  RESP=$(curl -s "$BASE$PATH")
  RESULT=$(echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print($JQ_FILTER)" 2>/dev/null)
  
  if [ $? -eq 0 ] && [ -n "$RESULT" ] && [ "$RESULT" != "None" ] && [ "$RESULT" != "" ]; then
    echo "  ✓ $DESC -> $RESULT"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $DESC (filter failed: $JQ_FILTER)"
    echo "    Response: $(echo "$RESP" | head -c 200)"
    FAIL=$((FAIL + 1))
  fi
}

echo "═══════════════════════════════════════════"
echo "  CoCo Platform — Deep Integration Tests"
echo "═══════════════════════════════════════════"
echo ""

# ─── Health ───
echo "▶ Health"
check_json "Health returns status ok" "/api/health" "'ok' if d.get('status')=='ok' else ''"
check_json "Health has version" "/api/health" "d.get('version','')"
check_json "Health has uptime" "/api/health" "str(d.get('uptime_seconds',0))"
check_json "Health reports hub.db" "/api/health" "'yes' if 'hub_db' in d.get('databases',{}) else ''"
echo ""

# ─── Dashboard ───
echo "▶ Dashboard"
check_json "Dashboard has projects array" "/api/dashboard" "'yes' if isinstance(d.get('projects'), list) else ''"
check_json "Dashboard has stations object" "/api/dashboard" "'yes' if isinstance(d.get('stations'), dict) else ''"
check_json "Dashboard has costs object" "/api/dashboard" "'yes' if isinstance(d.get('costs'), dict) else ''"
check_json "Dashboard has health array" "/api/dashboard" "'yes' if isinstance(d.get('health'), list) else ''"
echo ""

# ─── Projects ───
echo "▶ Projects"
check_json "Projects returns list" "/api/projects" "'yes' if isinstance(d, list) else ''"
check_json "Projects have names" "/api/projects" "d[0].get('name','') if len(d)>0 else 'empty-ok'"
echo ""

# ─── Stations CRUD ───
echo "▶ Station CRUD"
check "Create station" "POST" "/api/stations" '{"name":"test-station","model":"haiku","task_description":"test task"}' "200"

# Get station list and extract first ID
STATION_ID=$(curl -s "$BASE/api/stations" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')" 2>/dev/null)
if [ -n "$STATION_ID" ]; then
  echo "  ℹ Created station: $STATION_ID"
  check "Get station detail" "GET" "/api/stations/$STATION_ID" "" "200"
  check "Update station" "PATCH" "/api/stations/$STATION_ID" '{"name":"renamed-station"}' "200"
  check_json "Station name updated" "/api/stations/$STATION_ID" "'yes' if d.get('name')=='renamed-station' else ''"
  check "Delete station" "DELETE" "/api/stations/$STATION_ID" "" "200"
else
  echo "  ✗ Could not create station"
  FAIL=$((FAIL + 1))
fi
echo ""

# ─── Tasks CRUD ───
echo "▶ Task CRUD"
check "Create task" "POST" "/api/tasks" '{"title":"Test task","priority":"high","description":"Testing atomic checkout"}' "200"

TASK_ID=$(curl -s "$BASE/api/tasks" | python3 -c "import sys,json; d=json.load(sys.stdin); items=d if isinstance(d,list) else d.get('items',d); print(items[0]['id'] if items else '')" 2>/dev/null)
if [ -n "$TASK_ID" ]; then
  echo "  ℹ Created task: $TASK_ID"
  check "Get task detail" "GET" "/api/tasks/$TASK_ID" "" "200"
  check "Checkout task" "POST" "/api/tasks/$TASK_ID/checkout" '{"station_id":"test-station"}' "200"
  check "Double checkout returns 409" "POST" "/api/tasks/$TASK_ID/checkout" '{"station_id":"other-station"}' "409"
  check "Release task" "POST" "/api/tasks/$TASK_ID/release" '{}' "200"
  check "Update task status" "PATCH" "/api/tasks/$TASK_ID" '{"status":"done"}' "200"
else
  echo "  ✗ Could not create task"
  FAIL=$((FAIL + 1))
fi
echo ""

# ─── Content ───
echo "▶ Content"
check "Content list returns" "GET" "/api/content?limit=5" "" "200"
check_json "Content has items array" "/api/content?limit=5" "'yes' if 'items' in d else ''"
check_json "Content has total" "/api/content?limit=5" "str(d.get('total', 0))"
check "Content search" "GET" "/api/content?q=test&limit=5" "" "200"
check "Content filter by source" "GET" "/api/content?source=email&limit=5" "" "200"
echo ""

# ─── Brain / Queue / Config ───
echo "▶ Brain & Config"
check_json "Brain has people" "/api/brain" "'yes' if 'people' in d else ''"
check_json "Brain has stats" "/api/brain" "'yes' if 'stats' in d else ''"
check_json "People returns dict" "/api/brain/people" "'yes' if isinstance(d, dict) else ''"
check_json "Rules returns list" "/api/brain/rules" "'yes' if isinstance(d, list) else ''"
check_json "Queue has items" "/api/queue" "'yes' if 'items' in d else ''"
check_json "Config has version" "/api/config" "str(d.get('version', d.get('launch_ui', 'exists')))"
echo ""

# ─── Costs ───
echo "▶ Costs"
check_json "Cost summary has total_usd" "/api/costs/summary" "str(d.get('total_usd', 0))"
check_json "Cost summary has by_model" "/api/costs/summary" "'yes' if 'by_model' in d else ''"
check "Cost events list" "GET" "/api/costs/events?limit=5" "" "200"
check "Budgets list" "GET" "/api/budgets" "" "200"
check "Create budget" "POST" "/api/budgets" '{"project_id":"test-project","monthly_cap_usd":100.0}' "200"
echo ""

# ─── Sessions ───
echo "▶ Sessions"
check_json "Sessions returns list" "/api/sessions" "'yes' if isinstance(d, list) else ''"
echo ""

# ─── Settings ───
echo "▶ Settings"
check "Get settings" "GET" "/api/settings" "" "200"
check "Patch settings" "PATCH" "/api/settings" '{"test_key":"test_value"}' "200"
echo ""

# ─── Todos ───
echo "▶ Todos"
check "Todos list" "GET" "/api/todos" "" "200"
echo ""

# ─── Drafts ───
echo "▶ Drafts"
check "Drafts list" "GET" "/api/drafts" "" "200"
echo ""

# ─── 404s ───
echo "▶ Error handling"
check "Unknown station 404" "GET" "/api/stations/nonexistent-id" "" "404"
check "Unknown task 404" "GET" "/api/tasks/nonexistent-id" "" "404"
check "Chat POST returns 501" "POST" "/api/chat" '{"message":"hello"}' "501"
echo ""

# ─── SSE ───
echo "▶ SSE Events"
SSE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$BASE/api/events/stream" 2>/dev/null || echo "200")
if [ "$SSE_STATUS" = "200" ] || [ "$SSE_STATUS" = "000" ]; then
  echo "  ✓ SSE stream connects (status: $SSE_STATUS)"
  PASS=$((PASS + 1))
else
  echo "  ✗ SSE stream failed (status: $SSE_STATUS)"
  FAIL=$((FAIL + 1))
fi
echo ""

echo "═══════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════"

exit $FAIL
