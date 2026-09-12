#!/usr/bin/env bash
# Codex adapter — generates AGENTS.md in current directory
#
# Codex CLI reads AGENTS.md (https://agents.md/) at project root.
# This adapter compiles Coco skills + rules into a single AGENTS.md.
#
# Usage:
#   bash adapters/codex/install.sh             # write ./AGENTS.md, all bundles
#   bash adapters/codex/install.sh --core-only # core set only, no bundles
#   bash adapters/codex/install.sh --systems gsd,brain   # only these bundles
#   bash adapters/codex/install.sh -o PATH     # write to PATH
#   bash adapters/codex/install.sh --dry-run
#
# Bundles default to every bundle that actually ships something
# (scripts/installable-bundles.sh), not to the core alone: defaulting to core folded
# about a third of the framework into AGENTS.md and said nothing about it. --systems
# overrides the default, --core-only asks for the core set, and --systems wins if both
# are given.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUTPUT="./AGENTS.md"
# The generic adapter delegates here, so the receipt names the tool the user asked for.
ADAPTER_LABEL="${COCO_ADAPTER_LABEL:-codex}"
DRY_RUN=0
CORE_ONLY=0
SYSTEMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o) shift; OUTPUT="${1:-}" ;;
    --dry-run) DRY_RUN=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "${1:-}" ;;
    --core-only) CORE_ONLY=1 ;;
    # Header only: this adapter's --help used to grep every '^#' line, which would also
    # print the explanatory comments inside the code as if they were usage.
    --help|-h) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

