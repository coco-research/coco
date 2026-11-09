#!/usr/bin/env bash
# Cases for tests/check-vendor-lock.py: every rule in that gate that protects a
# licence has to be seen failing for its own reason, or a check that stops
# firing passes CI quietly.
#
# Each case takes a throwaway copy of the tree, breaks one thing on purpose,
# and requires the checker to exit 1 with a problem line naming that thing. One
# unmodified copy must exit 0, so a gate that fails everything fails here too.
#
# Offline. bash 3.2 on macOS: no associative arrays, no mapfile.
set -u

root=$(cd "$(dirname "$0")/.." && pwd)
checker="tests/check-vendor-lock.py"
tmpdir=${TMPDIR:-/tmp}
tmpdir=${tmpdir%/}
work=$(mktemp -d "$tmpdir/vendor-lock-cases.XXXXXX")
trap 'rm -rf "$work"' EXIT INT TERM

gsap_a="systems/hyperframes/skills/music-to-video/references/motion-primitives/assets/gsap.min.js"
gsap_b="systems/hyperframes/skills/talking-head-recut/assets/vendor/gsap.min.js"

fails=0

# A copy the checker can resolve its own ROOT in. No .git: these cases must not
# depend on git being installed or on HEAD existing.
copy_tree() {
  mkdir -p "$1"
  cp -R "$root/." "$1/"
  rm -rf "$1/.git" "$1/node_modules"
}

run_check() {   # run_check <dir> <output file> [checker args...]
  dir=$1
  shift
  out=$1
  shift
  ( cd "$dir" && python3 -B "$checker" "$@" ) >"$out" 2>&1
  return $?
}

require() {     # require <label> <status> <output file> <needle> [needle...]
  label=$1
  status=$2
  out=$3
  shift 3
  if [ "$status" -ne 1 ]; then
    echo "FAIL $label: expected the checker to exit 1, got $status"
    sed 's/^/    /' "$out"
    fails=$((fails + 1))
    return
  fi
  for needle in "$@"; do
    if ! grep -Fq -- "$needle" "$out"; then
      echo "FAIL $label: no problem line mentions '$needle'"
      sed 's/^/    /' "$out"
      fails=$((fails + 1))
      return
    fi
  done
  echo "ok   $label"
}

# One clean copy is the reference every case is cut from.
pristine="$work/pristine"
copy_tree "$pristine"

out="$work/clean.out"
run_check "$pristine" "$out"
status=$?
if [ "$status" -eq 0 ]; then
  echo "ok   unmodified copy passes"
else
  echo "FAIL unmodified copy: expected exit 0, got $status"
  sed 's/^/    /' "$out"
  fails=$((fails + 1))
fi

# 1. One byte changed in a GSAP build. Digests are pinned first, because a
#    committed digest is what makes the lock stand on its own.
case1="$work/case1"
cp -R "$pristine" "$case1"
out="$work/case1-update.out"
run_check "$case1" "$out" --update
status=$?
if [ "$status" -ne 0 ]; then
  echo "FAIL case 1 setup: --update exited $status"
  sed 's/^/    /' "$out"
  fails=$((fails + 1))
else
  python3 - "$case1/$gsap_b" <<'PY'
import sys
path = sys.argv[1]
data = bytearray(open(path, "rb").read())
at = data.find(b"GreenSock")
if at < 0:
    raise SystemExit("case 1: no GreenSock marker to flip")
data[at] ^= 0x20                    # G -> g: exactly one byte, notice untouched
with open(path, "wb") as handle:
    handle.write(data)
PY
  out="$work/case1.out"
  run_check "$case1" "$out"
  status=$?
  require "case 1 (one byte changed in $gsap_b)" "$status" "$out" \
    "$gsap_b" "changed since it was pinned"
fi

# 2. The GSAP notice text removed from one build. The digest is left unpinned,
#    so the notice rule is what has to catch it.
case2="$work/case2"
cp -R "$pristine" "$case2"
python3 - "$case2/$gsap_a" <<'PY'
import sys
path = sys.argv[1]
notice = b"Subject to the terms at https://gsap.com/standard-license"
data = open(path, "rb").read()
if notice not in data:
    raise SystemExit("case 2: notice text not found")
with open(path, "wb") as handle:
    handle.write(data.replace(notice, b"", 1))
PY
out="$work/case2.out"
run_check "$case2" "$out"
status=$?
require "case 2 (GSAP notice removed from $gsap_a)" "$status" "$out" \
  "$gsap_a" "no longer contains" "Subject to the terms at https://gsap.com/standard-license"

# 3. CC0-1.0 is allowed, but only on the Kenney.nl row.
case3="$work/case3"
cp -R "$pristine" "$case3"
python3 - "$case3/data/vendor-lock.json" humanizer CC0-1.0 <<'PY'
import json, sys
path, name, spdx = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, encoding="utf-8") as handle:
    rows = json.load(handle)
for row in rows:
    if row.get("name") == name:
        row["licence_spdx"] = spdx
        break
else:
    raise SystemExit(f"case 3: no row named {name}")
with open(path, "w", encoding="utf-8") as handle:
    json.dump(rows, handle, indent=2, ensure_ascii=False)
    handle.write("\n")
PY
out="$work/case3.out"
run_check "$case3" "$out"
status=$?
require "case 3 (CC0-1.0 on a row other than Kenney.nl)" "$status" "$out" \
  "humanizer: CC0-1.0 is reserved for the Kenney.nl row"

# 4. The GSAP pin moved. 3.15.0 is fixed until a licence reviewer says otherwise.
case4="$work/case4"
cp -R "$pristine" "$case4"
python3 - "$case4/data/vendor-lock.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    rows = json.load(handle)
for row in rows:
    if row.get("name") == "GSAP":
        row["pinned_ref"] = "3.16.0"
        break
else:
    raise SystemExit("case 4: no GSAP row")
with open(path, "w", encoding="utf-8") as handle:
    json.dump(rows, handle, indent=2, ensure_ascii=False)
    handle.write("\n")
PY
out="$work/case4.out"
run_check "$case4" "$out"
status=$?
require "case 4 (GSAP pinned_ref moved to 3.16.0)" "$status" "$out" \
  "GSAP: pinned_ref must stay 3.15.0" "3.16.0"

case5="$work/case5"
cp -R "$pristine" "$case5"
python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); d.append(42); json.dump(d, open(p, "w"))' \
  "$case5/data/vendor-lock.json"
out="$work/case5.out"
run_check "$case5" "$out"
status=$?
require "case 5 (a lock row that is not an object)" "$status" "$out" "must be an object"

case6="$work/case6"
cp -R "$pristine" "$case6"
sfx=$(ls "$case6"/skills/coco-ads/assets/sfx/*/*.ogg | head -1)
printf 'x' >> "$sfx"
out="$work/case6.out"
run_check "$case6" "$out"
status=$?
require "case 6 (one Kenney sound effect changed)" "$status" "$out" "Kenney.nl: files under"

if [ "$fails" -ne 0 ]; then
  echo "$fails vendor-lock case(s) failed."
  exit 1
fi
echo "All vendor-lock cases pass."
