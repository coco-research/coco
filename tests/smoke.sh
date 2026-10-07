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
for d in adapters/*/; do
  adapter=$(basename "$d")
  bash "adapters/$adapter/install.sh" --dry-run > "/tmp/$adapter.out" 2>&1 \
    && pass "adapters/$adapter/install.sh --dry-run" \
    || fail "adapters/$adapter/install.sh --dry-run"
done

bash adapters/cursor/install.sh --dry-run --systems superintelligence > /tmp/cursor-systems.out 2>&1 \
  && pass "cursor install.sh --dry-run --systems superintelligence" \
  || fail "cursor install.sh --dry-run --systems superintelligence"

echo ""
echo "=== Smoke test: cursor --systems superintelligence ==="
# Repro: cursor install.sh used to reject --systems (Unknown flag / exit 1), so the
# README flagship command died whenever ~/.cursor existed. Must write SI-Decide.md
# into CURSOR_HOME/commands, not ~/.claude/commands.
bash tests/cursor-si-commands.sh && pass "cursor --systems superintelligence writes SI-Decide.md" || fail "cursor --systems superintelligence did not write SI-Decide.md"

echo ""
echo "=== Smoke test: aider .aider.conf.yml keys ==="
bash tests/aider-conf-keys.sh && pass "aider .aider.conf.yml uses only real aider option keys" || fail "aider .aider.conf.yml has keys aider does not recognize"

echo ""
echo "=== Smoke test: grok --uninstall ==="
bash tests/grok-uninstall.sh && pass "grok --uninstall removes generated files and keeps user files" || fail "grok --uninstall left generated files or removed user files"

echo ""
echo "=== Smoke test: aider AGENTS.md agent descriptions ==="
bash tests/aider-agent-desc.sh && pass "aider AGENTS.md carries full agent descriptions" || fail "aider AGENTS.md truncates agent descriptions"

echo ""
echo "=== Smoke test: root install.sh ==="
bash install.sh --list > /tmp/list.out 2>&1 && pass "install.sh --list runs" || fail "install.sh --list failed"
bash install.sh --dry-run --adapter claude-code > /tmp/install-dry.out 2>&1 && pass "install.sh --dry-run" || fail "install.sh --dry-run"
# The root installer forwards --core-only to any adapter whose manifest names bundles;
# six adapters used to reject it with "Unknown flag" and exit 1.
for d in adapters/*/; do
  adapter=$(basename "$d")
  bash install.sh --adapter "$adapter" --core-only --dry-run > "/tmp/core-only-$adapter.out" 2>&1 \
    && pass "install.sh --adapter $adapter --core-only" \
    || fail "install.sh --adapter $adapter --core-only"
done

echo ""
echo "=== Smoke test: CLAUDE.md rules block ==="
bash tests/check-claude-md-block.sh && pass "rules block never damages CLAUDE.md" || fail "rules block damaged CLAUDE.md"

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
echo "=== Smoke test: systems/gsd/ context-loading references ==="
bash tests/check-gsd-refs.sh && pass "systems/gsd/ references resolve" || fail "systems/gsd/ references broken"

echo ""
echo "=== Smoke test: /team evidence-gate integrity ==="
bash tests/check-evidence-gate.sh && pass "/team evidence-gate present" || fail "/team evidence-gate incomplete"

echo ""
echo "=== Smoke test: security surface ==="
bash tests/check-security-surface.sh && pass "security-surface checks" || fail "security-surface checks"

echo ""
echo "=== Smoke test: aider installer backs up existing files ==="
bash tests/aider-backup.sh && pass "aider installer backs up existing AGENTS.md and .aider.conf.yml" || fail "aider installer overwrote existing files without a backup"

echo ""
echo "=== Smoke test: generic/codex clone guard (issue #238) ==="
bash tests/generic-clone-guard.sh && pass "clone guard refuses in-repo AGENTS.md writes" || fail "clone guard let an in-repo write through"

echo "=== Smoke test: generic adapter ships SI commands and front doors ==="
bash tests/generic-si-commands.sh && pass "generic first-run install ships the SI command family and front doors" || fail "generic first-run install missing the SI command family or front doors"

echo ""
echo "=== Summary ==="
echo "  passed: $PASS"
echo "  failed: $FAIL"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
