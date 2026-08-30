#!/usr/bin/env bash
# Grok adapter — wires Coco artifacts into ~/.grok/
#
# Usage:
#   bash adapters/grok/install.sh                    # install everything
#   bash adapters/grok/install.sh --systems gsd      # add GSD bundle
#   bash adapters/grok/install.sh --dry-run          # preview only

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_HOME="${GROK_HOME:-$HOME/.grok}"
DRY_RUN=0
SYSTEMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "$1" ;;
    --help|-h)
      grep '^#' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

run() {
  if [[ $DRY_RUN -eq 1 ]]; then echo "DRY: $*"; else "$@"; fi
}

STALE_COUNT=0
LINKED=0

link_dir() {
  local src=$1 dst=$2
  # A real file or directory at the target is NOT overwritten, because it may be the
  # user's own work. But it is reported loudly and counted, because a silent skip means
  # the target keeps serving a stale copy through every future re-install and nobody
  # finds out.
  if [[ -e "$dst" && ! -L "$dst" ]]; then
    echo "STALE: $dst is a real file, not a symlink — NOT updated. Remove it to let the installer manage it."
    STALE_COUNT=$((STALE_COUNT + 1))
    return
  fi
  [[ -L "$dst" ]] && run rm "$dst"
  run mkdir -p "$(dirname "$dst")"
  run ln -sf "$src" "$dst"
  echo "Linked: $dst -> $src"
  LINKED=$((LINKED + 1))
}

report_stale() {
  [[ $STALE_COUNT -eq 0 ]] && return 0
  echo
  echo "WARNING: $STALE_COUNT target(s) were real files rather than symlinks and were left"
  echo "untouched. They will keep serving stale content until you remove them. Re-run this"
  echo "installer afterwards to link them."
}

link_skills() {
  local dir=$1
  [[ -d "$dir" ]] || return 0
  local skill
  for skill in "$dir"/*/; do
    [[ -f "$skill/SKILL.md" ]] || continue
    link_dir "$skill" "$TARGET_HOME/skills/$(basename "$skill")"
  done
}

link_commands() {
  # Map commands/<namespace>/<name>.md → ~/.grok/commands/<namespace>:<name>.md
  # Grok discovers user-level commands as flat *.md files; it does not recurse.
  local ns nsname cmd cname
  for ns in "$REPO_ROOT/commands"/*/; do
    [[ -d "$ns" ]] || continue
    nsname=$(basename "$ns")
    for cmd in "$ns"*.md; do
      [[ -f "$cmd" ]] || continue
      cname=$(basename "$cmd" .md)
      [[ "$cname" == "INDEX" ]] && continue
      if [[ "$cname" == "_index" ]]; then
        link_dir "$cmd" "$TARGET_HOME/commands/$nsname.md"
      else
        link_dir "$cmd" "$TARGET_HOME/commands/$nsname:$cname.md"
      fi
    done
  done
}

link_agents() {
  local dir=$1
  [[ -d "$dir" ]] || return 0
  local agent name
  for agent in "$dir"/*.md; do
    [[ -f "$agent" ]] || continue
    name=$(basename "$agent")
    [[ "$name" == "INDEX.md" || "$name" == "README.md" ]] && continue
    link_dir "$agent" "$TARGET_HOME/agents/$name"
  done
}

link_rules() {
  local src_dir="$REPO_ROOT/rules/cursor-mdc"
  [[ -d "$src_dir" ]] || return 0
  run mkdir -p "$TARGET_HOME/rules"
  local mdc name
  for mdc in "$src_dir"/*.mdc; do
    [[ -f "$mdc" ]] || continue
    name=$(basename "$mdc" .mdc)
    link_dir "$mdc" "$TARGET_HOME/rules/$name.md"
  done
}

link_workflows() {
  local wf
  [[ -d "$REPO_ROOT/workflows" ]] || return 0
  for wf in "$REPO_ROOT/workflows"/*.md; do
    [[ -f "$wf" ]] || continue
    link_dir "$wf" "$TARGET_HOME/commands/workflow:$(basename "$wf")"
  done
}

link_si_team_skills() {
  local sys_dir=$1
  local team_dir
  for team_dir in "$sys_dir"/*/; do
    [[ -f "$team_dir/SKILL.md" ]] || continue
    link_dir "$team_dir" "$TARGET_HOME/skills/si-$(basename "$team_dir")"
  done
}

