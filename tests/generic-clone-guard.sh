#!/usr/bin/env bash
# Issue #238: README's `git clone ... && cd coco && bash install.sh` path
# auto-detects generic and used to overwrite the Coco checkout's own tracked
# AGENTS.md. The codex/generic adapter must refuse when the resolved output
# directory is inside the checkout (except --dry-run, which only warns).
#
# Tests the working tree (uncommitted changes included) in a throwaway copy;
# never runs an installer against this real repo root. Cleans up after itself.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/coco-clone-guard.XXXXXX")"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT

fail() { echo "FAIL: $1"; exit 1; }

mkdir -p "$tmp/proj/coco" "$tmp/home"

# Copy the working tree (git clone would miss uncommitted changes); then make the
# copy a git repo with AGENTS.md tracked, so `git status` can prove it stays clean.
# One tar reads the NUL-separated list from stdin: xargs would split a large
# list into several `tar -cf -` runs whose concatenated archives make the
# extractor stop at the first end-of-archive marker (SIGPIPE on Linux).
(
  cd "$ROOT" || exit 1
  git ls-files -z --cached --others --exclude-standard |
    while IFS= read -r -d '' f; do
      if [ -e "$f" ] || [ -L "$f" ]; then printf '%s\0' "$f"; fi
    done |
    tar --null -T - -cf -
) | tar -xf - -C "$tmp/proj/coco" ||
  fail "setup: failed to copy the working tree into $tmp/proj/coco"
git -C "$tmp/proj/coco" init -q
git -C "$tmp/proj/coco" add -A
git -C "$tmp/proj/coco" -c user.email=t@t -c user.name=t commit -qm base

# Clean environment: no detector dirs, no codex on PATH.
BASH_BIN="$(command -v bash)"
CLEAN_PATH="/usr/bin:/bin:/usr/sbin:/sbin"
for tool in python3 git bash node; do
  p="$(command -v "$tool" 2>/dev/null || true)"
  [ -n "$p" ] || continue
  d="$(cd "$(dirname "$p")" && pwd -P)"
  case ":$CLEAN_PATH:" in *":$d:"*) ;; *) CLEAN_PATH="$CLEAN_PATH:$d" ;; esac
done
if PATH="$CLEAN_PATH" command -v codex >/dev/null 2>&1; then
  mkdir -p "$tmp/bin"
  for tool in python3 git bash node; do
    p="$(command -v "$tool" 2>/dev/null || true)"
    [ -n "$p" ] || continue
    ln -sf "$p" "$tmp/bin/$(basename "$p")"
  done
  CLEAN_PATH="$tmp/bin:/usr/bin:/bin:/usr/sbin:/sbin"
fi

run() {  # run <dir> <cmd...> with a clean env in <dir>
  local dir=$1
  shift
  ( cd "$dir" && env -u CLAUDECODE -u CLAUDE_HOME -u CURSOR_HOME -u COCO_HOME -u XDG_CONFIG_HOME \
      HOME="$tmp/home" PATH="$CLEAN_PATH" "$@" )
}

clone_clean() {
  local dirty
  dirty="$(git -C "$tmp/proj/coco" status --porcelain)"
  [ -z "$dirty" ] || fail "$1: clone is dirty: $dirty"
}

no_backup() {
  if compgen -G "$tmp/proj/coco/AGENTS.md.backup-*" >/dev/null; then
    fail "$1: AGENTS.md.backup-* written inside the clone"
  fi
}

refuse_case() {  # refuse_case <name> <dir> <cmd...>
  local name=$1 dir=$2 status=0 out
  shift 2
  out="$(run "$dir" "$@" 2>&1)" || status=$?
  [ "$status" -ne 0 ] || fail "$name: expected non-zero exit, got 0"
  case "$out" in
    *refus*) ;;
    *) fail "$name: output does not mention refusing: $out" ;;
  esac
  case "$out" in
    *"project directory"*) ;;
    *) fail "$name: output does not mention the project directory: $out" ;;
  esac
  clone_clean "$name"
  no_backup "$name"
}

# Case 1: README path, auto-detect -> generic -> must refuse.
refuse_case "case 1 (auto-detect inside clone)" "$tmp/proj/coco" "$BASH_BIN" install.sh

# Case 2: explicit --adapter generic -> must refuse.
refuse_case "case 2 (--adapter generic)" "$tmp/proj/coco" "$BASH_BIN" install.sh --adapter generic

# Case 3: explicit --adapter codex -> must refuse.
refuse_case "case 3 (--adapter codex)" "$tmp/proj/coco" "$BASH_BIN" install.sh --adapter codex

# Case 4: --dry-run stays green and says a real run would refuse.
status=0
out="$(run "$tmp/proj/coco" "$BASH_BIN" install.sh --dry-run 2>&1)" || status=$?
[ "$status" -eq 0 ] || fail "case 4 (--dry-run): expected exit 0, got $status: $out"
case "$out" in
  *"would refuse"*) ;;
  *) fail "case 4 (--dry-run): no 'would refuse' note: $out" ;;
esac
clone_clean "case 4 (--dry-run)"
no_backup "case 4 (--dry-run)"

# Case 5: regression, install from the project dir next to the clone.
status=0
out="$(run "$tmp/proj" "$BASH_BIN" coco/install.sh 2>&1)" || status=$?
[ "$status" -eq 0 ] || fail "case 5 (project dir): expected exit 0, got $status: $out"
[ -f "$tmp/proj/AGENTS.md" ] || fail "case 5 (project dir): $tmp/proj/AGENTS.md was not written"
clone_clean "case 5 (project dir)"

# Case 6: regression, an existing AGENTS.md outside the clone is still backed up.
mkdir -p "$tmp/proj2"
printf 'hand-written\n' > "$tmp/proj2/AGENTS.md"
status=0
out="$(run "$tmp/proj2" "$BASH_BIN" "$tmp/proj/coco/install.sh" 2>&1)" || status=$?
[ "$status" -eq 0 ] || fail "case 6 (backup outside clone): expected exit 0, got $status: $out"
[ -f "$tmp/proj2/AGENTS.md" ] || fail "case 6 (backup outside clone): AGENTS.md missing after install"
compgen -G "$tmp/proj2/AGENTS.md.backup-*" >/dev/null || fail "case 6 (backup outside clone): backup not created"
grep -q 'hand-written' "$tmp/proj2"/AGENTS.md.backup-* || fail "case 6 (backup outside clone): backup lost the original content"
clone_clean "case 6 (backup outside clone)"

# Case 7: -o pointing anywhere inside the checkout is refused too.
mkdir -p "$tmp/proj/coco/sub"
refuse_case "case 7 (-o inside checkout)" "$tmp/proj/coco" "$BASH_BIN" "$tmp/proj/coco/adapters/codex/install.sh" -o "$tmp/proj/coco/sub/AGENTS.md"
[ ! -f "$tmp/proj/coco/sub/AGENTS.md" ] || fail "case 7 (-o inside checkout): sub/AGENTS.md was written"
if compgen -G "$tmp/proj/coco/sub/AGENTS.md.backup-*" >/dev/null; then
  fail "case 7 (-o inside checkout): sub/AGENTS.md.backup-* written"
fi
clone_clean "case 7 (-o inside checkout)"

echo "PASS: generic/codex clone guard (cases 1-7)"
