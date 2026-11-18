#!/usr/bin/env bash
# Hermetic verification for `coco connect` and `data/connectors.json` (bash 3.2 and bash 5).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLI="$ROOT/bin/coco.js"
CATALOG="$ROOT/data/connectors.json"

T="$(mktemp -d)"
cleanup() { rm -rf "$T"; }
trap cleanup EXIT

USER_HOME="$T/userdir"
CODEX_DIR="$T/codexdir"
PROJ_DIR="$T/project"
mkdir -p "$USER_HOME" "$CODEX_DIR" "$PROJ_DIR"

fail() { echo "FAIL: $*" >&2; exit 1; }

# 1. Validate data/connectors.json schema, verification levels, paths, and notes.
node - "$CATALOG" <<'NODE'
'use strict';
const fs = require('fs');
const data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (data.schema !== 1 || !Array.isArray(data.connectors) || data.connectors.length < 15) {
  process.stderr.write('FAIL: invalid connectors.json root\n');
  process.exit(1);
}
const allowedLevels = new Set(['tested', 'config', 'docs']);
const allowedFormats = new Set(['json', 'toml', 'docs']);
const byId = new Map();
for (const c of data.connectors) {
  if (!c.id || byId.has(c.id)) { process.stderr.write('FAIL: duplicate or missing id\n'); process.exit(1); }
  byId.set(c.id, c);
  if (!allowedLevels.has(c.level)) { process.stderr.write('FAIL: bad level on ' + c.id + '\n'); process.exit(1); }
  if (!allowedFormats.has(c.format)) { process.stderr.write('FAIL: bad format on ' + c.id + '\n'); process.exit(1); }
  if (!c.config_path || !c.source_url || !/^https:\/\//.test(c.source_url)) {
    process.stderr.write('FAIL: missing config_path or https source_url on ' + c.id + '\n');
    process.exit(1);
  }
}
const must = (cond, msg) => { if (!cond) { process.stderr.write('FAIL: ' + msg + '\n'); process.exit(1); } };
must(byId.get('codex').level === 'tested', 'codex must be tested');
must(byId.get('claude-code').level === 'tested' && byId.get('claude-code').config_path === '.mcp.json', 'claude-code must target .mcp.json at tested level');
must(byId.get('claude-desktop').level === 'config', 'claude-desktop must be config level');
must(byId.get('windsurf').config_path === '~/.config/devin/mcp_config.json' && /codeium/.test(byId.get('windsurf').note || ''), 'windsurf must point to devin path and note legacy conflict');
must(byId.get('antigravity').config_path === '~/.gemini/config/mcp_config.json', 'antigravity must point to ~/.gemini/config/mcp_config.json');
must(byId.get('amazon-q').config_path === '~/.kiro/settings/mcp.json', 'amazon-q must point to ~/.kiro/settings/mcp.json');
must(/shut down/i.test(byId.get('roo-code').note || '') && /unverified/i.test(byId.get('roo-code').note || ''), 'roo-code must carry unverified shutdown note');
NODE

# 2. `--list` prints every connector and accurate level without touching disk.
LIST_OUT="$(HOME="$USER_HOME" CODEX_HOME="$CODEX_DIR" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect --list)"
printf '%s\n' "$LIST_OUT" | grep -qE '^codex[[:space:]]+tested' || fail "--list missing codex tested"
printf '%s\n' "$LIST_OUT" | grep -qE '^claude-code[[:space:]]+tested' || fail "--list missing claude-code tested"
printf '%s\n' "$LIST_OUT" | grep -qE '^claude-desktop[[:space:]]+config' || fail "--list missing claude-desktop config"
printf '%s\n' "$LIST_OUT" | grep -qE '^cursor[[:space:]]+config' || fail "--list missing cursor config"
printf '%s\n' "$LIST_OUT" | grep -qE '^goose[[:space:]]+docs' || fail "--list missing goose docs"

# 3. Unknown tool and docs-only `--write` exit 2 without writing files.
rc=0
HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect nonexistent-harness >/dev/null 2>&1 || rc=$?
[ "$rc" -eq 2 ] || fail "unknown connector exited $rc (expected 2)"

rc=0
HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect goose --write >/dev/null 2>&1 || rc=$?
[ "$rc" -eq 2 ] || fail "docs-only --write exited $rc (expected 2)"

# 4. Print-only mode never writes target config; claude-code prints user-scope hint.
CURSOR_CFG="$USER_HOME/.cursor/mcp.json"
SNIPPET="$(HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect cursor --npx)"
[ ! -e "$CURSOR_CFG" ] || fail "print mode created $CURSOR_CFG"
printf '%s\n' "$SNIPPET" | grep -q '"cocosuperintelligence"' || fail "--npx snippet missing package name"

CC_SNIP="$(cd "$PROJ_DIR" && HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect claude-code)"
[ ! -e "$PROJ_DIR/.mcp.json" ] || fail "claude-code print created .mcp.json"
printf '%s\n' "$CC_SNIP" | grep -q 'claude mcp add --scope user coco --' || fail "claude-code print missing user-scope command hint"

