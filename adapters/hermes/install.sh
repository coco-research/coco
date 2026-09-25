#!/usr/bin/env bash
# Hermes adapter — wires Coco artifacts into a Hermes Agent profile.
#
# Hermes profiles keep skills at ~/.hermes/profiles/<profile>/skills/ and a
# Claude-compatible home at ~/.hermes/profiles/<profile>/home/.claude/ for
# agents, commands, and rules. This adapter symlinks Coco artifacts into both.
#
# Usage:
#   bash adapters/hermes/install.sh                          # current profile (HERMES_PROFILE or 'dev')
#   bash adapters/hermes/install.sh --profile dev            # explicit profile
#   bash adapters/hermes/install.sh --all-profiles           # every profile under ~/.hermes/profiles/
#   bash adapters/hermes/install.sh --systems gsd,brain      # add bundles
#   bash adapters/hermes/install.sh --dry-run                # preview only

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILES_ROOT="${HERMES_PROFILES:-$HOME/.hermes/profiles}"
PROFILE="${HERMES_PROFILE:-dev}"
ALL_PROFILES=0
DRY_RUN=0
CORE_ONLY=0
SYSTEMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) shift; PROFILE=$1 ;;
    --all-profiles) ALL_PROFILES=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "$1" ;;
    --core-only) CORE_ONLY=1 ;;
    --dry-run) DRY_RUN=1 ;;
    --help|-h)
      grep '^#' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

# Bundles install by default. This adapter predates that contract and used to install
# the core set alone unless --systems was passed, so a plain run silently delivered 74
# of 188 skills. Naming a subset still wins; --core-only is the opt-out.
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

