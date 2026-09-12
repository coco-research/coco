#!/usr/bin/env bash
# Cursor adapter — wires Coco artifacts into ~/.cursor/
#
# Usage:
#   bash adapters/cursor/install.sh                       # all bundles (the default)
#   bash adapters/cursor/install.sh --systems gsd,brain   # only these bundles
#   bash adapters/cursor/install.sh --core-only           # no bundles
#   bash adapters/cursor/install.sh --dry-run             # preview only
#
# Where things land:
#   skills/<name>/                   -> ~/.cursor/skills/<name>                      (symlink)
#   systems/<bundle>/skills/<name>/  -> ~/.cursor/skills/<name>                      (symlink)
#   adapters/cursor/skills/<name>/   -> ~/.cursor/skills/<name>                      (symlink)
#   rules/cursor-mdc/*.mdc           -> ~/.cursor/rules/<name>.mdc                   (symlink)
#   commands/<ns>/<name>.md          -> ~/.cursor/commands/<ns>:<name>.md            (symlink)
#   the SI-* command family          -> ~/.cursor/commands/SI-*.md                   (generated)
#
# Bundles default to every bundle that actually ships something
# (scripts/installable-bundles.sh) rather than to the core alone: defaulting to core
# delivered about a third of the framework and said nothing about it. --systems
# overrides the default, --core-only installs no bundles, and --systems wins if both
# are given.
#
# The Super Intelligence command family (242 commands) is generated at install time
# from the team registries, not committed. An install that skips that step delivers 38
# commands where the published total is 280.
#
# Cursor has no subagent concept in this adapter — no agent target, no discovery path —
# so systems/<bundle>/agents/*.md is deliberately not installed, and this script says so
# rather than silently dropping (for example) the 24 GSD agents.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_HOME="${CURSOR_HOME:-$HOME/.cursor}"
DRY_RUN=0
CORE_ONLY=0
SYSTEMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "${1:-}" ;;
    --core-only) CORE_ONLY=1 ;;
    # Header only: --help used to grep every '^#' line, which would also print the
    # explanatory comments inside the code as if they were usage.
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

run() {
  if [[ $DRY_RUN -eq 1 ]]; then echo "DRY: $*"; else "$@"; fi
}

STALE_COUNT=0

link_dir() {
  local src=$1 dst=$2
  # A real file or directory at the target is NOT overwritten, because it may be the
  # user's own work. But it is reported loudly and counted, because a silent skip here
  # means the target keeps serving a stale copy through every future re-install and
  # nobody finds out. Copies predating this adapter have gone months out of date.
  if [[ -e "$dst" && ! -L "$dst" ]]; then
    echo "STALE: $dst is a real file, not a symlink — NOT updated. Remove it to let this adapter manage it."
    STALE_COUNT=$((STALE_COUNT + 1))
    return
  fi
  # A dangling symlink is removed and relinked. These accumulate whenever the repo moves.
  [[ -L "$dst" ]] && run rm "$dst"
  run mkdir -p "$(dirname "$dst")"
  run ln -sf "$src" "$dst"
  echo "Linked: $dst -> $src"
}

# Counts are reported through globals rather than stdout, because the helpers also log
# their work and a command substitution would swallow that log into the number.
LINKED=0

