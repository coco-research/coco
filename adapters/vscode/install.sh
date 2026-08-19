#!/usr/bin/env bash
# VS Code adapter — wires Coco artifacts into the folders VS Code chat and the
# Copilot CLI agent runtime read natively. No extension required.
#
# Where things land:
#   skills/<name>/            -> ~/.copilot/skills/<name>/                        (symlink)
#   agents/*.md               -> ~/.copilot/agents/*.md                           (symlink)
#   commands/<ns>/<name>.md   -> <VS Code profile>/prompts/<ns>-<name>.prompt.md  (symlink)
#   commands/<ns>/_index.md   -> <VS Code profile>/prompts/<ns>.prompt.md         (symlink)
#   rules/cursor-mdc/*.mdc    -> ~/.copilot/instructions/*.instructions.md        (generated)
#
# ~/.copilot/{skills,agents,instructions} are default VS Code discovery locations
# (chat.agentSkillsLocations, chat.agentFilesLocations, chat.instructionsFilesLocations)
# and are also what the Copilot CLI agent runtime reads, so one install serves both.
# Prompt files have no user-level default outside the VS Code profile, so slash
# commands are linked into every profile's prompts folder.
#
# Usage:
#   bash adapters/vscode/install.sh                        # install everything
#   bash adapters/vscode/install.sh --systems gsd,brain    # add bundles
#   bash adapters/vscode/install.sh --dry-run              # preview only
#   bash adapters/vscode/install.sh --source /path/to/coco # link a different checkout
#   bash adapters/vscode/install.sh --user-dir "<dir>"     # extra VS Code User folder

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_ROOT="$REPO_ROOT"
COPILOT_HOME="${COPILOT_HOME:-$HOME/.copilot}"
DRY_RUN=0
SYSTEMS=()
EXTRA_USER_DIRS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "$1" ;;
    --source) shift; SOURCE_ROOT="$(cd "$1" && pwd)" ;;
    --user-dir) shift; EXTRA_USER_DIRS+=("$1") ;;
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
  # A dangling symlink is removed and relinked. These accumulate whenever the repo moves.
  [[ -L "$dst" ]] && run rm "$dst"
  run mkdir -p "$(dirname "$dst")"
  run ln -sf "$src" "$dst"
}

# VS Code keeps prompt files per profile, under <User>/prompts and
# <User>/profiles/<id>/prompts. Every VS Code-family install found on this machine gets
# the commands, so switching profile or edition does not silently lose them.
detect_user_dirs() {
  local -a bases=()
  case "$(uname -s)" in
    Darwin) bases=("$HOME/Library/Application Support") ;;
    MINGW*|MSYS*|CYGWIN*) bases=("${APPDATA:-$HOME/AppData/Roaming}") ;;
    *) bases=("${XDG_CONFIG_HOME:-$HOME/.config}") ;;
  esac
  local base app
  for base in "${bases[@]}"; do
    for app in "Code" "Code - Insiders" "VSCodium" "VSCodium - Insiders"; do
      [[ -d "$base/$app/User" ]] && echo "$base/$app/User"
    done
  done
  return 0
}

collect_prompt_dirs() {
  local -a user_dirs=()
  local d extra u p
  while IFS= read -r d; do [[ -n "$d" ]] && user_dirs+=("$d"); done < <(detect_user_dirs)
  for extra in "${EXTRA_USER_DIRS[@]:-}"; do
    [[ -n "$extra" ]] && user_dirs+=("$extra")
  done
  for u in "${user_dirs[@]:-}"; do
    [[ -n "$u" ]] || continue
    echo "$u/prompts"
    for p in "$u"/profiles/*/; do
      [[ -d "$p" ]] && echo "${p%/}/prompts"
    done
  done
  return 0
}

# Counts are reported through a global rather than stdout, because the helpers also log
# their work and a command substitution would swallow that log into the number.
LINKED=0

link_skills_from() {
  local dir=$1 skill
  LINKED=0
  [[ -d "$dir" ]] || return 0
  for skill in "$dir"/*/; do
    [[ -f "$skill/SKILL.md" ]] || continue
    link_dir "$skill" "$COPILOT_HOME/skills/$(basename "$skill")"
    LINKED=$((LINKED + 1))
  done
}

