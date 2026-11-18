#!/usr/bin/env bash
# Link Coco skills into ~/.agents/skills/ with a marker file, never replacing
# a user directory or foreign symlink. Compatible with bash 3.2 and bash 5.
# ponytail: ceiling = flat symlink set + marker file in ~/.agents/skills; upgrade path = per-harness skill filter manifest if SKILL.md schemas diverge.

set -euo pipefail
unset CDPATH

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
AGENTS_SKILLS_DIR="${AGENTS_SKILLS_DIR:-${AGENTS_HOME:-$HOME/.agents}/skills}"
MARKER_FILE="$AGENTS_SKILLS_DIR/.coco-agents-skills"

TMP_MARKER=""
TMP_LINK_DIR=""
cleanup_tmp() {
  [[ -n "${TMP_LINK_DIR:-}" ]] && rm -rf "$TMP_LINK_DIR"
  [[ -n "${TMP_MARKER:-}" ]] && rm -f "$TMP_MARKER"
  return 0
}
trap cleanup_tmp EXIT
trap 'cleanup_tmp; exit 130' INT
trap 'cleanup_tmp; exit 143' TERM

DRY_RUN=0
JSON_MODE=0
CORE_ONLY=0
UNINSTALL=0
SYSTEMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --json) JSON_MODE=1 ;;
    --core-only) CORE_ONLY=1 ;;
    --uninstall) UNINSTALL=1 ;;
    --systems) shift; IFS=',' read -ra SYSTEMS <<< "${1:-}" ;;
    *) echo "Unknown flag for link-agents-skills.sh: $1" >&2; exit 1 ;;
  esac
  shift
done

note() {
  if [[ "$JSON_MODE" -eq 1 ]]; then
    printf '%s\n' "$*" >&2
  else
    printf '%s\n' "$*"
  fi
}

