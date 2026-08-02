#!/usr/bin/env bash
# M0 smoke test - proves the four guarantees in SPEC.md against a real server.
#
#   1. round trip      POST /api/brain/checkpoint then GET /api/brain/thread
#   2. idempotency     the same content written twice leaves exactly one row
#   3. deferred write  a locked store yields deferred:true plus a sidecar file,
#                      the read still returns the entry, and the next start drains it
#   4. MCP tools       initialize / tools/list / tools/call over stdio, with
#                      structured metadata passed as a JSON object
#
# Everything runs in a throwaway temp directory on an ephemeral port. No
# existing store is touched. Requires bash, python3 and curl - nothing else.
#
# Run from anywhere:  bash systems/m0/tests/m0-smoke.sh

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$HERE/../skills/m0/scripts"
SERVER="$SCRIPTS/m0_server.py"
MCP="$SCRIPTS/m0_mcp.py"

WORK="$(mktemp -d "${TMPDIR:-/tmp}/m0-smoke.XXXXXX")"
export M0_DB="$WORK/thread.db"
export M0_SIDECAR_DIR="$WORK/sidecars"
export M0_BUSY_TIMEOUT_MS=600
export M0_PROJECT="smoke-project"
unset M0_SESSION_ID M0_SOURCE_TOOL M0_OWNER M0_VISIBILITY 2>/dev/null || true

PORT="$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')"
export M0_BASE_URL="http://127.0.0.1:$PORT"
SERVER_PID=""
LOCK_PID=""
PASS=0
FAIL=0

cleanup() {
  [ -n "$LOCK_PID" ] && kill "$LOCK_PID" 2>/dev/null
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null
  wait 2>/dev/null
  rm -rf "$WORK"
}
trap cleanup EXIT

check() { # check <label> <condition-description> <0|1 result>
  if [ "$2" = "0" ]; then
    printf '  PASS  %s\n' "$1"; PASS=$((PASS + 1))
  else
    printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL + 1))
  fi
}

jq_get() { python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('$1',''))"; }

start_server() {
  python3 "$SERVER" serve --port "$PORT" >"$WORK/server.log" 2>&1 &
  SERVER_PID=$!
  for _ in $(seq 1 60); do
    if curl -fsS "$M0_BASE_URL/api/health" >/dev/null 2>&1; then return 0; fi
    sleep 0.1
  done
  echo "server did not come up; log:"; cat "$WORK/server.log"; return 1
}

stop_server() {
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null
  wait "$SERVER_PID" 2>/dev/null
  SERVER_PID=""
}

row_count() { # row_count [where-clause]
  python3 - "$M0_DB" "${1:-1=1}" <<'PY'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1], timeout=5)
print(conn.execute(f"SELECT COUNT(*) FROM operational_thread WHERE {sys.argv[2]}").fetchone()[0])
PY
}

echo "M0 smoke test"
echo "  store: $M0_DB"
echo "  port:  $PORT"
echo

# ---------------------------------------------------------------- 1. round trip
echo "1. round trip"
start_server || exit 1
HEALTH="$(curl -fsS "$M0_BASE_URL/api/health")"
[ "$(printf '%s' "$HEALTH" | jq_get ok)" = "True" ]; check "health reports ok" "$?"

BODY='{"project":"smoke-project","kind":"compact_checkpoint",
 "text":"Smoke test wrote a checkpoint.",
 "next_step":"Read it back.","last_verified":"m0-smoke.sh step 1",
 "session_id":"smoke-1","source_tool":"smoke","branch":"main","head_sha":"abc1234",
 "meta_json":{"suite":"smoke","step":1}}'
W1="$(curl -fsS -X POST "$M0_BASE_URL/api/brain/checkpoint" -H 'Content-Type: application/json' -d "$BODY")"
ID1="$(printf '%s' "$W1" | jq_get id)"
TS1="$(printf '%s' "$W1" | jq_get ts)"
[ -n "$ID1" ]; check "write returns an id" "$?"
[ "$(printf '%s' "$W1" | jq_get deferred)" = "False" ]; check "write is not deferred" "$?"
[ "$(printf '%s' "$W1" | jq_get ok)" = "True" ]; check "write reports ok" "$?"

READ="$(curl -fsS "$M0_BASE_URL/api/brain/thread?project=smoke-project&limit=10")"
printf '%s' "$READ" | grep -Fq "$ID1"; check "read returns the entry" "$?"
printf '%s' "$READ" | grep -Fq '\"suite\":\"smoke\"'; check "metadata survives the round trip" "$?"
KIND_READ="$(curl -fsS "$M0_BASE_URL/api/brain/thread?project=smoke-project&kind=session_end")"
[ "$(printf '%s' "$KIND_READ" | jq_get count)" = "0" ]; check "kind filter excludes other kinds" "$?"
echo

# --------------------------------------------------------------- 2. idempotency
echo "2. idempotency"
W2="$(curl -fsS -X POST "$M0_BASE_URL/api/brain/checkpoint" -H 'Content-Type: application/json' -d "$BODY")"
[ "$(printf '%s' "$W2" | jq_get id)" = "$ID1" ]; check "re-write returns the same id" "$?"
[ "$(printf '%s' "$W2" | jq_get ts)" = "$TS1" ]; check "re-write preserves the original ts" "$?"
[ "$(row_count "id='$ID1'")" = "1" ]; check "exactly one row exists for that id" "$?"