# 5. `claude-code --write` writes project `.mcp.json` (NEVER `~/.claude.json`), preserves user entry, creates `.bak`, and is byte-identical on re-run.
printf '{\n  "mcpServers": {\n    "user-keep": {\n      "command": "echo",\n      "args": ["hi"]\n    }\n  }\n}\n' > "$PROJ_DIR/.mcp.json"
CC_WRITE_OUT="$(cd "$PROJ_DIR" && HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect claude-code --write)"
[ ! -e "$USER_HOME/.claude.json" ] || fail "claude-code --write touched ~/.claude.json"
[ -f "$PROJ_DIR/.mcp.json.bak" ] || fail "claude-code .mcp.json.bak missing"
printf '%s\n' "$CC_WRITE_OUT" | grep -q 'claude mcp add --scope user coco --' || fail "claude-code --write missing user-scope hint"
CC_HEX1="$(shasum -a 256 "$PROJ_DIR/.mcp.json" | awk '{print $1}')"
(cd "$PROJ_DIR" && HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect claude-code --write >/dev/null)
CC_HEX2="$(shasum -a 256 "$PROJ_DIR/.mcp.json" | awk '{print $1}')"
[ "$CC_HEX1" = "$CC_HEX2" ] || fail "claude-code --write twice changed bytes"

# 6. `claude-desktop --write`: existing user entry survives, backup made, `--write` twice is byte-identical, written command speaks MCP.
CLAUDE_CFG="$USER_HOME/Library/Application Support/Claude/claude_desktop_config.json"
mkdir -p "$(dirname "$CLAUDE_CFG")"
printf '{\n  "mcpServers": {\n    "user-keep": {\n      "command": "echo",\n      "args": ["hi"]\n    }\n  },\n  "globalShortcut": "Alt+Space"\n}\n' > "$CLAUDE_CFG"

HOME="$USER_HOME" COCO_CONNECT_PLATFORM=darwin COCO_NO_UPDATE_CHECK=1 node "$CLI" connect claude-desktop --write >/dev/null
[ -f "${CLAUDE_CFG}.bak" ] || fail "backup ${CLAUDE_CFG}.bak was not created"
FIRST_HEX="$(shasum -a 256 "$CLAUDE_CFG" | awk '{print $1}')"
HOME="$USER_HOME" COCO_CONNECT_PLATFORM=darwin COCO_NO_UPDATE_CHECK=1 node "$CLI" connect claude-desktop --write >/dev/null
SECOND_HEX="$(shasum -a 256 "$CLAUDE_CFG" | awk '{print $1}')"
[ "$FIRST_HEX" = "$SECOND_HEX" ] || fail "claude-desktop --write twice changed file bytes"

PROBE_TOOLS="$(HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node - "$PROJ_DIR/.mcp.json" <<'NODE'
'use strict';
const { spawn } = require('child_process');
const fs = require('fs');
const cfg = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (!cfg.mcpServers || !cfg.mcpServers['user-keep']) process.exit(1);
const coco = cfg.mcpServers.coco;
const proc = spawn(coco.command, coco.args, { stdio: ['pipe', 'pipe', 'pipe'] });
let out = '';
proc.stdout.on('data', (d) => {
  out += d.toString('utf8');
  if (out.split('\n').filter(Boolean).length >= 2) proc.stdin.end();
});
proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'probe', version: '1.0' } } }) + '\n');
proc.stdin.write(JSON.stringify({ jsonrpc: '2.0', id: 2, method: 'tools/list', params: {} }) + '\n');
proc.on('close', (code) => {
  if (code !== 0) process.exit(1);
  const replies = out.trim().split('\n').map((l) => JSON.parse(l));
  const names = replies[1].result.tools.map((t) => t.name);
  if (!names.includes('coco_search') || !names.includes('coco_board')) process.exit(1);
  process.stdout.write(names.join(','));
});
NODE
)"

# 7. TOML (`codex`) + updated paths (`windsurf` -> devin + legacy note, `antigravity` -> .gemini/config, `amazon-q` -> .kiro/settings + legacy fallback).
CODEX_CFG="$CODEX_DIR/config.toml"
printf 'model = "o3"\n\n[mcp_servers.user_srv]\ncommand = "echo"\nargs = ["ok"]\n' > "$CODEX_CFG"
HOME="$USER_HOME" CODEX_HOME="$CODEX_DIR" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect codex --write >/dev/null
[ -f "${CODEX_CFG}.bak" ] || fail "codex backup was not created"
TOML_HEX1="$(shasum -a 256 "$CODEX_CFG" | awk '{print $1}')"
HOME="$USER_HOME" CODEX_HOME="$CODEX_DIR" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect codex --write >/dev/null
TOML_HEX2="$(shasum -a 256 "$CODEX_CFG" | awk '{print $1}')"
[ "$TOML_HEX1" = "$TOML_HEX2" ] || fail "codex --write twice changed file bytes"
grep -q '\[mcp_servers\.user_srv\]' "$CODEX_CFG" || fail "codex user_srv lost"

