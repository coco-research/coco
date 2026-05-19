#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/rkz91/coco.git"
INSTALL_DIR="${COCO_DIR:-$HOME/.coco}"

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

ADAPTER="${COCO_ADAPTER:-$(detect_adapter)}"

echo "Installing Coco..."
echo "Adapter: $ADAPTER"
echo "Install directory: $INSTALL_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required but not installed."
  exit 1
fi

if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Coco already exists. Updating..."
  git -C "$INSTALL_DIR" pull
else
  if [ -e "$INSTALL_DIR" ]; then
    echo "Error: $INSTALL_DIR already exists but is not a Coco clone."
    echo "Remove it manually or set COCO_DIR to a different path."
    exit 1
  fi
  echo "Cloning Coco..."
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [ ! -f "install.sh" ]; then
  echo "Error: install.sh not found."
  exit 1
fi

bash install.sh --adapter "$ADAPTER"

echo "Coco installed successfully at $INSTALL_DIR"
