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
#   bash adapters/vscode/install.sh                        # core + every bundle
#   bash adapters/vscode/install.sh --core-only            # core only, no bundles
#   bash adapters/vscode/install.sh --systems gsd,brain    # only these bundles
#   bash adapters/vscode/install.sh --dry-run              # preview only
#   bash adapters/vscode/install.sh --source /path/to/coco # link a different checkout
#   bash adapters/vscode/install.sh --user-dir "<dir>"     # extra VS Code User folder
#
# Bundles default to every bundle that ships skills or agents, derived by
# scripts/installable-bundles.sh so a new bundle needs no edit here. --core-only opts out
# of all of them and wins over --systems; --systems <list> replaces the default set.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_ROOT="$REPO_ROOT"
COPILOT_HOME="${COPILOT_HOME:-$HOME/.copilot}"
DRY_RUN=0
SYSTEMS=()
CORE_ONLY=0
EXTRA_USER_DIRS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --core-only) CORE_ONLY=1 ;;
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

# No flag means every bundle that ships skills or agents. The advertised totals (280
# commands, 171 skills) are what a plain install is expected to deliver, and leaving them
# behind an opt-in flag is how 70 of 171 skills went missing without a word.
if [[ $CORE_ONLY -eq 1 ]]; then
  SYSTEMS=()
elif [[ ${#SYSTEMS[@]} -eq 0 ]]; then
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

STALE_COUNT=0

# Receipt counters. Every number printed at the end is counted while linking, so the
# summary cannot drift from what was actually installed.
SKILL_COUNT=0
AGENT_COUNT=0
COMMAND_COUNT=0
SI_COUNT=""
SI_SKIP=""
BUNDLES_INSTALLED=()

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

# A profile's directory name comes from `location` in globalStorage/storage.json, and that
# value is not always a single path segment -- VS Code writes nested locations such as
# "builtin/agents". Globbing profiles/*/ therefore does the wrong thing twice: it invents a
# prompts folder under a container segment that is not a profile, and it never descends to
# the real one. Read the declared list instead, and skip profiles whose useDefaultFlags.prompts
# is true, since those deliberately share the default profile's prompts folder.
profile_prompt_dirs() {
  local user_dir=$1 storage="$1/globalStorage/storage.json"
  [[ -f "$storage" ]] || return 0
  command -v python3 >/dev/null 2>&1 || return 0
  python3 - "$storage" <<'PY' 2>/dev/null || true
import json, sys
try:
    with open(sys.argv[1]) as fh:
        profiles = json.load(fh).get("userDataProfiles") or []
except Exception:
    sys.exit(0)
for p in profiles:
    loc = p.get("location")
    if not isinstance(loc, str) or not loc:
        continue
    if (p.get("useDefaultFlags") or {}).get("prompts"):
        continue
    print(loc)
PY
}

collect_prompt_dirs() {
  local -a user_dirs=()
  local d extra u loc found
  while IFS= read -r d; do [[ -n "$d" ]] && user_dirs+=("$d"); done < <(detect_user_dirs)
  for extra in "${EXTRA_USER_DIRS[@]:-}"; do
    [[ -n "$extra" ]] && user_dirs+=("$extra")
  done
  for u in "${user_dirs[@]:-}"; do
    [[ -n "$u" ]] || continue
    echo "$u/prompts"
    found=0
    while IFS= read -r loc; do
      [[ -n "$loc" ]] || continue
      found=1
      echo "$u/profiles/$loc/prompts"
    done < <(profile_prompt_dirs "$u")
    # Only fall back to guessing when the profile list could not be read at all (no
    # python3, or no storage.json yet). A readable list that yields nothing is an answer,
    # not a failure: it means every profile shares the default prompts folder.
    if [[ "$found" -eq 0 && ! -f "$u/globalStorage/storage.json" ]]; then
      for d in "$u"/profiles/*/; do
        [[ -d "$d" ]] && echo "${d%/}/prompts"
      done
    fi
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
  SKILL_COUNT=$((SKILL_COUNT + LINKED))
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
  AGENT_COUNT=$((AGENT_COUNT + LINKED))
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
  COMMAND_COUNT=$((COMMAND_COUNT + count))
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
  # files then point at that folder. scripts/generate-si-commands.sh runs both generators
  # (per-team + meta-orchestrator), which is the whole family rather than half of it.
  if [[ -f "$sys_dir/ai/scripts/build_commands.py" ]]; then
    local si_dir="$COPILOT_HOME/coco-generated/si-commands"
    local si_args=(--target "$si_dir")
    [[ $DRY_RUN -eq 1 ]] && si_args+=(--dry-run)

    local out
    if ! out=$(bash "$REPO_ROOT/scripts/generate-si-commands.sh" "${si_args[@]}" 2>&1); then
      echo "WARNING: scripts/generate-si-commands.sh failed; the SI-* command family is" >&2
      echo "missing from this install. Re-run it by hand to see the generator error." >&2
      SI_COUNT=""
      SI_SKIP="generator failed"
      return 0
    fi
    echo "$out"
    [[ $DRY_RUN -eq 1 ]] && return 0

    SI_COUNT=$(printf '%s\n' "$out" | sed -n 's/^Generated \([0-9][0-9]*\) SI commands.*/\1/p' | tail -n 1)
    if [[ -z "$SI_COUNT" ]]; then
      # Deliberately not assuming 242: when the generators did not run the count is
      # unknown, and the receipt says so rather than printing a number nobody verified.
      SI_SKIP=$(printf '%s\n' "$out" | sed -n 's/^Skip SI generation: //p' | head -n 1)
      [[ -n "$SI_SKIP" ]] || SI_SKIP="unknown reason"
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

print_receipt() {
  [[ $DRY_RUN -eq 1 ]] && return 0
  local bundles="core only"
  [[ ${#BUNDLES_INSTALLED[@]} -gt 0 ]] && bundles="$(IFS=,; echo "${BUNDLES_INSTALLED[*]}")"
  local commands
  if [[ ${#PROMPT_DIRS[@]} -eq 0 ]]; then
    commands="0   (no VS Code User folder found, so prompt files were skipped)"
  elif [[ -n "$SI_COUNT" ]]; then
    commands="$((COMMAND_COUNT + SI_COUNT))   ($COMMAND_COUNT core + $SI_COUNT Super Intelligence)"
  elif [[ -n "$SI_SKIP" ]]; then
    commands="$COMMAND_COUNT   (core commands only; SI generation skipped: $SI_SKIP)"
  else
    commands="$COMMAND_COUNT   (core commands only)"
  fi
  echo
  echo "Installed for VS Code / Copilot CLI:"
  echo "  Slash commands : $commands"
  echo "  Skills         : $SKILL_COUNT"
  echo "  Subagents      : $AGENT_COUNT"
  echo "  Bundles        : $bundles"
  echo "Core-only install: bash install.sh --adapter vscode --core-only"
}

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
  [[ -n "$sys" ]] || continue
  BUNDLES_INSTALLED+=("$sys")
  link_system "$sys"
done

if [[ $STALE_COUNT -gt 0 ]]; then
  echo
  echo "WARNING: $STALE_COUNT target(s) were real files rather than symlinks and were left"
  echo "untouched. They will keep serving stale content until you remove them. Re-run this"
  echo "installer afterwards to link them."
fi
print_receipt

echo "Done. Reload VS Code (Developer: Reload Window) to pick up the new files."
