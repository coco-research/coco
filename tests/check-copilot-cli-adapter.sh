#!/usr/bin/env bash
# End-to-end checks for adapters/github-copilot-cli/install.sh:
#   1. Merges mcpServers.coco into ~/.copilot/mcp-config.json preserving user entries and writing .bak once
#   2. Symlinks core, bundle, and SI front-door skills into ~/.copilot/skills/
#   3. Symlinks custom agents as ~/.copilot/agents/<name>.agent.md (excluding PROMPT-DEFENSE/INDEX/README)
#   4. Generates AGENTS.md and .github/copilot-instructions.md in project root (backing up non-Coco files once)
#   5. Second run leaves mcp-config.json and project instructions byte-identical with no duplicate backups
#   6. --dry-run in a fresh temp dir writes 0 files
#   7. --uninstall removes Coco's skills, agents, and mcpServers.coco while preserving user entries and foreign links
#   8. --core-only and --systems <bundle> honor bundle selection
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/copilot-cli-check.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1" >&2; exit 1; }

run_installer() {
  local proj=$1 home=$2
  shift 2
  (cd "$proj" && env -u COPILOT_HOME HOME="$home" bash "$ROOT/adapters/github-copilot-cli/install.sh" "$@")
}

echo "=== 1. Dry-run in fresh temp dir writes 0 files ==="
DRY_HOME="$WORK/dry-home"
DRY_PROJ="$WORK/dry-proj"
mkdir -p "$DRY_HOME" "$DRY_PROJ"
run_installer "$DRY_PROJ" "$DRY_HOME" --dry-run >"$WORK/dry.log" 2>&1
dry_files=$(find "$DRY_HOME" "$DRY_PROJ" -mindepth 1 | wc -l | tr -d ' ')
[[ "$dry_files" -eq 0 ]] || fail "--dry-run wrote $dry_files path(s) in fresh temp dirs"
pass "--dry-run wrote 0 files"

echo "=== 2. Install into seeded HOME + project dir ==="
THOME="$WORK/home"
TPROJ="$WORK/proj"
EXT_SKILL="$WORK/external-skill"
mkdir -p "$THOME/.copilot/skills/user-keep" "$THOME/.copilot/agents" "$TPROJ/.github" "$EXT_SKILL"

cat >"$THOME/.copilot/mcp-config.json" <<'JSON'
{"mcpServers":{"other":{"type":"local","command":"node","args":["other-mcp.js"],"tools":["*"]}}}
JSON
cp "$THOME/.copilot/mcp-config.json" "$WORK/orig-mcp.json"

printf '# User skill\n' >"$THOME/.copilot/skills/user-keep/SKILL.md"
printf '# External skill\n' >"$EXT_SKILL/SKILL.md"
ln -s "$EXT_SKILL" "$THOME/.copilot/skills/foreign-link"
printf '# User agent\n' >"$THOME/.copilot/agents/user-custom.agent.md"
printf '# Hand-written AGENTS\n' >"$TPROJ/AGENTS.md"
printf '# Hand-written Copilot instructions\n' >"$TPROJ/.github/copilot-instructions.md"

run_installer "$TPROJ" "$THOME" >"$WORK/install1.log" 2>&1

[[ -f "$THOME/.copilot/mcp-config.json.bak" ]] || fail "mcp-config.json.bak was not created"
cmp -s "$THOME/.copilot/mcp-config.json.bak" "$WORK/orig-mcp.json" || fail "mcp-config.json.bak does not match original user file"

python3 - "$THOME/.copilot/mcp-config.json" <<'PY'
import json, pathlib, sys
data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
servers = data.get("mcpServers") or {}
assert servers.get("other") == {
    "type": "local", "command": "node", "args": ["other-mcp.js"], "tools": ["*"]
}, f"mcpServers.other clobbered: {servers.get('other')}"
assert servers.get("coco") == {
    "type": "local",
    "command": "npx",
    "args": ["-y", "cocosuperintelligence", "mcp"],
    "tools": ["*"],
}, f"mcpServers.coco mismatch: {servers.get('coco')}"
PY
pass "mcp-config.json preserves mcpServers.other, adds mcpServers.coco, and writes .bak"