link_agents_from() {
  local dir=$1 agent name
  LINKED=0
  [[ -d "$dir" ]] || return 0
  for agent in "$dir"/*.md; do
    [[ -f "$agent" ]] || continue
    name=$(basename "$agent")
    [[ "$name" == "INDEX.md" || "$name" == "README.md" ]] && continue
    link_dir "$agent" "$COPILOT_HOME/agents/$name"
    LINKED=$((LINKED + 1))
  done
}

# Commands become prompt files. The Claude and Cursor adapters name them
# "<ns>:<name>", but a colon is not a portable filename and VS Code derives the
# slash-command name from the filename, so the namespace is joined with a dash.
link_command() {
  local src=$1 stem=$2 dir
  for dir in "${PROMPT_DIRS[@]}"; do
    link_dir "$src" "$dir/$stem.prompt.md"
  done
}

link_commands() {
  local count=0 ns nsname cmd cname
  for ns in "$SOURCE_ROOT/commands"/*/; do
    [[ -d "$ns" ]] || continue
    nsname=$(basename "$ns")
    for cmd in "$ns"*.md; do
      [[ -f "$cmd" ]] || continue
      cname=$(basename "$cmd" .md)
      if [[ "$cname" == "_index" ]]; then
        link_command "$cmd" "$nsname"
      else
        link_command "$cmd" "$nsname-$cname"
      fi
      count=$((count + 1))
    done
  done
  echo "Commands: $count linked as prompt files into ${#PROMPT_DIRS[@]} profile folder(s)"
}

# Rules are the one artifact that cannot be symlinked: VS Code needs the
# .instructions.md extension and an `applyTo` glob header, while the source is Cursor's
# .mdc format carrying `globs` / `alwaysApply`. They are regenerated on every run, so
# re-installing after a rule edit is all it takes to refresh them.
generate_instructions() {
  local src_dir="$SOURCE_ROOT/rules/cursor-mdc"
  [[ -d "$src_dir" ]] || return 0
  run mkdir -p "$COPILOT_HOME/instructions"
  local count=0 mdc name out
  for mdc in "$src_dir"/*.mdc; do
    [[ -f "$mdc" ]] || continue
    name=$(basename "$mdc" .mdc)
    out="$COPILOT_HOME/instructions/$name.instructions.md"
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "DRY: generate $out from $mdc"
    else
      awk -v src="$mdc" '
        # Values may arrive already quoted, and a checkout on Windows may carry CRLF.
        # Both would otherwise be copied verbatim into the generated YAML header, where
        # a re-quoted value ("\"**/*.tsx\"") or a stray \r makes the whole rule
        # unparseable and silently drops it.
        { sub(/\r$/, "") }
        function unquote(v,   q) {
          q = substr(v, 1, 1)
          if ((q == "\"" || q == "\047") && substr(v, length(v), 1) == q && length(v) > 1)
            v = substr(v, 2, length(v) - 2)
          return v
        }
        function yaml_quote(v) {
          gsub(/"/, "\\\"", v)
          return "\"" v "\""
        }
        function emit_header(desc, applyTo) {
          print "---"
          if (desc != "") print "description: " yaml_quote(desc)
          print "applyTo: " yaml_quote(applyTo)
          print "---"
          print ""
          print "<!-- Generated by the Coco VS Code adapter from " src " — edit the source, then re-run the installer. -->"
          print ""
        }
        NR == 1 && $0 != "---" { emit_header("", "**"); print; next }
        NR == 1 && $0 == "---" { infm = 1; next }
        infm && $0 == "---" {
          infm = 0
          applyTo = globs
          if (always == "true" || applyTo == "") applyTo = "**"
          emit_header(desc, applyTo)
          next
        }
        infm {
          if ($0 ~ /^description:/) { desc = unquote(trim(substr($0, 13))) }
          else if ($0 ~ /^globs:/) { globs = unquote(trim(substr($0, 7))) }
          else if ($0 ~ /^alwaysApply:/) { always = unquote(trim(substr($0, 13))) }
          next
        }
        function trim(v) {
          sub(/^[ \t]+/, "", v)
          sub(/[ \t]+$/, "", v)
          return v
        }
        { print }
      ' "$mdc" > "$out"
    fi
    count=$((count + 1))
  done
  echo "Rules: $count generated into $COPILOT_HOME/instructions"
}