link_skills_from() {
  local dir=$1 skill
  LINKED=0
  [[ -d "$dir" ]] || return 0
  for skill in "$dir"/*/; do
    [[ -f "$skill/SKILL.md" ]] || continue
    link_dir "$skill" "$TARGET_HOME/skills/$(basename "$skill")"
    LINKED=$((LINKED + 1))
  done
}

# Generated, not committed: scripts/generate-si-commands.sh runs both generators into the
# commands directory in one step, so a change to the registries cannot be applied to some
# adapters and forgotten here. Generation failure is non-fatal — the core commands are
# already linked and still work.
generate_si_commands() {
  local script="$REPO_ROOT/scripts/generate-si-commands.sh"
  [[ -f "$script" ]] || { echo "Skip SI generation: $script not found."; return 0; }

  local args=(--target "$TARGET_HOME/commands")
  [[ $DRY_RUN -eq 1 ]] && args+=(--dry-run)
  bash "$script" "${args[@]}" || {
    echo "WARNING: SI command generation failed; continuing with the core commands." >&2
    return 0
  }

  si_count=0
  if [[ $DRY_RUN -eq 0 ]]; then
    local f
    for f in "$TARGET_HOME/commands"/SI*.md; do
      [[ -f "$f" ]] || continue
      si_count=$((si_count + 1))
    done
    echo "System superintelligence: $si_count generated SI command(s) in $TARGET_HOME/commands"
  else
    echo "System superintelligence: SI command family would be generated into $TARGET_HOME/commands"
  fi
}

link_system() {
  local sys=$1
  local sys_dir="$REPO_ROOT/systems/$sys"
  [[ -d "$sys_dir" ]] || { echo "Unknown system: $sys" >&2; exit 1; }

  local did=0
  if [[ -d "$sys_dir/skills" ]]; then
    link_skills_from "$sys_dir/skills"
    skill_count=$((skill_count + LINKED))
    echo "System $sys: $LINKED skill(s) linked"
    did=1
  fi
  if [[ -d "$sys_dir/agents" ]]; then
    # Reported rather than installed: inventing an agent target here would write into a
    # path Cursor does not read, which looks installed and does nothing.
    echo "System $sys: agents skipped (Cursor has no subagent target in this adapter)"
    did=1
  fi
  # Tree-derived, like the VS Code adapter, so a renamed or relocated generator shows up
  # as "nothing to install" instead of a silently missing command family.
  if [[ -f "$sys_dir/ai/scripts/build_commands.py" ]]; then
    generate_si_commands
    did=1
  fi
  [[ $did -eq 1 ]] || echo "System $sys: nothing to install"
}

# Remove command symlinks this adapter should not leave in place. Two kinds accumulate:
#
#   1. Links pointing outside the current repository. Moving or renaming the repo leaves
#      these dangling, and nothing else ever revisits them.
#   2. Links to a directory. An older layout symlinked whole namespace directories
#      (commands/team -> <repo>/commands/team). Those resolve fine but sit one level too
#      deep for Cursor to discover, so they look installed while doing nothing. This
#      adapter only ever creates links to individual files.
prune_unusable_command_links() {
  local dir="$TARGET_HOME/commands"
  [[ -d "$dir" ]] || return 0
  local entry target
  for entry in "$dir"/*; do
    [[ -L "$entry" ]] || continue
    target=$(readlink "$entry")
    if [[ -d "$entry" ]]; then
      echo "Pruned directory link (too deep for Cursor to discover): $entry -> $target"
      run rm "$entry"
      continue
    fi
    case "$target" in
      "$REPO_ROOT"/*) continue ;;
    esac
    echo "Pruned foreign link: $entry -> $target"
    run rm "$entry"
  done
}

skill_count=0
cmd_count=0
si_count=0

if [[ ${#SYSTEMS[@]} -eq 0 ]]; then
  bundle_label="core only"
else
  bundle_label="$( IFS=,; printf '%s' "${SYSTEMS[*]}" )"
fi

echo "Coco · Cursor adapter"
echo "Source: $REPO_ROOT"
echo "Target: $TARGET_HOME"
echo "Bundles: $bundle_label"
[[ $DRY_RUN -eq 1 ]] && echo "(dry-run mode)"

# Skills
for skill in "$REPO_ROOT/skills"/*/; do
  [[ -d "$skill" ]] || continue
  name=$(basename "$skill")
  link_dir "$skill" "$TARGET_HOME/skills/$name"
  skill_count=$((skill_count + 1))
done

# Rules — symlink .mdc files (idempotent; replaces any prior symlink pointing
# back to this repo).  Earlier versions used `cp`, which made re-runs
# non-idempotent and orphaned old copies on Coco updates.
run mkdir -p "$TARGET_HOME/rules"
for mdc in "$REPO_ROOT/rules/cursor-mdc"/*.mdc; do
  name=$(basename "$mdc")
  link_dir "$mdc" "$TARGET_HOME/rules/$name"
done

# Cursor-specific helper skills
for skill in "$REPO_ROOT/adapters/cursor/skills"/*/; do
  [[ -d "$skill" ]] || continue
  name=$(basename "$skill")
  link_dir "$skill" "$TARGET_HOME/skills/$name"
  skill_count=$((skill_count + 1))
done

# Commands — flat files named <namespace>:<command>.md, matching the pattern Cursor reads
# for user-level commands (`~/.cursor/commands/*.md`). Cursor does not recurse into
# subdirectories here, so a directory symlink such as commands/team -> repo/commands/team
# puts every file one level too deep to be discovered. Earlier versions of this adapter
# installed no commands at all, which is why such links survived unnoticed.
prune_unusable_command_links
run mkdir -p "$TARGET_HOME/commands"
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
    cmd_count=$((cmd_count + 1))
  done
done
echo "Commands: $cmd_count linked into $TARGET_HOME/commands"

# Bundles. The SI generator lives inside the superintelligence bundle and is only run when
# that bundle is selected, which is what makes --core-only a real 38-command install.
for sys in "${SYSTEMS[@]:-}"; do
  [[ -n "$sys" ]] && link_system "$sys"
done

# A previous full install left generated SI-* files behind, and no bundle in this run owns
# them. They are reported, not deleted: this adapter removes what it created, never files a
# user may only have here, and a receipt that says 38 beside a directory holding 280 needs
# the difference named.
if [[ $DRY_RUN -eq 0 && $si_count -eq 0 ]]; then
  leftovers=0
  for f in "$TARGET_HOME/commands"/SI*.md; do
    [[ -f "$f" ]] || continue
    leftovers=$((leftovers + 1))
  done
  if [[ $leftovers -gt 0 ]]; then
    echo
    echo "Note: $leftovers generated SI command(s) from an earlier install are still in"
    echo "$TARGET_HOME/commands. They belong to the superintelligence bundle; re-run with"
    echo "--systems superintelligence to refresh them, or delete them to go core-only."
  fi
fi

if [[ $STALE_COUNT -gt 0 ]]; then
  echo
  echo "WARNING: $STALE_COUNT target(s) were real files rather than symlinks and were left"
  echo "untouched. They will keep serving stale content until you remove them. Re-run this"
  echo "installer afterwards to link them."
fi

if [[ $DRY_RUN -eq 1 ]]; then
  echo "Done. Nothing was written (dry run); re-run without --dry-run to install."
  exit 0
fi

# The receipt is the last thing printed, and every number in it is derived from what this
# run actually installed rather than from a table here.
echo
echo "Installed for cursor:"
printf '  %-15s: %s\n' "Slash commands" "$((cmd_count + si_count))"
printf '  %-15s: %s\n' "Skills" "$skill_count"
printf '  %-15s: %s\n' "Subagents" "0"
printf '  %-15s: %s\n' "Bundles" "$bundle_label"
echo "Core-only install: bash install.sh --adapter cursor --core-only"
