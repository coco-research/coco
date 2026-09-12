#!/usr/bin/env bash
# Claude Code adapter — wires Coco artifacts into ~/.claude/
#
# Usage:
#   bash adapters/claude-code/install.sh                    # core + every bundle
#   bash adapters/claude-code/install.sh --core-only        # core only, no bundles
#   bash adapters/claude-code/install.sh --systems gsd      # only the GSD bundle
#   bash adapters/claude-code/install.sh --dry-run          # preview only
#
# Bundles default to every bundle that ships skills or agents, derived by
# scripts/installable-bundles.sh so a new bundle needs no edit here. --core-only opts out
# of all of them and wins over --systems; --systems <list> replaces the default set.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_HOME="${CLAUDE_HOME:-$HOME/.claude}"
DRY_RUN=0
SYSTEMS=()
CORE_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --core-only) CORE_ONLY=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "$1" ;;
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
  # finds out. Copies predating this guard have gone months out of date in practice.
  if [[ -e "$dst" && ! -L "$dst" ]]; then
    echo "STALE: $dst is a real file, not a symlink — NOT updated. Remove it to let the installer manage it."
    STALE_COUNT=$((STALE_COUNT + 1))
    return
  fi
  # A dangling symlink is removed and relinked. These accumulate whenever the repo moves.
  [[ -L "$dst" ]] && run rm "$dst"
  run mkdir -p "$(dirname "$dst")"
  run ln -sf "$src" "$dst"
  echo "Linked: $dst -> $src"
}

report_stale() {
  [[ $STALE_COUNT -eq 0 ]] && return 0
  echo
  echo "WARNING: $STALE_COUNT target(s) were real files rather than symlinks and were left"
  echo "untouched. They will keep serving stale content until you remove them. Re-run this"
  echo "installer afterwards to link them."
}

link_skills() {
  for skill in "$REPO_ROOT/skills"/*/; do
    name=$(basename "$skill")
    link_dir "$skill" "$TARGET_HOME/skills/$name"
    SKILL_COUNT=$((SKILL_COUNT + 1))
  done
}

link_commands() {
  # Map commands/<namespace>/<name>.md → ~/.claude/commands/<namespace>:<name>.md
  for ns in "$REPO_ROOT/commands"/*/; do
    nsname=$(basename "$ns")
    for cmd in "$ns"*.md; do
      [[ -f "$cmd" ]] || continue
      cname=$(basename "$cmd" .md)
      if [[ "$cname" == "_index" ]]; then
        link_dir "$cmd" "$TARGET_HOME/commands/$nsname.md"
      else
        link_dir "$cmd" "$TARGET_HOME/commands/$nsname:$cname.md"
      fi
      COMMAND_COUNT=$((COMMAND_COUNT + 1))
    done
  done
}

