#!/usr/bin/env bash
# Guard: the install / skill / brainstorm surface must not re-grow the holes
# this PR closed. Run from repo root: bash tests/check-security-surface.sh
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
pass() { echo "  PASS: $1"; }
fail_() { echo "  FAIL: $1"; fail=1; }

echo "=== generate_prd.sh: no eval of user input ==="
if grep -F "eval \"\$var_name=" skills/prd-generator/scripts/generate_prd.sh >/dev/null; then
  fail_ "generate_prd.sh still evals \$var_name"
else
  pass "no eval assignment"
fi
if grep -F "printf -v \"\$var_name\"" skills/prd-generator/scripts/generate_prd.sh >/dev/null; then
  pass "uses printf -v"
else
  fail_ "generate_prd.sh does not use printf -v"
fi

echo ""
echo "=== generate_prd.sh: quoted payload stored, not executed ==="
tmp="$(mktemp -d "${TMPDIR:-/tmp}/prd-sec.XXXXXX")"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT

awk '
  /^prompt_input\(\)/ {p=1}
  p {print}
  p && /^}/ {exit}
' skills/prd-generator/scripts/generate_prd.sh > "$tmp/fn.sh"

cat > "$tmp/run.sh" <<'EOS'
#!/bin/bash
YELLOW=""; RED=""; NC=""
# shellcheck disable=SC1091
source "$(dirname "$0")/fn.sh"
marker="$1/PWNED"
payload="'; echo PWNED > '$marker'; x='"
# Here-string keeps prompt_input in this shell (a pipe would subshell it).
prompt_input "Feature/Product Name:" PRODUCT_NAME true >/dev/null <<<"$payload"
if [[ -f "$marker" ]]; then
  echo "EXECUTED"
  exit 2
fi
if [[ "$PRODUCT_NAME" == "$payload" ]]; then
  echo "STORED"
  exit 0
fi
printf 'UNEXPECTED:%s\n' "$PRODUCT_NAME"
exit 1
EOS

result="$(bash "$tmp/run.sh" "$tmp" 2>/dev/null || true)"
if [[ "$result" == "STORED" ]]; then
  pass "payload stored as a string"
elif [[ "$result" == "EXECUTED" ]]; then
  fail_ "payload executed via eval"
else
  fail_ "prompt_input did not store payload (got: ${result:-empty})"
fi

echo ""
echo "=== stop-server.sh: canonicalize before /tmp check ==="
if grep -F '[[ "$SCREEN_DIR" == /tmp/* ]]' skills/brainstorming/scripts/stop-server.sh >/dev/null; then
  fail_ "stop-server.sh still uses uncanonicalized /tmp/* glob"
else
  pass "no uncanonicalized /tmp/* glob"
fi
if grep -F 'pwd -P' skills/brainstorming/scripts/stop-server.sh >/dev/null; then
  pass "canonicalizes with pwd -P"
else
  fail_ "stop-server.sh does not canonicalize"
fi

echo ""
echo "=== stop-server.sh: /tmp/../ traversal is not deleted ==="
victim="$(mktemp -d "${TMPDIR:-/tmp}/stop-victim.XXXXXX")"
echo keep > "$victim/keep.txt"
# `/tmp/../<abs>` is a glob match for /tmp/* and used to rm -rf the resolved dir.
traversal="/tmp/..${victim}"
set +e
bash skills/brainstorming/scripts/stop-server.sh "$traversal" >/dev/null 2>&1
set -e
if [[ -f "$victim/keep.txt" ]]; then
  pass "traversal did not delete victim dir"
else
  fail_ "stop-server.sh deleted $victim via $traversal"
fi
rm -rf "$victim"

echo ""
echo "=== uninstall: exact clone-path prefix, not contains-match ==="
if grep -F '*${dir}*' bin/coco.js >/dev/null; then
  fail_ "bin/coco.js still contains-matches clone path"
else
  pass "bin/coco.js does not contains-match"
fi
if grep -RInF --exclude-dir=.git 'lname "*$(pwd)*"' README.md docs adapters Formula >/dev/null; then
  fail_ "docs still use *\$(pwd)* contains-match"
else
  pass "docs do not use *\$(pwd)* contains-match"
fi
if grep -F 'lname "*/coco/*"' adapters/vscode/README.md >/dev/null; then
  fail_ "vscode README still uses */coco/* contains-match"
else
  pass "vscode README does not use */coco/*"
fi

# Behavioral: a contains-match would also hit coco-research. Prefix + slash must not.
home="$tmp/home"
mkdir -p "$home/skills" "$tmp/coco/skills/foo" "$tmp/coco-research/skills/bar"
ln -s "$tmp/coco/skills/foo" "$home/skills/foo"
ln -s "$tmp/coco-research/skills/bar" "$home/skills/bar"
prefix="$tmp/coco/"
find "$home" -type l -lname "${prefix}*" -delete
if [[ -L "$home/skills/bar" && ! -L "$home/skills/foo" ]]; then
  pass "find prefix deletes coco links, keeps coco-research"
else
  fail_ "find prefix matched the wrong clone (foo=$(test -L "$home/skills/foo" && echo yes || echo no) bar=$(test -L "$home/skills/bar" && echo yes || echo no))"
fi

echo ""
echo "=== skills: no curl|sh, no npx skills add -y ==="
if grep -RInE 'curl[[:space:]].+\|[[:space:]]*sh' \
     skills/browser-automation/SKILL.md \
     skills/ai-marketing-videos/SKILL.md >/dev/null; then
  fail_ "skill still pipes curl to sh"
else
  pass "no curl|sh in gated skills"
fi
if grep -RInE 'npx skills add .+-y' skills --include='SKILL.md' >/dev/null; then
  fail_ "a skill still passes -y to npx skills add"
else
  pass "no npx skills add -y"
fi

echo ""
echo "=== clone is pinned to a release tag ==="
if grep -F 'PINNED_TAG' bin/coco.js >/dev/null; then
  pass "bin/coco.js has PINNED_TAG"
else
  fail_ "bin/coco.js has no PINNED_TAG"
fi
pkg_ver="$(python3 -c "import json;print(json.load(open('package.json'))['version'])")"
if grep -F "PINNED_TAG=\"v${pkg_ver}\"" bin/coco-bootstrap.sh >/dev/null; then
  pass "bootstrap pin matches package.json ($pkg_ver)"
else
  fail_ "bootstrap PINNED_TAG does not match package.json $pkg_ver"
fi
if grep -F "'--branch', PINNED_TAG" bin/coco.js >/dev/null \
   || grep -F '"--branch", PINNED_TAG' bin/coco.js >/dev/null; then
  pass "fresh clone uses --branch PINNED_TAG"
else
  fail_ "fresh clone is not pinned with --branch PINNED_TAG"
fi

echo ""
echo "=== Summary ==="
if [[ "$fail" -eq 0 ]]; then
  echo "  all security-surface checks passed"
  exit 0
fi
echo "  some check(s) failed"
exit 1
