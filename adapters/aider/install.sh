#!/usr/bin/env bash
# Aider CLI adapter — generates AGENTS.md and .aider.conf.yml in project root
#
# AGENTS.md is compiled by adapters/codex/install.sh (skills, commands, Super Intelligence
# commands, agents and rules) with the same bundle flags, then written here behind a
# checksummed header so a later install can tell Coco output from user edits (issue #256).
#
# Usage:
#   bash adapters/aider/install.sh                  # all bundles that ship something
#   bash adapters/aider/install.sh --systems gsd    # only these bundles
#   bash adapters/aider/install.sh --core-only      # core set only (smaller AGENTS.md)
#   bash adapters/aider/install.sh --dry-run
# Refuses to write inside the Coco checkout itself (issue #238); run from your project directory.

set -euo pipefail
unset CDPATH

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRY_RUN=0
COMPILE_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --systems) shift; COMPILE_ARGS+=(--systems "${1:-}") ;;
    --core-only) COMPILE_ARGS+=(--core-only) ;;
    --help|-h) bash "$REPO_ROOT/scripts/print-usage.sh" "$0"; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; exit 1 ;;
  esac
  shift
done

run() { [[ $DRY_RUN -eq 1 ]] && echo "DRY: $*" || "$@"; }

# Portable sha256 of a file: bare lowercase hex.
sha256_file() {
  local f=$1
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$f" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$f" | awk '{print $1}'
  else
    python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$f"
  fi
}

# Write a Coco-generated file: header line (printf format, %s = checksum) plus
# body. The checksum covers every byte after the first line, so a later install
# can tell untouched Coco output from user edits (issue #256).
write_generated() {
  local target=$1 fmt=$2 body=$3 tmpbody sum
  tmpbody=$(mktemp)
  printf '%s\n' "$body" > "$tmpbody"
  sum=$(sha256_file "$tmpbody")
  { printf "$fmt\n" "$sum"; cat "$tmpbody"; } > "$target"
  rm -f "$tmpbody"
}