link_system() {
  local sys=$1
  local sys_dir="$REPO_ROOT/systems/$sys"
  [[ -d "$sys_dir" ]] || { echo "Unknown system: $sys" >&2; exit 1; }
  if [[ -d "$sys_dir/skills" ]]; then
    link_skills "$sys_dir/skills"
  fi
  if [[ -d "$sys_dir/agents" ]]; then
    link_agents "$sys_dir/agents"
  fi
  if [[ -d "$sys_dir/commands" ]]; then
    local c
    for c in "$sys_dir/commands"/*.md; do
      [[ -f "$c" ]] || continue
      link_dir "$c" "$TARGET_HOME/commands/$(basename "$c")"
    done
  fi
  # Superintelligence: SI-* commands are generated from per-team registries, not shipped as files.
  #   build_commands.py      → per-team scoped commands  (/SI-<Team>-<Verb>, 225)
  #   build_meta_commands.py → cross-team orchestrator    (/SI, /SI-Orchestrate, /SI-<Verb>, 17)
  if [[ -f "$sys_dir/ai/scripts/build_commands.py" ]]; then
    link_si_team_skills "$sys_dir"
    if command -v python3 >/dev/null 2>&1; then
      run env COCO_SI_COMMANDS_DIR="$TARGET_HOME/commands" python3 "$sys_dir/ai/scripts/build_commands.py"
      if [[ -f "$sys_dir/scripts/build_meta_commands.py" ]]; then
        run env COCO_SI_COMMANDS_DIR="$TARGET_HOME/commands" python3 "$sys_dir/scripts/build_meta_commands.py"
      fi
      echo "Generated SI-* commands (per-team + meta-orchestrator) into $TARGET_HOME/commands"
    else
      echo "Skip SI generation: python3 not found. Run $sys_dir/ai/scripts/build_commands.py and $sys_dir/scripts/build_meta_commands.py manually."
    fi
  fi
}

wire_mcp() {
  local cfg="$TARGET_HOME/config.toml"
  local bin="$HOME/.coco/bin/coco-platform-mcp"
  local marker_start="# coco:mcp-start"
  local marker_end="# coco:mcp-end"

  if [[ ! -x "$bin" ]]; then
    echo "Skip MCP: $bin not found (coco-platform-mcp is installed by coco-connect, not this repo)."
    return 0
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY: would register [mcp_servers.coco-platform] in $cfg -> $bin"
    return 0
  fi
  run mkdir -p "$TARGET_HOME"
  if [[ -f "$cfg" ]] && grep -q 'mcp_servers.coco-platform' "$cfg"; then
    echo "MCP: coco-platform already in $cfg"
    return 0
  fi
  {
    echo ""
    echo "$marker_start"
    echo "# Registered by adapters/grok/install.sh. Native Grok config wins over"
    echo "# Cursor's ~/.cursor/mcp.json (which uses a relative ./backend path)."
    echo "[mcp_servers.coco-platform]"
    echo "command = \"$bin\""
    echo "enabled = true"
    echo "$marker_end"
  } >> "$cfg"
  echo "MCP: registered coco-platform -> $bin in $cfg"
}

wire_hooks() {
  local hook="$HOME/.coco/bin/coco-m0-hook"
  local dest="$TARGET_HOME/hooks/coco-m0.json"
  if [[ ! -x "$hook" ]]; then
    echo "Skip hooks: $hook not found."
    return 0
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY: would write $dest"
    return 0
  fi
  run mkdir -p "$TARGET_HOME/hooks"
  cat > "$dest" <<EOF
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "$hook sessionstart", "timeout": 12 }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          { "type": "command", "command": "$hook precompact", "timeout": 10 }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "$hook stop", "timeout": 10 }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          { "type": "command", "command": "$hook posttooluse", "timeout": 8 }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "$hook userpromptsubmit", "timeout": 12 }
        ]
      }
    ]
  }
}
EOF
  echo "Hooks: wrote $dest"
}

echo "Coco · Grok adapter"
echo "Source: $REPO_ROOT"
echo "Target: $TARGET_HOME"
[[ $DRY_RUN -eq 1 ]] && echo "(dry-run mode)"

link_skills "$REPO_ROOT/skills"
echo "Skills: core linked"
link_commands
echo "Commands: core linked"
link_agents "$REPO_ROOT/agents"
echo "Agents: core linked"
link_rules
echo "Rules: linked into $TARGET_HOME/rules"
link_workflows
echo "Workflows: linked as commands"

for sys in "${SYSTEMS[@]:-}"; do
  [[ -n "$sys" ]] && link_system "$sys"
done

wire_mcp
wire_hooks
report_stale

echo "Done. Start a new Grok session (or reload) to pick up skills, commands, and MCP."
