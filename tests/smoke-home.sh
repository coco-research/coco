#!/usr/bin/env bash
# Runs tests/smoke.sh with HOME pointed at a throwaway dir, per the task instructions.
set -uo pipefail
cd "$(dirname "$0")/.."
unset XDG_CONFIG_HOME APPDATA \
      CLAUDE_HOME CURSOR_HOME CLINE_HOME ROO_CODE_HOME CONTINUE_HOME \
      HERMES_PROFILES AMAZON_Q_HOME GROK_HOME COPILOT_HOME \
      WINDSURF_HOME ZED_HOME PI_AGENT_HOME AGENTS_HOME
PYTHONPATH="$(python3 -m site --user-site):${PYTHONPATH:-}" HOME=$(mktemp -d) bash tests/smoke.sh
