#!/usr/bin/env bash
# Smoke tests for Coco core scripts.
# Run from repo root: bash tests/smoke.sh

set -euo pipefail

cd "$(dirname "$0")/.."
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL+1)); }

echo "=== Smoke test: bin/coco.js (npm wrapper) ==="
node --check bin/coco.js && pass "bin/coco.js syntax check" || fail "bin/coco.js syntax error"
node bin/coco.js --help > /tmp/coco-help.out 2>&1 && pass "bin/coco.js --help runs" || fail "bin/coco.js --help failed"
grep -q "Coco" /tmp/coco-help.out && pass "bin/coco.js help output contains 'Coco'" || fail "bin/coco.js help output missing 'Coco'"

echo ""
echo "=== Smoke test: scripts/build-index.py ==="
python3 -c "import ast; ast.parse(open('scripts/build-index.py').read())" && pass "build-index.py parses" || fail "build-index.py syntax error"
python3 scripts/build-index.py > /tmp/build-index.out 2>&1 && pass "build-index.py runs" || fail "build-index.py failed"
test -f skills/INDEX.md && pass "skills/INDEX.md generated" || fail "skills/INDEX.md missing"
test -f commands/INDEX.md && pass "commands/INDEX.md generated" || fail "commands/INDEX.md missing"
test -f agents/INDEX.md && pass "agents/INDEX.md generated" || fail "agents/INDEX.md missing"
test -f docs/by-domain/pm.md && pass "docs/by-domain/pm.md generated" || fail "docs/by-domain/pm.md missing"

echo ""
echo "=== Smoke test: adapters dry-run ==="
for adapter in claude-code cursor codex generic; do
  bash adapters/$adapter/install.sh --dry-run > /tmp/$adapter.out 2>&1 \
    && pass "adapters/$adapter/install.sh --dry-run" \
    || fail "adapters/$adapter/install.sh --dry-run"
done

echo ""
echo "=== Smoke test: root install.sh ==="
bash install.sh --list > /tmp/list.out 2>&1 && pass "install.sh --list runs" || fail "install.sh --list failed"
bash install.sh --dry-run --adapter claude-code > /tmp/install-dry.out 2>&1 && pass "install.sh --dry-run" || fail "install.sh --dry-run"

echo ""
echo "=== Smoke test: frontmatter validity ==="
python3 <<'PY' && pass "all SKILL.md frontmatter parses" || fail "frontmatter parse errors"
import sys, pathlib, yaml
errors = []
for p in pathlib.Path('skills').glob('*/SKILL.md'):
    text = p.read_text()
    if not text.startswith('---'):
        errors.append(f'{p}: no frontmatter')
        continue
    parts = text.split('---', 2)
    if len(parts) < 3:
        errors.append(f'{p}: malformed frontmatter')
        continue
    try:
        yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        errors.append(f'{p}: yaml error — {e}')
sys.exit(1 if errors else 0)
PY

echo ""
echo "=== Smoke test: command cross-references ==="
bash tests/check-command-refs.sh && pass "command cross-references resolve" || fail "command cross-references broken"

echo ""
echo "=== Smoke test: /team evidence-gate integrity ==="
bash tests/check-evidence-gate.sh && pass "/team evidence-gate present" || fail "/team evidence-gate incomplete"

echo ""
echo "=== Summary ==="
echo "  passed: $PASS"
echo "  failed: $FAIL"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
