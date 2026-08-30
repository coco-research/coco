#!/usr/bin/env bash
# Cursor adapter — wires Coco artifacts into ~/.cursor/
#
# Usage:
#   bash adapters/cursor/install.sh
#   bash adapters/cursor/install.sh --dry-run
#   bash adapters/cursor/install.sh --systems superintelligence
#   bash adapters/cursor/install.sh --systems gsd,brain,superintelligence

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_HOME="${CURSOR_HOME:-$HOME/.cursor}"
DRY_RUN=0
SYSTEMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "${1:-}" ;;
    --help|-h) grep '^#' "$0" | sed 's/^# \?//'; exit 0 ;;
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

link_system() {
  local sys=$1
  local sys_dir="$REPO_ROOT/systems/$sys"
  [[ -d "$sys_dir" ]] || { echo "Unknown system: $sys" >&2; exit 1; }
  if [[ -d "$sys_dir/skills" ]]; then
    for s in "$sys_dir/skills"/*/; do
      name=$(basename "$s")
      link_dir "$s" "$TARGET_HOME/skills/$name"
    done
  fi
  if [[ -d "$sys_dir/commands" ]]; then
    for c in "$sys_dir/commands"/*.md; do
      [[ -f "$c" ]] || continue
      name=$(basename "$c")
      link_dir "$c" "$TARGET_HOME/commands/$name"
    done
  fi
  # Superintelligence: SI-* commands are generated from per-team registries, not shipped as files.
  # Written into $TARGET_HOME/commands (CURSOR_HOME, default ~/.cursor/commands) — the same
  # family claude-code writes to ~/.claude/commands. Do not route Cursor users through the
  # claude-code adapter to get these files.
  if [[ -f "$sys_dir/ai/scripts/build_commands.py" ]]; then
    run mkdir -p "$TARGET_HOME/commands"
    if [[ $DRY_RUN -eq 1 ]]; then
      echo "DRY: env COCO_SI_COMMANDS_DIR=$TARGET_HOME/commands python3 $sys_dir/ai/scripts/build_commands.py"
      if [[ -f "$sys_dir/scripts/build_meta_commands.py" ]]; then
        echo "DRY: env COCO_SI_COMMANDS_DIR=$TARGET_HOME/commands python3 $sys_dir/scripts/build_meta_commands.py"
      fi
      echo "DRY: would generate SI-* commands into $TARGET_HOME/commands"
    elif command -v python3 >/dev/null 2>&1; then
      env COCO_SI_COMMANDS_DIR="$TARGET_HOME/commands" python3 "$sys_dir/ai/scripts/build_commands.py"
      if [[ -f "$sys_dir/scripts/build_meta_commands.py" ]]; then
        env COCO_SI_COMMANDS_DIR="$TARGET_HOME/commands" python3 "$sys_dir/scripts/build_meta_commands.py"
      fi
      echo "Generated SI-* commands (per-team + meta-orchestrator) into $TARGET_HOME/commands"
    else
      echo "python3 not found; cannot generate SI-* commands into $TARGET_HOME/commands" >&2
      exit 1
    fi
  fi
}

echo "Coco · Cursor adapter"
echo "Source: $REPO_ROOT"
echo "Target: $TARGET_HOME"
[[ $DRY_RUN -eq 1 ]] && echo "(dry-run mode)"

# Skills
for skill in "$REPO_ROOT/skills"/*/; do
  name=$(basename "$skill")
  link_dir "$skill" "$TARGET_HOME/skills/$name"
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
  name=$(basename "$skill")
  link_dir "$skill" "$TARGET_HOME/skills/$name"
done

# Commands — flat files named <namespace>:<command>.md, matching the pattern Cursor reads
# for user-level commands (`~/.cursor/commands/*.md`). Cursor does not recurse into
# subdirectories here, so a directory symlink such as commands/team -> repo/commands/team
# puts every file one level too deep to be discovered. Earlier versions of this adapter
# installed no commands at all, which is why such links survived unnoticed.
prune_unusable_command_links
run mkdir -p "$TARGET_HOME/commands"
cmd_count=0
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

for sys in "${SYSTEMS[@]:-}"; do
  [[ -n "$sys" ]] && link_system "$sys"
done

if [[ $STALE_COUNT -gt 0 ]]; then
  echo
  echo "WARNING: $STALE_COUNT target(s) were real files rather than symlinks and were left"
  echo "untouched. They will keep serving stale content until you remove them. Re-run this"
  echo "installer afterwards to link them."
fi

echo "Done."