# Bundles default to everything that ships. Derived from the tree by the shared script,
# which excludes the documentation-only directories (`team`, `learning`) that ship no
# skills and no agents, so naming one of them cannot install nothing.
if [[ ${#SYSTEMS[@]} -eq 0 && $CORE_ONLY -eq 0 ]]; then
  default_bundles=$(bash "$REPO_ROOT/scripts/installable-bundles.sh")
  if [[ -n "$default_bundles" ]]; then
    IFS=',' read -ra SYSTEMS <<< "$default_bundles"
  fi
fi

# --core-only wins when both flags are given, uniformly across every adapter: the
# opt-out is the more conservative reading of a contradictory request.
if [[ "$CORE_ONLY" -eq 1 && "${#SYSTEMS[@]}" -gt 0 ]]; then
  SYSTEMS=()
fi

bundle_label() {
  if [[ ${#SYSTEMS[@]} -eq 0 ]]; then
    printf 'core only'
  else
    ( IFS=,; printf '%s' "${SYSTEMS[*]}" )
  fi
}

system_dir() {
  local sys=$1
  local dir="$REPO_ROOT/systems/$sys"
  [[ -d "$dir" ]] || { echo "Unknown system: $sys" >&2; exit 1; }
  printf '%s\n' "$dir"
}

emit_skill() {
  local skill=$1
  local name desc
  name=$(basename "$(dirname "$skill")")
  desc=$(awk -F': ' '/^description:/ {sub(/^description: */,""); gsub(/^"|"$/,""); print; exit}' "$skill")
  echo "- **$name** — $desc"
}

emit_invocation_guide() {
  cat <<'EOF'
## Codex Invocation Guide

Codex may not render Coco workflows as a visible slash-command palette. Treat the command and skill names in this file as model-available workflows.

When the user:
- types a literal command like `/team:plan` or `/gsd-plan-phase`, treat it as an explicit request to follow that workflow
- references a workflow name in plain English like `use team:ship`, `run gsd-new-project`, or `follow brain-init`, map it to the matching command or skill and follow it
- asks for an outcome that clearly matches one of the workflows below, prefer the named Coco workflow instead of inventing an ad hoc process

Routing preference:
1. Exact command name match
2. Exact skill name match
3. Closest plain-English match based on the descriptions in this file

If a workflow is chosen, say so briefly and then execute it.
EOF
}

emit_skills() {
  local found=0
  for skill in "$REPO_ROOT/skills"/*/SKILL.md; do
    [[ -f "$skill" ]] || continue
    emit_skill "$skill"
    found=1
  done
  for sys in ${SYSTEMS[@]+"${SYSTEMS[@]}"}; do
    local dir
    dir=$(system_dir "$sys")
    for skill in "$dir"/skills/*/SKILL.md; do
      [[ -f "$skill" ]] || continue
      emit_skill "$skill"
      found=1
    done
  done
  [[ $found -eq 1 ]] || echo "- None"
}

emit_commands_from_dir() {
  local base=$1
  for ns in "$base"/*/; do
    [[ -d "$ns" ]] || continue
    local nsname
    nsname=$(basename "$ns")
    for cmd in "$ns"*.md; do
      [[ -f "$cmd" ]] || continue
      local cname desc
      cname=$(basename "$cmd" .md)
      [[ "$cname" == "_index" ]] && continue
      desc=$(
        awk '
          /^>/ {
            sub(/^> */, "")
            print
            exit
          }
          /^# / {
            line=$0
            sub(/^# [^—-]+[—-] /, "", line)
            if (line != $0) {
              print line
              exit
            }
          }
        ' "$cmd"
      )
      if [[ -n "$desc" ]]; then
        echo "- \`/$nsname:$cname\` — $desc"
      else
        echo "- \`/$nsname:$cname\`"
      fi
    done
  done
}

emit_commands() {
  emit_commands_from_dir "$REPO_ROOT/commands"
  for sys in ${SYSTEMS[@]+"${SYSTEMS[@]}"}; do
    local dir
    dir=$(system_dir "$sys")
    [[ -d "$dir/commands" ]] || continue
    emit_commands_from_dir "$dir/commands"
  done
}

emit_agents_from_dir() {
  local base=$1
  for agent in "$base"/*.md; do
    [[ -f "$agent" ]] || continue
    local name desc
    name=$(basename "$agent" .md)
    [[ "$name" == "README" || "$name" == "INDEX" ]] && continue
    desc=$(awk -F': ' '/^description:/ {sub(/^description: */,""); gsub(/^"|"$/,""); print; exit}' "$agent")
    if [[ -n "$desc" ]]; then
      echo "- **$name** — $desc"
    else
      echo "- **$name**"
    fi
  done
}

emit_agents() {
  emit_agents_from_dir "$REPO_ROOT/agents"
  for sys in ${SYSTEMS[@]+"${SYSTEMS[@]}"}; do
    local dir
    dir=$(system_dir "$sys")
    [[ -d "$dir/agents" ]] || continue
    emit_agents_from_dir "$dir/agents"
  done
}

generate() {
  echo "# AGENTS.md"
  echo ""
  echo "Generated by Coco · adapters/codex/install.sh"
  echo "Source: $REPO_ROOT"
  echo "Systems: $(bundle_label)"
  echo ""
  emit_invocation_guide
  echo ""
  echo "## Skills"
  echo ""
  emit_skills
  echo ""
  echo "## Commands"
  echo ""
  emit_commands
  echo ""
  echo "## Agents"
  echo ""
  emit_agents
  echo ""
  echo "## Rules"
  echo ""
  for mdc in "$REPO_ROOT/rules/cursor-mdc"/*.mdc; do
    name=$(basename "$mdc" .mdc)
    echo "### $name"
    awk '/^---$/{f=!f; next} !f' "$mdc"
    echo ""
  done
}

if [[ $DRY_RUN -eq 1 ]]; then
  # Capture full output to temp file, then preview first 50 lines.
  # Avoids SIGPIPE under `set -o pipefail` when piping `generate | head`.
  TMP=$(mktemp)
  generate > "$TMP"
  head -50 "$TMP"
  echo "..."
  echo "(dry-run; full output would be written to $OUTPUT — $(wc -l < "$TMP") lines)"
  rm -f "$TMP"
else
  # Backup any existing AGENTS.md before overwrite (timestamped, never destroys).
  if [[ -f "$OUTPUT" ]]; then
    BACKUP="$OUTPUT.backup-$(date +%Y%m%d-%H%M%S)"
    cp "$OUTPUT" "$BACKUP"
    echo "Backed up existing $OUTPUT → $BACKUP"
  fi
  generate > "$OUTPUT"
  lines=$(wc -l < "$OUTPUT" | tr -d ' ')
  echo "Wrote $OUTPUT ($lines lines)"
  # The deliverable is one file, not three trees, so the receipt reports what this adapter
  # actually produced rather than echoing zeroes for skills and subagents.
  echo
  echo "Installed for $ADAPTER_LABEL:"
  printf '  %-15s: %s\n' "AGENTS.md" "$OUTPUT ($lines lines)"
  printf '  %-15s: %s\n' "Bundles" "$(bundle_label)"
  echo "Core-only install: bash install.sh --adapter $ADAPTER_LABEL --core-only"
fi