link_system() {
  local sys=$1
  local sys_dir="$SOURCE_ROOT/systems/$sys"
  [[ -d "$sys_dir" ]] || { echo "Unknown system: $sys" >&2; exit 1; }

  if [[ -d "$sys_dir/skills" ]]; then
    link_skills_from "$sys_dir/skills"
    echo "System $sys: $LINKED skill(s) linked"
  fi
  if [[ -d "$sys_dir/agents" ]]; then
    link_agents_from "$sys_dir/agents"
    echo "System $sys: $LINKED agent(s) linked"
  fi
  if [[ -d "$sys_dir/commands" && ${#PROMPT_DIRS[@]} -gt 0 ]]; then
    local c count=0
    for c in "$sys_dir/commands"/*.md; do
      [[ -f "$c" ]] || continue
      link_command "$c" "$(basename "$c" .md)"
      count=$((count + 1))
    done
    echo "System $sys: $count command(s) linked"
  fi

  # Superintelligence: SI-* commands are generated from per-team registries rather than
  # shipped as files, so they are built into a Coco-owned folder first and the prompt
  # files then point at that folder.
  #   build_commands.py      → per-team scoped commands  (/SI-<Team>-<Verb>)
  #   build_meta_commands.py → cross-team orchestrator    (/SI, /SI-Orchestrate, ...)
  if [[ -f "$sys_dir/ai/scripts/build_commands.py" ]]; then
    if ! command -v python3 >/dev/null 2>&1; then
      echo "Skip SI generation: python3 not found. Run $sys_dir/ai/scripts/build_commands.py manually."
      return
    fi
    local si_dir="$COPILOT_HOME/coco-generated/si-commands"
    run mkdir -p "$si_dir"
    run env COCO_SI_COMMANDS_DIR="$si_dir" python3 "$sys_dir/ai/scripts/build_commands.py"
    if [[ -f "$sys_dir/scripts/build_meta_commands.py" ]]; then
      run env COCO_SI_COMMANDS_DIR="$si_dir" python3 "$sys_dir/scripts/build_meta_commands.py"
    fi
    local si_count=0 f
    if [[ $DRY_RUN -eq 0 && ${#PROMPT_DIRS[@]} -gt 0 ]]; then
      for f in "$si_dir"/*.md; do
        [[ -f "$f" ]] || continue
        link_command "$f" "$(basename "$f" .md)"
        si_count=$((si_count + 1))
      done
    fi
    echo "System $sys: $si_count generated SI command(s) linked as prompt files"
  fi
}

PROMPT_DIRS=()
while IFS= read -r d; do [[ -n "$d" ]] && PROMPT_DIRS+=("$d"); done < <(collect_prompt_dirs)

echo "Coco · VS Code adapter"
echo "Source: $SOURCE_ROOT"
echo "Target: $COPILOT_HOME (skills, agents, instructions)"
[[ $DRY_RUN -eq 1 ]] && echo "(dry-run mode)"

if [[ ${#PROMPT_DIRS[@]} -eq 0 ]]; then
  echo
  echo "No VS Code User folder found, so slash commands were skipped."
  echo "Pass one explicitly if VS Code lives somewhere unusual:"
  echo "  bash adapters/vscode/install.sh --user-dir \"\$HOME/Library/Application Support/Code/User\""
  echo
else
  printf 'Prompts: %s\n' "${PROMPT_DIRS[@]}"
fi

link_skills_from "$SOURCE_ROOT/skills"
echo "Skills: $LINKED linked into $COPILOT_HOME/skills"
link_agents_from "$SOURCE_ROOT/agents"
echo "Agents: $LINKED linked into $COPILOT_HOME/agents"
[[ ${#PROMPT_DIRS[@]} -gt 0 ]] && link_commands
generate_instructions

for sys in "${SYSTEMS[@]:-}"; do
  [[ -n "$sys" ]] && link_system "$sys"
done

if [[ $STALE_COUNT -gt 0 ]]; then
  echo
  echo "WARNING: $STALE_COUNT target(s) were real files rather than symlinks and were left"
  echo "untouched. They will keep serving stale content until you remove them. Re-run this"
  echo "installer afterwards to link them."
fi

echo "Done. Reload VS Code (Developer: Reload Window) to pick up the new files."
