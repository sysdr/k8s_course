#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
cd "$BASE_DIR"

echo "Starting local FinOps demo (cost-analyzer + dashboard)..."
echo "Dashboard will show metrics from cost-analyzer API (non-zero values)."
echo ""

# Check for existing processes on ports
for port in 8001 3000; do
  if lsof -i :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Port $port already in use. Stop existing service or use: kill \$(lsof -t -i:$port)"
    exit 1
  fi
done

cd backend/cost-analyzer
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 &
UVICORN_PID=$!
cd "$BASE_DIR/frontend/cost-dashboard"
REACT_APP_COST_API_URL=http://localhost:8001 npm start &
NPM_PID=$!

echo "Cost-analyzer PID: $UVICORN_PID (http://localhost:8001)"
echo "Dashboard PID: $NPM_PID (http://localhost:3000)"
echo "Open http://localhost:3000 - values are loaded from API and are non-zero."
echo "Press Ctrl+C to stop both."
trap "kill $UVICORN_PID $NPM_PID 2>/dev/null; exit 0" INT TERM
wait
