#!/bin/bash
set -e
cd "$(dirname "$0")/.."

echo "Building CoCo Platform..."

# Build frontend
cd frontend
npm run build
cd ..

# Copy to backend static
rm -rf backend/static
cp -r frontend/dist backend/static

# Start server
echo "Starting CoCo Platform at http://localhost:8000"
cd backend
exec uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
