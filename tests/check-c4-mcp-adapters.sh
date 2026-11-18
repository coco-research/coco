#!/usr/bin/env bash
# Hermetic verification for MCP wiring in Kiro (`amazon-q`) and Cline (`cline`).
# Compatible with bash 3.2 and bash 5. Never touches real HOME.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

run_adapter() {
  local adapter=$1 home=$2
  shift 2
  env -u AMAZON_Q_HOME -u KIRO_HOME -u CLINE_HOME HOME="$home" \
    bash "$ROOT/adapters/$adapter/install.sh" "$@" >/dev/null
}

check_json_adapter() {
  local adapter=$1 rel_cfg=$2 root_key=$3
  local h1="$WORK/${adapter}-fresh"
  mkdir -p "$h1"

  # 1. Double-run byte identity + exactly one `coco` entry + marker present
  run_adapter "$adapter" "$h1"
  local cfg="$h1/$rel_cfg"
  [[ -f "$cfg" ]] || fail "$adapter: missing $cfg"
  [[ -f "${cfg}.coco-mcp" ]] || fail "$adapter: missing marker ${cfg}.coco-mcp"
  cp "$cfg" "$WORK/${adapter}-run1.json"
  run_adapter "$adapter" "$h1"
  cmp -s "$cfg" "$WORK/${adapter}-run1.json" \
    || fail "$adapter: second run changed $cfg bytes"

  python3 - "$cfg" "$root_key" <<'PY'
import json, pathlib, sys
doc = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
sec = doc[sys.argv[2]]
assert list(sec.keys()) == ["coco"], f"expected single coco entry, got {list(sec.keys())}"
assert sec["coco"]["command"] == "node" and sec["coco"]["args"][-1] == "mcp"
PY

  # 2. Pre-existing user server survives + `.bak` backup created before merge + idempotent re-run
  local h2="$WORK/${adapter}-merge"
  local cfg2="$h2/$rel_cfg"
  mkdir -p "$(dirname "$cfg2")"
  python3 - "$cfg2" "$root_key" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(
    json.dumps({sys.argv[2]: {"user-server": {"command": "uvx", "args": ["custom-mcp"]}}}, indent=2) + "\n",
    encoding="utf-8",
)
PY
  cp "$cfg2" "$WORK/${adapter}-pre.json"
  run_adapter "$adapter" "$h2"
  [[ -f "${cfg2}.bak" ]] || fail "$adapter: expected backup ${cfg2}.bak"
  cmp -s "${cfg2}.bak" "$WORK/${adapter}-pre.json" \
    || fail "$adapter: backup does not match pre-merge user file"
  cp "$cfg2" "$WORK/${adapter}-merged1.json"
  run_adapter "$adapter" "$h2"
  cmp -s "$cfg2" "$WORK/${adapter}-merged1.json" \
    || fail "$adapter: re-run after merge changed $cfg2 bytes"
  cmp -s "${cfg2}.bak" "$WORK/${adapter}-pre.json" \
    || fail "$adapter: re-run overwrote original .bak"

  python3 - "$cfg2" "$root_key" <<'PY'
import json, pathlib, sys
doc = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
sec = doc[sys.argv[2]]
assert sec["user-server"] == {"command": "uvx", "args": ["custom-mcp"]}, "sibling user entry lost"
assert "coco" in sec, "coco entry missing"
PY

  # 3. Planted user `coco` entry is NEVER overwritten
  local h3="$WORK/${adapter}-user-coco"
  local cfg3="$h3/$rel_cfg"
  mkdir -p "$(dirname "$cfg3")"
  python3 - "$cfg3" "$root_key" <<'PY'
import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(
    json.dumps({sys.argv[2]: {"coco": {"command": "my-private-coco", "args": ["--port", "9000"]}}}, indent=2) + "\n",
    encoding="utf-8",
)
PY
  cp "$cfg3" "$WORK/${adapter}-user-coco.json"
  run_adapter "$adapter" "$h3"
  cmp -s "$cfg3" "$WORK/${adapter}-user-coco.json" \
    || fail "$adapter: overwrote planted user 'coco' entry"

  # 4. --dry-run writes no MCP config
  local h4="$WORK/${adapter}-dry"
  mkdir -p "$h4"
  run_adapter "$adapter" "$h4" --dry-run
  [[ ! -e "$h4/$rel_cfg" ]] || fail "$adapter: --dry-run wrote $rel_cfg"
}

check_json_adapter "amazon-q" ".kiro/settings/mcp.json" "mcpServers"
check_json_adapter "cline" ".cline/data/settings/cline_mcp_settings.json" "mcpServers"

# Legacy ~/.aws/amazonq/mcp.json is used ONLY when already present without ~/.kiro
LEG_HOME="$WORK/legacy-q"
mkdir -p "$LEG_HOME/.aws/amazonq"
printf '{"mcpServers":{"existing":{"command":"echo","args":["hi"]}}}\n' >"$LEG_HOME/.aws/amazonq/mcp.json"
run_adapter "amazon-q" "$LEG_HOME"
[[ ! -e "$LEG_HOME/.kiro/settings/mcp.json" ]] || fail "amazon-q created ~/.kiro despite legacy ~/.aws/amazonq"
[[ -f "$LEG_HOME/.aws/amazonq/mcp.json.bak" ]] || fail "amazon-q did not back up legacy ~/.aws/amazonq/mcp.json"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert "existing" in d["mcpServers"] and "coco" in d["mcpServers"]' \
  "$LEG_HOME/.aws/amazonq/mcp.json"

echo "c4.1 mcp ok · amazon-q(kiro) + legacy fallback · cline · bytes identical · backups made · user entries kept"
