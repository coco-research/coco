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
# Refuses to write inside the Coco checkout itself (issue #238); run from your project directory.
#
# Bundles default to every bundle that actually ships something
# (scripts/installable-bundles.sh), not to the core alone: defaulting to core folded
# about a third of the framework into AGENTS.md and said nothing about it. --systems
# overrides the default, --core-only asks for the core set, and --systems wins if both
# are given.

set -euo pipefail
unset CDPATH

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
    --help|-h) bash "$REPO_ROOT/scripts/print-usage.sh" "$0"; exit 0 ;;
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

# The SI-* command family is generated (not committed) into a Coco-owned folder by
# scripts/generate-si-commands.sh; AGENTS.md points at the real files there.
SI_DIR="${COCO_HOME:-$HOME/.coco}/si-commands"
SI_COUNT=""
SI_SKIP=""
SI_NOTE=""

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

# Team front doors: systems/<bundle>/<team>/SKILL.md. Some bundles keep one front
# door per team rather than under skills/ — the 13 Super Intelligence teams do. The
# directory is a short slug (ai, gtm); the frontmatter name is the canonical id
# (ai-super-intelligence) the generated index and role roster use.
emit_team_front_door() {
  local skill=$1
  local name desc
  name=$(sed -n 's/^name: *//p' "$skill" | head -1 | tr -d '"')
  [[ -n "$name" ]] || name=$(basename "$(dirname "$skill")")
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
    for skill in "$dir"/*/SKILL.md; do
      [[ -f "$skill" ]] || continue
      emit_team_front_door "$skill"
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

si_bundle_selected() {
  local sys dir
  for sys in ${SYSTEMS[@]+"${SYSTEMS[@]}"}; do
    dir="$REPO_ROOT/systems/$sys"
    [[ -f "$dir/ai/scripts/build_commands.py" ]] && return 0
  done
  return 1
}

generate_si_commands() {
  if ! si_bundle_selected; then
    SI_SKIP="superintelligence bundle not selected"
    return 0
  fi
  local si_args=(--target "$SI_DIR")
  [[ $DRY_RUN -eq 1 ]] && si_args+=(--dry-run)

  local out
  if ! out=$(bash "$REPO_ROOT/scripts/generate-si-commands.sh" "${si_args[@]}" 2>&1); then
    echo "WARNING: scripts/generate-si-commands.sh failed; the SI-* command family is" >&2
    echo "missing from this install. Generator output (last 5 lines):" >&2
    printf '%s\n' "$out" | tail -n 5 >&2
    rmdir "$SI_DIR" 2>/dev/null || true
    SI_SKIP="generator failed"
    return 0
  fi
  echo "$out"
  [[ $DRY_RUN -eq 1 ]] && return 0

  SI_COUNT=$(printf '%s\n' "$out" | sed -n 's/^Generated \([0-9][0-9]*\) SI commands.*/\1/p' | tail -n 1)
  if [[ -z "$SI_COUNT" || "$SI_COUNT" == "0" ]]; then
    SI_SKIP=$(printf '%s\n' "$out" | sed -n 's/^Skip SI generation: //p' | head -n 1)
    [[ -n "$SI_SKIP" ]] || SI_SKIP="generator produced no commands"
    SI_COUNT=""
  fi
}