# Check skills: core (brainstorming), bundle (gsd), SI front doors (ai-super-intelligence), plus user/foreign preserved
[[ -L "$THOME/.copilot/skills/brainstorming" ]] || fail "core skill brainstorming not linked"
[[ -L "$THOME/.copilot/skills/ai-super-intelligence" ]] || fail "SI front-door skill ai-super-intelligence not linked"
gsd_skill=$(basename "$(find "$ROOT/systems/gsd/skills" -mindepth 2 -maxdepth 2 -name SKILL.md | head -n 1 | xargs dirname)")
[[ -L "$THOME/.copilot/skills/$gsd_skill" ]] || fail "bundle skill $gsd_skill not linked"
[[ ! -L "$THOME/.copilot/skills/user-keep" && -f "$THOME/.copilot/skills/user-keep/SKILL.md" ]] || fail "user skill dir overwritten"
[[ "$(readlink "$THOME/.copilot/skills/foreign-link")" == "$EXT_SKILL" ]] || fail "foreign skill symlink overwritten"
pass "core, bundle, and SI front-door skills linked; user dir and foreign symlink preserved"

# Check custom agents (*.agent.md) without PROMPT-DEFENSE / INDEX / README
agent_links=$(find "$THOME/.copilot/agents" -maxdepth 1 -type l -name '*.agent.md' | wc -l | tr -d ' ')
[[ "$agent_links" -ge 30 ]] || fail "expected >=30 linked *.agent.md files, found $agent_links"
for bad in PROMPT-DEFENSE INDEX README; do
  [[ ! -e "$THOME/.copilot/agents/${bad}.agent.md" && ! -L "$THOME/.copilot/agents/${bad}.agent.md" ]] \
    || fail "excluded file ${bad}.agent.md was linked"
done
[[ -f "$THOME/.copilot/agents/user-custom.agent.md" && ! -L "$THOME/.copilot/agents/user-custom.agent.md" ]] \
  || fail "user custom agent was overwritten"
pass "$agent_links *.agent.md symlinks created (PROMPT-DEFENSE/INDEX/README excluded)"

# Check AGENTS.md and .github/copilot-instructions.md + single backup
[[ -f "$TPROJ/AGENTS.md" && -f "$TPROJ/AGENTS.md.bak" ]] || fail "AGENTS.md or AGENTS.md.bak missing"
[[ -f "$TPROJ/.github/copilot-instructions.md" && -f "$TPROJ/.github/copilot-instructions.md.bak" ]] \
  || fail ".github/copilot-instructions.md or its .bak missing"
grep -q 'Hand-written AGENTS' "$TPROJ/AGENTS.md.bak" || fail "AGENTS.md.bak lost user content"
pass "AGENTS.md and .github/copilot-instructions.md generated with initial .bak backups"

echo "=== 3. Re-run is byte-identical with no duplicate backups ==="
cp "$THOME/.copilot/mcp-config.json" "$WORK/mcp-after-1.json"
cp "$TPROJ/AGENTS.md" "$WORK/agents-after-1.md"
cp "$TPROJ/.github/copilot-instructions.md" "$WORK/instr-after-1.md"

run_installer "$TPROJ" "$THOME" >"$WORK/install2.log" 2>&1

cmp -s "$THOME/.copilot/mcp-config.json" "$WORK/mcp-after-1.json" || fail "re-run changed mcp-config.json bytes"
cmp -s "$THOME/.copilot/mcp-config.json.bak" "$WORK/orig-mcp.json" || fail "re-run clobbered mcp-config.json.bak"
cmp -s "$TPROJ/AGENTS.md" "$WORK/agents-after-1.md" || fail "re-run changed AGENTS.md bytes"
cmp -s "$TPROJ/.github/copilot-instructions.md" "$WORK/instr-after-1.md" || fail "re-run changed copilot-instructions.md bytes"
extra_baks=$(find "$TPROJ" -name '*.bak-*' | wc -l | tr -d ' ')
[[ "$extra_baks" -eq 0 ]] || fail "re-run created $extra_baks duplicate backup(s)"
pass "second run kept mcp-config.json and project docs byte-identical"

