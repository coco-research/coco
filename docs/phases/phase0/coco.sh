#!/bin/bash
# CoCo — Conversational Terminal Assistant (Phase 0 POC)
# A joint creation by Rijul Kalra and Claude
#
# Usage:
#   ./coco.sh                    # Interactive mode (REPL)
#   ./coco.sh "research OAuth"   # Single command mode
#   echo "check email" | ./coco.sh  # Pipe mode

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYSTEM_PROMPT="$SCRIPT_DIR/coco-system-prompt.md"
COCO_HISTORY="$HOME/.coco_history"

# Colors
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
RESET='\033[0m'

# Ensure system prompt exists
if [[ ! -f "$SYSTEM_PROMPT" ]]; then
  echo "Error: System prompt not found at $SYSTEM_PROMPT"
  exit 1
fi

# Show context greeting
show_greeting() {
  local project_name branch status domain gsd_status

  project_name=$(basename "$(pwd)")
  branch=$(git branch --show-current 2>/dev/null || echo "no-git")

  if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
    status="clean"
  else
    status="dirty"
  fi

  if [[ -f "README.md" ]]; then
    domain=$(head -1 README.md | sed 's/^#\s*//')
  else
    domain="unknown"
  fi

  if [[ -d ".planning" ]]; then
    gsd_status="GSD: active"
  else
    gsd_status="GSD: inactive"
  fi

  echo -e "${BOLD}${CYAN}"
  echo "  ╭──────────────────────────────────────╮"
  echo "  │  CoCo                                │"
  echo "  ╰──────────────────────────────────────╯"
  echo -e "${RESET}"
  echo -e "  ${DIM}Project:${RESET} $project_name ($branch, $status)"
  echo -e "  ${DIM}Domain:${RESET}  $domain"
  echo -e "  ${DIM}$gsd_status${RESET}"
  echo ""
  echo -e "  ${BOLD}Ready.${RESET}"
  echo ""
}

# Dispatch a command to Claude
dispatch() {
  local input="$1"

  # Log to history
  echo "$(date '+%Y-%m-%d %H:%M:%S') | $input" >> "$COCO_HISTORY"

  # Build the prompt with system context
  local system_context
  system_context=$(cat "$SYSTEM_PROMPT")

  echo -e "${DIM}Dispatching...${RESET}"
  echo ""

  # Run claude with the system prompt and user input
  claude -p \
    --system-prompt "$system_context" \
    --output-format text \
    "$input"

  echo ""
}

# Notify on macOS when done (if not in interactive mode)
notify() {
  local msg="$1"
  if command -v osascript &>/dev/null; then
    osascript -e "display notification \"$msg\" with title \"CoCo\"" 2>/dev/null || true
  fi
}

# --- Main ---

# Single command mode: ./coco.sh "research OAuth patterns"
if [[ $# -gt 0 ]]; then
  dispatch "$*"
  notify "Done: $*"
  exit 0
fi

# Pipe mode: echo "check email" | ./coco.sh
if [[ ! -t 0 ]]; then
  input=$(cat)
  dispatch "$input"
  notify "Done: $input"
  exit 0
fi

# Interactive REPL mode
show_greeting

while true; do
  echo -ne "${CYAN}> ${RESET}"
  read -r input || break  # EOF (Ctrl+D) exits

  # Skip empty input
  [[ -z "$input" ]] && continue

  # Exit commands
  case "$input" in
    exit|quit|bye)
      echo -e "${DIM}CoCo signing off.${RESET}"
      break
      ;;
    history)
      if [[ -f "$COCO_HISTORY" ]]; then
        tail -20 "$COCO_HISTORY"
      else
        echo "No history yet."
      fi
      continue
      ;;
    help)
      echo ""
      echo "  CoCo understands natural language. Just tell me what you need:"
      echo ""
      echo "  ${BOLD}Build:${RESET}     \"develop the auth module\""
      echo "  ${BOLD}Fix:${RESET}       \"fix the login bug\""
      echo "  ${BOLD}Research:${RESET}  \"research OAuth patterns\""
      echo "  ${BOLD}Review:${RESET}    \"review the API code\""
      echo "  ${BOLD}Email:${RESET}     \"check my email\""
      echo "  ${BOLD}Present:${RESET}   \"create an ARB deck\""
      echo ""
      echo "  Or use any /team, /gsd, /pmstudio, /email command directly."
      echo ""
      echo "  ${DIM}Type 'exit' to quit, 'history' to see past commands.${RESET}"
      echo ""
      continue
      ;;
  esac

  dispatch "$input"
  notify "Done: $input"
  echo ""
done
