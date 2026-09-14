#!/usr/bin/env bash
# Coco Learning System — Observation Capture Hook
# Captures tool use events and appends to project-scoped observations.jsonl
#
# Usage (called by Claude Code hook system):
#   bash observe.sh <event_type> <tool_name> [input_summary] [output_summary]
#
# Environment:
#   COCO_LEARNING_DISABLED=1  — skip all capture
#   COCO_LEARNING_DIR         — override base dir (default: ~/.coco/learning)

set -euo pipefail

# Opt-out check
if [[ "${COCO_LEARNING_DISABLED:-}" == "1" ]]; then
  exit 0
fi

EVENT="${1:-unknown}"
TOOL="${2:-unknown}"
INPUT_SUMMARY="${3:-}"
OUTPUT_SUMMARY="${4:-}"

BASE_DIR="${COCO_LEARNING_DIR:-$HOME/.coco/learning}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SESSION_ID="${CLAUDE_SESSION_ID:-${CLAUDECODE_SESSION_ID:-unknown}}"

# Detect project context from git
PROJECT_ID=""
PROJECT_NAME=""
if command -v git &>/dev/null; then
  GIT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")
  if [[ -n "$GIT_REMOTE" ]]; then
    CLEAN_REMOTE=$(echo "$GIT_REMOTE" | sed 's|://[^@]*@|://|' | sed 's|/$||')
    PROJECT_ID=$(echo -n "$CLEAN_REMOTE" | shasum -a 256 | cut -c1-12)
    PROJECT_NAME=$(basename "$CLEAN_REMOTE" .git 2>/dev/null || echo "unknown")
  else
    REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
    if [[ -n "$REPO_ROOT" ]]; then
      PROJECT_ID=$(echo -n "$REPO_ROOT" | shasum -a 256 | cut -c1-12)
      PROJECT_NAME=$(basename "$REPO_ROOT")
    fi
  fi
fi

# Skip if no project context detected
if [[ -z "$PROJECT_ID" ]]; then
  exit 0
fi

# Truncate summaries to prevent unbounded JSONL growth
MAX_LEN=500
if [[ ${#INPUT_SUMMARY} -gt $MAX_LEN ]]; then
  INPUT_SUMMARY="${INPUT_SUMMARY:0:$MAX_LEN}..."
fi
if [[ ${#OUTPUT_SUMMARY} -gt $MAX_LEN ]]; then
  OUTPUT_SUMMARY="${OUTPUT_SUMMARY:0:$MAX_LEN}..."
fi

# Build JSON observation
OBS_DIR="$BASE_DIR/projects/$PROJECT_ID"
mkdir -p "$OBS_DIR"
OBS_FILE="$OBS_DIR/observations.jsonl"

escape_json() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  printf '%s' "$s"
}

INPUT_ESC=$(escape_json "$INPUT_SUMMARY")
OUTPUT_ESC=$(escape_json "$OUTPUT_SUMMARY")
TOOL_ESC=$(escape_json "$TOOL")
SESSION_ESC=$(escape_json "$SESSION_ID")
PROJ_NAME_ESC=$(escape_json "$PROJECT_NAME")

printf '{"timestamp":"%s","event":"%s","session":"%s","tool":"%s","input_summary":"%s","output_summary":"%s","project_id":"%s","project_name":"%s"}\n' \
  "$TIMESTAMP" "$EVENT" "$SESSION_ESC" "$TOOL_ESC" "$INPUT_ESC" "$OUTPUT_ESC" "$PROJECT_ID" "$PROJ_NAME_ESC" \
  >> "$OBS_FILE"