mkdir -p "$USER_HOME/.codeium/windsurf"
echo '{}' > "$USER_HOME/.codeium/windsurf/mcp_config.json"
WS_OUT="$(HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect windsurf --write)"
[ -f "$USER_HOME/.config/devin/mcp_config.json" ] || fail "windsurf did not write ~/.config/devin/mcp_config.json"
printf '%s\n' "$WS_OUT" | grep -q '\.codeium/windsurf/mcp_config\.json' || fail "windsurf did not report existing legacy path"

HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect antigravity --write >/dev/null
[ -f "$USER_HOME/.gemini/config/mcp_config.json" ] || fail "antigravity did not write ~/.gemini/config/mcp_config.json"

HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect amazon-q --write >/dev/null
[ -f "$USER_HOME/.kiro/settings/mcp.json" ] || fail "amazon-q did not write ~/.kiro/settings/mcp.json"

CUSTOM_CONFLICT="$T/conflict.json"
printf '{"mcpServers":{"coco":{"command":"custom-user-bin","args":["serve"]},"keep":{"command":"echo"}}}\n' > "$CUSTOM_CONFLICT"
rc=0
HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect cursor --write --config "$CUSTOM_CONFLICT" >/dev/null 2>&1 || rc=$?
[ "$rc" -eq 2 ] || fail "custom user coco entry was overwritten without --force (rc=$rc)"
HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect cursor --write --force --config "$CUSTOM_CONFLICT" >/dev/null
grep -q 'coco\.js' "$CUSTOM_CONFLICT" || fail "JSON --force did not replace non-Coco entry"
grep -q '"keep"' "$CUSTOM_CONFLICT" || fail "JSON --force dropped sibling entry"

# 8. Unmarked TOML `[mcp_servers.coco] # comment`, `--force`, `[[mcp_servers.coco]]`, `--config` missing value, and `loadCatalog` error handling.
TOML_COMMENT_CONFLICT="$T/codex-conflict.toml"
printf 'model = "o3"\n[mcp_servers.coco] # my custom notes\ncommand = "custom-toml-bin"\nargs = ["x"]\n\n[mcp_servers.keep]\ncommand = "echo"\n' > "$TOML_COMMENT_CONFLICT"
rc=0
HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect codex --write --config "$TOML_COMMENT_CONFLICT" >/dev/null 2>&1 || rc=$?
[ "$rc" -eq 2 ] || fail "unmarked non-Coco TOML section with comment did not exit 2 (rc=$rc)"
HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect codex --write --force --config "$TOML_COMMENT_CONFLICT" >/dev/null
[ "$(grep -c '^\[mcp_servers\.coco\]' "$TOML_COMMENT_CONFLICT")" -eq 1 ] || fail "TOML --force produced duplicate [mcp_servers.coco] header"
grep -q '^\[mcp_servers\.keep\]' "$TOML_COMMENT_CONFLICT" || fail "TOML --force dropped [mcp_servers.keep]"

TOML_COCO_UNMARKED="$T/codex-unmarked-coco.toml"
printf '[mcp_servers.coco] # legacy coco install\ncommand = "npx"\nargs = ["-y", "cocosuperintelligence", "mcp"]\n' > "$TOML_COCO_UNMARKED"
HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect codex --write --config "$TOML_COCO_UNMARKED" >/dev/null
[ "$(grep -c '^\[mcp_servers\.coco\]' "$TOML_COCO_UNMARKED")" -eq 1 ] || fail "unmarked Coco TOML section was duplicated instead of replaced"

TOML_ARRAY="$T/codex-array.toml"
printf '[[mcp_servers.coco]]\ncommand = "custom-array-bin"\n' > "$TOML_ARRAY"
rc=0
HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect codex --write --config "$TOML_ARRAY" >/dev/null 2>&1 || rc=$?
[ "$rc" -eq 2 ] || fail "TOML [[mcp_servers.coco]] array-of-tables did not exit 2 without --force (rc=$rc)"
HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect codex --write --force --config "$TOML_ARRAY" >/dev/null
grep -q '^# coco:mcp-start$' "$TOML_ARRAY" || fail "TOML --force did not replace [[mcp_servers.coco]]"

for bad_args in "cursor --write --config" "cursor --write --config --local" "cursor --write --config=" "codex cursor"; do
  rc=0
  # shellcheck disable=SC2086
  HOME="$USER_HOME" COCO_NO_UPDATE_CHECK=1 node "$CLI" connect $bad_args >/dev/null 2>&1 || rc=$?
  [ "$rc" -eq 2 ] || fail "bad args '$bad_args' did not exit 2 (rc=$rc)"
done

node -e "
const assert = require('assert');
const { loadCatalog } = require('$ROOT/bin/coco-connect.js');
assert.throws(() => loadCatalog('$T/missing-catalog.json'), /Connector catalog unreadable/);
"

echo "coco connect ok · 19 harnesses · bytes identical · user entry kept · backup made · unknown exits 2 · tools: $PROBE_TOOLS"
