#!/usr/bin/env bash
# The generated indexes must be a function of the commit, not of the working tree.
#
# An untracked leftover directory used to be indexed as if it shipped: a stale
# systems/<name>/ produced a phantom bundle row in systems/INDEX.md, which showed up
# as "INDEX files are out of date" in CI on twenty separate branches whose authors
# had not touched the index at all. This test pins that shut.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "SKIP: not a git checkout, so there is nothing to compare against."
  exit 0
fi

# Probe directories are named so they cannot collide with a real bundle or skill.
PROBE_SYS="systems/zz-index-probe"
PROBE_SKILL="skills/zz-index-probe"

cleanup() {
  rm -rf "$PROBE_SYS" "$PROBE_SKILL"
  python3 scripts/build-index.py >/dev/null 2>&1 || true
}
trap cleanup EXIT

python3 scripts/build-index.py >/dev/null

before_systems="$(git hash-object systems/INDEX.md)"
before_skills="$(git hash-object skills/INDEX.md)"

mkdir -p "$PROBE_SYS" "$PROBE_SKILL"
echo "Not part of the distributable." > "$PROBE_SYS/README.md"
cat > "$PROBE_SKILL/SKILL.md" <<'EOF'
---
name: zz-index-probe
description: "Use when this test runs. A probe that must never be indexed."
---
# Probe
EOF

python3 scripts/build-index.py >/dev/null

after_systems="$(git hash-object systems/INDEX.md)"
after_skills="$(git hash-object skills/INDEX.md)"

fail=0
if [ "$before_systems" != "$after_systems" ]; then
  echo "FAIL: an untracked systems/ directory changed systems/INDEX.md"
  git diff --stat systems/INDEX.md || true
  fail=1
fi
if [ "$before_skills" != "$after_skills" ]; then
  echo "FAIL: an untracked skills/ directory changed skills/INDEX.md"
  git diff --stat skills/INDEX.md || true
  fail=1
fi
if grep -q 'zz-index-probe' systems/INDEX.md skills/INDEX.md; then
  echo "FAIL: the probe was indexed"
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS: generated indexes ignore untracked files."
fi
exit "$fail"