frontmatter_name() {
  local file=$1 line trimmed in_fm=0 value first=1
  [[ -f "$file" ]] || return 0
  while IFS= read -r line || [[ -n "${line:-}" ]]; do
    line=${line%$'\r'}
    trimmed=${line%"${line##*[![:blank:]]}"}
    if [[ "$first" -eq 1 ]]; then
      first=0
      [[ "$trimmed" == "---" ]] || return 0
    fi
    if [[ "$trimmed" == "---" ]]; then
      if [[ "$in_fm" -eq 1 ]]; then
        return 0
      fi
      in_fm=1
      continue
    fi
    [[ "$in_fm" -eq 1 ]] || continue
    [[ "$line" == name:* ]] || continue
    value=${line#name:}
    value=${value#"${value%%[![:space:]]*}"}
    value=${value%"${value##*[![:blank:]]}"}
    case "$value" in
      \"*\") value=${value#\"}; value=${value%\"} ;;
      \'*\') value=${value#\'}; value=${value%\'} ;;
    esac
    if [[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] && [[ "$value" != *..* ]]; then
      printf '%s\n' "$value"
    fi
    return 0
  done <"$file"
}

PREV_MANAGED=$'\n'
PREV_REPO=""
if [[ -f "$MARKER_FILE" && ! -L "$MARKER_FILE" ]]; then
  while IFS= read -r mline || [[ -n "${mline:-}" ]]; do
    mline=${mline%$'\r'}
    if [[ "$mline" == "# repo: "* ]]; then
      PREV_REPO="${mline#\# repo: }"
      continue
    fi
    [[ -z "$mline" || "$mline" == \#* ]] && continue
    PREV_MANAGED+="${mline}"$'\n'
  done <"$MARKER_FILE"
fi

is_coco_link() {
  local name=$1 dst=$2 target
  [[ -L "$dst" ]] || return 1
  target=$(readlink "$dst")
  case "${target%/}" in
    "$REPO_ROOT"/*) return 0 ;;
  esac
  if [[ -n "$PREV_REPO" && "$PREV_MANAGED" == *$'\n'"$name"$'\n'* ]]; then
    case "${target%/}" in
      "${PREV_REPO%/}"/*) return 0 ;;
    esac
  fi
  return 1
}

if [[ "$UNINSTALL" -eq 1 ]]; then
  removed=0
  if [[ -d "$AGENTS_SKILLS_DIR" ]]; then
    for entry in "$AGENTS_SKILLS_DIR"/*; do
      [[ -L "$entry" ]] || continue
      ename=$(basename "$entry")
      if is_coco_link "$ename" "$entry"; then
        if [[ "$DRY_RUN" -eq 1 ]]; then
          note "DRY: rm $entry"
        else
          rm "$entry"
        fi
        removed=$((removed + 1))
      fi
    done
    if [[ -f "$MARKER_FILE" && ! -L "$MARKER_FILE" ]]; then
      if [[ "$DRY_RUN" -eq 1 ]]; then
        note "DRY: rm $MARKER_FILE"
      else
        rm -f "$MARKER_FILE"
      fi
    fi
  fi
  note "~/.agents/skills: removed $removed Coco link(s)"
  exit 0
fi

if [[ ${#SYSTEMS[@]} -eq 0 && "$CORE_ONLY" -eq 0 ]]; then
  default_bundles="$(bash "$REPO_ROOT/scripts/installable-bundles.sh" 2>/dev/null || true)"
  if [[ -n "$default_bundles" ]]; then
    IFS=',' read -ra SYSTEMS <<< "$default_bundles"
  fi
fi

if [[ "$CORE_ONLY" -eq 1 && ${#SYSTEMS[@]} -gt 0 ]]; then
  SYSTEMS=()
fi

SEEN_KEYS=$'\n'
NEW_MANAGED=$'\n'
LINKED_COUNT=0
SKIPPED_COUNT=0

if [[ "$DRY_RUN" -eq 0 ]]; then
  mkdir -p "$AGENTS_SKILLS_DIR"
fi

atomic_symlink() {
  local src=$1 dst=$2
  TMP_LINK_DIR=$(mktemp -d "$AGENTS_SKILLS_DIR/.coco-link.XXXXXX")
  ln -s "$src" "$TMP_LINK_DIR/link"
  mv -fh "$TMP_LINK_DIR/link" "$dst" 2>/dev/null \
    || mv -Tf "$TMP_LINK_DIR/link" "$dst" 2>/dev/null \
    || python3 -c 'import os, sys; os.replace(sys.argv[1], sys.argv[2])' "$TMP_LINK_DIR/link" "$dst"
  rmdir "$TMP_LINK_DIR"
  TMP_LINK_DIR=""
}

link_candidate() {
  local name=$1 src=${2%/} key dst existing
  key=$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]')
  if [[ "$SEEN_KEYS" == *$'\n'"$key"$'\n'* ]]; then
    note "skip $name: name taken"
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    return 0
  fi

  dst="$AGENTS_SKILLS_DIR/$name"
  if [[ -e "$dst" && ! -L "$dst" ]]; then
    note "skip $name: user folder kept"
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    return 0
  fi

  if [[ -L "$dst" ]]; then
    if ! is_coco_link "$name" "$dst"; then
      note "skip $name: user link kept"
      SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
      return 0
    fi
    existing=$(readlink "$dst")
    if [[ "${existing%/}" != "$src" ]]; then
      if [[ "$DRY_RUN" -eq 1 ]]; then
        note "DRY: ln -s $src $dst"
      else
        atomic_symlink "$src" "$dst"
      fi
    fi
  else
    if [[ "$DRY_RUN" -eq 1 ]]; then
      note "DRY: ln -s $src $dst"
    elif ! ln -s "$src" "$dst" 2>/dev/null; then
      if [[ -e "$dst" && ! -L "$dst" ]]; then
        note "skip $name: user folder kept"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return 0
      elif ! is_coco_link "$name" "$dst"; then
        note "skip $name: user link kept"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return 0
      fi
      existing=$(readlink "$dst")
      [[ "${existing%/}" == "$src" ]] || atomic_symlink "$src" "$dst"
    fi
  fi

  SEEN_KEYS+="${key}"$'\n'
  NEW_MANAGED+="${name}"$'\n'
  LINKED_COUNT=$((LINKED_COUNT + 1))
}

# 1. Core skills (skills/<name>/SKILL.md)
for skill_dir in "$REPO_ROOT/skills"/*/; do
  [[ -f "$skill_dir/SKILL.md" ]] || continue
  link_candidate "$(basename "$skill_dir")" "$skill_dir"
done

# 2. Bundle skills and team front doors
if [[ ${#SYSTEMS[@]} -gt 0 ]]; then
  for sys in "${SYSTEMS[@]}"; do
    [[ -n "$sys" ]] || continue
    sys_dir="$REPO_ROOT/systems/$sys"
    if [[ ! -d "$sys_dir" ]]; then
      echo "Unknown system: $sys" >&2
      exit 1
    fi
    if [[ -d "$sys_dir/skills" ]]; then
      for sdir in "$sys_dir/skills"/*/; do
        [[ -d "$sdir" ]] || continue
        if [[ -f "$sdir/SKILL.md" ]]; then
          link_candidate "$(basename "$sdir")" "$sdir"
        else
          for nested in "$sdir"/*/; do
            [[ -f "$nested/SKILL.md" ]] || continue
            link_candidate "$(basename "$nested")" "$nested"
          done
        fi
      done
    fi
    for tdir in "$sys_dir"/*/; do
      [[ -f "$tdir/SKILL.md" ]] || continue
      tname=$(frontmatter_name "$tdir/SKILL.md")
      [[ -n "$tname" ]] || tname=$(basename "$tdir")
      link_candidate "$tname" "$tdir"
    done
  done
fi

# 3. Prune stale Coco-managed symlinks from an earlier wider run (never real folders or foreign symlinks)
while IFS= read -r old_name; do
  [[ -n "$old_name" ]] || continue
  if [[ ! "$old_name" =~ ^[A-Za-z0-9._-]+$ || "$old_name" == "." || "$old_name" == ".." || "$old_name" == ".coco-agents-skills" ]]; then
    continue
  fi
  if [[ "$NEW_MANAGED" != *$'\n'"$old_name"$'\n'* ]]; then
    old_dst="$AGENTS_SKILLS_DIR/$old_name"
    if is_coco_link "$old_name" "$old_dst"; then
      if [[ "$DRY_RUN" -eq 1 ]]; then
        note "DRY: rm $old_dst"
      else
        rm "$old_dst"
      fi
    fi
  fi
done <<<"$PREV_MANAGED"

# 4. Write marker file only when bytes change so re-runs are a byte-identical no-op
if [[ "$DRY_RUN" -eq 0 ]]; then
  TMP_MARKER=$(mktemp "$AGENTS_SKILLS_DIR/.coco-agents-skills.XXXXXX")
  {
    printf '# managed-by: coco\n'
    printf '# repo: %s\n' "$REPO_ROOT"
    printf '%s' "$NEW_MANAGED" | sed '/^$/d' | LC_ALL=C sort -u
  } >"$TMP_MARKER"
  if [[ -f "$MARKER_FILE" && ! -L "$MARKER_FILE" ]] && cmp -s "$TMP_MARKER" "$MARKER_FILE"; then
    rm -f "$TMP_MARKER"
  else
    mv -f "$TMP_MARKER" "$MARKER_FILE"
  fi
  TMP_MARKER=""
fi

note "~/.agents/skills: $LINKED_COUNT linked · $SKIPPED_COUNT skipped"
