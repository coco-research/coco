#!/usr/bin/env bash
# Issue #250: re-running the codex/generic adapter with unchanged content left a new
# AGENTS.md.backup-<timestamp> behind every time, so backups piled up. A re-run that
# produces the same bytes must write nothing; a real change still gets exactly one backup.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

ok() { echo "ok: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

# Keep the host's own adapter homes out of the runs; HOME is the only path input.
run_install() { # <adapter> <project dir> <home dir> <log>
  (cd "$2" && env -u CLAUDE_HOME -u CURSOR_HOME -u COCO_HOME -u XDG_CONFIG_HOME \
    HOME="$3" bash "$ROOT/adapters/$1/install.sh" >"$4" 2>&1)
}

backups_in() { # <project dir> -> the AGENTS.md.backup-* paths, one per line
  shopt -s nullglob
  local found=("$1"/AGENTS.md.backup-*)
  shopt -u nullglob
  [[ ${#found[@]} -eq 0 ]] || printf '%s\n' "${found[@]}"
}

count_backups() { # <project dir>
  local n
  n=$(backups_in "$1" | wc -l | tr -d ' ')
  echo "$n"
}

for adapter in codex generic; do
  proj="$tmp/$adapter/project"
  home="$tmp/$adapter/home"
  mkdir -p "$proj" "$home"

  # --- first install: file written, nothing to back up ---------------------
  run_install "$adapter" "$proj" "$home" "$tmp/$adapter-1.log"
  [[ -f "$proj/AGENTS.md" ]] || fail "$adapter: first install wrote no AGENTS.md"
  [[ $(count_backups "$proj") -eq 0 ]] \
    || fail "$adapter: first install created a backup in a fresh project"
  ok "$adapter: first install writes AGENTS.md with no backup"

  # --- identical re-run: no write, no backup ------------------------------
  cp "$proj/AGENTS.md" "$tmp/$adapter-first.md"
  run_install "$adapter" "$proj" "$home" "$tmp/$adapter-2.log"
  [[ -f "$proj/AGENTS.md" ]] || fail "$adapter: identical re-run removed AGENTS.md"
  cmp -s "$proj/AGENTS.md" "$tmp/$adapter-first.md" \
    || fail "$adapter: identical re-run changed AGENTS.md"
  grep -qx 'AGENTS.md unchanged' "$tmp/$adapter-2.log" \
    || fail "$adapter: identical re-run did not print 'AGENTS.md unchanged'"
  [[ $(count_backups "$proj") -eq 0 ]] \
    || fail "$adapter: identical re-run left $(count_backups "$proj") backup(s)"
  ok "$adapter: identical re-run leaves AGENTS.md alone and makes no backup"

  # --- changed content: exactly one timestamped backup --------------------
  printf '%s\n' 'local edit for issue #250' >> "$proj/AGENTS.md"
  run_install "$adapter" "$proj" "$home" "$tmp/$adapter-3.log"
  n=$(count_backups "$proj")
  [[ "$n" -eq 1 ]] || fail "$adapter: changed re-run left $n backups, expected exactly 1"
  backup=$(backups_in "$proj")
  if cmp -s "$backup" "$tmp/$adapter-first.md"; then
    fail "$adapter: backup holds the regenerated file, not the edited one"
  fi
  grep -q 'local edit for issue #250' "$backup" \
    || fail "$adapter: backup is not the edited AGENTS.md"
  cmp -s "$proj/AGENTS.md" "$tmp/$adapter-first.md" \
    || fail "$adapter: changed re-run did not write the regenerated AGENTS.md"
  ok "$adapter: changed re-run makes exactly one backup of the edited file"
done

echo "PASS: re-running codex/generic does not pile up AGENTS.md backups"
