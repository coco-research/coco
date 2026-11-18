#!/usr/bin/env bash
# `coco update` on a detached release clone must resolve the newest vX.Y.Z tag on
# origin (even when the running CLI's own package.json is older), ignore
# non-semver/pre-release tags, stay safe offline, and refuse dirty/unpushed work.
# Hermetic: temp HOME + local bare repo via insteadOf; zero network calls.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

mkdir -p "$T/home/.config/git" "$T/cli/bin"
cp "$ROOT/bin/coco.js" "$T/cli/bin/coco.js"
printf '%s\n' '{"name":"cocosuperintelligence","version":"1.10.0"}' > "$T/cli/package.json"

export GIT_CONFIG_NOSYSTEM=1
GIT_TEST_ID=(-c user.name=test -c user.email=test@example.com -c commit.gpgsign=false -c tag.gpgSign=false)

git init -q --bare "$T/remote.git"
git init -q "$T/seed"
printf '%s\n' '{"name":"cocosuperintelligence","version":"1.10.0"}' > "$T/seed/package.json"
printf '#!/usr/bin/env bash\nexit 0\n' > "$T/seed/install.sh"
chmod +x "$T/seed/install.sh"
printf 'v1.10.0\n' > "$T/seed/RELEASE.txt"
git -C "$T/seed" "${GIT_TEST_ID[@]}" add -A
git -C "$T/seed" "${GIT_TEST_ID[@]}" commit -qm "release 1.10.0"
git -C "$T/seed" "${GIT_TEST_ID[@]}" tag v1.10.0
git -C "$T/seed" push -q "$T/remote.git" HEAD:refs/heads/main refs/tags/v1.10.0:refs/tags/v1.10.0

set_remote_url() {
  rm -f "$T/home/.gitconfig"
  git config --file "$T/home/.gitconfig" "url.file://$1.insteadOf" "https://github.com/coco-research/coco.git"
}

coco() {
  RC=0
  (
    cd "$T/cli"
    HOME="$T/home" \
    XDG_CONFIG_HOME="$T/home/.config" \
    GIT_CONFIG_GLOBAL="$T/home/.gitconfig" \
    COCO_NO_UPDATE_CHECK=1 \
    node bin/coco.js "$@"
  ) >"$T/out" 2>"$T/err" || RC=$?
}

make_detached_clone() {
  HOME="$T/home" XDG_CONFIG_HOME="$T/home/.config" GIT_CONFIG_GLOBAL="$T/home/.gitconfig" \
    git clone -q -c advice.detachedHead=false --branch v1.10.0 --depth 1 \
    https://github.com/coco-research/coco.git "$1"
}

set_remote_url "$T/remote.git"
make_detached_clone "$T/clone"
[ "$(git -C "$T/clone" config --local --get remote.origin.url)" = "https://github.com/coco-research/coco.git" ] \
  || fail "origin URL was rewritten in local config"
v110_sha="$(git -C "$T/remote.git" rev-parse "v1.10.0^{commit}")"
[ "$(git -C "$T/clone" rev-parse HEAD)" = "$v110_sha" ] || fail "initial clone not at v1.10.0"

# Publish v2.0.0 on the bare remote while running CLI stays at package.json 1.10.0.
printf '%s\n' '{"name":"cocosuperintelligence","version":"2.0.0"}' > "$T/seed/package.json"
printf 'v2.0.0\n' > "$T/seed/RELEASE.txt"
git -C "$T/seed" "${GIT_TEST_ID[@]}" commit -qam "release 2.0.0"
git -C "$T/seed" "${GIT_TEST_ID[@]}" tag -a v2.0.0 -m "v2.0.0"
git -C "$T/seed" push -q "$T/remote.git" HEAD:refs/heads/main refs/tags/v2.0.0:refs/tags/v2.0.0
v200_sha="$(git -C "$T/remote.git" rev-parse "v2.0.0^{commit}")"

# (1) Dirty tracked file and unpushed local commit on v1.10.0 still exit 2 untouched.
make_detached_clone "$T/clone-dirty"
printf 'local edit\n' >> "$T/clone-dirty/RELEASE.txt"
coco update "$T/clone-dirty"
[ "$RC" -eq 2 ] || fail "(1a) dirty update exited $RC ($(cat "$T/err"))"
[ "$(git -C "$T/clone-dirty" rev-parse HEAD)" = "$v110_sha" ] || fail "(1a) dirty HEAD moved"
grep -q "local edit" "$T/clone-dirty/RELEASE.txt" || fail "(1a) dirty edit lost"
grep -q "Nothing was changed." "$T/err" || fail "(1a) missing refusal message ($(cat "$T/err"))"

