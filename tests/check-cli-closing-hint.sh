#!/usr/bin/env bash
# The install's closing hint must not claim `update` re-runs the install (#253).
# A fake `git` makes the "clone" a stub dir with a no-op install.sh: no network, no real install.
set -euo pipefail

CLI="$(cd "$(dirname "$0")/.." && pwd)/bin/coco.js"
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mkdir "$T/bin" "$T/cwd" "$T/home"
cat > "$T/bin/git" <<'G'
#!/bin/sh
for a; do d="$a"; done
mkdir -p "$d" && echo 'exit 0' > "$d/install.sh"
G
chmod +x "$T/bin/git"

out=$(cd "$T/cwd" && HOME="$T/home" COCO_NO_UPDATE_CHECK=1 PATH="$T/bin:$PATH" node "$CLI" install 2>&1)

echo "$out" | grep -q 'npx cocosuperintelligence install' || { echo "FAIL: hint does not name 'install' for re-installing"; echo "$out"; exit 1; }
! echo "$out" | grep -qi 're-run install / update' || { echo "FAIL: hint still says update re-runs install"; exit 1; }
echo "PASS: closing hint is truthful"
