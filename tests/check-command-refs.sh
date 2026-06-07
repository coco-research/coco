#!/usr/bin/env bash
# Guard: command cross-references must match the installer's naming contract.
#
# The Claude Code adapter (adapters/claude-code/install.sh) deploys
#   commands/<ns>/<name>.md  ->  ~/.claude/commands/<ns>:<name>.md   (colon)
#   commands/<ns>/_index.md  ->  ~/.claude/commands/<ns>.md          (router)
#
# So a router/command that references a sibling as "<ns>-<name>.md" (hyphen)
# points at a file that is never created — the reference silently fails at
# runtime and the feature degrades quietly. This check fails loudly instead.
#
# Run from repo root: bash tests/check-command-refs.sh

set -euo pipefail
cd "$(dirname "$0")/.."

fail=0

for ns_dir in commands/*/; do
  ns=$(basename "$ns_dir")

  # 1. Forbid hyphen-style sibling references — the installer never produces them.
  while IFS= read -r hit; do
    [ -z "$hit" ] && continue
    echo "  FORBIDDEN (hyphen ref in '$ns'): $hit — use ${hit/${ns}-/${ns}:}"
    fail=1
  done < <(grep -rhoE "\b${ns}-[a-z][a-z-]*\.md" "$ns_dir" 2>/dev/null | sort -u)

  # 2. Every colon-style reference must map to a real source command file.
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    name=${ref#"${ns}":}
    name=${name%.md}
    case "$name" in
      feedback-archive) continue ;;  # runtime write target, not a source command
    esac
    if [ ! -f "${ns_dir}${name}.md" ]; then
      echo "  DANGLING (in '$ns'): $ref -> commands/${ns}/${name}.md missing"
      fail=1
    fi
  done < <(grep -rhoE "\b${ns}:[a-z][a-z-]*\.md" "$ns_dir" 2>/dev/null | sort -u)
done

if [ "$fail" -ne 0 ]; then
  echo "FAIL: command cross-references broken."
  echo "      Installer maps commands/<ns>/<name>.md -> <ns>:<name>.md (colon)."
  exit 1
fi

echo "PASS: all command cross-references resolve."