make_detached_clone "$T/clone-ahead"
printf 'committed edit\n' >> "$T/clone-ahead/RELEASE.txt"
git -C "$T/clone-ahead" "${GIT_TEST_ID[@]}" commit -qam "local wip"
ahead_sha="$(git -C "$T/clone-ahead" rev-parse HEAD)"
coco update "$T/clone-ahead"
[ "$RC" -eq 2 ] || fail "(1b) unpushed update exited $RC ($(cat "$T/err"))"
[ "$(git -C "$T/clone-ahead" rev-parse HEAD)" = "$ahead_sha" ] || fail "(1b) unpushed HEAD moved"
grep -q "unpushed" "$T/err" || fail "(1b) missing unpushed reason ($(cat "$T/err"))"

# (2) Clean detached clone on v1.10.0 updates to v2.0.0 (preserving untracked state).
mkdir -p "$T/clone/knowledge"
printf 'keep-note\n' > "$T/clone/knowledge/note.md"
coco update "$T/clone"
[ "$RC" -eq 0 ] || fail "(2) update exited $RC ($(cat "$T/err"))"
[ "$(git -C "$T/clone" rev-parse HEAD)" = "$v200_sha" ] \
  || fail "(2) clone stayed at $(git -C "$T/clone" rev-parse HEAD), expected v2.0.0 ($v200_sha)"
[ -f "$T/clone/knowledge/note.md" ] || fail "(2) untracked knowledge file removed"

# (3) Pre-release and non-semver tags (v2.1.0-rc.1, v2.1) on origin are ignored.
printf 'v2.1.0-rc.1\n' > "$T/seed/RELEASE.txt"
git -C "$T/seed" "${GIT_TEST_ID[@]}" commit -qam "rc 2.1.0-rc.1"
git -C "$T/seed" "${GIT_TEST_ID[@]}" tag -a v2.1.0-rc.1 -m "rc1"
git -C "$T/seed" "${GIT_TEST_ID[@]}" tag v2.1
git -C "$T/seed" push -q "$T/remote.git" refs/tags/v2.1.0-rc.1:refs/tags/v2.1.0-rc.1 refs/tags/v2.1:refs/tags/v2.1

make_detached_clone "$T/clone-rc"
coco update "$T/clone-rc"
[ "$RC" -eq 0 ] || fail "(3) update with pre-release tag exited $RC ($(cat "$T/err"))"
[ "$(git -C "$T/clone-rc" rev-parse HEAD)" = "$v200_sha" ] \
  || fail "(3) pre-release tag was not ignored: HEAD=$(git -C "$T/clone-rc" rev-parse HEAD)"

# (4) Offline fallback stays safe: neither crashes nor downgrades v2.0.0 back to v1.10.0.
make_detached_clone "$T/clone-offline"
set_remote_url "$T/unreachable-offline.git"

coco update "$T/clone-offline"
[ "$RC" -eq 0 ] || fail "(4a) offline update on v1.10.0 exited $RC ($(cat "$T/err"))"
[ "$(git -C "$T/clone-offline" rev-parse HEAD)" = "$v110_sha" ] || fail "(4a) offline v1.10.0 HEAD changed"

coco update "$T/clone"
[ "$RC" -eq 0 ] || fail "(4b) offline update on v2.0.0 exited $RC ($(cat "$T/err"))"
[ "$(git -C "$T/clone" rev-parse HEAD)" = "$v200_sha" ] || fail "(4b) offline update downgraded v2.0.0"

# (5) `coco install` stays pinned to PINNED_TAG (v1.10.0), and banner/help recommend @latest update.
set_remote_url "$T/remote.git"
mkdir -p "$T/install-cwd"
RC=0
(
  cd "$T/install-cwd"
  HOME="$T/home" XDG_CONFIG_HOME="$T/home/.config" GIT_CONFIG_GLOBAL="$T/home/.gitconfig" \
    COCO_NO_UPDATE_CHECK=1 node "$T/cli/bin/coco.js" install
) >"$T/inst.out" 2>"$T/inst.err" || RC=$?
[ "$RC" -eq 0 ] || fail "(5a) install exited $RC ($(cat "$T/inst.err"))"
[ "$(git -C "$T/install-cwd/coco" rev-parse HEAD)" = "$v110_sha" ] \
  || fail "(5a) install did not stay pinned to v1.10.0"
grep -q 'npx cocosuperintelligence@latest update' "$T/inst.out" \
  || fail "(5a) install hint missing @latest update ($(cat "$T/inst.out"))"

mkdir -p "$T/home/.coco"
node -e 'const fs=require("fs");fs.writeFileSync(process.argv[1],JSON.stringify({checkedAt:Date.now(),latest:"2.0.0"}));' \
  "$T/home/.coco/.update-check.json"
banner_out="$(env -u COCO_NO_UPDATE_CHECK HOME="$T/home" node "$T/cli/bin/coco.js" --help)"
printf '%s\n' "$banner_out" | grep -q 'Coco 2.0.0 is available' \
  || fail "(5b) cached update banner did not render"
[ "$(printf '%s\n' "$banner_out" | grep -c 'npx cocosuperintelligence@latest update')" -ge 2 ] \
  || fail "(5b) help + banner did not both recommend npx cocosuperintelligence@latest update"

echo "PASS: coco update resolves newest semver tag, ignores pre-releases, and stays safe offline"
