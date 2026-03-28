#!/bin/bash
# CoCo Platform — Development Server
set -e

cd "$(dirname "$0")/.."

echo "Starting CoCo Platform (dev mode)..."

# Start backend
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start frontend
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

echo ""
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  Health:   http://localhost:8000/api/health"
echo ""

wait