# Same metadata, re-encoded as a JSON string with the keys in another order.
BODY_STR='{"project":"smoke-project","kind":"compact_checkpoint",
 "text":"Smoke test wrote a checkpoint.",
 "next_step":"Read it back.","last_verified":"m0-smoke.sh step 1",
 "session_id":"smoke-1","source_tool":"smoke","branch":"main","head_sha":"abc1234",
 "meta_json":"{\"step\":1,\"suite\":\"smoke\"}"}'
W3="$(curl -fsS -X POST "$M0_BASE_URL/api/brain/checkpoint" -H 'Content-Type: application/json' -d "$BODY_STR")"
[ "$(printf '%s' "$W3" | jq_get id)" = "$ID1" ]; check "string-encoded metadata hashes identically" "$?"
[ "$(row_count "id='$ID1'")" = "1" ]; check "still exactly one row" "$?"
echo

# ------------------------------------------------------------ 3. deferred write
echo "3. deferred write under a locked store"
python3 - "$M0_DB" "$WORK/lock.state" <<'PY' >"$WORK/lock.log" 2>&1 &
import os, sqlite3, sys, time
db, state = sys.argv[1], sys.argv[2]
conn = sqlite3.connect(db, timeout=5, isolation_level=None)
conn.execute("BEGIN EXCLUSIVE")
open(state, "w").write("locked")
while os.path.exists(state):
    time.sleep(0.1)
conn.execute("ROLLBACK")
PY
LOCK_PID=$!
for _ in $(seq 1 60); do [ -f "$WORK/lock.state" ] && break; sleep 0.1; done
[ -f "$WORK/lock.state" ]; check "store is exclusively locked by another writer" "$?"

DEF_BODY='{"project":"smoke-project","kind":"session_end",
 "text":"Wrote while the store was locked.","next_step":"Drain on next start."}'
W4="$(curl -fsS -X POST "$M0_BASE_URL/api/brain/checkpoint" -H 'Content-Type: application/json' -d "$DEF_BODY")"
ID4="$(printf '%s' "$W4" | jq_get id)"
[ "$(printf '%s' "$W4" | jq_get deferred)" = "True" ]; check "response reports deferred:true" "$?"
[ "$(printf '%s' "$W4" | jq_get ok)" = "True" ]; check "response still reports ok:true" "$?"
[ "$(ls -1 "$M0_SIDECAR_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')" = "1" ]; check "one sidecar file was spooled" "$?"
[ "$(row_count "id='$ID4'")" = "0" ]; check "the row is not in the store yet" "$?"
LOCKED_READ="$(curl -fsS "$M0_BASE_URL/api/brain/thread?project=smoke-project&limit=10")"
printf '%s' "$LOCKED_READ" | grep -Fq "$ID4"; check "read still returns the deferred entry" "$?"

rm -f "$WORK/lock.state"
wait "$LOCK_PID" 2>/dev/null; LOCK_PID=""
stop_server
start_server || exit 1
grep -q "drained 1 sidecar write" "$WORK/server.log"; check "next start reports the drain" "$?"
[ "$(ls -1 "$M0_SIDECAR_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')" = "0" ]; check "the spool is empty" "$?"
[ "$(row_count "id='$ID4'")" = "1" ]; check "the deferred write landed in the store" "$?"
echo

# ------------------------------------------------------------------- 4. MCP
echo "4. MCP tools over stdio"
MCP_OUT="$(printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}' \
 '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
 '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"m0_remember","arguments":{"text":"MCP wrote this.","kind":"step_done","meta":{"via":"mcp","nested":{"ok":true}}}}}' \
 '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"m0_recall","arguments":{"limit":5}}}' \
 | python3 "$MCP" 2>"$WORK/mcp.err")"

printf '%s' "$MCP_OUT" | grep -Fq '"serverInfo"'; check "initialize returns serverInfo" "$?"
printf '%s' "$MCP_OUT" | grep -Fq '"m0_remember"'; check "tools/list advertises m0_remember" "$?"
printf '%s' "$MCP_OUT" | grep -Fq '"m0_recall"'; check "tools/list advertises m0_recall" "$?"
printf '%s' "$MCP_OUT" | python3 -c "
import json, sys
by_id = {m.get('id'): m for m in (json.loads(l) for l in sys.stdin if l.strip())}
tools = {t['name']: t for t in by_id[2]['result']['tools']}
meta = tools['m0_remember']['inputSchema']['properties']['meta']
sys.exit(0 if meta.get('type') == 'object' else 1)
"
check "the meta parameter is typed object, not string" "$?"
printf '%s' "$MCP_OUT" | grep -Fq '"isError": false'; check "tools/call succeeds" "$?"
printf '%s' "$MCP_OUT" | grep -Fq '\"nested\":{\"ok\":true}'; check "nested metadata object round-trips" "$?"
echo

echo "----"
echo "PASS $PASS   FAIL $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "m0 smoke: all guarantees verified."
