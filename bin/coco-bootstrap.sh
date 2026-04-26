#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/rkz91/coco.git"
INSTALL_DIR="${COCO_DIR:-$HOME/.coco}"

detect_adapter() {
  if command -v claude >/dev/null 2>&1; then
    echo "claude"
  elif command -v cursor >/dev/null 2>&1; then
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
  echo "Cloning Coco..."
  rm -rf "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

if [ ! -f "install.sh" ]; then
  echo "Error: install.sh not found."
  exit 1
fi

bash install.sh --adapter "$ADAPTER"

echo "Coco installed successfully at $INSTALL_DIR"