if [[ $ALL_PROFILES -eq 1 ]]; then
  PROFILES=()
  for d in "$PROFILES_ROOT"/*/; do
    [[ -d "$d" ]] && PROFILES+=("$(basename "$d")")
  done
  if [[ ${#PROFILES[@]} -eq 0 ]]; then
    echo "No profiles found under $PROFILES_ROOT" >&2
    exit 1
  fi
else
  # A missing profile dir is fatal for a real install, but --dry-run must still be able
  # to preview the plan (CI gates run with no real profiles on the machine). In that case
  # proceed with the named profile as a purely notional target.
  # Create the profile on demand. Hermes keeps a profile's skills and its
  # Claude-compatible home underneath the profile directory, and this script
  # already creates those subdirectories, so refusing to create the profile
  # root only meant that a first install failed on any machine where no
  # profile had been made by hand. --all-profiles still refuses an empty root,
  # because there is genuinely nothing to enumerate there.
  if [[ ! -d "$PROFILES_ROOT/$PROFILE" && $DRY_RUN -eq 0 ]]; then
    echo "Profile $PROFILE does not exist under $PROFILES_ROOT; creating it."
    mkdir -p "$PROFILES_ROOT/$PROFILE"
  fi
  PROFILES=("$PROFILE")
fi

run() {
  if [[ $DRY_RUN -eq 1 ]]; then echo "DRY: $*"; else "$@"; fi
}

STALE_COUNT=0

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

install_profile() {
  local profile=$1
  local base="$PROFILES_ROOT/$profile"
  local claude_home="$base/home/.claude"

  echo
  echo "=== Hermes profile: $profile ==="
  echo "skills:  $base/skills"
  echo "claude:  $claude_home"
  [[ $DRY_RUN -eq 1 ]] && echo "(dry-run mode)"

  # Skills live directly in the profile's skills dir, where Hermes discovers them.
  for skill in "$REPO_ROOT"/skills/*/; do
    link_dir "$skill" "$base/skills/$(basename "$skill")"
  done

  # Root-level agents and commands (not part of any system bundle).
  for agent in "$REPO_ROOT"/agents/*.md; do
    [[ -f "$agent" ]] || continue
    link_dir "$agent" "$claude_home/agents/$(basename "$agent")"
  done
  for ns in "$REPO_ROOT"/commands/*/; do
    nsname=$(basename "$ns")
    for cmd in "$ns"*.md; do
      [[ -f "$cmd" ]] || continue
      cname=$(basename "$cmd" .md)
      if [[ "$cname" == "_index" ]]; then
        link_dir "$cmd" "$claude_home/commands/$nsname.md"
      else
        link_dir "$cmd" "$claude_home/commands/$nsname:$cname.md"
      fi
    done
  done

  # Agents, commands, and rules go into the profile's Claude-compatible home,
  # matching the layout Claude Code itself uses.
  link_rules() { :; }  # placeholder; rules handled below per-profile scope

  local marker_start="<!-- coco:rules-start -->"
  local marker_end="<!-- coco:rules-end -->"
  local target="$claude_home/CLAUDE.md"
  run mkdir -p "$claude_home" "$claude_home/commands" "$claude_home/agents"

  local block
  block=$(cat <<EOF
$marker_start
<!-- This block is auto-generated by adapters/hermes/install.sh.
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
  elif [[ -f "$target" ]]; then
    awk -v s="$marker_start" -v e="$marker_end" '
      $0 == s { skip=1; next }
      $0 == e { skip=0; next }
      !skip
    ' "$target" > "$target.tmp"
    printf '%s\n' "" "$block" >> "$target.tmp"
    mv "$target.tmp" "$target"
    echo "Wrote rules block to $target"
  else
    printf '%s\n' "$block" > "$target"
    echo "Wrote rules block to $target"
  fi

  install_system() {
    local sys=$1
    local sys_dir="$REPO_ROOT/systems/$sys"
    [[ -d "$sys_dir" ]] || { echo "Unknown system: $sys" >&2; exit 1; }
    if [[ -d "$sys_dir/skills" ]]; then
      for s in "$sys_dir"/skills/*/; do
        link_dir "$s" "$base/skills/$(basename "$s")"
      done
    fi

    # Team front doors: systems/<bundle>/<team>/SKILL.md. Some bundles keep one front
    # door per team rather than under skills/ — the 13 Super Intelligence teams do — and
    # this walked only skills/, so every one of them was missing from the install. The
    # directory is a short slug (ai, gtm); the frontmatter name is the canonical id
    # (ai-super-intelligence) that the generated index and the role roster use.
    for t in "$sys_dir"/*/; do
      [[ -f "$t/SKILL.md" ]] || continue
      name=$(sed -n 's/^name: *//p' "$t/SKILL.md" | head -1 | tr -d '"')
      [[ -n "$name" ]] || name=$(basename "$t")
      link_dir "$t" "$base/skills/$name"
    done
    if [[ -d "$sys_dir/agents" ]]; then
      for a in "$sys_dir"/agents/*.md; do
        [[ -f "$a" ]] || continue
        link_dir "$a" "$claude_home/agents/$(basename "$a")"
      done
    fi
    if [[ -d "$sys_dir/commands" ]]; then
      for c in "$sys_dir"/commands/*.md; do
        [[ -f "$c" ]] || continue
        link_dir "$c" "$claude_home/commands/$(basename "$c")"
      done
    fi
    # Superintelligence: SI-* commands are generated from per-team registries, not shipped as files.
    if [[ -f "$sys_dir/ai/scripts/build_commands.py" ]] && command -v python3 >/dev/null 2>&1; then
      run env COCO_SI_COMMANDS_DIR="$claude_home/commands" python3 "$sys_dir/ai/scripts/build_commands.py"
      if [[ -f "$sys_dir/scripts/build_meta_commands.py" ]]; then
        run env COCO_SI_COMMANDS_DIR="$claude_home/commands" python3 "$sys_dir/scripts/build_meta_commands.py"
      fi
      echo "Generated SI-* commands into $claude_home/commands"
    fi
  }

  for sys in "${SYSTEMS[@]:-}"; do
    [[ -n "$sys" ]] && install_system "$sys"
  done

  report_stale
}

for p in "${PROFILES[@]}"; do
  install_profile "$p"
done

echo
echo "Done. Restart any running Hermes gateway to pick up new skills."