# True when the first line carries our checksum marker and the body still
# hashes to it, i.e. the file is byte-for-byte what Coco last wrote.
is_untouched_coco_output() {
  local f=$1 first expected actual
  IFS= read -r first < "$f" || return 1
  [[ "$first" == *"coco-generated sha256="* ]] || return 1
  expected=${first##*coco-generated sha256=}
  expected=${expected%%[!0-9a-f]*}   # drop any suffix like " -->"
  [[ "$expected" =~ ^[0-9a-f]{64}$ ]] || return 1
  actual=$(tail -n +2 "$f" | sha256_file /dev/stdin)
  [[ "$actual" == "$expected" ]]
}

# Back up a user file before overwriting. The first backup is <file>.coco-backup;
# once that exists it is NEVER overwritten — later backups are timestamped
# copies, then -1, -2, ... until a free name (issue #256).
backup_user_file() {
  local f=$1 b stamp base n=0
  if [[ ! -e "$f.coco-backup" ]]; then
    b="$f.coco-backup"
  else
    stamp=$(date +%Y%m%d-%H%M%S)
    base="$f.coco-backup-$stamp"
    b=$base
    while [[ -e "$b" ]]; do
      n=$((n+1))
      b="$base-$n"
    done
  fi
  cp -p "$f" "$b"
  echo "Backed up existing $f → $b"
}

# Install rule for a generated file (issue #256):
#   absent                    -> write, no backup
#   untouched Coco output     -> overwrite, no backup (checksum still matches)
#   anything else (user text) -> back up first, then write
install_generated() {
  local target=$1 fmt=$2 body=$3
  if [[ -f "$target" ]] && ! is_untouched_coco_output "$target"; then
    backup_user_file "$target"
  fi
  write_generated "$target" "$fmt" "$body"
}

echo "Coco · Aider CLI adapter"
echo "Source: $REPO_ROOT"
echo "Target: $(pwd) (project root)"

# Issue #238: never write into the Coco checkout itself (it has its own AGENTS.md).
# Compare physical paths so a symlinked cwd still matches. --dry-run writes nothing.
repo_root_phys="$(cd "$REPO_ROOT" && pwd -P)"
here_phys="$(pwd -P)"
if [[ $DRY_RUN -eq 0 && ( "$here_phys" == "$repo_root_phys" || "$here_phys" == "$repo_root_phys"/* ) ]]; then
  echo "ERROR: refusing to write AGENTS.md and .aider.conf.yml inside the Coco checkout ($repo_root_phys)." >&2
  echo "Run from your project directory: cd /path/to/your/project && bash $REPO_ROOT/install.sh --adapter aider" >&2
  exit 2
fi

compile() { # <codex -o target> [extra flags]: the codex compiler, told it is writing for Aider
  local out=$1
  shift
  env COCO_ADAPTER_LABEL=aider bash "$REPO_ROOT/adapters/codex/install.sh" -o "$out" "$@" \
    ${COMPILE_ARGS[@]+"${COMPILE_ARGS[@]}"}
}

# Entries in one top-level section of the compiled AGENTS.md. Only the first heading
# counts: rule bodies reuse names like "## Commands" further down.
count_entries() { # <file> <section> <entry regex>
  awk -v h="## $2" -v re="$3" '
    $0 == h && !seen { f = 1; seen = 1; next }
    f && /^## / { f = 0 }
    f && $0 ~ re { n++ }
    END { print n + 0 }' "$1"
}

if [[ $DRY_RUN -eq 1 ]]; then
  compile "$(pwd)/AGENTS.md" --dry-run
else
  work=$(mktemp -d)
  trap 'rm -rf "$work"' EXIT
  if ! compile "$work/AGENTS.md" > "$work/compile.log"; then
    cat "$work/compile.log" >&2
    echo "ERROR: compiling AGENTS.md failed; nothing was written." >&2
    exit 1
  fi
  # Our checksummed header replaces the compiler's title line.
  install_generated AGENTS.md \
    '# AGENTS.md — Generated by Coco for Aider CLI <!-- coco-generated sha256=%s -->' \
    "$(sed '1{/^# AGENTS.md$/d;}' "$work/AGENTS.md")"
  echo "Wrote: $(pwd)/AGENTS.md"
fi

# Generate .aider.conf.yml (body only; checksummed header added by write_generated)
CONF_CONTENT="# See https://aider.chat/docs/config.html for full reference

# Aider has no commit-format option; its default commit messages already
# follow Conventional Commits (<type>: <description>).

# Auto-commits enabled
auto-commits: true

# Read-only files (Coco artifacts — don't modify)
read:
  - AGENTS.md
  - .aider.conf.yml
"

CONF_CONTENT+="
# AGENTS.md lists Coco's skills, commands, agents and rules. Aider has no custom
# slash commands: ask for a command or skill by name (\"run team:ship\") instead.
# Skill files are in $REPO_ROOT/skills/; add one with /read-only <path> for its full text.
"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY: write .aider.conf.yml"
else
  install_generated .aider.conf.yml \
    '# .aider.conf.yml — Generated by Coco # coco-generated sha256=%s' \
    "$CONF_CONTENT"
  echo "Wrote: .aider.conf.yml"
fi

if [[ $DRY_RUN -eq 0 ]]; then
  echo
  echo "Installed for aider:"
  printf '  %-15s: %s\n' "AGENTS.md" "$(pwd)/AGENTS.md ($(wc -l < AGENTS.md | tr -d ' ') lines)"
  printf '  %-15s: %s\n' "Bundles" "$(sed -n 's/^Systems: //p' AGENTS.md | head -n 1)"
  printf '  %-15s: %s\n' "Skills" "$(count_entries AGENTS.md Skills '^- [*][*]')"
  printf '  %-15s: %s\n' "Commands" "$(count_entries AGENTS.md Commands '^- `')"
  printf '  %-15s: %s\n' "SI commands" "$(count_entries AGENTS.md 'Super Intelligence Commands' '^- `')"
  printf '  %-15s: %s\n' "Agents" "$(count_entries AGENTS.md Agents '^- [*][*]')"
  # Rule bodies carry their own headings; rule titles are the lowercase slugs.
  printf '  %-15s: %s\n' "Rules" "$(awk '$0 == "## Rules" { f = 1 } f && /^### [a-z0-9-]+$/ { n++ } END { print n + 0 }' AGENTS.md)"
  echo "Smaller AGENTS.md: bash $REPO_ROOT/install.sh --adapter aider --core-only"
fi
echo "Done."