emit_si_commands() {
  if ! si_bundle_selected; then
    echo "Not generated: superintelligence bundle not selected"
    return 0
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "Not generated: dry run"
    return 0
  fi

  local f files=()
  for f in "$SI_DIR"/SI.md "$SI_DIR"/SI-*.md; do
    [[ -f "$f" ]] || continue
    files+=("$f")
  done

  if [[ ${#files[@]} -eq 0 ]]; then
    echo "Not generated: ${SI_SKIP:-unknown reason}"
    return 0
  fi

  echo "These \`/SI-*\` commands are generated locally from the Super Intelligence team registries."
  echo "The full workflow for each command is the file \`$SI_DIR/<command>.md\`."
  echo "When the user types \`/SI-Decide <prompt>\`, read that file and follow it, treating the text after the command as ARGUMENTS."
  echo ""
  while IFS= read -r f; do
    local first cmd desc
    first=$(head -n 1 "$f" 2>/dev/null || true)
    cmd="/$(basename "$f" .md)"
    case "$first" in
      '# /SI'*) cmd="${first#\# }"; cmd="${cmd%% *}" ;;
    esac
    desc=""
    case "$first" in
      *" — "*) desc="${first#* — }" ;;
    esac
    if [[ -n "$desc" ]]; then
      echo "- \`$cmd\` — $desc"
    else
      echo "- \`$cmd\`"
    fi
  done < <(printf '%s\n' "${files[@]}" | LC_ALL=C sort)
}

generate() {
  echo "# AGENTS.md"
  echo ""
  echo "Generated by Coco · adapters/codex/install.sh"
  echo "Source: $REPO_ROOT"
  echo "Systems: $(bundle_label)$SI_NOTE"
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
  echo "## Super Intelligence Commands"
  echo ""
  emit_si_commands
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

# Issue #238: writing AGENTS.md inside the Coco checkout clobbers the repo's own
# tracked AGENTS.md, so refuse (except in --dry-run, which only warns). Resolve both
# sides physically so a symlinked path (e.g. /tmp -> /private/tmp) still compares equal.
output_dir=""
if [[ -n "$OUTPUT" ]]; then
  if [[ -d "$OUTPUT" ]]; then
    # -o may name a directory; check that directory itself, not its parent.
    output_dir="$(cd "$OUTPUT" 2>/dev/null && pwd -P)" || output_dir=""
  else
    output_dir="$(cd "$(dirname -- "$OUTPUT")" 2>/dev/null && pwd -P)" || output_dir=""
  fi
fi
repo_root_phys="$(cd "$REPO_ROOT" && pwd -P)"
if [[ "$output_dir" == "$repo_root_phys" || "$output_dir" == "$repo_root_phys"/* ]]; then
  if [[ $DRY_RUN -eq 1 ]]; then
    echo "NOTE: a real run would refuse: $output_dir/$(basename -- "$OUTPUT") is inside the Coco checkout ($repo_root_phys); run from your project directory or pass -o <path outside the checkout>."
  else
    if [[ "${COCO_AUTODETECTED:-}" == 1 ]]; then
      refusal_reason="no AI tool was detected, so install.sh fell back to the generic adapter, whose AGENTS.md target resolved inside the Coco checkout itself."
    else
      refusal_reason="the AGENTS.md target is inside the Coco checkout itself."
    fi
    {
      echo "ERROR: refusing to write: $refusal_reason"
      echo "  target:   $output_dir/$(basename -- "$OUTPUT")"
      echo "  checkout: $repo_root_phys"
      echo "Coco will not overwrite the repository's own AGENTS.md."
      echo "To proceed:"
      echo "  (a) run from your project directory: cd /path/to/your/project && bash $REPO_ROOT/install.sh"
      echo "  (b) or write to an explicit path: bash $REPO_ROOT/adapters/$ADAPTER_LABEL/install.sh -o /path/to/your/project/AGENTS.md"
      echo "  (c) or pick your tool's adapter: bash $REPO_ROOT/install.sh --list, then --adapter <name>"
    } >&2
    exit 2
  fi
fi

# Generate SI commands only after the #238 guard passed: an in-checkout run must write nothing.
generate_si_commands
if [[ $DRY_RUN -eq 0 && -z "$SI_COUNT" ]] && si_bundle_selected; then
  SI_NOTE=" (superintelligence: SI commands not generated: ${SI_SKIP:-unknown reason})"
fi

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
  skills_listed=$(awk '/^## Skills$/{f=1;next} /^## /{f=0} f && /^- \*\*/{n++} END{print n+0}' "$OUTPUT")
  if [[ -n "$SI_COUNT" ]]; then
    si_receipt="$SI_COUNT in $SI_DIR"
  else
    si_receipt="0 (not generated: ${SI_SKIP:-unknown reason})"
  fi
  echo "Wrote $OUTPUT ($lines lines)"
  # The deliverable is one file, not three trees, so the receipt reports what this adapter
  # actually produced rather than echoing zeroes for skills and subagents.
  echo
  echo "Installed for $ADAPTER_LABEL:"
  printf '  %-15s: %s\n' "AGENTS.md" "$OUTPUT ($lines lines)"
  printf '  %-15s: %s\n' "Bundles" "$(bundle_label)$SI_NOTE"
  printf '  %-15s: %s\n' "Skills listed" "$skills_listed"
  printf '  %-15s: %s\n' "SI commands" "$si_receipt"
  echo "Core-only install: bash install.sh --adapter $ADAPTER_LABEL --core-only"
fi
