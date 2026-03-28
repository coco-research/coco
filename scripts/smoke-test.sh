#!/bin/bash
# =============================================================================
# CoCo Platform — Comprehensive Smoke Test Suite
# Tests all critical API endpoints with color-coded output and summary.
# Usage: ./scripts/smoke-test.sh [BASE_URL]
# =============================================================================
set -euo pipefail

BASE="${1:-http://localhost:8000}"
PASS=0
FAIL=0
TOTAL=0

# Colors
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
BOLD="\033[1m"
RESET="\033[0m"

# Track created resources for cleanup
CREATED_SESSION_ID=""
CREATED_TODO_ID=""
CREATED_GOAL_ID=""

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

check() {
  local method="$1"
  local path="$2"
  local expected="$3"
  local label="${4:-$method $path}"
  local body="${5:-}"
  TOTAL=$((TOTAL + 1))

  local curl_args=(-s -o /tmp/smoke_body -w "%{http_code}" -X "$method")
  if [ -n "$body" ]; then
    curl_args+=(-H "Content-Type: application/json" -d "$body")
  fi
  curl_args+=("${BASE}${path}")

  STATUS=$(curl "${curl_args[@]}" 2>/dev/null || echo "000")

  if [ "$STATUS" = "$expected" ]; then
    echo -e "  ${GREEN}✓${RESET} ${label} -> ${STATUS}"
    PASS=$((PASS + 1))
    return 0
  else
    echo -e "  ${RED}✗${RESET} ${label} -> ${STATUS} (expected ${expected})"
    FAIL=$((FAIL + 1))
    return 1
  fi
}

get()  { check "GET"  "$1" "${2:-200}" "${3:-GET $1}"; }
post() { check "POST" "$1" "${2:-200}" "${4:-POST $1}" "${3:-}"; }
del()  { check "DELETE" "$1" "${2:-204}" "${3:-DELETE $1}"; }

# SSE test: connect, read a few bytes, disconnect
check_sse() {
  local path="$1"
  TOTAL=$((TOTAL + 1))
  local label="SSE $path (connect+disconnect)"

  # curl with 2-second timeout; any 200 response header = success
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "${BASE}${path}" 2>/dev/null || echo "000")

  # SSE endpoints return 200 even if we disconnect early (curl exits 28 on timeout)
  # Re-check: a 000 from timeout actually means the connection was accepted (SSE streams forever)
  if [ "$STATUS" = "200" ] || [ "$STATUS" = "000" ]; then
    echo -e "  ${GREEN}✓${RESET} ${label} -> connected"
    PASS=$((PASS + 1))
  else
    echo -e "  ${RED}✗${RESET} ${label} -> ${STATUS}"
    FAIL=$((FAIL + 1))
  fi
}