echo "=== 4. --core-only and --systems honor selection ==="
CHOME="$WORK/core-home"
CPROJ="$WORK/core-proj"
mkdir -p "$CHOME" "$CPROJ"
run_installer "$CPROJ" "$CHOME" --core-only >"$WORK/core.log" 2>&1
[[ -L "$CHOME/.copilot/skills/brainstorming" ]] || fail "--core-only missed core skill"
[[ ! -e "$CHOME/.copilot/skills/ai-super-intelligence" && ! -L "$CHOME/.copilot/skills/ai-super-intelligence" ]] \
  || fail "--core-only installed SI front-door skill"
[[ ! -e "$CHOME/.copilot/skills/$gsd_skill" && ! -L "$CHOME/.copilot/skills/$gsd_skill" ]] \
  || fail "--core-only installed GSD skill"
pass "--core-only installs core set only"

SHOME="$WORK/sys-home"
SPROJ="$WORK/sys-proj"
mkdir -p "$SHOME" "$SPROJ"
run_installer "$SPROJ" "$SHOME" --systems gsd >"$WORK/sys.log" 2>&1
[[ -L "$SHOME/.copilot/skills/$gsd_skill" ]] || fail "--systems gsd missed GSD skill"
[[ ! -e "$SHOME/.copilot/skills/ai-super-intelligence" && ! -L "$SHOME/.copilot/skills/ai-super-intelligence" ]] \
  || fail "--systems gsd installed SI front-door skill"
help_out=$(bash "$ROOT/adapters/github-copilot-cli/install.sh" --help)
[[ "$help_out" == *"GitHub Copilot CLI adapter"* && "$help_out" != *"/usr/bin/env"* ]] \
  || fail "--help output invalid"
pass "--systems gsd and --help behave cleanly"

echo "=== 5. --uninstall removes Coco artifacts and preserves user state ==="
run_installer "$TPROJ" "$THOME" --uninstall >"$WORK/uninstall.log" 2>&1

coco_skill_links=$(find "$THOME/.copilot/skills" -maxdepth 1 -type l -lname "$ROOT/*" | wc -l | tr -d ' ')
coco_agent_links=$(find "$THOME/.copilot/agents" -maxdepth 1 -type l -lname "$ROOT/*" | wc -l | tr -d ' ')
[[ "$coco_skill_links" -eq 0 ]] || fail "--uninstall left $coco_skill_links Coco skill link(s)"
[[ "$coco_agent_links" -eq 0 ]] || fail "--uninstall left $coco_agent_links Coco agent link(s)"
[[ -f "$THOME/.copilot/skills/user-keep/SKILL.md" ]] || fail "--uninstall removed user skill dir"
[[ "$(readlink "$THOME/.copilot/skills/foreign-link")" == "$EXT_SKILL" ]] || fail "--uninstall removed foreign symlink"
[[ -f "$THOME/.copilot/agents/user-custom.agent.md" ]] || fail "--uninstall removed user agent"

python3 - "$THOME/.copilot/mcp-config.json" <<'PY'
import json, pathlib, sys
data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
servers = data.get("mcpServers") or {}
assert "coco" not in servers, f"--uninstall left mcpServers.coco: {servers}"
assert servers.get("other") == {
    "type": "local", "command": "node", "args": ["other-mcp.js"], "tools": ["*"]
}, f"--uninstall damaged mcpServers.other: {servers}"
PY
pass "--uninstall removed Coco skills, agents, and mcpServers.coco while preserving mcpServers.other"

echo "PASS: all GitHub Copilot CLI adapter checks passed"
