#!/usr/bin/env bash
set -euo pipefail

echo "╔══════════════════════════════════════╗"
echo "║     CoCo Platform — Setup            ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Detect OS
OS="$(uname -s)"
case "$OS" in
  Darwin) echo "→ macOS detected" ;;
  Linux)  echo "→ Linux detected" ;;
  *)      echo "⚠ Unsupported OS: $OS (continuing anyway)" ;;
esac

# Check prerequisites
check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    echo "✗ $1 not found. $2"
    return 1
  fi
  echo "✓ $1 found"
}

echo ""
echo "Checking prerequisites..."
check_cmd python3 "Install Python 3.11+ from python.org"
check_cmd node "Install Node.js 18+ from nodejs.org"
check_cmd pnpm "Install: npm install -g pnpm"
check_cmd uv "Install: curl -LsSf https://astral.sh/uv/install.sh | sh"

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p ~/.coco ~/.hub
echo "✓ ~/.coco and ~/.hub created"

# Backend setup
echo ""
echo "Setting up backend..."
cd backend
uv sync
cd ..
echo "✓ Backend dependencies installed"

# Frontend setup
echo ""
echo "Setting up frontend..."
cd frontend
pnpm install
cd ..
echo "✓ Frontend dependencies installed"

# Environment
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓ .env created from template"
else
  echo "→ .env already exists, skipping"
fi

# Local config
if [ ! -f CLAUDE.local.md ]; then
  cp CLAUDE.local.md.template CLAUDE.local.md
  echo "✓ CLAUDE.local.md created from template"
else
  echo "→ CLAUDE.local.md already exists, skipping"
fi

# Initialize database
echo ""
echo "Initializing database..."
cd backend
uv run python -c "from app.db.init_db import init_platform_db; init_platform_db(); print('✓ platform.db initialized')"
cd ..

# Edition info
EDITION="${COCO_EDITION:-core}"
echo ""
echo "╔══════════════════════════════════════╗"
echo "║     Setup Complete!                   ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "Edition: $EDITION"
echo ""
echo "To start:"
echo "  ./scripts/dev.sh          # Development (hot reload)"
echo "  ./scripts/start.sh        # Production"
echo ""
if [ "$EDITION" = "core" ]; then
  echo "To enable Studio features (voice, replay, AI):"
  echo "  export COCO_EDITION=studio"
  echo "  # Add to .env for persistence"
fi
