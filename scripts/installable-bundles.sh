#!/usr/bin/env bash
# Print the bundles installed by default, comma-separated on one line.
#
# This is an explicit allow-list, not a scan of systems/. A scan would silently
# add any bundle that ships a SKILL.md or an agent as soon as it landed under
# systems/ — including systems/reverse-skill, a vendored reverse-engineering and
# security-testing bundle that must never be part of a default install. Naming
# the bundles here means adding one to the default set is a reviewed, one-line
# change to this file rather than an automatic side effect of adding a directory.
#
# reverse-skill is deliberately absent. It stays installable on request via
# --systems reverse-skill (see adapters/pi-desktop/install.sh --help), which the
# allow-list below has no effect on.
#
# tests/check-default-bundle-allowlist.sh gates this file: it fails if a bundle
# under systems/ ships something installable but is not accounted for here,
# so a new bundle cannot silently join (or silently fail to join) the default.
#
# Usage:
#   bash scripts/installable-bundles.sh                # prints "brain,cognee,..."
#   bash scripts/installable-bundles.sh --one-per-line

set -euo pipefail

ONE_PER_LINE=0
[[ "${1:-}" == "--one-per-line" ]] && ONE_PER_LINE=1

# Keep in sync with tests/check-default-bundle-allowlist.sh and with the
# supports_systems lists in adapters/*/manifest.json.
DEFAULT_BUNDLES=(gsd brain cognee hyperframes superintelligence m0)

if [[ "$ONE_PER_LINE" -eq 1 ]]; then
  printf '%s\n' "${DEFAULT_BUNDLES[@]}"
else
  ( IFS=,; printf '%s\n' "${DEFAULT_BUNDLES[*]}" )
fi
