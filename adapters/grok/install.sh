#!/usr/bin/env bash
# Grok adapter — wires Coco artifacts into ~/.grok/
#
# Usage:
#   bash adapters/grok/install.sh                    # install everything
#   bash adapters/grok/install.sh --systems gsd      # add GSD bundle
#   bash adapters/grok/install.sh --dry-run          # preview only
#   bash adapters/grok/install.sh --uninstall        # remove everything this installer wrote

set -euo pipefail
unset CDPATH

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_HOME="${GROK_HOME:-$HOME/.grok}"
DRY_RUN=0
SYSTEMS=()
CORE_ONLY=0
UNINSTALL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "$1" ;;
    --core-only) CORE_ONLY=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --help|-h)
      bash "$REPO_ROOT/scripts/print-usage.sh" "$0"
      exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

# Bundles install by default. This adapter predates that contract and installed the
# core set alone unless --systems was passed, so a plain run delivered 74 of its 188
# skills. Naming a subset still wins; --core-only is the opt-out.
if [[ $CORE_ONLY -eq 1 ]]; then
  SYSTEMS=()
elif [[ $UNINSTALL -eq 0 && ${#SYSTEMS[@]} -eq 0 ]]; then
  while IFS= read -r bundle; do
    [[ -n "$bundle" ]] && SYSTEMS+=("$bundle")
  done < <(bash "$REPO_ROOT/scripts/installable-bundles.sh" --one-per-line 2>/dev/null || true)
  if [[ ${#SYSTEMS[@]} -eq 0 ]]; then
    echo "WARNING: scripts/installable-bundles.sh listed no bundles; installing core only." >&2
  fi
fi

run() {
  if [[ $DRY_RUN -eq 1 ]]; then echo "DRY: $*"; else "$@"; fi
}

# Removes only what this installer wrote: symlinks into this clone, the generated SI-*
# command files (matched by the generator's marker line, so a user's own SI*.md stays),
# the config.toml MCP block between its markers, and the hooks file (matched by the hook
# binary path it contains). Anything else under the target is left alone.
uninstall() {
  # Before any find/rm: canonicalize, then refuse empty, the root, or a non-directory.
  # `cd && pwd -P` collapses /./ and a symlink to / into "/". macOS bash leaves
  # exactly "//" as "//" (Linux yields "/"). Both name the filesystem root.
  local canon
  if [[ -n "${GROK_HOME+x}" && -z "$GROK_HOME" ]]; then
    echo "Refusing to uninstall: GROK_HOME must not be empty or /." >&2
    exit 1
  fi
  if [[ -z "$TARGET_HOME" ]]; then
    echo "Refusing to uninstall: target must not be empty or /." >&2
    exit 1
  fi
  if [[ ! -d "$TARGET_HOME" ]]; then
    if [[ -e "$TARGET_HOME" || -L "$TARGET_HOME" ]]; then
      echo "Refusing to uninstall: $TARGET_HOME is not a directory." >&2
      exit 1
    fi
    echo "Nothing to remove: $TARGET_HOME does not exist."
    return 0
  fi
  # A relative target is anchored to $PWD before `cd`. CDPATH is unset above;
  # an absolute path is also ignored by `cd`'s CDPATH search.
  case "$TARGET_HOME" in
    /*) ;;
    *) TARGET_HOME=$PWD/$TARGET_HOME ;;
  esac
  canon=$(cd "$TARGET_HOME" && pwd -P) || {
    echo "Refusing to uninstall: $TARGET_HOME is not a directory." >&2
    exit 1
  }
  if [[ "$canon" == "/" || "$canon" == "//" ]]; then
    if [[ -n "${GROK_HOME+x}" ]]; then
      echo "Refusing to uninstall: GROK_HOME must not be empty or /." >&2
    else
      echo "Refusing to uninstall: target must not be empty or /." >&2
    fi
    exit 1
  fi
  if [[ ! -d "$canon" ]]; then
    echo "Refusing to uninstall: $canon is not a directory." >&2
    exit 1
  fi
  TARGET_HOME=$canon
  local f cfg="$TARGET_HOME/config.toml" hook="$TARGET_HOME/hooks/coco-m0.json" mode rewrite dir tmp p t hops
  # Resolve a symlinked config before any removal. A target that is not a
  # regular file, or a cycle past 40 hops, refuses here so the tree stays
  # untouched. Stock macOS has no GNU readlink -f and no realpath: walk the
  # links, then pwd -P the directory.
  rewrite=$cfg
  if [[ -L "$cfg" ]]; then
    p=$cfg
    hops=0
    while [ -L "$p" ]; do
      hops=$((hops + 1))
      if [[ $hops -gt 40 ]]; then
        echo "Refusing to edit $cfg: symlink cycle or chain exceeded 40 hops." >&2
        exit 1
      fi
      t=$(readlink "$p") || {
        echo "Refusing to edit $cfg: symlink does not resolve to a regular file." >&2
        exit 1
      }
      case "$t" in
        /*) p=$t ;;
        *) p=$(dirname "$p")/$t ;;
      esac
    done
    dir=$(cd "$(dirname "$p")" && pwd -P) || {
      echo "Refusing to edit $cfg: symlink does not resolve to a regular file." >&2
      exit 1
    }
    rewrite="$dir/${p##*/}"
    echo "config.toml is a symlink; editing its target in place: $rewrite"
    if [[ ! -f "$rewrite" ]]; then
      echo "Refusing to edit $cfg: symlink does not resolve to a regular file." >&2
      exit 1
    fi
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY: remove symlinks into $REPO_ROOT/ under $TARGET_HOME"
  else
    # -H follows a symlinked start dir so clone links inside it are still swept.
    find -H "$TARGET_HOME" -type l -lname "$REPO_ROOT/*" -delete
  fi
  # A symlinked commands/ may point outside the target. Do not follow it.
  if [[ -L "$TARGET_HOME/commands" ]]; then
    echo "NOTE: $TARGET_HOME/commands is a symlink; skipped the command sweep."
  elif [[ -d "$TARGET_HOME/commands" ]]; then
    # NUL-delimited names: a newline in a filename must not split the rm.
    # -P does not follow a symlinked start path.
    while IFS= read -r -d '' f; do
      if grep -q -e 'Generated by `build_commands.py`' -e 'Generated by `build_meta_commands.py`' -- "$f"; then
        run rm -- "$f"
      fi
    done < <(find -P "$TARGET_HOME/commands" -maxdepth 1 -type f \( -name 'SI.md' -o -name 'SI-*.md' \) -print0)
  fi
  if [[ -f "$cfg" ]] && grep -q '^# coco:mcp-start$' "$cfg" && grep -q '^# coco:mcp-end$' "$cfg"; then
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "DRY: remove the coco:mcp block from $cfg"
    else
      # A symlinked config stays a symlink: rewrite the resolved target, never the link.
      # stat -L reads that target's mode. A link's own mode (often 0777) is never applied.
      # mktemp in the target's directory closes the planted fixed-name temp race.
      dir=$(dirname "$rewrite")
      tmp=$(mktemp "$dir/config.toml.XXXXXX")
      trap 'rm -f -- "$tmp"' EXIT  # a failed rewrite must not leave a copy of the config (it may hold a secret)
      awk '/^# coco:mcp-start$/{skip=1} !skip{print} /^# coco:mcp-end$/{skip=0}' "$rewrite" > "$tmp"
      mode=$(stat -L -c %a "$rewrite" 2>/dev/null || stat -L -f %Lp "$rewrite" || true)
      mode=${mode:-600}
      chmod "$mode" "$tmp"
      mv "$tmp" "$rewrite"
      trap - EXIT
      if ! grep -q '[^[:space:]]' "$rewrite"; then
        # Never delete a symlink's target: an emptied dotfile must stay, or the
        # link dangles and the user's real file is gone.
        if [[ -L "$cfg" ]]; then
          echo "NOTE: $cfg is a symlink; left the empty target in place."
        else
          rm -f -- "$rewrite"
        fi
      fi
      # A group- or world-readable file that still holds a secret must not stay that way.
      if [[ -f "$rewrite" ]] && grep -Eq 'api_key|token' "$rewrite"; then
        if (( (8#$mode & 0044) != 0 )); then
          chmod 600 "$rewrite"
          echo "WARNING: $cfg contains api_key or token and was group- or world-readable; set mode to 0600." >&2
        fi
      fi
    fi
  fi
  if [[ -f "$hook" ]] && grep -qF "$HOME/.coco/bin/coco-m0-hook " "$hook"; then
    run rm "$hook"
    [[ $DRY_RUN -eq 1 ]] || rmdir "$TARGET_HOME/hooks" 2>/dev/null || true
  fi
  echo "Removed Coco-generated files from $TARGET_HOME"
}
if [[ $UNINSTALL -eq 1 ]]; then uninstall; exit 0; fi

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

link_si_personas() {
  # 495-persona board → ~/.grok/personas/<dept>/<slug>.md
  local sys_dir=$1
  local dept personas_dir f
  for dept in "$sys_dir"/*/; do
    personas_dir="${dept}personas"
    [[ -d "$personas_dir" ]] || continue
    for f in "$personas_dir"/*.md; do
      [[ -f "$f" ]] || continue
      link_dir "$f" "$TARGET_HOME/personas/$(basename "$dept")/$(basename "$f")"
    done
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
    link_si_personas "$sys_dir"
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
  # Create a missing config as 0600. umask applies only on create, so an existing file keeps its mode.
  ( umask 077; : >> "$cfg" )
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
