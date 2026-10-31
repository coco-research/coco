#!/usr/bin/env bash
# Issue #207: cursor and windsurf must install every Super Intelligence team
# front door (systems/<bundle>/<team>/SKILL.md, not under a skills/ folder).
# The link name is the frontmatter name, a re-run changes nothing, and a real
# file already at that path is left alone. cline and roo-code install no skills
# at all, so they are not here: this test does not invent a skills folder for them.
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT=$(pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
# The installers' own reader, so expected names match what they link. The fixtures
# below pin its parsing with explicit names.
# shellcheck disable=SC1091
source "$ROOT/scripts/lib/frontmatter.sh"

# name<TAB>team-dir for every front door in this checkout. The count is part of
# the assertion: the tree has 13, and an adapter that links a different set fails.
DOORS="$WORK/doors.tsv"
: >"$DOORS"
for f in "$ROOT"/systems/*/*/SKILL.md; do
  [[ -f "$f" ]] || continue
  case "$f" in
    */skills/*) continue ;;
  esac
  name=$(frontmatter_name "$f")
  [[ -n "$name" ]] || name=$(basename "$(dirname "$f")")
  printf '%s\t%s\n' "$name" "$(dirname "$f")" >>"$DOORS"
done
door_count=$(wc -l <"$DOORS" | tr -d ' ')
[[ "$door_count" -eq 13 ]] || fail "this checkout has $door_count front doors, expected 13"
dups=$(cut -f1 "$DOORS" | sort | uniq -d || true)
[[ -z "$dups" ]] || fail "duplicate front-door names: $dups"

# Bytes, symlink targets, and directory modes. Not mtimes: a re-run removes and
# relinks, which changes mtime and must not count as a change.
tree_id() {
  python3 - "$1" <<'PY'
import hashlib, os, sys
root = os.path.abspath(sys.argv[1])
rows = []
if os.path.isdir(root):
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in sorted(dirnames):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                rows.append("l " + rel + " -> " + os.readlink(p))
            else:
                rows.append("d " + rel + " %o" % (os.lstat(p).st_mode & 0o7777))
        for name in sorted(filenames):
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            if os.path.islink(p):
                rows.append("l " + rel + " -> " + os.readlink(p))
            elif os.path.isfile(p):
                digest = hashlib.sha256(open(p, "rb").read()).hexdigest()
                rows.append("f " + rel + " " + digest + " %o" % (os.lstat(p).st_mode & 0o7777))
            else:
                rows.append("o " + rel)
rows.sort()
sys.stdout.write("\n".join(rows) + ("\n" if rows else ""))
PY
}

target_of() {
  case "$1" in
    cursor) printf '%s\n' "$2/.cursor" ;;
    windsurf) printf '%s\n' "$2/.codeium/windsurf" ;;
    *) fail "no install target for $1" ;;
  esac
}

install_into() {
  local adapter=$1 home=$2 log=$3
  if ! env -u CURSOR_HOME -u WINDSURF_HOME -u CLINE_HOME -u ROO_CODE_HOME \
      HOME="$home" bash "$ROOT/adapters/$adapter/install.sh" >"$log" 2>&1; then
    echo "---- $log ----" >&2
    tail -n 40 "$log" >&2
    fail "$adapter install exited non-zero (log: $log)"
  fi
}

# Every front door is a symlink whose resolved path is that team directory
# inside this checkout. $3, when set, is one name expected to be a user file.
assert_doors() {
  local adapter=$1 skills=$2 skip=${3:-}
  local name src link resolved src_resolved linked=0
  while IFS=$'\t' read -r name src; do
    [[ -n "$name" ]] || continue
    link="$skills/$name"
    if [[ -n "$skip" && "$name" == "$skip" ]]; then
      [[ -e "$link" && ! -L "$link" ]] || fail "$adapter: existing user path $link was replaced"
      [[ -f "$link/KEEP" ]] || fail "$adapter: existing user file at $link was removed"
      continue
    fi
    [[ -L "$link" ]] || fail "$adapter: $name is not a symlink ($link)"
    resolved=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$link")
    src_resolved=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$src")
    [[ "$resolved" == "$src_resolved" ]] || fail "$adapter: $name resolves to $resolved, expected $src_resolved"
    case "$resolved" in
      "$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$ROOT")"/*) ;;
      *) fail "$adapter: $name resolves outside this checkout ($resolved)" ;;
    esac
    [[ -f "$resolved/SKILL.md" ]] || fail "$adapter: $name has no SKILL.md"
    linked=$((linked + 1))
  done <"$DOORS"
  if [[ -n "$skip" ]]; then
    [[ "$linked" -eq $((door_count - 1)) ]] || fail "$adapter: linked $linked front doors beside the user file, expected $((door_count - 1))"
  else
    [[ "$linked" -eq "$door_count" ]] || fail "$adapter: linked $linked front doors, expected $door_count"
  fi
}

for adapter in cursor windsurf; do
  echo "=== $adapter ==="
  home="$WORK/$adapter"
  mkdir -p "$home"
  log="$WORK/$adapter-install.log"
  install_into "$adapter" "$home" "$log"
  target=$(target_of "$adapter" "$home")
  skills="$target/skills"
  [[ -d "$skills" ]] || fail "$adapter: no skills directory at $skills"
  assert_doors "$adapter" "$skills"
  echo "  $door_count front doors land and resolve into this checkout"

  tree_id "$target" >"$WORK/$adapter-before.txt"
  install_into "$adapter" "$home" "$WORK/$adapter-rerun.log"
  tree_id "$target" >"$WORK/$adapter-after.txt"
  if ! cmp -s "$WORK/$adapter-before.txt" "$WORK/$adapter-after.txt"; then
    diff -u "$WORK/$adapter-before.txt" "$WORK/$adapter-after.txt" | head -n 40 >&2 || true
    fail "$adapter: re-run changed the install"
  fi
  echo "  re-run changed nothing"

  if grep -q -- '--uninstall)' "$ROOT/adapters/$adapter/install.sh"; then
    if ! env -u CURSOR_HOME -u WINDSURF_HOME HOME="$home" \
        bash "$ROOT/adapters/$adapter/install.sh" --uninstall >"$WORK/$adapter-uninstall.log" 2>&1; then
      tail -n 40 "$WORK/$adapter-uninstall.log" >&2
      fail "$adapter uninstall exited non-zero"
    fi
    while IFS=$'\t' read -r name _src; do
      [[ -n "$name" ]] || continue
      if [[ -e "$skills/$name" || -L "$skills/$name" ]]; then
        fail "$adapter uninstall left $skills/$name"
      fi
    done <"$DOORS"
    echo "  uninstall removed the front-door links"
  else
    echo "  no uninstall path; not checked"
  fi

  # A real directory at one front-door name is the user's own skill. The same
  # link_dir the other adapters use must leave it in place and still link the rest.
  user_home="$WORK/$adapter-user"
  mkdir -p "$user_home"
  user_skills="$(target_of "$adapter" "$user_home")/skills"
  planted=$(head -n 1 "$DOORS" | cut -f1)
  mkdir -p "$user_skills/$planted"
  printf 'user\n' >"$user_skills/$planted/KEEP"
  install_into "$adapter" "$user_home" "$WORK/$adapter-user.log"
  assert_doors "$adapter" "$user_skills" "$planted"
  echo "  existing user file at $planted was left alone"
done

# CRLF, a tab after the colon, and `name:` after the frontmatter. A reader
# that scans the whole file, or that only allows spaces after the colon, links
# "wrong" (or keeps a trailing CR). The id has to be the frontmatter value.
# The opening fence is line 1.
echo "=== crlf frontmatter ==="
crlf_root="$WORK/crlf-repo"
mkdir -p "$crlf_root/adapters/cursor" "$crlf_root/adapters/windsurf" "$crlf_root/scripts/lib" \
  "$crlf_root/systems/probe/crlf"
cp "$ROOT/scripts/lib/frontmatter.sh" "$crlf_root/scripts/lib/frontmatter.sh"
cp "$ROOT/adapters/cursor/install.sh" "$crlf_root/adapters/cursor/install.sh"
cp "$ROOT/adapters/windsurf/install.sh" "$crlf_root/adapters/windsurf/install.sh"
python3 - "$crlf_root/systems/probe/crlf/SKILL.md" <<'PY'
import pathlib, sys
pathlib.Path(sys.argv[1]).write_bytes(
    b"---\r\n"
    b"name:\t\"real-id\"\r\n"
    b"---\r\n"
    b"\r\n"
    b"name: wrong\r\n"
)
PY
# shellcheck disable=SC1091
source "$ROOT/scripts/lib/frontmatter.sh"
got=$(frontmatter_name "$crlf_root/systems/probe/crlf/SKILL.md")
[[ "$got" == "real-id" ]] || fail "helper returned $(printf '%q' "$got"), expected real-id"
for adapter in cursor windsurf; do
  home="$WORK/crlf-$adapter"
  mkdir -p "$home"
  if ! env -u CURSOR_HOME -u WINDSURF_HOME HOME="$home" \
      bash "$crlf_root/adapters/$adapter/install.sh" --systems probe \
      >"$WORK/crlf-$adapter.log" 2>&1; then
    tail -n 40 "$WORK/crlf-$adapter.log" >&2
    fail "$adapter crlf fixture install exited non-zero"
  fi
  skills="$(target_of "$adapter" "$home")/skills"
  link="$skills/real-id"
  if [[ ! -L "$link" ]]; then
    echo "skills dir:" >&2
    ls -la "$skills" >&2 || true
    fail "$adapter: frontmatter id real-id was not linked"
  fi
  if [[ -e "$skills/wrong" || -L "$skills/wrong" ]]; then
    fail "$adapter: linked the body id wrong"
  fi
  resolved=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$link")
  src_resolved=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$crlf_root/systems/probe/crlf")
  [[ "$resolved" == "$src_resolved" ]] || fail "$adapter: real-id resolves to $resolved, expected $src_resolved"
  echo "  $adapter: frontmatter id real-id, not the body"
done

# No frontmatter. A `---` line in the body, then `name: wrong`, is not a name
# field. The installer must link the team under its directory name.
echo "=== body fence is not frontmatter ==="
nofm_root="$WORK/nofm-repo"
mkdir -p "$nofm_root/adapters/cursor" "$nofm_root/adapters/windsurf" "$nofm_root/scripts/lib" \
  "$nofm_root/systems/probe/nofm"
cp "$ROOT/scripts/lib/frontmatter.sh" "$nofm_root/scripts/lib/frontmatter.sh"
cp "$ROOT/adapters/cursor/install.sh" "$nofm_root/adapters/cursor/install.sh"
cp "$ROOT/adapters/windsurf/install.sh" "$nofm_root/adapters/windsurf/install.sh"
python3 - "$nofm_root/systems/probe/nofm/SKILL.md" <<'PY'
import pathlib, sys
pathlib.Path(sys.argv[1]).write_text(
    "# Team notes\n"
    "\n"
    "A fence in the body is not frontmatter.\n"
    "\n"
    "---\n"
    "name: wrong\n"
    "\n"
    "Still the body.\n"
)
PY
got=$(frontmatter_name "$nofm_root/systems/probe/nofm/SKILL.md")
[[ -z "$got" ]] || fail "helper returned $(printf '%q' "$got") for a body fence, expected nothing"
for adapter in cursor windsurf; do
  home="$WORK/nofm-$adapter"
  mkdir -p "$home"
  if ! env -u CURSOR_HOME -u WINDSURF_HOME HOME="$home" \
      bash "$nofm_root/adapters/$adapter/install.sh" --systems probe \
      >"$WORK/nofm-$adapter.log" 2>&1; then
    tail -n 40 "$WORK/nofm-$adapter.log" >&2
    fail "$adapter body-fence fixture install exited non-zero"
  fi
  skills="$(target_of "$adapter" "$home")/skills"
  link="$skills/nofm"
  if [[ ! -L "$link" ]]; then
    echo "skills dir:" >&2
    ls -la "$skills" >&2 || true
    fail "$adapter: directory name nofm was not linked"
  fi
  if [[ -e "$skills/wrong" || -L "$skills/wrong" ]]; then
    fail "$adapter: linked the body id wrong"
  fi
  resolved=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$link")
  src_resolved=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$nofm_root/systems/probe/nofm")
  [[ "$resolved" == "$src_resolved" ]] || fail "$adapter: nofm resolves to $resolved, expected $src_resolved"
  echo "  $adapter: directory name nofm, not the body"
done

# A frontmatter name is one path component. ../escape, a/b, and "has space"
# are not slugs, so each team is linked under its directory name and the name
# creates nothing outside the skills directory.
echo "=== unsafe frontmatter name is not a path ==="
unsafe_root="$WORK/unsafe-repo"
mkdir -p "$unsafe_root/adapters/cursor" "$unsafe_root/adapters/windsurf" "$unsafe_root/scripts/lib" \
  "$unsafe_root/systems/probe/dotdot" "$unsafe_root/systems/probe/slash" "$unsafe_root/systems/probe/spaced"
cp "$ROOT/scripts/lib/frontmatter.sh" "$unsafe_root/scripts/lib/frontmatter.sh"
cp "$ROOT/adapters/cursor/install.sh" "$unsafe_root/adapters/cursor/install.sh"
cp "$ROOT/adapters/windsurf/install.sh" "$unsafe_root/adapters/windsurf/install.sh"
python3 - "$unsafe_root" <<'PY'
import pathlib, sys
root = pathlib.Path(sys.argv[1])
for team, name in (("dotdot", "../escape"), ("slash", "a/b"), ("spaced", "has space")):
    path = root / "systems" / "probe" / team / "SKILL.md"
    path.write_text('---\nname: "%s"\n---\n\nTeam %s.\n' % (name, team))
PY
for team in dotdot slash spaced; do
  got=$(frontmatter_name "$unsafe_root/systems/probe/$team/SKILL.md")
  [[ -z "$got" ]] || fail "helper returned $(printf '%q' "$got") for $team, expected nothing"
done
for adapter in cursor windsurf; do
  home="$WORK/unsafe-$adapter"
  mkdir -p "$home"
  if ! env -u CURSOR_HOME -u WINDSURF_HOME HOME="$home" \
      bash "$unsafe_root/adapters/$adapter/install.sh" --systems probe \
      >"$WORK/unsafe-$adapter.log" 2>&1; then
    tail -n 40 "$WORK/unsafe-$adapter.log" >&2
    fail "$adapter unsafe-name fixture install exited non-zero"
  fi
  target=$(target_of "$adapter" "$home")
  skills="$target/skills"
  for team in dotdot slash spaced; do
    link="$skills/$team"
    if [[ ! -L "$link" ]]; then
      echo "skills dir:" >&2
      ls -la "$skills" >&2 || true
      fail "$adapter: directory name $team was not linked"
    fi
    resolved=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$link")
    src_resolved=$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$unsafe_root/systems/probe/$team")
    [[ "$resolved" == "$src_resolved" ]] || fail "$adapter: $team resolves to $resolved, expected $src_resolved"
  done
  if [[ -e "$target/escape" || -L "$target/escape" || -e "$home/escape" || -L "$home/escape" ]]; then
    fail "$adapter: name ../escape created a path outside $skills"
  fi
  if [[ -e "$skills/a" || -L "$skills/a" || -e "$skills/a/b" || -L "$skills/a/b" ]]; then
    fail "$adapter: name a/b created a path under $skills"
  fi
  if [[ -e "$skills/has space" || -L "$skills/has space" ]]; then
    fail "$adapter: name 'has space' was used as a path"
  fi
  # The installer also creates rules, commands, or agents beside skills.
  # Anything else outside skills is this name leaving the directory.
  if ! python3 - "$home" "$skills" "$target" <<'PY'
import os, sys
home, skills, target = [os.path.abspath(p) for p in sys.argv[1:]]
allowed = [
    skills,
    os.path.join(target, "rules"),
    os.path.join(target, "commands"),
    os.path.join(target, "agents"),
]

def contains(root, path):
    return path == root or path.startswith(root + os.sep)

leaks = []
for dirpath, dirnames, filenames in os.walk(home, followlinks=False):
    for name in dirnames + filenames:
        path = os.path.abspath(os.path.join(dirpath, name))
        # Parents of skills/ (the home and the adapter dir) are not a leak.
        if contains(path, skills):
            continue
        if any(contains(root, path) for root in allowed):
            continue
        leaks.append(path)
if leaks:
    sys.stderr.write("created outside skills:\n" + "\n".join(leaks) + "\n")
    sys.exit(1)
PY
  then
    fail "$adapter: created a path outside $skills"
  fi
  echo "  $adapter: directory names dotdot, slash, spaced; nothing outside skills"
done

echo "PASS: cursor and windsurf install all $door_count SI team front doors"