link_agents() {
  for agent in "$REPO_ROOT/agents"/*.md; do
    name=$(basename "$agent")
    link_dir "$agent" "$TARGET_HOME/agents/$name"
    # INDEX.md and README.md are navigation rather than subagents: still linked, not
    # counted, so the receipt reports subagents instead of files.
    case "$name" in
      INDEX.md|README.md) ;;
      *) AGENT_COUNT=$((AGENT_COUNT + 1)) ;;
    esac
  done
}

# The Super Intelligence family (242 commands) is stamped out of the per-team registries
# rather than shipped as files. scripts/generate-si-commands.sh runs both generators, so
# this adapter cannot drift from the other adapters or half-implement the step.
run_si_generator() {
  local target=$1
  local args=(--target "$target")
  [[ $DRY_RUN -eq 1 ]] && args+=(--dry-run)

  local out
  if ! out=$(bash "$REPO_ROOT/scripts/generate-si-commands.sh" "${args[@]}" 2>&1); then
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
    # Deliberately not assuming 242 here: when the generators did not run the count is
    # unknown, and the receipt says so rather than printing a number nobody verified.
    SI_SKIP=$(printf '%s\n' "$out" | sed -n 's/^Skip SI generation: //p' | head -n 1)
    [[ -n "$SI_SKIP" ]] || SI_SKIP="unknown reason"
  fi
}

link_system() {
  local sys=$1
  local sys_dir="$REPO_ROOT/systems/$sys"
  [[ -d "$sys_dir" ]] || { echo "Unknown system: $sys" >&2; exit 1; }
  if [[ -d "$sys_dir/skills" ]]; then
    for s in "$sys_dir/skills"/*/; do
      name=$(basename "$s")
      link_dir "$s" "$TARGET_HOME/skills/$name"
      SKILL_COUNT=$((SKILL_COUNT + 1))
    done
  fi
  if [[ -d "$sys_dir/agents" ]]; then
    for a in "$sys_dir/agents"/*.md; do
      [[ -f "$a" ]] || continue
      name=$(basename "$a")
      link_dir "$a" "$TARGET_HOME/agents/$name"
      case "$name" in
        INDEX.md|README.md) ;;
        *) AGENT_COUNT=$((AGENT_COUNT + 1)) ;;
      esac
    done
  fi
  if [[ -d "$sys_dir/commands" ]]; then
    for c in "$sys_dir/commands"/*.md; do
      [[ -f "$c" ]] || continue
      name=$(basename "$c")
      link_dir "$c" "$TARGET_HOME/commands/$name"
      COMMAND_COUNT=$((COMMAND_COUNT + 1))
    done
  fi
  if [[ -f "$sys_dir/ai/scripts/build_commands.py" ]]; then
    run_si_generator "$TARGET_HOME/commands"
  fi
}

link_rules() {
  # Append a Coco-managed section to ~/.claude/CLAUDE.md that references rules.
  # Idempotent: removes any prior Coco-managed block before re-inserting.
  local target="$TARGET_HOME/CLAUDE.md"
  local marker_start="<!-- coco:rules-start -->"
  local marker_end="<!-- coco:rules-end -->"

  run mkdir -p "$TARGET_HOME"

  # Build the new block in a temp file
  local block
  block=$(cat <<EOF
$marker_start
<!-- This block is auto-generated by adapters/claude-code/install.sh.
     Edit the source files in $REPO_ROOT/rules/ — re-run install to refresh. -->

# Coco — cross-IDE rules

The following rules apply globally. Source: \`$REPO_ROOT/rules/cursor-mdc/\`

EOF
)
  for mdc in "$REPO_ROOT/rules/cursor-mdc"/*.mdc; do
    [[ -f "$mdc" ]] || continue
    block+=$'\n'"- \`$(basename "$mdc" .mdc)\`"
  done
  block+=$'\n\n'"For each rule, see [\`rules/cursor-mdc/\`]($REPO_ROOT/rules/cursor-mdc/)."
  block+=$'\n\n'"$marker_end"

  if [[ $DRY_RUN -eq 1 ]]; then
    echo "DRY: would write Coco rules block to $target"
    return
  fi

  # If CLAUDE.md exists, strip prior Coco block then append new
  if [[ -f "$target" ]]; then
    awk -v s="$marker_start" -v e="$marker_end" '
      $0 == s { skip=1; next }
      $0 == e { skip=0; next }
      !skip
    ' "$target" > "$target.tmp"
    printf '%s\n' "" "$block" >> "$target.tmp"
    mv "$target.tmp" "$target"
  else
    printf '%s\n' "$block" > "$target"
  fi
  echo "Wrote rules block to $target"
}

print_receipt() {
  [[ $DRY_RUN -eq 1 ]] && return 0
  local bundles="core only"
  [[ ${#BUNDLES_INSTALLED[@]} -gt 0 ]] && bundles="$(IFS=,; echo "${BUNDLES_INSTALLED[*]}")"
  local commands
  if [[ -n "$SI_COUNT" ]]; then
    commands="$((COMMAND_COUNT + SI_COUNT))   ($COMMAND_COUNT core + $SI_COUNT Super Intelligence)"
  elif [[ -n "$SI_SKIP" ]]; then
    commands="$COMMAND_COUNT   (core commands only; SI generation skipped: $SI_SKIP)"
  else
    commands="$COMMAND_COUNT   (core commands only)"
  fi
  echo
  echo "Installed for Claude Code:"
  echo "  Slash commands : $commands"
  echo "  Skills         : $SKILL_COUNT"
  echo "  Subagents      : $AGENT_COUNT"
  echo "  Bundles        : $bundles"
  echo "Core-only install: bash install.sh --adapter claude-code --core-only"
}

echo "Coco · Claude Code adapter"
echo "Source: $REPO_ROOT"
echo "Target: $TARGET_HOME"
[[ $DRY_RUN -eq 1 ]] && echo "(dry-run mode)"

link_skills
link_commands
link_agents
link_rules

for sys in "${SYSTEMS[@]:-}"; do
  [[ -n "$sys" ]] || continue
  BUNDLES_INSTALLED+=("$sys")
  link_system "$sys"
done

report_stale

print_receipt

echo "Done."
