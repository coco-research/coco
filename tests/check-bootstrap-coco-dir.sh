#!/usr/bin/env bash
# Issue #239: the npm CLI's update cache creates ~/.coco/.update-check.json, which made
# bin/coco-bootstrap.sh refuse to clone ("exists but is not a Coco clone"). The bootstrap
# must accept a ~/.coco holding only that cache file, and still refuse one with user data.
# git is stubbed on PATH, so this needs no network.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Stub git: `clone ... <dir>` makes <dir> with an install.sh; everything else answers plainly.
mkdir "$TMP/bin"
cat > "$TMP/bin/git" <<'STUB'
#!/usr/bin/env bash
for last; do :; done
case " $* " in
  *" clone "*)
    # git clone refuses a non-empty target; so does the stub.
    if [ -d "$last" ] && [ -n "$(ls -A "$last")" ]; then echo "fatal: not empty" >&2; exit 128; fi
    mkdir -p "$last/.git"; echo 'echo stub-install "$@"' > "$last/install.sh" ;;
  *" rev-parse "*) echo 0123456789abcdef ;;
  *" log "*) echo stub ;;
esac
STUB
chmod +x "$TMP/bin/git"

run() {  # run <home>: bootstrap with a throwaway HOME and the stubbed git
  HOME="$1" PATH="$TMP/bin:$PATH" COCO_DIR= COCO_BOOTSTRAP_YES=1 bash "$ROOT/bin/coco-bootstrap.sh" --adapter generic 2>&1
}

fail=0
check() { if [ "$2" = ok ]; then echo "PASS: $1"; else echo "FAIL: $1"; fail=1; fi; }

# 1. ~/.coco holding only the update cache: bootstrap proceeds and clones.
H1="$TMP/h1"; mkdir -p "$H1/.coco"; echo '{}' > "$H1/.coco/.update-check.json"
out="$(run "$H1")" && rc=0 || rc=$?
[ "$rc" = 0 ] && [ -d "$H1/.coco/.git" ] && [ ! -e "$H1/.coco/.update-check.json" ] \
  && check "cache-only ~/.coco is cloned into" ok || { echo "$out"; check "cache-only ~/.coco is cloned into" no; }

# 2. ~/.coco with a user file (alone or beside the cache): refused, nothing deleted.
for extra in "" ".update-check.json"; do
  H2="$TMP/h2$extra"; mkdir -p "$H2/.coco"; echo keep > "$H2/.coco/notes.txt"
  [ -n "$extra" ] && echo '{}' > "$H2/.coco/$extra"
  out="$(run "$H2")" && rc=0 || rc=$?
  [ "$rc" != 0 ] && [ -f "$H2/.coco/notes.txt" ] && [ ! -d "$H2/.coco/.git" ] \
    && check "user data in ~/.coco is refused and kept (cache: ${extra:-none})" ok \
    || { echo "$out"; check "user data in ~/.coco is refused and kept (cache: ${extra:-none})" no; }
done

# 3. A pre-existing *empty* ~/.coco: the guard clones into it instead of refusing.
H3="$TMP/h3"; mkdir -p "$H3/.coco"
out="$(run "$H3")" && rc=0 || rc=$?
[ "$rc" = 0 ] && [ -d "$H3/.coco/.git" ] \
  && check "empty ~/.coco is cloned into" ok || { echo "$out"; check "empty ~/.coco is cloned into" no; }

# 4. A *directory* named .update-check.json is not the regenerable cache file: it must
#    hit the friendly refusal (assert the message — a raw rm abort exits nonzero too)
#    and be left in place.
H4="$TMP/h4"; mkdir -p "$H4/.coco/.update-check.json"
out="$(run "$H4")" && rc=0 || rc=$?
[ "$rc" != 0 ] && grep -q "not a Coco clone" <<<"$out" \
  && [ -d "$H4/.coco/.update-check.json" ] && [ ! -d "$H4/.coco/.git" ] \
  && check "cache-named directory is refused with the friendly message and kept" ok \
  || { echo "$out"; check "cache-named directory is refused with the friendly message and kept" no; }

exit "$fail"
