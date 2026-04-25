#!/usr/bin/env bash
# Generic adapter — produces AGENTS.md for any tool that reads it.
# Aider, Continue, Windsurf, Cline, and others all consume AGENTS.md.
#
# Identical behavior to adapters/codex/install.sh — Codex is the
# canonical AGENTS.md consumer; this exists for clarity for users
# of other tools.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec bash "$REPO_ROOT/adapters/codex/install.sh" "$@"
