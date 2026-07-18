#!/usr/bin/env bash
# coco-bootstrap.sh — one-shot installer
#
# Usage:
#   bash <(curl -fsSL https://raw.githubusercontent.com/rkz91/coco/main/bin/coco-bootstrap.sh)
#   bash <(curl -fsSL ...) -- --adapter cursor --systems gsd
#   bash <(curl -fsSL ...) -- --dry-run
#   COCO_DIR=~/tools/coco bash <(curl -fsSL ...)
#
# Flags (passed through to install.sh after --, or set via env):
#   --adapter <name>    claude-code | cursor | codex | generic
#   --systems <list>    e.g. gsd,brain,team
#   --dry-run           preview only, no writes
#   --yes               skip the commit-verification prompt (for CI/scripted installs)
#
# Security:
#   This script does NOT execute anything from the network directly. It uses
#   `git clone` to fetch the full repository (TLS-verified), then pauses so
#   you can inspect the commit hash before proceeding.
#   To skip the pause in CI, set COCO_BOOTSTRAP_YES=1 or pass --yes.
set -euo pipefail

REPO_URL="https://github.com/rkz91/coco.git"
INSTALL_DIR="${COCO_DIR:-$HOME/.coco}"
YES="${COCO_BOOTSTRAP_YES:-}"
PASS_THROUGH=()

# Parse our own flags; collect the rest for install.sh
while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes|-y) YES=1 ;;
    --dry-run|--adapter|--systems)
      PASS_THROUGH+=("$1")
      [[ "$1" != "--dry-run" ]] && { shift; PASS_THROUGH+=("$1"); }
      ;;
    --) shift; PASS_THROUGH+=("$@"); break ;;
    *) PASS_THROUGH+=("$1") ;;
  esac
  shift
done

detect_adapter() {
  if [[ -n "${CLAUDECODE:-}" || -d "$HOME/.claude/skills" ]]; then
    echo "claude-code"
  elif [[ -d "$HOME/.cursor" ]]; then
    echo "cursor"
  elif command -v codex >/dev/null 2>&1; then
    echo "codex"
  else
    echo "generic"
  fi
}

# Inject --adapter if not already in pass-through args
if ! printf '%s\0' "${PASS_THROUGH[@]+"${PASS_THROUGH[@]}"}" | grep -qz -- '--adapter'; then
  PASS_THROUGH=("--adapter" "$(detect_adapter)" "${PASS_THROUGH[@]+"${PASS_THROUGH[@]}"}")
fi

echo "Coco bootstrap"
echo "Install directory: $INSTALL_DIR"
echo "Adapter: $(printf '%s\n' "${PASS_THROUGH[@]+"${PASS_THROUGH[@]}"}" | grep -A1 '\-\-adapter' | tail -1 || echo auto)"

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required but not installed." >&2
  exit 1
fi

# ── Clone or update ──────────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Coco already exists at $INSTALL_DIR. Pulling latest..."
  git -C "$INSTALL_DIR" pull --ff-only
else
  if [ -e "$INSTALL_DIR" ]; then
    echo "Error: $INSTALL_DIR exists but is not a Coco clone." >&2
    echo "Remove it manually or set COCO_DIR to a different path." >&2
    exit 1
  fi
  echo "Cloning Coco..."
  git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi

# ── Commit verification gate ─────────────────────────────────────────────────
COMMIT_HASH="$(git -C "$INSTALL_DIR" rev-parse HEAD)"
COMMIT_DATE="$(git -C "$INSTALL_DIR" log -1 --format='%ci' HEAD)"
COMMIT_MSG="$(git -C "$INSTALL_DIR" log -1 --format='%s' HEAD)"

echo ""
echo "┌─ Verify before you run ──────────────────────────────────────────────┐"
echo "│  Commit : $COMMIT_HASH"
echo "│  Date   : $COMMIT_DATE"
echo "│  Message: $COMMIT_MSG"
echo "│"
echo "│  Confirm this matches the latest release on GitHub:"
echo "│  https://github.com/rkz91/coco/commits/main"
echo "└──────────────────────────────────────────────────────────────────────┘"
echo ""

if [[ -z "$YES" ]]; then
  read -r -p "Proceed with installation? [y/N] " REPLY
  case "$REPLY" in
    [yY][eE][sS]|[yY]) ;;
    *)
      echo "Aborted. The clone is at $INSTALL_DIR — inspect it, then run:"
      echo "  bash \"$INSTALL_DIR/install.sh\" ${PASS_THROUGH[*]+"${PASS_THROUGH[*]}"}"
      exit 0
      ;;
  esac
fi

# ── Install ──────────────────────────────────────────────────────────────────
if [ ! -f "$INSTALL_DIR/install.sh" ]; then
  echo "Error: install.sh not found in cloned repo." >&2
  exit 1
fi

bash "$INSTALL_DIR/install.sh" "${PASS_THROUGH[@]+"${PASS_THROUGH[@]}"}"

echo ""
echo "Coco installed successfully at $INSTALL_DIR"
echo "Commit: $COMMIT_HASH"
