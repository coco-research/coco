#!/usr/bin/env bash
# Aider installer backup rule (issue #256, reworked):
#   - generated files carry a checksummed header (coco-generated sha256=<hex>)
#   - absent target            -> written, no backup
#   - untouched Coco output    -> overwritten, no backup
#   - anything else            -> backed up to <file>.coco-backup, then
#                                 <file>.coco-backup-<ts>[-N]; never overwritten
# Never runs the installer in the repo root: it writes AGENTS.md into cwd.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

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

fail() { echo "FAIL: $*"; exit 1; }

run_install() { # <proj> <home> [extra args...]
  local proj=$1 home=$2
  shift 2
  (cd "$proj" && HOME="$home" bash "$ROOT/adapters/aider/install.sh" "$@" >/dev/null)
}

count_dated() { # <dir> <name>  -> count of <name>.coco-backup-<something>
  local dir=$1 name=$2
  local found=()
  shopt -s nullglob
  found=("$dir/$name".coco-backup-*)
  shopt -u nullglob
  echo "${#found[@]}"
}

assert_coco_output() { # <file> <label>: first line carries a checksum matching the body
  local f=$1 label=$2 first expected actual
  [[ -f "$f" ]] || fail "assert_coco_output: $f missing"
  IFS= read -r first < "$f" || true
  [[ "$first" == *"coco-generated sha256="* ]] || fail "$label: first line lacks coco-generated sha256 marker"
  expected=${first##*coco-generated sha256=}
  expected=${expected%%[!0-9a-f]*}
  [[ "$expected" =~ ^[0-9a-f]{64}$ ]] || fail "$label: no 64-hex checksum in first line: $first"
  actual=$(tail -n +2 "$f" | sha256_file /dev/stdin)
  [[ "$actual" == "$expected" ]] || fail "$label: checksum mismatch (header $expected, body $actual)"
}

newproj() { # <name> -> echoes project dir, creates it + a HOME
  local d="$tmp/$1"
  mkdir -p "$d" "$tmp/$1-home"
  echo "$d"
}

### Case 1: fresh project -> files written, checksums valid, no backups
p=$(newproj p1)
run_install "$p" "$tmp/p1-home"
[[ -f "$p/AGENTS.md" && -f "$p/.aider.conf.yml" ]] || fail "case 1: generated files missing"
assert_coco_output "$p/AGENTS.md" "case 1 AGENTS.md"
assert_coco_output "$p/.aider.conf.yml" "case 1 .aider.conf.yml"
[[ ! -e "$p/AGENTS.md.coco-backup" && ! -e "$p/.aider.conf.yml.coco-backup" ]] || fail "case 1: fresh install created .coco-backup"
[[ $(count_dated "$p" AGENTS.md) -eq 0 && $(count_dated "$p" .aider.conf.yml) -eq 0 ]] || fail "case 1: fresh install created dated backups"

### Case 2: --dry-run with pre-existing hand-written files -> nothing changes
p=$(newproj p2)
printf '# My project AGENTS.md\nHand-written team rules.\n' > "$p/AGENTS.md"
printf 'model: my-model\nauto-commits: false\n' > "$p/.aider.conf.yml"
cp "$p/AGENTS.md" "$tmp/ref-p2-agents"      # references live OUTSIDE the project dir
cp "$p/.aider.conf.yml" "$tmp/ref-p2-conf"
run_install "$p" "$tmp/p2-home" --dry-run
cmp -s "$p/AGENTS.md" "$tmp/ref-p2-agents" || fail "case 2: --dry-run modified AGENTS.md"
cmp -s "$p/.aider.conf.yml" "$tmp/ref-p2-conf" || fail "case 2: --dry-run modified .aider.conf.yml"
[[ ! -e "$p/AGENTS.md.coco-backup" && ! -e "$p/.aider.conf.yml.coco-backup" ]] || fail "case 2: --dry-run created .coco-backup"
[[ $(count_dated "$p" AGENTS.md) -eq 0 && $(count_dated "$p" .aider.conf.yml) -eq 0 ]] || fail "case 2: --dry-run created dated backups"

### Case 3: hand-written AGENTS.md -> backed up byte-identical, replaced by Coco output
p=$(newproj p3)
printf '# My project AGENTS.md\nHand-written team rules. DO NOT LOSE.\n' > "$p/AGENTS.md"
cp "$p/AGENTS.md" "$tmp/ref-p3-agents"
run_install "$p" "$tmp/p3-home"
[[ -f "$p/AGENTS.md.coco-backup" ]] || fail "case 3: AGENTS.md.coco-backup missing"
cmp -s "$p/AGENTS.md.coco-backup" "$tmp/ref-p3-agents" || fail "case 3: backup is not byte-identical to the original"
assert_coco_output "$p/AGENTS.md" "case 3 new AGENTS.md"
grep -q 'DO NOT LOSE' "$p/AGENTS.md" && fail "case 3: user text leaked into generated AGENTS.md" || true

### Case 4: untouched Coco output re-install -> no backup at all
p=$(newproj p4)
run_install "$p" "$tmp/p4-home"
run_install "$p" "$tmp/p4-home"
[[ ! -e "$p/AGENTS.md.coco-backup" && ! -e "$p/.aider.conf.yml.coco-backup" ]] || fail "case 4: re-install of untouched Coco output created .coco-backup"
[[ $(count_dated "$p" AGENTS.md) -eq 0 && $(count_dated "$p" .aider.conf.yml) -eq 0 ]] || fail "case 4: re-install of untouched Coco output created dated backups"

### Case 5: user file -> backup survives two untouched re-installs, zero dated copies
p=$(newproj p5)
printf '# My project AGENTS.md\nHand-written team rules.\n' > "$p/AGENTS.md"
cp "$p/AGENTS.md" "$tmp/ref-p5-agents"
run_install "$p" "$tmp/p5-home"
run_install "$p" "$tmp/p5-home"
run_install "$p" "$tmp/p5-home"
cmp -s "$p/AGENTS.md.coco-backup" "$tmp/ref-p5-agents" || fail "case 5: .coco-backup drifted from the original hand-written file"
[[ $(count_dated "$p" AGENTS.md) -eq 0 ]] || fail "case 5: untouched re-installs created dated copies"

### Case 6: edited Coco output -> dated backup with the edit; .coco-backup untouched
p=$(newproj p6a)
printf '# My project AGENTS.md\nHand-written team rules.\n' > "$p/AGENTS.md"
cp "$p/AGENTS.md" "$tmp/ref-p6a-agents"
run_install "$p" "$tmp/p6a-home"
printf 'MY EDIT\n' >> "$p/AGENTS.md"        # keep header line, edit body
run_install "$p" "$tmp/p6a-home"
shopt -s nullglob; dated=("$p"/AGENTS.md.coco-backup-*); shopt -u nullglob
[[ ${#dated[@]} -eq 1 ]] || fail "case 6a: expected exactly 1 dated copy, found ${#dated[@]}"
grep -q 'MY EDIT' "${dated[0]}" || fail "case 6a: dated backup missing MY EDIT"
cmp -s "$p/AGENTS.md.coco-backup" "$tmp/ref-p6a-agents" || fail "case 6a: .coco-backup no longer matches the original"
# variant: fresh install, edit, re-install -> first backup holds the edit, no dated copy
p=$(newproj p6b)
run_install "$p" "$tmp/p6b-home"
printf 'MY EDIT\n' >> "$p/AGENTS.md"
run_install "$p" "$tmp/p6b-home"
grep -q 'MY EDIT' "$p/AGENTS.md.coco-backup" || fail "case 6b: .coco-backup missing MY EDIT"
[[ $(count_dated "$p" AGENTS.md) -eq 0 ]] || fail "case 6b: unexpected dated copies"

### Case 7: old Coco header without checksum -> treated as user content
p=$(newproj p7)
printf '# AGENTS.md — Generated by Coco for Aider CLI\nOld generated body.\n' > "$p/AGENTS.md"
cp "$p/AGENTS.md" "$tmp/ref-p7-agents"
run_install "$p" "$tmp/p7-home"
[[ -f "$p/AGENTS.md.coco-backup" ]] || fail "case 7: checksum-less old Coco file was not backed up"
cmp -s "$p/AGENTS.md.coco-backup" "$tmp/ref-p7-agents" || fail "case 7: backup is not byte-identical to the old file"

### Case 8: .aider.conf.yml follows the same rule
p=$(newproj p8a)
printf 'model: my-model\nauto-commits: false\n' > "$p/.aider.conf.yml"
cp "$p/.aider.conf.yml" "$tmp/ref-p8a-conf"
run_install "$p" "$tmp/p8a-home"
cmp -s "$p/.aider.conf.yml.coco-backup" "$tmp/ref-p8a-conf" || fail "case 8a: conf backup is not byte-identical to the original"
assert_coco_output "$p/.aider.conf.yml" "case 8a new conf"
run_install "$p" "$tmp/p8a-home"
[[ $(count_dated "$p" .aider.conf.yml) -eq 0 ]] || fail "case 8a: untouched re-install created a dated copy"
cmp -s "$p/.aider.conf.yml.coco-backup" "$tmp/ref-p8a-conf" || fail "case 8a: .coco-backup changed on untouched re-install"
# variant: .coco-backup exists, generated file edited -> dated copy, .coco-backup unchanged
p=$(newproj p8b)
printf 'model: my-model\nauto-commits: false\n' > "$p/.aider.conf.yml"
cp "$p/.aider.conf.yml" "$tmp/ref-p8b-conf"
run_install "$p" "$tmp/p8b-home"
printf '# MY EDIT\n' >> "$p/.aider.conf.yml"
run_install "$p" "$tmp/p8b-home"
shopt -s nullglob; dated=("$p"/.aider.conf.yml.coco-backup-*); shopt -u nullglob
[[ ${#dated[@]} -eq 1 ]] || fail "case 8b: expected exactly 1 dated copy, found ${#dated[@]}"
grep -q 'MY EDIT' "${dated[0]}" || fail "case 8b: dated backup missing MY EDIT"
cmp -s "$p/.aider.conf.yml.coco-backup" "$tmp/ref-p8b-conf" || fail "case 8b: .coco-backup no longer matches the original"

echo "PASS: aider installer checksum-guarded backups (8 cases)"