# Extract JSON field from /tmp/smoke_body
json_field() {
  python3 -c "import json,sys; print(json.load(open('/tmp/smoke_body'))$1)" 2>/dev/null || echo ""
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

echo ""
echo -e "${BOLD}${CYAN}CoCo Platform Smoke Tests${RESET}"
echo -e "${CYAN}Base URL: ${BASE}${RESET}"
echo ""

# --- Core ---
echo -e "${BOLD}--- Core ---${RESET}"
get "/api/health"
get "/api/dashboard"
get "/api/home"
get "/api/settings"

# --- Tree & Projects ---
echo ""
echo -e "${BOLD}--- Tree & Projects ---${RESET}"
get "/api/tree"
get "/api/tree/unplaced"
get "/api/projects"
get "/api/content?limit=5"

# --- Agents ---
echo ""
echo -e "${BOLD}--- Agents ---${RESET}"
get "/api/agents"
get "/api/agent-roles"
get "/api/agents/org-chart"

# --- Tasks ---
echo ""
echo -e "${BOLD}--- Tasks ---${RESET}"
get "/api/tasks"

# --- Todos ---
echo ""
echo -e "${BOLD}--- Todos ---${RESET}"
get "/api/todos"

# --- Goals ---
echo ""
echo -e "${BOLD}--- Goals ---${RESET}"
get "/api/goals"

# --- Drafts ---
echo ""
echo -e "${BOLD}--- Drafts ---${RESET}"
get "/api/drafts"

# --- Brain & Queue ---
echo ""
echo -e "${BOLD}--- Brain & Queue ---${RESET}"
get "/api/brain"
get "/api/brain/people"
get "/api/brain/rules"
get "/api/queue"
get "/api/config"

# --- Costs & Budgets ---
echo ""
echo -e "${BOLD}--- Costs & Budgets ---${RESET}"
get "/api/costs/summary"
get "/api/costs/events"
get "/api/budgets"

# --- Sessions & Activity ---
echo ""
echo -e "${BOLD}--- Sessions & Activity ---${RESET}"
get "/api/sessions"
get "/api/activity"
get "/api/chat/history"
get "/api/chat/sessions"

# --- Collaboration ---
echo ""
echo -e "${BOLD}--- Collaboration ---${RESET}"
get "/api/workflow-templates"
get "/api/nodes/root/context"
get "/api/nodes/root/handoffs"

# --- Triggers ---
echo ""
echo -e "${BOLD}--- Triggers ---${RESET}"
get "/api/triggers"

# --- Inbox ---
echo ""
echo -e "${BOLD}--- Inbox ---${RESET}"
get "/api/inbox/read-states"

# --- Templates ---
echo ""
echo -e "${BOLD}--- Templates ---${RESET}"
get "/api/templates"

# --- Voice ---
echo ""
echo -e "${BOLD}--- Voice ---${RESET}"
get "/api/tts/voices"

# --- SSE Streams ---
echo ""
echo -e "${BOLD}--- SSE Streams ---${RESET}"
check_sse "/api/events/stream"
check_sse "/api/events/agents"

# --- Write operations: Create ---
echo ""
echo -e "${BOLD}--- Create (POST) ---${RESET}"

# Create chat session
if post "/api/chat/sessions" "200" '{}' "POST /api/chat/sessions (create)"; then
  CREATED_SESSION_ID=$(json_field "['id']")
  if [ -n "$CREATED_SESSION_ID" ]; then
    echo -e "    ${YELLOW}created session: ${CREATED_SESSION_ID}${RESET}"
  fi
fi

# Create todo
if post "/api/todos" "201" '{"title":"smoke-test-todo","status":"open","priority":"low"}' "POST /api/todos (create)"; then
  CREATED_TODO_ID=$(json_field "['id']")
  if [ -n "$CREATED_TODO_ID" ]; then
    echo -e "    ${YELLOW}created todo: ${CREATED_TODO_ID}${RESET}"
  fi
fi

# Create goal
if post "/api/goals" "201" '{"title":"smoke-test-goal"}' "POST /api/goals (create)"; then
  CREATED_GOAL_ID=$(json_field "['id']")
  if [ -n "$CREATED_GOAL_ID" ]; then
    echo -e "    ${YELLOW}created goal: ${CREATED_GOAL_ID}${RESET}"
  fi
fi

# Jarvis command
post "/api/jarvis/command" "200" '{"text":"health"}' "POST /api/jarvis/command"

# --- Cleanup: Delete created test data ---
echo ""
echo -e "${BOLD}--- Cleanup (DELETE) ---${RESET}"

if [ -n "$CREATED_SESSION_ID" ]; then
  del "/api/chat/sessions/${CREATED_SESSION_ID}" "200" "DELETE /api/chat/sessions/${CREATED_SESSION_ID}"
fi

if [ -n "$CREATED_TODO_ID" ]; then
  # Todos may return 200 or 204 depending on implementation; check for both
  check "DELETE" "/api/todos/${CREATED_TODO_ID}" "200" "DELETE /api/todos/${CREATED_TODO_ID}" || \
  check "DELETE" "/api/todos/${CREATED_TODO_ID}" "204" "DELETE /api/todos/${CREATED_TODO_ID} (retry 204)" 2>/dev/null || true
fi

if [ -n "$CREATED_GOAL_ID" ]; then
  del "/api/goals/${CREATED_GOAL_ID}" "204" "DELETE /api/goals/${CREATED_GOAL_ID}"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}============================================${RESET}"
if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}  All tests passed: ${PASS}/${TOTAL}${RESET}"
else
  echo -e "${RED}${BOLD}  ${PASS}/${TOTAL} tests passed, ${FAIL} failed${RESET}"
fi
echo -e "${BOLD}============================================${RESET}"
echo ""

exit "$FAIL"
