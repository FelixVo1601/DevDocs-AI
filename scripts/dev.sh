#!/usr/bin/env bash
# One-command local development (macOS/Linux)
# Usage (from repo root):  ./scripts/dev.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> DevDocs AI local stack"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi
if [[ ! -f frontend/.env ]]; then
  cp frontend/.env.example frontend/.env
  echo "Created frontend/.env from frontend/.env.example"
fi

echo "==> Starting Postgres (Docker Compose)"
docker compose up -d db

if [[ ! -d backend/.venv ]]; then
  echo "==> Creating backend venv"
  python3 -m venv backend/.venv
fi

# shellcheck disable=SC1091
source backend/.venv/bin/activate
echo "==> Installing backend deps + migrating"
pip install -q -r backend/requirements.txt
( cd backend && alembic upgrade head )

if [[ ! -d frontend/node_modules ]]; then
  echo "==> Installing frontend deps"
  ( cd frontend && npm install )
fi

cleanup() {
  echo ""
  echo "==> Stopping API and UI"
  kill "${API_PID:-}" "${UI_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> Starting API on http://localhost:8001"
( cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8001 ) &
API_PID=$!

echo "==> Starting UI on http://localhost:5173"
( cd frontend && npm run dev -- --host localhost --port 5173 ) &
UI_PID=$!

echo ""
echo "Ready:"
echo "  UI:      http://localhost:5173"
echo "  Register http://localhost:5173/register"
echo "  App:     http://localhost:5173/app  (requires login)"
echo "  API:     http://localhost:8001/docs"
echo "  Health:  http://localhost:8001/health"
echo ""
echo "Use localhost (not 127.0.0.1) in the browser so the session cookie works."
echo "Press Ctrl+C to stop."

wait
