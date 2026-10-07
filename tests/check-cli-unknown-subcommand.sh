#!/usr/bin/env bash
# An unknown `coco` subcommand must fail before any git call: no clone, no ./coco (#268).
# A fake `git` on PATH records any call and fails, so this never touches the network.
set -euo pipefail

CLI="$(cd "$(dirname "$0")/.." && pwd)/bin/coco.js"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mkdir "$T/bin" "$T/cwd" "$T/home"
printf '#!/bin/sh\ntouch "%s/git-called"\nexit 1\n' "$T" > "$T/bin/git"
chmod +x "$T/bin/git"

rc=0
(cd "$T/cwd" && HOME="$T/home" COCO_NO_UPDATE_CHECK=1 PATH="$T/bin:$PATH" node "$CLI" doctor) >/dev/null 2>&1 || rc=$?

[ "$rc" -ne 0 ] || { echo "FAIL: 'coco doctor' exited 0"; exit 1; }
[ ! -e "$T/git-called" ] || { echo "FAIL: 'coco doctor' called git"; exit 1; }
[ ! -e "$T/cwd/coco" ] || { echo "FAIL: 'coco doctor' created ./coco"; exit 1; }
echo "PASS: unknown subcommand rejected before any clone"

# Positive control: leading flags must pass through to install. The fake git marks
# the call and fails, so a non-zero exit is expected here; the assertion is that
# git was reached at all.
rm -f "$T/git-called"
rc=0
(cd "$T/cwd" && HOME="$T/home" COCO_NO_UPDATE_CHECK=1 PATH="$T/bin:$PATH" node "$CLI" --adapter cursor) >/dev/null 2>&1 || rc=$?

[ -e "$T/git-called" ] || { echo "FAIL: 'coco --adapter cursor' never reached git"; exit 1; }
echo "PASS: leading flag reaches git"
